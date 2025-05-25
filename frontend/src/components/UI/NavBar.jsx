import React from 'react';
import { Link } from 'react-router-dom';

const NavBar = () => {
  return (
    <header>
      <nav>
        <Link to="/">메인</Link>
        <Link to="/upload">소설 업로드</Link>
        <Link to="/generate-audiobook">오디오북 생성</Link>
      </nav>
      <style jsx>{`
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
      `}</style>
    </header>
  );
};

export default NavBar; 