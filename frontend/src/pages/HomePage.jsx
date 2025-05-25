import React from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
  return (
    <div className="container">
      <h1>오디오북 생성 프로젝트</h1>
      <p className="description">
        TXT 파일을 업로드하여 다중 화자 오디오북을 생성하세요.
      </p>
      
      <div className="button-container">
        <Link to="/upload" className="button-link">
          소설 TXT 파일 업로드하기
        </Link>
        
        <Link to="/generate-audiobook" className="button-link secondary">
          생성된 오디오북 보기
        </Link>
      </div>
      
      <div className="features">
        <div className="feature-item">
          <h3>다중 화자 지원</h3>
          <p>소설 속 등장인물마다 다른 목소리로 재생됩니다.</p>
        </div>
        
        <div className="feature-item">
          <h3>자동 분석</h3>
          <p>AI를 활용한 등장인물 및 소설 구조 자동 분석</p>
        </div>
        
        <div className="feature-item">
          <h3>맞춤형 음성</h3>
          <p>등장인물에 맞는 최적의 성우 목소리 매칭</p>
        </div>
      </div>
      
      <style jsx>{`
        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
          text-align: center;
        }
        
        h1 {
          font-size: 2.5rem;
          margin-bottom: 1rem;
          color: #333;
        }
        
        .description {
          font-size: 1.2rem;
          margin-bottom: 2rem;
          color: #666;
        }
        
        .button-container {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          align-items: center;
          margin-bottom: 3rem;
        }
        
        .button-link {
          display: inline-block;
          padding: 12px 25px;
          font-size: 1.1rem;
          color: white;
          background-color: #646cff;
          text-decoration: none;
          border-radius: 8px;
          transition: background-color 0.3s ease;
          width: 100%;
          max-width: 300px;
        }
        
        .button-link:hover {
          background-color: #535bf2;
        }
        
        .button-link.secondary {
          background-color: #6c757d;
        }
        
        .button-link.secondary:hover {
          background-color: #5a6268;
        }
        
        .features {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 2rem;
          margin-top: 2rem;
        }
        
        .feature-item {
          padding: 1.5rem;
          border-radius: 8px;
          background-color: #f8f9fa;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .feature-item h3 {
          margin-top: 0;
          color: #333;
        }
        
        .feature-item p {
          color: #666;
        }
        
        @media (max-width: 768px) {
          .features {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default HomePage; 