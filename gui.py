"""Graficzny interfejs konwertera (Tkinter/ttk). Uruchamiany przez: python main.py"""
import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from konwerter import REGISTRY, ConversionError, ConversionRequest, available_targets, execute
from konwerter.rejestr import free_path

log = logging.getLogger(__name__)

SOURCE_TYPES = sorted({source for source, _ in REGISTRY})


def upper(extension: str) -> str:
    return extension.lstrip(".").upper()


MATRIX = "   ".join(
    f"{upper(src)} → {', '.join(upper(t) for t in available_targets(Path('x' + src)))}" for src in SOURCE_TYPES
)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Konwerter plików")
        self.resizable(True, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.source = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.target_format = tk.StringVar()
        self.status = tk.StringVar()
        self.busy = False
        self.result: Path | ConversionError | None = None

        frame = ttk.Frame(self, padding=12)
        frame.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Plik wejściowy:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.source, state="readonly", width=60).grid(row=0, column=1, sticky="ew", padx=6)
        self.source_button = ttk.Button(frame, text="Wybierz plik…", command=self.choose_source)
        self.source_button.grid(row=0, column=2, sticky="ew")

        ttk.Label(frame, text="Katalog zapisu:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.output_dir, state="readonly").grid(row=1, column=1, sticky="ew", padx=6)
        self.dir_button = ttk.Button(frame, text="Wybierz katalog…", command=self.choose_dir)
        self.dir_button.grid(row=1, column=2, sticky="ew")

        ttk.Label(frame, text="Format docelowy:").grid(row=2, column=0, sticky="w", pady=4)
        self.format_box = ttk.Combobox(frame, textvariable=self.target_format, state="disabled", width=10)
        self.format_box.grid(row=2, column=1, sticky="w", padx=6)
        self.format_box.bind("<<ComboboxSelected>>", lambda _: self.on_format_selected())

        ttk.Label(frame, text=f"Obsługiwane konwersje:   {MATRIX}", foreground="gray").grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        ttk.Separator(frame).grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        self.progress = ttk.Progressbar(frame)  # pusty w spoczynku, animowany podczas konwersji
        self.progress.grid(row=5, column=0, columnspan=2, sticky="ew", padx=(0, 6))
        self.convert_button = ttk.Button(frame, text="Konwertuj", command=self.start)
        self.convert_button.grid(row=5, column=2, sticky="ew")
        self.status_label = ttk.Label(frame, textvariable=self.status, wraplength=620)
        self.status_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.set_status("Wybierz plik wejściowy.")
        self.refresh()

    # --- wybór danych -------------------------------------------------------

    def choose_source(self):
        path = filedialog.askopenfilename(
            parent=self, title="Wybierz plik do konwersji",
            filetypes=[("Obsługiwane pliki", " ".join("*" + ext for ext in SOURCE_TYPES)), ("Wszystkie pliki", "*.*")],
        )
        if path:
            self.set_source(Path(path))

    def set_source(self, path: Path):
        self.source.set(str(path))
        if not self.output_dir.get():
            self.output_dir.set(str(path.parent))
        targets = available_targets(path)
        self.format_box["values"] = targets
        self.target_format.set(targets[0] if len(targets) == 1 else "")
        if not targets:
            self.set_status(f"Nieobsługiwany typ pliku: {path.suffix or '(brak rozszerzenia)'}. "
                            f"Wybierz plik: {', '.join(SOURCE_TYPES)}.", error=True)
        elif self.target_format.get():
            self.set_status("Gotowe – kliknij „Konwertuj”.")
        else:
            self.set_status("Wybierz format docelowy.")
        self.refresh()

    def choose_dir(self):
        path = filedialog.askdirectory(parent=self, title="Wybierz katalog zapisu",
                                       initialdir=self.output_dir.get() or None)
        if path:
            self.output_dir.set(str(Path(path)))
            self.refresh()

    def on_format_selected(self):
        self.set_status("Gotowe – kliknij „Konwertuj”.")
        self.refresh()

    # --- konwersja w wątku roboczym ------------------------------------------

    def start(self):
        request = ConversionRequest(Path(self.source.get()), self.target_format.get(), Path(self.output_dir.get()))
        try:
            request.validate()
        except ConversionError as e:
            self.show_error(e)
            return
        overwrite = False
        if request.target.exists():
            answer = messagebox.askyesnocancel(
                "Plik już istnieje",
                f"W katalogu docelowym jest już plik „{request.target.name}”.\n\n"
                f"Tak – nadpisz go\n"
                f"Nie – zapisz jako „{free_path(request.target).name}”\n"
                f"Anuluj – nie konwertuj",
                icon="warning", parent=self,
            )
            if answer is None:
                self.set_status("Anulowano – nic nie zostało zapisane.")
                return
            overwrite = answer

        self.busy = True
        self.refresh()
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        self.set_status(f"Trwa konwersja {request.source.name} → {upper(request.key[1])}…")
        worker = threading.Thread(target=self.work, args=(request, overwrite), daemon=True)
        worker.start()
        self.after(100, self.poll, worker)

    def work(self, request: ConversionRequest, overwrite: bool):
        """Działa w osobnym wątku – nie dotyka widżetów, tylko zapisuje wynik."""
        try:
            self.result = execute(request, overwrite)
        except ConversionError as e:
            self.result = e
        except Exception as e:  # błąd programu nie może zostawić okna w stanie „trwa konwersja”
            log.exception("Nieoczekiwany błąd konwersji")
            self.result = ConversionError(f"Nieoczekiwany błąd: {e}. Szczegóły w pliku konwerter.log.")

    def poll(self, worker: threading.Thread):
        if worker.is_alive():
            self.after(100, self.poll, worker)
            return
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.refresh()
        if isinstance(self.result, Path):
            self.set_status(f"Zapisano: {self.result}")
            messagebox.showinfo("Gotowe", f"Konwersja zakończona.\n\nZapisano plik:\n{self.result}", parent=self)
        else:
            self.show_error(self.result)

    # --- stan okna ----------------------------------------------------------

    def refresh(self):
        """Blokuje kontrolki, których nie wolno teraz użyć."""
        idle = [] if self.busy else ["!disabled"]
        for button in (self.source_button, self.dir_button):
            button.state(idle or ["disabled"])
        self.format_box.configure(state="readonly" if self.format_box["values"] and not self.busy else "disabled")
        ready = self.source.get() and self.output_dir.get() and self.target_format.get() and not self.busy
        self.convert_button.state(["!disabled"] if ready else ["disabled"])

    def set_status(self, text: str, error: bool = False):
        self.status.set(text)
        self.status_label.configure(foreground="#b00020" if error else "")

    def on_close(self):
        if self.busy and not messagebox.askyesno(
            "Trwa konwersja",
            "Konwersja jeszcze trwa. Zamknięcie okna może zostawić niedokończony plik.\n\nZamknąć mimo to?",
            icon="warning", parent=self,
        ):
            return
        self.destroy()

    def show_error(self, error: ConversionError):
        self.set_status(f"Błąd: {error}", error=True)
        messagebox.showerror("Konwersja nie powiodła się", str(error), parent=self)
