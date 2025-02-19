// Import required modules
const express = require('express');
const { spawn } = require('child_process');
const cors = require('cors');
const app = express();
const admin = require('firebase-admin');
const serviceAccount = require('./recipe-recommender-9d84c-firebase-adminsdk-d39zy-4d2df3e84e.json');
const functions = require('firebase-functions');
const compression = require('compression');
const path = require('path');

// Enable compression
app.use(compression());

// Initialize Firebase Admin SDK
// Resource: https://firebase.google.com/docs/admin/setup
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: "recipe-recommender-9d84c"
});

// Get a Firestore database instance
const db = admin.firestore();

// Enable CORS for all routes
// Resource: https://expressjs.com/en/resources/middleware/cors.html
app.use(cors());

// Parse JSON bodies for incoming requests
// Resource: https://expressjs.com/en/api.html#express.json
app.use(express.json());

// Add this before your routes
app.use((err, req, res, next) => {
  console.error('Global error handler:', err);
  res.status(500).json({
    error: 'An unexpected error occurred',
    message: err.message
  });
});

// Function to run Python script and return a Promise
// Resource: https://nodejs.org/api/child_process.html#child_processspawncommand-args-options
function runPythonScript(data) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python3', ['ai/generateRecipe.py']);
    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
      if (!data.toString().includes('DeprecationWarning')) {
        console.error(`Python script error: ${data}`);
      }
    });

    pythonProcess.stdin.write(JSON.stringify(data));
    pythonProcess.stdin.end();

    pythonProcess.on('close', (code) => {
      try {
        const jsonLines = output.split('\n')
          .filter(line => line.trim())
          .filter(line => line.trim().startsWith('{'));
        
        if (jsonLines.length === 0) {
          reject(new Error(`No valid JSON output found. Error: ${errorOutput}`));
          return;
        }

        const result = JSON.parse(jsonLines[jsonLines.length - 1]);
        
        if (result.error) {
          reject(new Error(result.error));
        } else {
          resolve(result);
        }
      } catch (error) {
        reject(new Error(`Error parsing Python script output: ${error.message}\nRaw output: ${output}`));
      }
    });

    pythonProcess.on('error', (error) => {
      reject(new Error(`Failed to start Python process: ${error.message}`));
    });
  });
}

// Route to generate a recipe
// Resource: https://expressjs.com/en/guide/routing.html
app.post('/generate-recipe', async (req, res) => {
  try {
    if (!req.body.preference) {
      return res.status(400).json({ error: 'Preference is required' });
    }
    
    const result = await runPythonScript(req.body);
    
    if (result.error) {
      return res.status(400).json({ error: result.error });
    }
    
    res.json(result);
  } catch (error) {
    console.error('Error in generate-recipe:', error);
    res.status(500).json({ error: error.toString() });
  }
});

// Route to update user profile
app.post('/api/user/profile', async (req, res) => {
  try {
    const { uid, email } = req.body;
    
    if (!uid) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    const userRef = db.collection('users').doc(uid);
    const doc = await userRef.get();

    const userData = {
      email,
      updatedAt: admin.firestore.FieldValue.serverTimestamp()
    };

    if (!doc.exists) {
      userData.createdAt = admin.firestore.FieldValue.serverTimestamp();
      await userRef.set(userData);
    } else {
      await userRef.update(userData);
    }

    const updatedDoc = await userRef.get();
    
    res.status(200).json({
      message: 'Profile updated successfully',
      profile: {
        email: updatedDoc.data().email
      }
    });
  } catch (error) {
    console.error('Profile update error:', error);
    res.status(500).json({ 
      error: 'Failed to update profile',
      message: error.message
    });
  }
});

// Route to get user profile
app.get('/api/user/profile/:uid', async (req, res) => {
  try {
    console.log('Fetching profile for uid:', req.params.uid);
    
    if (!req.params.uid) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    const userRef = db.collection('users').doc(req.params.uid);
    const userDoc = await userRef.get();
    
    if (!userDoc.exists) {
      // Create default user document
      const defaultUserData = {
        email: '',
        createdAt: admin.firestore.FieldValue.serverTimestamp()
      };
      
      await userRef.set(defaultUserData);
      console.log('Created default user document');
      return res.status(200).json(defaultUserData);
    }

    console.log('User document found:', userDoc.data());
    return res.status(200).json(userDoc.data());
    
  } catch (error) {
    console.error('Error in user profile route:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch profile',
      details: error.message
    });
  }
});

// Route to add a recipe to user's favorites
app.post('/api/user/favorites', async (req, res) => {
  try {
    const { uid, recipe } = req.body;
    console.log('Received request to save recipe:', { uid, recipe });
    
    // Validate required fields
    if (!uid) {
      console.error('Missing uid in request');
      return res.status(400).json({ error: 'User ID is required' });
    }

    if (!recipe) {
      console.error('Missing recipe data in request');
      return res.status(400).json({ error: 'Recipe data is required' });
    }

    if (!recipe.title || !recipe.content) {
      console.error('Missing required recipe fields:', recipe);
      return res.status(400).json({ error: 'Recipe must include title and content' });
    }

    // Verify user exists
    const userRef = db.collection('users').doc(uid);
    const userDoc = await userRef.get();
    
    if (!userDoc.exists) {
      console.error(`User ${uid} not found in database`);
      return res.status(404).json({ error: 'User not found' });
    }

    // Add recipe to favorites
    console.log('Adding recipe to favorites for user:', uid);
    const docRef = await db.collection('users')
      .doc(uid)
      .collection('favorites')
      .add({
        title: recipe.title,
        content: recipe.content,
        addedAt: admin.firestore.FieldValue.serverTimestamp()
      });

    console.log('Recipe saved successfully with ID:', docRef.id);
    res.status(200).json({ 
      message: 'Recipe added to favorites',
      recipeId: docRef.id
    });
  } catch (error) {
    console.error('Error adding favorite:', {
      error: error.message,
      stack: error.stack,
      uid: req.body.uid,
      recipe: req.body.recipe
    });
    res.status(500).json({ 
      error: 'Failed to add favorite',
      details: error.message
    });
  }
});

