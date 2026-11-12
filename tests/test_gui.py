"""Testy logiki okna (bez klikania). Uruchomienie: python -m unittest discover tests"""
import tkinter as tk
import unittest
from pathlib import Path

from gui import App

PRZYKLADY = Path(__file__).parent.parent / "przyklady"


class TestGui(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as e:  # np. serwer bez ekranu
            self.skipTest(f"brak środowiska graficznego: {e}")
        self.app.withdraw()
        self.addCleanup(self.app.destroy)

    def convert_enabled(self) -> bool:
        return "disabled" not in self.app.convert_button.state()

    def test_nothing_selected_blocks_conversion(self):
        self.assertFalse(self.convert_enabled())
        self.assertEqual(str(self.app.format_box["state"]), "disabled")

    def test_unsupported_file_blocks_format_and_button(self):
        self.app.set_source(PRZYKLADY / "plik.xyz")
        self.assertEqual(self.app.format_box["values"], "")
        self.assertEqual(str(self.app.format_box["state"]), "disabled")
        self.assertFalse(self.convert_enabled())
        self.assertIn("Nieobsługiwany typ pliku", self.app.status.get())

    def test_formats_depend_on_extension(self):
        self.app.set_source(PRZYKLADY / "raport.docx")
        self.assertEqual(self.app.format_box["values"], (".odt", ".pdf", ".txt"))
        self.assertFalse(self.convert_enabled())  # format jeszcze niewybrany
        self.app.target_format.set(".pdf")
        self.app.on_format_selected()
        self.assertTrue(self.convert_enabled())

    def test_single_format_is_preselected(self):
        self.app.set_source(PRZYKLADY / "osoby.csv")
        self.assertEqual(self.app.target_format.get(), ".json")
        self.assertEqual(self.app.output_dir.get(), str(PRZYKLADY))
        self.assertTrue(self.convert_enabled())

    def test_controls_locked_while_converting(self):
        self.app.set_source(PRZYKLADY / "osoby.csv")
        self.app.busy = True
        self.app.refresh()
        self.assertFalse(self.convert_enabled())
        self.assertIn("disabled", self.app.source_button.state())


if __name__ == "__main__":
    unittest.main()
