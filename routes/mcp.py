"""MCP protocol endpoints"""
import json
import logging
from flask import Blueprint, request, jsonify
from services.calculator import CalculatorEngine
from config.settings import CONFIG

logger = logging.getLogger(__name__)

mcp_bp = Blueprint('mcp', __name__)
calculator = CalculatorEngine()

# Load MCP tools registry from config
MCP_TOOLS = CONFIG.get('mcp_tools', {})

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
        
        if method == 'initialize':
            # MCP protocol initialization
            protocol_version = params.get('protocolVersion', '2024-11-05')
            client_info = params.get('clientInfo', {})
            
            logger.info(f"MCP client initialized: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}")
            
            return jsonify({
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": protocol_version,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "calculator-server",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            })
        
        elif method == 'tools/list':
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
