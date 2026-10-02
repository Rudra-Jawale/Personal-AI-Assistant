"""
AVA — Personal AI Assistant
Launch with: python start_ava.py   or   AVA.bat
"""

from __future__ import annotations

import math
import queue
import threading
import time
from datetime import datetime

import customtkinter as ctk

from main import (
    Ava,
    ava_greeting,
    is_exit_command,
    is_sleep_command,
    is_wake_command,
    normalize_command,
    strip_wake_phrase,
)
from speak import speak
from windows_integration import (
    is_start_with_windows,
    make_tray_image,
    set_start_with_windows,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#05070c",
    "sidebar": "#080d16",
    "surface": "#101826",
    "surface_light": "#182233",
    "accent": "#2ee6c7",
    "accent_dim": "#1bb39a",
    "accent2": "#7c5cff",
    "user_bubble": "#2563eb",
    "ava_bubble": "#121c2b",
    "text": "#e8eef7",
    "text_dim": "#8b9bb4",
    "danger": "#f43f5e",
    "warn": "#fbbf24",
}


class MessageBubble(ctk.CTkFrame):
    def __init__(self, master, sender, text, timestamp=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        is_user = sender == "user"
        bubble_color = COLORS["user_bubble"] if is_user else COLORS["ava_bubble"]
        border = COLORS["accent"] if not is_user else COLORS["user_bubble"]
        anchor = "e" if is_user else "w"
        padx = (90, 10) if is_user else (10, 90)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=5)

        bubble = ctk.CTkFrame(
            row,
            fg_color=bubble_color,
            corner_radius=18,
            border_width=1,
            border_color=border,
        )
        bubble.pack(anchor=anchor, padx=padx)

        ctk.CTkLabel(
            bubble,
            text=text,
            wraplength=460,
            justify="left",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=12)

        time_str = timestamp or datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            row,
            text=f"{'You' if is_user else 'AVA'}  ·  {time_str}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(anchor=anchor, padx=padx[0 if is_user else 1])


class AvaUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AVA")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(fg_color=COLORS["bg"])

        self.ava = None
        self.active = True
        self.voice_enabled = ctk.BooleanVar(value=True)
        self.wake_enabled = ctk.BooleanVar(value=True)
        self.start_windows = ctk.BooleanVar(value=is_start_with_windows())
        self.ui_queue = queue.Queue()
        self.listening = False
        self.processing = False
        self._stop_wake = threading.Event()
        self._orb_phase = 0
        self.tray_icon = None

        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.bind("<Unmap>", self._on_unmap)

        self._build_layout()
        self._show_welcome()
        self.after(80, self._process_ui_queue)
        self.after(40, self._animate_orb)
        threading.Thread(target=self._initialize_ava, daemon=True).start()
        threading.Thread(target=self._start_tray, daemon=True).start()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=292, fg_color=COLORS["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        hero = ctk.CTkFrame(sidebar, fg_color="transparent")
        hero.pack(fill="x", padx=22, pady=(26, 8))

        self.orb = ctk.CTkCanvas(
            hero,
            width=92,
            height=92,
            bg=COLORS["sidebar"],
            highlightthickness=0,
        )
        self.orb.pack()
        self._draw_orb(0.55)

        ctk.CTkLabel(
            hero,
            text="AVA",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(10, 0))
        ctk.CTkLabel(
            hero,
            text="Always listening  ·  Ay-va",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack()

        self.status_label = ctk.CTkLabel(
            sidebar,
            text="Starting up…",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["accent"],
        )
        self.status_label.pack(anchor="w", padx=22, pady=(18, 6))

        self.hint_label = ctk.CTkLabel(
            sidebar,
            text="Say  “Hey AVA”  to wake me",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
            wraplength=240,
            justify="left",
        )
        self.hint_label.pack(anchor="w", padx=22, pady=(0, 18))

        ctk.CTkLabel(
            sidebar,
            text="QUICK ACTIONS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=22, pady=(4, 8))

        quick_actions = [
            ("Ask the time", "what time is it"),
            ("Today’s date", "what is the date"),
            ("Open Calculator", "open calculator"),
            ("Open Chrome", "open chrome"),
            ("Search the web", "search python tutorials"),
            ("What do you know?", "what do you know about me"),
        ]
        for label, cmd in quick_actions:
            ctk.CTkButton(
                sidebar,
                text=label,
                fg_color=COLORS["surface"],
                hover_color=COLORS["surface_light"],
                text_color=COLORS["text"],
                anchor="w",
                height=34,
                corner_radius=10,
                command=lambda c=cmd: self._quick_action(c),
            ).pack(fill="x", padx=18, pady=2)

        settings = ctk.CTkFrame(sidebar, fg_color=COLORS["surface"], corner_radius=16)
        settings.pack(fill="x", padx=18, pady=(20, 10))

        ctk.CTkLabel(
            settings,
            text="Assistant",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkSwitch(
            settings,
            text="Hey AVA wake word",
            variable=self.wake_enabled,
            progress_color=COLORS["accent"],
            command=self._on_wake_toggle,
        ).pack(anchor="w", padx=14, pady=4)
        ctk.CTkSwitch(
            settings,
            text="Speak replies",
            variable=self.voice_enabled,
            progress_color=COLORS["accent"],
        ).pack(anchor="w", padx=14, pady=4)
        ctk.CTkSwitch(
            settings,
            text="Start with Windows",
            variable=self.start_windows,
            progress_color=COLORS["accent"],
            command=self._toggle_startup,
        ).pack(anchor="w", padx=14, pady=4)

        ctk.CTkButton(
            settings,
            text="Hide to tray",
            fg_color=COLORS["surface_light"],
            hover_color=COLORS["accent_dim"],
            height=32,
            command=self._hide_to_tray,
        ).pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkButton(
            settings,
            text="Clear chat",
            fg_color=COLORS["surface_light"],
            hover_color=COLORS["accent2"],
            height=32,
            command=self._clear_session,
        ).pack(fill="x", padx=14, pady=(0, 12))

    def _build_main_panel(self):
        main = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color=COLORS["surface"], height=64, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="Conversation",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=24, pady=16)

        self.mode_label = ctk.CTkLabel(
            header,
            text="Hands-free",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["accent"],
            fg_color=COLORS["surface_light"],
            corner_radius=16,
            width=110,
            height=28,
        )
        self.mode_label.pack(side="right", padx=20, pady=16)

        self.chat_frame = ctk.CTkScrollableFrame(
            main,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["surface_light"],
            scrollbar_button_hover_color=COLORS["accent_dim"],
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        input_bar = ctk.CTkFrame(main, fg_color=COLORS["surface"], corner_radius=0, height=88)
        input_bar.grid(row=2, column=0, sticky="ew")
        input_bar.grid_propagate(False)
        input_bar.grid_columnconfigure(1, weight=1)

        self.mic_btn = ctk.CTkButton(
            input_bar,
            text="●",
            width=52,
            height=52,
            font=ctk.CTkFont(size=22),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            text_color=COLORS["bg"],
            corner_radius=26,
            command=self._toggle_listen,
        )
        self.mic_btn.grid(row=0, column=0, padx=(18, 10), pady=18)

        self.input_entry = ctk.CTkEntry(
            input_bar,
            placeholder_text="Ask AVA anything, or say Hey AVA…",
            height=52,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["surface_light"],
            border_color=COLORS["surface_light"],
            corner_radius=16,
        )
        self.input_entry.grid(row=0, column=1, sticky="ew", pady=18)
        self.input_entry.bind("<Return>", lambda e: self._send_text())

        self.send_btn = ctk.CTkButton(
            input_bar,
            text="Send",
            width=96,
            height=52,
            fg_color=COLORS["accent2"],
            hover_color="#6848e6",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=16,
            command=self._send_text,
        )
        self.send_btn.grid(row=0, column=2, padx=(10, 18), pady=18)

    def _draw_orb(self, intensity):
        self.orb.delete("all")
        cx, cy = 46, 46
        glow = 28 + int(16 * intensity)
        self.orb.create_oval(cx - glow, cy - glow, cx + glow, cy + glow, fill="#0e2a28", outline="")
        self.orb.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, fill=COLORS["accent"], outline="")
        self.orb.create_oval(cx - 10, cy - 14, cx + 6, cy + 2, fill="#9ff7e8", outline="")

    def _animate_orb(self):
        listening = self.listening or (self.wake_enabled.get() and not self.processing)
        step = 0.12 if listening else 0.04
        self._orb_phase = (self._orb_phase + step) % 6.28
        intensity = 0.45 + 0.55 * abs(math.sin(self._orb_phase))
        if self.processing:
            intensity = 0.9
        self._draw_orb(intensity)
        self.after(50, self._animate_orb)

    def _show_welcome(self):
        welcome = ctk.CTkFrame(self.chat_frame, fg_color=COLORS["surface"], corner_radius=20)
        welcome.pack(fill="x", padx=14, pady=16)

        ctk.CTkLabel(
            welcome,
            text="AVA",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(padx=22, pady=(20, 6))
        ctk.CTkLabel(
            welcome,
            text=(
                # "AVA stays in the background like Siri. Close this window to hide it in the tray.\n"
                # "Then just say “Hey AVA” — no need to run Python files again.\n\n"
                # "Try: open calculator  ·  what’s the weather  ·  search AI news"
            ),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
            justify="left",
        ).pack(padx=22, pady=(0, 20))

    def _initialize_ava(self):
        try:
            ava = Ava(calibrate_mic=False)
            greeting = ava_greeting()
            self.ui_queue.put(("ready", ava, greeting))
        except Exception as exc:
            self.ui_queue.put(("error", str(exc)))

    def _start_tray(self):
        try:
            import pystray

            image = make_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Open AVA", self._show_from_tray, default=True),
                pystray.MenuItem("Listen now", self._tray_listen),
                pystray.MenuItem("Quit AVA", self._quit_app),
            )
            self.tray_icon = pystray.Icon("AVA", image, "AVA Assistant", menu)
            self.tray_icon.run()
        except Exception as exc:
            print(f"Tray icon unavailable: {exc}")

    def _show_from_tray(self, *_args):
        self.after(0, self._restore_window)

    def _tray_listen(self, *_args):
        self.after(0, self._restore_window)
        self.after(400, self._toggle_listen)

    def _restore_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        try:
            self.attributes("-topmost", True)
            self.after(400, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def _hide_to_tray(self):
        self.withdraw()
        self.ui_queue.put(("status", "Hidden — say Hey AVA", COLORS["accent"]))

    def _on_unmap(self, _event):
        return

    def _quit_app(self, *_args):
        self._stop_wake.set()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.after(0, self.destroy)

    def _toggle_startup(self):
        message = set_start_with_windows(self.start_windows.get())
        self._add_message("ava", message)

    def _on_wake_toggle(self):
        if self.wake_enabled.get():
            self.ui_queue.put(("status", "Listening for Hey AVA", COLORS["accent"]))
            self.ui_queue.put(("mode", "Hands-free"))
        else:
            self.ui_queue.put(("status", "Wake word off", COLORS["warn"]))
            self.ui_queue.put(("mode", "Manual"))

    def _process_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                kind = msg[0]
                if kind == "ready":
                    self.ava = msg[1]
                    greeting = msg[2]
                    self.status_label.configure(text="Listening for Hey AVA", text_color=COLORS["accent"])
                    self._add_message("ava", greeting)
                    if self.voice_enabled.get():
                        threading.Thread(target=lambda: self._speak(greeting), daemon=True).start()
                    threading.Thread(target=self._wake_loop, daemon=True).start()
                elif kind == "error":
                    self.status_label.configure(text="Error", text_color=COLORS["danger"])
                    self._add_message("ava", f"Failed to initialize: {msg[1]}")
                elif kind == "message":
                    self._add_message(msg[1], msg[2])
                elif kind == "status":
                    self.status_label.configure(text=msg[1], text_color=msg[2])
                elif kind == "mode":
                    self.mode_label.configure(text=msg[1])
                elif kind == "input_enable":
                    self._set_input_enabled(msg[1])
                elif kind == "bring_front":
                    self._restore_window()
        except queue.Empty:
            pass
        self.after(80, self._process_ui_queue)

    def _speak(self, text):
        if self.ava:
            self.ava.voice.set_speaking(True)
        try:
            speak(text)
        finally:
            time.sleep(0.35)
            if self.ava:
                self.ava.voice.set_speaking(False)

    def _wake_loop(self):
        while not self._stop_wake.is_set():
            if not self.ava or not self.ava.voice.available:
                time.sleep(0.5)
                continue
            if not self.wake_enabled.get() or self.processing or self.listening:
                time.sleep(0.2)
                continue
            text = self.ava.voice.listen_for_wake(
                self._stop_wake,
                should_skip=lambda: self.processing or self.listening or not self.wake_enabled.get(),
            )
            if not text or self._stop_wake.is_set():
                continue
            if not is_wake_command(text):
                continue
            self.ui_queue.put(("bring_front",))
            rest = strip_wake_phrase(text)
            if rest and not is_wake_command(rest):
                self.ui_queue.put(("status", "Working…", COLORS["accent"]))
                self._process_command_thread(rest)
            else:
                self.listening = True
                self.ui_queue.put(("status", "Yes? I'm listening", COLORS["accent"]))
                self.ui_queue.put(("mode", "Listening"))
                if self.voice_enabled.get():
                    self._speak("Yes?")
                follow = self.ava.listen(timeout=8, phrase_time_limit=12)
                self.listening = False
                if follow:
                    self._process_command_thread(follow)
                else:
                    self.ui_queue.put(("status", "Listening for Hey AVA", COLORS["accent"]))
                    self.ui_queue.put(("mode", "Hands-free"))
                    self.ui_queue.put(("input_enable", True))

    def _add_message(self, sender, text):
        bubble = MessageBubble(self.chat_frame, sender, text)
        bubble.pack(fill="x")
        self.after(40, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def _set_input_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.input_entry.configure(state=state)
        self.send_btn.configure(state=state)
        self.mic_btn.configure(state=state)
        self.processing = not enabled
        if enabled:
            self.mic_btn.configure(text="●", fg_color=COLORS["accent"])
            self.listening = False

    def _quick_action(self, command):
        self._restore_window()
        self._handle_command(command)

    def _send_text(self):
        text = self.input_entry.get().strip()
        if not text or self.processing:
            return
        self.input_entry.delete(0, "end")
        self._handle_command(text)

    def _toggle_listen(self):
        if self.processing or self.listening or not self.ava:
            return
        if not self.ava.voice.available:
            self._add_message("ava", "Voice input is unavailable. Please type instead.")
            return
        self.listening = True
        self.mic_btn.configure(text="…", fg_color=COLORS["danger"])
        self.ui_queue.put(("status", "Listening…", COLORS["accent"]))
        threading.Thread(target=self._listen_and_process, daemon=True).start()

    def _listen_and_process(self):
        try:
            text = self.ava.listen()
            if text:
                self.ui_queue.put(("status", "Working…", COLORS["accent"]))
                self._process_command_thread(text)
            else:
                self.ui_queue.put(("status", "Listening for Hey AVA", COLORS["accent"]))
                self.ui_queue.put(("input_enable", True))
        except Exception as exc:
            self.ui_queue.put(("message", "ava", f"Voice error: {exc}"))
            self.ui_queue.put(("status", "Listening for Hey AVA", COLORS["accent"]))
            self.ui_queue.put(("input_enable", True))

    def _handle_command(self, text):
        if not self.ava:
            self._add_message("ava", "Still starting. Please wait a moment.")
            return
        self.ui_queue.put(("input_enable", False))
        self.ui_queue.put(("status", "Working…", COLORS["accent"]))
        threading.Thread(target=self._process_command_thread, args=(text,), daemon=True).start()

    def _process_command_thread(self, raw_text):
        try:
            command = normalize_command(raw_text)
            self.ui_queue.put(("input_enable", False))
            self.ui_queue.put(("message", "user", raw_text.strip()))

            if is_exit_command(command):
                self.ui_queue.put(("message", "ava", "Goodbye. I'll hide in the tray. Say Hey AVA anytime."))
                if self.voice_enabled.get():
                    self._speak("I'll be in the background. Say Hey AVA when you need me.")
                self.ui_queue.put(("status", "Hidden — say Hey AVA", COLORS["accent"]))
                self.after(600, self._hide_to_tray)
                return

            if is_sleep_command(command):
                self.ava.brain.clear_session()
                response = "I'll keep listening for Hey AVA in the background."
                self.ui_queue.put(("mode", "Hands-free"))
            elif is_wake_command(command):
                rest = strip_wake_phrase(command)
                if rest:
                    response = self.ava.process_command(rest)
                else:
                    response = "I'm here. What can I do?"
                self.ui_queue.put(("mode", "Active"))
            else:
                response = self.ava.process_command(command)
                self.ui_queue.put(("mode", "Active"))

            self.ui_queue.put(("message", "ava", response))
            self.ui_queue.put(("status", "Listening for Hey AVA", COLORS["accent"]))
            if self.voice_enabled.get():
                self._speak(response)
        except Exception as exc:
            self.ui_queue.put(("message", "ava", f"Error: {exc}"))
            self.ui_queue.put(("status", "Listening for Hey AVA", COLORS["accent"]))
        finally:
            self.ui_queue.put(("input_enable", True))
            self.ui_queue.put(("mode", "Hands-free"))

    def _clear_session(self):
        if self.ava:
            self.ava.brain.clear_session()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self._show_welcome()
        if self.ava:
            self._add_message("ava", "Chat cleared. Say Hey AVA when you need me.")


def main():
    app = AvaUI()
    app.mainloop()


if __name__ == "__main__":
    main()
