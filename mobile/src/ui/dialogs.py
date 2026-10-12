"""Dialogs and modal sheets for Calculation History and Application Settings."""

from typing import Callable, List, Dict
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp

from mobile.src.ui.theme import theme
from mobile.src.ui.components import ThemedCard, CalcButton


class HistoryModal(ModalView):
    """Modal displaying past calculations with tap-to-restore functionality."""

    def __init__(
        self,
        history: List[Dict[str, str]],
        on_select: Callable[[str], None],
        on_clear: Callable[[], None],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.75)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.7)

        # Outer Container Card
        self.card = ThemedCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )
        self.add_widget(self.card)

        # Header Bar
        header = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        title = Label(
            text="Calculation History",
            font_size="16sp",
            bold=True,
            color=theme.text_main,
            halign="left",
        )
        title.bind(size=title.setter("text_size"))
        header.add_widget(title)

        close_btn = Button(
            text="✕",
            size_hint=(None, 1),
            width=dp(36),
            background_color=(0, 0, 0, 0),
            color=theme.text_secondary,
            font_size="16sp",
            bold=True,
        )
        close_btn.bind(on_release=lambda *a: self.dismiss())
        header.add_widget(close_btn)
        self.card.add_widget(header)

        # Scrollable history feed
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.feed_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.feed_layout.bind(minimum_height=self.feed_layout.setter("height"))

        if not history:
            empty_lbl = Label(
                text="No calculations recorded yet.\nPerform arithmetic to see history here.",
                font_size="13sp",
                color=theme.text_secondary,
                halign="center",
                size_hint_y=None,
                height=dp(120),
            )
            empty_lbl.bind(size=empty_lbl.setter("text_size"))
            self.feed_layout.add_widget(empty_lbl)
        else:
            for item in reversed(history):
                item_card = ThemedCard(
                    orientation="vertical",
                    size_hint_y=None,
                    height=dp(64),
                    padding=[dp(12), dp(8)],
                    spacing=dp(2),
                    radius=10,
                )
                expr = item.get("expression", "")
                res = item.get("result", "")
                ts = item.get("timestamp", "")

                top_row = BoxLayout(size_hint_y=None, height=dp(20))
                expr_lbl = Label(
                    text=expr,
                    font_size="13sp",
                    color=theme.text_secondary,
                    halign="left",
                )
                expr_lbl.bind(size=expr_lbl.setter("text_size"))
                ts_lbl = Label(
                    text=ts,
                    font_size="11sp",
                    color=theme.text_secondary,
                    size_hint_x=None,
                    width=dp(60),
                    halign="right",
                )
                ts_lbl.bind(size=ts_lbl.setter("text_size"))
                top_row.add_widget(expr_lbl)
                top_row.add_widget(ts_lbl)

                res_lbl = Label(
                    text=f"= {res}",
                    font_size="16sp",
                    bold=True,
                    color=theme.text_main,
                    size_hint_y=None,
                    height=dp(26),
                    halign="left",
                )
                res_lbl.bind(size=res_lbl.setter("text_size"))

                item_card.add_widget(top_row)
                item_card.add_widget(res_lbl)

                # Tap item to restore
                restore_btn = Button(
                    text="Tap to restore",
                    size_hint=(None, None),
                    size=(0, 0),
                    opacity=0,
                )
                # Make the card clickable using touch release
                def _make_handler(target_expr):
                    return lambda inst, touch: (
                        on_select(target_expr),
                        self.dismiss(),
                    ) if item_card.collide_point(*touch.pos) else False

                item_card.bind(on_touch_up=_make_handler(expr))
                self.feed_layout.add_widget(item_card)

        scroll.add_widget(self.feed_layout)
        self.card.add_widget(scroll)

        # Footer Action Button
        footer = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        clear_btn = CalcButton(
            text="Clear History",
            size_hint=(1, 1),
            font_size="13sp",
            is_operator=True,
        )
        def _on_clear_click(*a):
            on_clear()
            self.dismiss()

        clear_btn.bind(on_release=_on_clear_click)
        footer.add_widget(clear_btn)
        self.card.add_widget(footer)


