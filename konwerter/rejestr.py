"""Rejestr konwerterów – logika konwersji oddzielona od interfejsu (CLI i GUI)."""
import logging
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

Converter = Callable[[Path, Path], None]  # (plik źródłowy, plik docelowy)
REGISTRY: dict[tuple[str, str], Converter] = {}


class ConversionError(Exception):
    """Kontrolowany błąd konwersji; komunikat jest przeznaczony dla użytkownika."""


def converter(source: str, target: str):
    """Dekorator rejestrujący pojedynczy kierunek konwersji."""
    def register(func: Converter) -> Converter:
        REGISTRY[(source.lower(), target.lower())] = func
        return func
    return register


def available_targets(source: Path) -> list[str]:
    return sorted(target for (src, target) in REGISTRY if src == source.suffix.lower())


def free_path(path: Path) -> Path:
    """Bezpieczna nazwa: plik.json, a gdy istnieje – plik (1).json, plik (2).json, ..."""
    candidate, n = path, 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return candidate


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    target_format: str  # "json" albo ".json"
    output_dir: Path

    @property
    def key(self) -> tuple[str, str]:
        return self.source.suffix.lower(), "." + self.target_format.lower().lstrip(".")

    @property
    def target(self) -> Path:
        """Domyślna ścieżka wyniku (może już istnieć)."""
        return self.output_dir / (self.source.stem + self.key[1])

    def validate(self) -> None:
        """Sprawdza wszystko, co da się sprawdzić przed konwersją; każdy błąd mówi, co zrobić dalej."""
        if self.source == Path(""):
            raise ConversionError("Nie wybrano pliku wejściowego. Wybierz plik do konwersji.")
        if not self.target_format.strip(". "):
            raise ConversionError("Nie wybrano formatu docelowego. Wybierz format z listy.")
        if not self.source.is_file():
            raise ConversionError(f"Nie znaleziono pliku wejściowego: {self.source}. Sprawdź ścieżkę i wybierz plik ponownie.")
        if not self.output_dir.is_dir():
            raise ConversionError(f"Nie znaleziono katalogu docelowego: {self.output_dir}. Wybierz istniejący katalog.")
        if self.key not in REGISTRY:
            targets = ", ".join(available_targets(self.source))
            raise ConversionError(
                f"Nieobsługiwana konwersja {self.key[0] or '(brak rozszerzenia)'} → {self.key[1]}. "
                + (f"Wybierz jeden z formatów: {targets}." if targets else
                   f"Wybierz plik jednego z typów: {', '.join(sorted({s for s, _ in REGISTRY}))}.")
            )
        try:  # os.access() na Windows nie widzi uprawnień ACL – próbny plik jest pewniejszy
            with tempfile.TemporaryFile(dir=self.output_dir):
                pass
        except OSError as e:
            raise ConversionError(
                f"Brak uprawnień do zapisu w katalogu {self.output_dir}. Wybierz inny katalog zapisu."
            ) from e


def execute(request: ConversionRequest, overwrite: bool = False) -> Path:
    """Wykonuje konwersję i zwraca ścieżkę wyniku.

    overwrite=False: istniejący plik zostaje, wynik dostaje bezpieczną nazwę „plik (1).ext”.
    overwrite=True: istniejący plik jest zastępowany (GUI pyta o to użytkownika).
    """
    request.validate()
    target = request.target if overwrite else free_path(request.target)
    start = time.perf_counter()
    try:
        REGISTRY[request.key](request.source, target)
    except OSError as e:
        log.error("%s → %s: %s", request.source, target, e)
        raise ConversionError(
            f"Błąd odczytu/zapisu pliku: {e}. Sprawdź, czy plik nie jest otwarty w innym programie "
            f"(np. Word, Excel) i czy na dysku jest miejsce, a potem spróbuj ponownie."
        ) from e
    except ConversionError as e:
        log.error("%s → %s: %s", request.source, target, e)
        raise
    log.info("%s → %s (%.3f s)", request.source, target, time.perf_counter() - start)
    return target
