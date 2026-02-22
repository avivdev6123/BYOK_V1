"""
app/schemas/auth.py
-------------------
Milestone 4: Authentication request/response schemas.
"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user_id: int
    username: str
    session_token: str


class UserResponse(BaseModel):
    user_id: int
    username: str