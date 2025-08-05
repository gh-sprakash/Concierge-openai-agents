"""
Model Configuration - OpenAI and Bedrock Claude models only
Handles model initialization and configuration for different providers
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from agents import ModelSettings

class ModelProvider(Enum):
    """Supported model providers"""
    OPENAI = "openai"
    BEDROCK = "bedrock"

@dataclass
class ModelConfig:
    """Model configuration container"""
    name: str
    provider: ModelProvider
    model_id: str
    display_name: str
    description: str
    temperature: float = 0.2
    max_tokens: int = 1500
    
def get_available_models() -> Dict[str, ModelConfig]:
    """
    Get all available model configurations
    Returns only OpenAI and Bedrock Claude models
    """
    return {
        # 🤖 OpenAI Models
        "openai-gpt-4o": ModelConfig(
            name="openai-gpt-4o",
            provider=ModelProvider.OPENAI,
            model_id="gpt-4o",
            display_name="🤖 OpenAI GPT-4o",
            description="Latest GPT-4 Omni model - Best overall performance",
            temperature=0.2,
            max_tokens=1500
        ),
        
        "openai-gpt-4o-mini": ModelConfig(
            name="openai-gpt-4o-mini",
            provider=ModelProvider.OPENAI,
            model_id="gpt-4o-mini",
            display_name="🤖 OpenAI GPT-4o Mini",
            description="Faster, more cost-effective GPT-4o variant",
            temperature=0.2,
            max_tokens=1500
        ),
        
        "openai-gpt-4-turbo": ModelConfig(
            name="openai-gpt-4-turbo",
            provider=ModelProvider.OPENAI,
            model_id="gpt-4-turbo",
            display_name="🤖 OpenAI GPT-4 Turbo",
            description="High performance GPT-4 with faster response times",
            temperature=0.2,
            max_tokens=1500
        ),
        
        # 🧠 Anthropic Claude Models (via Bedrock)
        "claude-3-5-sonnet": ModelConfig(
            name="claude-3-5-sonnet",
            provider=ModelProvider.BEDROCK,
            model_id="bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            display_name="🧠 Claude 3.5 Sonnet",
            description="Latest Claude model with superior reasoning capabilities",
            temperature=0.1,
            max_tokens=2000
        ),
        
        "claude-3-5-haiku": ModelConfig(
            name="claude-3-5-haiku",
            provider=ModelProvider.BEDROCK,
            model_id="bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0",
            display_name="🧠 Claude 3.5 Haiku",
            description="Fast and efficient Claude model for quick responses",
            temperature=0.1,
            max_tokens=1500
        ),
        
        "claude-3-sonnet": ModelConfig(
            name="claude-3-sonnet",
            provider=ModelProvider.BEDROCK,
            model_id="bedrock/us.anthropic.claude-3-sonnet-20240229-v1:0",
            display_name="🧠 Claude 3 Sonnet",
            description="Previous generation Claude with reliable performance",
            temperature=0.1,
            max_tokens=2000
        ),
    }

def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a specific model"""
    available_models = get_available_models()
    return available_models.get(model_name)

def get_model_settings(model_config: ModelConfig) -> ModelSettings:
    """Convert ModelConfig to OpenAI Agents SDK ModelSettings"""
    return ModelSettings(
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens
    )

def get_models_by_provider(provider: ModelProvider) -> Dict[str, ModelConfig]:
    """Get all models for a specific provider"""
    all_models = get_available_models()
    return {
        name: config for name, config in all_models.items() 
        if config.provider == provider
    }

# Model recommendations for different use cases
RECOMMENDED_MODELS = {
    "general": "openai-gpt-4o-mini",  # Best balance of speed/cost/performance
    "reasoning": "claude-3-5-sonnet",  # Best for complex reasoning
    "fast": "claude-3-5-haiku",       # Fastest responses
    "comprehensive": "openai-gpt-4o"   # Most comprehensive responses
}

def get_recommended_model(use_case: str = "general") -> str:
    """Get recommended model for specific use case"""
    return RECOMMENDED_MODELS.get(use_case, "openai-gpt-4o-mini")