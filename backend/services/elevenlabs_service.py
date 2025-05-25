import requests
import time
import json
import os
from datetime import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 설정
from services.text_storage_service import BASE_STORAGE_PATH

# 오디오 파일 저장 경로
AUDIO_OUTPUT_FOLDER = os.path.join(BASE_STORAGE_PATH, 'audio_output')
if not os.path.exists(AUDIO_OUTPUT_FOLDER):
    os.makedirs(AUDIO_OUTPUT_FOLDER, exist_ok=True)

# API 키 로드
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# API 헤더
HEADERS = {
    'xi-api-key': ELEVENLABS_API_KEY,
    'Content-Type': 'application/json'
}

# 로깅 설정
logger = logging.getLogger(__name__)

# 감정 설정 프리셋 (음성 설정)
EMOTION_PRESETS = {
    "화남": {
        "stability": 0.3,      # 불안정한 감정
        "similarity_boost": 0.4,  # 자유로운 표현
        "style": 0.9,         # 매우 강한 감정
        "use_speaker_boost": True,
        "speed": 1.1          # 약간 빠른 속도
    },
    "행복": {
        "stability": 0.4,      # 약간 불안정한 감정
        "similarity_boost": 0.5,  # 중간 유사도
        "style": 0.8,         # 강한 감정
        "use_speaker_boost": True,
        "speed": 1.1          # 약간 빠른 속도
    },
    "슬픔": {
        "stability": 0.6,      # 중간 안정성
        "similarity_boost": 0.6,  # 중간 유사도
        "style": 0.7,         # 강한 감정
        "use_speaker_boost": True,
        "speed": 0.9          # 약간 느린 속도
    },
    "기쁨": {
        "stability": 0.3,      # 불안정한 감정
        "similarity_boost": 0.4,  # 자유로운 표현
        "style": 0.9,         # 매우 강한 감정
        "use_speaker_boost": True,
        "speed": 1.2          # 빠른 속도
    },
    "지루함": {
        "stability": 0.9,      # 매우 안정적
        "similarity_boost": 0.8,  # 높은 유사도
        "style": 0.2,         # 약한 감정
        "use_speaker_boost": True,
        "speed": 0.8          # 느린 속도
    },
    "중립": {
        "stability": 0.7,      # 중간 안정성
        "similarity_boost": 0.7,  # 중간 유사도
        "style": 0.5,         # 중간 감정
        "use_speaker_boost": True,
        "speed": 1.0          # 기본 속도
    },
    "분노": {
        "stability": 0.2,      # 매우 불안정한 감정
        "similarity_boost": 0.3,  # 자유로운 표현
        "style": 0.95,        # 매우 강한 감정
        "use_speaker_boost": True,
        "speed": 1.2          # 빠른 속도
    },
    "놀람": {
        "stability": 0.4,      # 불안정한 감정
        "similarity_boost": 0.5,  # 중간 유사도
        "style": 0.8,         # 강한 감정
        "use_speaker_boost": True,
        "speed": 1.1          # 약간 빠른 속도
    }
}

def check_api_key():
    """API 키가 설정되어 있는지 확인합니다."""
    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY is not set in environment variables")
        return False
    return True

def get_available_voices():
    """ElevenLabs에서 사용 가능한 모든 음성 목록을 가져옵니다."""
    if not check_api_key():
        return {"error": "API key is not configured"}, 500
    
    try:
        response = requests.get('https://api.elevenlabs.io/v1/voices', headers=HEADERS)
        response.raise_for_status()
        voices_data = response.json()
        
        # 모든 음성 정보 반환 (필터링 없이)
        return {"success": True, "voices": voices_data.get('voices', [])}, 200
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting voices from ElevenLabs API: {e}")
        return {"error": f"Failed to fetch voices: {str(e)}"}, 500

def get_emotion_settings(emotion_type="중립", tone="일반", expression_level=0.5):
    """감정 유형, 톤, 표현 수준에 따른 음성 설정을 반환합니다."""
    # 기본 감정 설정 가져오기
    settings = EMOTION_PRESETS.get(emotion_type, EMOTION_PRESETS["중립"]).copy()
    
    # 톤에 따른 추가 조정
    if tone == "격앙됨":
        settings["stability"] *= 0.8
        settings["style"] = min(1.0, settings["style"] * 1.2)
        settings["speed"] = min(1.2, settings["speed"] * 1.1)
    elif tone == "차분함":
        settings["stability"] = min(1.0, settings["stability"] * 1.2)
        settings["style"] *= 0.8
        settings["speed"] *= 0.9
    
    # 표현 수준에 따른 미세 조정 (0~1 사이 값)
    if 0 <= expression_level <= 1:
        # 표현 수준이 높을수록 style 값을 높임
        settings["style"] = min(1.0, settings["style"] * (0.7 + 0.3 * expression_level))
        # 표현 수준이 높을수록 stability를 낮춤
        settings["stability"] = max(0.1, settings["stability"] * (1.0 - 0.3 * expression_level))
    
    return settings

