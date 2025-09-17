from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import uuid
import logging
from datetime import datetime


from app.database import get_db
from app.dependencies import get_current_user

from app.models.models import *

logger = logging.getLogger(__name__)
router = APIRouter()

# Post endpoints
from sqlalchemy import func

@router.get("/threads/", response_model=List[ThreadOut])
def get_threads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    threads = db.query(Thread).order_by(Thread.created_at.desc()).all()

    # Get counts for all threads at once
    counts = dict(
        db.query(Comment.thread_id, func.count(Comment.id))
          .group_by(Comment.thread_id)
          .all()
    )

    # Assign replies_count using the precomputed values
    for thread in threads:
        thread.replies_count = counts.get(thread.id, 0)

    return threads

@router.post("/threads/", response_model=ThreadOut)
def create_thread(thread: ThreadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # current_user is already verified by get_current_user dependency
    db_author = db.query(Author).filter(Author.email == current_user.email).first()

    if not db_author:
        # If not, create and save a new author
        db_author = Author(
            full_name=current_user.full_name,
            email=current_user.email,
            avatar=current_user.avatar
        )
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
    db_thread = Thread(title=thread.title, description=thread.content, author_id=db_author.id) # Use current_user.id
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)
    
    return db_thread

@router.put("/threads/{thread_id}", response_model=ThreadOut)
def like_thread(thread_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Fetch the thread from the correct table
    db_thread = db.query(Thread).filter(Thread.id == thread_id).first()
    
    if not db_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Increment likes count
    db_thread.likes_count += 1
    db.commit()
    db.refresh(db_thread)

    return db_thread

@router.post("/comments/", response_model=CommentOut)
def create_comment(comment: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_author = db.query(Author).filter(Author.email == current_user.email).first()

    if not db_author:
        # If not, create and save a new author
        db_author = Author(
            full_name=current_user.full_name,
            email=current_user.email,
            avatar=current_user.avatar
        )
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
    print(comment)
    db_comment = Comment(thread_id=comment.thread_id, content=comment.content, author_id=db_author.id, parent_reply_id=comment.parent_reply_id) # Use current_user.id
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment

@router.put("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post_update: PostUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.owner_id != current_user.id: # Use current_user.id for authorization check
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    
    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        owner_id=post.owner_id,
        owner=post.owner,
        created_at=post.created_at,
        updated_at=post.updated_at,
        replies_count=len(post.replies),
        reactions_count=len(post.reactions)
    )

@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.owner_id != current_user.id: # Use current_user.id for authorization check
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

# Reply endpoints
@router.get("/posts/{post_id}/replies", response_model=List[ReplyResponse])
def get_replies(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Added current_user dependency
    replies = db.query(Reply).filter(Reply.post_id == post_id).order_by(Reply.created_at.asc()).all()
    reply_responses = []
    for reply in replies:
        reply_dict = {
            "id": reply.id,
            "content": reply.content,
            "post_id": reply.post_id,
            "author_id": reply.author_id,
            "author": reply.author,
            "created_at": reply.created_at,
            "updated_at": reply.updated_at,
            "reactions_count": len(reply.reactions)
        }
        reply_responses.append(ReplyResponse(**reply_dict))
    return reply_responses

@router.post("/posts/{post_id}/replies", response_model=ReplyResponse, status_code=status.HTTP_201_CREATED) # Added status_code
def create_reply(
    post_id: int,
    reply: ReplyCreate, # This now includes parent_reply_id
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Optional: Verify parent_reply_id if provided
    if reply.parent_reply_id:
        parent_reply = db.query(Reply).filter(Reply.id == reply.parent_reply_id).first()
        if not parent_reply:
            raise HTTPException(status_code=400, detail="Parent reply not found.")

    # --- THIS IS THE CRITICAL CHANGE ---
    db_reply = Reply(
        content=reply.content,
        post_id=post_id,
        author_id=current_user.id,
        parent_reply_id=reply.parent_reply_id # <--- PASS THE PARENT ID HERE
    )
    # ------------------------------------

    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)

    # Prepare the response. You might need to eagerly load 'author' and 'referenced_reply'
    # if they are not already loaded by default for your ORM.
    # For 'referenced_reply', you would typically fetch the parent reply object if parent_reply_id exists.
    # However, your frontend's `groupReplies` function is designed to handle this nested
    # `referenced_reply` structure from a flat list, so simply returning the parent_reply_id
    # is usually enough for the backend. The frontend will then do the lookup.

    # Example of potentially needing to load author if not lazy-loaded by default
    db_reply.author # Accessing it here might trigger loading if it's a relationship

    # To include the referenced_reply in the response, you would fetch it and serialize it.
    # This is often not done by the create endpoint, as the frontend's groupReplies
    # handles the construction of `referenced_reply`. However, if your frontend
    # *needs* this immediately in the single reply response, you'd do:
    # referenced_reply_data = None
    # if db_reply.parent_reply_id:
    #     parent_db_reply = db.query(Reply).filter(Reply.id == db_reply.parent_reply_id).first()
    #     if parent_db_reply:
    #         referenced_reply_data = ReplyResponse.from_orm(parent_db_reply) # Convert to schema
    #         # Ensure referenced_reply_data also has its author loaded if needed
    #         if parent_db_reply.author:
    #             referenced_reply_data.author = UserResponse.from_orm(parent_db_reply.author)


    return ReplyResponse(
        id=db_reply.id,
        content=db_reply.content,
        post_id=db_reply.post_id,
        author_id=db_reply.author_id,
        author=UserResponse.from_orm(db_reply.author) if db_reply.author else None, # Ensure author is serialized
        created_at=db_reply.created_at,
        updated_at=db_reply.updated_at,
        reactions_count=0, # Assuming new replies start with 0 reactions
        parent_reply_id=db_reply.parent_reply_id, # <--- INCLUDE IN RESPONSE
        # referenced_reply=referenced_reply_data # Only if you decide to send this from backend
    )

@router.put("/replies/{reply_id}", response_model=ReplyResponse)
def update_reply(reply_id: int, reply_update: ReplyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    
    if reply.author_id != current_user.id: # Use current_user.id for authorization check
        raise HTTPException(status_code=403, detail="Not authorized to edit this reply")
    
    reply.content = reply_update.content
    reply.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reply)
    
    return ReplyResponse(
        id=reply.id,
        content=reply.content,
        post_id=reply.post_id,
        author_id=reply.author_id,
        author=reply.author,
        created_at=reply.created_at,
        updated_at=reply.updated_at,
        reactions_count=len(reply.reactions)
    )

@router.delete("/replies/{reply_id}")
def delete_reply(reply_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    
    if reply.author_id != current_user.id: # Use current_user.id for authorization check
        raise HTTPException(status_code=403, detail="Not authorized to delete this reply")
    
    db.delete(reply)
    db.commit()
    return {"message": "Reply deleted successfully"}

# Reaction endpoints
@router.post("/posts/{post_id}/reactions", response_model=ReactionResponse)
def create_post_reaction(post_id: int, reaction: ReactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    # Check if user already reacted to this post
    existing_reaction = db.query(Reaction).filter(
        Reaction.post_id == post_id,
        Reaction.user_id == current_user.id # Use current_user.id
    ).first()
    
    if existing_reaction:
        # Update existing reaction
        existing_reaction.type = reaction.type
        db.commit()
        db.refresh(existing_reaction)
        return ReactionResponse(
            id=existing_reaction.id,
            type=existing_reaction.type,
            user_id=existing_reaction.user_id,
            user=existing_reaction.user,
            created_at=existing_reaction.created_at
        )
    
    db_reaction = Reaction(type=reaction.type, post_id=post_id, user_id=current_user.id) # Use current_user.id
    db.add(db_reaction)
    db.commit()
    db.refresh(db_reaction)
    
    return ReactionResponse(
        id=db_reaction.id,
        type=db_reaction.type,
        user_id=db_reaction.user_id,
        user=db_reaction.user,
        created_at=db_reaction.created_at
    )

@router.delete("/posts/{post_id}/reactions")
def delete_post_reaction(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    reaction = db.query(Reaction).filter(
        Reaction.post_id == post_id,
        Reaction.user_id == current_user.id # Use current_user.id
    ).first()
    
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    
    db.delete(reaction)
    db.commit()
    return {"message": "Reaction removed successfully"}

@router.post("/replies/{reply_id}/reactions")
def create_reply_reaction(reply_id: int, reaction: ReactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Replaced user_id
    # Check if user already reacted to this reply
    existing_reaction = db.query(ReplyReaction).filter(
        ReplyReaction.reply_id == reply_id,
        ReplyReaction.user_id == current_user.id # Use current_user.id
    ).first()
    
    if existing_reaction:
        existing_reaction.type = reaction.type
        db.commit()
        db.refresh(existing_reaction) # Refresh to get updated fields if needed, though message is returned
        return {"message": "Reaction updated"} # Changed to return a consistent message
    
    db_reaction = ReplyReaction(type=reaction.type, reply_id=reply_id, user_id=current_user.id) # Use current_user.id
    db.add(db_reaction)
    db.commit()
    db.refresh(db_reaction) # Refresh to get updated fields if needed
    return {"message": "Reaction added"}