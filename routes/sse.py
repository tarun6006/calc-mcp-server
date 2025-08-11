"""SSE (Server-Sent Events) endpoints for real-time communication"""
import json
import time
import logging
import uuid
from flask import Blueprint, request, Response, jsonify
from typing import Dict, Set
from routes.mcp import call_calculator_method

logger = logging.getLogger(__name__)

sse_bp = Blueprint('sse', __name__)

# Global storage for SSE clients
sse_clients: Dict[str, Dict] = {}
active_connections: Set[str] = set()

def generate_sse_response(client_id: str):
    """Generate SSE response stream for a client"""
    def event_stream():
        try:
            logger.info(f"Starting SSE stream for client {client_id}")
            
            # Send initial connection confirmation
            yield f"event: connected\ndata: {json.dumps({'client_id': client_id, 'status': 'connected'})}\n\n"
            
            # Keep connection alive with periodic heartbeats
            last_heartbeat = time.time()
            
            while client_id in active_connections:
                current_time = time.time()
                
                # Send heartbeat every 30 seconds
                if current_time - last_heartbeat > 30:
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': current_time})}\n\n"
                    last_heartbeat = current_time
                
                # Check for pending responses
                if client_id in sse_clients:
                    client_data = sse_clients[client_id]
                    if 'pending_responses' in client_data and client_data['pending_responses']:
                        # Send all pending responses
                        for response_data in client_data['pending_responses']:
                            yield f"event: message\ndata: {json.dumps(response_data)}\n\n"
                        
                        # Clear pending responses
                        client_data['pending_responses'] = []
                
                time.sleep(1)  # Small delay to prevent busy waiting
        
        except Exception as e:
            logger.error(f"SSE stream error for client {client_id}: {e}")
        finally:
            # Clean up client connection
            active_connections.discard(client_id)
            if client_id in sse_clients:
                del sse_clients[client_id]
            logger.info(f"SSE stream ended for client {client_id}")
    
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

@sse_bp.route('/sse/connect', methods=['GET'])
def sse_connect():
    """Establish SSE connection"""
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            client_id = str(uuid.uuid4())
        
        logger.info(f"SSE connection request from client {client_id}")
        
        # Initialize client data
        sse_clients[client_id] = {
            'connected_at': time.time(),
            'pending_responses': []
        }
        active_connections.add(client_id)
        
        return generate_sse_response(client_id)
    
    except Exception as e:
        logger.error(f"SSE connection error: {e}")
        return jsonify({"error": str(e)}), 500

@sse_bp.route('/sse/mcp', methods=['POST'])
def sse_mcp_request():
    """Handle MCP requests via SSE"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # Extract client_id from request headers or data
        client_id = request.headers.get('X-Client-ID') or data.get('client_id')
        if not client_id:
            return jsonify({"error": "Client ID required"}), 400
        
        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')
        
        logger.debug(f"SSE MCP request from {client_id}: {method} with params: {params}")
        
        # Process MCP request
        if method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            # Call calculator method
            result = call_calculator_method(tool_name, arguments)
            
            # Prepare response
            response_data = {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
            
            # Send response via SSE
            if client_id in sse_clients:
                sse_clients[client_id]['pending_responses'].append(response_data)
                logger.debug(f"Queued SSE response for client {client_id}")
                return jsonify({"status": "queued", "request_id": request_id}), 202
            else:
                return jsonify({"error": "Client not connected"}), 404
        
        elif method == 'tools/list':
            from routes.mcp import MCP_TOOLS
            
            response_data = {
                "jsonrpc": "2.0",
                "result": {"tools": [{"name": name, **schema} for name, schema in MCP_TOOLS.items()]},
                "id": request_id
            }
            
            # Send response via SSE
            if client_id in sse_clients:
                sse_clients[client_id]['pending_responses'].append(response_data)
                return jsonify({"status": "queued", "request_id": request_id}), 202
            else:
                return jsonify({"error": "Client not connected"}), 404
        
        else:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }
            
            if client_id in sse_clients:
                sse_clients[client_id]['pending_responses'].append(error_response)
                return jsonify({"status": "queued", "request_id": request_id}), 202
            else:
                return jsonify({"error": "Client not connected"}), 404
    
    except Exception as e:
        logger.error(f"SSE MCP request error: {e}")
        return jsonify({"error": str(e)}), 500

@sse_bp.route('/sse/status', methods=['GET'])
def sse_status():
    """Get SSE connection status"""
    try:
        return jsonify({
            "active_connections": len(active_connections),
            "connected_clients": list(active_connections),
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"SSE status error: {e}")
        return jsonify({"error": str(e)}), 500
