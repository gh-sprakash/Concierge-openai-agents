# 🚀 Sales Assistant Agents - OpenAI Agents

A comprehensive multi-agent sales assistant system built with OpenAI Agents SDK and AWS Bedrock integration. Features advanced security guardrails, persistent session management, and real-time business data integration.

## 🎯 Key Features

✅ **Agents as Tools**: Parallel data source access with intelligent orchestration  
✅ **Security Guardrails**: PII protection and content filtering  
✅ **Multi-Model Support**: OpenAI GPT-4o + Bedrock Claude models  
✅ **Session Management**: Persistent conversation history with SQLite  
✅ **Real Data Sources**: Salesforce, Veeva, Tableau, Knowledge Base integration  
✅ **Streaming Responses**: Real-time response generation with safety monitoring  
✅ **Production Ready**: Complete Streamlit web interface  

## 📚 Implementation Notebooks

The `ai-agents-implementation/` folder contains detailed implementation guides:

| Notebook | Key Implementation |
|----------|-------------------|
| `01_Environment_Setup_Dependencies.ipynb` | Multi-provider setup (OpenAI + Bedrock), model configurations, connection testing |
| `02_Session_Memory_Management.ipynb` | Persistent memory with OpenAI Agents SDK, multi-user session isolation |
| `03_Agent_Creation_Tools.ipynb` | Unified OpenAI+Bedrock interface, business tool integration, multi-provider orchestration |
| `04_Advanced_Agent_Patterns.ipynb` | Parallel execution patterns, sequential workflows, structured outputs with Pydantic |
| `05_Guardrails_Simple.ipynb` | Input/output guardrails, production safety patterns, PII protection |
| `06_Streaming_Guardrails_Multi_Model.ipynb` | Real-time streaming safety, multi-model guardrails, early termination |

## 📁 Project Structure

```
sales-assistant-agents/
├── ai-agents-implementation/    # 📚 Implementation notebooks (START HERE)
│   ├── 01_Environment_Setup_Dependencies.ipynb
│   ├── 02_Session_Memory_Management_FIXED.ipynb
│   ├── 03_Agent_Creation_Tools_BEDROCK.ipynb
│   ├── 04_Advanced_Agent_Patterns.ipynb
│   ├── 06_Guardrails_Simple.ipynb
│   └── 07_Streaming_Guardrails_Multi_Model_FIXED.ipynb
├── requirements.txt             # Python dependencies
├── .env.example                # Environment configuration template
├── src/                        # Core application source
│   ├── models/                 # Model configurations (OpenAI + Claude)
│   ├── agents/                 # Agent tools and orchestrator
│   ├── guardrails/            # Security and PII protection
│   ├── sessions/              # Conversation memory management
│   ├── data/                  # Mock data sources (Salesforce, Veeva, Tableau)
│   ├── knowledge/             # AWS Bedrock Knowledge Base integration
│   └── utils/                 # Streaming and utility functions
└── examples/
    └── streamlit_app.py       # Complete web interface
```

  🚀 Quick Start

  1. Review Implementation: Start with the notebooks in ai-agents-implementation/ to understand the architecture
  2. Install Dependencies: pip install -r requirements.txt
  3. Configure Environment: Copy .env.example to .env and add your API keys
  4. Run Application: streamlit run examples/streamlit_app.py

  🔧 Core Technologies

  - OpenAI Agents SDK: Memory management and agent orchestration
  - AWS Bedrock: Claude models via LiteLLM integration
  - Streamlit: Production web interface
  - SQLite: Persistent session storage
  - Pydantic: Type-safe data models
  - AsyncIO: Parallel processing and streaming

  ---
  Start with the implementation notebooks to understand how each component was built, then explore the production 
  application in the examples folder.


### 1. Installation

```bash
# Clone or create the project directory
cd sales-assistant-agents

# In case you are on a server. Run the following command only the first time. 
python -m venv ~/.agents

# In case you are on a server.
source ~/.agents/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# AWS Bedrock Configuration (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-key-here
AWS_REGION_NAME=us-west-2
```

### 3. Run the Application

```bash
# Start the Streamlit interface
streamlit run examples/streamlit_app.py
```

Visit `http://localhost:8501` to access the web interface.

## 🔧 Available Models

### OpenAI Models
- **🤖 GPT-4o**: Latest GPT-4 Omni model - Best overall performance
- **🤖 GPT-4o Mini**: Faster, cost-effective GPT-4o variant  
- **🤖 GPT-4 Turbo**: High performance with faster response times

### Bedrock Claude Models
- **🧠 Claude 3.5 Sonnet**: Latest Claude with superior reasoning
- **🧠 Claude 3.5 Haiku**: Fast and efficient for quick responses
- **🧠 Claude 3 Sonnet**: Previous generation with reliable performance

## 🧪 Testing the System

### ✅ Allowed Business Queries

