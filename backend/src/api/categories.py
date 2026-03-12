"""Category management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from src.database import get_db
from src.models.category import Category

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryCreateRequest(BaseModel):
    """Request schema for creating a category"""
    category_name: str
    description: str = None
    parent_category: str = None


class CategoryUpdateRequest(BaseModel):
    """Request schema for updating a category"""
    category_name: str = None
    description: str = None
    parent_category: str = None


@router.get("", response_model=dict)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """
    List all transaction categories.
    
    Query Parameters:
    - skip: Number of results to skip (pagination)
    - limit: Number of results to return (max 500)
    
    Returns:
        - total: Total categories
        - count: Number of categories in this page
        - categories: List of category objects
    """
    try:
        query = db.query(Category)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        categories = query.order_by(
            Category.category_name
        ).offset(skip).limit(limit).all()
        
        # Convert to response format
        category_items = [
            {
                "category_id": c.category_id,
                "category_name": c.category_name,
                "description": c.description,
                "parent_category": c.parent_category,
                "created_at": c.created_at.isoformat() if hasattr(c, 'created_at') else None,
            }
            for c in categories
        ]
        
        return {
            "status": "success",
            "total": total,
            "count": len(category_items),
            "skip": skip,
            "limit": limit,
            "categories": category_items
        }
        
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@router.get("/{category_id}", response_model=dict)
async def get_category_detail(
    category_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific category.
    
    Returns:
        - category_id: Category ID
        - category_name: Category name
        - description: Category description
        - parent_category: Parent category if any
        - created_at: Creation timestamp
    """
    try:
        category = db.query(Category).filter(
            Category.category_id == category_id
        ).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return {
            "status": "success",
            "category_id": category.category_id,
            "category_name": category.category_name,
            "description": category.description,
            "parent_category": category.parent_category,
            "created_at": category.created_at.isoformat() if hasattr(category, 'created_at') else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get category: {str(e)}")


@router.post("", response_model=dict)
async def create_category(
    category_data: CategoryCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a new transaction category.
    
    Returns:
        - category_id: New category ID
        - category_name: Category name
        - message: Success message
    """
    try:
        # Check if category already exists
        existing = db.query(Category).filter(
            Category.category_name == category_data.category_name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Category already exists")
        
        # Create new category
        new_category = Category(
            category_name=category_data.category_name,
            description=category_data.description,
            parent_category=category_data.parent_category
        )
        
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        
        logger.info(f"Category created: {new_category.category_name}")
        
        return {
            "status": "success",
            "category_id": new_category.category_id,
            "category_name": new_category.category_name,
            "description": new_category.description,
            "parent_category": new_category.parent_category,
            "message": f"Category '{category_data.category_name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating category: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")


@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: str,
    category_data: CategoryUpdateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Update category information.
    
    Returns:
        - category_id: Category ID
        - category_name: Updated name
        - message: Success message
    """
    try:
        category = db.query(Category).filter(
            Category.category_id == category_id
        ).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        changes = {}
        
        # Update category name if provided
        if category_data.category_name and category_data.category_name != category.category_name:
            # Check if new name already exists
            existing = db.query(Category).filter(
                Category.category_name == category_data.category_name,
                Category.category_id != category_id
            ).first()
            
            if existing:
                raise HTTPException(status_code=400, detail="Category name already exists")
            
            changes["category_name"] = category_data.category_name
            category.category_name = category_data.category_name
        
        # Update description if provided
        if category_data.description is not None:
            changes["description"] = category_data.description
            category.description = category_data.description
        
        # Update parent category if provided
        if category_data.parent_category is not None:
            changes["parent_category"] = category_data.parent_category
            category.parent_category = category_data.parent_category
        
        db.commit()
        db.refresh(category)
        
        logger.info(f"Category updated: {category.category_name} - Changes: {changes}")
        
        return {
            "status": "success",
            "category_id": category.category_id,
            "category_name": category.category_name,
            "description": category.description,
            "parent_category": category.parent_category,
            "message": f"Category '{category.category_name}' updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating category: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")
