// Import necessary components and hooks from React and Material-UI
import React, { useState, useEffect } from 'react';
import { fetchRecipeFromAI } from '../api/recipeApi';
// Resource for React hooks: https://react.dev/reference/react
import { 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress, 
  Box,
  Snackbar,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip
} from '@mui/material';
// Resource for Material-UI components: https://mui.com/material-ui/getting-started/overview/
import RecipeDisplay from './RecipeDisplay';
import { styled } from '@mui/material/styles';

const MobileTextField = styled(TextField)(({ theme }) => ({
  [theme.breakpoints.down('sm')]: {
    '& .MuiInputBase-input': {
      fontSize: '16px', // Prevents iOS zoom on focus
      padding: '12px'
    },
    '& .MuiInputLabel-root': {
      fontSize: '14px'
    }
  }
}));

const loadingMessages = [
  "Searching for the perfect recipe...",
  "Mixing ingredients with AI magic...",
  "Cooking up something special...",
  "Almost ready to serve...",
];

const RecipeGenerator = () => {
  // State declarations
  const [preference, setPreference] = useState('');
  const [dietaryRestrictions, setDietaryRestrictions] = useState([]);
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingMessage, setLoadingMessage] = useState('Searching for the perfect recipe...');

  const loadingMessages = [
    "Mixing ingredients with AI magic...",
    "Preheating our virtual oven...",
    "Gathering the freshest recipes...",
    "Adding a pinch of creativity...",
    "Almost ready to serve..."
  ];

  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setLoadingMessage(prevMessage => {
          const currentIndex = loadingMessages.indexOf(prevMessage);
          return loadingMessages[(currentIndex + 1) % loadingMessages.length];
        });
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [loading]);

  const handleGenerateRecipe = async () => {
    try {
      setLoading(true);
      setError('');
      const newRecipe = await fetchRecipeFromAI(
        preference,
        dietaryRestrictions
      );
      setRecipe(newRecipe);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNew = async () => {
    try {
      setLoading(true);
      setError('');
      // Keep the same preference but get a different recipe
      const newRecipe = await fetchRecipeFromAI(preference);
      setRecipe(newRecipe);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      pt: 4
    }}>
      <Typography 
        variant="h1" 
        sx={{ 
          fontSize: '3.5rem',
          color: '#FFD700',
          fontFamily: "'Playfair Display', serif",
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          mb: 4,
          textShadow: '2px 2px 4px rgba(0, 0, 0, 0.3)'
        }}
      >
        Flavormind
      </Typography>

      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          maxWidth: '800px',
          width: '100%',
          mx: 'auto'
        }}
      >
        {!recipe && (
          <>
            <Typography variant="h4" gutterBottom sx={{ color: '#FFD700' }}>
              What would you like to cook?
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 4 }}>
              <TextField
                fullWidth
                value={preference}
                onChange={(e) => setPreference(e.target.value)}
                placeholder="Enter your food preference..."
                sx={{ 
                  '& .MuiInputBase-input': { color: '#FFD700' },
                  '& .MuiOutlinedInput-root': {
                    '& fieldset': { borderColor: '#FFD700' },
                    '&:hover fieldset': { borderColor: '#FFD700' },
                    '&.Mui-focused fieldset': { borderColor: '#FFD700' }
                  }
                }}
              />

              <Button
                variant="contained"
                onClick={handleGenerateRecipe}
                disabled={loading || !preference.trim()}
                sx={{ 
                  bgcolor: '#FFD700',
                  color: '#000',
                  '&:hover': { bgcolor: '#FFD700', opacity: 0.9 }
                }}
              >
                Generate Recipe
              </Button>
            </Box>
          </>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress sx={{ color: '#FFD700' }} />
          </Box>
        )}

        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              mb: 4,
              backgroundColor: 'rgba(255, 0, 0, 0.1)',
              color: '#FFD700'
            }}
          >
            {error}
          </Alert>
        )}

        {recipe && !loading && (
          <RecipeDisplay
            recipe={recipe}
            onStartOver={() => {
              setRecipe(null);
              setPreference('');
            }}
            onGenerateNew={handleGenerateNew}
          />
        )}
      </Paper>
    </Box>
  );
};

export default RecipeGenerator;
