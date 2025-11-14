import customtkinter as ctk
from typing import Union, Tuple

class HoverButton(ctk.CTkButton):
    def __init__(self, *args, 
                 hover_color: Union[str, Tuple[str, str]] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_color = hover_color or self._fg_color
        self.normal_color = self._fg_color
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, event):
        self.configure(fg_color=self.hover_color)
        
    def _on_leave(self, event):
        self.configure(fg_color=self.normal_color)