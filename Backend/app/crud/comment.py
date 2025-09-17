# crud/comment.py - Improved version with better error handling
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from typing import List, Optional
import uuid
import logging

from app.models.comment import Comment
from app.schemas.comment import CommentCreate

logger = logging.getLogger(__name__)

def get_comments(db: Session) -> List[Comment]:
    """Get all top-level comments with their replies."""
    try:
        return db.query(Comment).filter(
            Comment.parent_id.is_(None)
        ).options(
            selectinload(Comment.replies),
            selectinload(Comment.owner)
        ).order_by(desc(Comment.timestamp)).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching comments: {e}")
        raise

def get_comment_by_id(db: Session, comment_id: uuid.UUID) -> Optional[Comment]:
    """Get a comment by its ID."""
    try:
        return db.query(Comment).options(
            selectinload(Comment.replies),
            selectinload(Comment.owner)
        ).filter(Comment.id == comment_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching comment {comment_id}: {e}")
        raise

def create_comment(db: Session, comment: CommentCreate, user_id: int) -> Comment:
    """Create a new comment or reply."""
    try:
        # Create the comment object
        db_comment = Comment(
            text=comment.text,
            user_id=user_id,
            parent_id=comment.parent_id
        )
        
        # Add and flush to get the ID
        db.add(db_comment)
        db.flush()  # This assigns the ID without committing
        
        # Refresh to load relationships
        db.refresh(db_comment)
        
        # Commit the transaction
        db.commit()
        
        # Load the comment with all relationships
        return db.query(Comment).options(
            selectinload(Comment.owner),
            selectinload(Comment.replies)
        ).filter(Comment.id == db_comment.id).first()
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating comment: {e}")
        raise

def delete_comment(db: Session, comment_id: uuid.UUID) -> bool:
    """Delete a comment and all its replies."""
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return False
        
        db.delete(comment)
        db.commit()
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting comment {comment_id}: {e}")
        raise

def like_comment(db: Session, comment_id: uuid.UUID) -> Optional[Comment]:
    """Increment the like count for a comment."""
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return None
        
        comment.likes += 1
        db.commit()
        
        # Return the updated comment with relationships
        return db.query(Comment).options(
            selectinload(Comment.owner),
            selectinload(Comment.replies)
        ).filter(Comment.id == comment_id).first()
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error liking comment {comment_id}: {e}")
        raise