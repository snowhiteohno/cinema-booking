"""
src/agents/mcq_agent.py
Screenshot → Gemini → MCQ answer on transparent overlay.
Migrated from mcq/main.py.
"""
from __future__ import annotations

import re
import threading
from typing import List

from src.agents.base_agent import BaseAgent, HotkeyDef
from src.core.gemini_client import GeminiClient
from src.core.screenshot import take_screenshot

PROMPT = (
    "You are an expert at solving multiple choice questions. "
    "Carefully read the question and ALL options in the screenshot, then select the correct answer(s).\n\n"
    "CRITICAL: First count how many options are shown. If there are 4 options, valid letters are ONLY A, B, C, D. "
    "If there are 3 options, valid letters are ONLY A, B, C. NEVER use a letter that does not correspond to an "
    "actual option visible in the screenshot. Do not invent options that are not there.\n\n"
    "Think through each option before deciding. Then on the VERY LAST LINE of your response, "
    "write ONLY the answer in this exact format:\n"
    "  Single answer:             B\n"
    "  Multiple correct options:  A,C\n"
    "  Multiple questions:        B|A,C|D   (one group per question, separated by |)\n\n"
    "The last line must contain ONLY letters that label actual options, commas, and pipes — nothing else."
)


class MCQAgent(BaseAgent):

    def get_name(self) -> str:
        return "MCQ AI"

    def get_description(self) -> str:
        return "Multiple-choice questions → answer shown on a tiny transparent overlay."

    def get_default_hotkeys(self) -> List[HotkeyDef]:
        return [
            HotkeyDef("k+,", "Add MCQ screenshot"),
            HotkeyDef("k+.", "Send to Gemini → show answer"),
            HotkeyDef("k+/", "Clear queue"),
            HotkeyDef("m+n", "Toggle overlay"),
        ]

    def _register_hotkeys(self) -> None:
        hk = self._config.hotkeys
        self._hotkeys.register(hk.add_screenshot, self._add_to_queue)
        self._hotkeys.register(hk.send,           self._send_queue)
        self._hotkeys.register(hk.clear_queue,    self._clear_queue)
        self._hotkeys.register(hk.toggle_overlay, self._toggle_overlay)

    def _run(self) -> None:
        from src.ui.mcq_overlay import MCQOverlay
        self._gemini     = GeminiClient(self._config.api_key, self._config.models)
        self._overlay    = MCQOverlay()
        self._overlay.start()
        self._queue:     list = []
        self._q_lock     = threading.Lock()
        self._processing = False
        print("🎯  MCQAgent ready.", flush=True)
        print("    k+,  Add    k+.  Send    m+n  Toggle overlay", flush=True)

    def stop(self) -> None:
        if self._overlay:
            self._overlay.stop()
        super().stop()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_to_queue(self) -> None:
        import time
        was_visible = hasattr(self, '_overlay') and self._overlay and self._overlay.visible
        if was_visible:
            self._overlay.hide()
            time.sleep(0.15)
        img = take_screenshot()
        if was_visible:
            self._overlay.show()
        with self._q_lock:
            self._queue.append(img)
            n = len(self._queue)
        print(f"Screenshot #{n} queued.", flush=True)

    def _send_queue(self) -> None:
        with self._q_lock:
            if not self._queue:
                print("⚠️  Queue empty.", flush=True)
                if hasattr(self, '_overlay') and self._overlay:
                    self._overlay.set_log("Queue empty")
                return
            imgs, self._queue = list(self._queue), []

        if self._processing:
            return
        self._processing = True

        def _run():
            try:
                if hasattr(self, '_overlay') and self._overlay:
                    self._overlay.set_thinking()
                answer = self._gemini.generate(
                    [PROMPT] + imgs,
                    models=["gemini-3.1-pro", "gemini-3-pro", "gemini-2.5-pro", "gemini-2.5-flash"],
                    thinking=True,
                )
                answer = self._clean_mcq(answer)
                if hasattr(self, '_overlay') and self._overlay:
                    self._overlay.set_answer(answer)
                print(f"✅  MCQ answer: {answer}", flush=True)
            except Exception as e:
                if hasattr(self, '_overlay') and self._overlay:
                    # Provide snippet of error to the UI
                    err_str = str(e)
                    short_err = err_str if len(err_str) < 30 else err_str[:27] + "..."
                    self._overlay.set_error(short_err)
                print(f"❌  {e}", flush=True)
            finally:
                self._processing = False

        threading.Thread(target=_run, daemon=True).start()

    def _clear_queue(self) -> None:
        with self._q_lock:
            n, self._queue = len(self._queue), []
        print(f"🗑️  Cleared {n}.", flush=True)
        if hasattr(self, '_overlay') and self._overlay:
            self._overlay.set_log("Queue cleared")

    def _toggle_overlay(self) -> None:
        self._overlay.toggle()

    @staticmethod
    def _clean_mcq(answer: str) -> str:
        answer = answer.strip().upper()

        # Scan from the bottom — Gemini 2.5 puts its actual answer last after thinking.
        # Accept any line that is ONLY letters A-G with commas and pipes.
        for line in reversed(answer.splitlines()):
            line = line.strip()
            if re.match(r'^[A-G]([,|][A-G])*$', line):
                return line

        # Look for first standalone clean pattern: A  or  A,C  or  B|A,C
        m = re.search(r'\b([A-G](?:[,|][A-G])*)\b', answer)
        if m:
            return m.group(1)

        # Last resort: first letter A-G that stands alone
        m = re.search(r'\b([A-G])\b', answer)
        if m:
            return m.group(1)

        m = re.search(r'[A-G]', answer)
        return m.group(0) if m else "?"
