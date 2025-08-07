# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Environment setup - copy .env.example to .env and configure:
# OPENAI_API_KEY=sk-your-openai-api-key-here
# AWS_ACCESS_KEY_ID=your-aws-access-key-here (optional for Bedrock)
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key-here (optional for Bedrock)
# AWS_REGION_NAME=us-west-2
```

### Running the Application
```bash
# Start the Streamlit web interface
streamlit run examples/streamlit_app.py

# Access at http://localhost:8501
```

### Testing
```bash
# Run tests (if available)
pytest

# Run async tests  
pytest -v pytest-asyncio

# Run with coverage
pytest --cov=src
```

## Docker Deployment (AWS EC2)

### Build and Run with Docker
```bash
# Build the Docker image
docker build -t sales-assistant .

# Run with environment variables
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your-key-here \
  -e AWS_ACCESS_KEY_ID=your-aws-key \
  -e AWS_SECRET_ACCESS_KEY=your-aws-secret \
  -e AWS_REGION_NAME=us-west-2 \
  -v $(pwd)/sessions:/app/sessions \
  sales-assistant

# Access at http://your-ec2-ip:8501
```

### Using Docker Compose
```bash
# Set environment variables in .env file:
# OPENAI_API_KEY=sk-your-openai-api-key-here
# AWS_ACCESS_KEY_ID=your-aws-access-key-here
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key-here
# AWS_REGION_NAME=us-west-2

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application  
docker-compose down
```

### EC2 Deployment Steps
```bash
# 1. Install Docker on AWS Linux 2
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone repository and deploy
git clone <your-repo-url>
cd Concierge-openai-agents
# Create .env file with your API keys
docker-compose up -d
```

## Architecture Overview

This is a **multi-agent sales assistant system** built with the OpenAI Agents SDK and AWS Bedrock integration. The architecture follows the "agents as tools" pattern for optimal performance and modularity.

### Core Components

**Models (`src/models/config.py`)**
- Unified configuration for OpenAI GPT-4o models and Bedrock Claude models via LiteLLM
- ModelProvider enum supports OPENAI and BEDROCK providers
- Default model recommendations by use case (general, reasoning, fast, comprehensive)

**Orchestrator (`src/agents/orchestrator.py`)**  
- Single `SalesOrchestrator` agent with all business tools integrated
- Supports both synchronous and streaming responses
- Built-in guardrails and session management integration
- Tools: Salesforce, Veeva CRM, Knowledge Base, Tableau Analytics, Compliance

**Session Management (`src/sessions/manager.py`)**
- Persistent SQLite-based sessions that survive app restarts
- Temporary in-memory sessions for short-term use
- Thread-safe session management with automatic cleanup

**Security (`src/guardrails/security.py`)**
- Input/output guardrails with PII protection (phone numbers, emails, SSN)
- Content filtering (blocks math problems, jokes, inappropriate requests)
- Multi-layer security with pattern matching and keyword detection

**Data Sources (`src/data/`)**
- Mock integrations for Salesforce CRM, Veeva CRM, and Tableau Analytics
- AWS Bedrock Knowledge Base integration (`src/knowledge/bedrock_kb.py`)
- Each data source provides realistic business data for demonstration

### Key Architectural Patterns

**"Agents as Tools" Pattern**
- Single orchestrator agent contains all business tools rather than multiple specialized agents
- Reduces complexity and improves performance compared to agent-to-agent communication
- Agent intelligently selects appropriate tools based on query context

**Multi-Model Support**
- Seamless switching between OpenAI and Bedrock Claude models
- Model-specific configuration (temperature, max_tokens) handled automatically
- Provider-agnostic interface through OpenAI Agents SDK + LiteLLM

**Streaming with Guardrails**
- Real-time response streaming with concurrent safety monitoring
- Early termination if guardrails are triggered during streaming
- Maintains user experience while ensuring content safety

## Data Flow

1. **Query Processing**: User input → Guardrails → Orchestrator Agent
2. **Tool Execution**: Agent selects appropriate business tools (Salesforce, Veeva, etc.)
3. **Response Generation**: Tools return structured data → Agent synthesizes comprehensive response
4. **Safety Check**: Output guardrails scan for PII/inappropriate content → Final response
5. **Session Storage**: Conversation history persisted to SQLite (if persistent session enabled)

## Business Context

The system is designed for **sales representatives in healthcare/pharma** to access enterprise data sources:

- **Salesforce**: Order history, customer information, compliance data
- **Veeva CRM**: Healthcare professional engagements and relationships  
- **Knowledge Base**: Product specifications, clinical studies, training materials
- **Tableau**: Business analytics, performance metrics, regional trends
- **Compliance**: Stark Law compliance, spending limits, risk assessment

## Implementation Notes

- All business data is **mock data** - no real customer information
- Guardrails specifically block PII requests to demonstrate enterprise safety
- Session databases are stored in `/sessions/` directory
- The system demonstrates production-ready patterns: error handling, health checks, performance monitoring
- Streamlit interface provides comprehensive testing of all system capabilities

## Key Files for Customization

- `src/models/config.py`: Add new model configurations
- `src/agents/tools.py`: Add new business data source tools
- `src/guardrails/security.py`: Modify security policies
- `examples/streamlit_app.py`: Production web interface