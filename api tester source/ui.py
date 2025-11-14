import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
from datetime import datetime
from requester import Requester
from storage import Storage
import os
from hover_button import HoverButton
from modern_widgets import ModernEntry, SearchEntry
from method_selector import MethodSelector
from loading_spinner import LoadingSpinner

# Modern color scheme inspired by shadcn design
COLORS = {
    "bg_dark": "#09090B",  # Darker background for better contrast
    "bg_light": "#FFFFFF",
    "sidebar_dark": "#18181B",  # Slightly lighter than bg for depth
    "sidebar_light": "#F4F4F5",
    "accent": "#0EA5E9",  # Modern blue accent
    "accent_hover": "#0284C7",
    "text_dark": "#FAFAFA",
    "text_muted_dark": "#A1A1AA",
    "text_light": "#18181B",
    "text_muted_light": "#71717A",
    "border_dark": "#27272A",
    "border_light": "#E4E4E7",
    "success": "#10B981",
    "method_get": "#2563EB",     # Blue
    "method_post": "#059669",    # Green
    "method_put": "#D97706",     # Orange
    "method_delete": "#DC2626",   # Red
    "method_patch": "#7C3AED",   # Purple
    "hover_dark": "#27272A",
    "hover_light": "#F4F4F5",
}

class ModernScrolledText(ctk.CTkTextbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(wrap="none", font=("Consolas", 12))

class MethodLabel(ctk.CTkLabel):
    def __init__(self, *args, method="GET", **kwargs):
        super().__init__(*args, **kwargs)
        self.method = method
        self.configure(
            text=method,
            font=("Segoe UI", 12, "bold"),
            width=70,
            height=28,
            corner_radius=4
        )
        self._set_color()
    
    def _set_color(self):
        method_colors = {
            "GET": COLORS["method_get"],
            "POST": COLORS["method_post"],
            "PUT": COLORS["method_put"],
            "DELETE": COLORS["method_delete"],
            "PATCH": COLORS["method_patch"]
        }
        color = method_colors.get(self.method, COLORS["method_get"])
        self.configure(fg_color=color)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("API Tester")
        self.geometry("1280x800")
        
        # Initialize backend components
        self.requester = Requester()
        self.storage = Storage()
        
        # Build UI
        self._setup_theme()
        self._build_layout()
        self._setup_keyboard_shortcuts()
        
        # Start in dark mode like HTTPie
        self._toggle_theme("dark")
    
    def _setup_theme(self):
        self.font = ("Segoe UI", 12)
        self.title_font = ("Segoe UI", 14, "bold")
        
    def _toggle_sidebar(self):
        if self.sidebar_expanded:
            # Collapse sidebar
            self.sidebar.configure(width=60)
            self.title_label.configure(text="")
            self.collapse_btn.configure(text="»")
            self.sidebar_expanded = False
        else:
            # Expand sidebar
            self.sidebar.configure(width=240)
            self.title_label.configure(text="API Tester")
            self.collapse_btn.configure(text="«")
            self.sidebar_expanded = True
        
    def _build_layout(self):
        # Main split between sidebar and content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar (always visible, like HTTPie)
        self.sidebar = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["sidebar_dark"])
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self._build_sidebar()
        
        # Main content area
        self.main_area = ctk.CTkFrame(self, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        # URL Bar at top
        self._build_url_bar()
        
        # Tabbed interface for request/response
        self.tabs = ctk.CTkTabview(self.main_area, corner_radius=0)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Request tab
        req_tab = self.tabs.add("Request")
        self._build_request_tab(req_tab)
        
        # Response tab
        resp_tab = self.tabs.add("Response")
        self._build_response_tab(resp_tab)
        
    def _build_sidebar(self):
        self.sidebar_expanded = True
        
        # Sidebar header with logo/title
        header = ctk.CTkFrame(self.sidebar, corner_radius=0, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=16)
        
        # App title with animation support
        self.title_label = ctk.CTkLabel(
            header,
            text="API Tester",
            font=self.title_font,
            text_color=COLORS["text_dark"]
        )
        self.title_label.pack(side="left")
        
        # Controls frame
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")
        
        # Theme toggle
        self.theme_btn = ctk.CTkButton(
            controls,
            text="🌙",
            width=32,
            height=32,
            corner_radius=16,
            command=lambda: self._toggle_theme("dark" if ctk.get_appearance_mode() == "Light" else "light"),
            fg_color=COLORS["sidebar_dark"],
            hover_color=COLORS["sidebar_dark"]
        )
        self.theme_btn.pack(side="right", padx=(8, 0))
        
        # Collapse toggle
        self.collapse_btn = ctk.CTkButton(
            controls,
            text="«",
            width=32,
            height=32,
            corner_radius=16,
            command=self._toggle_sidebar,
            fg_color=COLORS["sidebar_dark"],
            hover_color=COLORS["sidebar_dark"]
        )
        self.collapse_btn.pack(side="right")
        
        # Collections section
        # Templates section
        ctk.CTkLabel(
            self.sidebar,
            text="TEMPLATES",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dark"]
        ).pack(fill="x", pady=(20,10), padx=16)

        new_tmpl_btn = ctk.CTkButton(
            self.sidebar,
            text="+ Save Template",
            height=32,
            command=self._save_template,
            fg_color=COLORS["sidebar_dark"],
            hover_color=COLORS["sidebar_dark"]
        )
        new_tmpl_btn.pack(fill="x", padx=16, pady=(0,10))

        # Templates list
        templates = self.storage.get_templates()
        for tmpl in templates:
            self._add_template_item(tmpl)

        ctk.CTkLabel(
            self.sidebar,
            text="COLLECTIONS",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dark"]
        ).pack(fill="x", pady=(20,10), padx=16)

        # Environments manage button
        env_mgr_btn = ctk.CTkButton(
            self.sidebar,
            text="Manage Environments",
            height=32,
            command=self._manage_environments,
            fg_color=COLORS["sidebar_dark"],
            hover_color=COLORS["sidebar_dark"]
        )
        env_mgr_btn.pack(fill="x", padx=16, pady=(12,6))
        
        # New collection button
        new_coll_btn = ctk.CTkButton(
            self.sidebar,
            text="+ New Collection",
            height=32,
            command=self._new_collection,
            fg_color=COLORS["sidebar_dark"],
            hover_color=COLORS["sidebar_dark"]
        )
        new_coll_btn.pack(fill="x", padx=16, pady=(0,10))
        
        # Collections list
        collections = self.storage.get_collections()
        for collection in collections:
            self._add_collection_item(collection)
        
        # History section
        ctk.CTkLabel(
            self.sidebar,
            text="HISTORY",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dark"]
        ).pack(fill="x", pady=(20,10), padx=16)
        
        # History items
        history = self.storage.get_history(limit=10)
        for item in history:
            self._add_history_item(item)

    def _add_template_item(self, template):
        frame = ctk.CTkFrame(
            self.sidebar,
            corner_radius=4,
            fg_color="transparent"
        )
        frame.pack(fill="x", padx=16, pady=2)

        ctk.CTkLabel(
            frame,
            text=template.name,
            font=self.font,
            text_color=COLORS["text_dark"]
        ).pack(side="left", padx=8, pady=6)

        # Click to load
        frame.bind("<Button-1>", lambda e: self._load_template(template))
    
    def _build_url_bar(self):
        url_frame = ctk.CTkFrame(self.main_area, corner_radius=0, height=60)
        url_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        url_frame.grid_columnconfigure(2, weight=1)
        
        # Modern method selector with icons
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        self.method_selector = MethodSelector(
            url_frame,
            command=self._on_method_change,
            methods=methods,
            colors=COLORS,
            width=100,
            height=36
        )
        self.method_selector.grid(row=0, column=0, padx=(16, 8), pady=12)
        # Backwards-compatible adapter so existing code calling self.method_cb.get()/set() still works
        class _MethodAdapter:
            def __init__(self, ms):
                self._ms = ms
            def get(self):
                try:
                    return self._ms.current_method.get()
                except Exception:
                    return "GET"
            def set(self, value):
                try:
                    # reuse method_selector selection method if available
                    if hasattr(self._ms, '_select_method'):
                        self._ms._select_method(value)
                    else:
                        self._ms.current_method.set(value)
                except Exception:
                    pass

        self.method_cb = _MethodAdapter(self.method_selector)
        
        # Environment selector with modern styling
        self.envs = self.storage.get_environments()
        env_names = [e.name for e in self.envs] if self.envs else ["(no env)"]
        self.env_cb = ctk.CTkOptionMenu(
            url_frame,
            values=env_names,
            width=140,
            height=28,
            font=("Segoe UI", 10),
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_dark"],
            dropdown_hover_color=COLORS["hover_dark"],
            dropdown_text_color=COLORS["text_dark"]
        )
        self.env_cb.grid(row=0, column=1, padx=(4, 8), pady=12, sticky="w")
        
        # URL entry
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            url_frame,
            textvariable=self.url_var,
            placeholder_text="Enter request URL",
            height=36,
            font=self.font
        )
        self.url_entry.grid(row=0, column=1, padx=8, pady=12, sticky="ew")
        # Loading spinner (hidden until used)
        self.loading_spinner = LoadingSpinner(url_frame)
        self.loading_spinner.grid(row=0, column=3, padx=4, pady=12)

        # Send and Save Template buttons
        self.save_tmpl_btn = ctk.CTkButton(
            url_frame,
            text="Save",
            width=80,
            height=28,
            command=self._save_template,
            font=self.font
        )
        self.save_tmpl_btn.grid(row=0, column=3, padx=(8,4), pady=12)

        # Send button
        self.send_btn = ctk.CTkButton(
            url_frame,
            text="Send",
            width=100,
            height=36,
            command=self._on_send,
            font=self.font,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.send_btn.grid(row=0, column=4, padx=(8,16), pady=12)
        # Toplevel window to manage environments (create/edit/delete)
        win = ctk.CTkToplevel(self)
        win.title("Environments")
        win.geometry("600x400")

        left = ctk.CTkFrame(win)
        left.pack(side="left", fill="y", padx=8, pady=8)

        right = ctk.CTkFrame(win)
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        listbox = tk.Listbox(left, width=30)
        listbox.pack(fill="y", expand=True)

        envs = self.storage.get_environments()
        for e in envs:
            listbox.insert(tk.END, f"{e.id}: {e.name}")

        # Editor area
        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(right, textvariable=name_var, placeholder_text="Name")
        name_entry.pack(fill="x", pady=(0,8))

        vars_text = ctk.CTkTextbox(right, height=18)
        vars_text.pack(fill="both", expand=True)

        def on_select(evt):
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            env = envs[idx]
            name_var.set(env.name)
            vars_text.delete("1.0", tk.END)
            vars_text.insert(tk.END, env.variables or "{}")

        listbox.bind("<<ListboxSelect>>", on_select)

        def create_env():
            n = name_var.get().strip()
            v = vars_text.get("1.0", tk.END).strip() or "{}"
            if n:
                self.storage.create_environment(n, v)
                win.destroy()
                self._refresh_sidebar()

        def update_env():
            sel = listbox.curselection()
            if not sel:
                return
            env = envs[sel[0]]
            self.storage.update_environment(env.id, vars_text.get("1.0", tk.END).strip() or "{}")
            win.destroy()
            self._refresh_sidebar()

        def delete_env():
            sel = listbox.curselection()
            if not sel:
                return
            env = envs[sel[0]]
            self.storage.delete_environment(env.id)
            win.destroy()
            self._refresh_sidebar()

        btn_frame = ctk.CTkFrame(right)
        btn_frame.pack(fill="x", pady=6)
        ctk.CTkButton(btn_frame, text="Create", command=create_env).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Update", command=update_env).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Delete", fg_color="#D64949", command=delete_env).pack(side="left", padx=6)
        
    def _build_request_tab(self, parent):
        # Split into headers and body sections
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)  # Adjusted for body section
        
        # Headers section with modern styling
        header_frame = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16,8))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_rowconfigure(1, weight=1)
        
        # Headers title bar
        header_title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_title_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))
        
        ctk.CTkLabel(
            header_title_frame,
            text="Headers",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["text_muted_dark"]
        ).pack(side="left")
        
        # Add header button
        HoverButton(
            header_title_frame,
            text="+ Add Header",
            width=100,
            height=28,
            hover_color=COLORS["hover_dark"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border_dark"],
            command=self._add_header
        ).pack(side="right")
        
        # Modern headers text area
        self.headers_text = ModernScrolledText(
            header_frame,
            height=120,
            font=("Cascadia Code", 12),
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text_dark"],
            border_color=COLORS["border_dark"]
        )
        self.headers_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4,8))
        
        # Body section
        body_frame = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
        body_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0,8))
        
        ctk.CTkLabel(
            body_frame,
            text="Body",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["text_muted_dark"]
        ).pack(side="left", padx=8, pady=(8,4))
        self.headers_text.insert("1.0", "{}")
        
        # Body
        body_frame = ctk.CTkFrame(parent, corner_radius=0)
        body_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8,16))
        body_frame.grid_columnconfigure(0, weight=1)
        body_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            body_frame,
            text="Body",
            font=self.font
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(8,4))
        
        self.body_text = ModernScrolledText(body_frame)
        self.body_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
        
    def _build_response_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # Response info bar
        info_frame = ctk.CTkFrame(parent, corner_radius=0, height=40)
        info_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16,0))
        
        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Status: -",
            font=self.font
        )
        self.status_label.pack(side="left", padx=8, pady=8)
        
        self.time_label = ctk.CTkLabel(
            info_frame,
            text="Time: -",
            font=self.font
        )
        self.time_label.pack(side="left", padx=8, pady=8)
        
        # Response content
        content_frame = ctk.CTkFrame(parent, corner_radius=0)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8,16))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Inner tabview for body / headers like HTTPie
        self.resp_inner_tabs = ctk.CTkTabview(content_frame, width=1)
        self.resp_inner_tabs.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        body_tab = self.resp_inner_tabs.add("Body")
        headers_tab = self.resp_inner_tabs.add("Headers")

        self.resp_text = ModernScrolledText(body_tab)
        self.resp_text.pack(fill="both", expand=True, padx=4, pady=4)

        self.resp_headers_text = ModernScrolledText(headers_tab, height=10)
        self.resp_headers_text.pack(fill="both", expand=True, padx=4, pady=4)
    
    def _add_collection_item(self, collection):
        frame = ctk.CTkFrame(
            self.sidebar,
            corner_radius=4,
            fg_color="transparent"
        )
        frame.pack(fill="x", padx=16, pady=2)
        
        ctk.CTkLabel(
            frame,
            text=collection.name,
            font=self.font,
            text_color=COLORS["text_dark"]
        ).pack(side="left", padx=8, pady=6)
    
    def _add_history_item(self, history_item):
        frame = ctk.CTkFrame(
            self.sidebar,
            corner_radius=4,
            fg_color="transparent"
        )
        frame.pack(fill="x", padx=16, pady=2)
        
        MethodLabel(
            frame,
            method=history_item.method,
            text_color=COLORS["text_dark"]
        ).pack(side="left", padx=8, pady=6)
        
        url_label = ctk.CTkLabel(
            frame,
            text=history_item.url[:30] + "..." if len(history_item.url) > 30 else history_item.url,
            font=self.font,
            text_color=COLORS["text_dark"]
        )
        url_label.pack(side="left", fill="x", expand=True, padx=4)
        
        frame.bind("<Button-1>", lambda e: self._load_history_item(history_item))
        url_label.bind("<Button-1>", lambda e: self._load_history_item(history_item))
    
    def _new_collection(self):
        dialog = ctk.CTkInputDialog(
            text="Enter collection name:",
            title="New Collection"
        )
        name = dialog.get_input()
        if name:
            self.storage.create_collection(name)
            self._refresh_sidebar()
    
    def _load_history_item(self, item):
        self.method_cb.set(item.method)
        self.url_var.set(item.url)
        if item.headers:
            self.headers_text.delete("1.0", tk.END)
            self.headers_text.insert("1.0", item.headers)
        if item.body:
            self.body_text.delete("1.0", tk.END)
            self.body_text.insert("1.0", item.body)
        
        # Switch to request tab
        self.tabs.set("Request")

    def _save_template(self):
        dialog = ctk.CTkInputDialog(
            text="Enter template name:",
            title="Save Template"
        )
        name = dialog.get_input()
        if not name:
            return
        method = self.method_cb.get()
        url = self.url_var.get()
        headers = self.headers_text.get("1.0", tk.END).strip()
        body = self.body_text.get("1.0", tk.END).strip()
        self.storage.save_template(name=name, method=method, url=url, headers=headers, body=body)
        self._refresh_sidebar()

    def _delete_template(self, template):
        try:
            self.storage.delete_template(template.id)
        except Exception:
            pass
        self._refresh_sidebar()

    def _apply_environment_to_string(self, text: str) -> str:
        """Replace {{VAR}} tokens in text using the selected environment variables."""
        if not text:
            return text
        try:
            sel = self.env_cb.get()
        except Exception:
            sel = None
        if not sel or sel == "(no env)":
            return text
        # find environment object
        env = None
        for e in getattr(self, 'envs', []) or []:
            if e.name == sel:
                env = e
                break
        if not env:
            return text
        try:
            vars_map = json.loads(env.variables or "{}")
        except Exception:
            vars_map = {}

        def replace_token(s):
            out = s
            for k, v in vars_map.items():
                out = out.replace(f"{{{{{k}}}}}", str(v))
            return out

        return replace_token(text)

    def _load_template(self, template):
        # template is a Template ORM object
        try:
            self.method_cb.set(template.method)
        except Exception:
            pass
        self.url_var.set(template.url)
        if template.headers:
            self.headers_text.delete("1.0", tk.END)
            self.headers_text.insert("1.0", template.headers)
        if template.body:
            self.body_text.delete("1.0", tk.END)
            self.body_text.insert("1.0", template.body)
        self.tabs.set("Request")

    def _manage_environments(self):
        """Open a Toplevel window to manage environments (create/update/delete)."""
        win = ctk.CTkToplevel(self)
        win.title("Environments")
        win.geometry("700x420")

        left = ctk.CTkFrame(win, width=220)
        left.pack(side="left", fill="y", padx=8, pady=8)

        right = ctk.CTkFrame(win)
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        listbox = tk.Listbox(left, width=30)
        listbox.pack(fill="both", expand=True)

        # load current envs
        envs = self.storage.get_environments()
        for e in envs:
            listbox.insert(tk.END, f"{e.id}: {e.name}")

        # Editor area: name + JSON textarea
        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(right, textvariable=name_var, placeholder_text="Environment name")
        name_entry.pack(fill="x", pady=(0,8), padx=4)

        vars_text = ctk.CTkTextbox(right, height=14)
        vars_text.pack(fill="both", expand=True, padx=4, pady=(0,8))

        def on_select(evt):
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            env = envs[idx]
            name_var.set(env.name)
            vars_text.delete("1.0", tk.END)
            vars_text.insert(tk.END, env.variables or "{}")

        listbox.bind("<<ListboxSelect>>", on_select)

        def refresh_and_close():
            # refresh envs in main UI and close window
            try:
                self.envs = self.storage.get_environments()
                names = [e.name for e in self.envs] if self.envs else ["(no env)"]
                self.env_cb.configure(values=names)
            except Exception:
                pass
            win.destroy()

        def create_env():
            n = name_var.get().strip()
            v = vars_text.get("1.0", tk.END).strip() or "{}"
            if not n:
                return
            self.storage.create_environment(n, v)
            refresh_and_close()

        def update_env():
            sel = listbox.curselection()
            if not sel:
                return
            env = envs[sel[0]]
            self.storage.update_environment(env.id, vars_text.get("1.0", tk.END).strip() or "{}")
            refresh_and_close()

        def delete_env():
            sel = listbox.curselection()
            if not sel:
                return
            env = envs[sel[0]]
            self.storage.delete_environment(env.id)
            refresh_and_close()

        btn_frame = ctk.CTkFrame(right)
        btn_frame.pack(fill="x", pady=6)
        ctk.CTkButton(btn_frame, text="Create", command=create_env).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Update", command=update_env).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Delete", fg_color="#D64949", command=delete_env).pack(side="left", padx=6)
    
    def _add_header(self):
        # Create a popup for adding a header
        popup = ctk.CTkToplevel(self)
        popup.title("Add Header")
        popup.geometry("400x160")
        popup.resizable(False, False)
        
        # Center the popup
        popup.geometry(f"+{self.winfo_x() + 200}+{self.winfo_y() + 200}")
        
        # Header key
        key_frame = ctk.CTkFrame(popup, fg_color="transparent")
        key_frame.pack(fill="x", padx=20, pady=(20,10))
        
        ctk.CTkLabel(
            key_frame,
            text="Key:",
            width=80,
            anchor="w"
        ).pack(side="left")
        
        key_entry = ModernEntry(
            key_frame,
            placeholder_text="Content-Type",
            height=32,
            border_color=COLORS["accent"]
        )
        key_entry.pack(side="left", fill="x", expand=True)
        
        # Header value
        value_frame = ctk.CTkFrame(popup, fg_color="transparent")
        value_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            value_frame,
            text="Value:",
            width=80,
            anchor="w"
        ).pack(side="left")
        
        value_entry = ModernEntry(
            value_frame,
            placeholder_text="application/json",
            height=32,
            border_color=COLORS["accent"]
        )
        value_entry.pack(side="left", fill="x", expand=True)
        
        # Add button
        def add_header():
            key = key_entry.get().strip()
            value = value_entry.get().strip()
            if key and value:
                current = self.headers_text.get("1.0", "end-1c")
                if current and not current.endswith("\n"):
                    current += "\n"
                self.headers_text.insert("end", f"{key}: {value}\n")
                popup.destroy()
        
        HoverButton(
            popup,
            text="Add Header",
            command=add_header,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        ).pack(pady=20)
        
        # Make popup modal
        popup.transient(self)
        popup.grab_set()
        key_entry.focus()

    def _toggle_theme(self, mode):
        ctk.set_appearance_mode(mode)
        is_dark = mode == "dark"
        
        # Update theme button text
        self.theme_btn.configure(text="🌙" if not is_dark else "☀️")
        
        # Update sidebar colors with animation effect
        self.sidebar.configure(
            fg_color=COLORS["sidebar_dark"] if is_dark else COLORS["sidebar_light"]
        )
        
        # Update text colors
        text_color = COLORS["text_dark"] if is_dark else COLORS["text_light"]
        muted_color = COLORS["text_muted_dark"] if is_dark else COLORS["text_muted_light"]
        
        self.title_label.configure(text_color=text_color)
        
        # Configure hover colors for buttons
        hover_color = COLORS["hover_dark"] if is_dark else COLORS["hover_light"]
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, HoverButton):
                widget.hover_color = hover_color
        
        # Update theme button
        self.theme_btn.configure(
            text="🌙" if mode == "light" else "☀️"
        )
        
        # Force refresh for proper color updates
        self.update_idletasks()
    
    def _refresh_sidebar(self):
        # Clear and rebuild sidebar
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        self._build_sidebar()
    
    def _setup_keyboard_shortcuts(self):
        self.bind("<Control-Return>", lambda e: self._on_send())
        self.bind("<Control-s>", lambda e: self._save_current_request())
    
    def _on_method_change(self, method: str):
        """Handle UI changes when the HTTP method changes.

        Kept lightweight: updates adapter (for backward compatibility) and
        disables the body editor for methods that typically don't have bodies.
        """
        try:
            # keep adapter in sync if present
            if hasattr(self, 'method_cb') and hasattr(self.method_cb, 'set'):
                self.method_cb.set(method)
        except Exception:
            pass

        try:
            m = (method or '').upper()
            if m in ('GET', 'HEAD', 'OPTIONS'):
                # disable body for readonly methods
                if hasattr(self, 'body_text'):
                    try:
                        self.body_text.configure(state='disabled')
                    except Exception:
                        pass
            else:
                if hasattr(self, 'body_text'):
                    try:
                        self.body_text.configure(state='normal')
                    except Exception:
                        pass
        except Exception:
            pass
        
    def _on_send(self):
        url = self.url_var.get().strip()
        if not url:
            self._show_response("No URL provided", status="Error")
            return
            
        method = self.method_cb.get()
        # Apply environment interpolation
        url = self._apply_environment_to_string(url)
        raw_headers = self._apply_environment_to_string(self.headers_text.get("1.0", tk.END).strip() or "{}")
        try:
            headers = json.loads(raw_headers)
        except json.JSONDecodeError:
            self._show_response("Invalid JSON in headers", status="Error")
            return

        body = self._apply_environment_to_string(self.body_text.get("1.0", tk.END).strip() or None)
        
        self.send_btn.configure(state="disabled")
        # start spinner if available
        try:
            self.loading_spinner.start()
        except Exception:
            pass
        self._show_response("Sending request...", status="Sending")
        self.update_idletasks()
        
        try:
            start_time = datetime.now()
            resp = self.requester.send(
                method=method,
                url=url,
                headers=headers,
                data=body
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            try:
                pretty = json.dumps(resp.json(), indent=2)
            except Exception:
                pretty = resp.text
                
            # Prepare response headers
            try:
                headers_pretty = json.dumps(dict(resp.headers), indent=2)
            except Exception:
                headers_pretty = str(resp.headers)
            status = f"{resp.status_code} {resp.reason}"
            
            # Switch to response tab
            self.tabs.set("Response")
            
            self._show_response(
                pretty,
                status=status,
                duration=duration
            )

            # Populate headers tab
            try:
                self.resp_headers_text.delete("1.0", tk.END)
                self.resp_headers_text.insert(tk.END, headers_pretty)
            except Exception:
                pass
            
            # Add to history and refresh sidebar
            self.storage.add_to_history(
                method=method,
                url=url,
                headers=json.dumps(headers),
                body=body,
                response_code=resp.status_code,
                response_body=pretty
            )
            self._refresh_sidebar()
            
        except Exception as e:
            self._show_response(str(e), status="Error")
        finally:
            self.send_btn.configure(state="normal")
            try:
                self.loading_spinner.stop()
            except Exception:
                pass
    
    def _show_response(self, body, status="-", duration=None):
        self.status_label.configure(
            text=f"Status: {status}",
            text_color=COLORS["success"] if "2" in status else COLORS["text_dark"]
        )
        if duration is not None:
            self.time_label.configure(text=f"Time: {duration:.2f}s")
        # Show body in Body tab
        try:
            self.resp_inner_tabs.set("Body")
        except Exception:
            pass
        self.resp_text.delete("1.0", tk.END)
        self.resp_text.insert(tk.END, body)
    
    def _save_current_request(self, event=None):
        collections = self.storage.get_collections()
        if not collections:
            self._new_collection()
            return
            
        dialog = ctk.CTkInputDialog(
            text="Enter request name:",
            title="Save Request"
        )
        name = dialog.get_input()
        if name:
            collection = collections[0]
            self.storage.save_request(
                collection_id=collection.id,
                name=name,
                method=self.method_cb.get(),
                url=self.url_var.get(),
                headers=self.headers_text.get("1.0", tk.END).strip(),
                body=self.body_text.get("1.0", tk.END).strip()
            )
            self._refresh_sidebar()

if __name__ == '__main__':
    app = App()
    app.mainloop()