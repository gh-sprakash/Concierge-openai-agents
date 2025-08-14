"""
Sales Orchestrator Agent - Main agent with all business tools
Implements the "agents as tools" pattern for optimal performance and modularity
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from agents import Agent, Runner, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
from agents.exceptions import InputGuardrailTripwireTriggered

# Import tools and guardrails
from .tools import (
    query_salesforce_tool,
    query_veeva_tool, 
    query_knowledge_tool,
    query_tableau_tool,
    query_compliance_tool,
    SalesContext
)
from ..guardrails.input_guardrails import input_security_guardrail
from ..guardrails.output_guardrails import output_security_guardrail
from ..models.config import get_model_config, get_model_settings
from ..sessions.manager import SessionManager
from ..knowledge.bedrock_kb import knowledge_base


class SalesResponse(BaseModel):
    """Structured response model that ensures suggested questions are always included"""
    main_response: str = Field(description="The main response to the user's question")
    suggested_questions: List[str] = Field(
        description="3-5 relevant follow-up questions that extend the topic",
        min_items=3,
        max_items=5
    )
    
    def format_response(self) -> str:
        """Format the structured response into a readable string"""
        response = self.main_response
        if self.suggested_questions:
            response += "\n\nSuggested Questions:\n"
            for question in self.suggested_questions:
                response += f"• {question}\n"
        return response.strip()


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
        
        print(f"INFO: Sales Orchestrator initialized with {self.model_config.display_name}")
    
    def _create_orchestrator_agent(self) -> Agent:
        """Create the main orchestrator agent with all tools"""
        
        # Prepare guardrails
        input_guardrails = [input_security_guardrail] if self.enable_guardrails else []
        output_guardrails = [output_security_guardrail] if self.enable_guardrails else []
        
        # Create the agent with structured output
        agent = Agent(
            name="Sales Assistant Orchestrator",
            instructions="""
            You are a comprehensive sales assistant with access to all enterprise data sources.
            
            **AVAILABLE TOOLS & USAGE:**
            
            **query_knowledge_tool**: Product information, training materials, clinical data
            • Use for: "Guardant360 features", "Product specifications", "Clinical studies"
            • Returns: Raw document chunks from knowledge base that you should synthesize into a comprehensive response
            • IMPORTANT: When this tool returns document chunks, analyze and synthesize them into a coherent, helpful response
            
            **RESPONSE GUIDELINES:**
            • Provide specific, actionable insights in the main_response field
            • Reference actual data from tools
            • Be professional and business-focused
            • Format responses clearly with bullet points and sections
            • Always mention which data sources were consulted
            • Don't use markdown or HTML formatting, just plain text
            
            **MANDATORY STRUCTURED OUTPUT:**
            You MUST respond using the structured format with two fields:
            1. main_response: Your comprehensive answer to the user's question
            2. suggested_questions: EXACTLY 3-5 relevant follow-up questions that extend the topic
            
            **SUGGESTED QUESTIONS REQUIREMENTS:**
            • Must include mix of: deeper dive questions, related product questions, competitive questions, clinical questions
            • Should naturally extend the current topic
            • Examples: "How does this compare to competitors?", "What clinical data supports this?", "How can I position this to oncologists?"
            
            **RESTRICTIONS:**
            • Never share personal contact information (phone, email, SSN)
            • Don't attempt math calculations or tell jokes
            • Stay focused on legitimate business inquiries
            • Don't guess - use tools to get accurate data
            
            **MISSION**: Help sales representatives make data-driven decisions and build stronger customer relationships.
            """,
            output_type=SalesResponse,
            tools=[
                # query_salesforce_tool,
                # query_veeva_tool,
                query_knowledge_tool,
                # query_tableau_tool,
                # query_compliance_tool
            ],
            input_guardrails=input_guardrails,
            output_guardrails=output_guardrails,
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
            
            # Format the structured response
            try:
                structured_response = result.final_output_as(SalesResponse)
                formatted_response = structured_response.format_response()
            except Exception as e:
                print(f"WARNING: Failed to parse structured response: {e}")
                # Fallback to the raw output
                formatted_response = result.final_output
                # Try to ensure questions are included in fallback
                if "Suggested Questions:" not in formatted_response:
                    # Generate follow-up questions using a separate AI call
                    try:
                        follow_up_questions = await self._generate_follow_up_questions(query, formatted_response)
                        formatted_response += f"\n\nSuggested Questions:\n{follow_up_questions}"
                    except Exception as follow_up_error:
                        print(f"WARNING: Failed to generate follow-up questions: {follow_up_error}")
                        # Final fallback with hardcoded questions
                        formatted_response += "\n\nSuggested Questions:\n• How can I learn more about related Guardant Health products?\n• What clinical evidence supports these findings?\n• How does this compare to competitor offerings?"
            
            # Extract sources from knowledge base tool results
            kb_sources = []
            try:
                for item in result.new_items:
                    # Check if this is a tool result item
                    if hasattr(item, 'tool_name') and item.tool_name == 'query_knowledge_tool':
                        # Extract the tool result data
                        if hasattr(item, 'content'):
                            tool_result = item.content
                        elif hasattr(item, 'data'):
                            tool_result = item.data
                        else:
                            continue
                            
                        # Handle KnowledgeResult object
                        if hasattr(tool_result, 'sources'):
                            sources = tool_result.sources
                            if sources:
                                kb_sources.extend(sources)
                        # Handle dict representation
                        elif isinstance(tool_result, dict) and 'sources' in tool_result:
                            sources = tool_result.get('sources', [])
                            if sources:
                                kb_sources.extend(sources)
            except Exception as e:
                print(f"WARNING: Error extracting sources from tool results: {e}")
                
            # Fallback: if no sources extracted from tool results, try direct KB lookup
            if not kb_sources:
                try:
                    kb = knowledge_base.query_with_sources(query)
                    kb_sources = kb.get('sources', [])
                except Exception:
                    kb_sources = []

            return {
                "success": True,
                "response": formatted_response,
                "tools_used": tools_used,
                "execution_time": end_time - start_time,
                "model": self.model_config.display_name,
                "session_used": session is not None,
                "knowledge_sources": kb_sources,
                "result_object": result  # Full result object for advanced usage
            }
            
        except InputGuardrailTripwireTriggered as e:
            end_time = time.time()
            # Provide a user-friendly message for guardrail violations
            user_friendly_message = ("I'm sorry, but your question appears to be outside of my area of expertise. "
                                    "I'm designed to help with Guardant Health business inquiries, including our "
                                    "precision oncology products, liquid biopsy technology, clinical information, "
                                    "and sales-related topics. Please ask a question related to our Guardant Health.")
            
            output_info = getattr(e, 'output_info', {})
            return {
                "success": False,
                "response": user_friendly_message,
                "error": "Query blocked by content guardrail - topic outside business scope",
                "execution_time": end_time - start_time,
                "model": self.model_config.display_name,
                "guardrail_triggered": True
            }
            
        except Exception as e:
            end_time = time.time()
            output_info = getattr(e, 'output_info', str(e))
            return {
                "success": False,
                "response": f"ERROR: {str(e)}",
                "error": output_info,
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
            yield f"STREAMING ERROR: {str(e)}"
    
    async def _generate_follow_up_questions(self, original_query: str, response: str) -> str:
        """Generate follow-up questions using a separate AI call as fallback"""
        
        # Create a simple agent for generating follow-up questions
        follow_up_agent = Agent(
            name="Follow-up Question Generator",
            instructions=f"""
            Generate 3-5 relevant follow-up questions based on the user's original question and the response provided.
            
            Original Question: {original_query}
            Response: {response}
            
            Generate questions that:
            • Naturally extend the topic
            • Are relevant to Guardant Health sales representatives
            • Include mix of: deeper dive questions, product questions, competitive questions, clinical questions
            • Help sales reps have better conversations with healthcare professionals
            
            Format as bullet points without "Suggested Questions:" heading (that will be added automatically).
            Example format:
            • How does this compare to competitors?
            • What clinical data supports this?
            • How can I position this to oncologists?
            """,
            model_settings=get_model_settings(self.model_config)
        )
        
        try:
            result = await Runner.run(follow_up_agent, "Generate follow-up questions")
            return result.final_output
        except Exception as e:
            print(f"ERROR: Failed to generate follow-up questions: {e}")
            # Return basic fallback questions
            return "• How can I learn more about related Guardant Health products?\n• What clinical evidence supports these findings?\n• How does this compare to competitor offerings?"
    
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
        
        try:
            for item in result.new_items:
                tool_name = None
                
                # Try different ways to extract tool name
                if hasattr(item, 'tool_name') and item.tool_name:
                    tool_name = item.tool_name
                elif hasattr(item, 'function_name') and item.function_name:
                    tool_name = item.function_name
                elif hasattr(item, 'name') and item.name:
                    tool_name = item.name
                elif hasattr(item, 'type') and 'tool' in str(item.type).lower():
                    # Try to extract from item content or data
                    if hasattr(item, 'content'):
                        content = str(item.content)
                        if 'query_knowledge_tool' in content:
                            tool_name = 'query_knowledge_tool'
                        elif 'query_salesforce_tool' in content:
                            tool_name = 'query_salesforce_tool'
                        elif 'query_veeva_tool' in content:
                            tool_name = 'query_veeva_tool'
                        elif 'query_tableau_tool' in content:
                            tool_name = 'query_tableau_tool'
                        elif 'query_compliance_tool' in content:
                            tool_name = 'query_compliance_tool'
                
                # Debug logging (can be enabled if needed)
                # print(f"DEBUG: Item type: {type(item)}, tool_name: {tool_name}")
                # if hasattr(item, '__dict__'):
                #     print(f"DEBUG: Item attributes: {list(item.__dict__.keys())}")
                
                if tool_name and tool_name not in tools_used:
                    tools_used.append(tool_name)
                    
        except Exception as e:
            print(f"WARNING: Error extracting tools used: {e}")
        
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
