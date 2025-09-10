import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Enable React strict mode in development
const StrictModeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  if (process.env.NODE_ENV === 'development') {
    return <React.StrictMode>{children}</React.StrictMode>
  }
  return <>{children}</>
}

// Get the root element and ensure it exists
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found')
}

// Create React root and render the app
const root = ReactDOM.createRoot(rootElement)

root.render(
  <StrictModeWrapper>
    <App />
  </StrictModeWrapper>
)