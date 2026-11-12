# Uniwersalny konwerter plików – Programowanie V, Projekt 1

## Cel

Aplikacja desktopowa (Python 3 + Tkinter/ttk), która pozwala wybrać plik wejściowy, pokazuje wyłącznie dostępne dla niego formaty docelowe, wykonuje konwersję i zapisuje wynik we wskazanym katalogu. Obsługuje **8 kierunków konwersji z 3 grup**: dane strukturalne (CSV ↔ JSON), tekst/dokument (TXT ↔ DOCX) oraz formaty biurowe (DOCX/ODT → PDF, DOCX ↔ ODT). Konwersję można też uruchomić z wiersza poleceń, bez okna.

## Wymagania

| Zależność | Do czego | Instalacja |
|-----------|----------|------------|
| Python 3.10+ z modułem `tkinter` | cały program | https://www.python.org/downloads/ (na Linuksie dodatkowo `sudo apt install python3-tk`) |
| `python-docx` ≥ 1.1 | TXT ↔ DOCX | `requirements.txt` (patrz niżej) |
| LibreOffice | tylko grupa C (PDF, ODT) | https://www.libreoffice.org/download/ · Windows: `winget install TheDocumentFoundation.LibreOffice` · Linux: `sudo apt install libreoffice` |

Program szuka LibreOffice w kolejności: zmienna środowiskowa `KONWERTER_SOFFICE` (pełna ścieżka do `soffice`) → `soffice`/`libreoffice` w `PATH` → typowe katalogi instalacji (Windows, macOS). Brak LibreOffice lub `python-docx` daje komunikat z instrukcją instalacji; pozostałe konwersje działają dalej.

## Instalacja

```
git clone https://github.com/ZheniaOb/file-converter.git
cd file-converter
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Linux / macOS
python -m pip install -r requirements.txt
```

Sprawdzenie instalacji: `python -m unittest discover tests` – powinno wypisać `OK` (bez LibreOffice testy grupy C są pomijane: `OK (skipped=1)`).

## Uruchomienie – okno (GUI)

```
python main.py
```

1. **Wybierz plik…** – okno wyboru pokazuje domyślnie tylko obsługiwane typy (`.csv`, `.docx`, `.json`, `.odt`, `.txt`). Katalog zapisu ustawia się na katalog pliku.
2. **Format docelowy** – lista zawiera wyłącznie formaty dostępne dla rozszerzenia pliku (z `available_targets()`); dla nieobsługiwanego pliku lista jest zablokowana, a status podaje obsługiwane typy.
3. **Wybierz katalog…** – opcjonalnie inny katalog zapisu.
4. **Konwertuj** – przycisk jest aktywny dopiero, gdy wybrano plik, katalog i format.

- Jeśli plik wynikowy już istnieje, program pyta: **Tak** – nadpisz, **Nie** – zapisz jako `plik (1).ext`, **Anuluj** – nie konwertuj.
- Konwersja działa w osobnym wątku – okno nie zamarza (ważne przy LibreOffice, ok. 5 s); w tym czasie pasek postępu jest animowany, a przyciski zablokowane.
- Wynik: status pod paskiem i okno „Gotowe” ze ścieżką pliku; błąd: czerwony status i okno z przyczyną oraz dalszym krokiem.

## Uruchomienie – wiersz poleceń

```
python main.py przyklady/osoby.csv json -o wyniki
python main.py przyklady/produkty.json csv
python main.py przyklady/notatka.txt docx -o wyniki
python main.py przyklady/raport.docx pdf -o wyniki
```

- `format` można podać jako `json` lub `.json`.
- `-o` – katalog zapisu (musi istnieć); domyślnie katalog pliku wejściowego.
- W trybie bez GUI istniejący plik nigdy nie jest nadpisywany: powstaje `osoby (1).json`, `osoby (2).json`, ...
- Błędy kończą program kodem `1` z komunikatem; operacje i błędy są logowane do `konwerter.log`.

## Walidacja i obsługa błędów

