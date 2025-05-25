import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import { Button, StatusMessage, AudiobookPlayer } from '../components';
import { useToast } from '../contexts/ToastContext';

const AudiobookGenerationPage = () => {
  const [novels, setNovels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNovel, setSelectedNovel] = useState(null);
  const toast = useToast();
  
  // 오디오북 생성 관련 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [generationError, setGenerationError] = useState(null);

  // 소설 목록 불러오기
  const fetchNovels = async () => {
    try {
      setLoading(true);
      setGenerationStatus('');
      const metadata = await apiService.getAllMetadata();
      const novelList = Object.entries(metadata).map(([id, data]) => ({
        id,
        ...data,
      }));
      setNovels(novelList);
      setError(null);
    } catch (err) {
      console.error('Error fetching novels:', err);
      const errorMsg = err.message || '소설 목록을 불러오는 데 실패했습니다.';
      setError(errorMsg);
      setNovels([]);
      setGenerationStatus('소설 목록 로딩 실패');
      toast.showError(errorMsg, err.code || 'FETCH_ERROR');
    }
    setLoading(false);
  };

  // 컴포넌트 마운트 시 소설 목록 불러오기
  useEffect(() => {
    fetchNovels();
  }, []);

  // 소설 선택 핸들러
  const handleSelectNovel = (novel) => {
    setSelectedNovel(novel);
    setGenerationStatus('');
    setGenerationError(null);
  };

  // 오디오북 생성 요청
  const handleGenerateAudiobook = async () => {
    if (!selectedNovel) {
      const errorMsg = '오디오북을 생성할 소설을 선택해주세요.';
      setGenerationError(errorMsg);
      toast.showError(errorMsg, 'NOVEL_REQUIRED');
      return;
    }
    
    try {
      setIsGenerating(true);
      setGenerationError(null);
      setGenerationStatus('오디오북 생성 요청을 보내는 중...');
      
      // 오디오북 생성 API 호출
      const result = await apiService.generateAudiobook(selectedNovel.id, { force: false });
      
      // 이미 생성된 오디오북인 경우
      if (result.status && result.message && result.message.includes('이미 오디오북 생성이 진행 중이거나 완료되었습니다')) {
        const msg = '이미 오디오북이 생성되어 있습니다.';
        setGenerationStatus(msg);
        toast.showInfo(msg, 'AUDIOBOOK_EXISTS');
        setIsGenerating(false);
        return;
      }
      
      // 오디오북 생성 시작
      const msg = '오디오북 생성이 시작되었습니다. 이 과정은 몇 분 정도 소요될 수 있습니다.';
      setGenerationStatus(msg);
      toast.showSuccess(msg, 'AUDIOBOOK_STARTED');
      
      // 현재 상태 한 번 확인
      try {
        const statusResult = await apiService.getAudiobookStatus(selectedNovel.id);
        
        // 응답에서 필요한 값 추출
        const { status, generated_segments, total_segments } = statusResult;
        
        // 생성된 세그먼트가 있으면 진행 상태 표시
        if (generated_segments > 0) {
          if (status === 'completed' || (total_segments > 0 && generated_segments >= total_segments)) {
            const completeMsg = '오디오북 생성이 완료되었습니다!';
            setGenerationStatus(completeMsg);
            toast.showSuccess(completeMsg, 'AUDIOBOOK_COMPLETE');
          } else {
            const progressMsg = `오디오북 생성 중: ${generated_segments}/${total_segments || '?'} 세그먼트 완료`;
            setGenerationStatus(progressMsg);
            toast.showInfo(progressMsg, 'AUDIOBOOK_IN_PROGRESS');
          }
        }
      } catch (err) {
        // 상태 확인 실패해도 오류 메시지는 표시하지 않음
        console.error('오디오북 상태 확인 실패:', err);
      }
      
      setIsGenerating(false);
      
    } catch (err) {
      console.error('오디오북 생성 요청 실패:', err);
      
      // 사용자 친화적인 오류 메시지 표시
      let errorMessage = err.message || '오디오북 생성 중 오류가 발생했습니다.';
      
      // API 키 관련 오류 처리
      if (errorMessage.includes('API 키') || errorMessage.includes('API key')) {
        errorMessage = '오디오북 생성에 필요한 API 키가 설정되지 않았습니다. 관리자에게 문의하세요.';
      }
      
      setGenerationError(errorMessage);
      toast.showError(errorMessage, err.code || 'GENERATION_ERROR');
      setIsGenerating(false);
    }
  };
  
  // 오디오북 상태 확인
  const handleCheckStatus = async () => {
    if (!selectedNovel) {
      const errorMsg = '상태를 확인할 소설을 선택해주세요.';
      setGenerationError(errorMsg);
      toast.showError(errorMsg, 'NOVEL_REQUIRED');
      return;
    }
    
    try {
      setIsGenerating(true);
      setGenerationError(null);
      setGenerationStatus('오디오북 상태 확인 중...');
      
      const statusResult = await apiService.getAudiobookStatus(selectedNovel.id);
      
      // 응답에서 필요한 값 추출
      const { status, generated_segments, total_segments } = statusResult;
      
      // 생성 상태에 따른 메시지 표시
      if (status === 'not_started') {
        setGenerationStatus('이 소설의 오디오북이 아직 생성되지 않았습니다.');
        toast.showInfo('이 소설의 오디오북이 아직 생성되지 않았습니다.', 'AUDIOBOOK_NOT_STARTED');
      } else if (generated_segments === 0) {
        setGenerationStatus('오디오북 생성이 아직 시작되지 않았습니다.');
        toast.showInfo('오디오북 생성이 아직 시작되지 않았습니다.', 'AUDIOBOOK_NOT_STARTED');
      } else if (status === 'completed' || (total_segments > 0 && generated_segments >= total_segments)) {
        const completeMsg = `오디오북 생성이 완료되었습니다! (${generated_segments}개 세그먼트)`;
        setGenerationStatus(completeMsg);
        toast.showSuccess(completeMsg, 'AUDIOBOOK_COMPLETE');
      } else {
        const progressMsg = `오디오북 생성 중: ${generated_segments}/${total_segments || '?'} 세그먼트 완료`;
        setGenerationStatus(progressMsg);
        toast.showInfo(progressMsg, 'AUDIOBOOK_IN_PROGRESS');
      }
    } catch (err) {
      console.error('오디오북 상태 확인 실패:', err);
      const errorMsg = err.message || '오디오북 상태 확인 중 오류가 발생했습니다.';
      setGenerationError(`오류: ${errorMsg}`);
      toast.showError(errorMsg, err.code || 'STATUS_CHECK_ERROR');
    } finally {
      setIsGenerating(false);
    }
  };
  
  // 오디오북 플레이어 열기
  const openAudiobookPlayer = () => {
    if (!selectedNovel) {
      const errorMsg = '오디오북을 재생할 소설을 선택해주세요.';
      setGenerationError(errorMsg);
      toast.showError(errorMsg, 'NOVEL_REQUIRED');
      return;
    }
    
    setShowPlayer(true);
  };
  
  // 오디오북 플레이어 닫기
  const closeAudiobookPlayer = () => {
    setShowPlayer(false);
  };
  
  // 소설 삭제 기능
  const handleDeleteNovel = async () => {
    if (!selectedNovel) {
      const errorMsg = '삭제할 소설을 선택해주세요.';
      setGenerationError(errorMsg);
      toast.showError(errorMsg, 'NOVEL_REQUIRED');
      return;
    }
    
    // 사용자에게 삭제 확인
    const isConfirmed = window.confirm(`'${selectedNovel.original_filename}' 소설을 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`);
    
    if (!isConfirmed) {
      return; // 사용자가 취소함
    }
    
    try {
      setIsGenerating(true); // 삭제 중에도 버튼 비활성화
      setGenerationStatus(`'${selectedNovel.original_filename}' 삭제 중...`);
      
      // API 호출하여 소설 삭제
      const result = await apiService.deleteNovel(selectedNovel.id);
      
      const successMsg = `'${selectedNovel.original_filename}' 삭제 완료`;
      setGenerationStatus(successMsg);
      toast.showSuccess(successMsg, 'NOVEL_DELETED');
      setSelectedNovel(null); // 선택 초기화
      
      // 소설 목록 다시 불러오기
      await fetchNovels();
    } catch (err) {
      console.error('소설 삭제 실패:', err);
      const errorMsg = err.message || `소설 삭제에 실패했습니다.`;
      setGenerationError(`오류: ${errorMsg}`);
      toast.showError(errorMsg, err.code || 'DELETE_ERROR');
    } finally {
      setIsGenerating(false);
    }
  };

  // 오디오북 플레이어가 활성화된 경우 표시
  if (showPlayer && selectedNovel) {
    return (
      <AudiobookPlayer 
        fileId={selectedNovel.id}
        title={selectedNovel.original_filename}
        onBack={closeAudiobookPlayer}
      />
    );
  }

  return (
    <div className="container">
      <h1>오디오북 생성</h1>
      <p className="description">
        업로드된 소설에서 오디오북을 생성하고 재생합니다.
      </p>
      
      {loading && novels.length === 0 ? (
        <p className="loading-message">소설 목록을 불러오는 중...</p>
      ) : error && novels.length === 0 ? (
        <StatusMessage type="error" message={error} />
      ) : novels.length === 0 ? (
        <div className="empty-state">
          <p>업로드된 소설이 없습니다.</p>
          <Button 
            onClick={() => window.location.href = '/upload'} 
            variant="primary"
          >
            소설 업로드 페이지로 이동
          </Button>
        </div>
      ) : (
        <>
          <div className="novels-container">
            <h2>업로드된 소설 목록</h2>
            <div className="novels-list">
              {novels.map(novel => (
                <div 
                  key={novel.id}
                  className={`novel-item ${selectedNovel?.id === novel.id ? 'selected' : ''}`}
                  onClick={() => handleSelectNovel(novel)}
                >
                  <div className="novel-info">
                    <h3 className="novel-title">{novel.original_filename}</h3>
                    <p className="novel-meta">
                      업로드: {new Date(novel.upload_time).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {selectedNovel && (
            <div className="action-panel">
              <h3>선택된 소설: {selectedNovel.original_filename}</h3>
              
              {generationError && (
                <StatusMessage type="error" message={generationError} />
              )}
              
              {generationStatus && (
                <StatusMessage type="info" message={generationStatus} />
              )}
              
              <div className="action-buttons">
                <Button 
                  onClick={handleGenerateAudiobook} 
                  disabled={isGenerating}
                  variant="primary"
                >
                  {isGenerating ? '처리 중...' : '오디오북 생성'}
                </Button>
                
                <Button 
                  onClick={handleCheckStatus} 
                  disabled={isGenerating}
                  variant="secondary"
                >
                  상태 확인
                </Button>
                
                <Button 
                  onClick={openAudiobookPlayer} 
                  disabled={isGenerating}
                  variant="success"
                >
                  오디오북 재생
                </Button>
                
                <Button 
                  onClick={handleDeleteNovel} 
                  disabled={isGenerating}
                  variant="danger"
                >
                  소설 삭제
                </Button>
              </div>
            </div>
          )}
        </>
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
        
        .loading-message {
          text-align: center;
          padding: 2rem;
          color: #666;
        }
        
        .empty-state {
          text-align: center;
          padding: 2rem;
          background-color: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 2rem;
        }
        
        .novels-container {
          margin-bottom: 2rem;
        }
        
        .novels-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 1rem;
        }
        
        .novel-item {
          padding: 1rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .novel-item:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .novel-item.selected {
          border-color: #4a90e2;
          background-color: #f0f7ff;
        }
        
        .novel-title {
          margin: 0 0 0.5rem 0;
          font-size: 1.1rem;
        }
        
        .novel-meta {
          margin: 0;
          font-size: 0.9rem;
          color: #666;
        }
        
        .action-panel {
          background: #f9f9fa;
          border-radius: 8px;
          padding: 1.5rem;
          margin-bottom: 1.5rem;
        }
        
        .action-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          justify-content: center;
          margin-top: 1.5rem;
        }
        
        @media (max-width: 600px) {
          .action-buttons {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default AudiobookGenerationPage; 