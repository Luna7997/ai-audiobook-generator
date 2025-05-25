import React, { useEffect, useState } from 'react';

const Toast = ({ 
  message, 
  type = 'error', 
  code = null,
  duration = 3000, 
  onClose 
}) => {
  const [visible, setVisible] = useState(true);
  
  useEffect(() => {
    if (!message) return;
    
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => {
        onClose && onClose();
      }, 300); // 애니메이션 종료 후 완전히 제거
    }, duration);
    
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);
  
  if (!message) return null;
  
  const getIconByType = () => {
    switch (type) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      case 'success':
        return '✅';
      default:
        return 'ℹ️';
    }
  };
  
  return (
    <div className={`toast ${type} ${visible ? 'visible' : 'hidden'}`}>
      <div className="toast-content">
        <span className="toast-icon">{getIconByType()}</span>
        <div className="toast-message-container">
          {code && <div className="toast-code">오류 코드: {code}</div>}
          <div className="toast-message">{message}</div>
        </div>
        <button className="toast-close" onClick={() => {
          setVisible(false);
          setTimeout(() => onClose && onClose(), 300);
        }}>
          ×
        </button>
      </div>
      
      <style jsx>{`
        .toast {
          position: fixed;
          top: 20px;
          right: 20px;
          min-width: 300px;
          max-width: 450px;
          z-index: 9999;
          border-radius: 4px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          transform: translateX(120%);
          transition: transform 0.3s ease-out;
        }
        
        .toast.visible {
          transform: translateX(0);
        }
        
        .toast.hidden {
          transform: translateX(120%);
        }
        
        .toast.error {
          background-color: #fff2f0;
          border-left: 4px solid #ff4d4f;
        }
        
        .toast.warning {
          background-color: #fffbe6;
          border-left: 4px solid #faad14;
        }
        
        .toast.info {
          background-color: #e6f7ff;
          border-left: 4px solid #1890ff;
        }
        
        .toast.success {
          background-color: #f6ffed;
          border-left: 4px solid #52c41a;
        }
        
        .toast-content {
          display: flex;
          align-items: flex-start;
          padding: 12px 16px;
        }
        
        .toast-icon {
          margin-right: 12px;
          font-size: 20px;
        }
        
        .toast-message-container {
          flex: 1;
        }
        
        .toast-code {
          font-weight: bold;
          margin-bottom: 4px;
          font-family: monospace;
        }
        
        .toast-message {
          font-size: 14px;
          line-height: 1.5;
          word-break: break-word;
        }
        
        .toast-close {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #999;
          padding: 0;
          margin-left: 12px;
          line-height: 1;
        }
        
        .toast-close:hover {
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default Toast; 