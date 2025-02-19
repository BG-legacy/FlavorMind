import React from 'react';
import { 
  Button, 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemText,
  Chip,
  Grid 
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  AccessTime as AccessTimeIcon,
  AttachMoney as AttachMoneyIcon,
  Kitchen as KitchenIcon 
} from '@mui/icons-material';

const RecipeSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(4),
  padding: theme.spacing(2),
  backgroundColor: 'rgba(0, 0, 0, 0.2)',
  borderRadius: theme.shape.borderRadius,
}));

const RecipeTitle = styled(Typography)(({ theme }) => ({
  fontFamily: "'Playfair Display', serif",
  fontSize: '2.5rem',
  fontWeight: 700,
  color: '#FFD700',
  marginBottom: theme.spacing(3)
}));

const IngredientItem = ({ ingredient }) => {
  const { quantity, unit, item } = ingredient;
  return (
    <ListItem>
      <ListItemText>
        <span style={{ fontWeight: 'bold', color: '#FFD700' }}>
          {quantity} {unit}
        </span>
        {' '}
        {item}
      </ListItemText>
    </ListItem>
  );
};

const RecipeDisplay = ({ recipe, onStartOver, onGenerateNew }) => {
  const { 
    recipe_name, 
    recommendation, 
    budget_category, 
    difficulty,
    details 
  } = recipe;

  return (
    <Box>
      <RecipeTitle variant="h1">
        {recipe_name}
      </RecipeTitle>

      {recommendation && (
        <Typography 
          variant="subtitle1" 
          gutterBottom 
          sx={{ color: '#FFD700', marginBottom: 3 }}
        >
          {recommendation}
        </Typography>
      )}

      <Grid container spacing={2} sx={{ marginBottom: 3 }}>
        {budget_category && (
          <Grid item>
            <Chip
              icon={<AttachMoneyIcon />}
              label={budget_category}
              sx={{ 
                backgroundColor: 'rgba(255, 215, 0, 0.1)',
                color: '#FFD700'
              }}
            />
          </Grid>
        )}
        {difficulty && (
          <Grid item>
            <Chip
              icon={<AccessTimeIcon />}
              label={difficulty}
              sx={{ 
                backgroundColor: 'rgba(255, 215, 0, 0.1)',
                color: '#FFD700'
              }}
            />
          </Grid>
        )}
      </Grid>

      {details?.ingredients?.length > 0 && (
        <RecipeSection>
          <Typography variant="h6" sx={{ color: '#FFD700' }} gutterBottom>
            Ingredients
          </Typography>
          <List>
            {details.ingredients.map((ingredient, index) => (
              <IngredientItem 
                key={index} 
                ingredient={ingredient} 
              />
            ))}
          </List>
        </RecipeSection>
      )}

      {details?.instructions?.length > 0 && (
        <RecipeSection>
          <Typography variant="h6" sx={{ color: '#FFD700' }} gutterBottom>
            Instructions
          </Typography>
          <List>
            {details.instructions.map((step, index) => (
              <ListItem key={index}>
                <ListItemText 
                  primary={`${index + 1}. ${step}`}
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
            ))}
          </List>
        </RecipeSection>
      )}

      {details?.tips?.length > 0 && (
        <RecipeSection>
          <Typography variant="h6" sx={{ color: '#FFD700' }} gutterBottom>
            Tips
          </Typography>
          <List>
            {details.tips.map((tip, index) => (
              <ListItem key={index}>
                <ListItemText 
                  primary={`• ${tip}`}
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
            ))}
          </List>
        </RecipeSection>
      )}

      {details?.equipment?.length > 0 && (
        <RecipeSection>
          <Typography variant="h6" sx={{ color: '#FFD700' }} gutterBottom>
            Equipment Needed
          </Typography>
          <List>
            {details.equipment.map((item, index) => (
              <ListItem key={index}>
                <ListItemText 
                  primary={`• ${item}`}
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
            ))}
          </List>
        </RecipeSection>
      )}

      {details?.nutritional_info?.length > 0 && (
        <RecipeSection>
          <Typography variant="h6" sx={{ color: '#FFD700' }} gutterBottom>
            Nutritional Information
          </Typography>
          <List>
            {details.nutritional_info.map((info, index) => (
              <ListItem key={index}>
                <ListItemText 
                  primary={`• ${info}`}
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
            ))}
          </List>
        </RecipeSection>
      )}

      <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button 
          variant="outlined" 
          onClick={onStartOver}
          sx={{ 
            borderColor: '#FFD700', 
            color: '#FFD700',
            '&:hover': {
              borderColor: '#FFD700',
              backgroundColor: 'rgba(255, 215, 0, 0.1)'
            }
          }}
        >
          Start Over
        </Button>
        <Button 
          variant="contained" 
          onClick={onGenerateNew}
          sx={{ 
            bgcolor: '#FFD700', 
            color: '#000',
            '&:hover': {
              bgcolor: '#FFD700',
              opacity: 0.9
            }
          }}
        >
          Generate Another Recipe
        </Button>
      </Box>
    </Box>
  );
};

export default RecipeDisplay;
