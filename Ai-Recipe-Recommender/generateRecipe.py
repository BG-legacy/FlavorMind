import json
import sys
import csv  # Import csv module for reading CSV files
import random  # Import random module for selecting random recipes
import os  # Import os module for working with file paths
import pandas as pd  # Import pandas for working with dataframes
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import requests
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
USDA_API_KEY = os.getenv('BNqalkOxG3glXAKqJlw5aLfsNqOixFx3qGM5beWk')  # Get this from https://fdc.nal.usda.gov/api-key-signup.html

# Initialize the ChatOllama model
# Resource: https://python.langchain.com/docs/integrations/chat/ollama
llm = ChatOllama(model='llama3.1')

# Load the CSV file containing recipe data using pandas
current_directory = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_directory, 'Food Ingredients and Recipe Dataset with Image Name Mapping.csv')
if not os.path.exists(file_path):
    print(f"File not found: {file_path}. Please make sure the file is in the correct directory.")
    recipes_df = None
else:
    # Read the CSV file into a pandas DataFrame
    # Resource: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
    recipes_df = pd.read_csv(file_path)

# Define prompt templates for recipe recommendation and details
# Resource: https://python.langchain.com/docs/modules/model_io/prompts/prompt_templates/
recipe_prompt = ChatPromptTemplate.from_template(
    "Based on the user's preference for {preference}, recommend a recipe from the following options:\n\n{recipe_titles}\n\nProvide a brief 2-3 sentence description including the name and whether it's budget-friendly. Keep it concise."
)

details_prompt = ChatPromptTemplate.from_template(
    "Provide a detailed recipe in the following order:\n\n" +
    "1. Ingredients:\n" +
    "2. Estimated Cost: (specify if budget-friendly, moderate, or expensive)\n" +
    "3. Instructions:\n" +
    "4. Tips and Tricks:\n\n" +
    "For the {recipe_name} recipe. Please highlight any expensive ingredients that significantly impact the total cost."
)

# Create chains for recipe recommendation and details
# Resource: https://python.langchain.com/docs/modules/chains/
recipe_chain = recipe_prompt | llm | StrOutputParser()
details_chain = details_prompt | llm | StrOutputParser()

def get_ingredient_prices(ingredients: List[str]) -> Dict[str, float]:
    """
    Get prices for ingredients using USDA Food Data Central API
    Returns a dictionary of ingredient names and their estimated prices
    """
    prices = {}
    base_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    
    for ingredient in ingredients:
        params = {
            'api_key': USDA_API_KEY,
            'query': ingredient,
            'pageSize': 1,
            'dataType': 'Survey (FNDDS)'  # Using FNDDS data as it includes common household foods
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('foods'):
                # Get the first matching food item
                food = data['foods'][0]
                # Estimate price based on portion size and average market data
                # Note: This is a simplified estimation
                portion_size = food.get('servingSize', 100)  # default
                price_per_100g = get_estimated_price(food)
                prices[ingredient] = (price_per_100g * portion_size / 100)
            else:
                prices[ingredient] = get_fallback_price(ingredient)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {ingredient}: {e}")
            prices[ingredient] = get_fallback_price(ingredient)
            
    return prices

def get_estimated_price(food_item: Dict) -> float:
    """
    Estimate price based on food category and typical market prices
    This uses a simplified pricing model based on food categories
    """
    # Basic price categories (you can expand this based on your needs)
    category_prices = {
        'Vegetables': 2.0,  # $2 per 100g
        'Fruits': 2.5,
        'Meat': 5.0,
        'Fish': 6.0,
        'Dairy': 1.5,
        'Grains': 1.0,
        'Spices': 10.0,
        'Oils': 1.5,
        'default': 2.0
    }
    
    # Try to determine category from food description
    description = food_item.get('description', '').lower()
    
    if any(word in description for word in ['vegetable', 'carrot', 'broccoli', 'spinach']):
        return category_prices['Vegetables']
    elif any(word in description for word in ['fruit', 'apple', 'banana', 'orange']):
        return category_prices['Fruits']
    elif any(word in description for word in ['meat', 'beef', 'chicken', 'pork']):
        return category_prices['Meat']
    elif any(word in description for word in ['fish', 'salmon', 'tuna']):
        return category_prices['Fish']
    elif any(word in description for word in ['milk', 'cheese', 'yogurt']):
        return category_prices['Dairy']
    elif any(word in description for word in ['rice', 'bread', 'pasta']):
        return category_prices['Grains']
    elif any(word in description for word in ['spice', 'herb', 'seasoning']):
        return category_prices['Spices']
    elif any(word in description for word in ['oil', 'butter']):
        return category_prices['Oils']
    
    return category_prices['default']

def get_fallback_price(ingredient: str) -> float:
    """
    Provide fallback prices for common ingredients when API data is unavailable
    """
    fallback_prices = {
        'salt': 0.1,
        'pepper': 0.2,
        'water': 0.0,
        'sugar': 0.5,
        'flour': 0.8,
        'oil': 1.5,
        'default': 2.0
    }
    
    ingredient_lower = ingredient.lower()
    return next((price for item, price in fallback_prices.items() 
                if item in ingredient_lower), fallback_prices['default'])

def get_most_relevant_recipe(preference):
    if recipes_df is None:
        return "Recipe dataset not loaded.", None, None, None

    # Filter the recipes based on user preference
    # Resource: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.apply.html
    relevant_recipes = recipes_df[recipes_df.apply(lambda row: preference.lower() in str(row['Ingredients']).lower() or preference.lower() in str(row['Title']).lower(), axis=1)]
    
    if relevant_recipes.empty:
        return "No relevant recipes found.", None, None, None

    # Get a random relevant recipe
    # Resource: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.sample.html
    recommended_recipe = relevant_recipes.sample(n=1).iloc[0]
    
    # Convert the filtered recipe to a string format, including ingredients for cost assessment
    recipe_str = f"{recommended_recipe['Title']}: {recommended_recipe['Ingredients']}"
    
    # Invoke the chain to get a recommendation based on the preference and recipe data
    result = recipe_chain.invoke({
        'preference': preference,
        'recipe_titles': recipe_str
    })
    
    # Generate details for the recommended recipe
    details = details_chain.invoke({'recipe_name': recommended_recipe['Title']})
    
    # Get the image file name
    image_file_name = recommended_recipe['Image_Name']
    
    return result, recommended_recipe['Title'], details, image_file_name

def main():
    # Read input data from stdin
    # Resource: https://docs.python.org/3/library/json.html#json.loads
    input_data = json.loads(sys.stdin.read())
    preference = input_data.get('preference', '')
    get_details = input_data.get('get_details', False)
    recipe_name = input_data.get('recipe_name', '')
    
    if get_details:
        # If get_details is True, generate details for the specified recipe
        details = details_chain.invoke({'recipe_name': recipe_name})
        output = {'details': details}
    else:
        # Get a random relevant recipe based on the user's preference
        recommendation, recipe_name, details, image_file_name = get_most_relevant_recipe(preference)
        output = {
            'recommendation': recommendation,
            'recipe_name': recipe_name,
            'details': details,
            'image_file_name': image_file_name
        }
    
    # Print the output as JSON
    # Resource: https://docs.python.org/3/library/json.html#json.dumps
    print(json.dumps(output))

if __name__ == "__main__":
    main()
