from src.agents.graph import multi_agent_graph
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "2"}}

current_state = {
    "messages": [],
    "route_decision": "",
    "response": "",
    "summary": ""
}
async def main():
    while True:

        user_input = input("Enter your query: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        current_state["messages"].append(HumanMessage(content=user_input))
        async for event in multi_agent_graph.astream_events(current_state, config, version="v2"):
            if event["event"] == "on_chat_model_stream" and event["metadata"]["langgraph_node"] == "agent":
                print(event["data"]["chunk"].content, end="", flush=True)
        print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())