Przed konwersją `ConversionRequest.validate()` sprawdza: wybrany plik i format (niepuste), istnienie pliku i katalogu, obsługiwaną parę formatów oraz możliwość zapisu w katalogu (próbny plik tymczasowy). Konflikt nazw: GUI pyta o nadpisanie, CLI zapisuje pod bezpieczną nazwą. Dostępność `python-docx` i LibreOffice jest sprawdzana przy konwersji, która ich potrzebuje.

Wszystkie błędy przechodzą przez jeden wyjątek `ConversionError`; komunikat zawiera przyczynę i dalszy krok, np.:

```
Błąd: Błędny JSON w pliku bledny.json: Illegal trailing comma before end of object (wiersz 2, kolumna 18). Popraw wskazane miejsce i spróbuj ponownie.
```

Każda operacja (czas trwania) i każdy błąd są zapisywane w `konwerter.log` w katalogu uruchomienia.

## Testy

```
python -m unittest discover tests
```

23 testy automatyczne (`tests/`): konwertery wszystkich grup, `validate()`, `available_targets()`, bezpieczna nazwa i nadpisywanie, brak bibliotek/narzędzi oraz logika okna. Raport z minimalną macierzą testów, wynikami i zrzutami ekranu: [TESTY.md](TESTY.md).

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

## Znane ograniczenia

- Konwersje nie zachowują złożonego formatowania, osadzonych wykresów, przypisów ani makr; układ stron PDF może różnić się od oryginału.
- CSV → JSON nie rozpoznaje typów – liczby i daty zostają tekstem; JSON → CSV spłaszcza zagnieżdżone wartości do tekstu JSON.
- CSV z samym nagłówkiem daje `[]` – nazwy kolumn nie przechodzą do JSON.
- Pliki tekstowe muszą być w UTF-8 (inne kodowania, np. Windows-1250, dają komunikat o błędzie).
- Konwersje grupy C wymagają LibreOffice i trwają kilka sekund (start programu); limit czasu to 120 s.
- Zamknięcie okna w trakcie konwersji (po potwierdzeniu) przerywa ją i może zostawić niedokończony plik.
- Program był testowany na Windows 11 (Python 3.12 i 3.14, LibreOffice 26.8); Linux i macOS – tylko na podstawie dokumentacji.

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

- `konwerter/rejestr.py` – rejestr par formatów (`@converter`), `ConversionRequest.validate()`, `available_targets()`, `execute(request, overwrite=False)`, wspólny wyjątek `ConversionError`, bezpieczna nazwa pliku.
- `konwerter/dane.py` – grupa A: CSV ↔ JSON.
- `konwerter/dokumenty.py` – grupa B: TXT ↔ DOCX.
- `konwerter/biuro.py` – grupa C: wykrywanie i wywołanie LibreOffice.
- `gui.py` – okno Tkinter/ttk; nie zna konkretnych konwerterów – formaty bierze z `available_targets()`, konwersję uruchamia przez `execute()` w wątku roboczym, a wynik odbiera w wątku okna (`after()`).
- `main.py` – punkt startowy: bez argumentów otwiera okno, z argumentami działa w wierszu poleceń; konfiguruje log `konwerter.log`.

Nowa para formatów = nowa funkcja z dekoratorem `@converter(".x", ".y")`; interfejs pobiera listę celów z `available_targets()`.

## Źródła i narzędzia AI

- Wzorzec rejestru na podstawie „Kodu inspiracyjnego” z instrukcji projektu.
- Dokumentacja Pythona: `csv`, `json`, `pathlib`, `subprocess`, `threading`, `tkinter`/`ttk`, `tkinter.filedialog`, `unittest`.
- python-docx – https://python-docx.readthedocs.io/ (wybrana, bo jest czysto pythonowa i obsługuje odczyt i zapis DOCX).
- LibreOffice, parametry wiersza poleceń – https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html (jedyne darmowe narzędzie obsługujące DOCX, ODT i PDF na Windows, Linux i macOS).
- Kod przygotowany z pomocą Claude (Anthropic).

## Autor

Yevhenii Oberniak

