"""
Nova Apply - LLM Client
Unified interface for LLM providers (Kimi, Gemini, OpenAI, Ollama).
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    KIMI = "kimi"
    GEMINI = "google"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    text: str
    tokens_used: int
    tokens_prompt: int
    tokens_completion: int
    model: str
    provider: str
    latency_ms: float


class LLMClient:
    """Unified LLM client with automatic failover."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.primary = config.get('llm', {}).get('primary_provider', 'kimi')
        self.fallback = config.get('llm', {}).get('fallback_provider', 'google')
        self.local = config.get('llm', {}).get('local_model', 'ollama')
        
        self._clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM clients."""
        # Kimi (OpenAI compatible)
        kimi_key = os.getenv('KIMI_API_KEY')
        if kimi_key:
            try:
                from openai import OpenAI
                self._clients['kimi'] = OpenAI(
                    api_key=kimi_key,
                    base_url="https://api.moonshot.cn/v1"
                )
            except ImportError:
                pass
        
        # Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self._clients['google'] = genai
            except ImportError:
                pass
        
        # Ollama (local)
        try:
            import requests
            # Test if Ollama is running
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                self._clients['ollama'] = True
        except:
            pass
    
    def complete(self, 
                 prompt: str, 
                 model: Optional[str] = None,
                 temperature: float = 0.3,
                 max_tokens: int = 2000,
                 json_mode: bool = False) -> LLMResponse:
        """
        Generate completion from LLM.
        
        Tries primary, then fallback, then local.
        """
        start_time = time.time()
        
        providers_to_try = [self.primary, self.fallback]
        if self.local not in providers_to_try:
            providers_to_try.append(self.local)
        
        last_error = None
        
        for provider in providers_to_try:
            try:
                if provider == 'kimi':
                    return self._call_kimi(prompt, model, temperature, max_tokens, json_mode)
                elif provider == 'google':
                    return self._call_gemini(prompt, model, temperature, max_tokens, json_mode)
                elif provider == 'ollama':
                    return self._call_ollama(prompt, model, temperature, max_tokens, json_mode)
            except Exception as e:
                last_error = e
                continue
        
        raise Exception(f"All LLM providers failed. Last error: {last_error}")
    
    def _call_kimi(self, prompt, model, temperature, max_tokens, json_mode) -> LLMResponse:
        """Call Kimi API."""
        client = self._clients.get('kimi')
        if not client:
            raise Exception("Kimi client not initialized")
        
        model = model or "kimi-k2.5"
        
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        
        latency = (time.time() - time.time()) * 1000  # Placeholder
        
        return LLMResponse(
            text=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            tokens_prompt=response.usage.prompt_tokens,
            tokens_completion=response.usage.completion_tokens,
            model=model,
            provider="kimi",
            latency_ms=latency
        )
    
    def _call_gemini(self, prompt, model, temperature, max_tokens, json_mode) -> LLMResponse:
        """Call Gemini API."""
        import google.generativeai as genai
        import time

        model_name = model or "gemini-2.0-flash"
        start_time = time.time()

        # Configure the model
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Get the model
        gemini_model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config
        )

        # Build content
        if json_mode:
            prompt = f"{prompt}\n\nRespond with valid JSON only."

        # Generate response
        response = gemini_model.generate_content(prompt)

        latency_ms = (time.time() - start_time) * 1000

        # Extract usage info (Gemini doesn't provide token counts in same way)
        text = response.text
        # Rough estimation: 1 token ≈ 4 chars for English
        tokens_completion = len(text) // 4
        tokens_prompt = len(prompt) // 4
        tokens_used = tokens_prompt + tokens_completion

        return LLMResponse(
            text=text,
            tokens_used=tokens_used,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            model=model_name,
            provider="google",
            latency_ms=latency_ms
        )
    
    def _call_ollama(self, prompt, model, temperature, max_tokens, json_mode) -> LLMResponse:
        """Call local Ollama."""
        import requests
        
        model = model or "llama2"
        
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        })
        
        response.raise_for_status()
        data = response.json()
        
        return LLMResponse(
            text=data['response'],
            tokens_used=data.get('eval_count', 0) + data.get('prompt_eval_count', 0),
            tokens_prompt=data.get('prompt_eval_count', 0),
            tokens_completion=data.get('eval_count', 0),
            model=model,
            provider="ollama",
            latency_ms=0
        )
