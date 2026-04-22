#!/usr/bin/env python3
"""
Configuration settings for Kanpaku system
Centralized configuration for servers, models, and agents
"""

from pathlib import Path
from typing import Dict, Any

# Server Configuration - Maintaining multiple servers as requested
SERVER_CONFIG = {
    'kanpaku': {
        'port': 8001,
        'model': 'gemma4_e2b',
        'gpu_layers': 25,  # Safe default for 8GB VRAM
        'context_size': 5096,
        'parallel_requests': 1
    },
    'tonoben': {
        'port': 8002,
        'model': 'gemma4_e2b',
        'gpu_layers': 25,  # Safe default for 8GB VRAM
        'context_size': 5096,
        'parallel_requests': 1
    },
    'toneri_1': {
        'port': 8003,
        'model': 'gemma4_e2b',
        'gpu_layers': 20,  # Slightly lower for file operations
        'context_size': 5096,
        'parallel_requests': 1
    },
    'toneri_2': {
        'port': 8004,
        'model': 'gemma4_e2b',
        'gpu_layers': 20,  # Slightly lower for file operations
        'context_size': 5096,
        'parallel_requests': 1
    }
}

# Model Configuration
MODEL_CONFIG = {
    'default_context_size': 5096,
    'parallel_requests': 1,
    'timeout_seconds': 30,
    'host': '127.0.0.1'
}

# Grammar Schema Files Mapping
GRAMMAR_SCHEMA_FILES = {
    'kanpaku': 'kanpaku_instruction.json',
    'tonoben': 'tonoben_task_decomposition.json',
    'toneri_1': 'toneri_file_operations.json',
    'toneri_2': 'toneri_file_operations.json'
}

# Model Name to Environment Variable and Path Mapping
MODEL_PATH_MAPPING = {
    'gemma4_e2b': 'PATH_GEMMA4_E2B',
    'gemma4_26b_q4': 'PATH_GEMMA4_26B_Q4',
    'gemma4_26b_q8': 'PATH_GEMMA4_26B_Q8',
    'Qwen3.6_35b': 'PATH_QWEN3-6_35B',
    'llmjp4_8b': 'PATH_LLMJP4_8B',
    'deepseek_coder_6.7b': 'PATH_DEEPSEEK_CODER_6-7B'
}

# Paths Configuration
PATHS = {
    'grammar_schemas': Path(__file__).parent / 'grammar_schemas',
    'models': Path('/models'),  # Common model location
    'logs': Path('logs')
}

# Server Management Configuration
SERVER_MANAGEMENT = {
    'health_check_interval': 5,  # seconds
    'startup_timeout': 30,  # seconds
    'shutdown_timeout': 10,  # seconds
    'max_retries': 3
}

def get_server_config(agent_id: str) -> Dict[str, Any]:
    """Get server configuration for specific agent"""
    return SERVER_CONFIG.get(agent_id, {})

def get_server_url(agent_id: str) -> str:
    """Get server URL for specific agent"""
    config = get_server_config(agent_id)
    if not config:
        raise ValueError(f"No server configuration found for agent: {agent_id}")
    
    return f"http://{MODEL_CONFIG['host']}:{config['port']}"

def get_grammar_schema_file(agent_id: str) -> str:
    """Get grammar schema file path for specific agent"""
    schema_file = GRAMMAR_SCHEMA_FILES.get(agent_id)
    if not schema_file:
        return None
    
    return str(PATHS['grammar_schemas'] / schema_file)

def get_model_path(model_name: str) -> Path:
    """Get full path to model file from environment variables"""
    import os
    
    # Get environment variable name for this model
    env_var_name = MODEL_PATH_MAPPING.get(model_name)
    if not env_var_name:
        # Fallback to default path if model not in mapping
        return PATHS['models'] / f"{model_name}.gguf"
    
    # Get path from environment variable
    model_path = os.getenv(env_var_name)
    if not model_path:
        # Fallback to default path if environment variable not set
        return PATHS['models'] / f"{model_name}.gguf"
    
    return Path(model_path)

