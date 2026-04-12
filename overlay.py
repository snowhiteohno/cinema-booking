import tkinter as tk
from tkinter import font as tkfont
import threading
import ctypes
import ctypes.wintypes
import re

WDA_EXCLUDEFROMCAPTURE   = 0x00000011
DWMWA_WINDOW_CORNER_PREF = 33
DWMWCP_ROUND             = 2


# ── Markdown renderer ────────────────────────────────────────────────────────
class MarkdownRenderer:
    def __init__(self, text_widget: tk.Text):
        self.widget = text_widget
        self._define_tags()

    def _define_tags(self):
        mono = ('Cascadia Code', 10) if 'Cascadia Code' in tkfont.families() else ('Consolas', 10)
        self.widget.tag_configure('h1',          font=('Segoe UI', 18, 'bold'), foreground='#ffffff', spacing3=6)
        self.widget.tag_configure('h2',          font=('Segoe UI', 15, 'bold'), foreground='#e0e0e0', spacing3=4)
        self.widget.tag_configure('h3',          font=('Segoe UI', 12, 'bold'), foreground='#c0c0c0', spacing3=3)
        self.widget.tag_configure('bold',        font=('Segoe UI', 11, 'bold'), foreground='#f0f0f0')
        self.widget.tag_configure('italic',      font=('Segoe UI', 11, 'italic'), foreground='#d0d0d0')
        self.widget.tag_configure('normal',      font=('Segoe UI', 11), foreground='#d0d0d0')
        self.widget.tag_configure('inline_code', font=mono, foreground='#7dd3a8', background='#1a1a2e')
        self.widget.tag_configure('code_block',  font=mono, foreground='#a8d8ea', background='#0f0f1a',
                                  lmargin1=12, lmargin2=12, rmargin=12, spacing1=2, spacing3=2)
        self.widget.tag_configure('code_lang',   font=(mono[0], 9), foreground='#555577', background='#0f0f1a')
        self.widget.tag_configure('divider',     font=('Segoe UI', 4), foreground='#2a2a3a')
        self.widget.tag_configure('bullet',      font=('Segoe UI', 11), foreground='#7c6af7', lmargin1=8, lmargin2=20)

    def render(self, md: str):
        self.widget.configure(state='normal')
        self.widget.delete('1.0', tk.END)

        lines         = md.splitlines()
        i             = 0
        in_code_block = False
        code_lang     = ''
        code_buf      = []

        while i < len(lines):
            line = lines[i]

            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_lang     = line.strip()[3:].strip()
                    code_buf      = []
                else:
                    in_code_block = False
                    if code_lang:
                        self.widget.insert(tk.END, f' {code_lang}\n', 'code_lang')
                    self.widget.insert(tk.END, '\n'.join(code_buf) + '\n', 'code_block')
                    self._ins('\n', 'normal')
                    code_lang = ''
                    code_buf  = []
                i += 1
                continue

            if in_code_block:
                code_buf.append(line)
                i += 1
                continue

            if line.startswith('### '):
                self._ins(line[4:] + '\n', 'h3')
            elif line.startswith('## '):
                self._ins(line[3:] + '\n', 'h2')
            elif line.startswith('# '):
                self._ins(line[2:] + '\n', 'h1')
            elif line.strip() in ('---', '***', '___'):
                self._ins('─' * 55 + '\n', 'divider')
            elif re.match(r'^(\*|-|\+) ', line):
                self._ins('• ', 'bullet')
                self._inline(line[2:])
                self._ins('\n', 'normal')
            elif line.strip() == '':
                self._ins('\n', 'normal')
            else:
                self._inline(line)
                self._ins('\n', 'normal')

            i += 1

        self.widget.configure(state='disabled')
        self.widget.see('1.0')

    def _inline(self, text: str):
        for part in re.split(r'(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)', text):
            if part.startswith('`') and part.endswith('`'):
                self._ins(part[1:-1], 'inline_code')
            elif part.startswith('**') and part.endswith('**'):
                self._ins(part[2:-2], 'bold')
            elif part.startswith('*') and part.endswith('*'):
                self._ins(part[1:-1], 'italic')
            else:
                self._ins(part, 'normal')

    def _ins(self, text, tag):
        self.widget.insert(tk.END, text, tag)


