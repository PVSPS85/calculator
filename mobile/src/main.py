"""CalcAI Mobile Application Entrypoint.

Launches the CalcAI application with desktop window sizing configured for
a standard Android phone aspect ratio (420x840).
"""

import os
import sys

# Ensure repository root is on sys.path for direct script execution
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Configure Kivy Window dimensions before importing kivy.core.window
os.environ["KIVY_NO_ARGS"] = "1"
from kivy.config import Config
Config.set("graphics", "width", "420")
Config.set("graphics", "height", "840")
Config.set("graphics", "resizable", "1")
Config.set("kivy", "window_icon", "")

from kivy.app import App
from kivy.core.window import Window
from mobile.src.ui.theme import theme
from mobile.src.ui.home_screen import HomeScreen


class CalcAIApp(App):
    """Main CalcAI Kivy application."""

    def build(self):
        self.title = "CalcAI"
        Window.clearcolor = theme.bg_color
        return HomeScreen()


if __name__ == "__main__":
    CalcAIApp().run()
