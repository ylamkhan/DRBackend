# models.py
from sqlalchemy import Column, Integer, String, LargeBinary
from app.database import Base
from pydantic import BaseModel, EmailStr, validator,Field
from typing import List, Optional
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os

# IMPORTANT: Use the web-accessible URL path, not the file system path
# This will be served by FastAPI at http://127.0.0.1:8000/static/avatars/default.svg
# Assuming your backend serves from http://127.0.0.1:8000
DEFAULT_AVATAR_WEB_PATH = "/static/avatars/default.svg"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    # Use the web path as the default
    avatar = Column(String, default=DEFAULT_AVATAR_WEB_PATH)
    theme = Column(String, default='dark')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    posts = relationship("Post", back_populates="owner")
    replies = relationship("Reply", back_populates="author")
    reactions = relationship("Reaction", back_populates="user")

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    avatar = Column(String, nullable=True)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reactions_count = Column(Integer, default=0)
    user_reacted = Column(Boolean, default=False)
    parent_reply_id = Column(Integer, nullable=True)  # Assuming replies are nested via comment ID
    edited = Column(Boolean, default=False)
    thread_id = Column(Integer, ForeignKey("threads.id"))

    author = relationship("Author", backref="comments")
# --- Main model ---

class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    author_id = Column(Integer, ForeignKey("authors.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    replies_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_trending = Column(Boolean, default=False)

    author = relationship("Author", backref="threads")
    comments = relationship("Comment", backref="thread")

class AuthorOut(BaseModel):
    id: int
    full_name: str
    class Config:
        from_attributes = True

class CommentOut(BaseModel):
    id: int
    author_id: int
    content: str
    created_at: datetime
    reactions_count: int
    user_reacted: bool
    parent_reply_id: Optional[int] = None
    edited: bool
    author: AuthorOut
    class Config:
        from_attributes = True

class ThreadOut(BaseModel):
    id: int
    title: str
    description: str
    author_id: int
    created_at: datetime
    replies_count: int
    likes_count: int
    views_count: int
    last_activity: datetime
    is_trending: bool
    author: AuthorOut
    comments: List[CommentOut]
    class Config:
        from_attributes = True

class ThreadCreate(BaseModel):
    title: str
    content: str

class CommentCreate(BaseModel):
    content: str
    thread_id: int
    parent_reply_id: Optional[int] = None

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="posts")
    replies = relationship("Reply", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")


class Reply(Base):
    __tablename__ = "replies"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    post_id = Column(Integer, ForeignKey("posts.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    parent_reply_id = Column(Integer, ForeignKey("replies.id"), nullable=True)  # <--- New field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="replies")
    author = relationship("User", back_populates="replies")
    reactions = relationship("ReplyReaction", back_populates="reply", cascade="all, delete-orphan")

    parent = relationship("Reply", remote_side=[id], backref="children", uselist=False)  # <--- Self relationship
   
class Reaction(Base):
    __tablename__ = "reactions"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # like, love, laugh, angry, etc.
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="reactions")
    user = relationship("User", back_populates="reactions")

class ReplyReaction(Base):
    __tablename__ = "reply_reactions"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    reply_id = Column(Integer, ForeignKey("replies.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    reply = relationship("Reply", back_populates="reactions")


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    title: str
    content: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    owner: UserResponse
    created_at: datetime
    updated_at: datetime
    replies_count: int = 0
    reactions_count: int = 0
    
    class Config:
        from_attributes = True

class ReplyCreate(BaseModel):
    content: str
    parent_reply_id: Optional[int] = None

class ReplyUpdate(BaseModel):
    content: str

class ReplyResponse(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int
    author: UserResponse
    parent_reply_id: Optional[int] = None  # <--- to identify nested replies
    created_at: datetime
    updated_at: datetime
    reactions_count: int = 0

    class Config:
        from_attributes = True

class ReactionCreate(BaseModel):
    type: str

class ReactionResponse(BaseModel):
    id: int
    type: str
    user_id: int
    user: UserResponse
    created_at: datetime
    
    class Config:
        from_attributes = True


# Pydantic models for request validation
class UpdateUserInfoRequest(BaseModel):
    full_name: str
    email: EmailStr
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Full name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip()

class UpdateUserInfoResponse(BaseModel):
    message: str
    user: dict

class DeleteAccountResponse(BaseModel):
    message: str
    deleted_user_email: str

# Pydantic model for updating theme
class ThemeUpdate(BaseModel):
    theme: str





