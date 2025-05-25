import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'
import { NavBar } from './components'
import { HomePage, FileUploadPage, AudiobookGenerationPage } from './pages'
import { ToastProvider } from './contexts/ToastContext'

function App() {
  return (
    <ToastProvider>
      <Router>
        <div className="app-container">
          <NavBar />
          
          <main className="content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/upload" element={<FileUploadPage />} />
              <Route path="/generate-audiobook" element={<AudiobookGenerationPage />} />
            </Routes>
          </main>
          
          <style jsx>{`
            .app-container {
              display: flex;
              flex-direction: column;
              min-height: 100vh;
            }
            
            .content {
              flex: 1;
              padding: 1rem;
            }
          `}</style>
        </div>
      </Router>
    </ToastProvider>
  )
}

export default App
