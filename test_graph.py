from agents.graph import multi_agent_graph
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "2"}}

current_state = {
    "messages": [],
    "route_decision": "",
    "user_input": "",
    "response": ""
}
def main():
    while True: 
        
        user_input = input("Enter your query: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        current_state["messages"].append(HumanMessage(content=user_input))
        for chunk in multi_agent_graph.stream(current_state, config, stream_mode="values"):
            chunk['messages'][-1].pretty_print()
        

if __name__ == "__main__":
    # import asyncio
    # asyncio.run(main())
    main()