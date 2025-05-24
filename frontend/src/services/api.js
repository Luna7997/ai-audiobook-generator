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

// API 요청 함수들
export const apiService = {
  // 서버 상태 확인
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('서버 상태 확인 실패:', error);
      throw error;
    }
  },
  
  // Gemini API로 텍스트 생성
  generateText: async (prompt, systemInstruction = null) => {
    try {
      const response = await apiClient.post('/gemini/generate', {
        prompt,
        system_instruction: systemInstruction
      });
      return response.data;
    } catch (error) {
      console.error('텍스트 생성 요청 실패:', error);
      throw error;
    }
  },

  // New function for file upload
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
      throw error;
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
      throw error;
    }
  },

  // --- 새로운 API 호출 함수들 ---
  analyzeCharactersById: async (fileId) => {
    try {
      const response = await apiClient.post(`/analyze/characters/${fileId}`);
      return response.data; // 성공 시 { message, file_id, analysis_file, model_info }
    } catch (error) {
      console.error(`Error analyzing characters for fileId ${fileId}:`, error);
      throw error; // 에러 객체에는 response.data.error 등이 포함될 수 있음
    }
  },

  analyzeNovelStructureById: async (fileId) => {
    try {
      const response = await apiClient.post(`/analyze/structure/${fileId}`);
      return response.data; // 성공 시 { message, file_id, analysis_file, model_info }
    } catch (error) {
      console.error(`Error analyzing novel structure for fileId ${fileId}:`, error);
      throw error;
    }
  },
  // --- --- ---

  // --- 인물-성우 매칭 관련 함수 추가 ---
  
  // 사용 가능한 성우 목록 조회
  getVoiceActors: async () => {
    try {
      const response = await apiClient.get('/voice_actors');
      return response.data;
    } catch (error) {
      console.error('성우 목록 조회 실패:', error);
      throw error;
    }
  },
  
  // 등장인물과 성우 매칭 실행
  matchCharactersVoices: async (fileId) => {
    try {
      const response = await apiClient.post(`/match/characters_voices/${fileId}`);
      return response.data;
    } catch (error) {
      console.error(`등장인물-성우 매칭 실패 (fileId ${fileId}):`, error);
      throw error;
    }
  },
  
  // 매칭 결과 조회
  getCharacterVoiceMapping: async (fileId) => {
    try {
      const response = await apiClient.get(`/match/characters_voices/${fileId}`);
      return response.data;
    } catch (error) {
      console.error(`등장인물-성우 매칭 결과 조회 실패 (fileId ${fileId}):`, error);
      throw error;
    }
  }
};

export default apiService; 