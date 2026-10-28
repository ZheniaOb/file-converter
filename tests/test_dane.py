"""Uruchomienie: python -m unittest discover tests"""
import json
import tempfile
import unittest
from pathlib import Path

from konwerter import ConversionError, ConversionRequest, available_targets, execute

PRZYKLADY = Path(__file__).parent.parent / "przyklady"


class TestDane(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name)

    def convert(self, source: Path, fmt: str) -> Path:
        return execute(ConversionRequest(source, fmt, self.out))

    def test_available_targets(self):
        self.assertEqual(available_targets(Path("a.CSV")), [".json"])
        self.assertEqual(available_targets(Path("a.json")), [".csv"])
        self.assertEqual(available_targets(Path("a.docx")), [".odt", ".pdf", ".txt"])
        self.assertEqual(available_targets(Path("a.xyz")), [])

    def test_csv_json_csv_round_trip(self):
        source = PRZYKLADY / "osoby.csv"
        records = json.loads(self.convert(source, "json").read_text(encoding="utf-8"))
        self.assertEqual(list(records[0]), ["imię", "nazwisko", "miasto", "uwagi"])
        self.assertEqual(records[0]["uwagi"], 'jaźń, "cytat"')
        self.assertEqual(records[1]["miasto"], "")
        self.assertEqual(records[2]["uwagi"], "dwie\nlinie")

        back = self.convert(self.out / "osoby.json", ".csv")
        self.assertEqual(back.read_text(encoding="utf-8-sig").splitlines(),
                         source.read_text(encoding="utf-8").splitlines())

    def test_semicolon_csv_gives_same_json(self):
        a = self.convert(PRZYKLADY / "osoby.csv", "json").read_text(encoding="utf-8")
        b = self.convert(PRZYKLADY / "osoby_excel.csv", "json").read_text(encoding="utf-8")
        self.assertEqual(a, b)

    def test_json_union_of_keys_null_and_nested(self):
        lines = self.convert(PRZYKLADY / "produkty.json", "csv").read_text(encoding="utf-8-sig").splitlines()
        self.assertEqual(lines, [
            "id,nazwa,cena,dostępny,tagi",
            "1,Żółty ołówek,2.5,true,",
            '2,Gumka,,,"[""biuro"", ""szkoła""]"',
        ])

    def test_bad_json_gives_message_and_no_file(self):
        with self.assertRaisesRegex(ConversionError, r"Błędny JSON.*wiersz 2"):
            self.convert(PRZYKLADY / "bledny.json", "csv")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_wrong_json_structure(self):
        bad = self.out / "obiekt.json"
        bad.write_text('{"imię": "Anna"}', encoding="utf-8")
        with self.assertRaisesRegex(ConversionError, "tablicy obiektów"):
            self.convert(bad, "csv")

    def test_validate(self):
        with self.assertRaisesRegex(ConversionError, "Nie znaleziono pliku"):
            self.convert(self.out / "brak.csv", "json")
        with self.assertRaisesRegex(ConversionError, "Nieobsługiwana konwersja .csv → .pdf"):
            self.convert(PRZYKLADY / "osoby.csv", "pdf")

    def test_does_not_overwrite(self):
        first = self.convert(PRZYKLADY / "osoby.csv", "json")
        second = self.convert(PRZYKLADY / "osoby.csv", "json")
        self.assertEqual((first.name, second.name), ("osoby.json", "osoby (1).json"))


if __name__ == "__main__":
    unittest.main()
