import tkinter as tk
from tkinter import scrolledtext
import threading
import ctypes

WDA_EXCLUDEFROMCAPTURE = 0x00000011

class OverlayWindow:
    def __init__(self):
        self.root      = None
        self._ready    = threading.Event()
        self._drag_x   = 0
        self._drag_y   = 0

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        self._ready.wait()

    def _run(self):
        self.root = tk.Tk()
        self._build_window()
        self._ready.set()
        self.root.mainloop()

    def _build_window(self):
        self.root.title("ai-overlay")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='#0d0d0d')
        self.root.withdraw()

        # ── Border frame ────────────────────────────────────────────────────
        outer = tk.Frame(self.root, bg='#00ff88', padx=1, pady=1)
        outer.pack(fill='both', expand=True)

        inner = tk.Frame(outer, bg='#0d0d0d', padx=12, pady=10)
        inner.pack(fill='both', expand=True)

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(inner, bg='#0d0d0d')
        header.pack(fill='x', pady=(0, 6))

        title = tk.Label(
            header, text="⬤  AI Response",
            bg='#0d0d0d', fg='#00ff88',
            font=('Consolas', 10, 'bold')
        )
        title.pack(side='left')

        close_btn = tk.Label(
            header, text="  ✕  ",
            bg='#0d0d0d', fg='#666666',
            font=('Consolas', 10, 'bold'),
            cursor='hand2'
        )
        close_btn.pack(side='right')
        close_btn.bind('<Button-1>', lambda e: self.hide())
        close_btn.bind('<Enter>',    lambda e: close_btn.config(fg='#ff4444'))
        close_btn.bind('<Leave>',    lambda e: close_btn.config(fg='#666666'))

        tk.Frame(inner, bg='#1e1e1e', height=1).pack(fill='x', pady=(0, 8))

        # ── Scrollable text area ─────────────────────────────────────────────
        self.text_area = scrolledtext.ScrolledText(
            inner,
            bg='#0d0d0d', fg='#f0f0f0',
            font=('Consolas', 11),
            wrap=tk.WORD,
            relief='flat',
            bd=0,
            cursor='arrow',
            state='disabled',
            width=52,
            height=20
        )
        self.text_area.pack(fill='both', expand=True)

        # Style the scrollbar
        self.text_area.vbar.configure(
            bg='#1e1e1e',
            troughcolor='#0d0d0d',
            activebackground='#00ff88'
        )

        # ── Position top-right ───────────────────────────────────────────────
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"560x420+{sw - 590}+24")

        # ── Drag bindings on header only ─────────────────────────────────────
        for widget in (header, title):
            widget.bind('<Button-1>',  self._drag_start)
            widget.bind('<B1-Motion>', self._drag_move)

        self.root.bind('<Escape>', lambda e: self.hide())

        # ── Hide from screen capture ─────────────────────────────────────────
        self.root.update()
        try:
            hwnd   = ctypes.windll.user32.GetParent(self.root.winfo_id())
            result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            status = "✅ hidden from screen capture" if result else "⚠️ capture exclusion failed"
            print(f"logs: Overlay {status}", flush=True)
        except Exception as e:
            print(f"logs: Capture exclusion error: {e}", flush=True)

    def show(self, text: str):
        if not self.root:
            return

        def _update():
            self.text_area.configure(state='normal')
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert(tk.END, text)
            self.text_area.configure(state='disabled')
            self.text_area.see('1.0')   # scroll back to top
            self.root.deiconify()
            self.root.lift()

        self.root.after(0, _update)

    def hide(self):
        if self.root:
            self.root.after(0, self.root.withdraw)

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")