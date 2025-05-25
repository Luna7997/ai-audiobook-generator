import React, { createContext, useContext, useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ToastContainer from '../components/UI/ToastContainer';

// Context 생성
const ToastContext = createContext(null);

// Context Provider 컴포넌트
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  // 토스트 추가 함수
  const addToast = useCallback((message, options = {}) => {
    const { type = 'error', code = null, duration = 3000 } = options;
    
    const id = uuidv4();
    const newToast = {
      id,
      message,
      type,
      code,
      duration,
    };
    
    setToasts(prevToasts => [...prevToasts, newToast]);
    
    return id;
  }, []);

  // 토스트 제거 함수
  const removeToast = useCallback((id) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  }, []);

  // 모든 토스트 제거 함수
  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);
  
  // 특정 타입의 토스트 추가 헬퍼 함수들
  const showError = useCallback((message, code = null, duration) => {
    return addToast(message, { type: 'error', code, duration });
  }, [addToast]);
  
  const showWarning = useCallback((message, code = null, duration) => {
    return addToast(message, { type: 'warning', code, duration });
  }, [addToast]);
  
  const showInfo = useCallback((message, code = null, duration) => {
    return addToast(message, { type: 'info', code, duration });
  }, [addToast]);
  
  const showSuccess = useCallback((message, code = null, duration) => {
    return addToast(message, { type: 'success', code, duration });
  }, [addToast]);

  // Context 값
  const value = {
    toasts,
    addToast,
    removeToast,
    clearToasts,
    showError,
    showWarning,
    showInfo,
    showSuccess
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
};

// Custom Hook
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export default ToastContext; 