import React from 'react';
import { Link } from 'react-router-dom';
import '../App.css'; // 전반적인 스타일 가져오기 (필요에 따라)

function AudiobookMain() {
  return (
    <div className="container" style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>오디오북 생성 프로젝트</h1>
      <p style={{ fontSize: '1.2em', margin: '20px 0' }}>
        TXT 파일을 업로드하여 다중 화자 오디오북을 생성하세요.
      </p>
      <Link to="/upload" className="button-link" 
        style={{
          display: 'inline-block',
          padding: '12px 25px',
          fontSize: '1.1em',
          color: 'white',
          backgroundColor: '#646cff', // Vite 기본 파란색 계열
          textDecoration: 'none',
          borderRadius: '8px',
          transition: 'background-color 0.3s ease'
        }}
        onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#535bf2'} // 호버 효과
        onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#646cff'}
      >
        소설 TXT 파일 업로드하기
      </Link>
      <div style={{marginTop: '40px', fontSize: '0.9em', color: 'gray'}}>
        <p>개발 테스트 페이지로 이동:</p>
        <Link to="/test/api" style={{marginRight: '10px'}}>API/DB 테스트</Link>
        <Link to="/test/gemini">Gemini 채팅 테스트</Link>
      </div>
    </div>
  );
}

export default AudiobookMain; 