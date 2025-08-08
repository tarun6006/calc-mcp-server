import os
import json
import time
import uuid
import threading
import logging
import re
import math
from decimal import Decimal, getcontext, InvalidOperation
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
from queue import Queue
import mcp_utils
from mcp_utils.core import MCPServer
from mcp_utils.schema import CallToolResult, TextContent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Reduce noise from external libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

load_dotenv()

# Environment variables for configuration
CALC_SERVER_NAME = os.getenv("CALC_SERVER_NAME", "calculator-server")
CALC_SERVER_VERSION = os.getenv("CALC_SERVER_VERSION", "1.0")
CALC_PRECISION = int(os.getenv("CALC_PRECISION", "10"))
CALC_MAX_VALUE = float(os.getenv("CALC_MAX_VALUE", "1e15"))

# Set decimal precision
getcontext().prec = CALC_PRECISION

# ==========================================
# CALCULATION ENGINE CLASSES AND FUNCTIONS
# ==========================================

class MathExpressionParser:
    """Advanced math expression parser that handles natural language and symbols"""
    
    # Word to number mappings
    WORD_TO_NUMBER = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000, 'million': 1000000
    }
    
    # Operation word mappings
    OPERATION_WORDS = {
        'plus': '+', 'add': '+', 'added': '+', 'sum': '+', 'total': '+',
        'minus': '-', 'subtract': '-', 'subtracted': '-', 'less': '-', 'difference': '-',
        'times': '*', 'multiply': '*', 'multiplied': '*', 'product': '*', 'of': '*',
        'divide': '/', 'divided': '/', 'quotient': '/', 'over': '/',
        'power': '**', 'raised': '**', 'exponent': '**', 'squared': '**2', 'cubed': '**3'
    }
    
    def __init__(self):
        self.calc = CalculatorEngine()
    
    def parse_and_evaluate(self, expression):
        """Parse natural language expression and evaluate it"""
        try:
            # Clean and normalize the expression
            normalized = self._normalize_expression(expression)
            logger.debug(f"Normalized expression: {normalized}")
            
            # Convert to mathematical expression
            math_expr = self._convert_to_math_expression(normalized)
            logger.debug(f"Math expression: {math_expr}")
            
            # Evaluate the expression
            result = self._evaluate_expression(math_expr)
            return str(result)
            
        except Exception as e:
            logger.error(f"Error parsing expression '{expression}': {str(e)}")
            return f"Error: Unable to parse expression '{expression}'. {str(e)}"
    
    def _normalize_expression(self, expr):
        """Normalize the expression by cleaning and standardizing"""
        # Convert to lowercase and remove extra spaces
        expr = re.sub(r'\s+', ' ', expr.lower().strip())
        
        # Handle common phrase patterns
        expr = re.sub(r'what\s+is\s+', '', expr)
        expr = re.sub(r'calculate\s+', '', expr)
        expr = re.sub(r'compute\s+', '', expr)
        expr = re.sub(r'find\s+', '', expr)
        
        return expr
    
    def _convert_to_math_expression(self, expr):
        """Convert natural language to mathematical expression"""
        # Replace word numbers with digits
        for word, number in self.WORD_TO_NUMBER.items():
            pattern = r'\b' + word + r'\b'
            expr = re.sub(pattern, str(number), expr)
        
        # Replace operation words with symbols
        for word, symbol in self.OPERATION_WORDS.items():
            pattern = r'\b' + word + r'\b'
            if word in ['squared', 'cubed']:
                # Special handling for squared/cubed
                expr = re.sub(r'(\d+(?:\.\d+)?)\s+' + word, r'\1' + symbol, expr)
            else:
                expr = re.sub(pattern, ' ' + symbol + ' ', expr)
        
        # Clean up multiple spaces and operators
        expr = re.sub(r'\s+', ' ', expr)
        expr = re.sub(r'\s*([+\-*/()])\s*', r'\1', expr)
        
        return expr.strip()
    
    def _evaluate_expression(self, expr):
        """Safely evaluate mathematical expression"""
        try:
            # Remove any remaining non-math characters
            expr = re.sub(r'[^0-9+\-*/().e\s]', '', expr)
            
            # Replace ** with pow() for safety
            expr = re.sub(r'(\d+(?:\.\d+)?)\*\*(\d+(?:\.\d+)?)', r'pow(\1,\2)', expr)
            
            # Validate expression safety
            if not self._is_safe_expression(expr):
                raise ValueError("Unsafe mathematical expression")
            
            # Evaluate using Python's eval with restricted namespace
            safe_dict = {
                "__builtins__": {},
                "pow": pow,
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "sum": sum
            }
            
            result = eval(expr, safe_dict, {})
            
            # Validate result
            if abs(result) > CALC_MAX_VALUE:
                raise ValueError(f"Result exceeds maximum allowed value: {CALC_MAX_VALUE}")
            
            return Decimal(str(result)).quantize(Decimal('0.' + '0' * CALC_PRECISION))
            
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {str(e)}")
    
    def _is_safe_expression(self, expr):
        """Check if expression is safe to evaluate"""
        # Check for dangerous patterns
        dangerous_patterns = [
            r'__\w+__',  # Dunder methods
            r'import\s+',  # Import statements
            r'exec\s*\(',  # Exec calls
            r'eval\s*\(',  # Eval calls
            r'open\s*\(',  # File operations
            r'input\s*\(',  # Input calls
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expr, re.IGNORECASE):
                return False
        
        return True


