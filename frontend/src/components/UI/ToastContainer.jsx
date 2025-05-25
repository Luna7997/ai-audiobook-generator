import React from 'react';
import Toast from './Toast';

const ToastContainer = ({ toasts = [], removeToast }) => {
  if (!toasts.length) return null;
  
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          code={toast.code}
          duration={toast.duration || 3000}
          onClose={() => removeToast(toast.id)}
        />
      ))}
      
      <style jsx>{`
        .toast-container {
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 9999;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
      `}</style>
    </div>
  );
};

export default ToastContainer; 