# ── Overlay ──────────────────────────────────────────────────────────────────
class OverlayWindow:
    def __init__(self):
        self.root     = None
        self.renderer = None
        self._ready   = threading.Event()
        self._drag_x  = 0
        self._drag_y  = 0
        self.visible  = False
        self._hwnd    = None

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        self._ready.wait()

    def _run(self):
        self.root = tk.Tk()
        self._build_window()
        self._ready.set()
        self.root.mainloop()

    def _apply_capture_exclusion(self):
        """
        Call this every time the window is shown (deiconify).
        Windows can reset display affinity after window state changes.
        """
        try:
            result = ctypes.windll.user32.SetWindowDisplayAffinity(
                self._hwnd, WDA_EXCLUDEFROMCAPTURE
            )
            if not result:
                print("logs: ⚠️  SetWindowDisplayAffinity failed", flush=True)
        except Exception as e:
            print(f"logs: Capture exclusion error: {e}", flush=True)

    def _build_window(self):
        self.root.title("ai-overlay")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.88)
        self.root.configure(bg='#12121f')
        self.root.withdraw()

        self.root.update()
        self._hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

        # Rounded corners (Windows 11)
        try:
            val = ctypes.c_int(DWMWCP_ROUND)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                self._hwnd, DWMWA_WINDOW_CORNER_PREF,
                ctypes.byref(val), ctypes.sizeof(val)
            )
        except Exception:
            pass

        # Apply capture exclusion once at build time
        self._apply_capture_exclusion()

        # ── Layout ──────────────────────────────────────────────────────────
        outer = tk.Frame(self.root, bg='#2a2a4a', padx=1, pady=1)
        outer.pack(fill='both', expand=True)

        inner = tk.Frame(outer, bg='#12121f', padx=14, pady=10)
        inner.pack(fill='both', expand=True)

        header = tk.Frame(inner, bg='#12121f')
        header.pack(fill='x', pady=(0, 8))

        tk.Label(
            header, text="✦  AI",
            bg='#12121f', fg='#7c6af7',
            font=('Segoe UI', 10, 'bold')
        ).pack(side='left')

        tk.Label(
            header, text="Ctrl+/ to hide",
            bg='#12121f', fg='#2a2a4a',
            font=('Segoe UI', 9)
        ).pack(side='right', padx=(0, 8))

        close_btn = tk.Label(
            header, text=" ✕ ",
            bg='#12121f', fg='#333355',
            font=('Segoe UI', 10), cursor='hand2'
        )
        close_btn.pack(side='right')
        close_btn.bind('<Button-1>', lambda e: self.hide())
        close_btn.bind('<Enter>',    lambda e: close_btn.config(fg='#ff5555'))
        close_btn.bind('<Leave>',    lambda e: close_btn.config(fg='#333355'))

        tk.Frame(inner, bg='#1e1e35', height=1).pack(fill='x', pady=(0, 8))

        text_frame = tk.Frame(inner, bg='#12121f')
        text_frame.pack(fill='both', expand=True)

        scrollbar = tk.Scrollbar(
            text_frame, bg='#1e1e35', troughcolor='#12121f',
            activebackground='#7c6af7', relief='flat', bd=0, width=5
        )
        scrollbar.pack(side='right', fill='y')

        self.text_area = tk.Text(
            text_frame,
            bg='#12121f', fg='#d0d0d0',
            font=('Segoe UI', 11),
            wrap=tk.WORD, relief='flat', bd=0,
            cursor='arrow', state='disabled',
            width=52, height=22,
            yscrollcommand=scrollbar.set,
            padx=4, pady=4,
            selectbackground='#2a2a4a',
        )
        self.text_area.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.text_area.yview)

        self.renderer = MarkdownRenderer(self.text_area)

        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"580x480+{sw - 610}+24")

        for widget in (header,):
            widget.bind('<Button-1>',  self._drag_start)
            widget.bind('<B1-Motion>', self._drag_move)

    def show(self, md_text: str = None):
        if not self.root:
            return
        def _update():
            if md_text is not None:
                self.renderer.render(md_text)
            self.root.deiconify()
            self.root.lift()
            self.root.update()
            # Re-apply every time we show — Windows may reset it after deiconify
            self._apply_capture_exclusion()
            self.visible = True
        self.root.after(0, _update)

    def hide(self):
        if not self.root:
            return
        def _hide():
            self.root.withdraw()
            self.visible = False
        self.root.after(0, _hide)

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")