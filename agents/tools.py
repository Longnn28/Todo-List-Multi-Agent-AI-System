from langchain_core.tools import tool
from pydantic import Field, BaseModel
from geopy.geocoders import Nominatim
import requests
from datetime import datetime
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from config.database import get_db, TodoItem, SessionLocal
from config.vector_store import VectorStoreCRUD
from langchain_tavily import TavilySearch


class SearchInput(BaseModel):
    """Input for the search tool."""
    location: str = Field(description="The city to search for weather information")
    date: str = Field(description="The date for the weather forecast in YYYY-MM-DD format")

class TodoInput(BaseModel):
    """Input for todo operations."""
    title: str = Field(description="Title of the todo item")
    description: Optional[str] = Field(default=None, description="Description of the todo item")
    priority: Optional[str] = Field(default="medium", description="Priority level: low, medium, high")
    due_date: Optional[str] = Field(default=None, description="Due date in YYYY-MM-DD HH:MM format")

class TodoUpdateInput(BaseModel):
    """Input for updating todo items."""
    todo_id: int = Field(description="ID of the todo item to update")
    title: Optional[str] = Field(default=None, description="New title")
    description: Optional[str] = Field(default=None, description="New description")
    completed: Optional[bool] = Field(default=None, description="Completion status")
    priority: Optional[str] = Field(default=None, description="New priority level")
    due_date: Optional[str] = Field(default=None, description="New due date in YYYY-MM-DD HH:MM format")

class RAGInput(BaseModel):
    """Input for RAG search tool."""
    query: str = Field(description="The search query for school information")

class TavilySearchInput(BaseModel):
    """Input for Tavily search tool."""
    query: str = Field(description="The search query for web search")
    max_results: Optional[int] = Field(default=3, description="Maximum number of search results")

geolocator = Nominatim(user_agent="weather_tool")
vector_store = VectorStoreCRUD()

@tool
def get_weather(input: SearchInput) -> str:
    """Get the weather forecast for a given location and date."""
    location = input.location
    date = input.date

    location = geolocator.geocode(location)
    if location:
        try:
            lat, lon = location.latitude, location.longitude
            response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&start_date={date}&end_date={date}")
            data = response.json()
            return {time: temp for time, temp in zip(data['hourly']['time'], data['hourly']['temperature_2m'])}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Location not found"}

@tool
def rag_retrieve(input: RAGInput) -> str:
    """Retrieve relevant information from the school knowledge base."""
    try:
        import asyncio
        docs = asyncio.run(vector_store.search(input.query))
        if docs:
            context = "\n\n".join([f"Source: {doc.metadata.get('source_file', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])
            return context
        else:
            return "No relevant information found in the knowledge base."
    except Exception as e:
        return f"Error retrieving information: {str(e)}"

@tool
def tavily_search(input: TavilySearchInput) -> str:
    """Search the web using Tavily for current information."""
    try:
        tavily_tool = TavilySearch(max_results=input.max_results)
        results = tavily_tool.invoke({"query": input.query})
        
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"""
                    Result {i}:
                    Title: {result.get('title', 'N/A')}
                    URL: {result.get('url', 'N/A')}
                    Content: {result.get('content', 'N/A')[:300]}...
                    """)
            return "\n".join(formatted_results)
        else:
            return "No search results found."
    except Exception as e:
        return f"Error performing web search: {str(e)}"

@tool
def create_todo(input: TodoInput) -> str:
    """Create a new todo item."""
    try:
        db = SessionLocal()
        
        due_date = None
        if input.due_date:
            try:
                due_date = datetime.strptime(input.due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    due_date = datetime.strptime(input.due_date, "%Y-%m-%d")
                except ValueError:
                    return "Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM"
        
        todo = TodoItem(
            title=input.title,
            description=input.description,
            priority=input.priority,
            due_date=due_date
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
def get_todos() -> str:
    """Get all todo items."""
    try:
        db = SessionLocal()
        todos = db.query(TodoItem).all()
        
        if not todos:
            return "No todos found."
        
        result = "Current todos:\n"
        for todo in todos:
            status = "✅" if todo.completed else "⏰"
            due_info = f" (Due: {todo.due_date.strftime('%Y-%m-%d %H:%M')})" if todo.due_date else ""
            result += f"{status} {todo.id}. {todo.title} - {todo.priority} priority{due_info}\n"
            if todo.description:
                result += f"   Description: {todo.description}\n"
        
        return result
    
    except Exception as e:
        return f"Error retrieving todos: {str(e)}"
    finally:
        db.close()

@tool
def update_todo(input: TodoUpdateInput) -> str:
    """Update an existing todo item."""
    try:
        db = SessionLocal()
        todo = db.query(TodoItem).filter(TodoItem.id == input.todo_id).first()
        
        if not todo:
            return f"Todo with ID {input.todo_id} not found."
        
        if input.title is not None:
            todo.title = input.title
        if input.description is not None:
            todo.description = input.description
        if input.completed is not None:
            todo.completed = input.completed
        if input.priority is not None:
            todo.priority = input.priority
        if input.due_date is not None:
            try:
                todo.due_date = datetime.strptime(input.due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    todo.due_date = datetime.strptime(input.due_date, "%Y-%m-%d")
                except ValueError:
                    return "Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM"
        
        todo.updated_at = datetime.utcnow()
        db.commit()
        
        return f"Todo {input.todo_id} updated successfully."
    
    except Exception as e:
        return f"Error updating todo: {str(e)}"
    finally:
        db.close()

@tool
def delete_todo(todo_id: int) -> str:
    """Delete a todo item by ID."""
    try:
        db = SessionLocal()
        todo = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
        
        if not todo:
            return f"Todo with ID {todo_id} not found."
        
        db.delete(todo)
        db.commit()
        
        return f"Todo {todo_id} deleted successfully."
    
    except Exception as e:
        return f"Error deleting todo: {str(e)}"
    finally:
        db.close()
