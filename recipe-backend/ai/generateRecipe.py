# Import required libraries for JSON handling and system operations
import json
import sys
# Import CSV handling library
import csv
# Import for random selection functionality
import random
# Import for operating system interface
import os
# Import pandas for data manipulation
import pandas as pd
# Import LangChain components for AI model interaction
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
# Import for making HTTP requests
import requests
# Import type hints
from typing import Dict, List, Tuple
# Import for environment variable management
from dotenv import load_dotenv
# Import logging functionality
import logging
# Import for file path handling
from pathlib import Path
# Import for creating unique cache keys
import hashlib
# Import for date/time operations
from datetime import datetime, timedelta
# Import for object serialization
import pickle

# Set up basic logging configuration with timestamp, logger name, level, and message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Create a logger instance for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
# Set USDA API key for nutritional data lookup
USDA_API_KEY = 'ggNrcwGzbKlQ5siiy0DIqG1LhVXSvghkLZ3hnSVn'
# Get Ollama host URL from environment variables, with fallback
ollama_host = os.getenv('OLLAMA_HOST', 'http://34.173.253.123:11434')

# Initialize the LLM model with specific parameters
llm = ChatOllama(
    model="llama2:latest",    # Use latest Llama 2 model
    base_url=ollama_host,     # Set the host URL
    temperature=0.7,          # Control randomness (0.7 = moderately creative)
    format="json"             # Specify output format as JSON
)

# Attempt to load the recipe dataset from CSV
try:
    # Construct path to CSV file relative to current script location
    csv_path = Path(__file__).parent / 'Food Ingredients and Recipe Dataset with Image Name Mapping.csv'
    # Load CSV into pandas DataFrame
    recipe_df = pd.read_csv(csv_path)
    # Log successful load with recipe count
    logger.info(f"Successfully loaded {len(recipe_df)} recipes from dataset")
except Exception as e:
    # Log error if dataset load fails
    logger.error(f"Failed to load recipe dataset: {e}")
    # Set DataFrame to None if load fails
    recipe_df = None

# Define template for initial recipe generation
recipe_prompt = ChatPromptTemplate.from_template("""
Based on preference: {preference}
Please suggest ONE recipe that matches this preference.
Return the response in this exact JSON format:
{
    "recipe_name": "Name of the recipe",
    "description": "2-3 sentence description",
    "budget_category": "budget-friendly|moderate|premium",
    "difficulty": "easy|medium|hard"
}
""")

# Define template for detailed recipe instructions
details_prompt = ChatPromptTemplate.from_template("""
Generate detailed instructions for: {recipe_name}
Return the response in this exact JSON format:
{
    "ingredients": [
        {"item": "ingredient name", "quantity": "amount", "unit": "measurement"},
        {"item": "ingredient name", "quantity": "amount", "unit": "measurement"}
    ],
    "instructions": [
        "step 1",
        "step 2"
    ],
    "tips": [
        "tip 1",
        "tip 2"
    ],
    "equipment": [
        "item 1",
        "item 2"
    ]
}
""")

# Create processing chains for recipe generation
recipe_chain = recipe_prompt | llm | StrOutputParser()    # Chain for basic recipe info
details_chain = details_prompt | llm | StrOutputParser()  # Chain for detailed instructions

# Class to handle caching of USDA API responses
class USDACache:
    def __init__(self, cache_dir: str = "cache/usda", expiry_days: int = 30):
        # Initialize cache directory and create if it doesn't exist
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Set cache expiration period
        self.expiry_days = expiry_days

    def _get_cache_key(self, query: str) -> str:
        """Generate a unique cache key for the query using MD5 hash"""
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Dict:
        """Retrieve cached data if it exists and is not expired"""
        # Generate cache key for query
        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.pickle"
        
        if cache_file.exists():
            try:
                # Load cached data from file
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    
                # Check if cache is still valid
                if cached_data['expiry'] > datetime.now():
                    logger.debug(f"Cache hit for query: {query}")
                    return cached_data['data']
                    
                # Remove expired cache file
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Cache read error: {e}")
                
        return None

    def set(self, query: str, data: Dict):
        """Store data in cache with expiration date"""
        # Generate cache key for query
        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.pickle"
        
        try:
            # Prepare data with expiration timestamp
            cached_data = {
                'data': data,
                'expiry': datetime.now() + timedelta(days=self.expiry_days)
            }
            # Save to cache file
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
            logger.debug(f"Cached data for query: {query}")
        except Exception as e:
            logger.error(f"Cache write error: {e}")

# Initialize global cache instance
usda_cache = USDACache()

