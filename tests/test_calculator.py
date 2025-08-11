"""
Black box tests for calculator engine
Tests mathematical operations without knowing internal implementation
"""
import pytest
from services.calculator import CalculatorEngine

class TestCalculatorEngine:
    """Test calculator engine mathematical operations"""
    
    def setup_method(self):
        """Setup calculator engine for each test"""
        self.calc = CalculatorEngine()
    
    # Addition Tests
    def test_add_two_numbers(self):
        """Test basic addition of two numbers"""
        result = self.calc.add(5, 3)
        assert result == {"result": 8}
    
    def test_add_multiple_numbers(self):
        """Test addition of multiple numbers"""
        result = self.calc.add(1, 2, 3, 4, 5)
        assert result == {"result": 15}
    
    def test_add_negative_numbers(self):
        """Test addition with negative numbers"""
        result = self.calc.add(-5, 3, -2)
        assert result == {"result": -4}
    
    def test_add_decimal_numbers(self):
        """Test addition with decimal numbers"""
        result = self.calc.add(1.5, 2.3, 0.2)
        assert result == {"result": 4.0}
    
    def test_add_single_number_error(self):
        """Test addition with single number returns error"""
        result = self.calc.add(5)
        assert "error" in result
        assert "at least 2 numbers" in result["error"]
    
    def test_add_large_numbers(self):
        """Test addition with large numbers"""
        result = self.calc.add(1000000, 2000000, 3000000)
        assert result == {"result": 6000000}
    
    # Subtraction Tests
    def test_subtract_two_numbers(self):
        """Test basic subtraction"""
        result = self.calc.subtract(10, 3)
        assert result == {"result": 7}
    
    def test_subtract_multiple_numbers(self):
        """Test subtraction with multiple numbers"""
        result = self.calc.subtract(100, 10, 5, 2)
        assert result == {"result": 83}
    
    def test_subtract_negative_result(self):
        """Test subtraction resulting in negative number"""
        result = self.calc.subtract(5, 10)
        assert result == {"result": -5}
    
    def test_subtract_no_subtrahends_error(self):
        """Test subtraction with no subtrahends returns error"""
        result = self.calc.subtract(10)
        assert "error" in result
        assert "at least 2 numbers" in result["error"]
    
    # Multiplication Tests
    def test_multiply_two_numbers(self):
        """Test basic multiplication"""
        result = self.calc.multiply(4, 5)
        assert result == {"result": 20}
    
    def test_multiply_multiple_numbers(self):
        """Test multiplication with multiple numbers"""
        result = self.calc.multiply(2, 3, 4)
        assert result == {"result": 24}
    
    def test_multiply_with_zero(self):
        """Test multiplication with zero"""
        result = self.calc.multiply(5, 0, 10)
        assert result == {"result": 0}
    
    def test_multiply_negative_numbers(self):
        """Test multiplication with negative numbers"""
        result = self.calc.multiply(-2, 3, -4)
        assert result == {"result": 24}
    
    def test_multiply_decimal_numbers(self):
        """Test multiplication with decimal numbers"""
        result = self.calc.multiply(2.5, 4)
        assert result == {"result": 10.0}
    
    # Division Tests
    def test_divide_two_numbers(self):
        """Test basic division"""
        result = self.calc.divide(10, 2)
        assert result == {"result": 5.0}
    
    def test_divide_multiple_numbers(self):
        """Test division with multiple divisors"""
        result = self.calc.divide(100, 2, 5)
        assert result == {"result": 10.0}
    
    def test_divide_by_zero_error(self):
        """Test division by zero returns error"""
        result = self.calc.divide(10, 0)
        assert "error" in result
        assert "Division by zero" in result["error"]
    
    def test_divide_decimal_result(self):
        """Test division resulting in decimal"""
        result = self.calc.divide(7, 2)
        assert result == {"result": 3.5}
    
    def test_divide_no_divisors_error(self):
        """Test division with no divisors returns error"""
        result = self.calc.divide(10)
        assert "error" in result
        assert "at least 2 numbers" in result["error"]
    
    # Power Tests
    def test_power_basic(self):
        """Test basic exponentiation"""
        result = self.calc.power(2, 3)
        assert result == {"result": 8}
    
    def test_power_zero_exponent(self):
        """Test power with zero exponent"""
        result = self.calc.power(5, 0)
        assert result == {"result": 1}
    
    def test_power_negative_exponent(self):
        """Test power with negative exponent"""
        result = self.calc.power(2, -2)
        assert result == {"result": 0.25}
    
    def test_power_decimal_base(self):
        """Test power with decimal base"""
        result = self.calc.power(1.5, 2)
        assert result == {"result": 2.25}
    
    def test_power_large_exponent_error(self):
        """Test power with very large exponent returns error"""
        result = self.calc.power(2, 2000)
        assert "error" in result
        assert "Exponent too large" in result["error"]
    
    # Square Root Tests
    def test_sqrt_perfect_square(self):
        """Test square root of perfect square"""
        result = self.calc.sqrt(25)
        assert result == {"result": 5.0}
    
    def test_sqrt_non_perfect_square(self):
        """Test square root of non-perfect square"""
        result = self.calc.sqrt(2)
        assert abs(result["result"] - 1.4142135623730951) < 1e-10
    
    def test_sqrt_zero(self):
        """Test square root of zero"""
        result = self.calc.sqrt(0)
        assert result == {"result": 0.0}
    
    def test_sqrt_negative_error(self):
        """Test square root of negative number returns error"""
        result = self.calc.sqrt(-4)
        assert "error" in result
        assert "negative number" in result["error"]
    
    # Factorial Tests
    def test_factorial_small_number(self):
        """Test factorial of small number"""
        result = self.calc.factorial(5)
        assert result == {"result": 120}
    
    def test_factorial_zero(self):
        """Test factorial of zero"""
        result = self.calc.factorial(0)
        assert result == {"result": 1}
    
    def test_factorial_negative_error(self):
        """Test factorial of negative number returns error"""
        result = self.calc.factorial(-1)
        assert "error" in result
        assert "non-negative integer" in result["error"]
    
    def test_factorial_decimal_error(self):
        """Test factorial of decimal number returns error"""
        result = self.calc.factorial(3.5)
        assert "error" in result
        assert "non-negative integer" in result["error"]
    
    def test_factorial_large_number_error(self):
        """Test factorial of very large number returns error"""
        result = self.calc.factorial(200)
        assert "error" in result
        assert "too large" in result["error"]
    
    # Modulo Tests
    def test_modulo_basic(self):
        """Test basic modulo operation"""
        result = self.calc.modulo(17, 5)
        assert result == {"result": 2}
    
    def test_modulo_zero_remainder(self):
        """Test modulo with zero remainder"""
        result = self.calc.modulo(10, 5)
        assert result == {"result": 0}
    
    def test_modulo_by_zero_error(self):
        """Test modulo by zero returns error"""
        result = self.calc.modulo(10, 0)
        assert "error" in result
        assert "Division by zero" in result["error"]
    
    def test_modulo_negative_numbers(self):
        """Test modulo with negative numbers"""
        result = self.calc.modulo(-17, 5)
        assert result == {"result": 3}  # Python's modulo behavior
    
    # Absolute Value Tests
    def test_absolute_positive_number(self):
        """Test absolute value of positive number"""
        result = self.calc.absolute(5)
        assert result == {"result": 5}
    
    def test_absolute_negative_number(self):
        """Test absolute value of negative number"""
        result = self.calc.absolute(-5)
        assert result == {"result": 5}
    
    def test_absolute_zero(self):
        """Test absolute value of zero"""
        result = self.calc.absolute(0)
        assert result == {"result": 0}
    
    def test_absolute_decimal(self):
        """Test absolute value of decimal number"""
        result = self.calc.absolute(-3.14)
        assert result == {"result": 3.14}
    
    # Expression Parsing Tests
    def test_parse_expression_simple_addition(self):
        """Test parsing simple addition expression"""
        result = self.calc.parse_expression("2 + 3")
        assert result == {"result": 5}
    
    def test_parse_expression_word_numbers(self):
        """Test parsing expression with word numbers"""
        result = self.calc.parse_expression("five plus three")
        assert result == {"result": 8}
    
    def test_parse_expression_complex(self):
        """Test parsing complex expression"""
        result = self.calc.parse_expression("four times 2 plus 4")
        assert result == {"result": 12}
    
    def test_parse_expression_with_parentheses(self):
        """Test parsing expression with parentheses"""
        result = self.calc.parse_expression("(2 + 3) * 4")
        assert result == {"result": 20}
    
    def test_parse_expression_invalid(self):
        """Test parsing invalid expression returns error"""
        result = self.calc.parse_expression("invalid expression")
        assert "error" in result
    
    def test_parse_expression_empty(self):
        """Test parsing empty expression returns error"""
        result = self.calc.parse_expression("")
        assert "error" in result
    
    # Error Handling Tests
    def test_invalid_number_type(self):
        """Test operations with invalid number types"""
        result = self.calc.add("not_a_number", 5)
        assert "error" in result
    
    def test_very_large_number_error(self):
        """Test operations with numbers exceeding maximum value"""
        from config.settings import CALC_MAX_VALUE
        large_number = CALC_MAX_VALUE * 2
        
        result = self.calc.add(large_number, 1)
        assert "error" in result
        assert "too large" in result["error"]
    
    def test_operation_result_too_large(self):
        """Test operations resulting in values exceeding maximum"""
        from config.settings import CALC_MAX_VALUE
        large_number = CALC_MAX_VALUE / 2
        
        result = self.calc.multiply(large_number, 3)
        assert "error" in result
        assert "too large" in result["error"]
