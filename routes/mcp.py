"""MCP protocol endpoints"""
import json
import logging
from flask import Blueprint, request, jsonify
from services.calculator import CalculatorEngine

logger = logging.getLogger(__name__)

mcp_bp = Blueprint('mcp', __name__)
calculator = CalculatorEngine()

# MCP tools registry
MCP_TOOLS = {
    "add": {
        "description": "Add multiple numbers together. Can handle 2 or more numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numbers to add"
                }
            },
            "required": ["numbers"]
        }
    },
    "subtract": {
        "description": "Subtract numbers. First number minus all subsequent numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "minuend": {
                    "type": "number",
                    "description": "The number to subtract from"
                },
                "subtrahends": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numbers to subtract"
                }
            },
            "required": ["minuend", "subtrahends"]
        }
    },
    "multiply": {
        "description": "Multiply multiple numbers together. Can handle 2 or more numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numbers to multiply"
                }
            },
            "required": ["numbers"]
        }
    },
    "divide": {
        "description": "Divide numbers. First number divided by all subsequent numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dividend": {
                    "type": "number",
                    "description": "The number to be divided"
                },
                "divisors": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numbers to divide by"
                }
            },
            "required": ["dividend", "divisors"]
        }
    },
    "power": {
        "description": "Calculate exponentiation (base raised to the power of exponent).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base": {
                    "type": "number",
                    "description": "The base number"
                },
                "exponent": {
                    "type": "number",
                    "description": "The exponent"
                }
            },
            "required": ["base", "exponent"]
        }
    },
    "sqrt": {
        "description": "Calculate square root of a number.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {
                    "type": "number",
                    "description": "The number to find square root of"
                }
            },
            "required": ["number"]
        }
    },
    "factorial": {
        "description": "Calculate factorial of a number (n!).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {
                    "type": "integer",
                    "description": "The number to calculate factorial of (must be non-negative integer)"
                }
            },
            "required": ["number"]
        }
    },
    "modulo": {
        "description": "Calculate modulo (remainder of division).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dividend": {
                    "type": "number",
                    "description": "The number to be divided"
                },
                "divisor": {
                    "type": "number",
                    "description": "The number to divide by"
                }
            },
            "required": ["dividend", "divisor"]
        }
    },
    "absolute": {
        "description": "Calculate absolute value of a number.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {
                    "type": "number",
                    "description": "The number to find absolute value of"
                }
            },
            "required": ["number"]
        }
    },
    "parse_expression": {
        "description": "Parse and evaluate complex mathematical expressions from natural language. Handles multi-number operations, mixed symbols/words, and complex expressions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Natural language mathematical expression"
                }
            },
            "required": ["expression"]
        }
    }
}

@mcp_bp.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """Handle MCP protocol requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None
            }), 400
        
        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')
        
        logger.debug(f"MCP request: {method} with params: {params}")
        
        if method == 'tools/list':
            return jsonify({
                "jsonrpc": "2.0",
                "result": {"tools": [{"name": name, **schema} for name, schema in MCP_TOOLS.items()]},
                "id": request_id
            })
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            if tool_name not in MCP_TOOLS:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                    "id": request_id
                }), 404
            
            # Call the appropriate calculator method
            result = call_calculator_method(tool_name, arguments)
            
            return jsonify({
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            })
        
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }), 404
    
    except Exception as e:
        logger.error(f"MCP request error: {e}")
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": data.get('id') if 'data' in locals() else None
        }), 500

def call_calculator_method(tool_name: str, arguments: dict) -> dict:
    """Call the appropriate calculator method based on tool name"""
    try:
        if tool_name == "add":
            numbers = arguments.get("numbers", [])
            return calculator.add(*numbers)
        
        elif tool_name == "subtract":
            minuend = arguments.get("minuend")
            subtrahends = arguments.get("subtrahends", [])
            return calculator.subtract(minuend, *subtrahends)
        
        elif tool_name == "multiply":
            numbers = arguments.get("numbers", [])
            return calculator.multiply(*numbers)
        
        elif tool_name == "divide":
            dividend = arguments.get("dividend")
            divisors = arguments.get("divisors", [])
            return calculator.divide(dividend, *divisors)
        
        elif tool_name == "power":
            base = arguments.get("base")
            exponent = arguments.get("exponent")
            return calculator.power(base, exponent)
        
        elif tool_name == "sqrt":
            number = arguments.get("number")
            return calculator.sqrt(number)
        
        elif tool_name == "factorial":
            number = arguments.get("number")
            return calculator.factorial(number)
        
        elif tool_name == "modulo":
            dividend = arguments.get("dividend")
            divisor = arguments.get("divisor")
            return calculator.modulo(dividend, divisor)
        
        elif tool_name == "absolute":
            number = arguments.get("number")
            return calculator.absolute(number)
        
        elif tool_name == "parse_expression":
            expression = arguments.get("expression", "")
            return calculator.parse_expression(expression)
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        logger.error(f"Calculator method error for {tool_name}: {e}")
        return {"error": str(e)}
