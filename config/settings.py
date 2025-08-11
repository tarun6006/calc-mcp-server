import os
import logging
from decimal import getcontext
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Calculator Server Configuration
CALC_SERVER_NAME = os.getenv("CALC_SERVER_NAME", "calculator-server")
CALC_SERVER_VERSION = os.getenv("CALC_SERVER_VERSION", "1.0")
CALC_PRECISION = int(os.getenv("CALC_PRECISION", "10"))
CALC_MAX_VALUE = float(os.getenv("CALC_MAX_VALUE", "1e15"))

# Set decimal precision
getcontext().prec = CALC_PRECISION

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def log_configuration():
    """Log configuration information"""
    logger.info(f"Calculator MCP Server Configuration:")
    logger.info(f"  Server Name: {CALC_SERVER_NAME}")
    logger.info(f"  Version: {CALC_SERVER_VERSION}")
    logger.info(f"  Precision: {CALC_PRECISION} decimal places")
    logger.info(f"  Max Value: {CALC_MAX_VALUE}")
    logger.info(f"  Log Level: {LOG_LEVEL}")
