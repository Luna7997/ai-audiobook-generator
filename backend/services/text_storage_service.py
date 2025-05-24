import os
import json
import uuid
from datetime import datetime
import logging

# 처리된 텍스트와 메타데이터를 저장할 기본 경로
BASE_STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app_data')
METADATA_FILE = os.path.join(BASE_STORAGE_PATH, 'metadata.json')
NOVELS_ORIGINAL_FOLDER = os.path.join(BASE_STORAGE_PATH, 'novels_original')
CHARACTER_ANALYSIS_FOLDER = os.path.join(BASE_STORAGE_PATH, 'character_analysis')
NOVELS_PROCESSED_FOLDER = os.path.join(BASE_STORAGE_PATH, 'novels_processed')

# 저장 경로 및 메타데이터 파일, 분석 결과 폴더가 없으면 생성
if not os.path.exists(BASE_STORAGE_PATH):
    os.makedirs(BASE_STORAGE_PATH)
if not os.path.exists(NOVELS_ORIGINAL_FOLDER):
    os.makedirs(NOVELS_ORIGINAL_FOLDER)
if not os.path.exists(CHARACTER_ANALYSIS_FOLDER):
    os.makedirs(CHARACTER_ANALYSIS_FOLDER)
if not os.path.exists(NOVELS_PROCESSED_FOLDER):
    os.makedirs(NOVELS_PROCESSED_FOLDER)

if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

def load_metadata():
    """메타데이터 파일에서 모든 메타데이터를 로드합니다."""
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # 파일이 손상되었거나 비어있는 경우
        return {}

def save_metadata(metadata):
    """주어진 메타데이터를 파일에 저장합니다."""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

def save_processed_text(original_filename, text_content):
    """
    추출된 텍스트를 파일로 저장하고 메타데이터를 업데이트합니다.

    Args:
        original_filename (str): 원본 파일의 이름입니다.
        text_content (str): 저장할 텍스트 내용입니다.

    Returns:
        dict: 저장된 파일의 ID (UUID)와 파일명을 포함하는 딕셔너리, 또는 실패 시 None.
    """
    try:
        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}.txt"
        filepath = os.path.join(NOVELS_ORIGINAL_FOLDER, saved_filename)

        # 텍스트 파일 저장 (UTF-8 인코딩)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        file_size = os.path.getsize(filepath)
        
        # 메타데이터 업데이트
        metadata = load_metadata()
        metadata[file_id] = {
            'original_filename': original_filename,
            'saved_filename': saved_filename,
            'upload_timestamp': datetime.now().isoformat(),
            'size_bytes': file_size,
            'char_count': len(text_content) # 문자 수 (선택적)
        }
        save_metadata(metadata)
        
        return {
            'id': file_id,
            'filename': saved_filename
            # 향후 접근 URL도 여기서 생성하여 반환 가능
        }
    except Exception as e:
        print(f"Error saving processed text or updating metadata: {e}")
        # 실패 시 생성된 파일이 있다면 삭제하는 로직 추가 고려
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as remove_e:
                print(f"Error deleting partially saved file {filepath}: {remove_e}")
        return None

def get_processed_text_path(file_id):
    """주어진 ID에 해당하는 처리된 텍스트 파일의 경로를 반환합니다."""
    metadata = load_metadata()
    if file_id in metadata:
        saved_filename = metadata[file_id]['saved_filename']
        return os.path.join(NOVELS_ORIGINAL_FOLDER, saved_filename)
    return None

def get_metadata(file_id=None):
    """특정 파일 ID의 메타데이터 또는 전체 메타데이터를 반환합니다."""
    all_metadata = load_metadata()
    if file_id:
        return all_metadata.get(file_id)
    return all_metadata

