# Market Feasibility Analysis Chatbot - Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [System Components](#system-components)
4. [Multi-Agent System](#multi-agent-system)
5. [API Endpoints](#api-endpoints)
6. [Tools and Integrations](#tools-and-integrations)
7. [Data Sources](#data-sources)
8. [Deployment](#deployment)
9. [Development Setup](#development-setup)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance Guide](#maintenance-guide)

## Project Overview

The Market Feasibility Analysis Chatbot is an AI-powered API service designed to perform comprehensive market feasibility analysis for businesses. The system utilizes a multi-agent architecture with Large Language Models (LLMs) to analyze market conditions, competitor landscapes, and provide detailed feasibility reports for specific business types and locations.

### Key Features
- **Multi-Agent LLM System**: Coordinated agents for data collection, analysis, and reporting
- **Market Data Collection**: Integration with Perplexity API for real-time market research
- **Geographic Analysis**: Google Maps API integration for competitor and demographic analysis
- **Sales Forecasting**: Machine learning-based sales projection models
- **RESTful API**: Flask-based API for easy integration
- **LINE Bot Integration**: Direct messaging interface for users
- **Cloud-Ready**: Dockerized for Google Cloud Platform deployment

### Supported Business Types
- Food & Restaurant businesses
- Real Estate projects
- Retail establishments
- Service businesses

## Architecture

The system follows a microservices architecture with the following high-level components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   LINE Bot      │    │   Web API       │
│                 │    │   Interface     │    │   Interface     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │      Flask API Server       │
                    │        (api.py)             │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │   Multi-Agent Orchestrator  │
                    │   (chatbot_multiagent.py)   │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐    ┌─────────────▼───────────────┐    ┌───▼────┐
│   Data         │    │      Agent Network          │    │ Tools  │
│ Collection     │    │ ┌─────────────────────────┐ │    │ & APIs │
│   Agents       │    │ │  - Analyst Agent        │ │    │        │
│                │    │ │  - Data Collector Agent │ │    │        │
└────────────────┘    │ │  - Data Analyst Agent   │ │    └────────┘
                      │ │  - Reporter Agent       │ │
                      │ └─────────────────────────┘ │
                      └─────────────────────────────┘
```

## System Components

### 1. API Layer (`api.py`)
The main Flask application serving as the entry point for all requests.

**Key Endpoints:**
- `POST /` - LINE Bot webhook for message processing
- `POST /test` - Testing endpoint for direct API calls
- `GET /health` - Health check endpoint

**Features:**
- CORS enabled for cross-origin requests
- Error handling and logging
- LINE Bot message processing
- Response formatting

### 2. Multi-Agent System (`chatbot_multiagent.py`)
Core orchestration system managing the flow between different AI agents.

**Main Function:**
```python
def submitUserMessage(
    user_input: str, 
    user_id: str = "test", 
    keep_chat_history: bool = False, 
    return_reference: bool = False, 
    verbose: bool = False,
    recursion_limit: int = 20
) -> str
```

### 3. Agent Network (`agents/`)
Specialized AI agents for different analysis tasks:

#### Analyst Agent
- **Role**: Request understanding and routing
- **Responsibilities**: 
  - Parse user requests for location and business type
  - Route to appropriate data collection agents
  - Handle follow-up questions

#### Data Collector Agents
- **Food Data Collector**: Specializes in restaurant and food business analysis
- **Real Estate Data Collector**: Focuses on property and real estate markets

#### Data Analyst Agent
- **Role**: Process and analyze collected data
- **Responsibilities**: Synthesize information from multiple sources

#### Reporter Agent
- **Role**: Generate final feasibility reports
- **Responsibilities**: Create comprehensive, formatted analysis reports

### 4. Tools and Integrations (`tools/`)
External service integrations and utility functions:

#### Google Maps Integration (`tools/gplace.py`)
- Location search and validation
- Competitor identification
- Demographic analysis
- Nearby business discovery

#### Perplexity API Integration
- Real-time market research
- Competitor pricing information
- Market trend analysis

#### Sales Forecasting (`tools/sale_forecasting.py`)
- Machine learning-based sales predictions
- Revenue projections
- Market size estimation

## Multi-Agent System

### Agent State Management
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    chat_history: List[BaseMessage]
    data_context: list[str] = []
    sender: str
    user_request: dict
```

### Workflow Orchestration
The system uses LangGraph for agent coordination with conditional routing:

1. **Analyst Router**: Determines business type and routes to appropriate collector
2. **Data Collection**: Gathers market, competitor, and demographic data
3. **Analysis**: Processes collected information
4. **Reporting**: Generates final feasibility analysis

### Agent Communication
Agents communicate through a shared state system with message passing:
- **Tool Calls**: Agents can invoke external tools
- **Data Context**: Shared information between agents
- **Message History**: Conversation continuity

## API Endpoints

### POST /
**LINE Bot Webhook**
- Processes incoming LINE messages
- Handles user authentication via `userId`
- Maintains conversation history
- Returns formatted responses

### POST /test
**Testing Interface**
```json
{
  "message": "Coffee shop near MBK Center",
  "user_id": "test_user_123"
}
```

**Response:**
```json
{
  "response": "Detailed feasibility analysis report..."
}
```

### GET /health
**Health Check**
- Returns system status
- Used for monitoring and load balancer health checks

## Tools and Integrations

### 1. Geographic Data Tools
```python
@tool
def get_geometric_data(input_dict: NearbySearchInput):
    """
    Comprehensive geographic analysis including:
    - Nearby competitors
    - Dense community identification
    - Population statistics
    - Household expenditure data
    """
```

### 2. Market Research Tools
```python
@tool
def duckduckgo_search(query: str):
    """
    Real-time market research using Perplexity API:
    - Competitor pricing
    - Market trends
    - Business information
    """
```

### 3. Sales Forecasting Tools
```python
@tool
def restaurant_sale_projection(input_dict: RestaurantSaleProject):
    """
    ML-based sales forecasting:
    - Revenue projections
    - Order volume estimates
    - Profitability analysis
    """
```

## Data Sources

### 1. Statistical Data (`document/`)
- **Community Type by District**: Demographic classification
- **Population Data by District**: Population statistics
- **Household Expenditures**: Spending patterns by province and category
- **Restaurant Sales Data**: Historical sales data for ML training

### 2. External APIs
- **Google Maps API**: Location and business data
- **Perplexity API**: Real-time web search and analysis
- **OpenAI API**: LLM processing

### 3. Machine Learning Models (`model/`)
- **Restaurant Sales Predictor**: Trained model for sales forecasting
- **Feature Engineering**: Category-based prediction features

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11.9-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 8080
CMD gunicorn --bind :8080 api:app --timeout 600
```

### Environment Variables
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key
GPLACES_API_KEY=your_google_maps_key
PPLX_API_KEY=your_perplexity_key

# LINE Bot Configuration (if using)
LINE_TOKEN=your_line_token
LINE_SECRET=your_line_secret

# Application Settings
BOT_VERBOSE=1
LANGCHAIN_TRACING_V2=false
```

### Google Cloud Platform Deployment
1. Build Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run or Compute Engine
4. Configure environment variables
5. Set up monitoring and logging

## Development Setup

### Prerequisites
- Python 3.11+
- Virtual environment
- API keys for external services

### Installation
```bash
# Clone repository
git clone <repository-url>
cd market-feasibility-analysis-chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run development server
python api.py
```

### Testing
```bash
# Run API tests
python test/api_request_test.py

# Run chatbot QA tests
python test/chatbot_QA_test.py
```

## Troubleshooting

### Common Issues

#### 1. API Rate Limits
**Symptom**: `RatelimitException` errors
**Solution**: 
- Implement exponential backoff
- Monitor API usage
- Consider upgrading API plans

#### 2. Memory Issues
**Symptom**: Out of memory errors during processing
**Solution**:
- Optimize agent state management
- Implement conversation pruning
- Increase container memory limits

#### 3. Model Loading Errors
**Symptom**: `FileNotFoundError` for ML models
**Solution**:
- Verify model files exist in `model/` directory
- Check file permissions
- Validate pickle file integrity

### Debugging Tools

#### Verbose Mode
Enable detailed logging:
```python
result = submitUserMessage(
    user_message, 
    verbose=True,
    return_reference=True
)
```

#### Agent State Inspection
Monitor agent communications and state changes through LangGraph debugging.

## Maintenance Guide

### Regular Tasks

#### 1. Model Updates
- Retrain sales forecasting models quarterly
- Update training data with new market information
- Validate model performance metrics

#### 2. Data Refresh
- Update demographic and economic data annually
- Refresh competitor databases
- Validate data source reliability

#### 3. API Monitoring
- Monitor rate limits and usage patterns
- Track response times and error rates
- Update API keys before expiration

### Performance Optimization

#### 1. Caching Strategy
- Implement Redis for frequent geographic queries
- Cache demographic data for common locations
- Store processed competitor information

#### 2. Database Optimization
- Index frequently queried data
- Optimize vector store performance
- Regular data cleanup and archival

### Security Considerations

#### 1. API Key Management
- Rotate keys regularly
- Use environment variables, never hardcode
- Implement key monitoring and alerting

#### 2. Input Validation
- Sanitize user inputs
- Validate location data
- Implement rate limiting per user

### Monitoring and Alerting

#### 1. Application Metrics
- Response time monitoring
- Error rate tracking
- Agent performance metrics

#### 2. Infrastructure Monitoring
- CPU and memory usage
- Network latency
- Storage utilization

## Code Structure Reference

### Key Files
- `api.py`: Flask API server and endpoints
- `chatbot_multiagent.py`: Multi-agent orchestration
- `agents/__init__.py`: Agent definitions and node builders
- `agents/prompt.py`: Agent prompts and instructions
- `tools/__init__.py`: Tool definitions and integrations
- `tools/gplace.py`: Google Maps API integration
- `tools/sale_forecasting.py`: ML-based sales predictions

### Configuration Files
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container configuration
- `.env`: Environment variables (not in repo)

### Data Directories
- `document/`: Statistical and demographic data
- `model/`: Machine learning models
- `test/`: Test files and datasets

---

This documentation provides a comprehensive guide for developers and maintainers working on the Market Feasibility Analysis Chatbot. For specific implementation details, refer to the source code and inline documentation.
