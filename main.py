import json
import os
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from minecraft_launcher_lib.command import get_minecraft_command
from minecraft_launcher_lib.install import install_minecraft_version

# =========================
# SERUM LAUNCHER CONFIG
# =========================

APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
BASE_DIR = os.path.join(APPDATA, ".SerumLauncher")
GAME_DIR = os.path.join(BASE_DIR, "minecraft")
DATA_FILE = os.path.join(BASE_DIR, "data.json")
OWNER_DISCORD_URL = "https://discord.com/users/1406355912272248944"
SODIUM_URL = "https://modrinth.com/mod/sodium"
VERSIONS = ["1.8.9", "1.12.2", "1.12.5", "1.16.5", "1.18.2", "1.20.4", "1.21.4", "1.21.10", "26.1.2"]
DEFAULT_VERSION = "wybierz wersje"


def get_mods_dir(version: str) -> str:
    return os.path.join(BASE_DIR, "mods", version)


def ensure_dirs() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(GAME_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "mods"), exist_ok=True)
    for version in VERSIONS:
        os.makedirs(get_mods_dir(version), exist_ok=True)


def load_data() -> dict:
    default = {"nicks": []}
    if not os.path.exists(DATA_FILE):
        return default
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default
        if "nicks" not in data or not isinstance(data["nicks"], list):
            data["nicks"] = []
        return data
    except Exception:
        return default


def save_data(data: dict) -> None:
    ensure_dirs()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_nick(nick: str) -> None:
    nick = nick.strip()
    if not nick:
        return
    data = load_data()
    if nick not in data["nicks"]:
        data["nicks"].append(nick)
    save_data(data)


def ensure_version_mod_folder(version: str) -> str:
    mods_dir = get_mods_dir(version)
    os.makedirs(mods_dir, exist_ok=True)
    return mods_dir


def get_last_nick() -> str:
    data = load_data()
    return data["nicks"][-1] if data["nicks"] else ""


def open_url(url: str) -> None:
    webbrowser.open(url)


