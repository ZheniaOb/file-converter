# Uniwersalny konwerter plików – Programowanie V, Projekt 1

Etap: **Lab. 2** – konwersje CSV → JSON i JSON → CSV uruchamiane bez GUI.

## Wymagania

Python 3.10+. Na tym etapie tylko biblioteka standardowa (`csv`, `json`, `pathlib`) – brak zależności zewnętrznych.

## Uruchomienie

```
python main.py przyklady/osoby.csv json -o wyniki
python main.py przyklady/produkty.json csv
```

- `format` można podać jako `json` lub `.json`.
- `-o` – katalog zapisu (musi istnieć); domyślnie katalog pliku wejściowego.
- Istniejący plik nigdy nie jest nadpisywany: powstaje `osoby (1).json`, `osoby (2).json`, ...
- Błędy kończą program kodem `1` z komunikatem; operacje i błędy są logowane do `konwerter.log`.

Testy: `python -m unittest discover tests`

## Macierz konwersji

| Źródło | Cel  | Status       | Ograniczenia |
|--------|------|--------------|--------------|
| CSV    | JSON | działa       | wszystkie wartości jako tekst (brak rozpoznawania liczb) |
| JSON   | CSV  | działa       | patrz „Struktura JSON” |
| TXT, DOCX, ODT, PDF | – | Lab. 3 | – |

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

## Architektura

- `konwerter/rejestr.py` – rejestr par formatów (`@converter`), `ConversionRequest.validate()`, `available_targets()`, `execute()`, wspólny wyjątek `ConversionError`, bezpieczna nazwa pliku.
- `konwerter/dane.py` – konwertery CSV ↔ JSON.
- `main.py` – interfejs wiersza poleceń (GUI w Lab. 4 użyje tego samego rejestru).

Nowa para formatów = nowa funkcja z dekoratorem `@converter(".x", ".y")`; interfejs pobiera listę celów z `available_targets()`.

## Źródła i narzędzia AI

- Wzorzec rejestru na podstawie „Kodu inspiracyjnego” z instrukcji projektu.
- Dokumentacja Pythona: `csv`, `json`, `pathlib`, `unittest`.
- Kod przygotowany z pomocą Claude (Anthropic).

## Autor

Yevhenii Oberniak

