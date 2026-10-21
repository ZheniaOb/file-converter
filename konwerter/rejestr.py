"""Rejestr konwerterów – logika konwersji oddzielona od interfejsu (CLI, później GUI)."""
import logging
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

    def validate(self) -> None:
        if not self.source.is_file():
            raise ConversionError(f"Nie znaleziono pliku wejściowego: {self.source}")
        if not self.output_dir.is_dir():
            raise ConversionError(f"Nie znaleziono katalogu docelowego: {self.output_dir}")
        if self.key not in REGISTRY:
            targets = ", ".join(available_targets(self.source)) or "brak"
            raise ConversionError(
                f"Nieobsługiwana konwersja {self.key[0] or '(brak rozszerzenia)'} → {self.key[1]}. "
                f"Dostępne formaty docelowe: {targets}."
            )


def execute(request: ConversionRequest) -> Path:
    """Wykonuje konwersję; nigdy nie nadpisuje istniejącego pliku. Zwraca ścieżkę wyniku."""
    request.validate()
    target = free_path(request.output_dir / (request.source.stem + request.key[1]))
    start = time.perf_counter()
    try:
        REGISTRY[request.key](request.source, target)
    except OSError as e:
        log.error("%s → %s: %s", request.source, target, e)
        raise ConversionError(f"Błąd odczytu/zapisu pliku: {e}") from e
    except ConversionError as e:
        log.error("%s → %s: %s", request.source, target, e)
        raise
    log.info("%s → %s (%.3f s)", request.source, target, time.perf_counter() - start)
    return target
