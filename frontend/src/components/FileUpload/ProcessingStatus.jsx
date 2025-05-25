import React from 'react';
import StatusMessage from '../UI/StatusMessage';

const ProcessingStatus = ({ 
  fileStorageStatus,
  characterAnalysisStatus,
  structureAnalysisStatus,
  characterVoiceMatchingStatus,
  overallError
}) => {
  // 처리 단계별 상태 표시 및 스타일 지정 함수
  const getStatusIndicator = (status) => {
    if (!status) return null;
    
    let icon, statusText, statusClass;
    
    switch (status.status) {
      case 'pending':
        icon = '⏳';
        statusText = '처리 중...';
        statusClass = 'status-pending';
        break;
      case 'success':
        icon = '✅';
        statusText = '완료';
        statusClass = 'status-success';
        break;
      case 'failure':
        icon = '❌';
        statusText = '실패';
        statusClass = 'status-failure';
        break;
      case 'skipped':
        icon = '⏭️';
        statusText = '건너뜀';
        statusClass = 'status-skipped';
        break;
      default:
        icon = '⏹️';
        statusText = '대기 중';
        statusClass = 'status-idle';
    }
    
    return (
      <span className={statusClass}>
        {icon} {statusText}
        <style jsx>{`
          .status-pending {
            color: #1890ff;
            font-weight: bold;
          }
          
          .status-success {
            color: #52c41a;
            font-weight: bold;
          }
          
          .status-failure {
            color: #ff4d4f;
            font-weight: bold;
          }
          
          .status-skipped {
            color: #faad14;
            font-weight: normal;
          }
          
          .status-idle {
            color: #bfbfbf;
            font-weight: normal;
          }
        `}</style>
      </span>
    );
  };

  return (
    <div className="processing-status">
      {overallError && (
        <StatusMessage 
          type="error" 
          message={overallError} 
        />
      )}
      
      <div className="status-step">
        <div className="status-title">1. 파일 업로드 및 저장</div>
        <div className="status-detail">
          <div className="status-indicator">
            {getStatusIndicator(fileStorageStatus)}
          </div>
          {fileStorageStatus?.message && (
            <div className="status-message">
              {fileStorageStatus.message}
            </div>
          )}
        </div>
      </div>
      
      <div className="status-step">
        <div className="status-title">2. 등장인물 분석</div>
        <div className="status-detail">
          <div className="status-indicator">
            {getStatusIndicator(characterAnalysisStatus)}
          </div>
          {characterAnalysisStatus?.message && (
            <div className="status-message">
              {characterAnalysisStatus.message}
            </div>
          )}
        </div>
      </div>
      
      <div className="status-step">
        <div className="status-title">3. 소설 구조 분석</div>
        <div className="status-detail">
          <div className="status-indicator">
            {getStatusIndicator(structureAnalysisStatus)}
          </div>
          {structureAnalysisStatus?.message && (
            <div className="status-message">
              {structureAnalysisStatus.message}
            </div>
          )}
        </div>
      </div>
      
      <div className="status-step">
        <div className="status-title">4. 등장인물-성우 매칭</div>
        <div className="status-detail">
          <div className="status-indicator">
            {getStatusIndicator(characterVoiceMatchingStatus)}
          </div>
          {characterVoiceMatchingStatus?.message && (
            <div className="status-message">
              {characterVoiceMatchingStatus.message}
            </div>
          )}
        </div>
      </div>
      
      <style jsx>{`
        .processing-status {
          margin: 20px 0;
          background-color: #f9f9f9;
          border-radius: 8px;
          padding: 15px;
        }
        
        .status-step {
          margin-bottom: 15px;
          padding-bottom: 15px;
          border-bottom: 1px solid #eee;
        }
        
        .status-step:last-child {
          margin-bottom: 0;
          padding-bottom: 0;
          border-bottom: none;
        }
        
        .status-title {
          font-weight: bold;
          margin-bottom: 5px;
        }
        
        .status-detail {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        
        .status-message {
          font-size: 14px;
          color: #666;
          margin-left: 20px;
        }
      `}</style>
    </div>
  );
};

export default ProcessingStatus; 