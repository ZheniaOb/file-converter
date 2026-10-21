"""Konwerter plików – uruchamianie bez GUI.

Przykład:  python main.py przyklady/osoby.csv json -o wyniki
"""
import argparse
import logging
import sys
from pathlib import Path

from konwerter import ConversionError, ConversionRequest, execute


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")  # konsola bez UTF-8 nie wywróci programu
    parser = argparse.ArgumentParser(description="Konwersja plików CSV ↔ JSON.")
    parser.add_argument("plik", type=Path, help="plik wejściowy")
    parser.add_argument("format", help="format docelowy, np. json lub .csv")
    parser.add_argument("-o", "--katalog", type=Path, help="katalog zapisu (domyślnie katalog pliku)")
    args = parser.parse_args(argv)
    logging.basicConfig(filename="konwerter.log", encoding="utf-8", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    try:
        result = execute(ConversionRequest(args.plik, args.format, args.katalog or args.plik.parent))
    except ConversionError as e:
        print(f"Błąd: {e}", file=sys.stderr)
        return 1
    print(f"Zapisano: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
