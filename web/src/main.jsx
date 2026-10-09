import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App.jsx';
import './styles.css';
const bootstrap = document.getElementById('daily-data');
if (bootstrap) {
  const data = JSON.parse(bootstrap.textContent);
  createRoot(document.getElementById('daily-reader')).render(<App bootstrap={data} />);
}
