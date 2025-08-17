# 🎯 Todo List Multi-Agent AI System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.0-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.4-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)

## 📖 Mô tả dự án

**Todo List Multi-Agent AI System** là một ứng dụng quản lý công việc thông minh được xây dựng dựa trên kiến trúc Multi-Agent với LangGraph. Dự án này được phát triển nhằm giải quyết bài toán quản lý thời gian và học tập hiệu quả cho sinh viên và người học.

### 🎯 Bài toán giải quyết
- **Quản lý công việc phức tạp**: Sinh viên thường gặp khó khăn trong việc sắp xếp và ưu tiên các task học tập
- **Thiếu insight về hiệu suất**: Không có công cụ phân tích để hiểu rõ thói quen học tập và cải thiện
- **Thông tin học tập phân tán**: Khó tiếp cận thông tin trường học (học phí, nội quy, học bổng...)
- **Tư vấn cá nhân hóa**: Cần có hệ thống tư vấn thông minh dựa trên dữ liệu cá nhân

### 💡 Giải pháp Multi-Agent
Thay vì sử dụng một AI tổng quát, hệ thống chia nhỏ thành các chuyên gia (agents) chuyên biệt:
- **Schedule Agent**: Chuyên gia quản lý todo list
- **Analytics Agent**: Chuyên gia phân tích và tư vấn
- **RAG Agent**: Chuyên gia thông tin học tập
- **Generic Agent**: Hỗ trợ tổng quát và tìm kiếm

### 🔬 Công nghệ sử dụng
- **LangGraph**: Orchestration framework cho multi-agent workflows
- **Google Gemini 2.5 Flash**: Large Language Model chính
- **PostgreSQL**: Database với JSONB support cho checkpoints
- **Pinecone**: Vector database cho RAG capabilities
- **FastAPI**: REST API với streaming support

## 🌟 Tính năng chính

### 🤖 Multi-Agent Architecture
#### 📋 Schedule Agent - Todo Management
- **Chức năng**: Quản lý CRUD operations cho todo list
- **Tools**:
  - `create_todo`: Tạo task mới với thông tin chi tiết
  - `get_todos`: Lấy danh sách todos theo user_id  
  - `update_todo`: Cập nhật task (status, priority, deadline...)
  - `delete_todo`: Xóa task theo ID
- **Database**: Truy cập trực tiếp bảng `todos` trong PostgreSQL

#### 📚 RAG Agent - Knowledge Base
- **Chức năng**: Tư vấn thông tin học tập từ cơ sở kiến thức trường học
- **Tools**:
  - `rag_retrieve`: Tìm kiếm semantic trong vector database
- **Data Sources**: Documents về học phí, nội quy, học bổng, FAQ
- **Vector Store**: Pinecone với embeddings từ HuggingFace

#### 📊 Analytics Agent - Performance Analysis
- **Chức năng**: Phân tích hiệu suất học tập và đưa ra khuyến nghị
- **Tools**:
  - `todo_analytics`: Công cụ phân tích đa dạng với các mode:
    - `productivity`: Phân tích hiệu suất hoàn thành
    - `patterns`: Phân tích thói quen theo thời gian
    - `completion_rate`: Xu hướng tỷ lệ hoàn thành
    - `workload`: Đánh giá khối lượng công việc
- **Analytics Engine**: SQL aggregation + templated insights

#### 🔍 Generic Agent - General Purpose
- **Chức năng**: Xử lý câu hỏi tổng quát và tìm kiếm web
- **Tools**:
  - `tavily_search`: Tìm kiếm web real-time với Tavily API
- **Use Cases**: Tìm kiếm thông tin mới, chat tổng quát, tư vấn học tập

## 📱 Modern Tech Stack
- **Backend**: FastAPI với Python 3.12
- **AI/ML**: LangGraph, LangChain, Google Gemini
- **Database**: PostgreSQL với SQLAlchemy ORM
- **Vector Store**: Pinecone cho RAG capabilities

## Agent Flow Diagram

![Agent Flow Diagram](./img/graph.png)

## 🚀 Yêu cầu hệ thống
- Python 3.12+
- PostgreSQL 15+

## 🎯 Cách sử dụng các Agent

### 📋 Schedule Agent - Quản lý Todo
```
🔹 Tạo task: "Tạo task học Python với deadline ngày mai"
🔹 Xem task: "Hiển thị tất cả task của tôi"
🔹 Cập nhật: "Đánh dấu task #1 đã hoàn thành"
🔹 Xóa task: "Xóa task #3"
```

### 📊 Analytics Agent - Phân tích hiệu suất
```
🔹 Hiệu suất: "Phân tích hiệu suất học tập 30 ngày qua"
🔹 Pattern: "Tìm giờ vàng làm việc của tôi"
🔹 Xu hướng: "Tỷ lệ hoàn thành task như thế nào?"
🔹 Khuyến nghị: "Tư vấn lịch trình học tập tối ưu"
```

### 📚 RAG Agent - Tư vấn học tập
```
🔹 Học phí: "Chi phí học ngành Công nghệ thông tin là bao nhiêu?"
🔹 Học bổng: "Có những loại học bổng nào?"
🔹 Nội quy: "Quy định về trang phục đi học"
```

### 🔍 Generic Agent - Tìm kiếm và chat
```
🔹 Tìm kiếm: "Xu hướng công nghệ AI 2025"
🔹 Tư vấn: "Lộ trình học lập trình cho người mới"
🔹 Chat: "Cách cân bằng học tập và giải trí"
```

## 🔧 Cấu hình

### Environment Variables chính

| Variable | Mô tả | Ví dụ |
|----------|--------|--------|
| `DB_URI` | Connection string PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `GOOGLE_API_KEY` | API key cho Google Gemini | `AIza...` |
| `PINECONE_API_KEY` | API key cho Pinecone vector DB | `pc-...` |
| `TAVILY_API_KEY` | API key cho Tavily search | `tvly-...` |

### Cấu hình Agent Prompts
Tất cả prompts được định nghĩa trong `src/agents/prompts.py` và có thể tùy chỉnh:
- Router prompt để điều hướng request
- Agent-specific prompts cho từng chức năng
- Summarization prompt cho context management

## 📚 Architecture Decisions

### Tại sao Multi-Agent?
- **Separation of Concerns**: Mỗi agent chuyên về một domain
- **Scalability**: Dễ dàng thêm agent mới
- **Maintainability**: Logic rõ ràng và dễ debug

### Tại sao LangGraph?
- **State Management**: Quản lý conversation state hiệu quả
- **Checkpointing**: Persistent conversation memory
- **Streaming**: Real-time response streaming
- **Tool Integration**: Native tool calling support

### Tại sao PostgreSQL?
- **ACID Compliance**: Đảm bảo data integrity
- **JSON Support**: Native JSONB cho flexible schema
- **Performance**: Excellent indexing và query optimization
- **Extensions**: Rich ecosystem của extensions

## 📄 License

Dự án này được phát hành dưới MIT License. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

**Được phát triển với bởi Syntax Error team.**
