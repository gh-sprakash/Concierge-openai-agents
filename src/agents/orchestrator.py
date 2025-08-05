"""
Sales Orchestrator Agent - Main agent with all business tools
Implements the "agents as tools" pattern for optimal performance and modularity
"""

from typing import Dict, Any, Optional, List
from agents import Agent, Runner, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

# Import tools and guardrails
from .tools import (
    query_salesforce_tool,
    query_veeva_tool, 
    query_knowledge_tool,
    query_tableau_tool,
    query_compliance_tool,
    SalesContext
)
from ..guardrails.security import strict_security_guardrail
from ..models.config import get_model_config, get_model_settings
from ..sessions.manager import SessionManager


class SalesOrchestrator:
    """
    Main orchestrator for the sales assistant system
    
    Features:
    - Single agent with all business tools
    - Intelligent tool selection and usage
    - Streaming response capabilities
    - Comprehensive error handling
    - Session management integration
    """
    
    def __init__(
        self, 
        model_name: str = "openai-gpt-4o-mini",
        enable_guardrails: bool = True,
        enable_tracing: bool = False
    ):
        """
        Initialize the sales orchestrator
        
        Args:
            model_name: Model configuration name to use
            enable_guardrails: Whether to enable security guardrails
            enable_tracing: Whether to enable OpenAI tracing
        """
        self.model_name = model_name
        self.enable_guardrails = enable_guardrails
        self.enable_tracing = enable_tracing
        
        # Get model configuration
        self.model_config = get_model_config(model_name)
        if not self.model_config:
            raise ValueError(f"Unknown model configuration: {model_name}")
        
        # Initialize the orchestrator agent
        self.agent = self._create_orchestrator_agent()
        
        print(f"🤖 Sales Orchestrator initialized with {self.model_config.display_name}")
    
    def _create_orchestrator_agent(self) -> Agent:
        """Create the main orchestrator agent with all tools"""
        
        # Prepare guardrails
        guardrails = [strict_security_guardrail] if self.enable_guardrails else []
        
        # Create the agent
        agent = Agent(
            name="Sales Assistant Orchestrator",
            instructions="""
            🎯 **You are a comprehensive sales assistant with access to all enterprise data sources.**
            
            🔧 **AVAILABLE TOOLS & USAGE:**
            
            **query_salesforce_tool**: Order data, customer information, compliance
            • Use for: "What orders did Dr. X place?", "Show me order status", "Compliance information"
            • Returns: Structured order information, totals, recent activity
            
            **query_veeva_tool**: Healthcare professional engagements and relationships
            • Use for: "Who has Dr. X contacted?", "Latest engagement with Dr. Y", "Talking points"
            • Returns: Engagement history, contact relationships, meeting outcomes
            
            **query_knowledge_tool**: Product information, training materials, clinical data
            • Use for: "Guardant360 features", "Product specifications", "Clinical studies"
            • Returns: Detailed product information and training resources
            
            **query_tableau_tool**: Business analytics, trends, performance metrics
            • Use for: "Show me analytics", "Performance trends", "Regional data"
            • Returns: Formatted analytics reports and business insights
            
            **query_compliance_tool**: Stark Law compliance, risk assessment
            • Use for: "Compliance status for Dr. X", "Spending limits", "Risk assessment"
            • Returns: Detailed compliance information and recommendations
            
            📊 **INTELLIGENT TOOL STRATEGY:**
            • **Single queries**: Use the most relevant tool
            • **Complex questions**: Use MULTIPLE tools and synthesize results
            • **"Who has Dr. X contacted?"**: Use query_veeva_tool (business relationship data)
            • **Comprehensive analysis**: Combine Salesforce + Veeva + Tableau data
            
            ✅ **RESPONSE GUIDELINES:**
            • Provide specific, actionable insights
            • Reference actual data from tools
            • Be professional and business-focused
            • Format responses clearly with bullet points and sections
            • Always mention which data sources were consulted
            
            ❌ **RESTRICTIONS:**
            • Never share personal contact information (phone, email, SSN)
            • Don't attempt math calculations or tell jokes
            • Stay focused on legitimate business inquiries
            • Don't guess - use tools to get accurate data
            
            🎯 **MISSION**: Help sales representatives make data-driven decisions and build stronger customer relationships.
            """,
            tools=[
                query_salesforce_tool,
                query_veeva_tool,
                query_knowledge_tool,
                query_tableau_tool,
                query_compliance_tool
            ],
            input_guardrails=guardrails,
            model=self.model_config.model_id,
            model_settings=get_model_settings(self.model_config)
        )
        
        return agent
    
    async def process_query(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        session = None
    ) -> Dict[str, Any]:
        """
        Process a user query and return structured results
        
        Args:
            query: User question or request
            user_context: Optional user context (name, territory, role)
            session: Optional session for conversation history
            
        Returns:
            Dict containing response, metadata, and execution info
        """
        import time
        start_time = time.time()
        
        try:
            # Create sales context
            context = self._create_sales_context(user_context)
            
            # Run the agent
            result = await Runner.run(
                self.agent,
                query,
                context=context,
                session=session
            )
            
            end_time = time.time()
            
            # Extract tool usage information
            tools_used = self._extract_tools_used(result)
            
            return {
                "success": True,
                "response": result.final_output,
                "tools_used": tools_used,
                "execution_time": end_time - start_time,
                "model": self.model_config.display_name,
                "session_used": session is not None,
                "result_object": result  # Full result object for advanced usage
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response": f"❌ **Error**: {str(e)}",
                "error": str(e),
                "execution_time": end_time - start_time,
                "model": self.model_config.display_name
            }
    
    async def stream_query(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        session = None
    ):
        """
        Process a query with streaming response
        
        Args:
            query: User question or request
            user_context: Optional user context
            session: Optional session for conversation history
            
        Yields:
            Response chunks as they become available
        """
        from openai.types.responses import ResponseTextDeltaEvent
        
        try:
            # Create sales context
            context = self._create_sales_context(user_context)
            
            # Run with streaming
            result = Runner.run_streamed(
                self.agent,
                query,
                context=context,
                session=session
            )
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield event.data.delta
                    
        except Exception as e:
            yield f"❌ **Streaming Error**: {str(e)}"
    
    def _create_sales_context(self, user_context: Optional[Dict[str, Any]] = None) -> SalesContext:
        """Create sales context from user information"""
        if user_context is None:
            user_context = {}
        
        return SalesContext(
            user_name=user_context.get("name", "Sales Representative"),
            territory=user_context.get("territory", "Northeast"),
            user_role=user_context.get("role", "Sales Rep")
        )
    
    def _extract_tools_used(self, result) -> List[str]:
        """Extract which tools were used from the result"""
        tools_used = []
        
        for item in result.new_items:
            if hasattr(item, 'tool_name') and item.tool_name:
                tool_name = item.tool_name
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
        
        return tools_used
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration"""
        return {
            "name": self.model_config.name,
            "display_name": self.model_config.display_name,
            "description": self.model_config.description,
            "provider": self.model_config.provider.value,
            "model_id": self.model_config.model_id,
            "temperature": self.model_config.temperature,
            "max_tokens": self.model_config.max_tokens
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the orchestrator"""
        return {
            "orchestrator": "healthy",
            "model_config": self.get_model_info(),
            "guardrails_enabled": self.enable_guardrails,
            "tracing_enabled": self.enable_tracing,
            "tools_count": len(self.agent.tools) if self.agent.tools else 0
        }

# Export main class
__all__ = ['SalesOrchestrator']