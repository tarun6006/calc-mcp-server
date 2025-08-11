"""
Refactored Calculator MCP Server
Modular architecture with separated concerns
"""
import os
from flask import Flask
from config.settings import setup_logging, log_configuration
from routes.health import health_bp
from routes.mcp import mcp_bp
from routes.sse import sse_bp

# Setup logging first
setup_logging()

# Create Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(mcp_bp)
app.register_blueprint(sse_bp)

# Log configuration
log_configuration()

if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    
    port = int(os.environ.get("PORT", 8080))
    is_cloud_run = os.environ.get("K_SERVICE") is not None
    environment = "Cloud Run" if is_cloud_run else "Local"
    
    logger.info(f"Starting Calculator MCP Server on port {port} ({environment})")
    logger.info("Features Enabled:")
    logger.info("   - MCP (Model Context Protocol) support")
    logger.info("   - SSE (Server-Sent Events) transport")
    logger.info("   - Natural language expression parsing")
    logger.info("   - Multi-number mathematical operations")
    logger.info("   - Advanced mathematical functions")
    
    app.run(host="0.0.0.0", port=port, debug=not is_cloud_run)
