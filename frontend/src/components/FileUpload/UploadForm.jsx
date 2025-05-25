import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import Button from '../UI/Button';
import StatusMessage from '../UI/StatusMessage';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPE = 'text/plain';

const UploadForm = ({ onFileSelect, selectedFile, fileError, isUploading }) => {
  const [dragActive, setDragActive] = useState(false);
  
  const validateFile = (file) => {
    if (!file) return { isValid: false, error: '파일이 선택되지 않았습니다.' };

    if (file.type !== ALLOWED_FILE_TYPE) {
      return { isValid: false, error: '텍스트(.txt) 파일만 업로드 가능합니다.' };
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return { 
        isValid: false, 
        error: `파일 크기가 너무 큽니다. 최대 ${MAX_FILE_SIZE_BYTES / (1024 * 1024)}MB까지 가능합니다.` 
      };
    }

    return { isValid: true, error: '' };
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const validation = validateFile(file);
      
      if (validation.isValid) {
        onFileSelect(file);
      } else {
        onFileSelect(null, validation.error);
      }
    }
    setDragActive(false);
  }, [onFileSelect]);

  const { getRootProps, getInputProps } = useDropzone({ 
    onDrop,
    accept: {
      'text/plain': ['.txt']
    },
    multiple: false,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
    disabled: isUploading
  });

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      const validation = validateFile(file);
      
      if (validation.isValid) {
        onFileSelect(file);
      } else {
        onFileSelect(null, validation.error);
      }
    }
  };

  return (
    <div className="upload-form">
      <div 
        {...getRootProps()} 
        className={`dropzone ${dragActive ? 'active' : ''} ${isUploading ? 'disabled' : ''}`}
      >
        <input {...getInputProps()} disabled={isUploading} />
        <div className="dropzone-content">
          <div className="icon">📄</div>
          <p className="main-text">
            TXT 파일을 이곳에 끌어다 놓거나 클릭하여 업로드하세요.
          </p>
          <p className="sub-text">
            최대 10MB 크기의 TXT 파일을 지원합니다.
          </p>
        </div>
      </div>
      
      {fileError && (
        <StatusMessage type="error" message={fileError} />
      )}
      
      {selectedFile && (
        <div className="selected-file">
          <span className="file-name">선택된 파일: {selectedFile.name}</span>
          <span className="file-size">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
        </div>
      )}
      
      <div className="alternative-upload">
        <p>또는 파일 선택:</p>
        <input
          type="file"
          accept=".txt"
          onChange={handleFileChange}
          disabled={isUploading}
          className="file-input"
        />
      </div>
      
      <style jsx>{`
        .upload-form {
          margin: 20px 0;
        }
        
        .dropzone {
          border: 2px dashed #d9d9d9;
          border-radius: 8px;
          padding: 30px 20px;
          background-color: #fafafa;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .dropzone.active {
          border-color: #646cff;
          background-color: rgba(100, 108, 255, 0.05);
        }
        
        .dropzone.disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .dropzone-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 10px;
        }
        
        .icon {
          font-size: 36px;
          margin-bottom: 10px;
        }
        
        .main-text {
          font-size: 16px;
          margin: 0;
        }
        
        .sub-text {
          font-size: 14px;
          color: #888;
          margin: 0;
        }
        
        .selected-file {
          margin-top: 15px;
          padding: 10px;
          background-color: #f0f0f0;
          border-radius: 4px;
          display: flex;
          justify-content: space-between;
        }
        
        .file-name {
          font-weight: bold;
        }
        
        .file-size {
          color: #666;
        }
        
        .alternative-upload {
          margin-top: 15px;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        .file-input {
          flex: 1;
        }
      `}</style>
    </div>
  );
};

export default UploadForm; 