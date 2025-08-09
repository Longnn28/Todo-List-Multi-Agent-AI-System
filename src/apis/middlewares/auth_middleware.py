from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
import jwt
from jose import JWTError
import requests
from pydantic import BaseModel, Field, EmailStr

security = HTTPBearer()

class User(BaseModel):
    user_id: int = Field("", description="User's id")
    email: EmailStr = Field("", description="User's email")
    role: str = Field("", description="User's role")

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):

    try:
        token = credentials.credentials
        if not token:
            return JSONResponse(
                content={"msg": "Authentication failed"}, status_code=401
            )
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("id")
        email = payload.get("email")
        role = payload.get("role")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token - missing user ID")
        url = "http://103.81.87.99:8080/identity/auth/introspect"
        headers = {"accept": "*/*", "Content-Type": "application/json"}
        payload = {"token": token}

        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        if not result.get("data").get("valid"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return User(user_id=user_id, email=email, role=role)
    
    except JWTError:
        return JSONResponse(content={"msg": "Authentication failed"}, status_code=401)