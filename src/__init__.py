"""
Sales Assistant Agents - Complete system initialization
"""

__version__ = "1.0.0"

# Import main components
from .agents.orchestrator import SalesOrchestrator
from .sessions.manager import SessionManager, session_manager
from .models.config import get_available_models, get_model_config
from .guardrails.security import strict_security_guardrail
from .knowledge.bedrock_kb import knowledge_base

# Quick setup function for easy initialization
def create_sales_assistant(
    model_name: str = "openai-gpt-4o-mini",
    enable_guardrails: bool = True,
    persistent_sessions: bool = True
) -> tuple:
    """
    Quick setup function to create a sales assistant system
    
    Args:
        model_name: Model to use
        enable_guardrails: Enable security guardrails
        persistent_sessions: Use persistent sessions
        
    Returns:
        Tuple of (orchestrator, session_manager)
    """
    orchestrator = SalesOrchestrator(
        model_name=model_name,
        enable_guardrails=enable_guardrails
    )
    
    return orchestrator, session_manager

__all__ = [
    'SalesOrchestrator',
    'SessionManager', 
    'session_manager',
    'get_available_models',
    'get_model_config',
    'knowledge_base',
    'create_sales_assistant'
]