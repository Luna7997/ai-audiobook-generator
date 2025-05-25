import axios from 'axios';

// API 서버 URL (환경 변수에서 가져오거나 기본값 사용)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// API 클라이언트 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 에러 헬퍼 함수 - 응답에서 에러 메시지와 코드 추출
const extractErrorInfo = (error) => {
  // 서버 응답이 있는 경우
  if (error.response && error.response.data) {
    const { error: errorMessage, error_code, message } = error.response.data;
    return {
      message: errorMessage || message || error.message || '알 수 없는 오류가 발생했습니다.',
      code: error_code || null,
      status: error.response.status,
      originalError: error
    };
  }
  
  // 서버 응답이 없는 경우 (네트워크 오류 등)
  return {
    message: error.message || '서버에 연결할 수 없습니다.',
    code: 'NETWORK_ERROR',
    status: 0,
    originalError: error
  };
};

// API 요청 함수들
const apiService = {
  // 서버 상태 확인
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('서버 상태 확인 실패:', error);
      throw extractErrorInfo(error);
    }
  },

  // 파일 업로드 함수
  uploadFile: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/upload/txt', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress, // Pass the progress callback to axios
      });
      return response; // Return the full response object
    } catch (error) {
      console.error('Error uploading file:', error);
      throw extractErrorInfo(error);
    }
  },

  // Gemini API로 등장인물 추출 (이 함수는 이제 직접 사용되지 않을 수 있음, 또는 내부적으로 /api/analyze/characters를 호출하도록 변경 가능)
  // 현재는 /api/extract_characters POST 라우트 (텍스트 직접 전달)를 호출하고 있음.
  // 새로운 흐름에서는 file_id 기반의 analyzeCharacters 함수를 사용.
  extractCharacters: async (text = null, fileId = null) => {
    if (!text && !fileId) {
      throw new Error('Either text or fileId must be provided for character extraction.');
    }
    try {
      const payload = {};
      if (text) {
        payload.text = text;
      } else if (fileId) {
        payload.file_id = fileId;
      }
      const response = await apiClient.post('/extract_characters', payload);
      return response.data;
    } catch (error) {
      console.error('등장인물 추출 요청 실패:', error);
      throw extractErrorInfo(error);
    }
  },

  // --- 새로운 API 호출 함수들 ---
  analyzeCharacters: async (fileId) => {
    try {
      const response = await apiClient.post(`/analyze/characters/${fileId}`);
      return response.data; // 성공 시 { message, file_id, analysis_file, model_info }
    } catch (error) {
      console.error(`Error analyzing characters for fileId ${fileId}:`, error);
      throw extractErrorInfo(error); // 에러 객체에는 response.data.error 등이 포함될 수 있음
    }
  },

  analyzeNovelStructure: async (fileId) => {
    try {
      const response = await apiClient.post(`/analyze/structure/${fileId}`);
      return response.data; // 성공 시 { message, file_id, analysis_file, model_info }
    } catch (error) {
      console.error(`Error analyzing novel structure for fileId ${fileId}:`, error);
      throw extractErrorInfo(error);
    }
  },

  getVoiceActors: async () => {
    try {
      const response = await apiClient.get('/voice_actors');
      return response.data;
    } catch (error) {
      console.error('성우 목록 조회 실패:', error);
      throw extractErrorInfo(error);
    }
  },
  
  // 등장인물과 성우 매칭 실행
  matchCharactersVoices: async (fileId) => {
    try {
      const response = await apiClient.post(`/match/characters_voices/${fileId}`);
      return response.data;
    } catch (error) {
      console.error(`등장인물-성우 매칭 실패 (fileId ${fileId}):`, error);
      throw extractErrorInfo(error);
    }
  },
  
  // 매칭 결과 조회
  getCharacterVoiceMapping: async (fileId) => {
    try {
      const response = await apiClient.get(`/match/characters_voices/${fileId}`);
      return response.data;
    } catch (error) {
      console.error(`등장인물-성우 매칭 결과 조회 실패 (fileId ${fileId}):`, error);
      throw extractErrorInfo(error);
    }
  },

  // 모든 처리된 텍스트의 메타데이터 조회
  getAllMetadata: async () => {
    try {
      const response = await apiClient.get('/metadata');
      return response.data;
    } catch (error) {
      console.error('모든 메타데이터 조회 실패:', error);
      throw extractErrorInfo(error);
    }
  },

  // 소설 파일 삭제
  deleteNovel: async (fileId) => {
    try {
      const response = await apiClient.delete(`/processed_texts/${fileId}`);
      return response.data;
    } catch (error) {
      console.error(`소설 파일 삭제 실패 (fileId ${fileId}):`, error);
      throw extractErrorInfo(error);
    }
  },

  // ElevenLabs 음성 목록 가져오기
  getElevenLabsVoices: async () => {
    try {
      const response = await apiClient.get('/elevenlabs/voices');
      return response.data;
    } catch (error) {
      console.error('ElevenLabs 음성 목록 가져오기 실패:', error);
      throw extractErrorInfo(error);
    }
  },

  // 오디오북 생성 요청
  generateAudiobook: async (fileId, options = {}) => {
    try {
      const response = await apiClient.post(`/audiobook/generate/${fileId}`, options);
      return response.data;
    } catch (error) {
      console.error(`오디오북 생성 요청 실패 (fileId: ${fileId}):`, error);
      throw extractErrorInfo(error);
    }
  },

  // 오디오북 생성 상태 확인
  getAudiobookStatus: async (fileId) => {
    try {
      const response = await apiClient.get(`/audiobook/status/${fileId}`);
      return response.data;
    } catch (error) {
      console.error(`오디오북 상태 확인 실패 (fileId: ${fileId}):`, error);
      throw extractErrorInfo(error);
    }
  },

  // 오디오 파일 URL 가져오기
  getAudioFileUrl: (fileId, segmentId) => {
    return `${apiClient.defaults.baseURL}/audiobook/files/${fileId}/${segmentId}`;
  }
};

export default apiService; 