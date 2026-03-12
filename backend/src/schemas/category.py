"""Category related Pydantic schemas"""

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=5, max_length=255)
    description: str | None = None


class CategoryCreate(CategoryBase):
    """Category creation schema"""
    pass


class CategoryResponse(CategoryBase):
    """Category response schema"""
    category_id: int

    class Config:
        from_attributes = True
