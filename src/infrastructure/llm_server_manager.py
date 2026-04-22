#!/usr/bin/env python3
"""
LLM Server Manager for External llama.cpp Servers
Manages connections to external llama.cpp servers with automatic start/stop
"""

import logging
import requests
import subprocess
import time
import signal
import os
import sys
from typing import Dict, Optional, List, Any
from pathlib import Path
import json

# Import configuration
try:
    from config.settings import get_server_config, get_server_url, get_model_path
except ImportError:
    # Fallback for backward compatibility
    def get_server_config(agent_id: str) -> Dict[str, Any]:
        fallback_config = {
            'kanpaku': {'port': 8001, 'model': 'gemma4_e2b', 'gpu_layers': 25},
            'tonoben': {'port': 8002, 'model': 'gemma4_e2b', 'gpu_layers': 25},
            'toneri_1': {'port': 8003, 'model': 'gemma4_e2b', 'gpu_layers': 20},
            'toneri_2': {'port': 8004, 'model': 'gemma4_e2b', 'gpu_layers': 20}
        }
        return fallback_config.get(agent_id, {})
    
    def get_server_url(agent_id: str) -> str:
        config = get_server_config(agent_id)
        if not config:
            raise ValueError(f"No server configuration found for agent: {agent_id}")
        return f"http://127.0.0.1:{config['port']}"
    
    def get_model_path(model_name: str) -> Path:
        fallback_paths = [
            Path(f"/models/{model_name}.gguf"),
            Path(f"./models/{model_name}.gguf"),
            Path(f"models/{model_name}.gguf")
        ]
        for path in fallback_paths:
            if path.exists():
                return path
        return fallback_paths[0]  # Return first path as default


