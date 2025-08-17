from langchain_core.tools import tool
from pydantic import Field, BaseModel
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from src.config.database import TodoItem, SessionLocal
from src.config.vector_store import vector_store_crud
from langchain_tavily import TavilySearch
from src.analytics.todo_analytics import (
    analyze_productivity,
    analyze_patterns,
    analyze_completion_rate,
    analyze_workload
)
from src.utils.date_helpers import get_date_range


class TodoInput(BaseModel):
    """Input for todo operations."""
    title: str = Field(description="Title of the todo item")
    description: Optional[str] = Field(default=None, description="Description of the todo item")
    priority: Optional[str] = Field(default="medium", description="Priority level: low, medium, high")
    deadline: Optional[str] = Field(default=None, description="Deadline in YYYY-MM-DD HH:MM format")
    category: Optional[str] = Field(default="personal", description="Category of the todo : personal, work, study")
    userId: int = Field(description="User ID")

class TodoUpdateInput(BaseModel):
    """Input for updating todo items."""
    todo_id: int = Field(description="ID of the todo item to update")
    title: Optional[str] = Field(default=None, description="New title")
    description: Optional[str] = Field(default=None, description="New description")
    status: Optional[str] = Field(default=None, description="Status: pending, done, cancelled")
    priority: Optional[str] = Field(default=None, description="New priority level")
    deadline: Optional[str] = Field(default=None, description="New deadline in YYYY-MM-DD HH:MM format")
    category: Optional[str] = Field(default=None, description="Category of the todo item")
    userId: int = Field(description="User ID")

class RAGInput(BaseModel):
    """Input for RAG search tool."""
    query: str = Field(description="The search query for school information")

class TavilySearchInput(BaseModel):
    """Input for Tavily search tool."""
    query: str = Field(description="The search query for web search")
    max_results: Optional[int] = Field(default=3, description="Maximum number of search results")

class TodoAnalyticsInput(BaseModel):
    """Input for todo analytics tool."""
    analysis_type: str = Field(description="Type of analysis: 'productivity', 'patterns', 'completion_rate', 'workload'")
    days_back: Optional[int] = Field(default=30, description="Number of days to analyze")
    userId: int = Field(description="User ID")

@tool
def rag_retrieve(input: RAGInput) -> str:
    """Retrieve relevant information from the school knowledge base."""
    try:
        import asyncio
        docs = asyncio.run(vector_store_crud.search(input.query))
        if docs:
            context = "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])
            return context
        else:
            return "No relevant information found in the knowledge base."
    except Exception as e:
        return f"Error retrieving information: {str(e)}"

@tool
def tavily_search(input: TavilySearchInput) -> str:
    """Search the web using Tavily for current information."""
    try:
        tavily_tool = TavilySearch(max_results=input.max_results, time_range="day")
        tool_msg = tavily_tool.invoke({"query": input.query})
        
        if tool_msg:
            formatted_results = []
            for i, res in enumerate(tool_msg["results"], 1):
                formatted_results.append(f"""\nResult {i}:\nTitle: {res.get('title', 'N/A')}\nURL: {res.get('url', 'N/A')}\nContent: {res.get('content', 'N/A')}""")
            return "\n".join(formatted_results)
        else:
            return "No search results found."

    except Exception as e:
        return f"Error performing web search: {str(e)}"

