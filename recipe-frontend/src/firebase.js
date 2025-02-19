// recipe-frontend/src/firebase.js

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    apiKey: "AIzaSyBne4WwI6e5QPUjNHEJB-teqboWBgRe320",
    authDomain: "recipe-recommender-9d84c.firebaseapp.com",
    projectId: "recipe-recommender-9d84c",
    storageBucket: "recipe-recommender-9d84c.appspot.com",
    messagingSenderId: "577481829789",
    appId: "1:577481829789:web:bed183fda10927da3f5374",
    measurementId: "G-5F38PE6C27"
  };  

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
