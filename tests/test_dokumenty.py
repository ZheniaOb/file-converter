"""Uruchomienie: python -m unittest discover tests"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from konwerter import ConversionError, ConversionRequest, execute
from konwerter.biuro import find_soffice

PRZYKLADY = Path(__file__).parent.parent / "przyklady"


def libreoffice_installed() -> bool:
    try:
        find_soffice()
        return True
    except ConversionError:
        return False


class TestDokumenty(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name)

    def convert(self, source: Path, fmt: str) -> Path:
        return execute(ConversionRequest(source, fmt, self.out))

    def test_txt_docx_txt_keeps_paragraphs_and_polish_chars(self):
        source = PRZYKLADY / "notatka.txt"
        result = self.convert(self.convert(source, "docx"), "txt")
        self.assertEqual(result.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_docx_to_txt_includes_table_in_order(self):
        text = self.convert(PRZYKLADY / "raport.docx", "txt").read_text(encoding="utf-8")
        self.assertEqual(text.split("\n\n"), [
            "Raport kwartalny",
            "Sprzedaż w Łodzi i Gdańsku wzrosła o 12%.",
            "Miasto\tWynik\nŁódź\t120\nGdańsk\t95",
            "Podsumowanie: żółty kolor oznacza wzrost.\n",
        ])

    def test_corrupted_docx(self):
        with self.assertRaisesRegex(ConversionError, "nie jest poprawnym dokumentem DOCX"):
            self.convert(PRZYKLADY / "uszkodzony.docx", "txt")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_missing_libreoffice_is_reported(self):
        with mock.patch.dict(os.environ, {"KONWERTER_SOFFICE": str(self.out / "brak" / "soffice.exe")}):
            with self.assertRaisesRegex(ConversionError, "KONWERTER_SOFFICE.*Zainstaluj LibreOffice"):
                self.convert(PRZYKLADY / "raport.docx", "pdf")

    @unittest.skipUnless(libreoffice_installed(), "brak LibreOffice")
    def test_docx_pdf_and_odt_round_trip(self):
        pdf = self.convert(PRZYKLADY / "raport.docx", "pdf")
        self.assertEqual(pdf.read_bytes()[:5], b"%PDF-")
        odt = self.convert(PRZYKLADY / "raport.docx", "odt")
        text = self.convert(self.convert(odt, "docx"), "txt").read_text(encoding="utf-8")
        self.assertIn("Sprzedaż w Łodzi i Gdańsku", text)

    def test_corrupted_docx_to_pdf(self):
        with self.assertRaisesRegex(ConversionError, "uszkodzony albo nie jest dokumentem .DOCX"):
            self.convert(PRZYKLADY / "uszkodzony.docx", "pdf")
        self.assertEqual(list(self.out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
