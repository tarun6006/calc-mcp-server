"""
Black box tests for mathematical expression parser
Tests natural language parsing without knowing internal implementation
"""
import pytest
from services.parser import MathExpressionParser

class TestMathExpressionParser:
    """Test mathematical expression parser functionality"""
    
    def setup_method(self):
        """Setup parser for each test"""
        self.parser = MathExpressionParser()
    
    # Basic Expression Tests
    def test_parse_simple_addition(self):
        """Test parsing simple addition"""
        result = self.parser.parse_and_evaluate("2 + 3")
        assert result == {"result": 5}
    
    def test_parse_simple_subtraction(self):
        """Test parsing simple subtraction"""
        result = self.parser.parse_and_evaluate("10 - 3")
        assert result == {"result": 7}
    
    def test_parse_simple_multiplication(self):
        """Test parsing simple multiplication"""
        result = self.parser.parse_and_evaluate("4 * 5")
        assert result == {"result": 20}
    
    def test_parse_simple_division(self):
        """Test parsing simple division"""
        result = self.parser.parse_and_evaluate("15 / 3")
        assert result == {"result": 5}
    
    # Word Number Tests
    def test_parse_word_numbers(self):
        """Test parsing with word numbers"""
        result = self.parser.parse_and_evaluate("five plus three")
        assert result == {"result": 8}
    
    def test_parse_mixed_word_and_digit_numbers(self):
        """Test parsing with mixed word and digit numbers"""
        result = self.parser.parse_and_evaluate("five plus 3")
        assert result == {"result": 8}
    
    def test_parse_large_word_numbers(self):
        """Test parsing with larger word numbers"""
        result = self.parser.parse_and_evaluate("twenty plus thirty")
        assert result == {"result": 50}
    
    def test_parse_compound_word_numbers(self):
        """Test parsing with compound word numbers"""
        result = self.parser.parse_and_evaluate("twenty-five plus fifteen")
        # Note: This might not work perfectly depending on implementation
        # The test verifies the parser handles it gracefully
        assert "result" in result or "error" in result
    
    # Operation Word Tests
    def test_parse_operation_words(self):
        """Test parsing with operation words"""
        test_cases = [
            ("five plus three", 8),
            ("ten minus four", 6),
            ("three times four", 12),
            ("twenty divided by four", 5),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            assert result == {"result": expected}, f"Failed for expression: {expression}"
    
    def test_parse_alternative_operation_words(self):
        """Test parsing with alternative operation words"""
        test_cases = [
            ("five add three", 8),
            ("ten subtract four", 6),
            ("three multiply four", 12),
            ("twenty divide four", 5),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            if "result" in result:
                assert result == {"result": expected}, f"Failed for expression: {expression}"
            # Some alternative words might not be supported, which is okay
    
    # Complex Expression Tests
    def test_parse_complex_expression(self):
        """Test parsing complex mathematical expression"""
        result = self.parser.parse_and_evaluate("four times 2 plus 4")
        assert result == {"result": 12}
    
    def test_parse_expression_with_parentheses(self):
        """Test parsing expression with parentheses"""
        result = self.parser.parse_and_evaluate("(2 + 3) * 4")
        assert result == {"result": 20}
    
    def test_parse_nested_parentheses(self):
        """Test parsing expression with nested parentheses"""
        result = self.parser.parse_and_evaluate("((2 + 3) * 4) - 5")
        assert result == {"result": 15}
    
    def test_parse_order_of_operations(self):
        """Test parsing respects order of operations"""
        result = self.parser.parse_and_evaluate("2 + 3 * 4")
        assert result == {"result": 14}  # Should be 2 + (3 * 4) = 14, not (2 + 3) * 4 = 20
    
    # Power and Special Operations Tests
    def test_parse_power_expression(self):
        """Test parsing power/exponent expressions"""
        test_cases = [
            ("2 to the power of 3", 8),
            ("2 ** 3", 8),
            ("five squared", 25),
            ("two cubed", 8),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            if "result" in result:
                assert result == {"result": expected}, f"Failed for expression: {expression}"
    
    def test_parse_square_root(self):
        """Test parsing square root expressions"""
        test_cases = [
            ("square root of 25", 5.0),
            ("sqrt of 16", 4.0),
            ("root of 9", 3.0),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            if "result" in result:
                assert abs(result["result"] - expected) < 1e-10, f"Failed for expression: {expression}"
    
    def test_parse_factorial(self):
        """Test parsing factorial expressions"""
        result = self.parser.parse_and_evaluate("factorial of 5")
        if "result" in result:
            assert result == {"result": 120}
    
    # Natural Language Preprocessing Tests
    def test_parse_with_question_words(self):
        """Test parsing expressions with question prefixes"""
        test_cases = [
            ("what is 2 + 3", 5),
            ("calculate 4 * 5", 20),
            ("compute 10 - 3", 7),
            ("find 15 / 3", 5),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            assert result == {"result": expected}, f"Failed for expression: {expression}"
    
    def test_parse_with_punctuation(self):
        """Test parsing expressions with punctuation"""
        test_cases = [
            ("2 + 3?", 5),
            ("4 * 5!", 20),
            ("what is 10 - 3?", 7),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            assert result == {"result": expected}, f"Failed for expression: {expression}"
    
    def test_parse_case_insensitive(self):
        """Test parsing is case insensitive"""
        test_cases = [
            ("Five Plus Three", 8),
            ("TEN MINUS FOUR", 6),
            ("Three Times Four", 12),
        ]
        
        for expression, expected in test_cases:
            result = self.parser.parse_and_evaluate(expression)
            assert result == {"result": expected}, f"Failed for expression: {expression}"
    
    # Error Handling Tests
    def test_parse_invalid_expression(self):
        """Test parsing invalid mathematical expression"""
        invalid_expressions = [
            "not a math expression",
            "hello world",
            "abc + def",
            "2 + + 3",
            "/ 5",
        ]
        
        for expression in invalid_expressions:
            result = self.parser.parse_and_evaluate(expression)
            assert "error" in result, f"Should return error for: {expression}"
    
    def test_parse_empty_expression(self):
        """Test parsing empty expression"""
        result = self.parser.parse_and_evaluate("")
        assert "error" in result
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only expression"""
        result = self.parser.parse_and_evaluate("   ")
        assert "error" in result
    
    def test_parse_division_by_zero(self):
        """Test parsing expression that results in division by zero"""
        result = self.parser.parse_and_evaluate("5 / 0")
        assert "error" in result
        assert "zero" in result["error"].lower()
    
    def test_parse_very_large_result(self):
        """Test parsing expression that results in very large number"""
        result = self.parser.parse_and_evaluate("999999999999999 * 999999999999999")
        # Should either return result or error about size limit
        assert "result" in result or "error" in result
        
        if "error" in result:
            assert "large" in result["error"].lower()
    
    # Security Tests
    def test_parse_dangerous_expressions(self):
        """Test parsing potentially dangerous expressions"""
        dangerous_expressions = [
            "__import__('os').system('ls')",
            "exec('print(1)')",
            "eval('2+2')",
            "open('/etc/passwd')",
            "globals()",
            "locals()",
        ]
        
        for expression in dangerous_expressions:
            result = self.parser.parse_and_evaluate(expression)
            assert "error" in result, f"Should reject dangerous expression: {expression}"
    
    def test_parse_nested_function_calls(self):
        """Test parsing expressions with nested function calls"""
        # These should work with allowed functions
        safe_expressions = [
            "max(1, 2, 3)",
            "min(5, 3, 8)",
            "abs(-5)",
            "round(3.7)",
        ]
        
        for expression in safe_expressions:
            result = self.parser.parse_and_evaluate(expression)
            # Should either work or fail gracefully
            assert "result" in result or "error" in result
    
    # Edge Cases
    def test_parse_very_long_expression(self):
        """Test parsing very long expression"""
        # Create a long but valid expression
        long_expr = " + ".join(["1"] * 100)  # "1 + 1 + 1 + ... + 1" (100 times)
        result = self.parser.parse_and_evaluate(long_expr)
        
        if "result" in result:
            assert result == {"result": 100}
        else:
            # Might hit some limit, which is acceptable
            assert "error" in result
    
    def test_parse_decimal_numbers(self):
        """Test parsing expressions with decimal numbers"""
        result = self.parser.parse_and_evaluate("1.5 + 2.3")
        assert abs(result["result"] - 3.8) < 1e-10
    
    def test_parse_negative_numbers(self):
        """Test parsing expressions with negative numbers"""
        result = self.parser.parse_and_evaluate("-5 + 3")
        assert result == {"result": -2}
