"""Grupa A – dane strukturalne: CSV ↔ JSON."""
import csv
import io
import json
from pathlib import Path

from .rejestr import ConversionError, converter


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")  # UTF-8 z BOM (Excel) lub bez
    except UnicodeDecodeError as e:
        raise ConversionError(f"Plik {path.name} nie jest zapisany w UTF-8 (bajt nr {e.start}).") from e


def to_cell(value) -> str:
    """null → pusta komórka; tekst bez zmian; liczby, bool, listy, obiekty → zapis JSON."""
    if value is None:
        return ""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


@converter(".csv", ".json")
def csv_to_json(source: Path, target: Path) -> None:
    text = read_utf8(source)
    if not text.strip():
        raise ConversionError(f"Plik {source.name} jest pusty.")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel  # jedna kolumna albo nietypowy plik → przecinek
    reader = csv.reader(io.StringIO(text, newline=""), dialect)
    try:
        header = next(reader)
        if len(set(header)) != len(header):
            raise ConversionError(f"Nagłówek zawiera powtórzone nazwy kolumn: {header}")
        records = []
        for row in reader:
            if not row:
                continue  # pusty wiersz
            if len(row) > len(header):
                raise ConversionError(
                    f"Wiersz {reader.line_num} ma {len(row)} pól, a nagłówek {len(header)}."
                )
            row += [""] * (len(header) - len(row))
            records.append(dict(zip(header, row)))
    except csv.Error as e:
        raise ConversionError(f"Niepoprawny CSV w wierszu {reader.line_num}: {e}") from e
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


@converter(".json", ".csv")
def json_to_csv(source: Path, target: Path) -> None:
    try:
        data = json.loads(read_utf8(source))
    except json.JSONDecodeError as e:
        raise ConversionError(
            f"Błędny JSON w pliku {source.name}: {e.msg} (wiersz {e.lineno}, kolumna {e.colno})."
        ) from e
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ConversionError('Oczekiwano tablicy obiektów, np. [{"imię": "Anna"}, {"imię": "Jan"}].')
    if not data:
        raise ConversionError("Tablica JSON jest pusta – brak danych do zapisania.")
    header = list(dict.fromkeys(key for record in data for key in record))  # kolejność pojawienia się
    with target.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows([to_cell(record.get(key)) for key in header] for record in data)
