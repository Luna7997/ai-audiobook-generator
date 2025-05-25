import React from 'react';

const StatusMessage = ({ 
  type = 'info', 
  message, 
  className = '',
  style = {} 
}) => {
  if (!message) return null;
  
  const getTypeStyles = () => {
    const baseStyle = `
      padding: 10px;
      margin: 10px 0;
      border-radius: 4px;
      text-align: center;
    `;
    
    const typeStyles = {
      info: `
        color: #1890ff;
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
      `,
      success: `
        color: #52c41a;
        background-color: #f6ffed;
        border: 1px solid #b7eb8f;
      `,
      warning: `
        color: #faad14;
        background-color: #fffbe6;
        border: 1px solid #ffe58f;
      `,
      error: `
        color: #ff4d4f;
        background-color: #fff1f0;
        border: 1px solid #ffa39e;
      `
    };
    
    return baseStyle + (typeStyles[type] || typeStyles.info);
  };
  
  return (
    <div className={className} style={style}>
      {message}
      <style jsx>{`
        div {
          ${getTypeStyles()}
        }
      `}</style>
    </div>
  );
};

export default StatusMessage; 