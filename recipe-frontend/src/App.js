import React, { useState } from 'react';
import RecipeGenerator from './components/RecipeGenerator';
import LandingPage from './components/LandingPage';
import { ThemeProvider, createTheme, CssBaseline, Container } from '@mui/material';

// Create a custom theme for the application
const theme = createTheme({
  palette: {
    primary: {
      main: '#FFD700', // Gold color
    },
    secondary: {
      main: '#FFD700', // Also gold for consistency
    },
    background: {
      default: '#1a1a1a', // Dark background
      paper: '#282828', // Slightly lighter dark for paper elements
    },
    text: {
      primary: '#FFD700',
      secondary: '#FFD700',
    }
  },
  // ... keep existing theme configuration
});

const App = () => {
  const [showGenerator, setShowGenerator] = useState(false);

  const handleGetStarted = () => {
    setShowGenerator(true);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container>
        {!showGenerator ? (
          <LandingPage onGetStarted={handleGetStarted} />
        ) : (
          <RecipeGenerator />
        )}
      </Container>
    </ThemeProvider>
  );
};

export default App;