// Route to update user's cooking history
app.post('/api/user/cooking-history', async (req, res) => {
  try {
    const { uid, recipeId } = req.body;
    // Add cooking history entry to user's subcollection in Firestore
    await db.collection('users').doc(uid).collection('cookingHistory').add({
      recipeId,
      cookedAt: admin.firestore.FieldValue.serverTimestamp()
    });
    res.status(200).json({ message: 'Cooking history updated' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to update cooking history' });
  }
});

// Add this route near your other routes
app.get('/api/test', (req, res) => {
  res.json({ message: 'API is working' });
});

// Add this new route
app.get('/api/user/saved-recipes/:uid', async (req, res) => {
  try {
    const uid = req.params.uid;
    const savedRecipesSnapshot = await db.collection('users')
      .doc(uid)
      .collection('favorites')
      .orderBy('addedAt', 'desc')
      .get();
    
    const savedRecipes = [];
    for (const doc of savedRecipesSnapshot.docs) {
      const recipeData = await db.collection('recipes').doc(doc.id).get();
      if (recipeData.exists) {
        savedRecipes.push({
          id: doc.id,
          addedAt: doc.data().addedAt.toDate(),
          ...recipeData.data()
        });
      }
    }
    
    res.status(200).json(savedRecipes);
  } catch (error) {
    console.error('Error fetching saved recipes:', error);
    res.status(500).json({ error: 'Failed to fetch saved recipes' });
  }
});

// Add this new route for deleting saved recipes
app.delete('/api/user/saved-recipes/:uid/:recipeId', async (req, res) => {
  try {
    const { uid, recipeId } = req.params;
    
    await db.collection('users')
      .doc(uid)
      .collection('favorites')
      .doc(recipeId)
      .delete();
    
    res.status(200).json({ message: 'Recipe removed from favorites' });
  } catch (error) {
    console.error('Error deleting saved recipe:', error);
    res.status(500).json({ error: 'Failed to delete recipe' });
  }
});

// Move the verifyAuth middleware definition BEFORE any routes that use it
const verifyAuth = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'No token provided' });
    }

    const token = authHeader.split('Bearer ')[1];
    try {
      const decodedToken = await admin.auth().verifyIdToken(token);
      req.user = decodedToken;
      next();
    } catch (tokenError) {
      console.error('Token verification failed:', tokenError);
      return res.status(401).json({ 
        error: 'Invalid authentication token',
        details: tokenError.message 
      });
    }
  } catch (error) {
    console.error('Auth middleware error:', error);
    return res.status(500).json({ 
      error: 'Authentication failed',
      details: error.message 
    });
  }
};

// Apply middleware to protected routes
app.use('/api/user/*', verifyAuth);

// Now you can use verifyAuth in your routes
app.delete('/api/user/profile/:uid', verifyAuth, async (req, res) => {
  try {
    const { uid } = req.params;
    
    // Set proper content type
    res.setHeader('Content-Type', 'application/json');
    
    // Verify the authenticated user is deleting their own profile
    if (req.user.uid !== uid) {
      return res.status(403).json({ 
        error: 'Unauthorized to delete this profile' 
      });
    }

    // Delete user's favorites collection
    const favoritesRef = db.collection('users').doc(uid).collection('favorites');
    const favoritesSnapshot = await favoritesRef.get();
    const batch = db.batch();
    
    favoritesSnapshot.docs.forEach((doc) => {
      batch.delete(doc.ref);
    });
    await batch.commit();
    
    // Delete user document
    await db.collection('users').doc(uid).delete();
    
    try {
      // Delete Firebase Auth user
      await admin.auth().deleteUser(uid);
    } catch (authError) {
      console.error('Error deleting auth user:', authError);
      return res.status(500).json({ 
        error: 'Failed to delete authentication profile',
        details: authError.message 
      });
    }
    
    return res.status(200).json({ 
      message: 'Profile deleted successfully' 
    });
  } catch (error) {
    console.error('Error deleting profile:', error);
    return res.status(500).json({ 
      error: 'Failed to delete profile',
      details: error.message 
    });
  }
});

// Update the onUserCreated function
exports.onUserCreated = functions.auth.user().onCreate(async (user) => {
  try {
    const { uid, email, displayName } = user;
    
    // Create user profile in Firestore
    await db.collection('users').doc(uid).set({
      email,
      displayName: displayName || '',
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });
    
    // Send welcome email
    const { sendWelcomeEmail } = require('./utils/emailService');
    await sendWelcomeEmail(email, displayName || 'Valued User');
    
    console.log(`Created Firestore profile and sent welcome email for user ${uid}`);
  } catch (error) {
    console.error('Error in user creation process:', error);
    throw error;
  }
});
// Add cache headers
app.use((req, res, next) => {
  // Cache for 1 hour
  res.setHeader('Cache-Control', 'public, max-age=3600');
  next();
});

// Serve static files from the React frontend app
const buildPath = path.join(__dirname, "../recipe-frontend/build");
app.use(express.static(buildPath));

// Handle any requests that don't match the above
app.get("/*", function(req, res) {
  res.sendFile(
    path.join(__dirname, "../recipe-frontend/build/index.html"),
    function (err) {
      if (err) {
        res.status(500).send(err);
      }
    }
  );
});

// Start the server
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

