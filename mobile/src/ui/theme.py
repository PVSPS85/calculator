"""Theme definitions and color tokens for CalcAI.

Implements the requested premium monochrome aesthetic with dark and light variants.
"""

from kivy.event import EventDispatcher
from kivy.properties import ListProperty, StringProperty


class ThemeManager(EventDispatcher):
    """Observable theme manager supplying reactive color properties."""

    mode = StringProperty("dark")

    # Reactive Color Tokens (RGBA)
    bg_color = ListProperty([0.035, 0.035, 0.035, 1])          # #090909
    card_color = ListProperty([0.09, 0.09, 0.09, 1])           # #171717
    surface_color = ListProperty([0.133, 0.133, 0.133, 1])     # #222222
    border_color = ListProperty([0.188, 0.188, 0.188, 1])      # #303030
    text_main = ListProperty([0.96, 0.96, 0.96, 1])            # #F5F5F5
    text_secondary = ListProperty([0.64, 0.64, 0.64, 1])       # #A3A3A3
    button_num = ListProperty([0.08, 0.08, 0.08, 1])           # #141414
    button_op = ListProperty([0.14, 0.14, 0.14, 1])            # #242424
    button_eq = ListProperty([0.22, 0.22, 0.22, 1])            # #383838
    button_pressed = ListProperty([0.28, 0.28, 0.28, 1])       # #474747
    user_bubble = ListProperty([0.16, 0.16, 0.16, 1])          # #292929
    ai_bubble = ListProperty([0.10, 0.10, 0.10, 1])            # #1A1A1A

    THEMES = {
        "dark": {
            "bg_color": [0.035, 0.035, 0.035, 1],          # #090909
            "card_color": [0.09, 0.09, 0.09, 1],           # #171717
            "surface_color": [0.133, 0.133, 0.133, 1],     # #222222
            "border_color": [0.188, 0.188, 0.188, 1],      # #303030
            "text_main": [0.96, 0.96, 0.96, 1],            # #F5F5F5
            "text_secondary": [0.64, 0.64, 0.64, 1],       # #A3A3A3
            "button_num": [0.08, 0.08, 0.08, 1],
            "button_op": [0.14, 0.14, 0.14, 1],
            "button_eq": [0.22, 0.22, 0.22, 1],
            "button_pressed": [0.28, 0.28, 0.28, 1],
            "user_bubble": [0.16, 0.16, 0.16, 1],
            "ai_bubble": [0.10, 0.10, 0.10, 1],
        },
        "light": {
            "bg_color": [0.95, 0.95, 0.95, 1],             # Clean off-white
            "card_color": [1.0, 1.0, 1.0, 1],              # Pure white
            "surface_color": [0.90, 0.90, 0.90, 1],
            "border_color": [0.82, 0.82, 0.82, 1],
            "text_main": [0.10, 0.10, 0.10, 1],
            "text_secondary": [0.42, 0.42, 0.42, 1],
            "button_num": [0.98, 0.98, 0.98, 1],
            "button_op": [0.88, 0.88, 0.88, 1],
            "button_eq": [0.20, 0.20, 0.20, 1],            # Dark contrast for equals
            "button_pressed": [0.75, 0.75, 0.75, 1],
            "user_bubble": [0.86, 0.86, 0.86, 1],
            "ai_bubble": [0.94, 0.94, 0.94, 1],
        },
    }

    def set_mode(self, mode: str) -> None:
        """Switch between dark and light themes."""
        if mode in self.THEMES:
            self.mode = mode
            for token, value in self.THEMES[mode].items():
                setattr(self, token, value)


# Global singleton instance
theme = ThemeManager()
