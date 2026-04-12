# LLM Connection Wrappers for CoDD

CoDD ai_command  from callable LLM connection wrappers

## Overview

This package provides LLM connection wrappers that can be used with CoDD's `ai_command` configuration:

- **GeminiWrapper**: Google Gemini API 3-flash-preview connection
- **OllamaWrapper**: Local Ollama models connection

## Installation

```bash
pip install -r connect_llm/requirements.txt
```

## Usage with CoDD

### 1. Gemini API

Add to `codd.yaml`:

```yaml
ai_command: "python -m connect_llm.gemini_wrapper"
```

Set environment variable:

```bash
export GOOGLE_API_KEY="your-google-api-key"
```

### 2. Ollama Local Models

#### DeepSeek Coder V2 (default)

```yaml
ai_command: "python -m connect_llm.ollama_wrapper"
```

#### Gemma4 26B

```yaml
ai_command: "python -m connect_llm.ollama_wrapper --model gemma4:26b-a4b"
```

#### Custom Ollama Host

```yaml
ai_command: "python -m connect_llm.ollama_wrapper --host http://192.168.1.100:11434"
```

## Available Models

### Gemini
- `gemini-3-flash-preview` (default)

### Ollama
- `mannix/deepseek-coder-v2-lite-instruct:q5_k_m` (default)
- `gemma4:26b-a4b`

## CLI Testing

### Test Gemini

```bash
# Set API key first
export GOOGLE_API_KEY="your-key"

# Test with prompt
python -m connect_llm.gemini_wrapper "Hello, how are you?"

# Or read from stdin
echo "Explain quantum computing" | python -m connect_llm.gemini_wrapper
```

### Test Ollama

```bash
# List available models
python -m connect_llm.ollama_wrapper --list-models

# Test default model (DeepSeek)
python -m connect_llm.ollama_wrapper "Write a Python function"

# Test Gemma4 model
python -m connect_llm.ollama_wrapper --model gemma4:26b-a4b "Explain machine learning"

# Read from stdin
echo "Debug this Python code" | python -m connect_llm.ollama_wrapper
```

## Prerequisites

### Gemini API
1. Get Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set `GOOGLE_API_KEY` environment variable
3. Install dependencies: `pip install google-generativeai`

### Ollama
1. Install [Ollama](https://ollama.ai/)
2. Pull required models:
   ```bash
   ollama pull mannix/deepseek-coder-v2-lite-instruct:q5_k_m
   ollama pull gemma4:26b-a4b
   ```
3. Start Ollama service

## Error Handling

Both wrappers include comprehensive error handling:

- **Gemini**: API key validation, rate limiting, network errors
- **Ollama**: Model availability checks, connection errors, fallback to CLI

## Configuration Examples

### CoDD codd.yaml Examples

#### Gemini Configuration
```yaml
ai_command: "python -m connect_llm.gemini_wrapper"
project:
  name: "My Project"
  language: "python"
```

#### Ollama DeepSeek Configuration
```yaml
ai_command: "python -m connect_llm.ollama_wrapper"
project:
  name: "My Project"
  language: "python"
```

#### Ollama Gemma4 Configuration
```yaml
ai_command: "python -m connect_llm.ollama_wrapper --model gemma4:26b-a4b"
project:
  name: "My Project"
  language: "python"
```

## Troubleshooting

### Gemini Issues
- Check API key: `echo $GOOGLE_API_KEY`
- Verify internet connection
- Check API quota limits

### Ollama Issues
- Verify Ollama is running: `ollama list`
- Check model availability: `python -m connect_llm.ollama_wrapper --list-models`
- Verify connection: `curl http://localhost:11434/api/tags`

## Development

### Adding New Models

1. Create new wrapper class in `connect_llm/`
2. Implement `__call__(self, prompt: str) -> str` method
3. Add to `__init__.py`
4. Update documentation

### Testing

```bash
# Test all wrappers
python -m connect_llm.gemini_wrapper --help
python -m connect_llm.ollama_wrapper --help
```
