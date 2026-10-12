"""Safe mathematical calculation engine for CalcAI.

Features:
- Full arithmetic precedence (PEMDAS) and explicit/nested parentheses.
- Implicit multiplication for parentheses: 2(3+4) -> 2*(3+4).
- Auto-closing of unclosed parentheses upon evaluation.
- Full percentage arithmetic: A + B%, A - B%, A * B%, and standalone percentages.
- Strict AST-based expression evaluation prohibiting unrestricted eval().
- Graceful handling of division by zero, incomplete expressions, and invalid inputs.
- Input guards against repeated operator presses, double decimals, and redundant zeros.
- Session calculation history tracking.
"""

import ast
import operator
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class SafeMathEvaluator:
    """Evaluates arithmetic expressions using safe AST traversal."""

    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @classmethod
    def normalize(cls, expression: str) -> str:
        """Sanitize and normalize expression string for safe AST parsing."""
        if not expression or not expression.strip():
            raise ValueError("Incomplete expression")

        s = expression.strip()

        # Normalize symbols to standard Python operators
        s = (
            s.replace("×", "*")
            .replace("÷", "/")
            .replace("−", "-")
            .replace("–", "-")
        )

        # Check for incomplete trailing binary operator (e.g., "5 + " or "10 * ")
        if re.search(r"[+\-*/]\s*$", s):
            raise ValueError("Incomplete expression")

        # Auto-close open parentheses
        opens = s.count("(")
        closes = s.count(")")
        if opens > closes:
            s += ")" * (opens - closes)
        elif closes > opens:
            raise ValueError("Unmatched closing parenthesis")

        # Implicit multiplication:
        # e.g., 2(3+4) -> 2 * (3+4)
        s = re.sub(r"(\d+(\.\d+)?)\s*\(", r"\1 * (", s)
        # e.g., (3+4)2 -> (3+4) * 2
        s = re.sub(r"\)\s*(\d+(\.\d+)?)", r") * \1", s)
        # e.g., (2+3)(4+1) -> (2+3) * (4+1)
        s = re.sub(r"\)\s*\(", r") * (", s)
        # e.g., %( -> % * (
        s = re.sub(r"%\s*\(", r"% * (", s)

        # Standard calculator percentage handling:
        # 1. Additive / Subtractive percentages: A + B% -> (A + (A * (B / 100)))
        def _replace_add_sub_percent(match):
            a, op, b = match.group(1), match.group(3), match.group(4)
            return f"({a} {op} ({a} * ({b} / 100)))"

        s = re.sub(
            r"(\d+(\.\d+)?)\s*([+\-])\s*(\d+(\.\d+)?)%",
            _replace_add_sub_percent,
            s,
        )

        # 2. Parenthesized expressions with trailing percent: (expr)% -> ((expr) / 100)
        s = re.sub(r"(\([^()]+\))%", r"(\1 / 100)", s)

        # 3. Multiplicative, divisive, or standalone percentages: B% -> (B / 100)
        s = re.sub(r"(\d+(\.\d+)?)%", r"(\1 / 100)", s)

        return s

    @classmethod
    def evaluate(cls, expression: str) -> float:
        """Parse and safely evaluate a math expression."""
        normalized = cls.normalize(expression)

        try:
            parsed = ast.parse(normalized, mode="eval")
        except SyntaxError as e:
            raise ValueError("Invalid mathematical syntax") from e

        return cls._eval_node(parsed.body)

    @classmethod
    def _eval_node(cls, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if hasattr(ast, "Num") and isinstance(node, ast.Num):
            return float(node.n)

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in cls._OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} is not allowed")

            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)

            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Cannot divide by zero")

            # Guard against resource exhaustion via massive powers
            if op_type is ast.Pow:
                if abs(right) > 500 or (abs(left) > 1e10 and right > 10):
                    raise OverflowError("Exponent value too large")

            try:
                result = cls._OPERATORS[op_type](left, right)
                if isinstance(result, complex):
                    raise ValueError("Complex numbers are not supported")
                return float(result)
            except OverflowError:
                raise OverflowError("Calculation resulted in overflow")

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in cls._OPERATORS:
                raise ValueError(f"Unary operator {op_type.__name__} is not allowed")
            operand = cls._eval_node(node.operand)
            return float(cls._OPERATORS[op_type](operand))

        raise ValueError(f"Unsupported syntax: {type(node).__name__}")


