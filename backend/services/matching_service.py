import os
import json
import logging
from pathlib import Path

from services.text_storage_service import get_metadata
from services.gemini_service import match_characters_with_voice_actors

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 기본 경로 설정
BASE_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHARACTER_ANALYSIS_PATH = BASE_PATH / 'app_data' / 'character_analysis'
NOVELS_PROCESSED_PATH = BASE_PATH / 'app_data' / 'novels_processed'
NOVELS_MATCHED_PATH = BASE_PATH / 'app_data' / 'novels_matched'
ACTOR_LIST_PATH = BASE_PATH / 'app_data' / 'actor_list.json'

# novels_matched 폴더가 없는 경우 생성
if not os.path.exists(NOVELS_MATCHED_PATH):
    os.makedirs(NOVELS_MATCHED_PATH)
    logger.info(f"novels_matched 폴더 생성: {NOVELS_MATCHED_PATH}")

# --- voice_actor_service에서 통합된 함수들 ---

def load_voice_actors():
    """
    성우 목록을 JSON 파일에서 로드하여 반환합니다.
    
    Returns:
        list: 성우 정보 객체의 리스트 (없으면 빈 리스트)
    """
    try:
        if not os.path.exists(ACTOR_LIST_PATH):
            logger.error(f"성우 목록 파일이 존재하지 않습니다: {ACTOR_LIST_PATH}")
            return []
            
        with open(ACTOR_LIST_PATH, 'r', encoding='utf-8') as f:
            voice_actors = json.load(f)
            
        logger.info(f"{len(voice_actors)}명의 성우 데이터를 로드했습니다.")
        return voice_actors
    except json.JSONDecodeError as e:
        logger.error(f"성우 데이터 파싱 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"성우 데이터 로드 중 오류 발생: {e}")
        return []

# --- 기존 함수들 ---

def load_character_analysis(file_id):
    """
    특정 소설의 등장인물 분석 결과를 로드합니다.
    
    Args:
        file_id (str): 소설 파일 ID
        
    Returns:
        list: 등장인물 정보 객체의 리스트 (없으면 빈 리스트)
    """
    try:
        # 등장인물 분석 파일 경로 생성
        character_file_path = CHARACTER_ANALYSIS_PATH / f"{file_id}_characters.json"
        
        if not os.path.exists(character_file_path):
            logger.error(f"등장인물 분석 파일이 존재하지 않습니다: {character_file_path}")
            return []
            
        with open(character_file_path, 'r', encoding='utf-8') as f:
            characters = json.load(f)
            
        logger.info(f"{len(characters)}명의 등장인물 데이터를 로드했습니다.")
        return characters
    except json.JSONDecodeError as e:
        logger.error(f"등장인물 데이터 파싱 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"등장인물 데이터 로드 중 오류 발생: {e}")
        return []


def load_structure_analysis(file_id):
    """
    특정 소설의 구조 분석 결과를 로드합니다.
    
    Args:
        file_id (str): 소설 파일 ID
        
    Returns:
        list: 소설 구조 분석 객체의 리스트 (없으면 빈 리스트)
    """
    try:
        # 소설 구조 분석 파일 경로 생성
        structure_file_path = NOVELS_PROCESSED_PATH / f"{file_id}_structure.json"
        
        if not os.path.exists(structure_file_path):
            logger.error(f"소설 구조 분석 파일이 존재하지 않습니다: {structure_file_path}")
            return []
            
        with open(structure_file_path, 'r', encoding='utf-8') as f:
            structure_data = json.load(f)
            
        logger.info(f"소설 구조 분석 데이터를 로드했습니다. 항목 수: {len(structure_data)}")
        return structure_data
    except json.JSONDecodeError as e:
        logger.error(f"소설 구조 분석 데이터 파싱 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"소설 구조 분석 데이터 로드 중 오류 발생: {e}")
        return []


def match_with_gemini(characters, voice_actors, file_id=None, model_name: str = "gemini-2.0-flash", temperature: float = 0.1):
    """
    Gemini API를 사용하여 등장인물과 성우를 매칭합니다.
    
    Args:
        characters (list): 등장인물 정보 리스트
        voice_actors (list): 성우 정보 리스트
        file_id (str, optional): 소설 파일 ID
        model_name (str, optional): 사용할 모델의 이름입니다. Defaults to "gemini-2.0-flash".
        temperature (float, optional): 생성 시 샘플링 온도로, 0과 1 사이의 값입니다. Defaults to 0.1.
        
    Returns:
        dict: 등장인물 이름과 성우 ID 매핑 딕셔너리
    """
    character_voice_map = {}
    
    try:
        # gemini_service.py의 함수를 호출하여 매칭 수행
        logger.info("Gemini API 호출: 등장인물-성우 매칭")
        character_voice_map = match_characters_with_voice_actors(
            characters, 
            voice_actors,
            file_id,
            model_name,
            temperature
        )
        logger.info(f"등장인물-성우 매칭 성공: {len(character_voice_map)} 매핑")
            
    except Exception as e:
        logger.error(f"Gemini를 사용한 매칭 중 오류 발생: {str(e)}")
        # 오류 발생 시 빈 매핑 반환
    
    return character_voice_map


def match_characters_with_voices(file_id):
    """
    등장인물과 성우를 매칭합니다. Gemini API를 사용해 매칭합니다.
    
    Args:
        file_id (str): 소설 파일 ID
        
    Returns:
        dict: 매칭 결과 및 상태
    """
    try:
        # 1. 등장인물 분석 로드
        characters = load_character_analysis(file_id)
        if not characters:
            return {"success": False, "error": "등장인물 분석 데이터를 불러오지 못했습니다."}
        
        # 2. 성우 데이터 로드
        voice_actors = load_voice_actors()
        if not voice_actors:
            return {"success": False, "error": "성우 데이터를 불러오지 못했습니다."}
        
        # 3. 소설 구조 분석 로드
        structure_data = load_structure_analysis(file_id)
        if not structure_data:
            return {"success": False, "error": "소설 구조 분석 데이터를 불러오지 못했습니다."}
        
        # 4. 캐릭터-성우 매칭 (Gemini API 사용)
        character_voice_map = match_with_gemini(characters, voice_actors, file_id)
        
        # 5. 결과 데이터 생성
        result_data = {
            "character_voice_map": character_voice_map,
            "story_items": structure_data
        }
        
        # 6. 결과 저장
        save_result = save_matching_result(file_id, result_data)
        if not save_result.get("success"):
            return {"success": False, "error": save_result.get("error")}
        
        return {
            "success": True, 
            "message": "등장인물-성우 매칭이 완료되었습니다.",
            "file_id": file_id,
            "matching_file": save_result.get("matching_file"),
            "character_voice_map": character_voice_map
        }
        
    except Exception as e:
        logger.error(f"등장인물-성우 매칭 중 오류 발생: {e}")
        return {"success": False, "error": f"매칭 중 오류 발생: {str(e)}"}


def save_matching_result(file_id, matching_data):
    """
    매칭 결과를 저장합니다.
    
    Args:
        file_id (str): 소설 파일 ID
        matching_data (dict): 저장할 매칭 결과 데이터
        
    Returns:
        dict: 저장 결과 및 상태
    """
    try:
        # 매칭 결과 파일 경로 생성 (novels_matched 폴더에 저장)
        matching_filename = f"{file_id}_matching.json"
        matching_file_path = NOVELS_MATCHED_PATH / matching_filename
        
        # 결과 파일 저장
        with open(matching_file_path, 'w', encoding='utf-8') as f:
            json.dump(matching_data, f, ensure_ascii=False, indent=2)
        
        # 메타데이터 업데이트
        metadata = get_metadata()
        if file_id in metadata:
            metadata[file_id]["matching_file"] = matching_filename
            metadata[file_id]["matching_timestamp"] = __import__("datetime").datetime.now().isoformat()
            metadata[file_id]["matching_path"] = str(NOVELS_MATCHED_PATH)
            
            # 메타데이터 저장
            metadata_path = BASE_PATH / 'app_data' / 'metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        logger.info(f"매칭 결과를 저장했습니다: {matching_file_path}")
        return {"success": True, "matching_file": matching_filename}
        
    except Exception as e:
        logger.error(f"매칭 결과 저장 중 오류 발생: {e}")
        return {"success": False, "error": f"매칭 결과 저장 중 오류 발생: {str(e)}"}


def load_matching_result(file_id):
    """
    저장된 매칭 결과를 로드합니다.
    
    Args:
        file_id (str): 소설 파일 ID
        
    Returns:
        dict: 매칭 결과 데이터 또는 오류 정보
    """
    try:
        # 메타데이터에서 매칭 파일 이름 확인
        metadata = get_metadata()
        if file_id not in metadata or "matching_file" not in metadata[file_id]:
            logger.error(f"파일 ID {file_id}에 대한 매칭 정보가 메타데이터에 없습니다.")
            return {"success": False, "error": "매칭 정보를 찾을 수 없습니다."}
        
        matching_filename = metadata[file_id]["matching_file"]
        # 매칭 파일 경로 - 메타데이터에 저장 경로가 있으면 그것 사용, 없으면 NOVELS_MATCHED_PATH 사용
        if "matching_path" in metadata[file_id]:
            matching_file_path = Path(metadata[file_id]["matching_path"]) / matching_filename
        else:
            matching_file_path = NOVELS_MATCHED_PATH / matching_filename
        
        if not os.path.exists(matching_file_path):
            # 기존 경로(NOVELS_PROCESSED_PATH)에서도 한번 더 확인
            legacy_file_path = NOVELS_PROCESSED_PATH / matching_filename
            if os.path.exists(legacy_file_path):
                matching_file_path = legacy_file_path
                logger.info(f"기존 경로에서 매칭 결과 파일 발견: {matching_file_path}")
            else:
                logger.error(f"매칭 결과 파일이 존재하지 않습니다: {matching_file_path}")
                return {"success": False, "error": "매칭 결과 파일을 찾을 수 없습니다."}
        
        # 매칭 결과 로드
        with open(matching_file_path, 'r', encoding='utf-8') as f:
            matching_data = json.load(f)
        
        logger.info(f"매칭 결과를 로드했습니다: {matching_file_path}")
        return {
            "success": True, 
            "message": "매칭 결과를 로드했습니다.",
            "data": matching_data
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"매칭 결과 파일 파싱 오류: {e}")
        return {"success": False, "error": "매칭 결과 파일 형식이 잘못되었습니다."}
    except Exception as e:
        logger.error(f"매칭 결과 로드 중 오류 발생: {e}")
        return {"success": False, "error": f"매칭 결과 로드 중 오류 발생: {str(e)}"} 