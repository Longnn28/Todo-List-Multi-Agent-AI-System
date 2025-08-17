from fastapi import APIRouter, status, Depends, Form
from fastapi.responses import JSONResponse, StreamingResponse
import json
from langchain_core.messages import HumanMessage
from src.agents.graph import create_graph
from src.apis.middlewares.auth_middleware import get_current_user, User
from typing import Annotated
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/chatbot", tags=["AI"])

user_dependency = Annotated[User, Depends(get_current_user)]

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": None
}

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            os.getenv("DB_URI"),
            min_size=5, max_size=20,
            kwargs=connection_kwargs,
            open=False
        )
        await _pool.open()
    return _pool

graph = create_graph()

async def message_generator(input_graph: dict, config: dict):
    pool = await get_pool()
    checkpointer = AsyncPostgresSaver(pool)
    # await checkpointer.setup()
    
    multi_agent_graph = graph.compile(checkpointer=checkpointer)

    stream_text = ""
    async for event in multi_agent_graph.astream_events(
        input=input_graph,
        config=config,
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream" and event["metadata"]["langgraph_node"] == "agent":
            chunk_content = event["data"]["chunk"].content
            stream_text += chunk_content

            yield json.dumps(
                {
                    "type": "message",
                    "content": stream_text,
                },
                ensure_ascii=False,
            ) + "\n\n"
    
    yield json.dumps(
        {
            "type": "final_message",
            "content": stream_text,
        },
        ensure_ascii=False,
    )

@router.post("/stream/{conversation_id}")
async def multi_agent_stream(user: user_dependency, conversation_id: str, query: str = Form(...)):
    try:
        config = {
            "configurable": {
                "thread_id": conversation_id,
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role
            }
        }

        input_graph = {
            "messages": [HumanMessage(content=query)],
            "route_decision": "",
            "response": "",
            "summary": "",
            "user_id": str(user.user_id)
        }

        return StreamingResponse(
            message_generator(
                input_graph=input_graph,
                config=config,
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Streaming error: {str(e)}"},
        )