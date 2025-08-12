from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, RemoveMessage
from typing import TypedDict, List, Annotated
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import ChatPromptTemplate
from src.config.llm import llm
from src.agents.prompts import ROUTER_PROMPT, RAG_AGENT_PROMPT, SCHEDULE_AGENT_PROMPT, GENERIC_AGENT_PROMPT, ANALYTIC_AGENT_PROMPT, SUMMARIZE_PROMPT
from src.agents.tools import rag_retrieve, create_todo, get_todos, update_todo, delete_todo, tavily_search, todo_analytics
from datetime import datetime

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    route_decision: str
    response: str
    summary: str
    user_id: str

def should_summarize(state: AgentState) -> str:
    """Kiểm tra xem có cần tóm tắt ngữ cảnh không dựa trên số lượng tin nhắn AI."""
    ai_message_count = sum(1 for msg in state["messages"] if isinstance(msg, AIMessage))
    
    if ai_message_count >= 10:
        return "summarize"
    else:
        return "router"

def summarize_node(state: AgentState) -> AgentState:
    """Node tóm tắt ngữ cảnh cuộc hội thoại khi quá dài."""
    messages = state["messages"]
    summary = state.get("summary", "")

    # Tạo chat history từ tất cả messages
    chat_history = f"Summarized conversation:\n{summary}\n"
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        chat_history += f"{role}: {msg.content}\n"
    
    summarize_prompt = ChatPromptTemplate.from_template(SUMMARIZE_PROMPT)
    summarize_chain = summarize_prompt | llm
    
    response = summarize_chain.invoke({
        "chat_history": chat_history
    })

    # Xoá tất cả trừ 2 tin nhắn gần đây nhất
    remove_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    
    return {
        **state,
        "summary": response.content,
        "messages": remove_messages + [AIMessage(content=response.content)]
    }


def router_node(state: AgentState) -> AgentState:
    """Router agent to decide which agent should handle the request."""
    # Lấy user input từ message cuối cùng
    user_input = state["messages"][-1].content
    messages = state["messages"]
    
    # Lấy message AI cuối cùng để tạo chat history
    last_ai_message = ""
    if len(messages) >= 2:
        last_ai_message += f"Assistant: {messages[-2].content}"

    router_prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
    router_chain = router_prompt | llm

    response = router_chain.invoke({
        "user_input": user_input,
        "chat_history": last_ai_message
    })
    
    route_decision = response.content.strip().lower()
    
    if "rag_agent" in route_decision:
        route_decision = "rag_agent"
    elif "schedule_agent" in route_decision:
        route_decision = "schedule_agent"
    elif "analytic_agent" in route_decision:
        route_decision = "analytic_agent"
    elif "generic_agent" in route_decision:
        route_decision = "generic_agent"
    else:
        # Mặc định nếu không rõ
        route_decision = "generic_agent"
    
    return {
        **state,
        "route_decision": route_decision
    }

def create_rag_agent():
    """Create RAG agent using create_react_agent."""
    tools = [rag_retrieve]
    return create_react_agent(llm, tools, prompt=RAG_AGENT_PROMPT)

def create_schedule_agent(user_id=""):
    """Create Schedule agent using create_react_agent."""
    tools = [create_todo, get_todos, update_todo, delete_todo]
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_prompt = SCHEDULE_AGENT_PROMPT.format(
        current_datetime=current_datetime,
        user_id=user_id
    )
    return create_react_agent(llm, tools, prompt=formatted_prompt)

def create_generic_agent():
    """Create Generic agent using create_react_agent."""
    tools = [tavily_search]
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_prompt = GENERIC_AGENT_PROMPT.format(current_datetime=current_datetime)
    return create_react_agent(llm, tools, prompt=formatted_prompt)

def create_analytic_agent(user_id=""):
    """Create Analytic agent using create_react_agent."""
    tools = [todo_analytics]
    formatted_prompt = ANALYTIC_AGENT_PROMPT.format(user_id=user_id)
    return create_react_agent(llm, tools, prompt=formatted_prompt)

# Create agent instances
rag_agent = create_rag_agent()
generic_agent = create_generic_agent()

def rag_agent_node(state: AgentState) -> AgentState:
    """RAG agent node for school information queries."""
    result = rag_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def schedule_agent_node(state: AgentState) -> AgentState:
    """Schedule agent node for CRUD operations."""
    user_id = state["user_id"]
    
    # Tạo schedule agent với user_id
    schedule_agent = create_schedule_agent(user_id=user_id)
    
    result = schedule_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def generic_agent_node(state: AgentState) -> AgentState:
    """Generic agent node for general queries."""
    result = generic_agent.invoke({"messages": state["messages"]})
    
    final_message = result["messages"][-1].content if result["messages"] else "No response generated."
    
    return {
        **state,
        "response": final_message,
        "messages": [AIMessage(content=final_message)]
    }

def analytic_agent_node(state: AgentState) -> AgentState:
    """Analytic agent node for learning analytics and advice."""
    user_id = state["user_id"]
    
    # Tạo analytic agent với user_id
    analytic_agent = create_analytic_agent(user_id=user_id)
    
    result = analytic_agent.invoke({"messages": state["messages"]})
    
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
    graph.add_node("summarize_check", lambda state: state)  # Node kiểm tra
    graph.add_node("summarize", summarize_node)
    graph.add_node("router", router_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("schedule_agent", schedule_agent_node)
    graph.add_node("generic_agent", generic_agent_node)
    graph.add_node("analytic_agent", analytic_agent_node)
    
    graph.set_entry_point("summarize_check")
    
    graph.add_conditional_edges(
        "summarize_check",
        should_summarize,
        {
            "summarize": "summarize",
            "router": "router"
        }
    )
    
    graph.add_edge("summarize", "router")
    
    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "rag_agent": "rag_agent",
            "schedule_agent": "schedule_agent",
            "analytic_agent": "analytic_agent",
            "generic_agent": "generic_agent"
        }
    )
    
    # Add edges to end
    graph.add_edge("rag_agent", END)
    graph.add_edge("schedule_agent", END)
    graph.add_edge("analytic_agent", END)
    graph.add_edge("generic_agent", END)
    
    return graph
