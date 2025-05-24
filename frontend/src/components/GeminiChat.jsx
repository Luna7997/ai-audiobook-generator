import React, { useState, useRef, useEffect } from 'react';
import apiService from '../services/api';

const GeminiChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [systemInstruction, setSystemInstruction] = useState('당신은 도움을 주는 친절한 AI 비서입니다.');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // 메시지 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 메시지 전송 함수
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // 사용자 메시지 추가
    const userMessage = { role: 'user', content: input };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Gemini API 호출
      const response = await apiService.generateText(input, systemInstruction);
      
      // 백엔드 응답 구조에 맞게 수정
      if (response && response.generated_text) {
        // AI 응답 추가
        setMessages(prevMessages => [
          ...prevMessages, 
          { role: 'assistant', content: response.generated_text }
        ]);
      } else {
        // 에러 응답 처리 (response.error 확인)
        setMessages(prevMessages => [
          ...prevMessages, 
          { role: 'error', content: `오류: ${response.error || '응답 데이터를 받아오지 못했습니다.'}` }
        ]);
      }
    } catch (error) {
      // 예외 처리 (error.response.data.error 확인)
      const errorMessage = error.response?.data?.error || error.message || '요청 중 알 수 없는 오류가 발생했습니다.';
      setMessages(prevMessages => [
        ...prevMessages, 
        { role: 'error', content: `오류: ${errorMessage}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="system-instruction">
        <label htmlFor="system-instruction">시스템 지시사항:</label>
        <input 
          type="text" 
          id="system-instruction" 
          value={systemInstruction}
          onChange={(e) => setSystemInstruction(e.target.value)}
          placeholder="AI의 역할을 설정하세요"
        />
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Gemini AI와 대화를 시작하세요!</p>
            <p className="small">질문이나 요청을 입력하면 AI가 응답합니다.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="avatar">
                {message.role === 'user' ? '👤' : message.role === 'assistant' ? '🤖' : '⚠️'}
              </div>
              <div className="content">{message.content}</div>
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant loading">
            <div className="avatar">🤖</div>
            <div className="content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? '전송 중...' : '전송'}
        </button>
      </form>

      <style jsx>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 80vh;
          max-width: 800px;
          margin: 0 auto;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }

        .system-instruction {
          padding: 10px;
          background-color: #f0f4f8;
          border-bottom: 1px solid #ddd;
          display: flex;
          align-items: center;
        }

        .system-instruction label {
          font-weight: bold;
          margin-right: 10px;
          white-space: nowrap;
        }

        .system-instruction input {
          flex-grow: 1;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }

        .messages-container {
          flex-grow: 1;
          overflow-y: auto;
          padding: 16px;
          background-color: #fff;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #666;
          text-align: center;
          padding: 20px;
        }

        .empty-state p {
          margin: 5px 0;
        }

        .empty-state .small {
          font-size: 14px;
          opacity: 0.7;
        }

        .message {
          display: flex;
          align-items: flex-start;
          margin-bottom: 8px;
        }

        .avatar {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 8px;
          flex-shrink: 0;
          font-size: 16px;
        }

        .content {
          padding: 12px;
          border-radius: 8px;
          max-width: 80%;
          word-break: break-word;
        }

        .user .content {
          background-color: #e3f2fd;
          margin-left: auto;
          color: #0d47a1;
        }

        .assistant .content {
          background-color: #f1f8e9;
          color: #33691e;
        }

        .error .content {
          background-color: #ffebee;
          color: #c62828;
        }

        .input-form {
          display: flex;
          padding: 10px;
          border-top: 1px solid #ddd;
          background-color: #f9f9f9;
        }

        .input-form input {
          flex-grow: 1;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          margin-right: 8px;
          font-size: 16px;
        }

        .input-form button {
          padding: 10px 16px;
          background-color: #4285f4;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
          white-space: nowrap;
        }

        .input-form button:disabled {
          background-color: #a0a0a0;
          cursor: not-allowed;
        }

        .typing-indicator {
          display: flex;
          gap: 4px;
        }

        .typing-indicator span {
          height: 8px;
          width: 8px;
          background-color: #888;
          border-radius: 50%;
          display: inline-block;
          animation: bounce 1.5s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(1) {
          animation-delay: 0s;
        }

        .typing-indicator span:nth-child(2) {
          animation-delay: 0.2s;
        }

        .typing-indicator span:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes bounce {
          0%, 80%, 100% { 
            transform: translateY(0);
          }
          40% { 
            transform: translateY(-10px);
          }
        }
      `}</style>
    </div>
  );
};

export default GeminiChat; 