def get_usda_food_data(ingredient: str) -> Dict:
    """Get food data from USDA API with caching"""
    try:
        # Check cache before making API call
        cached_data = usda_cache.get(ingredient)
        if cached_data:
            return cached_data

        # If not in cache, prepare API request
        api_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        headers = {"Content-Type": "application/json"}
        params = {
            "api_key": USDA_API_KEY,
            "query": ingredient,
            "pageSize": 1
        }
        
        # Make API request
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            # Cache successful response
            usda_cache.set(ingredient, data)
            return data
            
        return None
        
    except Exception as e:
        logger.error(f"USDA API error for {ingredient}: {e}")
        return None

def parse_ingredients(ingredients_list):
    """Parse ingredients into a clean, structured format"""
    cleaned_ingredients = []
    
    for ingredient in ingredients_list:
        # Clean up ingredient string
        ingredient = ingredient.strip('[]\'\"')
        
        # Split into main ingredient and preparation instructions
        parts = ingredient.split(',')
        main_part = parts[0].strip()
        
        try:
            # Define common measurement units
            units = ['cup', 'cups', 'tbsp', 'tsp', 'pound', 'lb', 'oz', 'ounce', 'bunch', 'bunches']
            
            # Split ingredient into words
            words = main_part.split()
            quantity = ""
            unit = ""
            item = ""
            
            # Extract quantity (including fractions)
            i = 0
            while i < len(words) and (words[i][0].isdigit() or '/' in words[i]):
                quantity += words[i] + " "
                i += 1
            quantity = quantity.strip()
            
            # Extract unit of measurement
            while i < len(words) and any(u in words[i].lower() for u in units):
                unit += words[i] + " "
                i += 1
            unit = unit.strip()
            
            # Remaining words form the ingredient name
            item = " ".join(words[i:])
            
            # Add preparation instructions if present
            if len(parts) > 1:
                prep_instructions = ", ".join(parts[1:]).strip()
                item = f"{item} ({prep_instructions})"
            
            # Add parsed ingredient to list
            cleaned_ingredients.append({
                "quantity": quantity or "as needed",
                "unit": unit or "",
                "item": item or main_part
            })
            
        except Exception as e:
            logger.error(f"Error parsing ingredient '{ingredient}': {e}")
            # Fallback format if parsing fails
            cleaned_ingredients.append({
                "quantity": "as needed",
                "unit": "",
                "item": ingredient.strip()
            })
    
    return cleaned_ingredients

def generate_recipe_with_llm(preference: str) -> Dict:
    """Generate a recipe using the LLM when no matching recipes are found"""
    try:
        # Generate basic recipe information
        recipe_response = recipe_chain.invoke({"preference": preference})
        recipe_data = json.loads(recipe_response)
        
        # Generate detailed recipe instructions
        details_response = details_chain.invoke({"recipe_name": recipe_data["recipe_name"]})
        details_data = json.loads(details_response)
        
        # Combine basic info and details
        return {
            **recipe_data,
            "details": details_data
        }
    except Exception as e:
        logger.error(f"LLM recipe generation error: {str(e)}")
        # Return error template if generation fails
        return {
            "recipe_name": "Error generating recipe",
            "description": "Failed to generate recipe",
            "budget_category": "unknown",
            "difficulty": "unknown",
            "details": {
                "ingredients": [],
                "instructions": [],
                "tips": [],
                "equipment": []
            }
        }

def get_food_cost_category(ingredients: List[str]) -> str:
    """Determine budget category based on ingredients using cached USDA API"""
    try:
        total_cost = 0
        ingredient_count = 0
        
        # Calculate cost score for each ingredient
        for ingredient in ingredients:
            data = get_usda_food_data(ingredient)
            if data and data.get('foods') and len(data['foods']) > 0:
                ingredient_count += 1
                food = data['foods'][0]
                # Assign higher cost to branded products
                if 'brandOwner' in food:
                    total_cost += 3
                # Assign higher cost to protein-rich foods
                elif any(nutrient.get('name') == 'Protein' for nutrient in food.get('nutrients', [])):
                    total_cost += 2.5
                # Base cost for other ingredients
                else:
                    total_cost += 1.5

        # Return default if no ingredients processed
        if ingredient_count == 0:
            return "moderate"
            
        # Calculate average cost and determine category
        average_cost = total_cost / ingredient_count
        
        if average_cost > 2.5:
            return "premium"
        elif average_cost > 1.8:
            return "moderate"
        else:
            return "budget-friendly"
            
    except Exception as e:
        logger.error(f"Error determining budget category: {e}")
        return "moderate"