class CalculatorEngine:
    """Core calculation engine with individual operation functions"""
    
    def __init__(self):
        self.precision = CALC_PRECISION
        self.max_value = CALC_MAX_VALUE
        getcontext().prec = self.precision
    
    def _validate_numbers(self, *numbers):
        """Validate input numbers"""
        for num in numbers:
            try:
                decimal_num = Decimal(str(num))
                if abs(decimal_num) > self.max_value:
                    raise ValueError(f"Number {num} exceeds maximum allowed value: {self.max_value}")
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f"Invalid number: {num}")
        return [Decimal(str(num)) for num in numbers]
    
    def add(self, *numbers):
        """Add multiple numbers"""
        if len(numbers) < 2:
            raise ValueError("Addition requires at least 2 numbers")
        
        validated_numbers = self._validate_numbers(*numbers)
        result = sum(validated_numbers)
        
        if abs(result) > self.max_value:
            raise ValueError(f"Result exceeds maximum allowed value: {self.max_value}")
        
        return str(result)
    
    def subtract(self, minuend, *subtrahends):
        """Subtract multiple numbers from the first number"""
        if len(subtrahends) == 0:
            raise ValueError("Subtraction requires at least 2 numbers")
        
        all_numbers = [minuend] + list(subtrahends)
        validated_numbers = self._validate_numbers(*all_numbers)
        
        result = validated_numbers[0]
        for num in validated_numbers[1:]:
            result -= num
        
        if abs(result) > self.max_value:
            raise ValueError(f"Result exceeds maximum allowed value: {self.max_value}")
        
        return str(result)
    
    def multiply(self, *numbers):
        """Multiply multiple numbers"""
        if len(numbers) < 2:
            raise ValueError("Multiplication requires at least 2 numbers")
        
        validated_numbers = self._validate_numbers(*numbers)
        result = Decimal('1')
        
        for num in validated_numbers:
            result *= num
            if abs(result) > self.max_value:
                raise ValueError(f"Result exceeds maximum allowed value: {self.max_value}")
        
        return str(result)
    
    def divide(self, dividend, *divisors):
        """Divide by multiple numbers sequentially"""
        if len(divisors) == 0:
            raise ValueError("Division requires at least 2 numbers")
        
        all_numbers = [dividend] + list(divisors)
        validated_numbers = self._validate_numbers(*all_numbers)
        
        result = validated_numbers[0]
        for num in validated_numbers[1:]:
            if num == 0:
                raise ValueError("Division by zero is not allowed")
            result /= num
        
        if abs(result) > self.max_value:
            raise ValueError(f"Result exceeds maximum allowed value: {self.max_value}")
        
        return str(result)
    
    def power(self, base, exponent):
        """Calculate power (base^exponent)"""
        validated_numbers = self._validate_numbers(base, exponent)
        base, exponent = validated_numbers
        
        try:
            result = base ** exponent
            if abs(result) > self.max_value:
                raise ValueError(f"Result exceeds maximum allowed value: {self.max_value}")
            return str(result)
        except (OverflowError, ValueError) as e:
            raise ValueError(f"Power calculation failed: {str(e)}")
    
    def sqrt(self, number):
        """Calculate square root"""
        validated_numbers = self._validate_numbers(number)
        num = validated_numbers[0]
        
        if num < 0:
            raise ValueError("Cannot calculate square root of negative number")
        
        result = num.sqrt()
        return str(result)
    
    def factorial(self, number):
        """Calculate factorial"""
        validated_numbers = self._validate_numbers(number)
        num = validated_numbers[0]
        
        if num != int(num) or num < 0:
            raise ValueError("Factorial requires a non-negative integer")
        
        num = int(num)
        if num > 170:  # Prevent extremely large factorials
            raise ValueError("Factorial input too large")
        
        result = Decimal(str(math.factorial(num)))
        
        if abs(result) > self.max_value:
            raise ValueError(f"Result exceeds maximum allowed value: {self.max_value}")
        
        return str(result)
    
    def modulo(self, dividend, divisor):
        """Calculate modulo (remainder)"""
        validated_numbers = self._validate_numbers(dividend, divisor)
        dividend, divisor = validated_numbers
        
        if divisor == 0:
            raise ValueError("Modulo by zero is not allowed")
        
        result = dividend % divisor
        return str(result)
    
    def absolute(self, number):
        """Calculate absolute value"""
        validated_numbers = self._validate_numbers(number)
        num = validated_numbers[0]
        
        result = abs(num)
        return str(result)
    
    def parse_expression(self, expression):
        """Parse and evaluate natural language mathematical expression"""
        parser = MathExpressionParser()
        return parser.parse_and_evaluate(expression)

