"""Entrypoint for CalcAI Mobile Application when launched directly or packaged as an Android APK."""

import os
import sys
import types

# When packaged by Buildozer (source.dir = mobile), the current directory is the root of the app.
# Create a virtual 'mobile' module pointing to this directory so existing package imports
# (e.g., 'from mobile.src.ui.theme import theme') resolve correctly on Android.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.abspath(os.path.join(_current_dir, ".."))

for p in (_current_dir, _parent_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

if "mobile" not in sys.modules:
    mobile_pkg = types.ModuleType("mobile")
    mobile_pkg.__path__ = [_current_dir]
    mobile_pkg.__file__ = os.path.join(_current_dir, "__init__.py")
    sys.modules["mobile"] = mobile_pkg

from mobile.src.main import CalcAIApp

if __name__ == "__main__":
    CalcAIApp().run()
