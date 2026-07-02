"""
AVA — Personal AI Assistant Desktop UI
Run with: python ui.py
"""

import queue
import threading
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from main import (
    Ava,
    ava_greeting,
    is_exit_command,
    is_sleep_command,
    is_wake_command,
    normalize_command,
)
from speak import speak

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#0f1419",
    "sidebar": "#151b23",
    "surface": "#1c2430",
    "surface_light": "#243040",
    "accent": "#00d4aa",
    "accent_dim": "#00a888",
    "user_bubble": "#2563eb",
    "ava_bubble": "#1e293b",
    "text": "#e2e8f0",
    "text_dim": "#94a3b8",
    "danger": "#ef4444",
}


class MessageBubble(ctk.CTkFrame):
    def __init__(self, master, sender, text, timestamp=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        is_user = sender == "user"
        bubble_color = COLORS["user_bubble"] if is_user else COLORS["ava_bubble"]
        anchor = "e" if is_user else "w"
        padx = (80, 8) if is_user else (8, 80)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)

        bubble = ctk.CTkFrame(row, fg_color=bubble_color, corner_radius=16)
        bubble.pack(anchor=anchor, padx=padx)

        label = ctk.CTkLabel(
            bubble,
            text=text,
            wraplength=420,
            justify="left",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text"],
        )
        label.pack(padx=14, pady=10)

        time_str = timestamp or datetime.now().strftime("%H:%M")
        meta = ctk.CTkLabel(
            row,
            text=f"{'You' if is_user else 'AVA'} · {time_str}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )
        meta.pack(anchor=anchor, padx=padx[0 if is_user else 1])


class AvaUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AVA — Personal AI Assistant")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg"])

        self.ava = None
        self.active = True
        self.voice_enabled = ctk.BooleanVar(value=True)
        self.ui_queue = queue.Queue()
        self.listening = False
        self.processing = False

        self._build_layout()
        self._show_welcome()
        self.after(100, self._process_ui_queue)
        threading.Thread(target=self._initialize_ava, daemon=True).start()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=260, fg_color=COLORS["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(28, 8))

        ctk.CTkLabel(
            logo_frame,
            text="AVA",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Advanced Virtual Assistant",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w")

        self.status_label = ctk.CTkLabel(
            sidebar,
            text="● Initializing...",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["accent"],
        )
        self.status_label.pack(anchor="w", padx=20, pady=(16, 24))

        ctk.CTkLabel(
            sidebar,
            text="QUICK ACTIONS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=20, pady=(0, 8))

        quick_actions = [
            ("What time is it?", "what time is it"),
            ("Today's date", "what is the date"),
            ("Open Notepad", "open notepad"),
            ("Search Python", "search python tutorials"),
            ("Remember my name", "remember that my name is "),
            ("What do you know?", "what do you know about me"),
        ]
        for label, cmd in quick_actions:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                fg_color=COLORS["surface"],
                hover_color=COLORS["surface_light"],
                anchor="w",
                height=36,
                command=lambda c=cmd: self._quick_action(c),
            )
            btn.pack(fill="x", padx=16, pady=3)

        settings_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["surface"], corner_radius=12)
        settings_frame.pack(fill="x", padx=16, pady=(24, 12))

        ctk.CTkLabel(
            settings_frame,
            text="Settings",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 8))

        ctk.CTkSwitch(
            settings_frame,
            text="Voice responses",
            variable=self.voice_enabled,
            progress_color=COLORS["accent"],
        ).pack(anchor="w", padx=14, pady=4)

        ctk.CTkButton(
            settings_frame,
            text="Clear chat session",
            fg_color=COLORS["surface_light"],
            hover_color=COLORS["accent_dim"],
            height=32,
            command=self._clear_session,
        ).pack(fill="x", padx=14, pady=(8, 12))

        ctk.CTkLabel(
            sidebar,
            text="Voice: Hey AVA\nSleep: stop / goodbye\nExit: quit / exit",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
            justify="left",
        ).pack(side="bottom", anchor="w", padx=20, pady=20)

    def _build_main_panel(self):
        main = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color=COLORS["surface"], height=56, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="Chat",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=20, pady=14)

        self.mode_label = ctk.CTkLabel(
            header,
            text="Active",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["accent"],
            fg_color=COLORS["surface_light"],
            corner_radius=20,
            width=80,
            height=28,
        )
        self.mode_label.pack(side="right", padx=20, pady=14)

        self.chat_frame = ctk.CTkScrollableFrame(
            main,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["surface_light"],
            scrollbar_button_hover_color=COLORS["accent_dim"],
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        input_bar = ctk.CTkFrame(main, fg_color=COLORS["surface"], corner_radius=0, height=80)
        input_bar.grid(row=2, column=0, sticky="ew")
        input_bar.grid_propagate(False)
        input_bar.grid_columnconfigure(1, weight=1)

        self.mic_btn = ctk.CTkButton(
            input_bar,
            text="🎤",
            width=48,
            height=48,
            font=ctk.CTkFont(size=22),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            command=self._toggle_listen,
        )
        self.mic_btn.grid(row=0, column=0, padx=(16, 8), pady=16)

        self.input_entry = ctk.CTkEntry(
            input_bar,
            placeholder_text="Type a message or click the mic to speak...",
            height=48,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["surface_light"],
            border_color=COLORS["surface_light"],
        )
        self.input_entry.grid(row=0, column=1, sticky="ew", pady=16)
        self.input_entry.bind("<Return>", lambda e: self._send_text())

        self.send_btn = ctk.CTkButton(
            input_bar,
            text="Send",
            width=90,
            height=48,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._send_text,
        )
        self.send_btn.grid(row=0, column=2, padx=(8, 16), pady=16)

    def _show_welcome(self):
        welcome = ctk.CTkFrame(self.chat_frame, fg_color=COLORS["surface"], corner_radius=16)
        welcome.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(
            welcome,
            text="Welcome to AVA",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(padx=20, pady=(16, 4))

        ctk.CTkLabel(
            welcome,
            text=(
                "Your personal AI assistant with voice and chat.\n"
                "Ask questions, control apps, search the web, or just chat.\n\n"
                "Try: \"open notepad\", \"search AI news\", \"what time is it\", "
                "or \"remember that I like coffee\""
            ),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
            justify="left",
        ).pack(padx=20, pady=(0, 16))

    def _initialize_ava(self):
        try:
            ava = Ava(calibrate_mic=False)
            greeting = ava_greeting()
            self.ui_queue.put(("ready", ava, greeting))
        except Exception as exc:
            self.ui_queue.put(("error", str(exc)))

    def _process_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                kind = msg[0]

                if kind == "ready":
                    self.ava = msg[1]
                    greeting = msg[2]
                    self.status_label.configure(text="● Ready", text_color=COLORS["accent"])
                    self._add_message("ava", greeting)
                    if self.voice_enabled.get():
                        threading.Thread(target=lambda: speak(greeting), daemon=True).start()

                elif kind == "error":
                    self.status_label.configure(text="● Error", text_color=COLORS["danger"])
                    self._add_message("ava", f"Failed to initialize: {msg[1]}")

                elif kind == "message":
                    self._add_message(msg[1], msg[2])

                elif kind == "status":
                    self.status_label.configure(text=msg[1], text_color=msg[2])

                elif kind == "mode":
                    self.mode_label.configure(text=msg[1])

                elif kind == "input_enable":
                    self._set_input_enabled(msg[1])

                elif kind == "scroll":
                    self.chat_frame._parent_canvas.yview_moveto(1.0)

        except queue.Empty:
            pass

        self.after(100, self._process_ui_queue)

    def _add_message(self, sender, text):
        bubble = MessageBubble(self.chat_frame, sender, text)
        bubble.pack(fill="x")
        self.after(50, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def _set_input_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.input_entry.configure(state=state)
        self.send_btn.configure(state=state)
        self.mic_btn.configure(state=state)
        self.processing = not enabled
        if enabled:
            self.mic_btn.configure(text="🎤", fg_color=COLORS["accent"])
            self.listening = False

    def _quick_action(self, command):
        if command.endswith(" "):
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, command)
            self.input_entry.focus()
            return
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
        self.listening = True
        self.mic_btn.configure(text="...", fg_color=COLORS["danger"])
        self.ui_queue.put(("status", "● Listening...", COLORS["accent"]))
        threading.Thread(target=self._listen_and_process, daemon=True).start()

    def _listen_and_process(self):
        try:
            text = self.ava.listen()
            if text:
                self.ui_queue.put(("status", "● Processing...", COLORS["accent"]))
                self._process_command_thread(text)
            else:
                self.ui_queue.put(("status", "● Ready", COLORS["accent"]))
                self.ui_queue.put(("input_enable", True))
        except Exception as exc:
            self.ui_queue.put(("message", "ava", f"Voice error: {exc}"))
            self.ui_queue.put(("status", "● Ready", COLORS["accent"]))
            self.ui_queue.put(("input_enable", True))

    def _handle_command(self, text):
        if not self.ava:
            self._add_message("ava", "Still initializing. Please wait a moment...")
            return
        self.ui_queue.put(("input_enable", False))
        self.ui_queue.put(("status", "● Processing...", COLORS["accent"]))
        threading.Thread(target=self._process_command_thread, args=(text,), daemon=True).start()

    def _process_command_thread(self, raw_text):
        try:
            command = normalize_command(raw_text)
            self.ui_queue.put(("message", "user", raw_text.strip()))

            if is_exit_command(command):
                self.ui_queue.put(("message", "ava", "Goodbye! Shutting down AVA."))
                self.ui_queue.put(("status", "● Goodbye", COLORS["text_dim"]))
                self.after(1500, self.destroy)
                return

            if not self.active:
                if is_wake_command(command):
                    self.active = True
                    response = "Hello. I'm listening."
                    self.ui_queue.put(("mode", "Active"))
                else:
                    response = "Say 'Hey AVA' to wake me up."
                    self.ui_queue.put(("message", "ava", response))
                    self.ui_queue.put(("status", "● Standby", COLORS["text_dim"]))
                    self.ui_queue.put(("input_enable", True))
                    return
            elif is_sleep_command(command):
                self.active = False
                self.ava.brain.clear_session()
                response = "Going to standby. Say hey AVA when you need me."
                self.ui_queue.put(("mode", "Standby"))
            else:
                response = self.ava.process_command(command)

            self.ui_queue.put(("message", "ava", response))
            self.ui_queue.put(("status", "● Ready", COLORS["accent"]))

            if self.voice_enabled.get():
                speak(response)

        except Exception as exc:
            self.ui_queue.put(("message", "ava", f"Error: {exc}"))
            self.ui_queue.put(("status", "● Ready", COLORS["accent"]))
        finally:
            self.ui_queue.put(("input_enable", True))

    def _clear_session(self):
        if self.ava:
            self.ava.brain.clear_session()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self._show_welcome()
        if self.ava:
            self._add_message("ava", "Chat session cleared. How can I help you?")


def main():
    app = AvaUI()
    app.mainloop()


if __name__ == "__main__":
    main()
