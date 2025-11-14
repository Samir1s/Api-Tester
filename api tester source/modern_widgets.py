import customtkinter as ctk
from typing import Union, Tuple

class ModernEntry(ctk.CTkEntry):
    def __init__(self, *args,
                 placeholder_text: str = None,
                 border_color: Union[str, Tuple[str, str]] = None,
                 **kwargs):
        super().__init__(*args, placeholder_text=placeholder_text, **kwargs)
        self.border_color = border_color
        self.default_border = self._border_color
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
    def _on_focus_in(self, event):
        if self.border_color:
            self.configure(border_color=self.border_color)
            
    def _on_focus_out(self, event):
        self.configure(border_color=self.default_border)
        
class SearchEntry(ModernEntry):
    def __init__(self, *args, command=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = command
        self.bind("<Return>", self._on_return)
        
    def _on_return(self, event):
        if self.command:
            self.command()