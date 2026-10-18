import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';
import App from './App';
import AuthProvider from './AuthProvider';
import CatalogProvider from './CatalogProvider';
import { Router } from './router';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Router>
      <AuthProvider>
        <CatalogProvider>
          <App />
        </CatalogProvider>
      </AuthProvider>
    </Router>
  </React.StrictMode>,
);
