"""
Sales Assistant Streamlit Application
Production-ready web interface showcasing all system capabilities
"""

import streamlit as st
import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.orchestrator import SalesOrchestrator
from src.sessions.manager import session_manager
from src.models.config import get_available_models, ModelProvider
from src.knowledge.bedrock_kb import knowledge_base
from agents.exceptions import InputGuardrailTripwireTriggered

# Environment setup
import os
from dotenv import load_dotenv
load_dotenv()

# Streamlit configuration
st.set_page_config(
    page_title="🚀 Sales Assistant Agents",
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.streaming-text {
    border-left: 3px solid #667eea;
    padding-left: 10px;
    margin: 10px 0;
    background-color: #f8f9fa;
    border-radius: 5px;
    padding: 10px;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
}

.guardrail-test {
    background: #f8f9fa;
    border: 2px dashed #dee2e6;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)


class SalesAssistantApp:
    """Main Streamlit application class"""
    
    def __init__(self):
        """Initialize the application"""
        self.orchestrator: Optional[SalesOrchestrator] = None
        self.current_model = None
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())[:8]
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'metrics' not in st.session_state:
            st.session_state.metrics = {
                'total_queries': 0,
                'successful_queries': 0, 
                'guardrail_blocks': 0,
                'total_time': 0.0
            }
    
    def render_header(self):
        """Render the main application header"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 2rem; color: white; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);'>
            <h1>🚀 Sales Assistant Agents</h1>
            <p style='font-size: 1.1em; margin: 0;'>OpenAI Agents SDK | 🛡️ Security Guardrails | 🔧 Agents as Tools | 🌊 Streaming</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self) -> tuple:
        """Render sidebar configuration and return selected options"""
        with st.sidebar:
            st.markdown("### ⚙️ Configuration")
            
            # Model selection
            available_models = get_available_models()
            model_names = list(available_models.keys())
            
            # Group models by provider for better UX
            openai_models = [name for name in model_names if available_models[name].provider == ModelProvider.OPENAI]
            bedrock_models = [name for name in model_names if available_models[name].provider == ModelProvider.BEDROCK]
            
            st.markdown("**🤖 OpenAI Models:**")
            for model in openai_models:
                st.markdown(f"• {available_models[model].display_name}")
            
            st.markdown("**🧠 Bedrock Claude Models:**")
            for model in bedrock_models:
                st.markdown(f"• {available_models[model].display_name}")
            
            model_choice = st.selectbox(
                "Select AI Model:",
                model_names,
                index=1,  # Default to second model
                help="Choose between OpenAI and Bedrock Claude models"
            )
            
            # Display model info
            selected_model = available_models[model_choice]
            st.info(f"**{selected_model.display_name}**\n\n{selected_model.description}")
            
            # Session configuration
            st.markdown("### 💾 Session Management")
            session_type = st.radio(
                "Memory Type:",
                ["persistent", "temporary"],
                help="Persistent: SQLite file, survives restart\nTemporary: In-memory, cleared when app closes"
            )
            
            # Session controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Chat"):
                    asyncio.run(session_manager.clear_session(st.session_state.user_id, session_type))
                    st.session_state.chat_history = []
                    st.success("✅ Cleared!")
                    st.experimental_rerun()
            
            with col2:
                if st.button("📊 Reset Metrics"):
                    st.session_state.metrics = {
                        'total_queries': 0, 'successful_queries': 0, 
                        'guardrail_blocks': 0, 'total_time': 0.0
                    }
                    st.success("✅ Reset!")
                    st.experimental_rerun()
            
            # Metrics display
            self.render_metrics()
            
            # System health
            self.render_system_health()
            
            # Guardrail testing guide
            self.render_guardrail_guide()
            
            return model_choice, session_type
    
    def render_metrics(self):
        """Render performance metrics"""
        st.markdown("### 📈 Performance Metrics")
        
        metrics = st.session_state.metrics
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total Queries", metrics['total_queries'])
            st.metric("✅ Successful", metrics['successful_queries'])
        
        with col2:
            st.metric("🛡️ Guardrail Blocks", metrics['guardrail_blocks'])
            if metrics['successful_queries'] > 0:
                avg_time = metrics['total_time'] / metrics['successful_queries']
                st.metric("⚡ Avg Response Time", f"{avg_time:.2f}s")
            else:
                st.metric("⚡ Avg Response Time", "0.00s")
        
        # Success rate
        if metrics['total_queries'] > 0:
            success_rate = (metrics['successful_queries'] / metrics['total_queries']) * 100
            st.progress(success_rate / 100)
            st.caption(f"Success Rate: {success_rate:.1f}%")
    
    def render_system_health(self):
        """Render system health status"""
        st.markdown("### 🏥 System Health")
        
        # Knowledge Base status
        kb_health = knowledge_base.health_check()
        if kb_health["available"]:
            st.success("✅ Knowledge Base: Connected")
        else:
            st.warning("⚠️ Knowledge Base: Mock Mode")
        
        # Session manager
        active_sessions = len(session_manager.list_active_sessions())
        st.info(f"💾 Active Sessions: {active_sessions}")
        
        # Model status
        if self.orchestrator:
            st.success("✅ Orchestrator: Ready")
        else:
            st.warning("⚠️ Orchestrator: Initializing")
    
    def render_guardrail_guide(self):
        """Render guardrail testing guide"""
        st.markdown("### 🛡️ Guardrail Testing")
        
        st.error("❌ **These queries are BLOCKED:**")
        blocked_examples = [
            "What is Dr. Julie's phone number?",
            "Tell me Dr. Shafique's email address", 
            "What is 25 + 37?",
            "Tell me a joke",
            "What's Dr. Julie's SSN?"
        ]
        for example in blocked_examples:
            st.code(f'"{example}"', language="text")
        
        st.success("✅ **These queries are ALLOWED:**")
        allowed_examples = [
            "What tests did Dr. Julie order?",
            "Who has Dr. Shafique contacted?",
            "Show me Dr. Julie's engagements", 
            "What are Guardant360 features?",
            "Analyze Dr. Julie's account comprehensively"
        ]
        for example in allowed_examples:
            st.code(f'"{example}"', language="text")
    
    def initialize_orchestrator(self, model_name: str):
        """Initialize the orchestrator with selected model"""
        if self.current_model != model_name:
            with st.spinner(f"🔄 Initializing {model_name}..."):
                try:
                    self.orchestrator = SalesOrchestrator(
                        model_name=model_name,
                        enable_guardrails=True,
                        enable_tracing=False
                    )
                    self.current_model = model_name
                    st.success("✅ Agent initialized!")
                    
                except Exception as e:
                    st.error(f"❌ Failed to initialize: {e}")
                    print(f"❌ Initialization error: {e}")
                    self.orchestrator = None
    
    def render_welcome_message(self):
        """Render welcome message with capabilities"""
        if not st.session_state.chat_history:
            st.markdown("""
            <div class='guardrail-test'>
                <h2 style="color: #495057; text-align: center;">🔧 Sales Assistant Capabilities</h2>
                
                <div style="text-align: left; max-width: 800px; margin: 0 auto;">
                    <h4 style="color: #28a745;">✅ Available Business Queries:</h4>
                    <ul>
                        <li><code>"What tests did Dr. Julie order?"</code> - Salesforce order data</li>
                        <li><code>"Who has Dr. Shafique contacted?"</code> - Veeva relationship data</li>
                        <li><code>"Analyze Dr. Julie's account comprehensively"</code> - Multi-tool analysis</li>
                        <li><code>"What are Guardant360 features?"</code> - Knowledge Base product info</li>
                        <li><code>"Show me analytics trends"</code> - Tableau business intelligence</li>
                        <li><code>"Dr. Julie's compliance status"</code> - Stark Law compliance</li>
                    </ul>
                    
                    <h4 style="color: #dc3545;">🧪 Test Security Guardrails (Will be blocked):</h4>
                    <ul>
                        <li><code>"What is Dr. Julie's phone number?"</code> - PII protection</li>
                        <li><code>"What is 25 + 37?"</code> - Math problem filtering</li> 
                        <li><code>"Tell me a joke"</code> - Inappropriate content blocking</li>
                    </ul>
                    
                    <h4 style="color: #667eea;">🔧 Key Features:</h4>
                    <ul>
                        <li>✅ <strong>Agents as Tools</strong>: Parallel data source access</li>
                        <li>✅ <strong>Security Guardrails</strong>: PII protection & content filtering</li>
                        <li>✅ <strong>Multi-Model Support</strong>: OpenAI GPT-4o + Bedrock Claude</li>
                        <li>✅ <strong>Session Management</strong>: Persistent conversation history</li>
                        <li>✅ <strong>Real Data Sources</strong>: Salesforce, Veeva, Tableau, Knowledge Base</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_chat_interface(self, session_type: str):
        """Render the main chat interface"""
        # Display chat history
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
                    
            elif message['role'] == 'assistant':
                with st.chat_message("assistant"):
                    st.markdown(f"<div class='streaming-text'>{message['content']}</div>", unsafe_allow_html=True)
                    
                    if 'metadata' in message:
                        metadata = message['metadata']
                        tools_text = ', '.join(metadata.get('tools_used', ['None']))
                        
                        st.caption(
                            f"⚡ {metadata.get('execution_time', 0):.2f}s | "
                            f"🤖 {metadata.get('model', 'Unknown')} | "
                            f"🔧 Tools: {tools_text} | "
                            f"💾 {metadata.get('session_type', 'Unknown')}"
                        )
                        
            elif message['role'] == 'error':
                with st.chat_message("assistant"):
                    st.error(message['content'])
        
        # Chat input
        if prompt := st.chat_input("🧪 Try: 'Who has Dr. Shafique contacted?' (new!) vs 'What is Dr. Julie's phone number?' (blocked)"):
            self.process_user_input(prompt, session_type)
    
    def process_user_input(self, prompt: str, session_type: str):
        """Process user input and generate response"""
        if not self.orchestrator:
            st.error("❌ Orchestrator not initialized. Please select a model first.")
            return
        
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("⌨️ Processing your request..."):
                try:
                    # Get session
                    session = session_manager.get_session(
                        st.session_state.user_id, 
                        session_type
                    )
                    
                    # Process query
                    result = asyncio.run(self.orchestrator.process_query(
                        prompt,
                        user_context={
                            "name": "Sales Representative",
                            "territory": "Northeast", 
                            "role": "Sales Rep"
                        },
                        session=session
                    ))
                    
                    if result["success"]:
                        # Display response
                        st.markdown(f"<div class='streaming-text'>{result['response']}</div>", unsafe_allow_html=True)
                        
                        # Update metrics
                        st.session_state.metrics['total_queries'] += 1
                        st.session_state.metrics['successful_queries'] += 1
                        st.session_state.metrics['total_time'] += result['execution_time']
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': result['response'],
                            'timestamp': datetime.now().isoformat(),
                            'metadata': {
                                'execution_time': result['execution_time'],
                                'tools_used': result.get('tools_used', []),
                                'session_type': session_type,
                                'model': result.get('model', 'Unknown')
                            }
                        })
                        
                    else:
                        # Handle error
                        st.error(result['response'])
                        
                        # Update metrics
                        st.session_state.metrics['total_queries'] += 1
                        if "Guardrail" in result['response']:
                            st.session_state.metrics['guardrail_blocks'] += 1
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'role': 'error',
                            'content': result['response'],
                            'timestamp': datetime.now().isoformat()
                        })
                
                except InputGuardrailTripwireTriggered as e:
                    error_msg = f"🛡️ **Security Guardrail Triggered**: Your query was blocked for security reasons.\n\n{str(e)}"
                    st.error(error_msg)
                    
                    # Update metrics
                    st.session_state.metrics['total_queries'] += 1
                    st.session_state.metrics['guardrail_blocks'] += 1
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'role': 'error',
                        'content': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                
                except Exception as e:
                    error_msg = f"❌ **Unexpected Error**: {str(e)}"
                    st.error(error_msg)
                    
                    # Update metrics
                    st.session_state.metrics['total_queries'] += 1
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'role': 'error', 
                        'content': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Rerun to update the interface
        st.experimental_rerun()
    
    def run(self):
        """Main application runner"""
        # Render header
        self.render_header()
        
        # Render sidebar and get configuration
        model_choice, session_type = self.render_sidebar()
        
        # Initialize orchestrator
        self.initialize_orchestrator(model_choice)
        
        # Render welcome message
        self.render_welcome_message()
        
        # Render chat interface
        self.render_chat_interface(session_type)


def main():
    """Main entry point"""
    app = SalesAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
