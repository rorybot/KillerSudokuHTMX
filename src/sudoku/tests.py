from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .views import SIZE, peers


MUTATING_URLS = (
    ("select_cell", [0, 0]),
    ("enter_number", None),
    ("move_selection", ["right"]),
    ("clear_cell", None),
    ("toggle_note_mode", None),
    ("reset_grid", None),
)


class SudokuTestCase(TestCase):
    def setUp(self):
        self.client.get(reverse("sudoku_grid"))

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
        self.assertContains(response, "New board")

    def test_board_contains_htmx_contract_and_csrf_header(self):
        response = self.client.get(reverse("sudoku_grid"))
        self.assertContains(response, 'hx-headers=\'{"X-CSRFToken":"')
        self.assertContains(response, 'hx-post="/select/0/0/"')
        self.assertContains(response, 'hx-post="/enter/"', count=9)
        self.assertContains(response, 'hx-post="/clear/"')
        self.assertContains(response, 'hx-post="/toggle_note_mode/"')
        self.assertContains(response, 'hx-post="/reset/"')

    def test_existing_session_state_is_rendered_without_reinitialization(self):
        self.set_cell(3, 4, final=8)
        session = self.client.session
        session["selected"] = [3, 4]
        session["note_mode"] = True
        session.save()

        response = self.client.get(reverse("sudoku_grid"))

        self.assertContains(response, '<span class="ks-final">8</span>', html=True)
        self.assertContains(response, "Notes on")
        self.assertContains(response, 'id="cell-3-4" class="ks-cell ks-cell-selected"')
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
        self.assertContains(response, 'id="cell-6-7" class="ks-cell ks-cell-selected"')
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
        self.assertContains(response, 'id="cell-0-0" class="ks-cell ks-cell-selected"')


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

        first.post(reverse("enter_number"), {"num": "7"})
        first.post(reverse("toggle_note_mode"))

        self.assertEqual(first.session["grid"][0][0]["final"], 7)
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