Try these examples to see the system in action:

```
"What tests did Dr. Julie order?"
"Who has Dr. Shafique contacted?"
"Analyze Dr. Julie's account comprehensively"
"What are Guardant360 features?"
"Show me analytics trends"
"Dr. Ahmed's compliance status"
```

### ❌ Blocked Security Tests

These queries will be blocked by guardrails:

```
"What is Dr. Julie's phone number?"     # PII protection
"Tell me Dr. Shafique's email address"  # PII protection
"What is 25 + 37?"                      # Math filtering
"Tell me a joke"                        # Inappropriate content
```

## 🔧 Data Sources

The system integrates with multiple mock data sources:

### Salesforce CRM
- Order history and status
- Financial totals and summaries
- Stark Law compliance data

### Veeva CRM  
- Healthcare professional engagements
- Contact relationship mapping
- Meeting outcomes and talking points

### Tableau Analytics
- Test ordering trends
- Regional performance metrics
- Customer satisfaction scores

### AWS Bedrock Knowledge Base
- Product specifications and features
- Clinical studies and evidence
- Training materials and best practices

## 🛡️ Security Features

### PII Protection
- Phone numbers, email addresses blocked
- Social Security numbers filtered
- Personal address requests denied

### Content Filtering
- Math problems and calculations blocked
- Jokes and entertainment content filtered
- Off-topic queries restricted

### Output Safety
- Response scanning for leaked PII
- Pattern matching for sensitive data
- Secondary safety checks

## 💾 Session Management

### Persistent Sessions
- SQLite file storage
- Survives application restart
- Conversation history preserved

### Temporary Sessions  
- In-memory storage
- Cleared when application closes
- Faster for short-term use

## 📊 Performance Metrics

The application tracks:
- Total queries processed
- Successful vs. blocked queries  
- Guardrail activation rate
- Average response times
- Success rate percentages

## 🏥 System Health Monitoring

- Knowledge Base connectivity status
- Active session tracking
- Model initialization status
- Component health checks

## 🔄 Development Usage

### Quick Setup

```python
from src import create_sales_assistant

# Initialize system
orchestrator, session_manager = create_sales_assistant(
    model_name="openai-gpt-4o-mini",
    enable_guardrails=True,
    persistent_sessions=True
)

# Process a query
result = await orchestrator.process_query(
    "What orders did Dr. Julie place?",
    user_context={"name": "Sales Rep", "territory": "Northeast"}
)

print(result["response"])
```

### Custom Integration

```python
from src.agents.orchestrator import SalesOrchestrator
from src.sessions.manager import session_manager

# Initialize orchestrator
orchestrator = SalesOrchestrator(
    model_name="claude-3-5-sonnet",
    enable_guardrails=True
)

# Get user session
session = session_manager.get_session("user_123", "persistent")

# Process with session
result = await orchestrator.process_query(
    "Analyze Dr. Ahmed's account comprehensively",
    session=session
)
```

## 🎨 Streamlit Interface

The included Streamlit application provides:

- **Model Selection**: Choose between OpenAI and Claude models
- **Session Management**: Persistent vs. temporary memory
- **Real-time Chat**: Interactive conversation interface  
- **Performance Metrics**: Query success rates and timing
- **System Health**: Component status monitoring
- **Guardrail Testing**: Interactive security demonstrations

## 🔧 Customization

### Adding New Data Sources

1. Create data source in `src/data/new_source.py`
2. Add function tool in `src/agents/tools.py`  
3. Import in orchestrator tools list

### Custom Security Policies

```python
from src.guardrails.security import create_custom_policy_guardrail

# Create HIPAA policy guardrail
hipaa_guardrail = create_custom_policy_guardrail(
    policy_name="HIPAA",
    policy_rules=[
        "No patient health information requests",
        "No medical record access",
        "No treatment information sharing"
    ]
)
```

### Additional Models

Add new models in `src/models/config.py`:

```python
"new-model": ModelConfig(
    name="new-model",
    provider=ModelProvider.OPENAI,
    model_id="gpt-4-new",
    display_name="🤖 New Model",
    description="Description of capabilities"
)
```

## 📈 Production Deployment

### Environment Variables

Set these in production:

```bash
OPENAI_API_KEY=your-production-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
LOG_LEVEL=INFO
DEBUG=False
```

### Session Cleanup

```python
# Clean up old sessions (30+ days)
session_manager.cleanup_old_sessions(days_old=30)
```

### Health Monitoring

```python
# Check system health
health = orchestrator.health_check()
kb_health = knowledge_base.health_check()
```

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**: Verify environment variables are set correctly
**Model Initialization**: Check model name matches available configurations
**Session Errors**: Ensure sessions directory has write permissions
**Guardrail Blocks**: Review security policy to understand blocks

### Debug Mode

Set `DEBUG=True` in `.env` for detailed logging.



