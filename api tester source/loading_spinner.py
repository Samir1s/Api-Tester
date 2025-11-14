import customtkinter as ctk
import tkinter as tk

class LoadingSpinner(ctk.CTkFrame):
    """A small spinner using a tkinter.Canvas and an after-loop animation.

    This avoids threading and the 'transparent' color issue by using a
    neutral background color when necessary.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # keep the frame visually transparent in CTk terms
        try:
            self.configure(fg_color="transparent")
        except Exception:
            pass

        # Determine a safe background for the canvas. Try common attributes
        # on the parent; fall back to a sensible default.
        bg_color = None
        try:
            parent = self.master
            # customtkinter frames may not expose a standard bg; try several
            bg_color = getattr(parent, "_fg_color", None)
            if not bg_color or bg_color == "transparent":
                # try tkinter cget as a fallback
                try:
                    bg_color = parent.cget("bg")
                except Exception:
                    bg_color = None
        except Exception:
            bg_color = None

        if not bg_color or bg_color == "transparent":
            # neutral dark default; chosen to match the app's dark theme
            bg_color = "#09090B"

        # Normalize color values that may come from customtkinter (sometimes
        # these are tuples or space-separated values like "gray81 gray20").
        try:
            if isinstance(bg_color, (list, tuple)):
                bg_color = bg_color[-1]
            if isinstance(bg_color, str) and " " in bg_color:
                # pick the last color (usually the dark theme color)
                bg_color = bg_color.split()[-1]
        except Exception:
            bg_color = "#09090B"

        # Use a plain tkinter Canvas for reliable drawing
        self.canvas = tk.Canvas(self, width=30, height=30, bg=bg_color, highlightthickness=0)
        self.canvas.pack(expand=True)

        # Animation state
        self._angle = 0
        self._animating = False
        self._job = None

    def start(self):
        if not self._animating:
            self._animating = True
            self._animate()

    def stop(self):
        self._animating = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _animate(self):
        if not self._animating:
            return
        self._angle = (self._angle + 15) % 360
        self.canvas.delete("spinner")
        # Draw an arc to simulate a spinner
        self.canvas.create_arc(4, 4, 26, 26, start=self._angle, extent=300, tags="spinner", width=2, style="arc", outline="#A3A3A3")
        self._job = self.after(60, self._animate)
