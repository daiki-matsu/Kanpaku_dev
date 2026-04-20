"""
CoDD用LLM接続ラッパー
CoDD ai_commandから呼び出し可能なLLM接続ラッパー
"""

try:
    from .gemini_wrapper import GeminiWrapper
    _gemini_available = True
except ImportError:
    GeminiWrapper = None
    _gemini_available = False

from .ollama_wrapper import ollamaWrapper
from .env_loader import load_env_file, get_env_var

__all__ = ['ollamaWrapper', 'load_env_file', 'get_env_var']
if _gemini_available:
    __all__.append('GeminiWrapper')
