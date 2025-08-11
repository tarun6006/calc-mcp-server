"""Health check endpoints"""
import time
import logging
from flask import Blueprint, jsonify
from config.settings import CALC_SERVER_NAME, CALC_SERVER_VERSION

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the calculator MCP server"""
    try:
        return jsonify({
            "status": "healthy",
            "server": CALC_SERVER_NAME,
            "version": CALC_SERVER_VERSION,
            "timestamp": time.time(),
            "services": {
                "calculator_engine": True,
                "mcp_protocol": True,
                "sse_transport": True
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }), 500
