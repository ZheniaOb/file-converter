# Uniwersalny konwerter plików – Programowanie V, Projekt 1

Etap: **Lab. 3** – 8 kierunków konwersji z 3 grup (CSV/JSON, TXT/DOCX, DOCX/ODT/PDF), uruchamiane bez GUI.

## Wymagania

- Python 3.10+
- `python-docx` (TXT ↔ DOCX): `pip install -r requirements.txt`
- LibreOffice (tylko grupa C: PDF, ODT): https://www.libreoffice.org/download/
  (Windows: `winget install TheDocumentFoundation.LibreOffice`)

Program szuka LibreOffice w kolejności: zmienna środowiskowa `KONWERTER_SOFFICE` (pełna ścieżka do `soffice`) → `soffice`/`libreoffice` w `PATH` → typowe katalogi instalacji (Windows, macOS). Brak LibreOffice daje komunikat z instrukcją instalacji; pozostałe konwersje działają dalej.

## Uruchomienie

```
python main.py przyklady/osoby.csv json -o wyniki
python main.py przyklady/produkty.json csv
python main.py przyklady/notatka.txt docx -o wyniki
python main.py przyklady/raport.docx pdf -o wyniki
```

- `format` można podać jako `json` lub `.json`.
- `-o` – katalog zapisu (musi istnieć); domyślnie katalog pliku wejściowego.
- Istniejący plik nigdy nie jest nadpisywany: powstaje `osoby (1).json`, `osoby (2).json`, ...
- Błędy kończą program kodem `1` z komunikatem; operacje i błędy są logowane do `konwerter.log`.

Testy: `python -m unittest discover tests`

## Macierz konwersji

| Grupa | Źródło | Cel  | Narzędzie | Ograniczenia |
|-------|--------|------|-----------|--------------|
| A | CSV  | JSON | `csv`, `json` | wszystkie wartości jako tekst (brak rozpoznawania liczb) |
| A | JSON | CSV  | `csv`, `json` | patrz „Struktura JSON” |
| B | TXT  | DOCX | python-docx | tylko czysty tekst, bez stylów |
| B | DOCX | TXT  | python-docx | tracone: formatowanie, obrazy, przypisy, nagłówki/stopki strony |
| C | DOCX | PDF  | LibreOffice | układ stron może się nieznacznie różnić od Worda |
| C | ODT  | PDF  | LibreOffice | jw. |
| C | DOCX | ODT  | LibreOffice | złożone formatowanie (makra, pola) może się zmienić |
| C | ODT  | DOCX | LibreOffice | jw. |

Inne pary (np. PDF → DOCX, TXT → PDF) nie są obsługiwane.

## Semantyka TXT ↔ DOCX

- TXT czytany i zapisywany w UTF-8.
- TXT → DOCX: akapit = blok tekstu oddzielony pustą linią; pojedyncza nowa linia wewnątrz bloku → złamanie wiersza w tym samym akapicie.
- DOCX → TXT: akapity i tabele w kolejności z dokumentu, oddzielone pustą linią; puste akapity pomijane; komórki tabeli oddzielone tabulatorem, wiersze tabeli nową linią.

## LibreOffice (grupa C)

Wywołanie: `soffice --headless --norestore -env:UserInstallation=<tymczasowy profil> --convert-to <format> --outdir <katalog tymczasowy> <plik>`.

- `subprocess.run` z listą argumentów (bez `shell=True`) i limitem czasu 120 s.
- Sprawdzany jest kod zakończenia oraz to, czy plik wynikowy powstał (LibreOffice zwraca 0 także dla pliku, którego nie umiał otworzyć).
- Osobny tymczasowy profil sprawia, że konwersja działa także przy otwartym oknie LibreOffice.
- Wynik powstaje w katalogu tymczasowym i dopiero potem jest przenoszony pod bezpieczną nazwę – nic nie zostanie nadpisane.

## Semantyka CSV ↔ JSON

