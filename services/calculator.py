"""Calculator engine with mathematical operations"""
import math
import logging
from decimal import Decimal, InvalidOperation
from typing import Union, List, Dict, Any
from config.settings import CALC_MAX_VALUE
from services.parser import MathExpressionParser

logger = logging.getLogger(__name__)

class CalculatorEngine:
    """Core calculator engine with mathematical operations"""
    
    def __init__(self):
        self.parser = MathExpressionParser()
    
    def _validate_numbers(self, *numbers: Union[int, float]) -> None:
        """Validate input numbers against maximum value limit"""
        for num in numbers:
            if not isinstance(num, (int, float)):
                raise ValueError(f"Invalid number type: {type(num)}")
            if abs(num) > CALC_MAX_VALUE:
                raise ValueError(f"Number too large: {num} (max: {CALC_MAX_VALUE})")
    
    def add(self, *numbers: Union[int, float]) -> Dict[str, Any]:
        """Add multiple numbers together"""
        try:
            if len(numbers) < 2:
                return {"error": "Addition requires at least 2 numbers"}
            
            self._validate_numbers(*numbers)
            result = sum(numbers)
            
            if abs(result) > CALC_MAX_VALUE:
                return {"error": f"Result too large: {result} (max: {CALC_MAX_VALUE})"}
            
            logger.info(f"Addition: {' + '.join(map(str, numbers))} = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Addition error: {e}")
            return {"error": str(e)}
    
    def subtract(self, minuend: Union[int, float], *subtrahends: Union[int, float]) -> Dict[str, Any]:
        """Subtract numbers from the first number"""
        try:
            if len(subtrahends) == 0:
                return {"error": "Subtraction requires at least 2 numbers"}
            
            all_numbers = [minuend] + list(subtrahends)
            self._validate_numbers(*all_numbers)
            
            result = minuend - sum(subtrahends)
            
            if abs(result) > CALC_MAX_VALUE:
                return {"error": f"Result too large: {result} (max: {CALC_MAX_VALUE})"}
            
            logger.info(f"Subtraction: {minuend} - {' - '.join(map(str, subtrahends))} = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Subtraction error: {e}")
            return {"error": str(e)}
    
    def multiply(self, *numbers: Union[int, float]) -> Dict[str, Any]:
        """Multiply multiple numbers together"""
        try:
            if len(numbers) < 2:
                return {"error": "Multiplication requires at least 2 numbers"}
            
            self._validate_numbers(*numbers)
            
            result = 1
            for num in numbers:
                result *= num
                if abs(result) > CALC_MAX_VALUE:
                    return {"error": f"Result too large during multiplication (max: {CALC_MAX_VALUE})"}
            
            logger.info(f"Multiplication: {' × '.join(map(str, numbers))} = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Multiplication error: {e}")
            return {"error": str(e)}
    
    def divide(self, dividend: Union[int, float], *divisors: Union[int, float]) -> Dict[str, Any]:
        """Divide the first number by subsequent numbers"""
        try:
            if len(divisors) == 0:
                return {"error": "Division requires at least 2 numbers"}
            
            all_numbers = [dividend] + list(divisors)
            self._validate_numbers(*all_numbers)
            
            # Check for division by zero
            for divisor in divisors:
                if divisor == 0:
                    return {"error": "Division by zero"}
            
            result = dividend
            for divisor in divisors:
                result /= divisor
                if abs(result) > CALC_MAX_VALUE:
                    return {"error": f"Result too large during division (max: {CALC_MAX_VALUE})"}
            
            logger.info(f"Division: {dividend} ÷ {' ÷ '.join(map(str, divisors))} = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Division error: {e}")
            return {"error": str(e)}
    
    def power(self, base: Union[int, float], exponent: Union[int, float]) -> Dict[str, Any]:
        """Calculate base raised to the power of exponent"""
        try:
            self._validate_numbers(base, exponent)
            
            # Check for potentially dangerous operations
            if abs(exponent) > 1000:
                return {"error": "Exponent too large (max: 1000)"}
            
            result = pow(base, exponent)
            
            if abs(result) > CALC_MAX_VALUE:
                return {"error": f"Result too large: {result} (max: {CALC_MAX_VALUE})"}
            
            logger.info(f"Power: {base}^{exponent} = {result}")
            return {"result": result}
            
        except OverflowError:
            return {"error": "Mathematical overflow in power calculation"}
        except Exception as e:
            logger.error(f"Power calculation error: {e}")
            return {"error": str(e)}
    
    def sqrt(self, number: Union[int, float]) -> Dict[str, Any]:
        """Calculate square root of a number"""
        try:
            self._validate_numbers(number)
            
            if number < 0:
                return {"error": "Cannot calculate square root of negative number"}
            
            result = math.sqrt(number)
            
            logger.info(f"Square root: √{number} = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Square root error: {e}")
            return {"error": str(e)}
    
    def factorial(self, number: Union[int, float]) -> Dict[str, Any]:
        """Calculate factorial of a number"""
        try:
            if not isinstance(number, int) and not (isinstance(number, float) and number.is_integer()):
                return {"error": "Factorial requires a non-negative integer"}
            
            n = int(number)
            if n < 0:
                return {"error": "Factorial requires a non-negative integer"}
            if n > 170:  # Factorial of numbers > 170 causes overflow
                return {"error": "Number too large for factorial calculation (max: 170)"}
            
            result = math.factorial(n)
            
            if result > CALC_MAX_VALUE:
                return {"error": f"Result too large: {result} (max: {CALC_MAX_VALUE})"}
            
            logger.info(f"Factorial: {n}! = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Factorial error: {e}")
            return {"error": str(e)}
    
    def modulo(self, dividend: Union[int, float], divisor: Union[int, float]) -> Dict[str, Any]:
        """Calculate modulo (remainder of division)"""
        try:
            self._validate_numbers(dividend, divisor)
            
            if divisor == 0:
                return {"error": "Division by zero in modulo operation"}
            
            result = dividend % divisor
            
            logger.info(f"Modulo: {dividend} % {divisor} = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Modulo error: {e}")
            return {"error": str(e)}
    
    def absolute(self, number: Union[int, float]) -> Dict[str, Any]:
        """Calculate absolute value of a number"""
        try:
            self._validate_numbers(number)
            
            result = abs(number)
            
            logger.info(f"Absolute: |{number}| = {result}")
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Absolute value error: {e}")
            return {"error": str(e)}
    
    def parse_expression(self, expression: str) -> Dict[str, Any]:
        """Parse and evaluate a complex mathematical expression"""
        try:
            logger.info(f"Parsing expression: {expression}")
            result = self.parser.parse_and_evaluate(expression)
            
            if "result" in result:
                logger.info(f"Expression result: {expression} = {result['result']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Expression parsing error: {e}")
            return {"error": str(e)}