def save_character_analysis(original_file_id, analysis_data):
    """
    등장인물 분석 결과를 JSON 파일로 저장합니다.

    Args:
        original_file_id (str): 원본 텍스트 파일의 ID (metadata.json의 키).
        analysis_data (list): 등장인물 분석 결과 (딕셔너리 리스트).

    Returns:
        str: 저장된 JSON 파일의 이름, 또는 실패 시 None.
    """
    try:
        # 분석 결과 파일명은 원본 파일 ID를 기반으로 생성 (예: <original_file_id>_characters.json)
        analysis_filename = f"{original_file_id}_characters.json"
        filepath = os.path.join(CHARACTER_ANALYSIS_FOLDER, analysis_filename)

        # JSON 파일 저장 (UTF-8 인코딩)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=4)
        
        # 메타데이터에 분석 파일 정보 추가 (선택적)
        metadata = load_metadata()
        if original_file_id in metadata:
            metadata[original_file_id]['character_analysis_file'] = analysis_filename
            metadata[original_file_id]['character_analysis_timestamp'] = datetime.now().isoformat()
            save_metadata(metadata)
        else:
            # 원본 파일 ID가 메타데이터에 없는 경우 (일반적으로 발생하지 않아야 함)
            print(f"Warning: Original file ID {original_file_id} not found in metadata while saving character analysis.")
            # 이 경우, 분석 파일은 저장되지만 메타데이터에는 연결되지 않음.

        return analysis_filename
    except Exception as e:
        print(f"Error saving character analysis: {e}")
        return None

def save_novel_structure_analysis(original_file_id, structure_data):
    """
    소설 구조 분석 결과를 JSON 파일로 저장합니다.

    Args:
        original_file_id (str): 원본 텍스트 파일의 ID (metadata.json의 키).
        structure_data (list | dict): 구조 분석 결과 (JSON 파싱된 데이터).

    Returns:
        str: 저장된 JSON 파일의 이름, 또는 실패 시 None.
    """
    try:
        # 구조 분석 결과 파일명은 원본 파일 ID를 기반으로 생성 (예: <original_file_id>_structure.json)
        analysis_filename = f"{original_file_id}_structure.json"
        filepath = os.path.join(NOVELS_PROCESSED_FOLDER, analysis_filename) # 저장 위치 novels_processed

        # JSON 파일 저장 (UTF-8 인코딩)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(structure_data, f, ensure_ascii=False, indent=4)
        
        # 메타데이터에 구조 분석 파일 정보 추가
        metadata = load_metadata()
        if original_file_id in metadata:
            metadata[original_file_id]['structure_analysis_file'] = analysis_filename
            metadata[original_file_id]['structure_analysis_timestamp'] = datetime.now().isoformat()
            save_metadata(metadata)
        else:
            logging.warning(f"Warning: Original file ID {original_file_id} not found in metadata while saving structure analysis.")

        return analysis_filename
    except Exception as e:
        logging.error(f"Error saving novel structure analysis: {e}") # logging 추가
        print(f"Error saving novel structure analysis: {e}") # 기존 print 유지 또는 제거
        return None

# 테스트용 코드
if __name__ == '__main__':
    print(f"Base storage path: {BASE_STORAGE_PATH}")
    print(f"Metadata file: {METADATA_FILE}")

    # 테스트 저장
    test_original_name = "my_novel.txt"
    test_content = "이것은 오디오북으로 변환될 소설의 내용입니다.\n여러 줄로 이루어져 있습니다.\n" * 10
    
    save_result = save_processed_text(test_original_name, test_content)
    
    if save_result:
        print(f"\nText saved successfully:")
        print(f"  ID: {save_result['id']}")
        print(f"  Filename: {save_result['filename']}")
        
        # 메타데이터 조회 테스트
        saved_id = save_result['id']
        retrieved_metadata = get_metadata(saved_id)
        print(f"\nRetrieved metadata for {saved_id}:")
        print(json.dumps(retrieved_metadata, indent=4, ensure_ascii=False))
        
        # 파일 경로 조회 테스트
        retrieved_path = get_processed_text_path(saved_id)
        print(f"\nRetrieved path for {saved_id}: {retrieved_path}")
        if retrieved_path and os.path.exists(retrieved_path):
            with open(retrieved_path, 'r', encoding='utf-8') as f_read:
                print(f"  Content preview: {f_read.read(100)}...")
        else:
            print(f"  Could not retrieve or find file at path: {retrieved_path}") 
            
        # 전체 메타데이터 조회
        all_meta = get_metadata()
        print(f"\nAll metadata entries: {len(all_meta)}")

        # 생성된 테스트 파일 및 메타데이터 정리 (선택적)
        # if os.path.exists(retrieved_path):
        #     os.remove(retrieved_path)
        # metadata_after_cleanup = load_metadata()
        # if saved_id in metadata_after_cleanup:
        #     del metadata_after_cleanup[saved_id]
        #     save_metadata(metadata_after_cleanup)
        # print("Cleaned up test data.")

    else:
        print("\nFailed to save text.") 