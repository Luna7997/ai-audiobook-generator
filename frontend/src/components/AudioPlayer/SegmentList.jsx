import React from 'react';

const SegmentList = ({ segments, currentSegment, onSelectSegment }) => {
  // 세그먼트 파일명에서 확장자를 제거하고 표시
  const getDisplayFilename = (filename) => {
    return filename ? filename.split('.')[0] : '';
  };

  return (
    <div className="segments-container">
      <h3>오디오북 세그먼트</h3>
      <div className="segments-list">
        {segments.length === 0 ? (
          <p className="no-segments">재생 가능한 세그먼트가 없습니다.</p>
        ) : (
          segments.map((segment) => (
            <div
              key={segment.id}
              className={`segment-item ${currentSegment && currentSegment.id === segment.id ? 'active' : ''}`}
              onClick={() => onSelectSegment(segment)}
            >
              <div className="segment-info">
                <span className="segment-filename">세그먼트 {getDisplayFilename(segment.filename)}</span>
                <span>{Math.floor(segment.duration || 0)}초</span>
              </div>
              <p className="segment-text">{segment.text}</p>
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .segments-container {
          margin-top: 20px;
        }
        
        h3 {
          margin-bottom: 10px;
          font-size: 18px;
        }
        
        .segments-list {
          max-height: 300px;
          overflow-y: auto;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          padding: 10px;
        }
        
        .segment-item {
          padding: 8px 12px;
          margin: 4px 0;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        
        .segment-item:hover {
          background-color: #f5f5f5;
        }
        
        .segment-item.active {
          background-color: #e6f7ff;
          border-left: 3px solid #1890ff;
        }
        
        .segment-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 14px;
        }
        
        .segment-filename {
          font-weight: bold;
        }
        
        .segment-text {
          margin-top: 4px;
          font-size: 13px;
          color: #555;
        }
        
        .no-segments {
          text-align: center;
          color: #999;
          padding: 20px;
        }
      `}</style>
    </div>
  );
};

export default SegmentList; 