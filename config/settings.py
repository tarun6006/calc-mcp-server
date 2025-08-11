"""Configuration and environment variable management for Calculator MCP Server"""
import os
import logging
import yaml
from decimal import getcontext
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}. Using defaults.")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        return {}

# Load YAML configuration
CONFIG = load_config()

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