class SerumLauncher:
    def __init__(self) -> None:
        ensure_dirs()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("Serum Launcher")
        self.root.geometry("980x620")
        self.root.minsize(980, 620)
        self.root.resizable(False, False)

        self.version_var = tk.StringVar(value=DEFAULT_VERSION)
        self.nick_var = tk.StringVar(value=get_last_nick())
        self.status_var = tk.StringVar(value="Gotowy do uruchomienia.")
        self.proc = None

        self._build_ui()
        self._show_game_tab()

    # -------------------------
    # UI
    # -------------------------

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self.root, width=190, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.main = ctk.CTkFrame(self.root, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        brand = ctk.CTkLabel(
            self.sidebar,
            text="SERUM",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        brand.pack(pady=(26, 6))

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Launcher",
            text_color="#8b8b8b",
            font=ctk.CTkFont(size=13),
        )
        subtitle.pack(pady=(0, 20))

        self.game_btn = ctk.CTkButton(
            self.sidebar,
            text="Game",
            height=44,
            corner_radius=14,
            command=self._show_game_tab,
        )
        self.game_btn.pack(padx=18, pady=(10, 8), fill="x")

        self.support_btn = ctk.CTkButton(
            self.sidebar,
            text="Support",
            height=44,
            corner_radius=14,
            command=self._show_support_tab,
        )
        self.support_btn.pack(padx=18, pady=8, fill="x")

        spacer = ctk.CTkLabel(self.sidebar, text="")
        spacer.pack(expand=True)

        bottom = ctk.CTkLabel(
            self.sidebar,
            text="AppData\n.SerumLauncher",
            justify="center",
            text_color="#707070",
            font=ctk.CTkFont(size=12),
        )
        bottom.pack(pady=18)

        self.game_frame = ctk.CTkFrame(self.main, corner_radius=0)
        self.support_frame = ctk.CTkFrame(self.main, corner_radius=0)

        for frame in (self.game_frame, self.support_frame):
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)

        self._build_game_tab()
        self._build_support_tab()

    # -------------------------
    # Game tab
    # -------------------------

    def _build_game_tab(self) -> None:
        outer = ctk.CTkFrame(self.game_frame, fg_color="transparent")
        outer.pack(expand=True, fill="both", padx=28, pady=24)

        top = ctk.CTkFrame(outer, corner_radius=18)
        top.pack(fill="x", pady=(0, 18))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)

        title_box = ctk.CTkFrame(top, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w", padx=22, pady=18)
        ctk.CTkLabel(
            title_box,
            text="Game",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Wybierz nick(cracked), wersję i odpalaj.",
            text_color="#9b9b9b",
        ).pack(anchor="w", pady=(4, 0))

        nick_box = ctk.CTkFrame(top, fg_color="transparent")
        nick_box.grid(row=0, column=1, sticky="e", padx=22, pady=18)
        ctk.CTkLabel(nick_box, text="Nick", text_color="#9b9b9b").pack(anchor="e")
        self.nick_entry = ctk.CTkEntry(
            nick_box,
            width=240,
            height=40,
            textvariable=self.nick_var,
            placeholder_text="Wpisz nick...",
        )
        self.nick_entry.pack(anchor="e", pady=(6, 0))

        center = ctk.CTkFrame(outer, corner_radius=22)
        center.pack(expand=True, fill="both")

        center_inner = ctk.CTkFrame(center, fg_color="transparent")
        center_inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center_inner,
            text="Wersja Minecraft",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=(0, 12))

        self.version_box = ctk.CTkComboBox(
            center_inner,
            values=VERSIONS,
            variable=self.version_var,
            width=240,
            height=42,
            state="readonly",
        )
        self.version_box.pack(pady=(0, 18))

        self.play_btn = ctk.CTkButton(
            center_inner,
            text="GRAJ",
            width=260,
            height=54,
            corner_radius=16,
            font=ctk.CTkFont(size=22, weight="bold"),
            command=self._start_launch_thread,
        )
        self.play_btn.pack(pady=(2, 14))

        self.progress = ctk.CTkProgressBar(center_inner, width=320)
        self.progress.set(0)
        self.progress.pack(pady=(8, 8))

        self.status_label = ctk.CTkLabel(
            center_inner,
            textvariable=self.status_var,
            text_color="#b7b7b7",
        )
        self.status_label.pack(pady=(8, 0))

    # -------------------------
    # Support tab
    # -------------------------

    def _build_support_tab(self) -> None:
        outer = ctk.CTkFrame(self.support_frame, fg_color="transparent")
        outer.pack(expand=True, fill="both", padx=28, pady=24)

        top = ctk.CTkFrame(outer, corner_radius=18)
        top.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(
            top,
            text="Support",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(
            top,
            text="Przyciski pomocnicze i linki kontaktowe.",
            text_color="#9b9b9b",
        ).pack(anchor="w", padx=22, pady=(0, 18))

        cards = ctk.CTkFrame(outer, corner_radius=22)
        cards.pack(expand=True, fill="both")
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        left_card = ctk.CTkFrame(cards, corner_radius=18)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(18, 10), pady=18)
        right_card = ctk.CTkFrame(cards, corner_radius=18)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 18), pady=18)

        ctk.CTkLabel(
            left_card,
            text="Discord owner",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(18, 6), padx=18, anchor="w")
        ctk.CTkLabel(
            left_card,
            text="Przejdź do profilu właściciela serwera.",
            text_color="#a1a1a1",
            wraplength=300,
            justify="left",
        ).pack(pady=(0, 16), padx=18, anchor="w")
        ctk.CTkButton(
            left_card,
            text="Otwórz Discord",
            height=42,
            corner_radius=14,
            command=lambda: open_url(OWNER_DISCORD_URL),
        ).pack(padx=18, pady=(0, 18), fill="x")

        ctk.CTkLabel(
            right_card,
            text="sodium",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(18, 6), padx=18, anchor="w")
        ctk.CTkLabel(
            right_card,
            text="",
            text_color="#a1a1a1",
            wraplength=300,
            justify="left",
        ).pack(pady=(0, 10), padx=18, anchor="w")
        ctk.CTkLabel(
            right_card,
            text=f"Polecamy zainstalować Sodium",
            text_color="#9b9b9b",
            wraplength=300,
            justify="left",
        ).pack(padx=18, pady=(0, 12), fill="x")
        ctk.CTkButton(
            right_card,
            text="pobierz sodium",
            height=42,
            corner_radius=14,
            command=lambda: open_url(SODIUM_URL),
        ).pack(padx=18, pady=(0, 18), fill="x")

    # -------------------------
    # Tab switching
    # -------------------------

    def _show_game_tab(self) -> None:
        self.support_frame.grid_remove()
        self.game_frame.grid()
        self.game_btn.configure(state="disabled")
        self.support_btn.configure(state="normal")

    def _show_support_tab(self) -> None:
        self.game_frame.grid_remove()
        self.support_frame.grid()
        self.support_btn.configure(state="disabled")
        self.game_btn.configure(state="normal")

    # -------------------------
    # Helpers
    # -------------------------

    def _refresh_nick_from_file(self) -> None:
        self.nick_var.set(get_last_nick())
        self.status_var.set("Wczytano ostatni zapisany nick.")

    def _open_app_folder(self) -> None:
        try:
            os.startfile(BASE_DIR)
        except Exception as e:
            messagebox.showerror("Serum", f"Nie udało się otworzyć folderu:\n{e}")

    def _start_launch_thread(self) -> None:
        self.play_btn.configure(state="disabled")
        self.progress.set(0)
        self.status_var.set("Przygotowanie...")
        threading.Thread(target=self._launch_game, daemon=True).start()

    def _launch_game(self) -> None:
        nick = self.nick_var.get().strip()
        version = self.version_var.get().strip()

        if not nick:
            self.root.after(0, lambda: messagebox.showerror("Serum", "Wpisz nick."))
            self.root.after(0, self._reset_play_button)
            return

        try:
            self.root.after(0, lambda: self.status_var.set(f"Instalowanie wersji {version}..."))
            self.root.after(0, lambda: self.progress.set(0.15))
            install_minecraft_version(version, GAME_DIR)

            self.root.after(0, lambda: self.status_var.set("Zapisywanie nicku..."))
            save_nick(nick)
            ensure_version_mod_folder(version)
            self.root.after(0, lambda: self.progress.set(0.45))

            self.root.after(0, lambda: self.status_var.set("Tworzenie komendy uruchomienia..."))
            options = {
                "username": nick,
                "uuid": "00000000-0000-0000-0000-000000000000",
                "token": "offline",
            }
            cmd = get_minecraft_command(version, GAME_DIR, options)
            self.root.after(0, lambda: self.progress.set(0.75))

            self.root.after(0, lambda: self.status_var.set("Uruchamianie Minecrafta..."))
            self.proc = subprocess.Popen(cmd, cwd=GAME_DIR)

            # Foldery modów per wersja są już tworzone, więc łatwo później dopiąć Sodium/Fabric.
            self.root.after(0, lambda: self.progress.set(1.0))
            self.root.after(0, lambda: self.status_var.set("Minecraft uruchomiony."))
            self.root.after(0, self.root.withdraw)

            threading.Thread(target=self._watch_process, daemon=True).start()

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Serum", f"Błąd uruchomienia:\n{e}"))
            self.root.after(0, lambda: self.status_var.set("Wystąpił błąd."))
            self.root.after(0, lambda: self.progress.set(0))
            self.root.after(0, self._reset_play_button)

    def _watch_process(self) -> None:
        try:
            if self.proc:
                self.proc.wait()
        finally:
            self.root.after(0, self._restore_launcher)

    def _restore_launcher(self) -> None:
        self.root.deiconify()
        self.status_var.set("Minecraft zamknięty.")
        self.progress.set(0)
        self._reset_play_button()

    def _reset_play_button(self) -> None:
        self.play_btn.configure(state="normal")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ensure_dirs()
    app = SerumLauncher()
    app.run()

