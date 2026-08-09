import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App.tsx';
import { bootstrapAuth } from './store/authStore.ts';

// Start the Firebase auth listener (runs once, stays alive).
// Returns an unsubscribe function — kept alive for the entire app session.
bootstrapAuth();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
