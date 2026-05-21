"""
src/agents/combo_agent.py
MCQ + AutoType in one process. Press m+m to toggle between modes.
Shared hotkeys (k+, / k+. / k+/) route to whichever agent is active.
"""
from __future__ import annotations

from typing import List

from src.agents.base_agent import BaseAgent, HotkeyDef
from src.agents.mcq_agent import MCQAgent
from src.agents.autotype_agent import AutoTypeAgent


class ComboAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self._mcq  = MCQAgent()
        self._at   = AutoTypeAgent()
        self._mode = "mcq"

    def get_name(self) -> str:
        return "MCQ + AutoType"

    def get_description(self) -> str:
        return "MCQ overlay + auto-typing in one. Press m+m to toggle modes."

    def get_default_hotkeys(self) -> List[HotkeyDef]:
        return [
            HotkeyDef("k+,",  "Add screenshot  (routes to active mode)"),
            HotkeyDef("k+.",  "Send to Gemini  (routes to active mode)"),
            HotkeyDef("k+/",  "Clear queue     (routes to active mode)"),
            HotkeyDef("f+g",  "Toggle MCQ ↔ AutoType mode"),
            HotkeyDef("m+n",  "Toggle MCQ overlay"),
            HotkeyDef("a+s",  "Pause / Resume typing"),
            HotkeyDef("k+x",  "Stop typing immediately"),
        ]

    def _register_hotkeys(self) -> None:
        hk = self._config.hotkeys
        self._hotkeys.register(hk.add_screenshot, self._add)
        self._hotkeys.register(hk.send,           self._send)
        self._hotkeys.register(hk.clear_queue,    self._clear)
        self._hotkeys.register("f+g",             self._toggle_mode)
        self._hotkeys.register(hk.toggle_overlay, self._mcq._toggle_overlay)
        self._hotkeys.register(hk.pause_typing,   self._at._toggle_pause)
        self._hotkeys.register(hk.stop_typing,    self._at._stop)

    def _run(self) -> None:
        # Bootstrap sub-agents: inject config/hotkeys and call _run() directly
        # so they set up their internal state without re-registering hotkeys.
        for agent in (self._mcq, self._at):
            agent._config  = self._config
            agent._hotkeys = self._hotkeys
            agent._run()

        print("🔀  Combo agent ready.  Active mode: MCQ", flush=True)
        print("    f+g  Toggle mode   k+,  Add   k+.  Send   k+/  Clear", flush=True)
        print("    m+n  MCQ overlay   a+s  Pause   k+x  Stop typing", flush=True)

    def stop(self) -> None:
        self._mcq.stop()
        self._at.stop()
        super().stop()

    # ── Routing ───────────────────────────────────────────────────────────────

    def _add(self) -> None:
        if self._mode == "mcq":
            self._mcq._add_to_queue()
        else:
            self._at._add_to_queue()

    def _send(self) -> None:
        if self._mode == "mcq":
            self._mcq._send_queue()
        else:
            self._at._send_queue()

    def _clear(self) -> None:
        if self._mode == "mcq":
            self._mcq._clear_queue()
        else:
            self._at._clear_queue()

    def _toggle_mode(self) -> None:
        self._mode = "autotype" if self._mode == "mcq" else "mcq"
        if self._mode == "autotype":
            label, color = "AUTO-TYPE", "#ffaa00"
        else:
            label, color = "MCQ", "#00ff88"
        print(f"\n{'═'*40}", flush=True)
        print(f"  MODE → {label}", flush=True)
        print(f"{'═'*40}\n", flush=True)
        if hasattr(self._mcq, '_overlay') and self._mcq._overlay:
            self._mcq._overlay.set_answer(label[:3])
            # recolor via schedule
            overlay = self._mcq._overlay
            def _recolor():
                if overlay._lbl:
                    overlay._lbl.config(fg=color)
            overlay.schedule(_recolor)