@tool
def create_todo(input: TodoInput) -> str:
    """Create a new todo item.

    Args:
        input: TodoInput object containing todo details
        
    Returns:
        A confirmation message with the created todo's ID
    """
    try:
        db = SessionLocal()
        
        deadline_date = None
        if input.deadline:
            try:
                deadline_date = datetime.strptime(input.deadline, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    deadline_date = datetime.strptime(input.deadline, "%Y-%m-%d")
                except ValueError:
                    return "Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM"
        
        todo = TodoItem(
            title=input.title,
            description=input.description,
            priority=input.priority,
            deadline=deadline_date,
            category=input.category,
            status="pending",
            userId=input.userId
        )
        
        db.add(todo)
        db.commit()
        db.refresh(todo)
        
        return f"Todo created successfully with ID: {todo.id}"
    
    except Exception as e:
        return f"Error creating todo: {str(e)}"
    finally:
        db.close()

@tool
def get_todos(userId: int) -> str:
    """Get all todo items for a specific user from current date to future.
    
    Args:
        userId: User ID for filtering todos (required)
        
    Returns:
        A JSON string representation of the user's todos
    """
    try:
        db = SessionLocal()
        
        # Lấy ngày hiện tại và đặt giờ về 00:00:00
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Lọc todo theo userId và chỉ lấy các todo có deadline từ ngày hiện tại trở đi hoặc không có deadline
        query = db.query(TodoItem).filter(TodoItem.userId == userId,
            ((TodoItem.deadline.is_(None)) | (TodoItem.deadline >= current_date))
        )
        todos = query.all()
        
        if not todos:
            return str({"message": "No todos found", "todos": []})
        
        todos_list = []
        for todo in todos:
            todo_dict = {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "priority": todo.priority,
                "status": todo.status,
                "deadline": todo.deadline.strftime('%Y-%m-%d %H:%M') if todo.deadline else None,
                "category": todo.category,
                "userId": todo.userId
            }
            todos_list.append(todo_dict)
        
        result = {
            "message": f"Found {len(todos_list)} todos",
            "todos": todos_list
        }
        
        return str(result)
    
    except Exception as e:
        return str({"error": f"Error retrieving todos: {str(e)}", "todos": []})
    finally:
        db.close()

@tool
def update_todo(input: TodoUpdateInput) -> str:
    """Update an existing todo item with authorization check.
    
    Args:
        input: TodoUpdateInput object containing update details
        
    Returns:
        A confirmation message or error message
    """
    try:
        db = SessionLocal()
        
        query = db.query(TodoItem).filter(TodoItem.id == input.todo_id, TodoItem.userId == input.userId)
        todo = query.first()
        
        if not todo:
            return f"Todo with ID {input.todo_id} not found or you don't have permission to update it."
        
        if input.title is not None:
            todo.title = input.title
        if input.description is not None:
            todo.description = input.description
        if input.status is not None:
            todo.status = input.status
        if input.priority is not None:
            todo.priority = input.priority
        if input.category is not None:
            todo.category = input.category
        if input.deadline is not None:
            try:
                todo.deadline = datetime.strptime(input.deadline, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    todo.deadline = datetime.strptime(input.deadline, "%Y-%m-%d")
                except ValueError:
                    return "Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM"
        
        todo.updatedAt = datetime.utcnow()
        db.commit()
        
        return f"Todo {input.todo_id} updated successfully."
    
    except Exception as e:
        return f"Error updating todo: {str(e)}"
    finally:
        db.close()

@tool
def delete_todo(todo_id: int, userId: int) -> str:
    """Delete a todo item by its ID with user authorization.
    
    Args:
        todo_id: The ID of the todo item to delete
        userId: User ID for authentication (required)
        
    Returns:
        A confirmation message or error message
    """
    try:
        db = SessionLocal()
        
        query = db.query(TodoItem).filter(TodoItem.id == todo_id, TodoItem.userId == userId)
        todo = query.first()
        
        if not todo:
            return f"Todo with ID {todo_id} not found or you don't have permission to delete it."
        
        db.delete(todo)
        db.commit()
        
        return f"Todo {todo_id} deleted successfully."
    
    except Exception as e:
        return f"Error deleting todo: {str(e)}"
    finally:
        db.close()

@tool
def todo_analytics(input: TodoAnalyticsInput) -> str:
    """Analyze todo patterns and provide insights for better productivity."""
    try:
        db = SessionLocal()
        
        # Calculate date range using utils helper
        start_date, end_date = get_date_range(input.days_back)
        
        # Prepare base query with user filtering
        base_query = db.query(TodoItem).filter(TodoItem.createdAt >= start_date)
        if input.userId:
            base_query = base_query.filter(TodoItem.userId == input.userId)
        
        # Use analytics helpers from utils with user filtering
        if input.analysis_type == "productivity":
            return analyze_productivity(db, start_date, end_date, input.userId)
        elif input.analysis_type == "patterns":
            return analyze_patterns(db, start_date, end_date, input.userId)
        elif input.analysis_type == "completion_rate":
            return analyze_completion_rate(db, start_date, end_date, input.userId)
        elif input.analysis_type == "workload":
            return analyze_workload(db, start_date, end_date, input.userId)
        else:
            return "Invalid analysis type. Available types: productivity, patterns, completion_rate, workload"
    
    except Exception as e:
        return f"Error performing analytics: {str(e)}"
    finally:
        db.close()
