"""Comprehensive unit and edge-case test suite for CalcAI arithmetic engine."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import unittest
from mobile.src.core.calculator import SafeMathEvaluator, CalculatorEngine


class TestSafeMathEvaluator(unittest.TestCase):
    """Direct tests for SafeMathEvaluator AST parsing and arithmetic rules."""

    def test_basic_operations(self):
        self.assertEqual(SafeMathEvaluator.evaluate("12 + 8"), 20.0)
        self.assertEqual(SafeMathEvaluator.evaluate("25 − 9"), 16.0)
        self.assertEqual(SafeMathEvaluator.evaluate("7 × 6"), 42.0)
        self.assertEqual(SafeMathEvaluator.evaluate("48 ÷ 4"), 12.0)

    def test_arithmetic_precedence_pemdas(self):
        # Multiplication before addition
        self.assertEqual(SafeMathEvaluator.evaluate("3 + 5 × 2"), 13.0)
        # Division before subtraction
        self.assertEqual(SafeMathEvaluator.evaluate("20 − 8 ÷ 2"), 16.0)
        # Mixed compound precedence
        self.assertEqual(SafeMathEvaluator.evaluate("2 + 3 × 4 − 6 ÷ 2"), 11.0)

    def test_parentheses_and_nesting(self):
        # Override standard precedence
        self.assertEqual(SafeMathEvaluator.evaluate("(3 + 5) × 2"), 16.0)
        self.assertEqual(SafeMathEvaluator.evaluate("(20 − 8) ÷ 2"), 6.0)
        # Nested parentheses
        self.assertEqual(SafeMathEvaluator.evaluate("((2 + 3) × (8 − 4)) ÷ 4"), 5.0)

    def test_implicit_multiplication(self):
        # Number before parenthesis: 2(3+4) -> 14
        self.assertEqual(SafeMathEvaluator.evaluate("2(3 + 4)"), 14.0)
        # Parenthesis before number: (3+4)2 -> 14
        self.assertEqual(SafeMathEvaluator.evaluate("(3 + 4)2"), 14.0)
        # Parenthesis before parenthesis: (2+3)(4+1) -> 25
        self.assertEqual(SafeMathEvaluator.evaluate("(2 + 3)(4 + 1)"), 25.0)

    def test_auto_close_parentheses(self):
        # Auto-closing unclosed open parentheses
        self.assertEqual(SafeMathEvaluator.evaluate("(10 + 5 × 2"), 20.0)
        self.assertEqual(SafeMathEvaluator.evaluate("((2 + 3) × 4"), 20.0)

    def test_decimals_and_precision(self):
        res = SafeMathEvaluator.evaluate("0.1 + 0.2")
        self.assertAlmostEqual(res, 0.3, places=6)
        self.assertEqual(SafeMathEvaluator.evaluate("10.5 × 2"), 21.0)
        self.assertEqual(SafeMathEvaluator.evaluate("7.75 − 2.25"), 5.5)

    def test_negative_numbers(self):
        self.assertEqual(SafeMathEvaluator.evaluate("−5 + 12"), 7.0)
        self.assertEqual(SafeMathEvaluator.evaluate("10 × −4"), -40.0)
        self.assertEqual(SafeMathEvaluator.evaluate("−(3 + 7)"), -10.0)
        self.assertEqual(SafeMathEvaluator.evaluate("−5 × −5"), 25.0)

    def test_percentages(self):
        # Standalone percentage
        self.assertEqual(SafeMathEvaluator.evaluate("50%"), 0.5)
        # Percentage addition: 100 + 10% = 110
        self.assertEqual(SafeMathEvaluator.evaluate("100 + 10%"), 110.0)
        # Percentage subtraction: 200 - 25% = 150
        self.assertEqual(SafeMathEvaluator.evaluate("200 − 25%"), 150.0)
        # Percentage multiplication: 200 * 15% = 30
        self.assertEqual(SafeMathEvaluator.evaluate("200 × 15%"), 30.0)
        # Parenthesized expression with percent: (40 + 60)% = 1.0
        self.assertEqual(SafeMathEvaluator.evaluate("(40 + 60)%"), 1.0)

    def test_division_by_zero_and_modulo_zero(self):
        with self.assertRaises(ZeroDivisionError):
            SafeMathEvaluator.evaluate("10 ÷ 0")
        with self.assertRaises(ZeroDivisionError):
            SafeMathEvaluator.evaluate("10 / (5 − 5)")

    def test_incomplete_expressions(self):
        with self.assertRaises(ValueError) as ctx:
            SafeMathEvaluator.evaluate("10 + ")
        self.assertIn("Incomplete expression", str(ctx.exception))

        with self.assertRaises(ValueError):
            SafeMathEvaluator.evaluate("")

    def test_unmatched_closing_parenthesis(self):
        with self.assertRaises(ValueError) as ctx:
            SafeMathEvaluator.evaluate("10 + 5)")
        self.assertIn("Unmatched closing parenthesis", str(ctx.exception))

    def test_security_against_unauthorized_syntax(self):
        # Function calls, imports, variables must raise syntax/eval errors
        disallowed_inputs = [
            "__import__('os').system('ls')",
            "open('/etc/passwd')",
            "lambda x: x + 1",
            "eval('2+2')",
            "import os",
        ]
        for payload in disallowed_inputs:
            with self.assertRaises((ValueError, SyntaxError)):
                SafeMathEvaluator.evaluate(payload)


class TestCalculatorEngine(unittest.TestCase):
    """Stateful tests for CalculatorEngine keypad interactions and history."""

    def setUp(self):
        self.engine = CalculatorEngine()

    def test_digit_input_and_evaluation(self):
        self.engine.input_digit("4")
        self.engine.input_digit("2")
        self.assertEqual(self.engine.expression, "42")
        res, err = self.engine.evaluate()
        self.assertEqual(res, "42")
        self.assertIsNone(err)

    def test_repeated_zero_prevention(self):
        self.engine.input_digit("0")
        self.engine.input_digit("0")
        self.assertEqual(self.engine.expression, "0")
        self.engine.input_digit("5")
        self.assertEqual(self.engine.expression, "5")

    def test_decimal_guards(self):
        self.engine.input_digit("3")
        self.engine.input_decimal()
        self.engine.input_digit("1")
        self.engine.input_decimal()  # Second decimal should be ignored
        self.engine.input_digit("4")
        self.assertEqual(self.engine.expression, "3.14")

    def test_repeated_operator_substitution(self):
        self.engine.input_digit("8")
        self.engine.input_operator("+")
        self.assertEqual(self.engine.expression, "8 + ")
        # Tapping multiply replaces plus
        self.engine.input_operator("×")
        self.assertEqual(self.engine.expression, "8 × ")
        self.engine.input_digit("2")
        res, err = self.engine.evaluate()
        self.assertEqual(res, "16")

    def test_smart_parentheses_flow(self):
        # Type: ( 5 + 3 ) * 2
        self.engine.input_parenthesis()
        self.assertEqual(self.engine.expression, "(")
        self.engine.input_digit("5")
        self.engine.input_operator("+")
        self.engine.input_digit("3")
        self.engine.input_parenthesis()
        self.assertEqual(self.engine.expression, "(5 + 3)")
        self.engine.input_operator("×")
        self.engine.input_digit("2")
        res, err = self.engine.evaluate()
        self.assertEqual(res, "16")

    def test_backspace_behavior(self):
        self.engine.input_digit("1")
        self.engine.input_digit("2")
        self.engine.input_operator("+")
        self.engine.input_digit("3")
        self.assertEqual(self.engine.expression, "12 + 3")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "12 + ")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "12")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "1")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "")

    def test_sign_toggle(self):
        self.engine.input_digit("9")
        self.engine.toggle_sign()
        self.assertEqual(self.engine.expression, "−9")
        self.engine.toggle_sign()
        self.assertEqual(self.engine.expression, "9")

        # Toggle after operator
        self.engine.input_operator("+")
        self.engine.input_digit("5")
        self.engine.toggle_sign()
        self.assertEqual(self.engine.expression, "9 + −5")
        res, err = self.engine.evaluate()
        self.assertEqual(res, "4")

    def test_session_history_tracking(self):
        self.assertEqual(len(self.engine.history), 0)

        # Calculation 1
        self.engine.input_digit("1")
        self.engine.input_operator("+")
        self.engine.input_digit("1")
        self.engine.evaluate()

        # Calculation 2
        self.engine.input_operator("×")
        self.engine.input_digit("5")
        self.engine.evaluate()

        self.assertEqual(len(self.engine.history), 2)
        self.assertEqual(self.engine.history[0]["result"], "2")
        self.assertEqual(self.engine.history[1]["result"], "10")
        self.assertIn("timestamp", self.engine.history[0])

        # Clear history
        self.engine.clear_history()
        self.assertEqual(len(self.engine.history), 0)

    def test_error_handling_division_by_zero(self):
        self.engine.input_digit("5")
        self.engine.input_operator("÷")
        self.engine.input_digit("0")
        res, err = self.engine.evaluate()
        self.assertEqual(res, "Error")
        self.assertIn("Cannot divide by zero", err)

    def test_format_number_cleanup(self):
        # Integer floats show without decimal
        self.assertEqual(CalculatorEngine.format_number(42.0), "42")
        # Floating point rounding
        self.assertEqual(CalculatorEngine.format_number(0.30000000000000004), "0.3")
        # Large integer
        self.assertEqual(CalculatorEngine.format_number(1000000.0), "1000000")
        # Negative zero
        self.assertEqual(CalculatorEngine.format_number(-0.0), "0")


if __name__ == "__main__":
    unittest.main()