**Kodowanie.** Wejście: UTF-8 z BOM lub bez. Wyjście: JSON – UTF-8; CSV – UTF-8 z BOM (Excel poprawnie pokazuje wtedy polskie znaki). Plik w innym kodowaniu daje komunikat o błędzie.

**CSV → JSON.**
- Pierwszy wiersz to nagłówek; nazwy kolumn muszą być unikalne.
- Separator wykrywany automatycznie: `,`, `;` (Excel PL) lub tabulator.
- Wynik: tablica obiektów, klucze w kolejności kolumn, wartości jako tekst.
- Pusta komórka → `""`; brakujące pola na końcu wiersza → `""`; nadmiarowe pola → błąd; puste wiersze są pomijane.

**Struktura JSON (JSON → CSV).** Akceptowana jest wyłącznie tablica obiektów:

```json
[{"imię": "Anna", "wiek": 30}, {"imię": "Jan", "miasto": "Łódź"}]
```

- Nagłówek = suma kluczy ze wszystkich obiektów w kolejności pierwszego wystąpienia.
- `null` i brak klucza → pusta komórka.
- Liczby, `true`/`false`, listy i obiekty zagnieżdżone → zapis JSON w komórce (np. `["a", "b"]`).
- Błędny JSON, inny typ niż tablica obiektów lub pusta tablica → komunikat, plik wynikowy nie powstaje.

## Dane przykładowe (`przyklady/`)

| Plik | Co sprawdza | Oczekiwany wynik |
|------|-------------|------------------|
| `osoby.csv` | polskie znaki, pusta wartość, cudzysłów, przecinek i nowa linia w polu | JSON z 3 rekordami; powrót do CSV daje identyczną treść |
| `osoby_excel.csv` | separator `;` | JSON identyczny jak z `osoby.csv` |
| `produkty.json` | różne klucze, `null`, liczba, bool, lista | CSV z kolumnami `id,nazwa,cena,dostępny,tagi` |
| `bledny.json` | przecinek przed `}` | `Błąd: Błędny JSON ... (wiersz 2, kolumna 18).` |
| `notatka.txt` | akapity, lista, polskie znaki | DOCX z 4 akapitami; powrót do TXT daje identyczną treść |
| `raport.docx` | nagłówek, akapity, tabela | TXT z tabelą w środku; PDF i ODT otwierają się poprawnie |
| `uszkodzony.docx` | tekst z rozszerzeniem `.docx` | `Błąd: Plik uszkodzony.docx nie jest poprawnym dokumentem DOCX ...` |

## Architektura

- `konwerter/rejestr.py` – rejestr par formatów (`@converter`), `ConversionRequest.validate()`, `available_targets()`, `execute()`, wspólny wyjątek `ConversionError`, bezpieczna nazwa pliku.
- `konwerter/dane.py` – grupa A: CSV ↔ JSON.
- `konwerter/dokumenty.py` – grupa B: TXT ↔ DOCX.
- `konwerter/biuro.py` – grupa C: wykrywanie i wywołanie LibreOffice.
- `main.py` – interfejs wiersza poleceń (GUI w Lab. 4 użyje tego samego rejestru).

Nowa para formatów = nowa funkcja z dekoratorem `@converter(".x", ".y")`; interfejs pobiera listę celów z `available_targets()`.

## Źródła i narzędzia AI

- Wzorzec rejestru na podstawie „Kodu inspiracyjnego” z instrukcji projektu.
- Dokumentacja Pythona: `csv`, `json`, `pathlib`, `subprocess`, `unittest`.
- python-docx – https://python-docx.readthedocs.io/ (wybrana, bo jest czysto pythonowa i obsługuje odczyt i zapis DOCX).
- LibreOffice, parametry wiersza poleceń – https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html (jedyne darmowe narzędzie obsługujące DOCX, ODT i PDF na Windows, Linux i macOS).
- Kod przygotowany z pomocą Claude (Anthropic).

## Autor

Yevhenii Oberniak

