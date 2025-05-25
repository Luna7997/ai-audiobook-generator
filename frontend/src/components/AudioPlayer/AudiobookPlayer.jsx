import React, { useState, useEffect, useRef } from 'react';
import apiService from '../../services/api';
import AudioControls from './AudioControls';
import SegmentList from './SegmentList';
import Button from '../UI/Button';
import StatusMessage from '../UI/StatusMessage';
import { useToast } from '../../contexts/ToastContext';

const AudiobookPlayer = ({ fileId, title, onBack }) => {
  const [audioSegments, setAudioSegments] = useState([]);
  const [currentSegment, setCurrentSegment] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [autoPlay, setAutoPlay] = useState(true);
  
  const toast = useToast();
  const audioRef = useRef(null);
  
  // 오디오북 상태 확인 및 데이터 로드 (컴포넌트 마운트 시 한 번만 실행)
  useEffect(() => {
    const fetchAudiobookStatus = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setStatusMessage('오디오북 상태 확인 중...');
        
        const statusData = await apiService.getAudiobookStatus(fileId);
        console.log('오디오북 상태 데이터:', statusData);
        
        // 응답에서 필요한 값 추출 (안전하게 기본값 제공)
        const { 
          status = 'not_started', 
          message = '', 
          generated_segments = 0, 
          total_segments = 0, 
          audio_files = [],
          segment_texts = {}
        } = statusData;
        
        console.log('세그먼트 텍스트:', segment_texts);
        
        // 생성 상태에 따른 처리
        if (status === 'not_started') {
          const msg = '이 소설의 오디오북이 아직 생성되지 않았습니다.';
          setStatusMessage(msg);
          toast.showInfo(msg, 'AUDIOBOOK_NOT_STARTED');
          setIsLoading(false);
          return;
        }

        // 오류 상태 처리 (반드시 세그먼트 처리보다 위에 위치)
        if (status === 'error') {
          setStatusMessage(message || '오디오북 생성 중 오류가 발생했습니다.');
          setError(message || '오디오북 생성 중 오류가 발생했습니다.');
          toast.showError(message || '오디오북 생성 중 오류가 발생했습니다.', 'AUDIOBOOK_GENERATION_ERROR');
          setIsLoading(false);
          return;
        }
        
        // 세그먼트 생성 여부 확인
        if (generated_segments === 0) {
          const msg = '오디오북 생성이 아직 완료되지 않았습니다. 잠시 후 다시 확인해주세요.';
          setStatusMessage(msg);
          toast.showInfo(msg, 'AUDIOBOOK_IN_PROGRESS');
          setIsLoading(false);
          return;
        }
        
        // 오디오 파일 배열 확인
        if (!audio_files || !Array.isArray(audio_files) || audio_files.length === 0) {
          const msg = '오디오북 파일 정보를 찾을 수 없습니다. 잠시 후 다시 시도해주세요.';
          setStatusMessage(msg);
          toast.showWarning(msg, 'AUDIOBOOK_FILES_NOT_FOUND');
          setIsLoading(false);
          return;
        }
        
        // 오디오 세그먼트 데이터 구성
        const segments = audio_files.map(filename => {
          const segmentNumber = parseInt(filename.split('.')[0]);
          return {
            id: segmentNumber,
            url: apiService.getAudioFileUrl(fileId, segmentNumber),
            order: segmentNumber,
            filename: filename,
            text: segment_texts?.[filename] || "대사 내용 없음"
          };
        }).sort((a, b) => a.order - b.order);
        
        setAudioSegments(segments);
        
        // 상태 및 완료 메시지 업데이트
        if (segments.length > 0) {
          setCurrentSegment(segments[0]);
          
          if (status === 'completed' || (total_segments > 0 && generated_segments >= total_segments)) {
            const completeMsg = `오디오북 생성 완료: ${segments.length}개 세그먼트`;
            setStatusMessage(completeMsg);
            // status가 completed일 때는 토스트 메시지를 표시하지 않음
          } else {
            const progressMsg = `오디오북 생성 중: ${segments.length}/${total_segments || '?'} 세그먼트 완료`;
            setStatusMessage(progressMsg);
            toast.showInfo(progressMsg, 'AUDIOBOOK_IN_PROGRESS');
          }
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('오디오북 상태 확인 오류:', error);
        const errorMsg = error.message || '오디오북 상태 확인 중 오류가 발생했습니다.';
        setError(errorMsg);
        toast.showError(errorMsg, error.code || 'AUDIOBOOK_STATUS_ERROR');
        setIsLoading(false);
      }
    };
    
    // 컴포넌트 마운트 시 한 번만 실행
    fetchAudiobookStatus();
    
    // 클린업 함수
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []); // 빈 의존성 배열 - 컴포넌트 마운트 시 한 번만 실행
  
  // fileId가 변경되면 상태 업데이트 (필요한 경우)
  useEffect(() => {
    if (fileId) {
      console.log('fileId 변경됨:', fileId);
      // 여기서는 API를 직접 호출하지 않고, 필요한 경우 페이지 새로고침으로 처리
    }
  }, [fileId]);
  
  // 오디오 플레이어 이벤트 핸들러
  useEffect(() => {
    const audioElement = audioRef.current;
    
    if (!audioElement || !currentSegment) return;
    
    const handleAudioEnded = () => {
      if (autoPlay && hasNextSegment()) {
        playNextSegment();
      } else {
        setIsPlaying(false);
      }
    };
    
    // 오디오 이벤트 리스너 설정
    audioElement.addEventListener('ended', handleAudioEnded);
    
    // 오디오 소스 변경 시 로드 및 자동 재생
    audioElement.src = currentSegment.url;
    audioElement.load();
    
    // 자동 재생 옵션이 활성화되고 플레이 중이면 로드 후 재생
    if (isPlaying) {
      const playPromise = audioElement.play();
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          console.error('오디오 재생 오류:', error);
          toast.showError('오디오 재생 중 오류가 발생했습니다. 다시 시도해주세요.', 'AUDIO_PLAYBACK_ERROR');
          setIsPlaying(false);
        });
      }
    }
    
    // 클린업 함수
    return () => {
      audioElement.removeEventListener('ended', handleAudioEnded);
    };
  }, [currentSegment, autoPlay, toast]);
  
  // 다음 세그먼트 여부 확인
  const hasNextSegment = () => {
    if (!currentSegment || audioSegments.length === 0) return false;
    return audioSegments.some(segment => segment.order > currentSegment.order);
  };
  
  // 이전 세그먼트 여부 확인
  const hasPrevSegment = () => {
    if (!currentSegment || audioSegments.length === 0) return false;
    return audioSegments.some(segment => segment.order < currentSegment.order);
  };
  
  // 재생/일시정지 토글
  const togglePlayPause = () => {
    if (!audioRef.current || !currentSegment) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      const playPromise = audioRef.current.play();
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          console.error('오디오 재생 오류:', error);
          toast.showError('오디오 재생 중 오류가 발생했습니다. 다시 시도해주세요.', 'AUDIO_PLAYBACK_ERROR');
        });
      }
    }
    
    setIsPlaying(!isPlaying);
  };
  
  // 다음 세그먼트 재생
  const playNextSegment = () => {
    if (!currentSegment || audioSegments.length === 0) return;
    
    const currentIndex = audioSegments.findIndex(segment => segment.id === currentSegment.id);
    if (currentIndex >= 0 && currentIndex < audioSegments.length - 1) {
      setCurrentSegment(audioSegments[currentIndex + 1]);
    }
  };
  
  // 이전 세그먼트 재생
  const playPrevSegment = () => {
    if (!currentSegment || audioSegments.length === 0) return;
    
    const currentIndex = audioSegments.findIndex(segment => segment.id === currentSegment.id);
    if (currentIndex > 0) {
      setCurrentSegment(audioSegments[currentIndex - 1]);
    }
  };
  
  // 특정 세그먼트 선택
  const selectSegment = (segment) => {
    setCurrentSegment(segment);
    if (!isPlaying) {
      setIsPlaying(true);
    }
  };
  
  // 자동 재생 토글
  const toggleAutoPlay = () => {
    setAutoPlay(!autoPlay);
    toast.showInfo(`자동 재생이 ${!autoPlay ? '활성화' : '비활성화'}되었습니다.`, 'AUTOPLAY_TOGGLE');
  };
  
  // 상태 수동 새로고침
  const handleRefreshStatus = async () => {
    try {
      setIsLoading(true);
      setStatusMessage('오디오북 상태 새로고침 중...');
      
      const statusData = await apiService.getAudiobookStatus(fileId);
      
      // 새로운 오디오 파일이 있는지 확인
      const newAudioFiles = statusData.audio_files || [];
      if (newAudioFiles.length > audioSegments.length) {
        // 새로운 세그먼트가 있으면 상태를 업데이트하기 위해 페이지를 새로고침
        window.location.reload();
        return;
      }
      
      toast.showInfo('최신 상태입니다.', 'REFRESH_STATUS');
      setIsLoading(false);
      setStatusMessage('오디오북 상태가 최신입니다.');
    } catch (error) {
      console.error('상태 새로고침 오류:', error);
      const errorMsg = error.message || '상태 새로고침 중 오류가 발생했습니다.';
      toast.showError(errorMsg, error.code || 'REFRESH_ERROR');
      setIsLoading(false);
    }
  };
  
  if (isLoading && audioSegments.length === 0) {
    return (
      <div className="container">
        <h2>{title}</h2>
        <p>오디오북 데이터를 불러오는 중...</p>
        <Button onClick={onBack} variant="secondary">뒤로 가기</Button>
        
        <style jsx>{`
          .container {
            text-align: center;
            padding: 20px;
          }
        `}</style>
      </div>
    );
  }
  
  return (
    <div className="container">
      <h2>{title} - 오디오북 플레이어</h2>
      
      {error ? (
        <StatusMessage type="error" message={error} />
      ) : statusMessage ? (
        <StatusMessage type="info" message={statusMessage} />
      ) : null}
      
      {audioSegments.length > 0 && currentSegment ? (
        <>
          <div className="player-wrapper">
            <audio 
              ref={audioRef} 
              controls 
              className="audio-player"
            >
              <source src={currentSegment.url} type="audio/mpeg" />
              브라우저가 오디오 재생을 지원하지 않습니다.
            </audio>
            
            <AudioControls 
              isPlaying={isPlaying}
              onPlayPause={togglePlayPause}
              onNext={playNextSegment}
              onPrev={playPrevSegment}
              hasNext={hasNextSegment()}
              hasPrev={hasPrevSegment()}
              autoPlay={autoPlay}
              onToggleAutoPlay={toggleAutoPlay}
            />
          </div>
          
          <div className="refresh-button" style={{ textAlign: 'center', marginBottom: '15px' }}>
            <Button 
              onClick={handleRefreshStatus} 
              variant="secondary"
              disabled={isLoading}
            >
              {isLoading ? '새로고침 중...' : '상태 새로고침'}
            </Button>
          </div>
          
          <SegmentList 
            segments={audioSegments}
            currentSegment={currentSegment}
            onSelectSegment={selectSegment}
          />
        </>
      ) : (
        <p>재생 가능한 오디오북 세그먼트가 없습니다.</p>
      )}
      
      <div className="back-button-container">
        <Button onClick={onBack} variant="secondary">목록으로 돌아가기</Button>
      </div>
      
      <style jsx>{`
        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          border-radius: 10px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          background-color: white;
        }
        
        h2 {
          text-align: center;
          margin-bottom: 20px;
        }
        
        .player-wrapper {
          padding: 15px;
          border-radius: 8px;
          background-color: #f8f9fa;
          margin-bottom: 20px;
        }
        
        .audio-player {
          width: 100%;
          margin-bottom: 10px;
        }
        
        .back-button-container {
          margin-top: 20px;
          text-align: center;
        }
      `}</style>
    </div>
  );
};

export default AudiobookPlayer; 