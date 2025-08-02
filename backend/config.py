"""
Global configuration for the Resume Analyzer application.

This module contains shared configuration values used across all components.
"""

import json
import os
from typing import Dict, List, Any

# Load model configuration from JSON file
def load_models_config() -> Dict[str, Any]:
    """Load models configuration from models.json file"""
    config_path = os.path.join(os.path.dirname(__file__), "models.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback configuration if file doesn't exist
        return {
            "default_model": "llama-3.3-70b-versatile",
            "available_models": [
                {
                    "id": "llama-3.3-70b-versatile",
                    "name": "Llama 3.3 70B Versatile",
                    "description": "Versatile model for general conversations",
                    "provider": "groq"
                }
            ]
        }

# Load configuration
_models_config = load_models_config()

# Global model configuration
MODEL_NAME = _models_config["default_model"]

# Available models (backward compatibility)
AVAILABLE_MODELS = [model["id"] for model in _models_config["available_models"]]

def update_model_name(new_model_name: str) -> bool:
    """
    Update the global MODEL_NAME variable and persist to models.json.
    
    Args:
        new_model_name (str): The new model name to set
        
    Returns:
        bool: True if update successful, False if model not available
    """
    global MODEL_NAME, _models_config
    
    if new_model_name in AVAILABLE_MODELS:
        # Update global variable
        MODEL_NAME = new_model_name
        
        # Update config and persist to file
        _models_config["default_model"] = new_model_name
        try:
            config_path = os.path.join(os.path.dirname(__file__), "models.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(_models_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not persist model config to file: {e}")
            # Still return True since the in-memory update succeeded
        
        return True
    return False

def get_current_model() -> str:
    """
    Get the current MODEL_NAME.
    
    Returns:
        str: Current model name
    """
    return MODEL_NAME

def get_available_models() -> list:
    """
    Get list of available models.
    
    Returns:
        list: List of available model names
    """
    return AVAILABLE_MODELS.copy()

def get_available_models_detailed() -> List[Dict[str, str]]:
    """
    Get detailed list of available models with metadata.
    
    Returns:
        List[Dict]: List of model dictionaries with id, name, description, provider
    """
    return _models_config["available_models"].copy()

def get_model_info(model_id: str) -> Dict[str, str]:
    """
    Get detailed information about a specific model.
    
    Args:
        model_id (str): The model ID to get info for
        
    Returns:
        Dict[str, str]: Model information or None if not found
    """
    for model in _models_config["available_models"]:
        if model["id"] == model_id:
            return model.copy()
    return None

def reload_models_config():
    """
    Reload models configuration from file.
    Useful for hot-reloading configuration changes.
    """
    global _models_config, MODEL_NAME, AVAILABLE_MODELS
    _models_config = load_models_config()
    MODEL_NAME = _models_config["default_model"]
    AVAILABLE_MODELS = [model["id"] for model in _models_config["available_models"]]

# Other configuration values can be added here as needed