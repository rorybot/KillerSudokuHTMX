from django.test import TestCase
from django.urls import reverse


class SudokuViewsTests(TestCase):
    def setUp(self):
        self.client.get(reverse("sudoku_grid"))

    def state(self):
        return self.client.session

    def post(self, name, data=None, args=None):
        return self.client.post(reverse(name, args=args), data or {})

    def test_initial_page_has_board_controls_and_note_mode(self):
        response = self.client.get(reverse("sudoku_grid"))
        self.assertContains(response, 'id="sudoku-app"')
        self.assertContains(response, 'role="gridcell"', count=81)
        self.assertContains(response, "Notes off")
        self.assertEqual(self.state()["selected"], [0, 0])

    def test_endpoints_that_change_state_require_post(self):
        for name, args in (("enter_number", None), ("clear_cell", None), ("toggle_note_mode", None), ("reset_grid", None), ("select_cell", [0, 0]), ("move_selection", ["right"])):
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 405)

    def test_select_move_and_wrap(self):
        self.post("select_cell", args=[8, 8])
        self.post("move_selection", args=["right"])
        self.post("move_selection", args=["down"])
        self.assertEqual(self.state()["selected"], [0, 0])

    def test_final_number_toggles_and_clears_cell_notes(self):
        session = self.client.session
        session["grid"][0][0]["notes"] = [1, 2]
        session.save()
        self.post("enter_number", {"num": "4"})
        self.assertEqual(self.state()["grid"][0][0], {"final": 4, "notes": []})
        self.post("enter_number", {"num": "4"})
        self.assertIsNone(self.state()["grid"][0][0]["final"])

    def test_notes_toggle_in_note_mode(self):
        self.post("toggle_note_mode")
        response = self.post("enter_number", {"num": "7"})
        self.assertContains(response, "Notes on")
        self.assertEqual(self.state()["grid"][0][0]["notes"], [7])
        self.post("enter_number", {"num": "7"})
        self.assertEqual(self.state()["grid"][0][0]["notes"], [])

    def test_final_entry_removes_note_from_row_column_and_box(self):
        session = self.client.session
        for row, col in ((0, 8), (8, 0), (1, 1), (8, 8)):
            session["grid"][row][col]["notes"] = [5]
        session.save()
        self.post("enter_number", {"num": "5"})
        grid = self.state()["grid"]
        self.assertEqual(grid[0][8]["notes"], [])
        self.assertEqual(grid[8][0]["notes"], [])
        self.assertEqual(grid[1][1]["notes"], [])
        self.assertEqual(grid[8][8]["notes"], [5])

    def test_clear_and_reset(self):
        self.post("enter_number", {"num": "3"})
        self.post("clear_cell")
        self.assertIsNone(self.state()["grid"][0][0]["final"])
        self.post("enter_number", {"num": "3"})
        self.post("toggle_note_mode")
        self.post("reset_grid")
        state = self.state()
        self.assertFalse(state["note_mode"])
        self.assertTrue(all(cell == {"final": None, "notes": []} for row in state["grid"] for cell in row))

    def test_invalid_number_does_not_change_grid(self):
        self.post("enter_number", {"num": "not-a-number"})
        self.assertIsNone(self.state()["grid"][0][0]["final"])