# Initialize calculator engine
calculator = CalculatorEngine()
math_parser = MathExpressionParser()

app = Flask(__name__)
response_queue = Queue()

# Initialize MCP Server with error handling
try:
    mcp = MCPServer(CALC_SERVER_NAME, CALC_SERVER_VERSION, response_queue)
    logger.info("MCPServer initialized with response_queue")
except TypeError as e:
    logger.warning(f"First initialization failed: {e}")
    try:
        mcp = MCPServer(CALC_SERVER_NAME, CALC_SERVER_VERSION)
        if hasattr(mcp, 'response_queue'):
            mcp.response_queue = response_queue
        logger.info("MCPServer initialized without response_queue parameter")
    except Exception as e2:
        logger.warning(f"Second initialization failed: {e2}")
        mcp = MCPServer(name=CALC_SERVER_NAME, version=CALC_SERVER_VERSION)
        if hasattr(mcp, 'response_queue'):
            mcp.response_queue = response_queue
        logger.info("MCPServer initialized with keyword arguments")

# SSE Infrastructure
sse_clients = {}  # Store SSE client connections
sse_requests = {}  # Store pending requests for SSE responses
sse_lock = threading.Lock()

class SSEClient:
    """Represents an SSE client connection"""
    def __init__(self, client_id):
        self.client_id = client_id
        self.queue = Queue()
        self.connected = True
        self.last_heartbeat = time.time()
    
    def send_message(self, message_type, data, request_id=None):
        """Send a message to the SSE client"""
        if not self.connected:
            return False
        
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": time.time()
            }
            if request_id:
                message["request_id"] = request_id
            
            self.queue.put(f"data: {json.dumps(message)}\n\n")
            return True
        except Exception as e:
            logger.error(f"Failed to send SSE message to {self.client_id}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Mark client as disconnected"""
        self.connected = False


def cleanup_disconnected_clients():
    """Remove disconnected clients from the registry"""
    with sse_lock:
        disconnected = [client_id for client_id, client in sse_clients.items() 
                       if not client.connected or (time.time() - client.last_heartbeat) > 300]
        for client_id in disconnected:
            logger.info(f"Removing disconnected SSE client: {client_id}")
            sse_clients.pop(client_id, None)


def send_sse_response(client_id, request_id, response_data):
    """Send MCP response via SSE to specific client"""
    with sse_lock:
        client = sse_clients.get(client_id)
        if client:
            success = client.send_message("mcp_response", response_data, request_id)
            if success:
                logger.debug(f"Sent SSE response to client {client_id} for request {request_id}")
            return success
        else:
            logger.warning(f"SSE client {client_id} not found for response")
            return False


def heartbeat_worker():
    """Background worker to send heartbeats and clean up disconnected clients"""
    while True:
        try:
            cleanup_disconnected_clients()
            
            with sse_lock:
                for client_id, client in list(sse_clients.items()):
                    if client.connected:
                        client.send_message("heartbeat", {"timestamp": time.time()})
            
            time.sleep(30)  # Send heartbeat every 30 seconds
        except Exception as e:
            logger.error(f"Heartbeat worker error: {e}")
            time.sleep(5)


# Start heartbeat worker in background
heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
heartbeat_thread.start()


# ==========================================
# MCP TOOL DEFINITIONS USING CALCULATOR ENGINE
# ==========================================


@mcp.tool()
def add(*numbers: float) -> CallToolResult:
    """Add multiple numbers together.
    
    Args:
        numbers: Numbers to add (minimum 2 required)
    
    Returns:
        The sum of all numbers
    """
    try:
        logger.info(f"Addition request: {numbers}")
        result = calculator.add(*numbers)
        logger.info(f"Addition result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Addition error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])


@mcp.tool()
def subtract(minuend: float, *subtrahends: float) -> CallToolResult:
    """Subtract multiple numbers from the first number.
    
    Args:
        minuend: Number to subtract from
        subtrahends: Numbers to subtract (minimum 1 required)
    
    Returns:
        The result after subtracting all subtrahends from minuend
    """
    try:
        logger.info(f"Subtraction request: {minuend} - {subtrahends}")
        result = calculator.subtract(minuend, *subtrahends)
        logger.info(f"Subtraction result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Subtraction error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])


@mcp.tool()
def multiply(*numbers: float) -> CallToolResult:
    """Multiply multiple numbers together.
    
    Args:
        numbers: Numbers to multiply (minimum 2 required)
    
    Returns:
        The product of all numbers
    """
    try:
        logger.info(f"Multiplication request: {numbers}")
        result = calculator.multiply(*numbers)
        logger.info(f"Multiplication result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Multiplication error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])


@mcp.tool()
def divide(dividend: float, *divisors: float) -> CallToolResult:
    """Divide by multiple numbers sequentially.
    
    Args:
        dividend: Number to be divided
        divisors: Numbers to divide by (minimum 1 required)
    
    Returns:
        The result after dividing by all divisors sequentially
    """
    try:
        logger.info(f"Division request: {dividend} / {divisors}")
        result = calculator.divide(dividend, *divisors)
        logger.info(f"Division result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Division error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])


@mcp.tool()
def power(base: float, exponent: float) -> CallToolResult:
    """Raise base to the power of exponent.
    
    Args:
        base: Base number
        exponent: Exponent
    
    Returns:
        The result of base raised to the power of exponent
    """
    try:
        logger.info(f"Power request: {base} ^ {exponent}")
        result = calculator.power(base, exponent)
        logger.info(f"Power result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Power error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])

@mcp.tool()
def sqrt(number: float) -> CallToolResult:
    """Calculate square root of a number.
    
    Args:
        number: Number to calculate square root of
    
    Returns:
        The square root of the number
    """
    try:
        logger.info(f"Square root request: sqrt({number})")
        result = calculator.sqrt(number)
        logger.info(f"Square root result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Square root error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])

@mcp.tool()
def factorial(number: int) -> CallToolResult:
    """Calculate factorial of a number.
    
    Args:
        number: Non-negative integer to calculate factorial of
    
    Returns:
        The factorial of the number
    """
    try:
        logger.info(f"Factorial request: {number}!")
        result = calculator.factorial(number)
        logger.info(f"Factorial result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Factorial error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])

@mcp.tool()
def modulo(dividend: float, divisor: float) -> CallToolResult:
    """Calculate modulo (remainder) of division.
    
    Args:
        dividend: Number to be divided
        divisor: Number to divide by
    
    Returns:
        The remainder after division
    """
    try:
        logger.info(f"Modulo request: {dividend} % {divisor}")
        result = calculator.modulo(dividend, divisor)
        logger.info(f"Modulo result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Modulo error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])

@mcp.tool()
def absolute(number: float) -> CallToolResult:
    """Calculate absolute value of a number.
    
    Args:
        number: Number to calculate absolute value of
    
    Returns:
        The absolute value of the number
    """
    try:
        logger.info(f"Absolute value request: |{number}|")
        result = calculator.absolute(number)
        logger.info(f"Absolute value result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Absolute value error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])

@mcp.tool()
def parse_expression(expression: str) -> CallToolResult:
    """Parse and evaluate natural language mathematical expressions.
    
    This tool can handle complex expressions like:
    - "four times 2 plus 4" = 12
    - "what is 10 divided by 2 minus 3" = 2
    - "calculate 5 squared plus 3 cubed" = 52
    - Mixed symbols and words: "5 * two + 3" = 13
    
    Args:
        expression: Natural language mathematical expression
    
    Returns:
        The result of evaluating the expression
    """
    try:
        logger.info(f"Expression parsing request: '{expression}'")
        result = math_parser.parse_and_evaluate(expression)
        logger.info(f"Expression result: {result}")
        return CallToolResult(content=[TextContent(type='text', text=result)])
    except Exception as e:
        error_msg = f"Expression parsing error: {str(e)}"
        logger.error(error_msg)
        return CallToolResult(content=[TextContent(type='text', text=error_msg)])


@app.route("/sse/connect", methods=["GET"])
def sse_connect():
    """Establish SSE connection for MCP communication"""
    client_id = request.args.get("client_id")
    if not client_id:
        client_id = str(uuid.uuid4())
    
    logger.info(f"SSE client connecting: {client_id}")
    
    def event_stream():
        # Create and register SSE client
        with sse_lock:
            sse_client = SSEClient(client_id)
            sse_clients[client_id] = sse_client
        
        # Send connection confirmation
        sse_client.send_message("connected", {"client_id": client_id, "server": CALC_SERVER_NAME})
        
        try:
            while sse_client.connected:
                try:
                    # Get message from client's queue (blocking with timeout)
                    message = sse_client.queue.get(timeout=30)
                    yield message
                    sse_client.last_heartbeat = time.time()
                except:
                    # Send heartbeat if no messages
                    sse_client.send_message("heartbeat", {"timestamp": time.time()})
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
        except GeneratorExit:
            logger.info(f"SSE client disconnected: {client_id}")
        finally:
            # Clean up on disconnect
            sse_client.disconnect()
            with sse_lock:
                sse_clients.pop(client_id, None)
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )


@app.route("/sse/mcp", methods=["POST"])
def handle_sse_mcp():
    """Handle MCP requests via SSE"""
    body = request.get_json()
    client_id = body.get("client_id") if body else None
    
    if not client_id:
        return jsonify({"error": "client_id required for SSE MCP requests"}), 400
    
    logger.debug(f"SSE MCP request from client {client_id}: {body}")
    
    try:
        # Extract the actual MCP request
        mcp_request = body.get("mcp_request", {})
        request_id = body.get("request_id", str(uuid.uuid4()))
        
        # Process MCP request
        response = mcp.handle_message(mcp_request)
        
        if hasattr(response, 'model_dump'):
            response_data = response.model_dump(exclude_none=True)
        elif hasattr(response, 'dict'):
            response_data = response.dict(exclude_none=True)
        elif isinstance(response, dict):
            response_data = response
        else:
            try:
                response_data = response.__dict__
            except:
                response_data = {"error": "Unable to serialize response"}
                logger.error("Failed to serialize MCP response")
        
        # Send response via SSE
        success = send_sse_response(client_id, request_id, response_data)
        
        if success:
            return jsonify({"status": "sent", "request_id": request_id}), 200
        else:
            return jsonify({"error": "Failed to send SSE response", "request_id": request_id}), 500
        
    except Exception as e:
        error_msg = f"SSE MCP request handling failed: {str(e)}"
        logger.error(error_msg)
        
        # Try to send error via SSE
        error_response = {"error": error_msg}
        send_sse_response(client_id, request_id, error_response)
        
        return jsonify({"error": error_msg}), 500


@app.route("/mcp", methods=["POST"])
def handle_mcp():
    """Handle traditional HTTP MCP requests (kept for compatibility)"""
    body = request.get_json()
    logger.debug(f"HTTP MCP request received: {body}")
    
    try:
        response = mcp.handle_message(body)
        
        if hasattr(response, 'model_dump'):
            response_data = response.model_dump(exclude_none=True)
        elif hasattr(response, 'dict'):
            response_data = response.dict(exclude_none=True)
        elif isinstance(response, dict):
            response_data = response
        else:
            try:
                response_data = response.__dict__
            except:
                response_data = {"error": "Unable to serialize response"}
                logger.error("Failed to serialize MCP response")
        
        logger.debug(f"HTTP MCP response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"HTTP MCP request handling failed: {e}")
        return jsonify({"error": f"MCP request handling failed: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "service": CALC_SERVER_NAME,
        "version": CALC_SERVER_VERSION,
        "precision": CALC_PRECISION,
        "max_value": CALC_MAX_VALUE
    }), 200


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with service information"""
    with sse_lock:
        active_sse_clients = len([c for c in sse_clients.values() if c.connected])
    
    return jsonify({
        "service": CALC_SERVER_NAME,
        "version": CALC_SERVER_VERSION,
        "description": "MCP Calculator Server - Provides mathematical operations via MCP protocol with SSE support",
        "transport_modes": {
            "sse": "Server-Sent Events (primary)",
            "http": "Traditional HTTP (compatibility)"
        },
        "endpoints": {
            "/sse/connect": "SSE connection endpoint (GET)",
            "/sse/mcp": "SSE MCP protocol endpoint (POST)",
            "/mcp": "HTTP MCP protocol endpoint (POST)",
            "/health": "Health check endpoint (GET)",
            "/": "Service information (GET)"
        },
        "available_tools": [
            "add(a, b) - Add two numbers",
            "subtract(a, b) - Subtract b from a",
            "multiply(a, b) - Multiply two numbers",
            "divide(a, b) - Divide a by b",
            "power(a, b) - Raise a to power of b"
        ],
        "configuration": {
            "precision": CALC_PRECISION,
            "max_value": CALC_MAX_VALUE
        },
        "status": {
            "active_sse_clients": active_sse_clients,
            "total_registered_clients": len(sse_clients)
        }
    }), 200


if __name__ == "__main__":
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logging.getLogger().setLevel(getattr(logging, log_level))
        logger.info(f"Log level set to: {log_level}")
    
    port = int(os.environ.get("PORT", 5003))
    is_cloud = os.environ.get("K_SERVICE") is not None or os.environ.get("PORT") == "8080"
    environment = "Cloud" if is_cloud else "Local"
    
    logger.info(f"Starting MCP Calculator Server on port {port} ({environment})")
    logger.info("Configuration:")
    logger.info(f"   - Service: {CALC_SERVER_NAME} v{CALC_SERVER_VERSION}")
    logger.info(f"   - Transport: SSE (primary) + HTTP (compatibility)")
    logger.info(f"   - Precision: {CALC_PRECISION} decimal places")
    logger.info(f"   - Max Value: {CALC_MAX_VALUE}")
    logger.info("Available Endpoints:")
    logger.info("   - /sse/connect - SSE connection endpoint")
    logger.info("   - /sse/mcp - SSE MCP requests")
    logger.info("   - /mcp - HTTP MCP requests (compatibility)")
    logger.info("   - /health - Health check")
    logger.info("Available Tools:")
    logger.info("   - add(a, b) - Addition")
    logger.info("   - subtract(a, b) - Subtraction") 
    logger.info("   - multiply(a, b) - Multiplication")
    logger.info("   - divide(a, b) - Division")
    logger.info("   - power(a, b) - Exponentiation")
    
    app.run(host="0.0.0.0", port=port, debug=not is_cloud)
