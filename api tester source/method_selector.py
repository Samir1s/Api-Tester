import customtkinter as ctk
from typing import List, Callable
import json

class MethodSelector(ctk.CTkFrame):
    def __init__(self, *args, 
                 command: Callable = None,
                 methods: List[str] = None,
                 colors: dict = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        
        self.methods = methods or ["GET", "POST", "PUT", "DELETE", "PATCH"]
        self.colors = colors or {}
        self.command = command
        
        # Method button
        self.current_method = ctk.StringVar(value=self.methods[0])
        self.method_btn = ctk.CTkButton(
            self,
            textvariable=self.current_method,
            width=90,
            command=self._show_dropdown
        )
        self.method_btn.pack(expand=True, fill="both")
        self._update_button_color()
        
        # Create dropdown window
        self.dropdown = None
        
    def _show_dropdown(self):
        if self.dropdown:
            self.dropdown.destroy()
            self.dropdown = None
            return
            
        # Create dropdown window
        self.dropdown = ctk.CTkToplevel()
        self.dropdown.wm_overrideredirect(True)
        self.dropdown.transient(self)
        
        # Position dropdown below button
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.dropdown.geometry(f"90x{len(self.methods) * 35}+{x}+{y}")
        
        # Add method options
        for method in self.methods:
            btn = ctk.CTkButton(
                self.dropdown,
                text=method,
                fg_color=self.colors.get(f"method_{method.lower()}", "gray"),
                command=lambda m=method: self._select_method(m)
            )
            btn.pack(pady=1, padx=1, fill="x")
            
        # Bind events to auto-close
        self.dropdown.bind("<FocusOut>", lambda e: self.dropdown.destroy())
        self.dropdown.focus_set()
        
    def _select_method(self, method):
        self.current_method.set(method)
        if self.dropdown:
            self.dropdown.destroy()
            self.dropdown = None
        self._update_button_color()
        if self.command:
            self.command(method)
            
    def _update_button_color(self):
        method = self.current_method.get()
        color = self.colors.get(f"method_{method.lower()}", "gray")
        self.method_btn.configure(fg_color=color)