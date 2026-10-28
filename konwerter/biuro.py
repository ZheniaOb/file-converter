"""Grupa C – formaty biurowe przez LibreOffice w trybie bez interfejsu (--headless)."""
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from .rejestr import ConversionError, converter

TIMEOUT = 120  # s
INSTALL_HINT = (
    "Zainstaluj LibreOffice (https://www.libreoffice.org/download/) "
    "albo ustaw zmienną środowiskową KONWERTER_SOFFICE na pełną ścieżkę do programu soffice."
)
KNOWN_PATHS = [
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "LibreOffice/program/soffice.exe",
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
]


def find_soffice() -> str:
    """Kolejność: zmienna KONWERTER_SOFFICE → PATH (soffice, libreoffice) → typowe ścieżki instalacji."""
    if configured := os.environ.get("KONWERTER_SOFFICE"):
        if Path(configured).is_file():
            return configured
        raise ConversionError(f"KONWERTER_SOFFICE wskazuje nieistniejący plik: {configured}. {INSTALL_HINT}")
    for name in ("soffice", "libreoffice"):
        if found := shutil.which(name):
            return found
    for path in KNOWN_PATHS:
        if path.is_file():
            return str(path)
    raise ConversionError(f"Nie znaleziono LibreOffice. {INSTALL_HINT}")


def libreoffice_convert(source: Path, target: Path) -> None:
    # DOCX i ODT to archiwa ZIP; LibreOffice bez tej kontroli "skonwertowałby" dowolny tekst
    if not zipfile.is_zipfile(source):
        raise ConversionError(f"Plik {source.name} jest uszkodzony albo nie jest dokumentem {source.suffix.upper()}.")
    with tempfile.TemporaryDirectory() as tmp:
        command = [
            find_soffice(), "--headless", "--norestore",
            # osobny profil: konwersja działa także przy otwartym oknie LibreOffice
            f"-env:UserInstallation={Path(tmp, 'profil').as_uri()}",
            "--convert-to", target.suffix.lstrip("."), "--outdir", tmp, str(source),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=TIMEOUT)
        except subprocess.TimeoutExpired as e:
            raise ConversionError(f"LibreOffice nie zakończył konwersji w {TIMEOUT} s.") from e
        if result.returncode != 0:
            raise ConversionError(
                f"LibreOffice zakończył pracę z kodem {result.returncode}: {result.stderr.strip() or 'brak opisu'}"
            )
        produced = Path(tmp) / (source.stem + target.suffix)
        if not produced.is_file():  # LibreOffice zwraca 0 także wtedy, gdy nie umie otworzyć pliku
            raise ConversionError(f"LibreOffice nie utworzył pliku – {source.name} może być uszkodzony.")
        shutil.move(produced, target)


for pair in [(".docx", ".pdf"), (".odt", ".pdf"), (".docx", ".odt"), (".odt", ".docx")]:
    converter(*pair)(libreoffice_convert)
