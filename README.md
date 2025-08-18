# 🎯 Todo List Multi-Agent AI System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.0-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.4-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)

## 📖 Project Description

**Todo List Multi-Agent AI System** is an intelligent task management application built on Multi-Agent architecture with LangGraph. This project was developed to solve time management and effective learning problems for students and learners.

### 🎯 Problems Solved
- **Complex Task Management**: Students often struggle with organizing and prioritizing their learning tasks
- **Lack of Performance Insights**: No analytical tools to understand study habits and improve productivity
- **Scattered Learning Information**: Difficulty accessing school information (tuition fees, regulations, scholarships...)
- **Personalized Consultation**: Need for intelligent advisory system based on personal data

### 💡 Multi-Agent Solution
Instead of using a general AI, the system is divided into specialized experts (agents):
- **Schedule Agent**: Todo list management specialist
- **Analytics Agent**: Analysis and advisory specialist
- **RAG Agent**: Academic information specialist
- **Generic Agent**: General support and search

### 🔬 Technology Stack
- **LangGraph**: Orchestration framework for multi-agent workflows
- **Google Gemini 2.5 Flash**: Primary Large Language Model
- **PostgreSQL**: Database with JSONB support for checkpoints
- **Pinecone**: Vector database for RAG capabilities
- **FastAPI**: REST API with streaming support

## 🌟 Key Features

### 🤖 Multi-Agent Architecture
#### 📋 Schedule Agent - Todo Management
- **Function**: Manage CRUD operations for todo list
- **Tools**:
  - `create_todo`: Create new tasks with detailed information
  - `get_todos`: Get todos list by user_id  
  - `update_todo`: Update tasks (status, priority, deadline...)
  - `delete_todo`: Delete tasks by ID
- **Database**: Direct access to `todos` table in PostgreSQL

#### 📚 RAG Agent - Knowledge Base
- **Function**: Provide academic information consultation from school knowledge base
- **Tools**:
  - `rag_retrieve`: Semantic search in vector database
- **Data Sources**: Documents about tuition fees, regulations, scholarships, FAQ
- **Vector Store**: Pinecone with HuggingFace embeddings

#### 📊 Analytics Agent - Performance Analysis
- **Function**: Analyze learning performance and provide recommendations
- **Tools**:
  - `todo_analytics`: Diverse analysis tool with modes:
    - `productivity`: Completion performance analysis
    - `patterns`: Time-based habit analysis
    - `completion_rate`: Completion rate trends
    - `workload`: Workload assessment
- **Analytics Engine**: SQL aggregation + templated insights

#### 🔍 Generic Agent - General Purpose
- **Function**: Handle general questions and web search
- **Tools**:
  - `tavily_search`: Real-time web search with Tavily API
- **Use Cases**: New information search, general chat, learning consultation

## 📱 Modern Tech Stack
- **Backend**: FastAPI with Python 3.12
- **AI/ML**: LangGraph, LangChain, Google Gemini
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Store**: Pinecone for RAG capabilities

## Agent Flow Diagram

![Agent Flow Diagram](./img/graph.png)

## 🚀 System Requirements
- Python 3.12+
- PostgreSQL 15+

## 🎯 How to Use Each Agent

### 📋 Schedule Agent - Todo Management
```
🔹 Create task: "Create a Python learning task with tomorrow's deadline"
🔹 View tasks: "Show all my tasks"
🔹 Update: "Mark task #1 as completed"
🔹 Delete task: "Delete task #3"
```

### 📊 Analytics Agent - Performance Analysis
```
🔹 Performance: "Analyze learning performance over the past 30 days"
🔹 Pattern: "Find my golden working hours"
🔹 Trends: "What's my task completion rate?"
🔹 Recommendations: "Advise optimal learning schedule"
```

### 📚 RAG Agent - Academic Consultation
```
🔹 Tuition: "How much does Computer Science major cost?"
🔹 Scholarships: "What types of scholarships are available?"
🔹 Regulations: "What are the dress code regulations?"
```

### 🔍 Generic Agent - Search and Chat
```
🔹 Search: "AI technology trends 2025"
🔹 Consultation: "Programming learning roadmap for beginners"
🔹 Chat: "How to balance study and entertainment"
```

## 🔧 Configuration

### Main Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_URI` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `GOOGLE_API_KEY` | API key for Google Gemini | `AIza...` |
| `PINECONE_API_KEY` | API key for Pinecone vector DB | `pc-...` |
| `TAVILY_API_KEY` | API key for Tavily search | `tvly-...` |

### Agent Prompts Configuration
All prompts are defined in `src/agents/prompts.py` and can be customized:
- Router prompt for request routing
- Agent-specific prompts for each function
- Summarization prompt for context management

## 📚 Architecture Decisions

### Why Multi-Agent?
- **Separation of Concerns**: Each agent specializes in one domain
- **Scalability**: Easy to add new agents
- **Maintainability**: Clear logic and easy debugging

### Why LangGraph?
- **State Management**: Efficient conversation state management
- **Checkpointing**: Persistent conversation memory
- **Streaming**: Real-time response streaming
- **Tool Integration**: Native tool calling support

### Why PostgreSQL?
- **ACID Compliance**: Ensures data integrity
- **JSON Support**: Native JSONB for flexible schema
- **Performance**: Excellent indexing and query optimization
- **Extensions**: Rich ecosystem of extensions

## 📄 License

This project is released under MIT License.

**Developed by Syntax Error team.**
