"""
Voice API Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class VoiceMessage(BaseModel):
    """Incoming voice message"""
    type: str
    text: Optional[str] = None
    audio_data: Optional[str] = None
    command: Optional[str] = None
    session_id: Optional[str] = "default"
    recipe: Optional[Dict[str, Any]] = None


class VoiceResponse(BaseModel):
    """Voice API response"""
    type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class RecipeStructuredData(BaseModel):
    """Structured recipe data from AI"""
    title: Optional[str] = None
    description: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    prep_time: Optional[int] = 0
    cook_time: Optional[int] = 0
    servings: Optional[int] = 4
    difficulty: Optional[str] = "medium"
    ingredients: Optional[List[Dict[str, str]]] = []
    instructions: Optional[List[Dict[str, Any]]] = []
    cultural_background: Optional[str] = ""


class CookingSession(BaseModel):
    """Cooking session data"""
    recipe_id: str
    current_step: int = 0
    is_active: bool = True
    saved_progress: Optional[Dict[str, Any]] = None


class RecipeBookRequest(BaseModel):
    """Request to compile recipe book"""
    recipe_ids: List[str]
    title: str = "My Recipe Book"
    author: Optional[str] = None


class RecipeBookResponse(BaseModel):
    """Recipe book response"""
    title: str
    recipes: List[Dict[str, Any]]
    total_recipes: int
    pdf_content: Optional[bytes] = None

