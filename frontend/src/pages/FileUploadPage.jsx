import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { UploadForm, ProgressIndicator, ProcessingStatus, Button } from '../components';
import { useToast } from '../contexts/ToastContext';

const FileUploadPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  // 단계별 상태
  const [fileStorageStatus, setFileStorageStatus] = useState({ status: 'idle', message: '' });
  const [characterAnalysisStatus, setCharacterAnalysisStatus] = useState({ status: 'idle', message: '' });
  const [structureAnalysisStatus, setStructureAnalysisStatus] = useState({ status: 'idle', message: '' });
  const [characterVoiceMatchingStatus, setCharacterVoiceMatchingStatus] = useState({ status: 'idle', message: '' });
  const [overallError, setOverallError] = useState(null);
  
  const [currentFileId, setCurrentFileId] = useState(null);
  const [characterVoiceMap, setCharacterVoiceMap] = useState(null);
  
  // 파일 선택 핸들러
  const handleFileSelection = (file, error = '') => {
    setSelectedFile(file);
    setFileError(error);
    
    // 오류가 있는 경우 토스트 메시지 표시
    if (error) {
      toast.showError(error);
    }
    
    // 새 파일 선택 시 상태 초기화
    setUploadProgress(0);
    setFileStorageStatus({ status: 'idle', message: '' });
    setCharacterAnalysisStatus({ status: 'idle', message: '' });
    setStructureAnalysisStatus({ status: 'idle', message: '' });
    setCharacterVoiceMatchingStatus({ status: 'idle', message: '' });
    setOverallError(null);
    setCurrentFileId(null);
    setCharacterVoiceMap(null);
  };

  // 파일 업로드 처리
  const handleUpload = async () => {
    if (!selectedFile) {
      const errorMsg = '업로드할 파일을 먼저 선택해주세요.';
      setOverallError(errorMsg);
      toast.showError(errorMsg, 'FILE_REQUIRED');
      return;
    }
    
    if (fileError) {
      const errorMsg = '유효하지 않은 파일입니다. 다른 파일을 선택해주세요.';
      setOverallError(errorMsg);
      toast.showError(errorMsg, 'INVALID_FILE');
      return;
    }

    // 상태 초기화 및 업로드 시작
    setIsUploading(true);
    setUploadProgress(0);
    setFileStorageStatus({ status: 'pending', message: '파일 업로드 및 저장 중...' });
    setCharacterAnalysisStatus({ status: 'idle', message: '' });
    setStructureAnalysisStatus({ status: 'idle', message: '' });
    setCharacterVoiceMatchingStatus({ status: 'idle', message: '' });
    setOverallError(null);
    setCurrentFileId(null);
    setCharacterVoiceMap(null);

    try {
      // 1. 파일 업로드 및 저장
      const uploadRes = await apiService.uploadFile(selectedFile, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });

      if (uploadRes.data && uploadRes.data.file_id) {
        const fileId = uploadRes.data.file_id;
        setCurrentFileId(fileId);
        
        setFileStorageStatus({ 
          status: 'success', 
          message: `파일 저장 완료: ${uploadRes.data.message} (ID: ${fileId})` 
        });
        setSelectedFile(null); // 성공 후 파일 선택 해제

        // 2. 등장인물 분석
        setCharacterAnalysisStatus({ status: 'pending', message: '등장인물 분석 중...' });
        try {
          const charAnalysisRes = await apiService.analyzeCharacters(fileId);
          setCharacterAnalysisStatus({ 
            status: 'success', 
            message: `등장인물 분석 완료: ${charAnalysisRes.message} (저장 파일: ${charAnalysisRes.analysis_file})`
          });

          // 3. 소설 구조 분석
          setStructureAnalysisStatus({ status: 'pending', message: '소설 구조 분석 중...' });
          try {
            const structAnalysisRes = await apiService.analyzeNovelStructure(fileId);
            setStructureAnalysisStatus({ 
              status: 'success', 
              message: `소설 구조 분석 완료: ${structAnalysisRes.message} (저장 파일: ${structAnalysisRes.analysis_file})`
            });

            // 4. 등장인물-성우 매칭
            setCharacterVoiceMatchingStatus({ status: 'pending', message: '등장인물-성우 매칭 중...' });
            try {
              const matchingRes = await apiService.matchCharactersVoices(fileId);
              setCharacterVoiceMatchingStatus({
                status: 'success',
                message: `등장인물-성우 매칭 완료: ${matchingRes.message} (저장 파일: ${matchingRes.matching_file})`
              });
              
              if (matchingRes.character_voice_map) {
                setCharacterVoiceMap(matchingRes.character_voice_map);
              }
              
              // 모든 과정이 성공적으로 완료되면 성공 토스트 표시
              toast.showSuccess('모든 처리 과정이 성공적으로 완료되었습니다.');
              
            } catch (matchingError) {
              console.error('Character-Voice matching error:', matchingError);
              const errorMsg = matchingError.message || '등장인물-성우 매칭 실패';
              setCharacterVoiceMatchingStatus({ status: 'failure', message: `등장인물-성우 매칭 실패: ${errorMsg}` });
              setOverallError('등장인물-성우 매칭 중 오류가 발생했습니다.');
              toast.showError(errorMsg, matchingError.code);
            }
            
          } catch (structError) {
            console.error('Structure analysis error:', structError);
            const errorMsg = structError.message || '소설 구조 분석 실패';
            setStructureAnalysisStatus({ status: 'failure', message: `소설 구조 분석 실패: ${errorMsg}` });
            setCharacterVoiceMatchingStatus({ status: 'skipped', message: '선행 작업(소설 구조 분석) 실패로 매칭을 건너뛰었습니다.' });
            setOverallError('소설 구조 분석 중 오류가 발생했습니다.');
            toast.showError(errorMsg, structError.code);
          }
        } catch (charError) {
          console.error('Character analysis error:', charError);
          const errorMsg = charError.message || '등장인물 분석 실패';
          setCharacterAnalysisStatus({ status: 'failure', message: `등장인물 분석 실패: ${errorMsg}` });
          setStructureAnalysisStatus({ status: 'skipped', message: '선행 작업(등장인물 분석) 실패로 구조 분석을 건너뛰었습니다.' });
          setCharacterVoiceMatchingStatus({ status: 'skipped', message: '선행 작업 실패로 매칭을 건너뛰었습니다.' });
          setOverallError('등장인물 분석 중 오류가 발생했습니다.');
          toast.showError(errorMsg, charError.code);
        }
      } else {
        // uploadRes.data가 없거나 file_id가 없는 경우
        const errorMsg = uploadRes.data?.error || '파일 업로드 후 서버 응답이 올바르지 않습니다.';
        setFileStorageStatus({ status: 'failure', message: `파일 저장 실패: ${errorMsg}` });
        setCharacterAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 등장인물 분석을 건너뛰었습니다.' });
        setStructureAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 소설 구조 분석을 건너뛰었습니다.' });
        setCharacterVoiceMatchingStatus({ status: 'skipped', message: '파일 저장 실패로 매칭을 건너뛰었습니다.' });
        setOverallError(uploadRes.data?.error || '파일 업로드에 실패했습니다.');
        toast.showError(errorMsg, uploadRes.data?.error_code || 'UPLOAD_FAILURE');
      }
    } catch (uploadErr) {
      console.error('Upload error during file stage:', uploadErr);
      const errorMsg = uploadErr.message || '파일 업로드 중 알 수 없는 오류 발생';
      setFileStorageStatus({ status: 'failure', message: `파일 저장 실패: ${errorMsg}` });
      setCharacterAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 분석 작업을 건너뛰었습니다.' });
      setStructureAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 분석 작업을 건너뛰었습니다.' });
      setCharacterVoiceMatchingStatus({ status: 'skipped', message: '파일 저장 실패로 매칭을 건너뛰었습니다.' });
      setOverallError('파일 업로드 중 오류가 발생했습니다.');
      toast.showError(errorMsg, uploadErr.code);
    } finally {
      setIsUploading(false);
    }
  };

  // 오디오북 생성 페이지로 이동
  const handleGoToGeneration = () => {
    navigate('/generate-audiobook');
  };

  // 처리 상태 진행 여부 확인
  const isProcessingComplete = 
    fileStorageStatus.status === 'success' && 
    (characterVoiceMatchingStatus.status === 'success' || 
     (characterVoiceMatchingStatus.status === 'skipped' && structureAnalysisStatus.status === 'success') || 
     (structureAnalysisStatus.status === 'skipped' && characterAnalysisStatus.status === 'success'));

  return (
    <div className="container">
      <h1>소설 파일 업로드</h1>
      <p className="description">
        TXT 형식의 소설 파일을 업로드하여 오디오북 생성을 준비하세요.
      </p>
      
      <UploadForm 
        onFileSelect={handleFileSelection}
        selectedFile={selectedFile}
        fileError={fileError}
        isUploading={isUploading}
      />
      
      {uploadProgress > 0 && uploadProgress < 100 && (
        <ProgressIndicator progress={uploadProgress} />
      )}
      
      <div className="upload-actions">
        <Button 
          onClick={handleUpload} 
          disabled={!selectedFile || isUploading}
          variant="primary"
        >
          {isUploading ? '처리 중...' : '파일 업로드 및 분석 시작'}
        </Button>
      </div>
      
      {(fileStorageStatus.status !== 'idle' || 
        characterAnalysisStatus.status !== 'idle' || 
        structureAnalysisStatus.status !== 'idle' || 
        characterVoiceMatchingStatus.status !== 'idle' || 
        overallError) && (
        <div className="status-section">
          <h2>처리 상태</h2>
          <ProcessingStatus 
            fileStorageStatus={fileStorageStatus}
            characterAnalysisStatus={characterAnalysisStatus}
            structureAnalysisStatus={structureAnalysisStatus}
            characterVoiceMatchingStatus={characterVoiceMatchingStatus}
            overallError={overallError}
          />
        </div>
      )}
      
      {isProcessingComplete && (
        <div className="next-steps">
          <p>파일 처리가 완료되었습니다. 이제 오디오북을 생성할 수 있습니다.</p>
          <Button onClick={handleGoToGeneration} variant="primary">
            오디오북 생성 페이지로 이동
          </Button>
        </div>
      )}
      
      <style jsx>{`
        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        h1 {
          text-align: center;
          margin-bottom: 1rem;
        }
        
        .description {
          text-align: center;
          margin-bottom: 2rem;
          color: #666;
        }
        
        .upload-actions {
          margin-top: 1rem;
          display: flex;
          justify-content: center;
        }
        
        .status-section {
          margin-top: 2rem;
        }
        
        .status-section h2 {
          margin-bottom: 1rem;
          font-size: 1.5rem;
        }
        
        .next-steps {
          margin-top: 2rem;
          padding: 1.5rem;
          background-color: #f0f7ff;
          border-radius: 8px;
          text-align: center;
        }
        
        .next-steps p {
          margin-bottom: 1rem;
        }
      `}</style>
    </div>
  );
};

export default FileUploadPage; 