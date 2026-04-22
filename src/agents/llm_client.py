#!/usr/bin/env python3
"""
LLM Client for external llama.cpp servers
Provides unified interface for agents to connect to external llama.cpp servers
"""

import logging
import time
import json
import yaml
import requests
from typing import Dict, List, Optional, Any

# OpenAI client for compatibility
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Import configuration
try:
    from config.settings import get_server_url, get_grammar_schema_file
except ImportError:
    # Fallback for backward compatibility
    def get_server_url(agent_id: str) -> str:
        port_mapping = {
            'kanpaku': 8001,
            'tonoben': 8002,
            'toneri_1': 8003,
            'toneri_2': 8004
        }
        port = port_mapping.get(agent_id, 8001)
        return f"http://127.0.0.1:{port}"
    
    def get_grammar_schema_file(agent_id: str) -> str:
        return None


class LLMClient:
    """LLM client for agents using external llama.cpp servers"""
    
    def __init__(self, agent_id: str, model_name: str = "gemma4_e2b", server_url: str = None):
        """
        Initialize LLM client for agent
        
        Args:
            agent_id: Agent identifier
            model_name: Model to use
            server_url: External server URL (if None, uses config)
        """
        self.agent_id = agent_id
        self.model_name = model_name
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Determine server URL
        if server_url:
            self.server_url = server_url
        else:
            # Use configuration
            self.server_url = get_server_url(agent_id)
        
        # Initialize client
        self.client = None
        self._ensure_client_connected()
        
        # Grammar schema will be loaded dynamically per request
    
    def _ensure_client_connected(self) -> None:
        """Ensure client is connected to external server"""
        if not self.client:
            self.client = OpenAI(
                base_url=f"{self.server_url}/v1",
                api_key="kanpaku-dummy-key"
            )
            self.logger.info(f"Connected to external server for {self.agent_id} at {self.server_url}")
    
    def _check_server_health(self) -> bool:
        """Check if external server is healthy"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _load_grammar_schema(self, agent_id: str = None, schema_name: str = None) -> Optional[Dict]:
        """Load grammar schema dynamically for this agent"""
        from pathlib import Path
        
        # Use provided agent_id or default to self.agent_id
        target_agent_id = agent_id or self.agent_id
        
        # Get schema file path from configuration
        schema_path = get_grammar_schema_file(target_agent_id)
        if not schema_path:
            self.logger.warning(f"No grammar schema file configured for {target_agent_id}")
            return None
        
        try:
            schema_file = Path(schema_path)
            if schema_file.exists():
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                self.logger.info(f"Loaded grammar schema for {target_agent_id} from {schema_file}")
                return schema
            else:
                self.logger.warning(f"Grammar schema file not found: {schema_file}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load grammar schema for {target_agent_id}: {str(e)}")
            return None
    
    def __call__(self, prompt: str, schema_name: str = None, **kwargs) -> str:
        """
        Generate response from LLM with optional JSON schema
        
        Args:
            prompt: Input prompt
            schema_name: Optional schema name to use (overrides default)
            **kwargs: Additional parameters
            
        Returns:
            Generated response text (converted from JSON to YAML if applicable)
        """
        try:
            # Check server health
            if not self._check_server_health():
                raise RuntimeError(f"External server not available for {self.agent_id}")
            
            # Ensure client is connected
            self._ensure_client_connected()
            
            # Load schema dynamically if specified
            grammar_schema = None
            if schema_name:
                grammar_schema = self._load_grammar_schema(schema_name=schema_name)
            else:
                # Use default schema for this agent
                grammar_schema = self._load_grammar_schema()
            
            # Use JSON schema if available
            if grammar_schema:
                return self._call_with_schema(prompt, grammar_schema, **kwargs)
            else:
                # Fallback to regular chat completion
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
                return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"LLM error for {self.agent_id}: {str(e)}")
            raise RuntimeError(f"LLM service unavailable for {self.agent_id}: {str(e)}")
    
    def _call_with_schema(self, prompt: str, grammar_schema: Dict, **kwargs) -> str:
        """
        Call LLM with JSON schema and convert to YAML
        
        Args:
            prompt: Input prompt
            grammar_schema: JSON schema to use
            **kwargs: Additional parameters
            
        Returns:
            YAML string converted from JSON response
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_schema", "json_schema": grammar_schema},
            temperature=kwargs.get('temperature', 0.1),  # Lower temperature for structured output
            **{k: v for k, v in kwargs.items() if k != 'temperature'}
        )
        
        # Parse JSON response
        json_response = json.loads(response.choices[0].message.content)
        
        # Convert to YAML for compatibility with existing code
        yaml_response = yaml.dump(json_response, default_flow_style=False, allow_unicode=True)
        
        self.logger.debug(f"LLM JSON response for {self.agent_id}: {json_response}")
        return yaml_response
    
    def generate(self, prompt: str, schema_name: str = None, **kwargs) -> str:
        """
        Generate method for compatibility with existing code
        
        Args:
            prompt: Input prompt
            schema_name: Optional schema name to use
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        return self.__call__(prompt, schema_name=schema_name, **kwargs)
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat completion method
        
        Args:
            messages: List of message dicts
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        try:
            # Check server health
            if not self._check_server_health():
                raise RuntimeError(f"External server not available for {self.agent_id}")
            
            # Ensure client is connected
            self._ensure_client_connected()
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **kwargs
            )
            
            self.logger.debug(f"Chat completion response for {self.agent_id}: {response.choices[0].message.content[:100]}...")
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Chat completion error for {self.agent_id}: {str(e)}")
            raise RuntimeError(f"Chat completion failed for {self.agent_id}: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get wrapper and server status"""
        return {
            "agent_id": self.agent_id,
            "model_name": self.model_name,
            "server_healthy": self._check_server_health(),
            "client_connected": self.client is not None,
            "server_url": self.server_url
        }
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        # For external servers, no cleanup needed
        pass
