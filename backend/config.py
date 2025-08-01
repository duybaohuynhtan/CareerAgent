"""
Global configuration for the Resume Analyzer application.

This module contains shared configuration values used across all components.
"""

# Global model configuration
MODEL_NAME = "gemma2-9b-it"

# Available models
AVAILABLE_MODELS = [
    "deepseek-r1-distill-llama-70b",
    "llama-3.3-70b-versatile", 
    "gemma2-9b-it"
]

def update_model_name(new_model_name: str) -> bool:
    """
    Update the global MODEL_NAME variable.
    
    Args:
        new_model_name (str): The new model name to set
        
    Returns:
        bool: True if update successful, False if model not available
    """
    global MODEL_NAME
    
    if new_model_name in AVAILABLE_MODELS:
        MODEL_NAME = new_model_name
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

# Other configuration values can be added here as needed