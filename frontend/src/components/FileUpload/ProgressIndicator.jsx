import React from 'react';

const ProgressIndicator = ({ progress = 0 }) => {
  return (
    <div className="progress-wrapper">
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="progress-text">{progress}% 완료</div>
      
      <style jsx>{`
        .progress-wrapper {
          margin: 20px 0;
        }
        
        .progress-bar {
          width: 100%;
          height: 8px;
          background-color: #f0f0f0;
          border-radius: 4px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background-color: #646cff;
          transition: width 0.3s ease;
        }
        
        .progress-text {
          text-align: right;
          font-size: 14px;
          margin-top: 5px;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default ProgressIndicator; 