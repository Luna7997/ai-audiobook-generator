import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
// import ApiTester from './components/ApiTester'
import GeminiChat from './components/GeminiChat'
import FileUpload from './components/FileUpload'
import AudiobookMain from './components/AudiobookMain'
// import CharacterExtractor from './components/CharacterExtractor'

function App() {
  return (
    <Router>
      <div className="app-container">
        <header>
          <nav>
            <Link to="/">메인</Link>
            <Link to="/upload">소설 업로드</Link>
            {/* <Link to="/extract-characters">등장인물 분석</Link> */}
            {/* <Link to="/test/api">API 테스트</Link> */}
            <Link to="/test/gemini">Gemini 테스트</Link>
          </nav>
        </header>

        <Routes>
          <Route path="/" element={<AudiobookMain />} />
          <Route path="/upload" element={<FileUpload />} />
          {/* <Route path="/extract-characters" element={<CharacterExtractor />} /> */}
          {/* <Route path="/test/api" element={<ApiTester />} /> */}
          <Route path="/test/gemini" element={<GeminiChat />} />
        </Routes>
        
        <style jsx>{`
          .app-container {
            padding: 2rem;
            text-align: center;
          }
          header {
            margin-bottom: 2rem;
          }
          nav {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1rem;
          }
          nav a {
            color: #646cff;
            text-decoration: inherit;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: background-color 0.3s;
          }
          nav a:hover {
            background-color: rgba(100, 108, 255, 0.1);
          }
          .navigation-links {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
          }
          .navigation-links a {
            display: inline-block;
            background-color: #f0f0f0;
            color: #333;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            text-decoration: none;
            transition: background-color 0.3s;
          }
          .navigation-links a:hover {
            background-color: #e0e0e0;
          }
        `}</style>
      </div>
    </Router>
  )
}

export default App
