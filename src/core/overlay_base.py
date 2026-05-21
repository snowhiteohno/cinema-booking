"""
src/core/overlay_base.py
Base Tkinter floating window: always-on-top, drag, configurable alpha/colors.
Cross-platform (Windows, Linux, macOS).
"""
from __future__ import annotations

import threading
from typing import Optional

import tkinter as tk


class BaseOverlay:
    def __init__(self, title: str = "overlay", alpha: float = 0.92,
                 bg: str = "#0e0e1a", width: int = 580, height: int = 560,
                 pos_x: int = -1, pos_y: int = 24):
        self.title   = title
        self.alpha   = alpha
        self.bg      = bg
        self.width   = width
        self.height  = height
        self.pos_x   = pos_x
        self.pos_y   = pos_y

        self.root:    Optional[tk.Tk] = None
        self._ready   = threading.Event()
        self.visible: bool = False
        self._drag_x  = 0
        self._drag_y  = 0

    def start(self) -> None:
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        self._ready.wait()

    def _run(self) -> None:
        self.root = tk.Tk()
        self._configure_window()
        self._build_content()
        self._ready.set()
        self.root.mainloop()

    def _configure_window(self) -> None:
        self.root.title(self.title)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", self.alpha)
        except Exception:
            pass
        self.root.configure(bg=self.bg)
        self.root.withdraw()

        sw = self.root.winfo_screenwidth()
        x  = (sw - self.width - 30) if self.pos_x < 0 else self.pos_x
        self.root.geometry(f"{self.width}x{self.height}+{x}+{self.pos_y}")

    def _build_content(self) -> None:
        pass

    def _bind_drag(self, widget: tk.Widget) -> None:
        widget.bind("<Button-1>",  self._drag_start)
        widget.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event) -> None:
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def show(self) -> None:
        if not self.root:
            return
        def _u():
            self.root.deiconify()
            self.root.lift()
            self.root.update()
            self.visible = True
        self.root.after(0, _u)

    def hide(self) -> None:
        if not self.root:
            return
        def _u():
            self.root.withdraw()
            self.visible = False
        self.root.after(0, _u)

    def toggle(self) -> None:
        if self.visible:
            self.hide()
        else:
            self.show()

    def schedule(self, fn, *args) -> None:
        if self.root:
            self.root.after(0, lambda: fn(*args))
