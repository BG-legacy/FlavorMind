// recipe-frontend/src/api/recipeApi.js

import { API_URL } from '../config/api';

export const fetchRecipeFromAI = async (preference, dietary_restrictions = null, budget_preference = null) => {
  try {
    console.log('Starting recipe generation for:', { preference, dietary_restrictions, budget_preference });
    
    const response = await fetch(`${API_URL}/generate-recipe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ 
        preference,
        dietary_restrictions,
        budget_preference
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail?.message || errorData.detail || "Failed to generate recipe");
    }

    const data = await response.json();
    console.log('Raw recipe data:', data);

    // Transform ingredients from array of objects to structured format
    const formattedIngredients = data.details.ingredients.map(ingredient => {
      if (typeof ingredient === 'object' && ingredient !== null) {
        return {
          quantity: ingredient.quantity || "as needed",
          unit: ingredient.unit || "",
          item: ingredient.item || ingredient.toString()
        };
      }
      return {
        quantity: "as needed",
        unit: "",
        item: ingredient.toString()
      };
    });

    return {
      recipe_name: data.recipe_name,
      recommendation: data.recommendation,
      budget_category: data.budget_category,
      difficulty: data.difficulty,
      details: {
        ingredients: formattedIngredients,
        instructions: Array.isArray(data.details.instructions) 
          ? data.details.instructions 
          : [data.details.instructions],
        tips: Array.isArray(data.details.tips) 
          ? data.details.tips 
          : [],
        equipment: Array.isArray(data.details.equipment)
          ? data.details.equipment
          : [],
        nutritional_info: data.details.nutritional_info || []
      }
    };

  } catch (error) {
    console.error('Recipe generation error:', error);
    throw new Error(
      error.message || 
      "Something went wrong while creating your recipe. Please try again!"
    );
  }
};

// Note: This file can be expanded to include other API calls related to recipes
// For example, you might add functions for saving recipes, fetching user favorites, etc.
