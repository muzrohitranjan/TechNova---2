"""
PDF Generation Service for Recipes
"""
import io
from typing import Dict, Any, List
from datetime import datetime


class PDFService:
    """Service for generating PDF documents for recipes"""
    
    @staticmethod
    def generate_recipe_pdf(recipe: Dict[str, Any]) -> bytes:
        """Generate PDF for a single recipe"""
        # Create PDF content as HTML
        html_content = PDFService._create_recipe_html(recipe)
        
        # Return as bytes (in production, use weasyprint or similar)
        # For now, return HTML that can be converted
        return html_content.encode('utf-8')
    
    @staticmethod
    def _create_recipe_html(recipe: Dict[str, Any]) -> str:
        """Create HTML representation of recipe for PDF"""
        ingredients = recipe.get('ingredients', [])
        instructions = recipe.get('instructions', [])
        
        ingredients_html = ""
        for ing in ingredients:
            qty = ing.get('quantity', '')
            unit = ing.get('unit', '')
            name = ing.get('name', '')
            ingredients_html += f"<li>{qty} {unit} {name}</li>\n"
        
        instructions_html = ""
        for inst in instructions:
            step = inst.get('step_number', '')
            text = inst.get('instruction', '')
            instructions_html += f"<li><strong>Step {step}:</strong> {text}</li>\n"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{recipe.get('title', 'Recipe')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #d35400; border-bottom: 2px solid #d35400; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        .meta {{ color: #7f8c8d; margin-bottom: 20px; }}
        .ingredients, .instructions {{ margin-left: 20px; }}
        .ingredients li, .instructions li {{ margin-bottom: 10px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>{recipe.get('title', 'Untitled Recipe')}</h1>
    <p class="meta">
        Cuisine: {recipe.get('cuisine', 'N/A')} | 
        Category: {recipe.get('category', 'N/A')} | 
        Difficulty: {recipe.get('difficulty', 'N/A')}
    </p>
    <p class="meta">
        Prep Time: {recipe.get('prep_time', 0)} min | 
        Cook Time: {recipe.get('cook_time', 0)} min | 
        Servings: {recipe.get('servings', 4)}
    </p>
    
    <h2>Description</h2>
    <p>{recipe.get('description', 'No description available.')}</p>
    
    <h2>Ingredients</h2>
    <ul class="ingredients">
        {ingredients_html}
    </ul>
    
    <h2>Instructions</h2>
    <ol class="instructions">
        {instructions_html}
    </ol>
    
    {f"<h2>Cultural Background</h2><p>{recipe.get('cultural_background', '')}</p>" if recipe.get('cultural_background') else ""}
    
    <div class="footer">
        <p>Generated from Tech Nova - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def generate_recipe_book_pdf(recipes: List[Dict[str, Any]], title: str = "Recipe Book") -> bytes:
        """Generate PDF for a collection of recipes (recipe book)"""
        recipes_html = ""
        
        for idx, recipe in enumerate(recipes, 1):
            ingredients = recipe.get('ingredients', [])
            instructions = recipe.get('instructions', [])
            
            ingredients_html = ""
            for ing in ingredients:
                qty = ing.get('quantity', '')
                unit = ing.get('unit', '')
                name = ing.get('name', '')
                ingredients_html += f"<li>{qty} {unit} {name}</li>\n"
            
            instructions_html = ""
            for inst in instructions:
                step = inst.get('step_number', '')
                text = inst.get('instruction', '')
                instructions_html += f"<li><strong>Step {step}:</strong> {text}</li>\n"
            
            recipes_html += f"""
            <div class="recipe">
                <h2>{idx}. {recipe.get('title', 'Untitled Recipe')}</h2>
                <p class="meta">
                    Cuisine: {recipe.get('cuisine', 'N/A')} | 
                    Category: {recipe.get('category', 'N/A')} | 
                    Difficulty: {recipe.get('difficulty', 'N/A')} |
                    Prep: {recipe.get('prep_time', 0)}min | 
                    Cook: {recipe.get('cook_time', 0)}min
                </p>
                <p>{recipe.get('description', '')}</p>
                
                <h3>Ingredients</h3>
                <ul>{ingredients_html}</ul>
                
                <h3>Instructions</h3>
                <ol>{instructions_html}</ol>
                
                {f"<h3>Cultural Background</h3><p>{recipe.get('cultural_background', '')}</p>" if recipe.get('cultural_background') else ""}
            </div>
            <hr>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #d35400; text-align: center; }}
        .recipe {{ margin-bottom: 40px; page-break-inside: avoid; }}
        h2 {{ color: #2c3e50; margin-top: 20px; }}
        h3 {{ color: #34495e; }}
        .meta {{ color: #7f8c8d; font-size: 14px; }}
        ul, ol {{ margin-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        hr {{ border: none; border-top: 1px solid #ccc; margin: 30px 0; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p style="text-align: center;">Compiled on {datetime.now().strftime('%Y-%m-%d')}</p>
    <p style="text-align: center;">Total Recipes: {len(recipes)}</p>
    
    {recipes_html}
    
    <div class="footer">
        <p>Generated from Tech Nova</p>
    </div>
</body>
</html>
"""
        return html.encode('utf-8')
    
    @staticmethod
    def generate_cooking_guide_pdf(recipe: Dict[str, Any], current_step: int = 0) -> bytes:
        """Generate PDF for guided cooking mode"""
        instructions = recipe.get('instructions', [])
        
        # Get remaining steps
        remaining_steps = instructions[current_step:] if current_step < len(instructions) else []
        
        steps_html = ""
        for inst in remaining_steps:
            step = inst.get('step_number', '')
            text = inst.get('instruction', '')
            steps_html += f"""
            <div class="step">
                <h3>Step {step}</h3>
                <p>{text}</p>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cooking Guide - {recipe.get('title', 'Recipe')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; }}
        h1 {{ color: #27ae60; }}
        .step {{ background: #f8f9fa; padding: 15px; margin-bottom: 15px; border-left: 4px solid #27ae60; }}
        .step h3 {{ color: #2c3e50; margin-top: 0; }}
        .progress {{ color: #7f8c8d; margin-bottom: 20px; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>🍳 Cooking Guide</h1>
    <h2>{recipe.get('title', 'Recipe')}</h2>
    <p class="progress">Starting from step {current_step + 1} of {len(instructions)}</p>
    
    {steps_html}
    
    <div class="footer">
        <p>Generated from Tech Nova - Good luck!</p>
    </div>
</body>
</html>
"""
        return html.encode('utf-8')

