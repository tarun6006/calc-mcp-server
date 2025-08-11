"""Mathematical expression parser for natural language processing"""
import re
import math
import logging
import yaml
import os
from decimal import Decimal, InvalidOperation
from typing import Union, Dict, Any
from config.settings import CALC_MAX_VALUE

logger = logging.getLogger(__name__)

class MathExpressionParser:
    """Handles natural language to mathematical expression conversion and evaluation"""
    
    def __init__(self):
        """Initialize parser with configuration from YAML file"""
        self.config = self._load_config()
        parser_config = self.config.get('parser', {})
        self.word_to_number = parser_config.get('word_to_number', {})
        self.operation_words = parser_config.get('operation_words', {})
        self.normalization_config = parser_config.get('normalization', {})
        self.security_config = parser_config.get('security', {})
        self.safe_functions = parser_config.get('safe_functions', {})
        
        logger.debug(f"Parser initialized with {len(self.word_to_number)} word-to-number mappings")
        logger.debug(f"Parser initialized with {len(self.operation_words)} operation word mappings")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info("Configuration loaded successfully")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            # Return default empty configuration
            return {
                'parser': {
                    'word_to_number': {},
                    'operation_words': {},
                    'normalization': {'prefixes': []},
                    'security': {'dangerous_patterns': []},
                    'safe_functions': {}
                }
            }
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration YAML: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            return {}
    
    def parse_and_evaluate(self, expression: str) -> Dict[str, Any]:
        """Main entry point for parsing and evaluating expressions"""
        try:
            logger.debug(f"Parsing expression: {expression}")
            
            # Normalize the expression
            normalized = self._normalize_expression(expression)
            logger.debug(f"Normalized: {normalized}")
            
            # Convert words to mathematical expression
            math_expr = self._convert_to_math_expression(normalized)
            logger.debug(f"Math expression: {math_expr}")
            
            # Evaluate the expression
            result = self._evaluate_expression(math_expr)
            
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Error parsing expression '{expression}': {e}")
            return {"error": f"Could not parse expression: {e}"}
    
    def _normalize_expression(self, expr: str) -> str:
        """Clean and normalize the input expression using configuration"""
        # Convert to lowercase
        expr = expr.lower().strip()
        
        # Remove common prefixes from configuration
        prefixes = self.normalization_config.get('prefixes', [])
        for prefix in prefixes:
            if expr.startswith(prefix):
                expr = expr[len(prefix):].strip()
        
        # Remove characters specified in configuration
        remove_chars = self.normalization_config.get('remove_chars', '[?!]')
        expr = re.sub(remove_chars, '', expr)
        
        # Normalize whitespace if configured
        if self.normalization_config.get('normalize_whitespace', True):
            expr = re.sub(r'\s+', ' ', expr)
        
        return expr
    
    def _convert_to_math_expression(self, expr: str) -> str:
        """Convert natural language to mathematical expression using configuration"""
        # Replace word numbers with digits from configuration
        for word, number in self.word_to_number.items():
            expr = re.sub(r'\b' + re.escape(word) + r'\b', number, expr)
        
        # Replace operation words with symbols from configuration
        for word, symbol in self.operation_words.items():
            if word == 'to the power of':
                expr = re.sub(r'\bto the power of\b', '**', expr)
            elif word == 'square root':
                # Handle "square root of X" pattern
                expr = re.sub(r'\bsquare root of\b', 'sqrt', expr)
            else:
                expr = re.sub(r'\b' + re.escape(word) + r'\b', symbol, expr)
        
        # Handle special cases
        expr = re.sub(r'(\d+)\s*squared', r'(\1)**2', expr)
        expr = re.sub(r'(\d+)\s*cubed', r'(\1)**3', expr)
        
        # Clean up extra spaces around operators
        expr = re.sub(r'\s*([+\-*/()%])\s*', r'\1', expr)
        expr = re.sub(r'\s*(\*\*)\s*', r'\1', expr)
        
        return expr.strip()
    
    def _evaluate_expression(self, expr: str) -> Union[int, float]:
        """Safely evaluate mathematical expression using configuration"""
        # Security: Check for dangerous patterns from configuration
        dangerous_patterns = self.security_config.get('dangerous_patterns', [])
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expr, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous expression: {expr}")
        
        # Handle special functions from configuration
        for func_name, func_mapping in self.safe_functions.items():
            if func_name in expr:
                if func_name == 'factorial':
                    expr = re.sub(rf'{func_name}\(([^)]+)\)', rf'{func_mapping}(int(\1))', expr)
                elif func_name in ['sqrt', 'square root']:
                    # Handle both sqrt and "square root" patterns
                    expr = re.sub(rf'{func_name}\(([^)]+)\)', rf'{func_mapping}(\1)', expr)
                    # Also handle "square root of X" pattern
                    expr = re.sub(r'sqrt\s+of\s+(\d+)', rf'{func_mapping}(\1)', expr)
                else:
                    expr = re.sub(rf'{func_name}\(([^)]+)\)', rf'{func_mapping}(\1)', expr)
        
        # Safe evaluation namespace
        safe_dict = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "round": round,
            "max": max,
            "min": min,
            "sum": sum,
            "pow": pow
        }
        
        try:
            # Evaluate the expression
            result = eval(expr, safe_dict)
            
            # Convert to appropriate numeric type
            if isinstance(result, (int, float)):
                # Check for overflow
                if abs(result) > CALC_MAX_VALUE:
                    raise ValueError(f"Result too large: {result} (max: {CALC_MAX_VALUE})")
                
                # Return as int if it's a whole number, otherwise float
                if isinstance(result, float) and result.is_integer():
                    return int(result)
                return result
            else:
                raise ValueError(f"Invalid result type: {type(result)}")
                
        except ZeroDivisionError:
            raise ValueError("Division by zero")
        except OverflowError:
            raise ValueError("Mathematical overflow")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {e}")
