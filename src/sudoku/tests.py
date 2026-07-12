import random
from copy import deepcopy

from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .generator import (
    DIFFICULTIES,
    count_solutions,
    generate_puzzle,
    generate_solution,
)
from .views import SIZE, legal_numbers, peers


MUTATING_URLS = (
    ("select_cell", [0, 0]),
    ("enter_number", None),
    ("move_selection", ["right"]),
    ("clear_cell", None),
    ("toggle_note_mode", None),
    ("reset_grid", None),
    ("new_game", None),
)


class SudokuTestCase(TestCase):
    def setUp(self):
        self.client.get(reverse("sudoku_grid"))
        solution = [[(row * 3 + row // 3 + col) % 9 + 1 for col in range(9)] for row in range(9)]
        session = self.client.session
        session["solution"] = solution
        session["cages"] = [
            {"cells": [[row, col] for col in range(9)], "sum": 45}
            for row in range(9)
        ]
        session.save()

    @property
    def state(self):
        return self.client.session

    def post(self, name, data=None, args=None):
        return self.client.post(reverse(name, args=args), data or {})

    def set_cell(self, row, col, *, final=None, notes=None):
        session = self.client.session
        grid = session["grid"]
        grid[row][col] = {"final": final, "notes": notes or []}
        session["grid"] = grid
        session.save()


class SudokuPageTests(SudokuTestCase):
    def test_initial_page_initializes_empty_state(self):
        state = self.state
        self.assertEqual(state["selected"], [0, 0])
        self.assertFalse(state["note_mode"])
        self.assertEqual(len(state["grid"]), SIZE)
        self.assertTrue(
            all(
                cell == {"final": None, "notes": []}
                for row in state["grid"]
                for cell in row
            )
        )

    def test_initial_page_renders_complete_accessible_board(self):
        response = self.client.get(reverse("sudoku_grid"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sudoku/grid.html")
        self.assertContains(response, 'id="sudoku-app"')
        self.assertContains(response, 'role="row"', count=9)
        self.assertContains(response, 'role="gridcell"', count=81)
        self.assertContains(response, 'aria-selected="true"', count=1)
        self.assertContains(response, "Notes off")
        self.assertContains(response, "New game")
        self.assertContains(response, "Killer Sudoku")
        self.assertContains(response, 'id="theme-toggle"')

    def test_board_contains_htmx_contract_and_csrf_header(self):
        response = self.client.get(reverse("sudoku_grid"))
        self.assertContains(response, 'hx-headers=\'{"X-CSRFToken":"')
        self.assertContains(response, 'hx-post="/select/0/0/"')
        self.assertContains(response, 'hx-post="/enter/"', count=9)
        self.assertContains(response, 'hx-post="/clear/"')
        self.assertContains(response, 'hx-post="/toggle_note_mode/"')
        self.assertContains(response, 'hx-post="/reset/"')
        self.assertContains(response, 'hx-post="/new/"')
        self.assertContains(response, 'aria-label="Puzzle difficulty"')

    def test_existing_session_state_is_rendered_without_reinitialization(self):
        self.set_cell(3, 4, final=8)
        session = self.client.session
        session["selected"] = [3, 4]
        session["note_mode"] = True
        session.save()

        response = self.client.get(reverse("sudoku_grid"))

        self.assertContains(response, '<span class="ks-final">8</span>', html=True)
        self.assertContains(response, "Notes on")
        self.assertContains(response, 'id="cell-3-4"')
        self.assertContains(response, "ks-cell-selected")
        self.assertEqual(self.state["selected"], [3, 4])


class EndpointContractTests(SudokuTestCase):
    def test_all_state_changing_endpoints_require_post(self):
        for name, args in MUTATING_URLS:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 405)

    def test_all_successful_mutations_return_replaceable_board_fragment(self):
        for name, args in MUTATING_URLS:
            with self.subTest(name=name):
                response = self.post(name, args=args)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "sudoku/board.html")
                self.assertContains(response, 'id="sudoku-app"')
                self.assertContains(response, 'hx-headers=\'{"X-CSRFToken":"')
                self.assertNotContains(response, "<!DOCTYPE html>")

    def test_unknown_move_direction_returns_bad_request_without_changing_selection(self):
        response = self.post("move_selection", args=["diagonal"])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Unknown direction")
        self.assertEqual(self.state["selected"], [0, 0])


class SelectionAndMovementTests(SudokuTestCase):
    def test_select_cell_updates_session_and_rendered_selection(self):
        response = self.post("select_cell", args=[6, 7])
        self.assertEqual(self.state["selected"], [6, 7])
        self.assertContains(response, 'id="cell-6-7"')
        self.assertContains(response, "ks-cell-selected")
        self.assertContains(response, 'aria-selected="true"', count=1)

    def test_each_direction_moves_one_cell(self):
        expected = {
            "up": [3, 4],
            "down": [5, 4],
            "left": [4, 3],
            "right": [4, 5],
        }
        for direction, destination in expected.items():
            with self.subTest(direction=direction):
                self.post("select_cell", args=[4, 4])
                self.post("move_selection", args=[direction])
                self.assertEqual(self.state["selected"], destination)

    def test_movement_wraps_at_all_four_edges(self):
        cases = (
            ([0, 4], "up", [8, 4]),
            ([8, 4], "down", [0, 4]),
            ([4, 0], "left", [4, 8]),
            ([4, 8], "right", [4, 0]),
        )
        for start, direction, destination in cases:
            with self.subTest(start=start, direction=direction):
                self.post("select_cell", args=start)
                self.post("move_selection", args=[direction])
                self.assertEqual(self.state["selected"], destination)


class NumberEntryTests(SudokuTestCase):
    def test_final_number_is_entered_and_same_number_toggles_off(self):
        response = self.post("enter_number", {"num": "4"})
        self.assertEqual(self.state["grid"][0][0], {"final": 4, "notes": []})
        self.assertContains(response, '<span class="ks-final">4</span>', html=True)

        self.post("enter_number", {"num": "4"})
        self.assertEqual(self.state["grid"][0][0], {"final": None, "notes": []})

    def test_different_final_number_replaces_existing_number(self):
        self.post("enter_number", {"num": "4"})
        self.post("enter_number", {"num": "9"})
        self.assertEqual(self.state["grid"][0][0], {"final": 9, "notes": []})

    def test_entering_final_number_clears_notes_in_that_cell(self):
        self.set_cell(0, 0, notes=[1, 2, 8])
        self.post("enter_number", {"num": "8"})
        self.assertEqual(self.state["grid"][0][0], {"final": 8, "notes": []})

    def test_invalid_and_missing_numbers_do_not_change_grid(self):
        for value in (None, "", "text", "0", "10", "-1"):
            with self.subTest(value=value):
                data = {} if value is None else {"num": value}
                response = self.post("enter_number", data)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    self.state["grid"][0][0],
                    {"final": None, "notes": []},
                )


class NotesTests(SudokuTestCase):
    def test_note_mode_toggles_on_and_off(self):
        on_response = self.post("toggle_note_mode")
        self.assertTrue(self.state["note_mode"])
        self.assertContains(on_response, "Notes on")
        self.assertContains(on_response, 'aria-pressed="true"')

        off_response = self.post("toggle_note_mode")
        self.assertFalse(self.state["note_mode"])
        self.assertContains(off_response, "Notes off")
        self.assertContains(off_response, 'aria-pressed="false"')

    def test_notes_are_added_sorted_and_toggled_independently(self):
        self.post("toggle_note_mode")
        for number in (7, 2, 5):
            self.post("enter_number", {"num": str(number)})
        self.assertEqual(self.state["grid"][0][0]["notes"], [2, 5, 7])

        self.post("enter_number", {"num": "5"})
        self.assertEqual(self.state["grid"][0][0]["notes"], [2, 7])

    def test_note_mode_replaces_a_final_value_instead_of_adding_a_note(self):
        self.set_cell(0, 0, final=3)
        self.post("toggle_note_mode")
        self.post("enter_number", {"num": "6"})
        self.assertEqual(self.state["grid"][0][0], {"final": 6, "notes": []})

    def test_final_entry_removes_matching_note_from_all_peers_only(self):
        peer_cells = ((0, 8), (8, 0), (1, 1))
        for row, col in (*peer_cells, (8, 8)):
            self.set_cell(row, col, notes=[2, 5, 7])

        self.post("enter_number", {"num": "5"})
        grid = self.state["grid"]

        for row, col in peer_cells:
            with self.subTest(row=row, col=col):
                self.assertEqual(grid[row][col]["notes"], [2, 7])
        self.assertEqual(grid[8][8]["notes"], [2, 5, 7])


class ClearAndResetTests(SudokuTestCase):
    def test_clear_removes_final_and_notes_from_selected_cell_only(self):
        self.set_cell(0, 0, final=4)
        self.set_cell(1, 1, notes=[2, 3])
        self.post("select_cell", args=[1, 1])

        self.post("clear_cell")

        grid = self.state["grid"]
        self.assertEqual(grid[1][1], {"final": None, "notes": []})
        self.assertEqual(grid[0][0], {"final": 4, "notes": []})
        self.assertEqual(self.state["selected"], [1, 1])

    def test_reset_restores_every_part_of_initial_state(self):
        self.set_cell(2, 3, final=9)
        self.set_cell(4, 5, notes=[1, 6])
        self.post("select_cell", args=[7, 8])
        self.post("toggle_note_mode")

        response = self.post("reset_grid")

        state = self.state
        self.assertEqual(state["selected"], [0, 0])
        self.assertFalse(state["note_mode"])
        self.assertTrue(
            all(
                cell == {"final": None, "notes": []}
                for row in state["grid"]
                for cell in row
            )
        )
        self.assertContains(response, 'id="cell-0-0"')
        self.assertContains(response, "ks-cell-selected")


class KillerGameTests(SudokuTestCase):
    def test_game_state_contains_solution_cages_and_difficulty(self):
        state = self.state
        self.assertEqual(state["difficulty"], "medium")
        self.assertEqual(state["game_status"], "playing")
        self.assertEqual(
            {tuple(cell) for cage in state["cages"] for cell in cage["cells"]},
            {(row, col) for row in range(9) for col in range(9)},
        )
        for row in state["solution"]:
            self.assertEqual(set(row), set(range(1, 10)))

    def test_new_game_uses_selected_difficulty_and_replaces_puzzle(self):
        old_solution = deepcopy(self.state["solution"])

        response = self.post("new_game", {"difficulty": "hard"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.state["difficulty"], "hard")
        self.assertNotEqual(self.state["solution"], old_solution)
        self.assertContains(response, '<option value="hard" selected>Hard</option>')
        self.assertTrue(
            all(
                cell == {"final": None, "notes": []}
                for row in self.state["grid"]
                for cell in row
            )
        )

    def test_new_game_rejects_unknown_difficulty_without_replacing_puzzle(self):
        old_solution = deepcopy(self.state["solution"])
        response = self.post("new_game", {"difficulty": "impossible"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.state["solution"], old_solution)

    def test_restart_preserves_current_puzzle(self):
        solution = deepcopy(self.state["solution"])
        cages = deepcopy(self.state["cages"])
        self.post("enter_number", {"num": "1"})
        self.post("reset_grid")
        self.assertEqual(self.state["solution"], solution)
        self.assertEqual(self.state["cages"], cages)

    def test_cage_totals_and_boundaries_are_rendered(self):
        response = self.client.get(reverse("sudoku_grid"))
        self.assertContains(response, 'class="ks-cage-sum">45</span>', count=9)
        self.assertContains(response, "cage-top")

    def test_conflicting_number_is_disabled_and_rejected_by_server(self):
        self.set_cell(0, 1, final=5)
        response = self.post("select_cell", args=[0, 0])
        self.assertContains(response, 'disabled aria-label="5 cannot be played in this cell"')

        self.post("enter_number", {"num": "5"})
        self.assertIsNone(self.state["grid"][0][0]["final"])

    def test_cage_sum_limits_available_numbers(self):
        session = self.client.session
        session["cages"] = [
            {"cells": [[0, 0], [0, 1]], "sum": 3},
            {"cells": [[0, col] for col in range(2, 9)], "sum": 42},
            *[
                {"cells": [[row, col] for col in range(9)], "sum": 45}
                for row in range(1, 9)
            ],
        ]
        session.save()

        self.assertEqual(legal_numbers(self.state["grid"], [0, 0], self.state["cages"]), {1, 2})
        response = self.post("select_cell", args=[0, 0])
        for number in range(3, 10):
            self.assertContains(
                response,
                f'disabled aria-label="{number} cannot be played in this cell"',
            )

    def test_completing_solution_shows_success_message(self):
        session = self.client.session
        solution = session["solution"]
        session["grid"] = [
            [{"final": solution[row][col], "notes": []} for col in range(9)]
            for row in range(9)
        ]
        session["grid"][0][0]["final"] = None
        session["selected"] = [0, 0]
        session.save()

        response = self.post("enter_number", {"num": str(solution[0][0])})

        self.assertEqual(self.state["game_status"], "won")
        self.assertContains(response, "Puzzle complete!")


class SecurityAndIsolationTests(TestCase):
    def test_mutations_reject_missing_csrf_token(self):
        for name, args in MUTATING_URLS:
            with self.subTest(name=name):
                client = Client(enforce_csrf_checks=True)
                client.get(reverse("sudoku_grid"))
                response = client.post(reverse(name, args=args))
                self.assertEqual(response.status_code, 403)

    def test_board_csrf_token_authorizes_every_mutation(self):
        for name, args in MUTATING_URLS:
            with self.subTest(name=name):
                client = Client(enforce_csrf_checks=True)
                page = client.get(reverse("sudoku_grid"))
                token = page.cookies["csrftoken"].value
                response = client.post(
                    reverse(name, args=args),
                    HTTP_X_CSRFTOKEN=token,
                )
                self.assertEqual(response.status_code, 200)

    def test_clients_have_independent_boards(self):
        first = Client()
        second = Client()
        first.get(reverse("sudoku_grid"))
        second.get(reverse("sudoku_grid"))

        number = first.session["solution"][0][0]
        first.post(reverse("enter_number"), {"num": str(number)})
        first.post(reverse("toggle_note_mode"))

        self.assertEqual(first.session["grid"][0][0]["final"], number)
        self.assertTrue(first.session["note_mode"])
        self.assertIsNone(second.session["grid"][0][0]["final"])
        self.assertFalse(second.session["note_mode"])


class PeerCalculationTests(SimpleTestCase):
    def test_center_cell_has_twenty_unique_peers(self):
        result = peers(4, 4)
        self.assertEqual(len(result), 20)
        self.assertNotIn((4, 4), result)

    def test_peers_include_entire_row_column_and_box(self):
        result = peers(1, 1)
        for index in range(SIZE):
            if index != 1:
                self.assertIn((1, index), result)
                self.assertIn((index, 1), result)
        for row in range(3):
            for col in range(3):
                if (row, col) != (1, 1):
                    self.assertIn((row, col), result)

    def test_peer_sets_are_symmetric(self):
        for row, col in ((0, 0), (4, 4), (8, 3)):
            for peer in peers(row, col):
                self.assertIn((row, col), peers(*peer))


class GeneratorTests(SimpleTestCase):
    def test_generated_solution_obeys_sudoku_rules(self):
        solution = generate_solution(random.Random(7))
        expected = set(range(1, 10))
        for row in solution:
            self.assertEqual(set(row), expected)
        for col in range(9):
            self.assertEqual({solution[row][col] for row in range(9)}, expected)
        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                self.assertEqual(
                    {
                        solution[row][col]
                        for row in range(box_row, box_row + 3)
                        for col in range(box_col, box_col + 3)
                    },
                    expected,
                )

    def test_generated_cages_cover_grid_once_and_match_solution(self):
        puzzle = generate_puzzle("medium", random.Random(11))
        cells = [tuple(cell) for cage in puzzle["cages"] for cell in cage["cells"]]
        self.assertEqual(len(cells), 81)
        self.assertEqual(len(set(cells)), 81)
        for cage in puzzle["cages"]:
            values = [puzzle["solution"][row][col] for row, col in cage["cells"]]
            self.assertEqual(sum(values), cage["sum"])
            self.assertEqual(len(values), len(set(values)))
            self.assertGreaterEqual(len(values), 2)
            self.assertTrue(self._is_connected(cage["cells"]))

    def test_cage_constraints_have_exactly_one_solution(self):
        puzzle = generate_puzzle("easy", random.Random(1))
        self.assertEqual(count_solutions(puzzle["cages"]), 1)

    def test_difficulties_have_progressively_fewer_larger_cages(self):
        cage_counts = []
        for difficulty in DIFFICULTIES:
            puzzle = generate_puzzle(difficulty, random.Random(17))
            cage_counts.append(len(puzzle["cages"]))
            self.assertFalse(any(len(cage["cells"]) == 1 for cage in puzzle["cages"]))
        self.assertGreater(cage_counts[0], cage_counts[1])
        self.assertGreater(cage_counts[1], cage_counts[2])

    @staticmethod
    def _is_connected(cells):
        remaining = {tuple(cell) for cell in cells}
        pending = [remaining.pop()]
        while pending:
            row, col = pending.pop()
            neighbours = {
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            } & remaining
            remaining -= neighbours
            pending.extend(neighbours)
        return not remaining