class LLMServerManager:
    """LLM Server Manager for external servers with automatic lifecycle management"""
    
    def __init__(self, agent_id: str, model_name: str = "gemma4_e2b", server_url: str = None):
        """
        Initialize server manager for agent
        
        Args:
            agent_id: Agent identifier
            model_name: Model to use
            server_url: External server URL (if None, uses config)
        """
        self.agent_id = agent_id
        self.model_name = model_name
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.server_process = None
        self.is_managed = False  # Whether this manager controls the server process
        
        # Determine server URL
        if server_url:
            self.server_url = server_url
            self.is_managed = False  # External URL, not managed
        else:
            # Use configuration
            self.server_url = get_server_url(agent_id)
            self.is_managed = True  # Managed server
    
    
    def get_server_url(self) -> str:
        """Get server URL"""
        return self.server_url
    
    def is_healthy(self) -> bool:
        """Check if external server is healthy"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_status(self) -> Dict[str, any]:
        """Get server status"""
        return {
            "agent_id": self.agent_id,
            "model_name": self.model_name,
            "server_url": self.server_url,
            "is_healthy": self.is_healthy(),
            "is_managed": self.is_managed,
            "server_process_alive": self.server_process and self.server_process.poll() is None
        }
    
    def start_server(self) -> bool:
        """
        Start llama.cpp server for this agent
        Only starts if server is managed (not external URL)
        """
        if not self.is_managed:
            # External server, just check if it's healthy
            return self.is_healthy()
        
        if self.server_process and self.server_process.poll() is None:
            # Server already running
            if self.is_healthy():
                self.logger.info(f"Server for {self.agent_id} already running and healthy")
                return True
            else:
                # Server running but not healthy, stop and restart
                self.stop_server()
        
        try:
            # Extract port from URL
            port = int(self.server_url.split(':')[-1])
            
            # Get configuration for this agent
            server_config = get_server_config(self.agent_id)
            if not server_config:
                self.logger.error(f"No server configuration found for agent: {self.agent_id}")
                return False
            
            # Get model path
            model_path = get_model_path(self.model_name)
            
            if not model_path.exists():
                self.logger.error(f"Model file not found for {self.model_name} at {model_path}")
                return False
            
            # Build llama.cpp server command with configurable settings
            cmd = [
                "llama-cpp-server",
                "-m", str(model_path),
                "--host", "127.0.0.1",
                "--port", str(port),
                "--ctx-size", str(server_config.get('context_size', 2048)),
                "--n-gpu-layers", str(server_config.get('gpu_layers', 25)),  # Safe default
                "--parallel", str(server_config.get('parallel_requests', 4))
            ]
            
            self.logger.info(f"Starting llama.cpp server for {self.agent_id} on port {port}")
            self.logger.info(f"Command: {' '.join(cmd)}")
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            # Wait for server to be healthy
            max_wait = 30  # seconds
            wait_interval = 1
            for i in range(max_wait):
                if self.is_healthy():
                    self.logger.info(f"Server for {self.agent_id} started successfully")
                    return True
                time.sleep(wait_interval)
                
                # Check if process died
                if self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    self.logger.error(f"Server process died for {self.agent_id}")
                    self.logger.error(f"stdout: {stdout.decode()}")
                    self.logger.error(f"stderr: {stderr.decode()}")
                    return False
            
            self.logger.error(f"Server for {self.agent_id} failed to become healthy within {max_wait}s")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start server for {self.agent_id}: {str(e)}")
            return False
    
    def stop_server(self) -> None:
        """Stop llama.cpp server for this agent"""
        if not self.is_managed or not self.server_process:
            return
        
        try:
            if self.server_process.poll() is None:
                self.logger.info(f"Stopping server for {self.agent_id}")
                
                # Try graceful shutdown first
                self.server_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=10)
                    self.logger.info(f"Server for {self.agent_id} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    self.logger.warning(f"Force killing server for {self.agent_id}")
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                    else:
                        self.server_process.kill()
                    self.server_process.wait()
                    self.logger.info(f"Server for {self.agent_id} force killed")
            
            self.server_process = None
            
        except Exception as e:
            self.logger.error(f"Error stopping server for {self.agent_id}: {str(e)}")
            self.server_process = None


class GlobalServerManager:
    """Global server manager for all agents with lifecycle management"""
    
    _shared_servers = {}  # Shared servers by model name
    _agent_servers = {}   # Agent-specific server references
    _instance = None
    
    @classmethod
    def get_server(cls, agent_id: str, model_name: str = "gemma4_e2b", server_url: str = None) -> 'LLMServerManager':
        """
        Get or create server manager for agent
        For managed servers, each agent gets its own manager instance
        """
        # For managed servers, each agent gets its own manager
        server_key = f"{agent_id}_{model_name}"
        
        if server_key not in cls._shared_servers:
            cls._shared_servers[server_key] = LLMServerManager(
                agent_id=agent_id, 
                model_name=model_name,
                server_url=server_url
            )
        
        # Track which agents are using this server
        cls._agent_servers[agent_id] = cls._shared_servers[server_key]
        
        return cls._shared_servers[server_key]
    
    @classmethod
    def start_server(cls, agent_id: str, model_name: str = "gemma4_e2b", server_url: str = None) -> bool:
        """
        Start server for specific agent
        """
        server = cls.get_server(agent_id, model_name, server_url)
        return server.start_server()
    
    @classmethod
    def stop_server(cls, agent_id: str) -> None:
        """Stop server for specific agent"""
        if agent_id in cls._agent_servers:
            server = cls._agent_servers[agent_id]
            del cls._agent_servers[agent_id]
            
            # Stop the server
            server.stop_server()
            
            # Remove from shared servers
            server_key = f"{agent_id}_{server.model_name}"
            if server_key in cls._shared_servers:
                del cls._shared_servers[server_key]
    
    @classmethod
    def stop_all_servers(cls) -> None:
        """Stop all managed servers"""
        for agent_id in list(cls._agent_servers.keys()):
            cls.stop_server(agent_id)
    
    @classmethod
    def get_all_status(cls) -> List[Dict[str, Any]]:
        """Get status of all servers"""
        status_list = []
        seen_servers = set()
        for agent_id, server in cls._agent_servers.items():
            server_id = id(server)
            if server_id not in seen_servers:
                status = server.get_status()
                status['using_agents'] = [aid for aid, srv in cls._agent_servers.items() if srv == server]
                status_list.append(status)
                seen_servers.add(server_id)
        return status_list

# Cleanup on exit
import atexit
atexit.register(GlobalServerManager.stop_all_servers)
