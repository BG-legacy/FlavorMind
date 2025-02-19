from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import json
import os
import subprocess
import traceback
from threading import Lock
from pathlib import Path
import logging
from fastapi.staticfiles import StaticFiles
import pandas as pd

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FlavorMind API",
    description="AI-Powered Recipe Generation API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecipeRequest(BaseModel):
    preference: str = Field(..., description="User's recipe preference or craving")
    dietary_restrictions: Optional[List[str]] = Field(
        default=None,
        description="List of dietary restrictions (e.g., vegetarian, gluten-free)"
    )
    budget_preference: Optional[str] = Field(
        default=None,
        description="Preferred budget category: budget-friendly, moderate, or premium"
    )

class Ingredient(BaseModel):
    quantity: str = Field(..., description="Amount of ingredient needed")
    unit: str = Field(default="", description="Unit of measurement")
    item: str = Field(..., description="Name of ingredient and preparation instructions")

class RecipeDetails(BaseModel):
    ingredients: List[Ingredient]
    instructions: List[str]
    tips: Optional[List[str]] = Field(default=[], description="Cooking tips and nutritional information")
    equipment: Optional[List[str]] = Field(default=[], description="Required kitchen equipment")
    nutritional_info: Optional[List[str]] = Field(default=[], description="USDA nutritional information")

class RecipeResponse(BaseModel):
    recipe_name: str
    recommendation: str
    budget_category: str = "moderate"
    difficulty: str = "medium"
    details: RecipeDetails
    error: Optional[str] = None

# Load recipe dataset
try:
    csv_path = Path(__file__).parent / 'ai' / 'Food Ingredients and Recipe Dataset with Image Name Mapping.csv'
    recipe_df = pd.read_csv(csv_path)
    logger.info(f"Successfully loaded {len(recipe_df)} recipes from dataset")
except Exception as e:
    logger.error(f"Failed to load recipe dataset: {e}")
    recipe_df = None

async def run_python_script(data: dict) -> Dict[str, Any]:
    """Execute the recipe generation script with the provided data."""
    try:
        if recipe_df is None:
            raise Exception("Recipe dataset not available")

        script_path = Path(__file__).parent / 'ai' / 'generateRecipe.py'
        logger.info(f"Executing recipe generator: {script_path}")
        
        # Ensure USDA cache directory exists
        usda_cache_dir = Path(__file__).parent / 'cache' / 'usda'
        usda_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced environment variables
        env = {
            **os.environ,
            'PYTHONPATH': str(Path(__file__).parent),
            'OLLAMA_HOST': os.getenv('OLLAMA_HOST', 'http://34.173.253.123:11434'),
            'PYTHONUNBUFFERED': '1',
            'RECIPE_CSV_PATH': str(csv_path),
            'USDA_CACHE_DIR': str(usda_cache_dir),
            'USDA_API_KEY': os.getenv('USDA_API_KEY', 'ggNrcwGzbKlQ5siiy0DIqG1LhVXSvghkLZ3hnSVn')
        }
        
        if not script_path.exists():
            raise FileNotFoundError(f"Recipe generator not found at: {script_path}")
            
        process = subprocess.Popen(
            ['python3', str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(Path(__file__).parent)
        )

        stdout, stderr = process.communicate(input=json.dumps(data))

        if process.returncode != 0:
            logger.error(f"Recipe generation failed: {stderr}")
            return {
                "error": "Recipe generation failed",
                "details": f"Error: {stderr}"
            }

        try:
            result = json.loads(stdout)
            
            # Process ingredients through our parser
            if isinstance(result.get("details", {}).get("ingredients"), list):
                ingredients_raw = result["details"]["ingredients"]
                
                # Ensure ingredients are properly formatted
                formatted_ingredients = []
                for ing in ingredients_raw:
                    if isinstance(ing, dict):
                        formatted_ingredients.append({
                            "quantity": str(ing.get("quantity", "as needed")),
                            "unit": str(ing.get("unit", "")),
                            "item": str(ing.get("item", "")).strip()
                        })
                    else:
                        # Handle string ingredients by parsing them
                        parts = str(ing).split(" ", 2)
                        formatted_ingredients.append({
                            "quantity": parts[0] if len(parts) > 0 else "as needed",
                            "unit": parts[1] if len(parts) > 1 else "",
                            "item": parts[2] if len(parts) > 2 else str(ing)
                        })
                
                result["details"]["ingredients"] = formatted_ingredients

            formatted_result = {
                "recipe_name": result.get("recipe_name", "Custom Recipe"),
                "recommendation": result.get("recommendation", "A delicious recipe just for you!"),
                "budget_category": result.get("budget_category", "moderate"),
                "difficulty": result.get("difficulty", "medium"),
                "details": {
                    "ingredients": result.get("details", {}).get("ingredients", []),
                    "instructions": [
                        str(instruction) 
                        for instruction in result.get("details", {}).get("instructions", [])
                    ],
                    "tips": [
                        str(tip) 
                        for tip in result.get("details", {}).get("tips", [])
                    ],
                    "equipment": [
                        str(item) 
                        for item in result.get("details", {}).get("equipment", [])
                    ],
                    "nutritional_info": result.get("details", {}).get("nutritional_info", [])
                }
            }
            
            return formatted_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid recipe format received: {stdout}\nError: {e}")
            return {
                "error": "Recipe format error",
                "details": "We had trouble formatting your recipe. Please try again!"
            }

    except Exception as e:
        logger.error(f"Recipe generation error: {str(e)}", exc_info=True)
        return {
            "error": "Recipe creation failed",
            "details": f"An unexpected error occurred: {str(e)}"
        }

@app.post("/generate-recipe", response_model=RecipeResponse)
async def generate_recipe(request: RecipeRequest):
    """
    Generate a recipe based on user preferences and dietary restrictions.
    Returns a complete recipe with ingredients, instructions, and tips.
    """
    try:
        if not request.preference or not request.preference.strip():
            raise HTTPException(
                status_code=400,
                detail="Please tell us what you'd like to cook!"
            )
        
        data = {
            "preference": request.preference.strip(),
            "dietary_restrictions": request.dietary_restrictions,
            "budget_preference": request.budget_preference
        }
        
        result = await run_python_script(data)
        
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=result
            )
            
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Recipe generation failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Kitchen troubles!",
                "message": str(e)
            }
        )

@app.get("/health")
async def health_check():
    """Check if the API is running properly"""
    return {
        "status": "healthy",
        "message": "Our kitchen is open and ready to cook!"
    }

@app.get("/")
async def root():
    """API root endpoint with available endpoints information"""
    return {
        "status": "API is running",
        "message": "Welcome to FlavorMind's Kitchen!",
        "endpoints": {
            "health": "/health - Check if our kitchen is open",
            "generate_recipe": "/generate-recipe - Create a personalized recipe"
        }
    }

