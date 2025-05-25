import React from 'react';
import Button from '../UI/Button';

const AudioControls = ({ 
  isPlaying, 
  onPlayPause, 
  onNext, 
  onPrev, 
  hasNext, 
  hasPrev,
  autoPlay,
  onToggleAutoPlay
}) => {
  return (
    <div className="controls-wrapper">
      <Button 
        onClick={onPrev} 
        disabled={!hasPrev}
        variant="secondary"
      >
        이전
      </Button>
      
      <Button 
        onClick={onPlayPause}
        variant="primary"
      >
        {isPlaying ? '일시정지' : '재생'}
      </Button>
      
      <Button 
        onClick={onNext} 
        disabled={!hasNext}
        variant="secondary"
      >
        다음
      </Button>
      
      <label className="autoplay-toggle">
        <input 
          type="checkbox" 
          checked={autoPlay} 
          onChange={onToggleAutoPlay} 
        />
        자동 재생
      </label>
      
      <style jsx>{`
        .controls-wrapper {
          display: flex;
          justify-content: center;
          gap: 15px;
          margin: 15px 0;
          align-items: center;
        }
        
        .autoplay-toggle {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 14px;
          cursor: pointer;
          user-select: none;
        }
      `}</style>
    </div>
  );
};

export default AudioControls; 