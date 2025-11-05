"""Configure logging for the application."""

import logging
import sys

def setup_logging():
    """Configure logging to redirect LiteLLM logs to file and keep custom logs visible."""

    # Configure root logger to write to file
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only warnings and errors for LiteLLM

    # File handler for all logs
    file_handler = logging.FileHandler('litellm_proxy.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    root_logger.addHandler(file_handler)

    # Suppress LiteLLM console output
    litellm_logger = logging.getLogger('LiteLLM')
    litellm_logger.setLevel(logging.ERROR)
    litellm_logger.propagate = False
    litellm_logger.addHandler(file_handler)

    # Suppress other noisy loggers
    for logger_name in ['LiteLLM Proxy', 'LiteLLM Router', 'httpx', 'uvicorn.access']:
        noisy_logger = logging.getLogger(logger_name)
        noisy_logger.setLevel(logging.ERROR)
        noisy_logger.propagate = False
        noisy_logger.addHandler(file_handler)

    # Keep uvicorn error logs visible
    uvicorn_logger = logging.getLogger('uvicorn.error')
    uvicorn_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    uvicorn_logger.addHandler(console_handler)
