"""Main CalcAI Home Screen view.

Combines the compact header, expandable conversational AI assistant panel,
large arithmetic display, and responsive calculator keypad in a single,
clean monochrome mobile layout.
"""

from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ObjectProperty, ListProperty

from mobile.src.ui.theme import theme
from mobile.src.ui.components import (
    ThemedCard,
    CalcButton,
    ThemedTextInput,
    ChatBubble,
    QuickPromptChip,
)
from mobile.src.ui.dialogs import HistoryModal, SettingsModal
from mobile.src.core.calculator import CalculatorEngine
from mobile.src.core.ai_service import AIService


class HomeScreen(BoxLayout):
    """Primary application view containing the AI assistant and calculator."""

    is_ai_expanded = BooleanProperty(False)
    chat_messages = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(14), dp(10), dp(14), dp(10)]
        self.spacing = dp(8)

        # Core logic services
        self.engine = CalculatorEngine()
        self.ai_service = AIService()

        # Initial welcome message in chat history
        self.chat_messages = [
            {
                "sender": "ai",
                "text": (
                    "Welcome to CalcAI! I can help you solve formulas, "
                    "break down math problems step-by-step, or answer general questions.\n\n"
                    "Tap 'Explain with AI' on any calculation below to get an instant breakdown."
                ),
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        ]

        self._build_header()
        self._build_ai_panel()
        self._build_calculator_section()

        # Update root background with theme
        theme.bind(bg_color=self._redraw_background)
        self.bind(pos=self._redraw_background, size=self._redraw_background)
        self._redraw_background()

    def _redraw_background(self, *args):
        from kivy.graphics import Color, Rectangle

        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme.bg_color)
            Rectangle(pos=self.pos, size=self.size)

    # =========================================================================
    # 1. HEADER BAR
    # =========================================================================
    def _build_header(self):
        header = BoxLayout(
            size_hint_y=None,
            height=dp(42),
            spacing=dp(8),
        )

        # App Brand Title & Badge
        brand_box = BoxLayout(spacing=dp(6), size_hint_x=0.6)
        logo = Label(
            text="CalcAI",
            font_size="19sp",
            bold=True,
            color=theme.text_main,
            size_hint_x=None,
            width=dp(70),
            halign="left",
        )
        logo.bind(size=logo.setter("text_size"))

        badge_card = ThemedCard(
            size_hint=(None, None),
            size=(dp(58), dp(22)),
            radius=6,
            pos_hint={"center_y": 0.5},
        )
        badge_lbl = Label(
            text="AI 1.0",
            font_size="10sp",
            bold=True,
            color=theme.text_secondary,
        )
        badge_card.add_widget(badge_lbl)

        brand_box.add_widget(logo)
        brand_box.add_widget(badge_card)
        header.add_widget(brand_box)

        # Action Buttons (History & Settings)
        actions_box = BoxLayout(
            spacing=dp(6),
            size_hint_x=0.4,
            pos_hint={"center_y": 0.5},
        )

        hist_btn = Button(
            text="⏱ History",
            font_size="11sp",
            background_color=(0, 0, 0, 0),
            color=theme.text_secondary,
            bold=True,
        )
        hist_btn.bind(on_release=self._open_history_dialog)

        set_btn = Button(
            text="⚙ Settings",
            font_size="11sp",
            background_color=(0, 0, 0, 0),
            color=theme.text_secondary,
            bold=True,
        )
        set_btn.bind(on_release=self._open_settings_dialog)

        actions_box.add_widget(hist_btn)
        actions_box.add_widget(set_btn)
        header.add_widget(actions_box)

        self.add_widget(header)

    # =========================================================================
    # 2. EXPANDABLE AI ASSISTANT PANEL
    # =========================================================================
    def _build_ai_panel(self):
        self.ai_card = ThemedCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(105),  # Compact height initially
            padding=[dp(12), dp(8)],
            spacing=dp(6),
        )

        # Header of AI Card (Toggle Bar)
        self.ai_card_header = BoxLayout(size_hint_y=None, height=dp(28))
        self.ai_status_lbl = Label(
            text="✦ AI Assistant",
            font_size="12sp",
            bold=True,
            color=theme.text_main,
            halign="left",
        )
        self.ai_status_lbl.bind(size=self.ai_status_lbl.setter("text_size"))

        self.expand_btn = Button(
            text="Expand Chat ▾",
            font_size="11sp",
            bold=True,
            size_hint=(None, 1),
            width=dp(100),
            background_color=(0, 0, 0, 0),
            color=theme.text_secondary,
        )
        self.expand_btn.bind(on_release=self._toggle_ai_expansion)

        self.ai_card_header.add_widget(self.ai_status_lbl)
        self.ai_card_header.add_widget(self.expand_btn)
        self.ai_card.add_widget(self.ai_card_header)

        # --- A. Compact Preview View ---
        self.ai_compact_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(60),
            spacing=dp(4),
        )
        self.ai_preview_lbl = Label(
            text="Ask anything or tap 'Explain with AI' below to break down any formula.",
            font_size="12sp",
            color=theme.text_secondary,
            halign="left",
            valign="middle",
        )
        self.ai_preview_lbl.bind(size=self.ai_preview_lbl.setter("text_size"))
        self.ai_compact_box.add_widget(self.ai_preview_lbl)
        self.ai_card.add_widget(self.ai_compact_box)

        # --- B. Expanded Conversation View ---
        self.ai_expanded_box = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=1,
            opacity=0,
        )

        # Quick Suggestion Chips Row
        chips_scroll = ScrollView(
            size_hint_y=None,
            height=dp(30),
            do_scroll_y=False,
            do_scroll_x=True,
        )
        chips_layout = BoxLayout(
            size_hint_x=None,
            spacing=dp(6),
            height=dp(30),
        )
        chips_layout.bind(minimum_width=chips_layout.setter("width"))

        chip1 = QuickPromptChip(text="Explain last calculation")
        chip1.bind(on_release=lambda *a: self._explain_current_calculation())
        chip2 = QuickPromptChip(text="Help with order of operations")
        chip2.bind(on_release=lambda *a: self._send_user_message("Explain the order of operations in math (PEMDAS)"))
        chip3 = QuickPromptChip(text="Percentage formula")
        chip3.bind(on_release=lambda *a: self._send_user_message("How do percentage calculations work?"))

        chips_layout.add_widget(chip1)
        chips_layout.add_widget(chip2)
        chips_layout.add_widget(chip3)
        chips_scroll.add_widget(chips_layout)
        self.ai_expanded_box.add_widget(chips_scroll)

        # Scrollable Chat Messages Feed
        self.chat_scroll = ScrollView(size_hint_y=1, do_scroll_x=False)
        self.chat_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter("height"))
        self.chat_scroll.add_widget(self.chat_layout)
        self.ai_expanded_box.add_widget(self.chat_scroll)

        # Chat Input Bar
        chat_input_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self.chat_input = ThemedTextInput(
            hint_text="Ask CalcAI anything...",
            font_size="13sp",
            size_hint_x=0.82,
        )
        self.chat_input.bind(on_text_validate=lambda *a: self._on_send_chat())

        send_btn = CalcButton(
            text="➤",
            font_size="16sp",
            size_hint_x=0.18,
            is_equals=True,
        )
        send_btn.bind(on_release=lambda *a: self._on_send_chat())

        chat_input_bar.add_widget(self.chat_input)
        chat_input_bar.add_widget(send_btn)
        self.ai_expanded_box.add_widget(chat_input_bar)

        self.add_widget(self.ai_card)
        self._refresh_chat_feed()

    def _toggle_ai_expansion(self, *args):
        """Toggle between compact preview and expanded conversation view."""
        self.is_ai_expanded = not self.is_ai_expanded
        if self.is_ai_expanded:
            self.ai_card.size_hint_y = 0.52  # Take half the screen
            self.ai_card.height = 0
            self.expand_btn.text = "Collapse ▴"
            self.ai_card.remove_widget(self.ai_compact_box)
            self.ai_expanded_box.opacity = 1
            self.ai_card.add_widget(self.ai_expanded_box)
            Clock.schedule_once(lambda dt: self._scroll_chat_to_bottom(), 0.1)
        else:
            self.ai_card.size_hint_y = None
            self.ai_card.height = dp(105)
            self.expand_btn.text = "Expand Chat ▾"
            self.ai_expanded_box.opacity = 0
            self.ai_card.remove_widget(self.ai_expanded_box)
            self.ai_card.add_widget(self.ai_compact_box)

    def _refresh_chat_feed(self):
        """Render all messages from memory in the chat layout."""
        self.chat_layout.clear_widgets()
        for msg in self.chat_messages:
            bubble = ChatBubble(
                sender=msg["sender"],
                text=msg["text"],
                timestamp=msg.get("timestamp", ""),
            )
            self.chat_layout.add_widget(bubble)

        # Update compact preview with the latest message
        if self.chat_messages:
            latest = self.chat_messages[-1]
            first_line = latest["text"].split("\n")[0][:80]
            self.ai_preview_lbl.text = f"{latest['sender'].upper()}: {first_line}..."

        Clock.schedule_once(lambda dt: self._scroll_chat_to_bottom(), 0.1)

    def _scroll_chat_to_bottom(self):
        if hasattr(self, "chat_scroll"):
            self.chat_scroll.scroll_y = 0

    def _on_send_chat(self):
        text = self.chat_input.text.strip()
        if not text:
            return
        self.chat_input.text = ""
        self._send_user_message(text)

    def _send_user_message(self, text: str, context: dict = None):
        """Append user message, display loading state, and asynchronously query the AI assistant."""
        user_msg = {
            "sender": "user",
            "text": text,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
        self.chat_messages.append(user_msg)

        # Loading indicator bubble in conversation stream
        loading_msg = {
            "sender": "ai",
            "text": "✦ CalcAI is thinking...",
            "timestamp": datetime.now().strftime("%H:%M"),
            "is_loading": True,
        }
        self.chat_messages.append(loading_msg)
        self._refresh_chat_feed()

        # Ensure expanded panel is open so user sees response
        if not self.is_ai_expanded:
            self._toggle_ai_expansion()

        # Query AI service asynchronously
        def _on_success(ai_text: str):
            def _update(dt):
                loading_msg["text"] = ai_text
                loading_msg["is_loading"] = False
                self._refresh_chat_feed()
            Clock.schedule_once(_update, 0)

        def _on_error(err_str: str):
            def _update_err(dt):
                loading_msg["text"] = (
                    f"⚠️ {err_str}\n\n"
                    "Tap 'Settings' to verify the Backend URL and Gemini API key status."
                )
                loading_msg["is_loading"] = False
                loading_msg["is_error"] = True
                self._refresh_chat_feed()
            Clock.schedule_once(_update_err, 0)

        self.ai_service.query(
            prompt=text,
            context=context,
            on_success=_on_success,
            on_error=_on_error,
        )

    # =========================================================================
    # 3. CALCULATOR SECTION
    # =========================================================================
    def _build_calculator_section(self):
        self.calc_container = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=1,
        )

        # A. Display Card
        display_card = ThemedCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(105),
            padding=[dp(16), dp(10)],
            spacing=dp(2),
        )

        # Secondary expression preview (e.g. 125 * 4 + 20)
        self.expr_preview_label = Label(
            text="",
            font_size="15sp",
            color=theme.text_secondary,
            halign="right",
            valign="bottom",
            size_hint_y=0.35,
        )
        self.expr_preview_label.bind(
            size=self.expr_preview_label.setter("text_size")
        )

        # Primary large result / active input
        self.main_display_label = Label(
            text="0",
            font_size="38sp",
            bold=True,
            color=theme.text_main,
            halign="right",
            valign="middle",
            size_hint_y=0.65,
        )
        self.main_display_label.bind(
            size=self.main_display_label.setter("text_size")
        )

        display_card.add_widget(self.expr_preview_label)
        display_card.add_widget(self.main_display_label)
        self.calc_container.add_widget(display_card)

        # B. "Explain Calculation with AI" Button Bar & Parentheses
        explain_bar = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        self.paren_btn = CalcButton(
            text="( )",
            font_size="14sp",
            size_hint_x=0.22,
            is_operator=True,
        )
        self.paren_btn.bind(on_release=lambda *a: self._on_parenthesis())
        explain_bar.add_widget(self.paren_btn)

        self.explain_btn = CalcButton(
            text="✨ Explain with AI",
            font_size="12sp",
            size_hint_x=0.78,
            is_equals=True,
        )
        self.explain_btn.bind(on_release=lambda *a: self._explain_current_calculation())
        explain_bar.add_widget(self.explain_btn)
        self.calc_container.add_widget(explain_bar)

        # C. Responsive Keypad Grid (5 Rows x 4 Columns)
        keypad = GridLayout(
            cols=4,
            spacing=dp(8),
            size_hint_y=1,
        )

        button_specs = [
            # Row 1
            ("C", "action", lambda: self._on_clear()),
            ("±", "action", lambda: self._on_toggle_sign()),
            ("%", "action", lambda: self._on_percent()),
            ("÷", "op", lambda: self._on_operator("÷")),
            # Row 2
            ("7", "num", lambda: self._on_digit("7")),
            ("8", "num", lambda: self._on_digit("8")),
            ("9", "num", lambda: self._on_digit("9")),
            ("×", "op", lambda: self._on_operator("×")),
            # Row 3
            ("4", "num", lambda: self._on_digit("4")),
            ("5", "num", lambda: self._on_digit("5")),
            ("6", "num", lambda: self._on_digit("6")),
            ("−", "op", lambda: self._on_operator("−")),
            # Row 4
            ("1", "num", lambda: self._on_digit("1")),
            ("2", "num", lambda: self._on_digit("2")),
            ("3", "num", lambda: self._on_digit("3")),
            ("+", "op", lambda: self._on_operator("+")),
            # Row 5
            ("0", "num", lambda: self._on_digit("0")),
            (".", "num", lambda: self._on_decimal()),
            ("⌫", "action", lambda: self._on_backspace()),
            ("=", "eq", lambda: self._on_equals()),
        ]

        for label, btn_type, callback in button_specs:
            btn = CalcButton(
                text=label,
                is_operator=(btn_type == "op" or btn_type == "action"),
                is_equals=(btn_type == "eq"),
            )
            # Bind callback safely using closure default
            btn.bind(on_release=lambda inst, cb=callback: cb())
            keypad.add_widget(btn)

        self.calc_container.add_widget(keypad)
        self.add_widget(self.calc_container)

    # =========================================================================
    # 4. CALCULATOR INTERACTION HANDLERS
    # =========================================================================
    def _update_display(self):
        expr = self.engine.expression
        if not expr:
            self.main_display_label.text = "0"
            self.expr_preview_label.text = (
                f"= {self.engine.last_result}" if self.engine.last_result else ""
            )
        else:
            self.main_display_label.text = expr
            self.expr_preview_label.text = ""

    def _on_digit(self, digit: str):
        self.engine.input_digit(digit)
        self._update_display()

    def _on_operator(self, op: str):
        self.engine.input_operator(op)
        self._update_display()

    def _on_parenthesis(self):
        self.engine.input_parenthesis()
        self._update_display()

    def _on_decimal(self):
        self.engine.input_decimal()
        self._update_display()

    def _on_toggle_sign(self):
        self.engine.toggle_sign()
        self._update_display()

    def _on_percent(self):
        self.engine.apply_percentage()
        self._update_display()

    def _on_backspace(self):
        self.engine.backspace()
        self._update_display()

    def _on_clear(self):
        self.engine.clear()
        self._update_display()

    def _on_equals(self):
        active_expr = self.engine.expression.strip()
        if not active_expr:
            return

        res, err = self.engine.evaluate()
        if err:
            self.main_display_label.text = "Error"
            self.expr_preview_label.text = err
        else:
            self.main_display_label.text = res
            self.expr_preview_label.text = active_expr

    def _explain_current_calculation(self):
        """Feed the active expression and result into the AI Assistant as an explanation request."""
        expr = ""
        res = ""
        if self.engine.history:
            last = self.engine.history[-1]
            expr = last.get("expression", "")
            res = last.get("result", "")

        if not expr:
            expr = self.engine.expression or self.expr_preview_label.text or "10 + 5"
            res = self.engine.last_result or self.main_display_label.text or "15"

        prompt = f"Please explain the calculation step-by-step: {expr} = {res}"
        context = {
            "type": "explain_calculation",
            "expression": expr,
            "result": res,
        }
        self._send_user_message(prompt, context=context)

    # =========================================================================
    # 5. DIALOG OPENERS
    # =========================================================================
    def _open_history_dialog(self, *args):
        def _restore_expression(expr: str):
            self.engine.expression = expr
            self._update_display()

        modal = HistoryModal(
            history=self.engine.history,
            on_select=_restore_expression,
            on_clear=self.engine.clear_history,
        )
        modal.open()

    def _open_settings_dialog(self, *args):
        modal = SettingsModal(ai_service=self.ai_service)
        modal.open()
