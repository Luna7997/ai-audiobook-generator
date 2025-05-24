import React, { useState, useCallback, useEffect } from 'react';
import apiService from '../services/api'; // api.js 경로에 따라 수정 필요
import { useDropzone } from 'react-dropzone';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPE = 'text/plain';

function FileUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  // 단계별 상태 추가
  const [fileStorageStatus, setFileStorageStatus] = useState({ status: 'idle', message: '' }); // idle, pending, success, failure
  const [characterAnalysisStatus, setCharacterAnalysisStatus] = useState({ status: 'idle', message: '' });
  const [structureAnalysisStatus, setStructureAnalysisStatus] = useState({ status: 'idle', message: '' });
  const [characterVoiceMatchingStatus, setCharacterVoiceMatchingStatus] = useState({ status: 'idle', message: '' });
  const [overallError, setOverallError] = useState(null);
  
  const [currentFileId, setCurrentFileId] = useState(null);
  const [characterVoiceMap, setCharacterVoiceMap] = useState(null);
  const [voiceActorList, setVoiceActorList] = useState([]);
  
  // 성우 목록 불러오기
  useEffect(() => {
    const loadVoiceActors = async () => {
      try {
        const response = await apiService.getVoiceActors();
        if (response && response.voice_actors) {
          setVoiceActorList(response.voice_actors);
        }
      } catch (error) {
        console.error('성우 목록 로드 실패:', error);
      }
    };
    
    loadVoiceActors();
  }, []);

  const validateFile = (file) => {
    if (!file) return false;

    if (file.type !== ALLOWED_FILE_TYPE) {
      setFileError('Invalid file type. Please upload a .txt file.');
      return false;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setFileError(`File is too large. Maximum size is ${MAX_FILE_SIZE_BYTES / (1024 * 1024)}MB.`);
      return false;
    }

    setFileError('');
    return true;
  };

  const handleFileSelection = (file) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      setUploadStatus(`Selected file: ${file.name}`);
    } else {
      setSelectedFile(null);
      setUploadStatus(''); // Clear previous status if validation fails
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      handleFileSelection(acceptedFiles[0]);
    }
    setUploadProgress(0);
    setFileStorageStatus({ status: 'idle', message: '' });
    setCharacterAnalysisStatus({ status: 'idle', message: '' });
    setStructureAnalysisStatus({ status: 'idle', message: '' });
    setCharacterVoiceMatchingStatus({ status: 'idle', message: '' });
    setOverallError(null);
    setCurrentFileId(null);
    setCharacterVoiceMap(null);
  }, []);

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files.length > 0) {
      handleFileSelection(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setOverallError('업로드할 파일을 먼저 선택해주세요.');
      return;
    }
    if (fileError) { // Prevent upload if there's a validation error
        setOverallError('Cannot upload due to file error.');
        return;
    }

    // 모든 상태 초기화
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

      // uploadFile은 axios 응답 전체를 반환하므로, data에 접근해야 함
      if (uploadRes.data && uploadRes.data.file_id) {
        const fileId = uploadRes.data.file_id;
        setCurrentFileId(fileId);
        
        setFileStorageStatus({ 
            status: 'success', 
            message: `파일 저장 완료: ${uploadRes.data.message} (ID: ${fileId})` 
        });
        console.log('File processing result:', uploadRes.data.data);
        setSelectedFile(null); // 성공 후 파일 선택 해제

        // 2. 등장인물 분석
        setCharacterAnalysisStatus({ status: 'pending', message: '등장인물 분석 중...' });
        try {
          const charAnalysisRes = await apiService.analyzeCharactersById(fileId);
          setCharacterAnalysisStatus({ 
            status: 'success', 
            message: `등장인물 분석 완료: ${charAnalysisRes.message} (저장 파일: ${charAnalysisRes.analysis_file})`
          });
          console.log('Character analysis response:', charAnalysisRes);

          // 3. 소설 구조 분석
          setStructureAnalysisStatus({ status: 'pending', message: '소설 구조 분석 중...' });
          try {
            const structAnalysisRes = await apiService.analyzeNovelStructureById(fileId);
            setStructureAnalysisStatus({ 
              status: 'success', 
              message: `소설 구조 분석 완료: ${structAnalysisRes.message} (저장 파일: ${structAnalysisRes.analysis_file})`
            });
            console.log('Structure analysis response:', structAnalysisRes);

            // 4. 등장인물-성우 매칭
            setCharacterVoiceMatchingStatus({ status: 'pending', message: '등장인물-성우 매칭 중...' });
            try {
              const matchingRes = await apiService.matchCharactersVoices(fileId);
              setCharacterVoiceMatchingStatus({
                status: 'success',
                message: `등장인물-성우 매칭 완료: ${matchingRes.message} (저장 파일: ${matchingRes.matching_file})`
              });
              console.log('Character-Voice matching response:', matchingRes);
              
              if (matchingRes.character_voice_map) {
                setCharacterVoiceMap(matchingRes.character_voice_map);
              }
              
            } catch (matchingError) {
              console.error('Character-Voice matching error:', matchingError);
              const errorMsg = matchingError.response?.data?.error || matchingError.message || '등장인물-성우 매칭 실패';
              setCharacterVoiceMatchingStatus({ status: 'failure', message: `등장인물-성우 매칭 실패: ${errorMsg}` });
              setOverallError('등장인물-성우 매칭 중 오류가 발생했습니다.');
            }
            
          } catch (structError) {
            console.error('Structure analysis error:', structError);
            const errorMsg = structError.response?.data?.error || structError.message || '소설 구조 분석 실패';
            setStructureAnalysisStatus({ status: 'failure', message: `소설 구조 분석 실패: ${errorMsg}` });
            setCharacterVoiceMatchingStatus({ status: 'skipped', message: '선행 작업(소설 구조 분석) 실패로 매칭을 건너뛰었습니다.' });
            setOverallError('소설 구조 분석 중 오류가 발생했습니다.');
          }
        } catch (charError) {
          console.error('Character analysis error:', charError);
          const errorMsg = charError.response?.data?.error || charError.message || '등장인물 분석 실패';
          setCharacterAnalysisStatus({ status: 'failure', message: `등장인물 분석 실패: ${errorMsg}` });
          setStructureAnalysisStatus({ status: 'skipped', message: '선행 작업(등장인물 분석) 실패로 구조 분석을 건너뛰었습니다.' });
          setCharacterVoiceMatchingStatus({ status: 'skipped', message: '선행 작업 실패로 매칭을 건너뛰었습니다.' });
          setOverallError('등장인물 분석 중 오류가 발생했습니다.');
        }
      } else {
        // uploadRes.data가 없거나 file_id가 없는 경우
        const errorMsg = uploadRes.data?.error || '파일 업로드 후 서버 응답이 올바르지 않습니다.';
        setFileStorageStatus({ status: 'failure', message: `파일 저장 실패: ${errorMsg}` });
        setCharacterAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 등장인물 분석을 건너뛰었습니다.' });
        setStructureAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 소설 구조 분석을 건너뛰었습니다.' });
        setCharacterVoiceMatchingStatus({ status: 'skipped', message: '파일 저장 실패로 매칭을 건너뛰었습니다.' });
        setOverallError(uploadRes.data?.error || '파일 업로드에 실패했습니다.');
      }
    } catch (uploadErr) {
      console.error('Upload error during file stage:', uploadErr);
      const errorMsg = uploadErr.response?.data?.error || uploadErr.message || '파일 업로드 중 알 수 없는 오류 발생';
      setFileStorageStatus({ status: 'failure', message: `파일 저장 실패: ${errorMsg}` });
      setCharacterAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 분석 작업을 건너뛰었습니다.' });
      setStructureAnalysisStatus({ status: 'skipped', message: '파일 저장 실패로 분석 작업을 건너뛰었습니다.' });
      setCharacterVoiceMatchingStatus({ status: 'skipped', message: '파일 저장 실패로 매칭을 건너뛰었습니다.' });
      setOverallError(errorMsg);
    }
  };

  const dropzoneStyle = {
    border: fileError ? '2px dashed red' : '2px dashed #ccc',
    borderRadius: '4px',
    padding: '20px',
    textAlign: 'center',
    cursor: 'pointer',
    marginBottom: '20px',
  };

  const renderMatchingResult = () => {
    if (!characterVoiceMap) return null;
    
    // 성우 ID로 성우 정보 찾기 함수
    const getActorNameById = (actorId) => {
      const actor = voiceActorList.find(actor => actor.id === actorId);
      return actor ? actor.name : actorId;
    };
    
    return (
      <div className="matching-result">
        <h3>등장인물-성우 매칭 결과</h3>
        <table>
          <thead>
            <tr>
              <th>등장인물</th>
              <th>성우</th>
              <th>특성</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(characterVoiceMap).map(([character, actorId]) => {
              const actor = voiceActorList.find(a => a.id === actorId);
              return (
                <tr key={character}>
                  <td>{character}</td>
                  <td>{actor ? actor.name : actorId}</td>
                  <td>{actor ? actor.feature : '정보 없음'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Upload TXT File for Audiobook Generation</h2>
      <div
        style={dropzoneStyle}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          onDrop(event.dataTransfer.files);
        }}
        onClick={() => document.getElementById('fileInput').click()} // Div 클릭 시 파일 입력창 열기
      >
        <input
          type="file"
          accept=".txt,text/plain"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          id="fileInput"
        />
        <p>Drag 'n' drop a .txt file here, or click to select a file.</p>
        <p style={{fontSize: '0.9em', color: 'gray'}}>Max file size: {MAX_FILE_SIZE_BYTES / (1024 * 1024)}MB</p>
      </div>
      
      {fileError && <p style={{ color: 'red' }}>{fileError}</p>}
      {selectedFile && !fileError && <p>Ready to upload: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)</p>}
      
      <button onClick={handleUpload} disabled={!selectedFile || fileStorageStatus.status === 'pending' || characterAnalysisStatus.status === 'pending' || structureAnalysisStatus.status === 'pending' || characterVoiceMatchingStatus.status === 'pending' }>
        Upload and Process
      </button>
      
      {uploadStatus && <p style={{ marginTop: '15px' }}>{uploadStatus}</p>}
      
      {uploadProgress > 0 && (
        <div style={{ width: '100%', backgroundColor: '#eee', borderRadius: '4px', marginTop: '10px', height: '24px' }}>
          <div
            style={{
              width: `${uploadProgress}%`,
              backgroundColor: '#4CAF50', // Green
              height: '100%',
              borderRadius: '4px',
              textAlign: 'center',
              color: 'white',
              lineHeight: '24px',
              transition: 'width 0.3s ease-in-out'
            }}
          >
            {uploadProgress}%
          </div>
        </div>
      )}

      <div className="processing-steps" style={{ marginTop: '20px' }}>
        {fileStorageStatus.status !== 'idle' && (
          <div className={`step ${fileStorageStatus.status}`}>
            <div className="step-title">
              <span className="step-number">1</span>
              <span className="step-name">파일 저장</span>
              <span className={`status-badge ${fileStorageStatus.status}`}>
                {fileStorageStatus.status === 'pending' ? '진행 중...' : 
                 fileStorageStatus.status === 'success' ? '완료' : '실패'}
              </span>
            </div>
            <div className="step-message">{fileStorageStatus.message}</div>
          </div>
        )}
        
        {characterAnalysisStatus.status !== 'idle' && (
          <div className={`step ${characterAnalysisStatus.status}`}>
            <div className="step-title">
              <span className="step-number">2</span>
              <span className="step-name">등장인물 분석</span>
              <span className={`status-badge ${characterAnalysisStatus.status}`}>
                {characterAnalysisStatus.status === 'pending' ? '진행 중...' : 
                 characterAnalysisStatus.status === 'success' ? '완료' : 
                 characterAnalysisStatus.status === 'skipped' ? '건너뜀' : '실패'}
              </span>
            </div>
            <div className="step-message">{characterAnalysisStatus.message}</div>
          </div>
        )}
        
        {structureAnalysisStatus.status !== 'idle' && (
          <div className={`step ${structureAnalysisStatus.status}`}>
            <div className="step-title">
              <span className="step-number">3</span>
              <span className="step-name">소설 구조 분석</span>
              <span className={`status-badge ${structureAnalysisStatus.status}`}>
                {structureAnalysisStatus.status === 'pending' ? '진행 중...' : 
                 structureAnalysisStatus.status === 'success' ? '완료' : 
                 structureAnalysisStatus.status === 'skipped' ? '건너뜀' : '실패'}
              </span>
            </div>
            <div className="step-message">{structureAnalysisStatus.message}</div>
          </div>
        )}
        
        {characterVoiceMatchingStatus.status !== 'idle' && (
          <div className={`step ${characterVoiceMatchingStatus.status}`}>
            <div className="step-title">
              <span className="step-number">4</span>
              <span className="step-name">등장인물-성우 매칭</span>
              <span className={`status-badge ${characterVoiceMatchingStatus.status}`}>
                {characterVoiceMatchingStatus.status === 'pending' ? '진행 중...' : 
                 characterVoiceMatchingStatus.status === 'success' ? '완료' : 
                 characterVoiceMatchingStatus.status === 'skipped' ? '건너뜀' : '실패'}
              </span>
            </div>
            <div className="step-message">{characterVoiceMatchingStatus.message}</div>
          </div>
        )}
      </div>
      
      {characterVoiceMatchingStatus.status === 'success' && renderMatchingResult()}
      
      {overallError && (
        <div className="error-message" style={{ marginTop: '20px', color: 'red' }}>
          {overallError}
        </div>
      )}
      
      {characterVoiceMatchingStatus.status === 'success' && currentFileId && (
        <div style={{ marginTop: '20px' }}>
          <button 
            onClick={() => { /* 구현 예정: 다음 단계로 이동 */ }}
            style={{ backgroundColor: '#4caf50', color: 'white', padding: '10px 20px' }}
          >
            오디오북 생성으로 이동
          </button>
        </div>
      )}
      
      <style jsx>{`
        .processing-steps {
          margin-top: 20px;
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        
        .step {
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 15px;
          background-color: #f9f9f9;
        }
        
        .step.success {
          border-color: #4caf50;
          background-color: rgba(76, 175, 80, 0.1);
        }
        
        .step.failure {
          border-color: #f44336;
          background-color: rgba(244, 67, 54, 0.1);
        }
        
        .step.pending {
          border-color: #2196f3;
          background-color: rgba(33, 150, 243, 0.1);
        }
        
        .step.skipped {
          border-color: #ff9800;
          background-color: rgba(255, 152, 0, 0.1);
        }
        
        .step-title {
          display: flex;
          align-items: center;
          margin-bottom: 5px;
        }
        
        .step-number {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          background-color: #666;
          color: white;
          border-radius: 50%;
          margin-right: 10px;
          font-size: 14px;
        }
        
        .step-name {
          font-weight: bold;
        }
        
        .status-badge {
          margin-left: auto;
          padding: 3px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: bold;
        }
        
        .status-badge.success {
          background-color: #4caf50;
          color: white;
        }
        
        .status-badge.failure {
          background-color: #f44336;
          color: white;
        }
        
        .status-badge.pending {
          background-color: #2196f3;
          color: white;
        }
        
        .status-badge.skipped {
          background-color: #ff9800;
          color: white;
        }
        
        .step-message {
          margin-top: 5px;
          font-size: 14px;
        }
        
        .matching-result {
          margin-top: 20px;
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 15px;
        }
        
        .matching-result h3 {
          margin-top: 0;
          margin-bottom: 15px;
        }
        
        .matching-result table {
          width: 100%;
          border-collapse: collapse;
        }
        
        .matching-result th, 
        .matching-result td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        
        .matching-result th {
          background-color: #f2f2f2;
        }
      `}</style>
    </div>
  );
}

export default FileUpload; 