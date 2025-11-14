# modern_httpie_tk_final_gradient.py
# HTTPie-like modern Tkinter client (with gradient background, glowing borders, and animated Send button)
# pip install customtkinter requests pygments

import os, json, sqlite3, threading, time
from pathlib import Path
from functools import partial
from tkinter import ttk, filedialog, messagebox, scrolledtext, Canvas
import customtkinter as ctk
import requests
from pygments import lex
from pygments.lexers import JsonLexer
from pygments.token import Token

APP_TITLE = "HTTPie-like — Gradient Edition"
DB_FILE = "httpie_like_data.db"
DEFAULT_TIMEOUT = 30

# ---------- Gradient + UI Colors ----------
COLORS = {
    "bg_top": "#0600AB",       # Deep indigo top
    "bg_bottom": "#00033D",    # Navy bottom
    "border_glow": "#977DFF",  # Purple border glow
    "accent_from": "#FFCCF2",  # Pink gradient start
    "accent_to": "#0033FF",    # Blue gradient end
}

# ---------- DB utilities ----------
def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, method TEXT, url TEXT,
        params TEXT, headers TEXT, body TEXT,
        collection TEXT, draft INTEGER DEFAULT 0,
        created_at REAL
      )
    """)
    cur.execute("""
      CREATE TABLE IF NOT EXISTS environments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, content TEXT
      )
    """)
    cur.execute("""
      CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, description TEXT
      )
    """)
    con.commit()
    con.close()

# ---------- Gradient background ----------
def draw_vertical_gradient(canvas, width, height, color_top, color_bottom, steps=180):
    canvas.delete("gradient")
    r1, g1, b1 = canvas.winfo_rgb(color_top)
    r2, g2, b2 = canvas.winfo_rgb(color_bottom)
    r1, g1, b1 = r1 / 256, g1 / 256, b1 / 256
    r2, g2, b2 = r2 / 256, g2 / 256, b2 / 256
    for i in range(steps):
        frac = i / (steps - 1)
        nr = int(r1 + (r2 - r1) * frac)
        ng = int(g1 + (g2 - g1) * frac)
        nb = int(b1 + (b2 - b1) * frac)
        color = f"#{nr:02x}{ng:02x}{nb:02x}"
        y1 = int((i / steps) * height)
        y2 = int(((i + 1) / steps) * height)
        canvas.create_rectangle(0, y1, width, y2, outline=color, fill=color, tags="gradient")
    canvas.lower("gradient")

# ---------- Animated gradient button ----------
class GradientButton(Canvas):
    def __init__(self, parent, text="Send", command=None, width=92, height=36):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg="#00033D")
        self.text = text
        self.command = command
        self.pos = 0
        self.running = True
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        self._animate()

    def _animate(self):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        steps = 12
        pos = (self.pos % 100) / 100
        for i in range(steps):
            t = (i / (steps - 1)) + pos
            r1, g1, b1 = (255, 204, 242)  # pink
            r2, g2, b2 = (0, 51, 255)     # blue
            r = int(r1 + (r2 - r1) * (t % 1))
            g = int(g1 + (g2 - g1) * (t % 1))
            b = int(b1 + (b2 - b1) * (t % 1))
            color = f"#{r:02x}{g:02x}{b:02x}"
            y1, y2 = (i / steps) * h, ((i + 1) / steps) * h
            self.create_rectangle(0, y1, w, y2, outline=color, fill=color)
        self.create_text(w / 2, h / 2, text=self.text, fill="white", font=("Helvetica", 10, "bold"))
        self.pos += 1
        if self.running:
            self.after(80, self._animate)

# ---------- Parsing helpers ----------
def pretty_json_if_possible(text: str) -> str:
    if not text:
        return ""
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception:
        return text

def parse_kv_or_json(text: str) -> dict:
    s = text.strip()
    if not s:
        return {}
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    out = {}
    for line in s.splitlines():
        line = line.strip()
        if not line:
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            out[k.strip()] = v.strip()
        elif ':' in line:
            k, v = line.split(':', 1)
            out[k.strip()] = v.strip()
        else:
            out[line] = ""
    return out

# ---------- JSON highlighting ----------
JSON_TAGS = {
    "json_key": {"foreground": "#9CDCFE"},
    "json_string": {"foreground": "#CE9178"},
    "json_number": {"foreground": "#B5CEA8"},
    "json_bool": {"foreground": "#569CD6"},
    "json_null": {"foreground": "#569CD6"},
    "status": {"foreground": "#00D084", "font": ("Helvetica", 10, "bold")},
}

# ---------- UI Components ----------
class RequestTab:
    def __init__(self, notebook, app, title="Request"):
        self.app = app
        self.frame = ctk.CTkFrame(notebook, fg_color="transparent")
        self.title = title
        self.method = ctk.StringVar(value="GET")
        self.url = ctk.StringVar(value="https://httpbin.org/get")
        self.status = ctk.StringVar(value="Not sent")
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self.frame, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkOptionMenu(top, values=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
                          variable=self.method, width=90).pack(side="left", padx=(0, 8))
        url_entry = ctk.CTkEntry(top, textvariable=self.url,
                                 border_color=COLORS["border_glow"], border_width=2)
        url_entry.pack(side="left", fill="x", expand=True)
        GradientButton(top, text="Send", command=self.send).pack(side="left", padx=(8, 6))
        ctk.CTkButton(top, text="Save", width=70, border_color=COLORS["border_glow"]).pack(side="left")

        # --- Main split: left editor, right response ---
        main = ctk.CTkFrame(self.frame, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=6)
        left = ctk.CTkFrame(main, width=420, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        # --- Tabs: Params / Headers / Auth / Body ---
        tabs_container = ctk.CTkFrame(left, fg_color="transparent")
        tabs_container.pack(fill="both", expand=True)
        tabctl = ttk.Notebook(tabs_container)
        tabctl.pack(fill="both", expand=True)

        # Params
        pframe = ttk.Frame(tabctl)
        self.params = scrolledtext.ScrolledText(pframe, height=6)
        self.params.pack(fill="both", expand=True)
        tabctl.add(pframe, text="Params")

        # Headers
        hframe = ttk.Frame(tabctl)
        self.headers = scrolledtext.ScrolledText(hframe, height=6)
        self.headers.pack(fill="both", expand=True)
        tabctl.add(hframe, text="Headers")

        # Auth
        aframe = ttk.Frame(tabctl)
        self.auth_type = ctk.StringVar(value="None")
        ctk.CTkLabel(aframe, text="Auth Type").pack(anchor="w", padx=6, pady=(6, 2))
        ctk.CTkOptionMenu(aframe, values=["None", "API Key", "Basic Auth", "Bearer Token"], variable=self.auth_type)\
            .pack(anchor="w", padx=6)
        self.auth_area = ctk.CTkFrame(aframe, fg_color="transparent")
        self.auth_area.pack(fill="both", expand=True, padx=6, pady=6)
        self.auth_type.trace_add("write", self._render_auth)
        self._render_auth()
        tabctl.add(aframe, text="Auth")

        # Body
        bframe = ttk.Frame(tabctl)
        self.body = scrolledtext.ScrolledText(bframe, height=16)
        self.body.pack(fill="both", expand=True)
        tabctl.add(bframe, text="Body")

        # Left quick actions/drafts
        quick = ctk.CTkFrame(left, fg_color="transparent")
        quick.pack(fill="x", pady=(8, 0), padx=6)
        self.draft_label = ctk.StringVar(value="Draft: Unsaved")
        ctk.CTkLabel(quick, textvariable=self.draft_label).pack(side="left")
        ctk.CTkButton(quick, text="Save Draft", width=100, command=self.save_draft,
                      border_color=COLORS["border_glow"]).pack(side="right")

        # Right: status + response
        rtop = ctk.CTkFrame(right, fg_color="transparent")
        rtop.pack(fill="x")
        ctk.CTkLabel(rtop, textvariable=self.status).pack(side="left", padx=6, pady=(4, 2))
        resp_frame = ctk.CTkFrame(right, fg_color="transparent")
        resp_frame.pack(fill="both", expand=True, padx=(6, 6), pady=(6, 6))
        self.response = scrolledtext.ScrolledText(resp_frame)
        self.response.pack(fill="both", expand=True)
        self._setup_response_tags()
        rbot = ctk.CTkFrame(right, fg_color="transparent")
        rbot.pack(fill="x", padx=6, pady=(0, 6))
        ctk.CTkButton(rbot, text="Copy", width=90, command=self.copy_response,
                      border_color=COLORS["border_glow"]).pack(side="right", padx=(6, 6))
        ctk.CTkButton(rbot, text="Save...", width=90, command=self.save_response_file,
                      border_color=COLORS["border_glow"]).pack(side="right")

    # (rest of methods from your original RequestTab: _render_auth, _setup_response_tags, copy_response,
    # save_response_file, save_request, save_draft, send, _display_json)
    # [They remain identical to your provided file.]

# ---------- Sidebar ----------
# (same as your original Sidebar, but optional border glow)
class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app, width=320):
        super().__init__(parent, width=width, fg_color="#111214", border_color=COLORS["border_glow"], border_width=1)
        self.app = app
        self.pack_propagate(False)
        self._build()
    # (keep original _build, _add_collection, refresh unchanged)

# ---------- ModernHTTPieApp ----------
class ModernHTTPieApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1365x768")
        self.root.minsize(1100, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        init_db()
        self._build()

    def _build(self):
        # Gradient background
        self.canvas = Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.container = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self._container_window_id = self.canvas.create_window(0, 0, anchor="nw", window=self.container)
        self.root.bind("<Configure>", self._render_background)
        self._render_background(None)

        self.sidebar = Sidebar(self.container, self)
        self.sidebar.pack(side="left", fill="y")

        main = ctk.CTkFrame(self.container, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", padx=6, pady=8)
        self.tab_ctl = ttk.Notebook(top)
        self.tab_ctl.pack(fill="x", expand=True, side="left")
        self.tabs = []
        toolbar = ctk.CTkFrame(top, fg_color="transparent")
        toolbar.pack(side="right", padx=6)
        ctk.CTkButton(toolbar, text="New Tab", width=100, command=self.new_tab,
                      border_color=COLORS["border_glow"]).pack(side="left", padx=6)
        ctk.CTkButton(toolbar, text="Import", width=100, command=self.import_requests,
                      border_color=COLORS["border_glow"]).pack(side="left", padx=6)
        ctk.CTkButton(toolbar, text="Export", width=100, command=self.export_requests,
                      border_color=COLORS["border_glow"]).pack(side="left", padx=6)
        self.new_tab()

    def _render_background(self, event):
        w = self.canvas.winfo_width() or self.root.winfo_width()
        h = self.canvas.winfo_height() or self.root.winfo_height()
        draw_vertical_gradient(self.canvas, w, h, COLORS["bg_top"], COLORS["bg_bottom"])
        self.canvas.tag_raise(self._container_window_id)

    # (keep all other ModernHTTPieApp methods from your provided version: new_tab, refresh_sidebar,
    # show_history, show_envs, import_requests, export_requests, toggle_theme)

# ---------- Small dialogs ----------
# (keep simple_input() and text_input() unchanged)

# ---------- Run ----------
def main():
    init_db()
    root = ctk.CTk()
    app = ModernHTTPieApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
