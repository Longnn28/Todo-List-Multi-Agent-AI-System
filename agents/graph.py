from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, List, Annotated
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import ChatPromptTemplate
from config.llm import llm
#from langgraph.checkpoint.postgres import PostgresSaver
#from psycopg import Connection
from agents.prompts import ROUTER_PROMPT, RAG_AGENT_PROMPT, SCHEDULE_AGENT_PROMPT, GENERIC_AGENT_PROMPT, ADVISOR_AGENT_PROMPT
from agents.tools import rag_retrieve, create_todo, get_todos, update_todo, delete_todo, tavily_search, todo_analytics
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    route_decision: str
    response: str


def router_node(state: AgentState) -> AgentState:
    """Router agent to decide which agent should handle the request."""
    # Lấy user input từ message cuối cùng
    user_input = state["messages"][-1].content
    messages = state["messages"]
    
    # Tạo chat history từ tất cả messages
    chat_history = ""
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        chat_history += f"{role}: {msg.content}\n"
    
    router_prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
    router_chain = router_prompt | llm

    response = router_chain.invoke({
        "user_input": user_input,
        "chat_history": chat_history
    })
    
    # Extract the route decision from the response
    route_decision = response.content.strip().lower()
    
    # Ensure valid route decision
    if "rag_agent" in route_decision:
        route_decision = "rag_agent"
    elif "schedule_agent" in route_decision:
        route_decision = "schedule_agent"
    elif "advisor_agent" in route_decision:
        route_decision = "advisor_agent"
    elif "generic_agent" in route_decision:
        route_decision = "generic_agent"
    else:
        # Default to generic if unclear
        route_decision = "generic_agent"
    
    return {
        **state,
        "route_decision": route_decision
    }

def create_rag_agent():
    """Create RAG agent using create_react_agent."""
    tools = [rag_retrieve]
    return create_react_agent(llm, tools, prompt=RAG_AGENT_PROMPT)

def create_schedule_agent():
    """Create Schedule agent using create_react_agent."""
    tools = [create_todo, get_todos, update_todo, delete_todo]
    # Format prompt with current datetime
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_prompt = SCHEDULE_AGENT_PROMPT.format(current_datetime=current_datetime)
    return create_react_agent(llm, tools, prompt=formatted_prompt)

def create_generic_agent():
    """Create Generic agent using create_react_agent."""
    tools = [tavily_search]
    # Format prompt with current datetime
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_prompt = GENERIC_AGENT_PROMPT.format(current_datetime=current_datetime)
    return create_react_agent(llm, tools, prompt=formatted_prompt)

def create_advisor_agent():
    """Create Study Advisor agent using create_react_agent."""
    tools = [todo_analytics]
    return create_react_agent(llm, tools, prompt=ADVISOR_AGENT_PROMPT)

# Create agent instances
rag_agent = create_rag_agent()
schedule_agent = create_schedule_agent()
generic_agent = create_generic_agent()
advisor_agent = create_advisor_agent()

def rag_agent_node(state: AgentState) -> AgentState:
    """RAG agent node for school information queries."""
    # Sử dụng messages từ state để có memory
    result = rag_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def schedule_agent_node(state: AgentState) -> AgentState:
    """Schedule agent node for CRUD operations."""
    # Sử dụng messages từ state để có memory
    result = schedule_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def generic_agent_node(state: AgentState) -> AgentState:
    """Generic agent node for general queries."""
    # Sử dụng messages từ state để có memory
    result = generic_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def advisor_agent_node(state: AgentState) -> AgentState:
    """Advisor agent node for learning analytics and advice."""
    # Sử dụng messages từ state để có memory
    result = advisor_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def route_to_agent(state: AgentState) -> str:
    """Conditional routing function."""
    route_decision = state.get("route_decision", "generic_agent")
    return route_decision

# Create the graph
def create_graph() -> StateGraph:
    """Create the multi-agent workflow graph."""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("schedule_agent", schedule_agent_node)
    graph.add_node("generic_agent", generic_agent_node)
    graph.add_node("advisor_agent", advisor_agent_node)
    
    # Set entry point
    graph.set_entry_point("router")
    
    # Add conditional routing
    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "rag_agent": "rag_agent",
            "schedule_agent": "schedule_agent",
            "advisor_agent": "advisor_agent",
            "generic_agent": "generic_agent"
        }
    )
    
    # Add edges to end
    graph.add_edge("rag_agent", END)
    graph.add_edge("schedule_agent", END)
    graph.add_edge("advisor_agent", END)
    graph.add_edge("generic_agent", END)
    
    return graph.compile()

# DB_URI = os.getenv("DB_URI")

# connection_kwargs = {
#     "autocommit": True,
#     "prepare_threshold": 0,
# }

# conn = Connection.connect(DB_URI, **connection_kwargs)
# checkpointer = PostgresSaver(conn)
# #checkpointer.setup()
multi_agent_graph = create_graph()
