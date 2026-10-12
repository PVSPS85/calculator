"""Reusable UI components for CalcAI.

Provides custom-drawn widgets for cards, calculator buttons, chat bubbles,
and styled inputs respecting the monochrome design system.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty

from mobile.src.ui.theme import theme


class ThemedCard(BoxLayout):
    """Container with rounded corners, background color, and a subtle border."""

    bg_color = ListProperty([0, 0, 0, 0])
    border_color = ListProperty([0, 0, 0, 0])
    radius = NumericProperty(14)
    border_width = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.bg_color or self.bg_color == [0, 0, 0, 0]:
            self.bg_color = theme.card_color
        if not self.border_color or self.border_color == [0, 0, 0, 0]:
            self.border_color = theme.border_color

        theme.bind(
            card_color=self._update_theme_colors,
            border_color=self._update_theme_colors,
        )
        self.bind(pos=self._redraw, size=self._redraw)

    def _update_theme_colors(self, *args):
        self.bg_color = theme.card_color
        self.border_color = theme.border_color
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(self.radius)]
            )
            Color(*self.border_color)
            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(self.radius),
                ),
                width=dp(self.border_width),
            )


class CalcButton(Button):
    """Responsive calculator button with custom surface color and tactile feedback."""

    normal_bg = ListProperty([0.08, 0.08, 0.08, 1])
    is_operator = BooleanProperty(False)
    is_equals = BooleanProperty(False)
    radius = NumericProperty(12)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.background_down = ""
        self.bold = True
        self.font_size = "20sp"
        self.color = theme.text_main

        theme.bind(
            text_main=self._on_theme_change,
            button_num=self._on_theme_change,
            button_op=self._on_theme_change,
            button_eq=self._on_theme_change,
        )
        self._apply_initial_color()
        self.bind(pos=self._redraw, size=self._redraw, state=self._redraw)

    def _apply_initial_color(self):
        if self.is_equals:
            self.normal_bg = theme.button_eq
        elif self.is_operator:
            self.normal_bg = theme.button_op
        else:
            self.normal_bg = theme.button_num

    def _on_theme_change(self, *args):
        self.color = theme.text_main
        self._apply_initial_color()
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == "down":
                Color(*theme.button_pressed)
            else:
                Color(*self.normal_bg)

            RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(self.radius)]
            )
            Color(*theme.border_color)
            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(self.radius),
                ),
                width=dp(1),
            )


class ThemedTextInput(TextInput):
    """Styled input field with custom surface background, padding, and border."""

    radius = NumericProperty(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.background_active = ""
        self.foreground_color = theme.text_main
        self.hint_text_color = theme.text_secondary
        self.cursor_color = theme.text_main
        self.padding = [dp(12), dp(10), dp(12), dp(10)]
        self.multiline = False

        theme.bind(
            text_main=lambda *a: setattr(self, "foreground_color", theme.text_main),
            text_secondary=lambda *a: setattr(self, "hint_text_color", theme.text_secondary),
        )
        self.bind(pos=self._redraw, size=self._redraw, focus=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme.surface_color)
            RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(self.radius)]
            )
            # Active focus indicator: brighter border when focused
            if self.focus:
                Color(0.5, 0.5, 0.5, 1)
            else:
                Color(*theme.border_color)
            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(self.radius),
                ),
                width=dp(1),
            )


class ChatBubble(BoxLayout):
    """Conversational bubble with role identification, text wrapping, and timestamp."""

    sender = StringProperty("ai")  # 'user' or 'ai'
    message_text = StringProperty("")
    timestamp = StringProperty("")

    def __init__(self, sender: str, text: str, timestamp: str = "", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(12), dp(10), dp(12), dp(10)]
        self.spacing = dp(4)
        self.sender = sender
        self.message_text = text
        self.timestamp = timestamp

        # Sender label
        role_title = "You" if sender == "user" else "CalcAI Assistant"
        self.header_label = Label(
            text=f"{role_title}  •  {timestamp}" if timestamp else role_title,
            font_size="11sp",
            bold=True,
            color=theme.text_secondary,
            size_hint_y=None,
            height=dp(16),
            halign="left",
        )
        self.header_label.bind(size=self.header_label.setter("text_size"))
        self.add_widget(self.header_label)

        # Content label with word wrapping
        self.content_label = Label(
            text=text,
            font_size="13sp",
            color=theme.text_main,
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        # Dynamic height calculation based on wrapped texture size
        self.content_label.bind(
            width=lambda instance, val: setattr(instance, "text_size", (val, None)),
            texture_size=self._update_content_height,
        )
        self.add_widget(self.content_label)

        self.bind(pos=self._redraw, size=self._redraw)

    def _update_content_height(self, instance, size):
        self.content_label.height = max(dp(22), size[1])
        self.height = self.header_label.height + self.content_label.height + dp(24)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.sender == "user":
                Color(*theme.user_bubble)
            else:
                Color(*theme.ai_bubble)
            RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(12)]
            )
            Color(*theme.border_color)
            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(12),
                ),
                width=dp(1),
            )


class QuickPromptChip(Button):
    """Clickable prompt chip for contextual suggestions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.background_down = ""
        self.font_size = "11sp"
        self.size_hint = (None, None)
        self.height = dp(28)
        self.padding = [dp(10), dp(4)]
        self.color = theme.text_secondary

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            texture_size=lambda inst, val: setattr(self, "width", val[0] + dp(20)),
        )

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme.surface_color)
            RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(14)]
            )
            Color(*theme.border_color)
            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(14),
                ),
                width=dp(1),
            )
