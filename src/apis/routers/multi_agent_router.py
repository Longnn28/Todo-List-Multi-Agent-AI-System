from fastapi import APIRouter, status, Depends, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any
import json
import datetime
from uuid import uuid4
from langchain_core.messages import HumanMessage
from src.agents.graph import create_graph
from src.utils.logger import logger
from src.apis.middlewares.auth_middleware import get_current_user, User
from typing import Annotated
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.config.pool_manager import get_connection_pool
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/chatbot", tags=["AI"])

user_dependency = Annotated[User, Depends(get_current_user)]

# Remove old pool management code - now handled by pool_manager
# All pool creation logic moved to src.config.pool_manager

async def message_generator(input_graph: dict, config: dict):
    pool = await get_connection_pool()
    async with pool.connection() as conn:
        checkpointer = AsyncPostgresSaver(conn)
        # await checkpointer.setup()
        graph = create_graph()
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
        logger.info(f"Message: {stream_text}")

@router.get("/health")
async def health_check():
    """Health check endpoint to monitor database pool status"""
    try:
        pool = await get_connection_pool()
        # Test connection
        async with pool.connection() as conn:
            pass
        
        return {
            "status": "healthy",
            "database": "connected",
            "pool_stats": {
                "available": pool.get_stats().get("pool_available", "unknown"),
                "size": pool.get_stats().get("pool_size", "unknown"),
                "max_size": pool.get_stats().get("pool_max", "unknown")
            },
            "message": "Database pool is operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy", 
                "database": "disconnected",
                "error": str(e)
            }
        )

@router.post("/stream/{conversation_id}")
async def multi_agent_stream(
    #user: user_dependency, 
    conversation_id: str, 
    query: str = Form(...)):
    try:
        user = {
            "user_id": 3,
            "email": "test@example.com",
            "role": "user"
        }
        # config = {
        #     "configurable": {
        #         "thread_id": conversation_id,
        #         "user_id": user.user_id,
        #         "email": user.email,
        #         "role": user.role
        #     }
        # }

        config = {
            "configurable": {
                "thread_id": conversation_id,
                "user_id": user["user_id"],
                "email": user["email"],
                "role": user["role"]
            }
        }

        input_graph = {
            "messages": [HumanMessage(content=query)],
            "route_decision": "",
            "response": "",
            "summary": "",
            "user_id": str(user["user_id"])
        }

        return StreamingResponse(
            message_generator(
                input_graph=input_graph,
                config=config,
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Streaming error: {str(e)}"},
        )


@router.post("/create-conversation", response_model=Dict[str, Any])
async def create_conversation(user: user_dependency):
    try:
        conversation_id = str(uuid4())
        logger.info(f"Created new conversation with ID: {conversation_id} for user: {user.user_id}")

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "created_at": str(datetime.datetime.now()),
            "user_id": user.user_id,
            "message": "Created new conversation successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to create conversation: {str(e)}"},
        )


@router.post("/create-conversation-test", response_model=Dict[str, Any])
async def create_conversation_test():
    try:
        conversation_id = str(uuid4())

        mock_user = {
            "user_id": "test_user",
            "email": "test@example.com",
            "role": "user"
        }
        logger.info(f"Created new test conversation with ID: {conversation_id}")
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "created_at": str(datetime.datetime.now()),
            "user_id": mock_user["user_id"],
            "message": "Created new conversation successfully for testing"
        }
    
    except Exception as e:
        logger.error(f"Error creating test conversation: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to create test conversation: {str(e)}"},
        )