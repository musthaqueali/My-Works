// Google Firebase Configuration for Chevron Tracker
// Shared cloud database synced forever

const firebaseConfig = {
  apiKey: "AIzaSyBOmIXuJGmBDCLJejkACVxj2DGuza2OgW4",
  authDomain: "chevrontracker.firebaseapp.com",
  databaseURL: "https://chevrontracker-default-rtdb.firebaseio.com",
  projectId: "chevrontracker",
  storageBucket: "chevrontracker.firebasestorage.app",
  messagingSenderId: "1035645066754",
  appId: "1:1035645066754:web:d43ef8c266f81c625a511b",
  measurementId: "G-TKXF813NWW"
};

window.FIREBASE_CONFIG = firebaseConfig;

// Microsoft Entra ID (Azure AD) Work-Account Configuration
// Supports single-sign-on for all Pinnacle and Chevron corporate accounts
const msalConfig = {
  auth: {
    // Registered Azure App Client ID (can be overridden by window.AZURE_CLIENT_ID or localStorage)
    clientId: localStorage.getItem('chevron_azure_client_id') || window.AZURE_CLIENT_ID || "3f511943-42e1-4560-a299-d596489419fb",
    authority: "https://login.microsoftonline.com/common",
    redirectUri: (typeof window !== 'undefined' && window.location) 
      ? (window.location.origin.includes('localhost') || window.location.protocol === 'file:'
          ? window.location.href.split('#')[0].split('?')[0]
          : "https://chevrontracker01.netlify.app/")
      : "https://chevrontracker01.netlify.app/"
  },
  cache: {
    cacheLocation: "localStorage",
    storeAuthStateInCookie: false
  }
};

window.MSAL_CONFIG = msalConfig;