def determine_difficulty(instructions: List[str], ingredients: List[str]) -> str:
    """Determine recipe difficulty based on number of steps and ingredients"""
    try:
        # Count steps and ingredients
        steps = len(instructions)
        ingredients_count = len(ingredients)
        
        # Calculate difficulty score (weighted average)
        difficulty_score = (steps * 0.6) + (ingredients_count * 0.4)
        
        # Determine difficulty category based on score
        if difficulty_score > 15:
            return "hard"
        elif difficulty_score > 8:
            return "medium"
        else:
            return "easy"
            
    except Exception as e:
        logger.error(f"Error determining difficulty: {e}")
        return "medium"

def get_nutritional_info(ingredient: str) -> List[str]:
    """Get nutritional information with caching"""
    try:
        # Get ingredient data from USDA API
        data = get_usda_food_data(ingredient)
        tips = []
        
        if data and data.get('foods') and len(data['foods']) > 0:
            food = data['foods'][0]
            nutrients = food.get('nutrients', [])
            
            # Generate nutritional tips based on nutrient content
            for nutrient in nutrients:
                name = nutrient.get('name', '').lower()
                value = nutrient.get('value', 0)
                
                # Add tips for significant nutrient amounts
                if 'protein' in name and value > 5:
                    tips.append(f"Good source of protein ({value:.1f}g per serving)")
                elif 'fiber' in name and value > 3:
                    tips.append(f"High in fiber ({value:.1f}g per serving)")
                elif 'vitamin' in name and value > 10:
                    tips.append(f"Contains {name}")
                
                # Limit to top 3 nutritional tips
                if len(tips) >= 3:
                    break
                    
        return tips
        
    except Exception as e:
        logger.error(f"Error getting nutritional info: {e}")
        return []

def get_most_relevant_recipe(preference: str) -> Dict:
    """Find and generate the most relevant recipe based on user preference"""
    logger.info(f"Finding recipe for preference: {preference}")
    
    try:
        # Check if recipe dataset is available
        if recipe_df is None:
            raise Exception("Recipe dataset not available")

        # Search for recipes matching preference
        matches = recipe_df[recipe_df['Title'].str.lower().str.contains(preference.lower(), na=False)]
        
        if not matches.empty:
            # Select random matching recipe
            recipe = matches.iloc[random.randint(0, len(matches) - 1)]
            
            # Parse ingredients from recipe
            raw_ingredients = recipe['Ingredients'].split(',')
            ingredients = []
            for ing in raw_ingredients:
                parts = ing.strip().split(' ', 1)
                if len(parts) > 1:
                    quantity = parts[0]
                    item = parts[1]
                else:
                    quantity = ""
                    item = parts[0]
                
                ingredients.append({
                    "quantity": quantity,
                    "unit": "",
                    "item": item.strip()
                })

            # Parse instructions into steps
            instructions = [step.strip() for step in recipe['Instructions'].split('.') if step.strip()]

            # Get recipe metadata
            budget_category = get_food_cost_category([ing['item'] for ing in ingredients])
            difficulty = determine_difficulty(instructions, ingredients)

            # Get nutritional information
            nutritional_tips = []
            try:
                # Get tips for main ingredients
                for ing in ingredients[:3]:
                    tips = get_nutritional_info(ing['item'])
                    nutritional_tips.extend(tips)
            except Exception as e:
                logger.error(f"Error getting nutritional info: {e}")

            # Return formatted recipe
            return {
                "recipe_name": recipe['Title'],
                "recommendation": f"A delicious {preference} recipe just for you!",
                "budget_category": budget_category,
                "difficulty": difficulty,
                "details": {
                    "ingredients": ingredients,
                    "instructions": instructions,
                    "tips": [
                        "Read through the entire recipe before starting",
                        "Prep all ingredients before cooking for best results"
                    ] + nutritional_tips,
                    "equipment": [
                        "Basic kitchen equipment needed for cooking",
                        "Measuring cups and spoons",
                        "Mixing bowls",
                        "Cooking utensils"
                    ]
                }
            }

        # If no match found, use LLM to generate recipe
        return generate_recipe_with_llm(preference)

    except Exception as e:
        logger.error(f"Recipe generation error: {str(e)}")
        return generate_recipe_with_llm(preference)

def main():
    """Main execution function"""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        preference = input_data.get('preference', '')
        logger.info(f"Processing recipe request: {preference}")
        
        # Generate recipe and output as JSON
        result = get_most_relevant_recipe(preference)
        print(json.dumps(result))
        logger.info("Recipe generation successful")
        
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}", exc_info=True)
        sys.exit(1)

# Execute main function if script is run directly
if __name__ == "__main__":
    main()
