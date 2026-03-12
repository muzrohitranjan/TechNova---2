"""
Voice Service for Speech-to-Text and Text-to-Speech
"""
import json
import base64
from typing import Dict, Any, Optional, Callable
import openai
import io
from app.config import settings




class VoiceService:
    """Service for handling voice input/output for recipes"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.active_sessions = {}
    
    async def handle_voice_message(self, message: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Handle incoming voice message from WebSocket"""
        msg_type = message.get("type")
        
        if msg_type == "transcript":
            # User sent text transcript (from browser Web Speech API)
            return await self._handle_transcript(message.get("text", ""), websocket)
        
        elif msg_type == "audio":
            # User sent audio data (needs STT processing)
            return await self._handle_audio(message.get("audio_data", ""), websocket)
        
        elif msg_type == "command":
            # Voice command for guided cooking
            return await self._handle_command(message.get("command", ""), message.get("session_id", ""))
        
        elif msg_type == "start_recording":
            return await self._start_recording(message, websocket)
        
        elif msg_type == "stop_recording":
            return await self._stop_recording(message, websocket)
        
        elif msg_type == "start_cooking":
            return await self._start_cooking_mode(message, websocket)
        
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            }
    
    async def _handle_transcript(self, text: str, websocket) -> Dict[str, Any]:
        """Handle text transcript from speech"""
        if not text:
            return {
                "type": "error",
                "message": "No text provided"
            }
        
        # Process through AI service
        result = self.ai_service.extract_recipe_from_text(text)
        
        # Send response
        response = {
            "type": "recipe_data",
            "data": result["recipe"],
            "missing_fields": result["missing_fields"],
            "follow_up_questions": result["follow_up_questions"]
        }
        
        # If there are follow-up questions, ask the first one
        if result["follow_up_questions"]:
            response["message"] = result["follow_up_questions"][0]
            response["ask_question"] = True
        else:
            response["message"] = "I've captured all the recipe details. Would you like me to save this recipe?"
            response["ready_to_save"] = True
        
        return response
    
    async def _handle_audio(self, audio_data: str, websocket) -> Dict[str, Any]:
        """Handle audio data - convert to text (STT) with OpenAI Whisper"""
        if not audio_data:
            return {"type": "error", "message": "No audio data provided"}

        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
                # Fallback to simulated if no key
                return {
                    "type": "transcript",
                    "text": "Sample recipe from voice input (add OPENAI_API_KEY to .env for real STT)",
                    "message": "Using demo mode - add OpenAI key for real transcription"
                }
            
            # Real OpenAI Whisper
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.webm", io.BytesIO(audio_bytes), "audio/webm"),
                response_format="text",
                language="en"
            )
            
            return {
                "type": "transcript",
                "text": transcript.strip(),
                "message": f"I heard: {transcript.strip()}"
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"STT failed: {str(e)}"
            }

    
    async def _handle_command(self, command: str, session_id: str) -> Dict[str, Any]:
        """Handle voice commands for guided cooking"""
        if session_id not in self.active_sessions:
            return {
                "type": "error",
                "message": "No active cooking session. Please start cooking a recipe first."
            }
        
        session = self.active_sessions[session_id]
        recipe = session["recipe"]
        current_step = session["current_step"]
        
        # Parse command
        command_lower = command.lower().strip()
        
        if any(word in command_lower for word in ["next", "continue", "forward"]):
            intent = "next"
        elif any(word in command_lower for word in ["repeat", "again", "once more"]):
            intent = "repeat"
        elif any(word in command_lower for word in ["back", "previous"]):
            intent = "previous"
        elif any(word in command_lower for word in ["help", "what", "where"]):
            intent = "help"
        else:
            # Try to extract step number
            import re
            match = re.search(r'step\s*(\d+)', command_lower)
            if match:
                step_num = int(match.group(1))
                instructions = recipe.get("instructions", [])
                if 0 < step_num <= len(instructions):
                    session["current_step"] = step_num
                    return {
                        "type": "cooking_step",
                        "message": f"Step {step_num}: {instructions[step_num-1]['instruction']}",
                        "current_step": step_num,
                        "total_steps": len(instructions),
                        "is_complete": step_num >= len(instructions)
                    }
            
            return {
                "type": "error",
                "message": "I didn't understand. Say 'next', 'repeat', 'previous', or 'help'."
            }
        
        # Generate response using AI service
        response = self.ai_service.generate_cooking_response(
            intent, current_step, recipe
        )
        
        # Update session
        session["current_step"] = response["next_step"]
        
        return {
            "type": "cooking_step",
            "message": response["message"],
            "current_step": response["next_step"],
            "total_steps": len(recipe.get("instructions", [])),
            "is_complete": response["is_complete"]
        }
    
    async def _start_recording(self, message: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Start voice recording session"""
        session_id = message.get("session_id", "default")
        
        self.active_sessions[session_id] = {
            "type": "voice_recording",
            "recipe": {},
            "current_step": 0,
            "started_at": "now"
        }
        
        return {
            "type": "recording_started",
            "session_id": session_id,
            "message": "I'm listening. Tell me about your recipe!"
        }
    
    async def _stop_recording(self, message: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Stop voice recording session"""
        session_id = message.get("session_id", "default")
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.get("type") == "voice_recording":
                recipe = session.get("recipe", {})
                if recipe:
                    structured = self.ai_service.generate_structured_recipe(recipe)
                    return {
                        "type": "recipe_ready",
                        "recipe": structured,
                        "message": "I've processed your recipe. Would you like to save it?"
                    }
        
        return {
            "type": "recording_stopped",
            "message": "Recording stopped. What would you like to do next?"
        }
    
    async def _start_cooking_mode(self, message: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Start guided cooking mode for a recipe"""
        recipe = message.get("recipe", {})
        
        if not recipe:
            return {
                "type": "error",
                "message": "No recipe provided to start cooking."
            }
        
        # Generate session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        self.active_sessions[session_id] = {
            "type": "cooking",
            "recipe": recipe,
            "current_step": 0,
            "started_at": "now"
        }
        
        instructions = recipe.get("instructions", [])
        first_step = instructions[0] if instructions else {}
        
        return {
            "type": "cooking_started",
            "session_id": session_id,
            "message": f"Let's start cooking! {first_step.get('instruction', 'Begin with the first step.')}",
            "current_step": 1,
            "total_steps": len(instructions),
            "commands_available": ["next", "repeat", "previous", "help"]
        }
    

        """Generate TTS audio from text"""
        # In production, integrate with:
        # - ElevenLabs API
        # - Google Cloud Text-to-Speech
        # - gTTS (free alternative)
        
        # For demo, return None (browser will use Web Speech API)
        return None
    
    def cleanup_session(self, session_id: str):
        """Clean up a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

