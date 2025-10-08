import os
from pathlib import Path

# --- Environment Mode Detection ---

# 1. Determine the application's root directory.
APP_ROOT = Path(__file__).resolve().parent

# Define the expected mode file name
APP_ENV_FILE_NAME = ".app_env_mode"
ENV_FILE_PATH = APP_ROOT / APP_ENV_FILE_NAME

# Default to production mode if the file somehow doesn't exist
APP_MODE = "PROD" 

if ENV_FILE_PATH.exists():
    try:
        # Read the file content, strip whitespace/newlines, and normalize to uppercase
        APP_MODE = ENV_FILE_PATH.read_text().strip().upper()
    except Exception as e:
        print(f"Warning: Could not read environment mode file at {ENV_FILE_PATH}. Defaulting to PROD. Error: {e}")

# Global constants for easy access throughout your application
IS_DEV_MODE = (APP_MODE == "DEV")
IS_PROD_MODE = (APP_MODE == "PROD")