"""
AI Service for Recipe Processing using LLM
"""

from typing import Dict, Any, Optional, List


class AIService:
    """Service for AI-powered recipe processing"""
    
    # System prompt for recipe understanding
    SYSTEM_PROMPT = """You are an expert culinary assistant specializing in Indian and global cuisines. 
Your task is to:
1. Extract structured recipe data from conversational text
2. Identify missing recipe fields and generate follow-up questions
3. Structure recipes into proper JSON format

Recipe JSON Structure:
{
    "title": "string",
    "description": "string", 
    "cuisine": "string",
    "category": "string (breakfast/lunch/dinner/snacks/desserts)",
    "prep_time": "number (minutes)",
    "cook_time": "number (minutes)", 
    "servings": "number",
    "difficulty": "string (easy/medium/hard)",
    "ingredients": [{"quantity": "string", "unit": "string", "name": "string"}],
    "instructions": [{"step_number": "number", "instruction": "string"}],
    "cultural_background": "string"
}

When information is missing, ask follow-up questions to get:
- Specific ingredients and quantities
- Cooking method and steps
- Cultural significance
- Serving suggestions

Always respond in a helpful, conversational manner."""

    def __init__(self):
        self.conversation_history = []
        
    def extract_recipe_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured recipe from conversational text"""
        # For demo purposes, use rule-based extraction
        # In production, integrate with OpenAI/Anthropic API
        
        recipe_data = self._parse_conversational_recipe(text)
        
        # Check for missing fields
        missing_fields = self._identify_missing_fields(recipe_data)
        
        return {
            "recipe": recipe_data,
            "missing_fields": missing_fields,
            "follow_up_questions": self._generate_follow_questions(missing_fields)
        }
    
    def _parse_conversational_recipe(self, text: str) -> Dict[str, Any]:
        """Parse conversational text into recipe data"""
        text_lower = text.lower()
        
        # Extract recipe title (usually first sentence or key phrase)
        title = self._extract_title(text)
        
        # Extract cuisine
        cuisine = self._extract_cuisine(text_lower)
        
        # Extract category
        category = self._extract_category(text_lower)
        
        # Extract difficulty
        difficulty = self._extract_difficulty(text_lower)
        
        # Extract ingredients
        ingredients = self._extract_ingredients(text)
        
        # Extract instructions
        instructions = self._extract_instructions(text)
        
        # Extract times
        prep_time, cook_time = self._extract_times(text)
        
        # Extract servings
        servings = self._extract_servings(text)
        
        return {
            "title": title,
            "description": "",
            "cuisine": cuisine,
            "category": category,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "servings": servings,
            "difficulty": difficulty,
            "ingredients": ingredients,
            "instructions": instructions,
            "cultural_background": ""
        }
    
    def _extract_title(self, text: str) -> str:
        """Extract recipe title from text"""
        lines = text.split('\n')
        if lines:
            # First non-empty line is likely the title
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:
                    # Clean up the title
                    title = re.sub(r'^(recipe for|how to make|i want to make|my.*recipe)[:\s]*', '', line.lower())
                    return title.title()
        return "Untitled Recipe"
    
    def _extract_cuisine(self, text: str) -> str:
        """Extract cuisine type from text"""
        cuisines = {
            "south indian": "South Indian",
            "north indian": "North Indian", 
            "gujarati": "Gujarati",
            "maharashtrian": "Maharashtrian",
            "rajasthani": "Rajasthani",
            "bengali": "Bengali",
            "hyderabadi": "Hyderabadi",
            "kashmiri": "Kashmiri",
            "punjabi": "Punjabi",
            "tamil": "Tamil",
            "kerala": "Kerala",
            "italian": "Italian",
            "chinese": "Chinese",
            "mexican": "Mexican"
        }
        
        for key, value in cuisines.items():
            if key in text:
                return value
        return "Other"
    
    def _extract_category(self, text: str) -> str:
        """Extract category from text"""
        categories = {
            "breakfast": "breakfast",
            "lunch": "lunch", 
            "dinner": "dinner",
            "snack": "snacks",
            "dessert": "desserts",
            "sweets": "desserts"
        }
        
        for key, value in categories.items():
            if key in text:
                return value
        return "lunch"
    
    def _extract_difficulty(self, text: str) -> str:
        """Extract difficulty level"""
        if any(word in text for word in ["easy", "simple", "quick", "beginner"]):
            return "easy"
        elif any(word in text for word in ["hard", "difficult", "complex", "expert"]):
            return "hard"
        return "medium"
    
    def _extract_ingredients(self, text: str) -> List[Dict[str, str]]:
        """Extract ingredients from text"""
        ingredients = []
        
        # Common ingredient patterns
        patterns = [
            r'(\d+(?:\s*-\s*\d+)?)\s*(cups?|tbsp|tsp|tablespoons?|teaspoons?|oz|ounces?|lbs?|pounds?|grams?|g|kg|ml|l|pieces?|cloves?|pinch)\s+([a-zA-Z\s]+)',
            r'([a-zA-Z\s]+)\s+(\d+(?:\s*-\s*\d+)?)\s*(cups?|tbsp|tsp|pieces?|cloves?)',
            r'(\d+)\s+([a-zA-Z\s]+)'
        ]
        
        # Find ingredient-like lines
        lines = text.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            # Skip instruction lines
            if any(word in line for word in ["step", "first", "then", "next", "add", "cook", "heat", "mix"]):
                continue
                
            # Skip if it's a title or too short
            if len(line) < 5 or line.startswith('#'):
                continue
            
            # Try to extract quantity and name
            match = re.search(r'(\d+(?:\s*-\s*\d+)?)\s*(.*)', line)
            if match:
                qty = match.group(1)
                name = match.group(2).strip()
                
                # Clean up name
                name = re.sub(r'^(of\s+)', '', name)
                
                if name and len(name) > 2:
                    ingredients.append({
                        "quantity": qty,
                        "unit": "",
                        "name": name
                    })
        
        # If no ingredients found, create sample
        if not ingredients:
            ingredients = [{"quantity": "", "unit": "", "name": "See instructions"}]
            
        return ingredients[:20]  # Limit to 20 ingredients
    
    def _extract_instructions(self, text: str) -> List[Dict[str, Any]]:
        """Extract cooking instructions"""
        instructions = []
        
        lines = text.split('\n')
        step_num = 1
        
        instruction_keywords = ["step", "first", "then", "next", "add", "cook", 
                               "heat", "mix", "stir", "pour", "simmer", "boil",
                               "fry", "bake", "roast", "grind", "chop", "cut"]
        
        for line in lines:
            line = line.strip()
            line_lower = line.lower()
            
            # Check if line looks like an instruction
            if any(keyword in line_lower for keyword in instruction_keywords):
                # Clean up the instruction
                instruction = re.sub(r'^(step\s*\d+[:.]?\s*)', '', line_lower)
                instruction = re.sub(r'^(\d+[.)]\s*)', '', instruction)
                
                if len(instruction) > 5:
                    instructions.append({
                        "step_number": step_num,
                        "instruction": instruction.capitalize()
                    })
                    step_num += 1
        
        # If no instructions found, add placeholder
        if not instructions:
            instructions = [{"step_number": 1, "instruction": "Follow voice instructions"}]
            
        return instructions[:15]  # Limit to 15 steps
    
    def _extract_times(self, text: str) -> tuple:
        """Extract prep and cook times"""
        prep_time = 0
        cook_time = 0
        
        # Pattern for time extraction
        time_patterns = [
            (r'prep\s*time[:\s]*(\d+)\s*(min|minute)', 'prep'),
            (r'prepare\s*(?:for)?\s*(\d+)\s*(min|minute)', 'prep'),
            (r'cook\s*time[:\s]*(\d+)\s*(min|minute)', 'cook'),
            (r'cooking\s*(?:for)?\s*(\d+)\s*(min|minute)', 'cook'),
            (r'takes?\s*(\d+)\s*(min|minute)', 'cook')
        ]
        
        for pattern, time_type in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                minutes = int(match.group(1))
                if time_type == 'prep':
                    prep_time = minutes
                else:
                    cook_time = minutes
        
        return prep_time, cook_time
    
    def _extract_servings(self, text: str) -> int:
        """Extract number of servings"""
        patterns = [
            r'servings?[:\s]*(\d+)',
            r'serves?\s*(\d+)',
            r'for\s*(\d+)\s*(people|persons)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return 4  # Default servings
    
    def _identify_missing_fields(self, recipe: Dict[str, Any]) -> List[str]:
        """Identify missing or incomplete recipe fields"""
        missing = []
        
        if not recipe.get("title") or recipe["title"] == "Untitled Recipe":
            missing.append("title")
        if not recipe.get("description"):
            missing.append("description")
        if not recipe.get("cuisine") or recipe["cuisine"] == "Other":
            missing.append("cuisine")
        if not recipe.get("ingredients") or len(recipe["ingredients"]) < 2:
            missing.append("ingredients")
        if not recipe.get("instructions") or len(recipe["instructions"]) < 2:
            missing.append("instructions")
        if not recipe.get("cultural_background"):
            missing.append("cultural_background")
        if recipe.get("prep_time", 0) == 0:
            missing.append("prep_time")
        if recipe.get("cook_time", 0) == 0:
            missing.append("cook_time")
            
        return missing
    
    def _generate_follow_questions(self, missing_fields: List[str]) -> List[str]:
        """Generate follow-up questions for missing fields"""
        questions = []
        
        field_questions = {
            "title": "What would you like to name this recipe?",
            "description": "Can you briefly describe this dish?",
            "cuisine": "Which cuisine does this recipe belong to? (Indian, Italian, Chinese, etc.)",
            "ingredients": "What are the main ingredients needed? Please list them.",
            "instructions": "Can you describe the cooking steps?",
            "cultural_background": "What's the cultural significance or story behind this recipe?",
            "prep_time": "How long does it take to prepare the ingredients?",
            "cook_time": "How long does it take to cook?"
        }
        
        for field in missing_fields:
            if field in field_questions:
                questions.append(field_questions[field])
        
        return questions
    
    def process_follow_up_answer(self, field: str, answer: str) -> Dict[str, Any]:
        """Process user's answer to follow-up question"""
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": answer
        })
        
        return {
            "status": "received",
            "field": field,
            "message": f"Thank you! I've recorded: {answer}"
        }
    
    def generate_structured_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final structured recipe JSON"""
        # Validate and clean the recipe data
        structured = {
            "title": recipe_data.get("title", "Untitled Recipe"),
            "description": recipe_data.get("description", ""),
            "cuisine": recipe_data.get("cuisine", "Other"),
            "category": recipe_data.get("category", "lunch"),
            "prep_time": recipe_data.get("prep_time", 0),
            "cook_time": recipe_data.get("cook_time", 0),
            "servings": recipe_data.get("servings", 4),
            "difficulty": recipe_data.get("difficulty", "medium"),
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "cultural_background": recipe_data.get("cultural_background", ""),
            "is_ai_generated": True
        }
        
        return structured
    
    def generate_cooking_response(self, intent: str, current_step: int, 
                                   recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for guided cooking mode"""
        instructions = recipe.get("instructions", [])
        
        if intent == "next":
            if current_step < len(instructions):
                return {
                    "message": f"Step {current_step + 1}: {instructions[current_step]['instruction']}",
                    "next_step": current_step + 1,
                    "is_complete": current_step + 1 >= len(instructions)
                }
            else:
                return {
                    "message": "Congratulations! You've completed all the steps. Enjoy your meal!",
                    "next_step": current_step,
                    "is_complete": True
                }
                
        elif intent == "repeat":
            if current_step > 0 and current_step <= len(instructions):
                return {
                    "message": f"Step {current_step}: {instructions[current_step - 1]['instruction']}",
                    "next_step": current_step,
                    "is_complete": False
                }
            return {
                "message": "You're on the first step. Let me repeat: " + instructions[0]['instruction'],
                "next_step": 1,
                "is_complete": False
            }
            
        elif intent == "previous":
            if current_step > 1:
                return {
                    "message": f"Going back to step {current_step - 1}: {instructions[current_step - 2]['instruction']}",
                    "next_step": current_step - 1,
                    "is_complete": False
                }
            return {
                "message": "You're already at the first step!",
                "next_step": 1,
                "is_complete": False
            }
            
        elif intent == "help":
            return {
                "message": f"You're on step {current_step} of {len(instructions)}. Say 'next' to continue, 'repeat' to hear again, or 'previous' to go back.",
                "next_step": current_step,
                "is_complete": False
            }
            
        return {
            "message": "I didn't understand. Say 'next', 'repeat', 'previous', or 'help'.",
            "next_step": current_step,
            "is_complete": False
        }

