import os
from typing import Optional
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text based on prompt"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available/configured"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class ClaudeProvider(LLMProvider):
    """Anthropic Claude LLM provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
        return self._client
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        client = self._get_client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class LocalProvider(LLMProvider):
    """Local LLM provider (for models like Llama, etc.)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        import json
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get('temperature', 0.7),
                        "num_predict": kwargs.get('max_tokens', 1000)
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise RuntimeError(f"Local LLM API error: {e}")
    
    def is_available(self) -> bool:
        import requests
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

class LLMFactory:
    """Factory for creating LLM provider instances"""
    
    _providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "local": LocalProvider,
    }
    
    @classmethod
    def create_llm(cls, provider_name: str = None, **kwargs) -> Optional[LLMProvider]:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider ("openai", "claude", "local")
                         If None, will try to determine from environment
            **kwargs: Additional arguments to pass to the provider constructor
            
        Returns:
            LLMProvider instance or None if not available/configured
        """
        # Determine provider from environment if not specified
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER", "local").lower()
        
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown LLM provider: {provider_name}. Available: {list(cls._providers.keys())}")
        
        provider = provider_class(**kwargs)
        
        # Check if provider is available/configured
        if not provider.is_available():
            # Try fallback order: openai -> claude -> local
            for fallback_name in ["openai", "claude", "local"]:
                if fallback_name == provider_name:
                    continue
                fallback_class = cls._providers[fallback_name]
                fallback_provider = fallback_class(**kwargs)
                if fallback_provider.is_available():
                    return fallback_provider
            return None
            
        return provider
    
    @classmethod
    def get_available_providers(cls) -> dict:
        """Get status of all providers"""
        status = {}
        for name, provider_class in cls._providers.items():
            provider = provider_class()
            status[name] = provider.is_available()
        return status