"""
src/ui/mcq_overlay.py
Tiny floating MCQ answer overlay. Cross-platform.
"""
from __future__ import annotations

import tkinter as tk
from src.core.overlay_base import BaseOverlay

BG = "#0a0a14"


class MCQOverlay(BaseOverlay):
    def __init__(self):
        super().__init__(
            title="mcq",
            alpha=0.92,
            bg=BG,
            width=90,
            height=44,
            pos_x=-1,
            pos_y=-1,
        )
        self._lbl = None

    def _configure_window(self) -> None:
        super()._configure_window()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"90x44+{sw - 120}+{sh - 120}")

    def _build_content(self) -> None:
        self._lbl = tk.Label(
            self.root,
            text="—",
            bg=BG,
            fg="#00ff88",
            font=("monospace", 14, "bold"),
            justify="center",
        )
        self._lbl.pack(fill="both", expand=True)
        self._bind_drag(self._lbl)

    def set_thinking(self) -> None:
        self.schedule(self._update_main, "...", "#555577")

    def set_answer(self, answer: str) -> None:
        self.schedule(self._update_main, answer, "#00ff88")

    def set_error(self, err_msg: str = "") -> None:
        self.schedule(self._update_main, "ERR", "#ff5555")

    def set_log(self, log_msg: str) -> None:
        pass

    def _update_main(self, text: str, color: str) -> None:
        if self._lbl:
            self._lbl.config(text=text, fg=color)

    def stop(self) -> None:
        if self.root:
            self.schedule(self.root.destroy)
        self.visible = False
