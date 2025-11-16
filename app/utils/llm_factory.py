"""
LLM Factory - Abstracts LLM provider selection (vLLM vs Ollama).

This module provides a single interface to create LLM instances regardless of
the underlying provider. This allows seamless switching between:
- vLLM (production, GPU-optimized, OpenAI-compatible)
- Ollama (development, Mac-friendly, local)

Usage:
    from app.utils.llm_factory import get_llm
    
    llm = get_llm(model_name="Llama-3.2-3B-Instruct", temperature=0.1)

Configuration:
    Set LLM_PROVIDER environment variable:
    - "vllm" for production (uses vLLM with ChatOpenAI)
    - "ollama" for development (uses Ollama with ChatOllama)
"""

import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm(
    model_name: str,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    seed: Optional[int] = None,
    format_schema: Optional[dict] = None,
    json_mode: bool = False
):
    """
    Factory function to create LLM instance based on configured provider.
    
    Args:
        model_name: Name of the model to use
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum tokens to generate (None = model default)
        seed: Random seed for reproducibility (Ollama only)
        format_schema: Pydantic schema for structured outputs (Ollama only)
    
    Returns:
        LLM instance (ChatOpenAI for vLLM, ChatOllama for Ollama)
    
    Raises:
        ValueError: If LLM_PROVIDER is not "vllm" or "ollama"
        ImportError: If required package is not installed
    
    Examples:
        # Basic usage
        llm = get_llm("Llama-3.2-3B-Instruct")
        
        # With max tokens
        llm = get_llm("Llama-3.2-3B-Instruct", max_tokens=500)
        
        # With structured output (Ollama only)
        from app.schemas.synthesizer_output import SynthesizerOutput
        llm = get_llm(
            "llama3.2:3b",
            format_schema=SynthesizerOutput.model_json_schema()
        )
    """
    provider = settings.llm_provider.lower()
    
    if provider == "vllm":
        # For vLLM: Use json_mode if format_schema is provided
        use_json_mode = json_mode or (format_schema is not None)
        return _create_vllm_client(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=use_json_mode
        )
    elif provider == "ollama":
        return _create_ollama_client(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            format_schema=format_schema
        )
    else:
        raise ValueError(
            f"Invalid LLM_PROVIDER: {provider}. Must be 'vllm' or 'ollama'"
        )


def _create_vllm_client(
    model_name: str,
    temperature: float,
    max_tokens: Optional[int] = None,
    json_mode: bool = False
):
    """
    Create ChatOpenAI client for vLLM.
    
    vLLM provides an OpenAI-compatible API, so we use ChatOpenAI.
    vLLM supports JSON mode via response_format parameter (like OpenAI).
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for vLLM provider. "
            "Install with: pip install langchain-openai"
        )
    
    kwargs = {
        "model": model_name,
        "base_url": settings.vllm_base_url,
        "api_key": "EMPTY",  # vLLM doesn't require API key
        "temperature": temperature,
    }
    
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    
    # JSON mode: Forces model to output valid JSON
    # Note: vLLM supports this via guided decoding (similar to Ollama's format)
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    
    logger.debug(
        f"Creating vLLM client: model={model_name}, "
        f"base_url={settings.vllm_base_url}, temp={temperature}, json_mode={json_mode}"
    )
    
    return ChatOpenAI(**kwargs)


def _create_ollama_client(
    model_name: str,
    temperature: float,
    max_tokens: Optional[int] = None,
    seed: Optional[int] = None,
    format_schema: Optional[dict] = None
):
    """
    Create ChatOllama client for Ollama.
    
    Ollama supports additional features like structured outputs via format parameter.
    """
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError(
            "langchain-ollama is required for Ollama provider. "
            "Install with: pip install langchain-ollama"
        )
    
    kwargs = {
        "model": model_name,
        "base_url": settings.ollama_base_url,
        "temperature": temperature,
    }
    
    if max_tokens:
        kwargs["num_predict"] = max_tokens  # Ollama uses num_predict, not max_tokens
    
    if seed is not None:
        kwargs["seed"] = seed
    
    if format_schema:
        kwargs["format"] = format_schema  # Structured outputs
    
    logger.debug(
        f"Creating Ollama client: model={model_name}, "
        f"base_url={settings.ollama_base_url}, temp={temperature}"
    )
    
    return ChatOllama(**kwargs)


def get_provider_info() -> dict:
    """
    Get information about the current LLM provider configuration.
    
    Returns:
        dict with provider, base_url, and models
    """
    provider = settings.llm_provider.lower()
    
    if provider == "vllm":
        return {
            "provider": "vLLM",
            "base_url": settings.vllm_base_url,
            "supervisor_model": settings.supervisor_model,
            "planner_model": settings.planner_model,
            "synthesizer_model": settings.synthesizer_model,
        }
    else:
        return {
            "provider": "Ollama",
            "base_url": settings.ollama_base_url,
            "supervisor_model": settings.supervisor_model,
            "planner_model": settings.planner_model,
            "synthesizer_model": settings.synthesizer_model,
        }