def generate_speech(voice_id, text, emotion_settings=None):
    """주어진 음성 ID와 텍스트, 감정 설정으로 음성을 생성합니다."""
    if not check_api_key():
        return {"error": "API key is not configured"}, 500
    
    if not voice_id:
        return {"error": "Voice ID is required"}, 400
        
    if not text or not text.strip():
        return {"error": "Text is required and cannot be empty"}, 400
    
    # 기본 감정 설정 사용 (중립)
    if emotion_settings is None:
        emotion_settings = EMOTION_PRESETS["중립"]
    
    try:
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        data = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {
                'stability': emotion_settings.get('stability', 0.7),
                'similarity_boost': emotion_settings.get('similarity_boost', 0.7),
                'style': emotion_settings.get('style', 0.5),
                'use_speaker_boost': emotion_settings.get('use_speaker_boost', True),
                'speed': emotion_settings.get('speed', 1.0)
            }
        }
        
        response = requests.post(url, headers=HEADERS, json=data)
        
        if not response.ok:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return {"error": f"ElevenLabs API error: {response.status_code} - {response.text}"}, response.status_code
        
        return {"success": True, "audio_data": response.content}, 200
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting speech synthesis: {e}")
        return {"error": f"Failed to generate speech: {str(e)}"}, 500

def save_audio_file(audio_data, file_id, segment_order):
    """생성된 오디오 데이터를 파일로 저장합니다."""
    try:
        # 파일 ID별 디렉토리 생성
        output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # 파일명 생성 (3자리 숫자 형식으로 순서 표시)
        output_file = os.path.join(output_dir, f"{int(segment_order):03d}.mp3")
        
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Audio file saved: {output_file}")
        return {"success": True, "file_path": output_file}, 200
        
    except Exception as e:
        logger.error(f"Error saving audio file: {e}")
        return {"error": f"Failed to save audio file: {str(e)}"}, 500

def get_audio_file_path(file_id, segment_order):
    """특정 파일 ID와 세그먼트 순서에 해당하는 오디오 파일 경로를 반환합니다."""
    output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
    output_file = os.path.join(output_dir, f"{int(segment_order):03d}.mp3")
    
    if os.path.exists(output_file):
        return {"success": True, "file_path": output_file}, 200
    else:
        return {"error": "Audio file not found"}, 404

def generate_audiobook_segment(file_id, segment_data):
    """
    단일 오디오북 세그먼트(문장/대사)를 생성합니다.
    
    Args:
        file_id (str): 원본 소설 파일 ID
        segment_data (dict): 세그먼트 데이터 (order, speaker, text, emotion 등 포함)
    
    Returns:
        dict: 성공/실패 여부와 관련 메시지
    """
    try:
        order = segment_data.get("order")
        speaker = segment_data.get("speaker")
        text = segment_data.get("text")
        emotion = segment_data.get("emotion", "중립")
        tone = segment_data.get("tone", "일반")
        expression_level = segment_data.get("expression_level", 0.5)
        voice_id = segment_data.get("voice_id")
        
        # 필수 데이터 검증
        if not all([order is not None, speaker, text, voice_id]):
            missing_fields = []
            if order is None:
                missing_fields.append("order")
            if not speaker:
                missing_fields.append("speaker")
            if not text:
                missing_fields.append("text")
            if not voice_id:
                missing_fields.append("voice_id")
                
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400
        
        # 감정 설정 가져오기
        emotion_settings = get_emotion_settings(emotion, tone, expression_level)
        
        # 음성 생성
        speech_result, status_code = generate_speech(voice_id, text, emotion_settings)
        
        if status_code != 200:
            return speech_result, status_code
        
        # 오디오 파일 저장
        save_result, save_status = save_audio_file(speech_result["audio_data"], file_id, order)
        
        if save_status != 200:
            return save_result, save_status
        
        return {
            "success": True, 
            "message": f"Audio segment {order} generated successfully", 
            "file_path": save_result["file_path"],
            "segment_order": order,
            "speaker": speaker
        }, 200
        
    except Exception as e:
        logger.error(f"Error generating audiobook segment: {e}")
        return {"error": f"Failed to generate audiobook segment: {str(e)}"}, 500