class CalculatorEngine:
    """State manager for calculator operations, inputs, and session history."""

    def __init__(self):
        self.expression: str = ""
        self.last_result: Optional[str] = None
        self.history: List[Dict[str, str]] = []
        self._just_evaluated: bool = False

    def input_digit(self, digit: str) -> None:
        """Append a digit (0-9) to the current expression with leading zero checks."""
        if self._just_evaluated:
            self.expression = digit
            self._just_evaluated = False
            return

        # Avoid redundant leading zeros like '00'
        tokens = re.split(r"[ +−×÷(]", self.expression)
        last_token = tokens[-1] if tokens else ""
        if last_token == "0" and digit != ".":
            # Replace lone '0' with the new digit
            self.expression = self.expression[:-1] + digit
            return

        # If previous character was a closing parenthesis, insert implicit multiplication
        if self.expression.endswith(")"):
            self.expression += " × " + digit
            return

        self.expression += digit

    def input_operator(self, op: str) -> None:
        """Append or substitute an arithmetic operator (+, −, ×, ÷)."""
        self._just_evaluated = False
        display_op = {"*": "×", "/": "÷", "-": "−", "+": "+"}.get(op, op)

        if not self.expression:
            if display_op == "−":
                self.expression = "−"
            elif self.last_result:
                self.expression = self.last_result + " " + display_op + " "
            return

        # If expression ends with an open parenthesis and operator is minus: allow unary minus
        if self.expression.endswith("("):
            if display_op == "−":
                self.expression += "−"
            return

        # If last part was an operator, cleanly replace it
        stripped = self.expression.rstrip()
        if stripped and stripped[-1] in ("+", "−", "×", "÷"):
            # Check if this was a unary minus preceded by an operator: e.g. "× −"
            if len(stripped) >= 2 and stripped[-2:] in ("×−", "÷−", "+−", "−−"):
                self.expression = stripped[:-2].rstrip() + " " + display_op + " "
            elif display_op == "−" and stripped[-1] in ("×", "÷"):
                # Allow e.g. 5 × −3
                self.expression = stripped + " −"
            else:
                self.expression = stripped[:-1].rstrip() + " " + display_op + " "
        else:
            self.expression = self.expression + " " + display_op + " "

    def input_decimal(self) -> None:
        """Append a decimal point, ensuring only one decimal point per number token."""
        if self._just_evaluated:
            self.expression = "0."
            self._just_evaluated = False
            return

        if not self.expression:
            self.expression = "0."
            return

        if self.expression.endswith(")"):
            self.expression += " × 0."
            return

        tokens = re.split(r"[ +−×÷(]", self.expression)
        last_token = tokens[-1] if tokens else ""

        if "." in last_token:
            return  # Prevent repeated decimal in the same token

        if not last_token or last_token == "−":
            self.expression += "0."
        else:
            self.expression += "."

    def input_parenthesis(self) -> None:
        """Smart parenthesis toggle: inserts '(' or ')' based on expression state."""
        if self._just_evaluated:
            self.expression = "("
            self._just_evaluated = False
            return

        if not self.expression:
            self.expression = "("
            return

        opens = self.expression.count("(")
        closes = self.expression.count(")")
        stripped = self.expression.rstrip()
        last_char = stripped[-1] if stripped else ""

        if last_char in ("+", "−", "×", "÷", "("):
            self.expression += " (" if not self.expression.endswith(" ") and not self.expression.endswith("(") else "("
        elif opens > closes and (last_char.isdigit() or last_char in ("%", ")", ".")):
            self.expression += ")"
        else:
            # If after a number or closed parenthesis and all opens are closed, insert implicit multiplication
            if last_char.isdigit() or last_char in (")", "%"):
                self.expression += " × ("
            else:
                self.expression += "("

    def toggle_sign(self) -> None:
        """Invert sign of active number token or wrap in unary negation."""
        if self._just_evaluated and self.last_result:
            try:
                val = -float(self.last_result)
                res = self.format_number(val)
                self.expression = res
                self.last_result = res
                self._just_evaluated = False
                return
            except ValueError:
                pass

        if not self.expression:
            self.expression = "−"
            return

        if self.expression == "−":
            self.expression = ""
            return

        # If single number, toggle sign
        try:
            val = float(self.expression.replace("−", "-"))
            self.expression = self.format_number(-val).replace("-", "−")
            return
        except ValueError:
            pass

        # If expression ends with a number token after space
        match = re.search(r"(\s*[+−×÷]\s*)(−?)(\d+(\.\d+)?)$", self.expression)
        if match:
            op_part = match.group(1)
            is_neg = bool(match.group(2))
            num_part = match.group(3)
            start_idx = match.start()
            if is_neg:
                # Remove negation
                self.expression = self.expression[:start_idx] + op_part + num_part
            else:
                # Add negation
                self.expression = self.expression[:start_idx] + op_part + "−" + num_part
            return

        # If ends with operator, toggle trailing minus
        if self.expression.endswith(" "):
            self.expression += "−"
        elif self.expression.endswith("−"):
            self.expression = self.expression[:-1]

    def apply_percentage(self) -> None:
        """Append percentage symbol to the current number or closed parenthesis."""
        if not self.expression:
            return

        stripped = self.expression.rstrip()
        if stripped and (stripped[-1].isdigit() or stripped[-1] == ")"):
            self.expression = stripped + "%"

    def backspace(self) -> None:
        """Remove the last token or character."""
        if self._just_evaluated:
            self.clear()
            return

        if not self.expression:
            return

        # If expression ends with an operator with spaces, e.g. " + "
        if self.expression.endswith(" "):
            self.expression = self.expression.rstrip()
            if self.expression and self.expression[-1] in ("+", "−", "×", "÷"):
                self.expression = self.expression[:-1].rstrip()
                return

        self.expression = self.expression[:-1]

    def clear(self) -> None:
        """Reset current expression."""
        self.expression = ""
        self._just_evaluated = False

    def evaluate(self) -> Tuple[str, Optional[str]]:
        """Evaluate the expression. Returns (result_string, error_message)."""
        if not self.expression.strip():
            return "", "Empty expression"

        try:
            val = SafeMathEvaluator.evaluate(self.expression)
            result_str = self.format_number(val)

            # Record to session history
            self.history.append({
                "expression": self.expression.strip(),
                "result": result_str,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
            self.last_result = result_str
            self.expression = result_str
            self._just_evaluated = True
            return result_str, None
        except ZeroDivisionError as e:
            return "Error", str(e)
        except OverflowError as e:
            return "Error", str(e)
        except ValueError as e:
            return "Error", str(e)
        except Exception as e:
            return "Error", "Invalid expression"

    def clear_history(self) -> None:
        """Clear session calculation history."""
        self.history.clear()

    @staticmethod
    def format_number(val: float) -> str:
        """Format numbers cleanly without floating point precision noise."""
        if abs(val - round(val)) < 1e-11:
            return str(int(round(val)))
        # Format up to 8 decimal places, removing redundant trailing zeros
        formatted = f"{val:.8f}".rstrip("0").rstrip(".")
        if formatted in ("-0", "-0.0"):
            return "0"
        return formatted
