// Google Firebase Configuration for Chevron Tracker
// Shared cloud database synced forever

const firebaseConfig = {
  apiKey: "AIzaSyBOmIXuJGmBDCLJejkACVxj2DGuza2OgW4",
  authDomain: "chevrontracker.firebaseapp.com",
  databaseURL: "https://chevrontracker-default-rtdb.firebaseio.com", // Default US region. If you selected Europe or Asia, replace this with the URL shown on your Firebase Realtime Database screen.
  projectId: "chevrontracker",
  storageBucket: "chevrontracker.firebasestorage.app",
  messagingSenderId: "1035645066754",
  appId: "1:1035645066754:web:d43ef8c266f81c625a511b",
  measurementId: "G-TKXF813NWW"
};

// Make config globally accessible
window.FIREBASE_CONFIG = firebaseConfig;