def generate_complete_audiobook(file_id, story_data):
    """
    소설 전체 오디오북을 생성합니다.
    
    Args:
        file_id (str): 원본 소설 파일 ID
        story_data (dict): 소설 구조 및 음성 매핑 데이터
    
    Returns:
        dict: 성공/실패 여부와 관련 메시지
    """
    try:
        # story_data 구조 검증
        if not isinstance(story_data, dict):
            return {"error": "Invalid story data format. Expected a dictionary."}, 400
        
        character_voice_map = story_data.get("character_voice_map", {})
        story_items = story_data.get("story_items", [])
        
        if not story_items:
            return {"error": "No story items found in the provided data."}, 400
        
        # 생성 결과 저장할 리스트
        generation_results = []
        failed_segments = []
        
        # 진행 상태 초기화
        total_segments = len(story_items)
        processed_segments = 0
        
        # 총 세그먼트 수 정보를 저장할 디렉토리 생성
        output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # 총 세그먼트 수 정보를 파일로 저장
        info_file = os.path.join(output_dir, "audiobook_info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_segments": total_segments,
                "start_time": datetime.now().isoformat()
            }, f)
        
        # 각 세그먼트 처리
        for item in story_items:
            order = item.get("order")
            speaker = item.get("speaker")
            text = item.get("text")
            emotion = item.get("emotion", "중립")
            tone = item.get("tone", "일반")
            
            # voice_id 할당
            voice_id = character_voice_map.get(speaker)
            if not voice_id:
                logger.warning(f"No voice ID found for speaker '{speaker}'. This segment will be skipped.")
                failed_segments.append({"order": order, "speaker": speaker, "reason": "No voice ID assigned"})
                processed_segments += 1
                continue
            
            # 세그먼트 데이터 구성
            segment_data = {
                "order": order,
                "speaker": speaker,
                "text": text,
                "emotion": emotion,
                "tone": tone,
                "voice_id": voice_id
            }
            
            # 세그먼트 생성
            result, status_code = generate_audiobook_segment(file_id, segment_data)
            
            if status_code == 200:
                generation_results.append({
                    "order": order,
                    "speaker": speaker,
                    "status": "success",
                    "file_path": result.get("file_path")
                })
            else:
                failed_segments.append({
                    "order": order,
                    "speaker": speaker,
                    "status": "failed",
                    "reason": result.get("error", "Unknown error")
                })
            
            processed_segments += 1
            
            # API 호출 간 딜레이 (0.3초)
            if processed_segments < total_segments:
                time.sleep(0.3)
        
        # 처리 결과 반환
        success_count = len(generation_results)
        failed_count = len(failed_segments)
        
        return {
            "success": True,
            "message": f"Audiobook generation completed. {success_count} segments successful, {failed_count} segments failed.",
            "file_id": file_id,
            "total_segments": total_segments,
            "successful_segments": success_count,
            "failed_segments": failed_count,
            "generation_results": generation_results,
            "failed_details": failed_segments
        }, 200
        
    except Exception as e:
        logger.error(f"Error generating complete audiobook: {e}")
        return {"error": f"Failed to generate complete audiobook: {str(e)}"}, 500

def check_generation_status(file_id):
    """
    특정 소설의 오디오북 생성 상태를 확인합니다.
    
    Args:
        file_id (str): 원본 소설 파일 ID
    
    Returns:
        dict: 생성 상태 정보
        int: HTTP 상태 코드
    """
    try:
        output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
        total_segments = 0

        response = {
            "file_id": file_id,
            "status": "not_started",
            "message": "Audiobook generation has not been started for this file.",
            "total_segments": 0,
            "generated_segments": 0,
            "audio_files": []
        }

        if not os.path.exists(output_dir):
            return response, 200

        audio_files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
        generated_count = len(audio_files)

        info_file = os.path.join(output_dir, "audiobook_info.json")
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info_data = json.load(f)
                    total_segments = info_data.get("total_segments", 0)
            except Exception as e:
                logger.error(f"Error reading audiobook info file: {e}")

        # 파일명(정수) 오름차순 정렬
        file_numbers = sorted([int(f.split('.')[0]) for f in audio_files if f.split('.')[0].isdigit()])
        error_in_sequence = False
        for idx, num in enumerate(file_numbers):
            if num != idx + 1:
                error_in_sequence = True
                break

        if generated_count == 0:
            status = "in_progress"
            message = "Audiobook generation has started but no segments have been generated yet."
        elif error_in_sequence:
            status = "error"
            message = "오디오북 생성 중 오류가 발생했습니다. 일부 세그먼트가 누락되었습니다. (파일 번호 불일치)"
        elif total_segments > 0 and generated_count >= total_segments:
            status = "completed"
            message = f"Audiobook generation completed. All {total_segments} segments have been generated."
        else:
            status = "in_progress"
            message = f"{generated_count} audio segments have been generated."
            if total_segments > 0:
                message += f" Progress: {generated_count}/{total_segments} segments."

        return {
            "file_id": file_id,
            "status": status,
            "message": message,
            "total_segments": total_segments,
            "generated_segments": generated_count,
            "audio_files": sorted(audio_files)
        }, 200

    except Exception as e:
        logger.error(f"Error checking audiobook generation status: {e}")
        return {
            "file_id": file_id,
            "status": "error",
            "message": f"Failed to check audiobook generation status: {str(e)}",
            "total_segments": 0,
            "generated_segments": 0,
            "audio_files": []
        }, 500