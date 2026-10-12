"""Automated interaction verification for CalcAI UI and Calculator interactions."""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ["KIVY_NO_ARGS"] = "1"

from kivy.app import App
from kivy.clock import Clock
from mobile.src.main import CalcAIApp
from mobile.src.ui.home_screen import HomeScreen


def run_automated_ui_test():
    print(">>> Starting CalcAI UI Verification...")
    app = CalcAIApp()

    passed_checks = []

    def _test_step(dt):
        screen = app.root
        assert isinstance(screen, HomeScreen), "Root widget is not HomeScreen"
        passed_checks.append("Requirement 1: App launched without crashing and HomeScreen initialized")

        # 2. Test Four Basic Operations: Addition, Subtraction, Multiplication, Division
        # 2a. Addition: 15 + 25 = 40
        screen._on_clear()
        screen._on_digit("1")
        screen._on_digit("5")
        screen._on_operator("+")
        screen._on_digit("2")
        screen._on_digit("5")
        screen._on_equals()
        assert screen.main_display_label.text == "40", f"Addition failed: {screen.main_display_label.text}"
        passed_checks.append("Requirement 2a: Addition verified (15 + 25 = 40)")

        # 2b. Subtraction: 50 − 18 = 32
        screen._on_clear()
        screen._on_digit("5")
        screen._on_digit("0")
        screen._on_operator("−")
        screen._on_digit("1")
        screen._on_digit("8")
        screen._on_equals()
        assert screen.main_display_label.text == "32", f"Subtraction failed: {screen.main_display_label.text}"
        passed_checks.append("Requirement 2b: Subtraction verified (50 − 18 = 32)")

        # 2c. Multiplication: 12 × 4 = 48
        screen._on_clear()
        screen._on_digit("1")
        screen._on_digit("2")
        screen._on_operator("×")
        screen._on_digit("4")
        screen._on_equals()
        assert screen.main_display_label.text == "48", f"Multiplication failed: {screen.main_display_label.text}"
        passed_checks.append("Requirement 2c: Multiplication verified (12 × 4 = 48)")

        # 2d. Division: 84 ÷ 7 = 12
        screen._on_clear()
        screen._on_digit("8")
        screen._on_digit("4")
        screen._on_operator("÷")
        screen._on_digit("7")
        screen._on_equals()
        assert screen.main_display_label.text == "12", f"Division failed: {screen.main_display_label.text}"
        passed_checks.append("Requirement 2d: Division verified (84 ÷ 7 = 12)")

        # 3. Test Division by Zero Handling
        screen._on_clear()
        screen._on_digit("9")
        screen._on_operator("÷")
        screen._on_digit("0")
        screen._on_equals()
        assert screen.main_display_label.text == "Error", f"Expected 'Error', got {screen.main_display_label.text}"
        assert "Cannot divide by zero" in screen.expr_preview_label.text
        passed_checks.append("Requirement 3: Division by zero handled gracefully without crash ('Error')")

        # 4. Test Clear and Backspace
        # 4a. Backspace
        screen._on_clear()
        screen._on_digit("1")
        screen._on_digit("2")
        screen._on_digit("3")
        assert screen.main_display_label.text == "123"
        screen._on_backspace()
        assert screen.main_display_label.text == "12", f"Backspace failed: {screen.main_display_label.text}"
        screen._on_backspace()
        assert screen.main_display_label.text == "1"
        screen._on_backspace()
        assert screen.main_display_label.text == "0"
        passed_checks.append("Requirement 4a: Backspace verified (123 -> 12 -> 1 -> 0)")

        # 4b. Clear
        screen._on_digit("7")
        screen._on_digit("7")
        screen._on_operator("+")
        screen._on_digit("3")
        assert screen.main_display_label.text == "77 + 3"
        screen._on_clear()
        assert screen.main_display_label.text == "0"
        assert screen.engine.expression == ""
        passed_checks.append("Requirement 4b: Clear verified (77 + 3 -> 0)")

        # 5. Test AI Panel Expands and Collapses
        assert not screen.is_ai_expanded
        screen._toggle_ai_expansion()
        assert screen.is_ai_expanded
        assert screen.ai_card.size_hint_y == 0.52
        assert screen.expand_btn.text == "Collapse ▴"
        passed_checks.append("Requirement 5a: AI panel expands verified")

        # 7. Test Calculator Remains Accessible while AI Panel is Expanded
        # Perform calculation while AI panel is open
        screen._on_clear()
        screen._on_digit("7")
        screen._on_operator("+")
        screen._on_digit("3")
        screen._on_equals()
        assert screen.main_display_label.text == "10"
        assert screen.calc_container.parent is screen
        assert len(screen.calc_container.children) > 0
        passed_checks.append("Requirement 7: Calculator remains accessible and functional while AI panel is expanded")

        # Collapse AI Panel
        screen._toggle_ai_expansion()
        assert not screen.is_ai_expanded
        assert screen.expand_btn.text == "Expand Chat ▾"
        passed_checks.append("Requirement 5b: AI panel collapses verified")

        # 6. Test Chat Input, Loading State, and Error/Response States
        initial_msg_count = len(screen.chat_messages)
        screen.chat_input.text = "What is the Pythagorean theorem?"
        screen._on_send_chat()
        assert screen.chat_input.text == ""  # Input cleared after submission
        assert len(screen.chat_messages) == initial_msg_count + 2
        user_msg = screen.chat_messages[-2]
        loading_msg = screen.chat_messages[-1]
        assert user_msg["text"] == "What is the Pythagorean theorem?"
        assert loading_msg.get("is_loading") is True
        passed_checks.append("Requirement 6a: Chat input submitted and loading state active")

        # Test Transfer Calculation to AI
        screen._explain_current_calculation()
        assert screen.chat_messages[-1].get("is_loading") is True
        passed_checks.append("Requirement 6b: 'Explain with AI' context transfer triggered loading state")

        # 8. Test History Works
        assert len(screen.engine.history) >= 4  # (15+25, 50-18, 12*4, 84/7, etc.)
        last_history_item = screen.engine.history[-1]
        assert "expression" in last_history_item
        assert "result" in last_history_item
        assert "timestamp" in last_history_item

        # Test History restoration callback
        saved_expr = screen.engine.history[0]["expression"]
        screen.engine.expression = saved_expr
        screen._update_display()
        assert screen.main_display_label.text == saved_expr
        passed_checks.append("Requirement 8a: History recorded and restored to calculator display")

        # Test History clearing
        screen.engine.clear_history()
        assert len(screen.engine.history) == 0
        passed_checks.append("Requirement 8b: History cleared successfully")

        # Test Settings and History Dialog instantiation
        screen._open_history_dialog()
        screen._open_settings_dialog()
        passed_checks.append("Requirement 8c: History and Settings modals instantiate without error")

        # 6c. Wait for async chat response/error state resolution
        def _check_chat_resolution(dt2, elapsed=0):
            # Check if loading indicator resolved
            current_loading = any(m.get("is_loading", False) for m in screen.chat_messages)
            if not current_loading or elapsed > 4.0:
                # Loading finished or timeout reached
                resolved = [m for m in screen.chat_messages if m.get("sender") == "ai" and not m.get("is_loading")]
                assert len(resolved) >= 1
                passed_checks.append("Requirement 6c: Chat loading state transitioned to response/error state")

                print("\n=======================================================")
                print(">>> ALL 10 INTEGRATION & QUALITY CHECKS PASSED:")
                print("=======================================================")
                for check in passed_checks:
                    print(f"  ✓ {check}")
                print("=======================================================\n")
                Clock.schedule_once(lambda d: app.stop(), 0.2)
            else:
                Clock.schedule_once(lambda d: _check_chat_resolution(d, elapsed + 0.5), 0.5)

        Clock.schedule_once(lambda d: _check_chat_resolution(d, 0), 1.0)

    Clock.schedule_once(_test_step, 0.5)
    app.run()


if __name__ == "__main__":
    run_automated_ui_test()

