"""
Voice Routes - WebSocket endpoints for real-time voice interaction
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any
import json

from app.services.voice_service import VoiceService
from app.services.ai_service import AIService
from app.services.pdf_service import PDFService
from app.utils.security import get_current_active_user
from app.schemas.voice_schema import (
    VoiceMessage, 
    VoiceResponse, 
    RecipeStructuredData,
    RecipeBookRequest,
    RecipeBookResponse
)

router = APIRouter(prefix="/api/voice", tags=["Voice"])


class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()
voice_service = VoiceService()


@router.websocket("/ws")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time voice conversation"""
    client_id = None
    
    try:
        # First message should contain auth token
        auth_message = await websocket.receive_json()
        
        # Check authentication
        token = auth_message.get("token")
        if not token:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication required"
            })
            await websocket.close()
            return
        
        # Accept connection
        await websocket.accept()
        client_id = f"user_{id(websocket)}"
        manager.connect(websocket, client_id)
        
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to voice service"
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_json()
            response = await voice_service.handle_voice_message(data, websocket)
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        if client_id:
            manager.disconnect(client_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Error: {str(e)}"
        })


@router.post("/transcribe")
async def transcribe_voice(
    message: VoiceMessage,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Process voice transcript and extract recipe"""
    try:
        result = await voice_service._handle_transcript(message.text, None)
        return result
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error processing transcript: {str(e)}"
        }


@router.post("/command")
async def handle_voice_command(
    command: str,
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Handle voice command for guided cooking"""
    try:
        result = await voice_service._handle_command(command, session_id)
        return result
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error processing command: {str(e)}"
        }


@router.post("/cooking/start")
async def start_cooking_mode(
    recipe_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Start guided cooking mode"""
    from app.services.recipe_service import RecipeService
    
    try:
        recipe_service = RecipeService()
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            return {
                "type": "error",
                "message": "Recipe not found"
            }
        
        # Start cooking session
        message = {"recipe": recipe}
        result = await voice_service._start_cooking_mode(message, None)
        
        return result
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error starting cooking mode: {str(e)}"
        }


# ============== PDF Routes ==============

@router.post("/pdf/recipe/{recipe_id}")
async def generate_recipe_pdf(
    recipe_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Generate PDF for a single recipe"""
    from app.services.recipe_service import RecipeService
    
    try:
        recipe_service = RecipeService()
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            return {
                "type": "error",
                "message": "Recipe not found"
            }
        
        # Check access
        is_owner = recipe["user_id"] == current_user["id"]
        is_admin = current_user.get("role") == "admin"
        
        if not recipe.get("is_public", True) and not is_owner and not is_admin:
            return {
                "type": "error",
                "message": "Not authorized to generate PDF for this recipe"
            }
        
        # Generate PDF
        pdf_content = PDFService.generate_recipe_pdf(recipe)
        
        return {
            "type": "pdf_ready",
            "recipe_title": recipe.get("title"),
            "pdf_content": pdf_content.decode('utf-8') if pdf_content else ""
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error generating PDF: {str(e)}"
        }


@router.post("/pdf/cooking-guide/{recipe_id}")
async def generate_cooking_guide_pdf(
    recipe_id: str,
    current_step: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Generate cooking guide PDF"""
    from app.services.recipe_service import RecipeService
    
    try:
        recipe_service = RecipeService()
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            return {
                "type": "error",
                "message": "Recipe not found"
            }
        
        pdf_content = PDFService.generate_cooking_guide_pdf(recipe, current_step)
        
        return {
            "type": "pdf_ready",
            "recipe_title": recipe.get("title"),
            "pdf_content": pdf_content.decode('utf-8') if pdf_content else ""
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error generating cooking guide: {str(e)}"
        }


# ============== Recipe Book Routes ==============

@router.post("/recipe-book/create")
async def create_recipe_book(
    request: RecipeBookRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Create a recipe book from selected recipes"""
    from app.services.recipe_service import RecipeService
    
    try:
        recipe_service = RecipeService()
        recipes = []
        
        for recipe_id in request.recipe_ids:
            recipe = recipe_service.get_recipe_by_id(recipe_id)
            if recipe:
                # Check access
                is_owner = recipe["user_id"] == current_user["id"]
                is_admin = current_user.get("role") == "admin"
                
                if recipe.get("is_public", True) or is_owner or is_admin:
                    recipes.append(recipe)
        
        if not recipes:
            return {
                "type": "error",
                "message": "No valid recipes found"
            }
        
        # Generate PDF
        pdf_content = PDFService.generate_recipe_book_pdf(
            recipes, 
            request.title or "My Recipe Book"
        )
        
        return {
            "type": "recipe_book_ready",
            "title": request.title,
            "total_recipes": len(recipes),
            "pdf_content": pdf_content.decode('utf-8') if pdf_content else ""
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error creating recipe book: {str(e)}"
        }


# ============== AI Processing Routes ==============

@router.post("/ai/process-recipe")
async def process_recipe_with_ai(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Process text through AI to extract recipe structure"""
    try:
        ai_service = AIService()
        result = ai_service.extract_recipe_from_text(text)
        
        return {
            "type": "recipe_processed",
            "data": result
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error processing recipe: {str(e)}"
        }


@router.post("/ai/generate-recipe")
async def generate_final_recipe(
    recipe_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Generate final structured recipe JSON"""
    try:
        ai_service = AIService()
        structured = ai_service.generate_structured_recipe(recipe_data)
        
        return {
            "type": "recipe_generated",
            "recipe": structured
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error generating recipe: {str(e)}"
        }


@router.post("/ai/follow-up")
async def process_follow_up(
    field: str,
    answer: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Process user's answer to follow-up question"""
    try:
        ai_service = AIService()
        result = ai_service.process_follow_up_answer(field, answer)
        
        return {
            "type": "follow_up_processed",
            "data": result
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error processing follow-up: {str(e)}"
        }