class SettingsModal(ModalView):
    """Modal displaying theme preference, backend URL configuration, and live connection status."""

    def __init__(self, ai_service=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.92, 0.82)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.7)
        self.ai_service = ai_service

        self.card = ThemedCard(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )
        self.add_widget(self.card)

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(36))
        title = Label(
            text="Settings",
            font_size="17sp",
            bold=True,
            color=theme.text_main,
            halign="left",
        )
        title.bind(size=title.setter("text_size"))
        header.add_widget(title)

        close_btn = Button(
            text="✕",
            size_hint=(None, 1),
            width=dp(36),
            background_color=(0, 0, 0, 0),
            color=theme.text_secondary,
            font_size="16sp",
            bold=True,
        )
        close_btn.bind(on_release=lambda *a: self.dismiss())
        header.add_widget(close_btn)
        self.card.add_widget(header)

        # Theme Selector Section
        theme_title = Label(
            text="THEME PREFERENCE",
            font_size="11sp",
            bold=True,
            color=theme.text_secondary,
            size_hint_y=None,
            height=dp(16),
            halign="left",
        )
        theme_title.bind(size=theme_title.setter("text_size"))
        self.card.add_widget(theme_title)

        theme_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        self.dark_btn = CalcButton(
            text="● Dark Monochrome",
            font_size="12sp",
            size_hint=(0.5, 1),
            is_equals=(theme.mode == "dark"),
        )
        self.light_btn = CalcButton(
            text="○ Minimalist Light",
            font_size="12sp",
            size_hint=(0.5, 1),
            is_equals=(theme.mode == "light"),
        )

        def _select_dark(*a):
            theme.set_mode("dark")
            self.dark_btn.text = "● Dark Monochrome"
            self.light_btn.text = "○ Minimalist Light"
            self.dark_btn.is_equals = True
            self.light_btn.is_equals = False

        def _select_light(*a):
            theme.set_mode("light")
            self.dark_btn.text = "○ Dark Monochrome"
            self.light_btn.text = "● Minimalist Light"
            self.dark_btn.is_equals = False
            self.light_btn.is_equals = True

        self.dark_btn.bind(on_release=_select_dark)
        self.light_btn.bind(on_release=_select_light)
        theme_box.add_widget(self.dark_btn)
        theme_box.add_widget(self.light_btn)
        self.card.add_widget(theme_box)

        # Backend URL Configuration Section
        backend_title = Label(
            text="BACKEND SERVICE URL",
            font_size="11sp",
            bold=True,
            color=theme.text_secondary,
            size_hint_y=None,
            height=dp(16),
            halign="left",
        )
        backend_title.bind(size=backend_title.setter("text_size"))
        self.card.add_widget(backend_title)

        from mobile.src.ui.components import ThemedTextInput
        initial_url = self.ai_service.backend_url if self.ai_service else "http://127.0.0.1:8000"
        self.url_input = ThemedTextInput(
            text=initial_url,
            font_size="13sp",
            size_hint_y=None,
            height=dp(40),
        )
        self.card.add_widget(self.url_input)

        # Test Connection Row
        test_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        test_btn = CalcButton(
            text="Test Backend Connection",
            font_size="12sp",
            size_hint_x=0.6,
            is_operator=True,
        )
        test_row.add_widget(test_btn)
        self.card.add_widget(test_row)

        self.status_lbl = Label(
            text="Status: Untested",
            font_size="11sp",
            color=theme.text_secondary,
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
        )
        self.status_lbl.bind(size=self.status_lbl.setter("text_size"))
        self.card.add_widget(self.status_lbl)

        def _run_connection_test(*a):
            target_url = self.url_input.text.strip()
            if self.ai_service:
                self.ai_service.set_backend_url(target_url)
            self.status_lbl.text = "Testing connection..."

            def _on_result(res):
                from kivy.clock import Clock
                def _update_ui(dt):
                    if res.get("status") == "healthy":
                        key_status = "Key Configured" if res.get("api_key_configured") else "No API Key in .env"
                        self.status_lbl.text = f"● Connected ({res.get('model')}, {key_status})"
                    else:
                        self.status_lbl.text = f"✕ {res.get('detail', 'Connection failed')}"
                Clock.schedule_once(_update_ui, 0)

            if self.ai_service:
                self.ai_service.check_health_async(_on_result)
            else:
                self.status_lbl.text = "AI Service not loaded."

        test_btn.bind(on_release=_run_connection_test)

        # Dismiss / Save Button
        done_btn = CalcButton(
            text="Save & Close",
            size_hint_y=None,
            height=dp(42),
            font_size="13sp",
            is_equals=True,
        )
        def _on_done(*a):
            if self.ai_service and self.url_input.text.strip():
                self.ai_service.set_backend_url(self.url_input.text.strip())
            self.dismiss()

        done_btn.bind(on_release=_on_done)
        self.card.add_widget(done_btn)
