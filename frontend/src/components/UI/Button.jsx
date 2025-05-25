import React from 'react';

const Button = ({ 
  children, 
  onClick, 
  type = 'button', 
  disabled = false, 
  className = '', 
  variant = 'primary' 
}) => {
  const getButtonStyle = () => {
    const baseStyle = `
      padding: 8px 16px;
      border-radius: 4px;
      border: none;
      font-size: 14px;
      cursor: ${disabled ? 'not-allowed' : 'pointer'};
      transition: background-color 0.3s;
    `;
    
    const variantStyles = {
      primary: `
        background-color: ${disabled ? '#cccccc' : '#646cff'};
        color: ${disabled ? '#666666' : 'white'};
      `,
      secondary: `
        background-color: ${disabled ? '#f0f0f0' : '#f8f9fa'};
        color: ${disabled ? '#999999' : '#333333'};
        border: 1px solid ${disabled ? '#e0e0e0' : '#d0d0d0'};
      `,
      danger: `
        background-color: ${disabled ? '#ffcccc' : '#ff4d4d'};
        color: ${disabled ? '#999999' : 'white'};
      `
    };
    
    return baseStyle + (variantStyles[variant] || variantStyles.primary);
  };
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{ ...{ cursor: disabled ? 'not-allowed' : 'pointer' } }}
    >
      {children}
      <style jsx>{`
        button {
          ${getButtonStyle()}
        }
        button:hover:not(:disabled) {
          background-color: ${variant === 'primary' ? '#535bf2' : 
                             variant === 'secondary' ? '#e9ecef' : 
                             variant === 'danger' ? '#ff3333' : '#535bf2'};
        }
      `}</style>
    </button>
  );
};

export default Button; 