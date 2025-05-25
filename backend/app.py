from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import uuid
import json

# 서비스 모듈 가져오기
from services.gemini_service import extract_characters_from_text, analyze_novel_structure
from services.text_storage_service import save_processed_text, get_processed_text_path, get_metadata, save_metadata, save_character_analysis, save_novel_structure_analysis
from services.text_storage_service import BASE_STORAGE_PATH, NOVELS_ORIGINAL_FOLDER, CHARACTER_ANALYSIS_FOLDER, NOVELS_PROCESSED_FOLDER, METADATA_FILE
# 매칭 서비스 모듈 가져오기 (voice_actor_service 기능 포함)
from services.matching_service import match_characters_with_voices, load_matching_result, load_voice_actors
from services.matching_service import NOVELS_MATCHED_PATH, BASE_PATH
# ElevenLabs 서비스 모듈 가져오기
from services.elevenlabs_service import get_available_voices, generate_audiobook_segment, generate_complete_audiobook, check_generation_status, AUDIO_OUTPUT_FOLDER, ELEVENLABS_API_KEY, check_api_key

# 환경 변수 로드
load_dotenv()

# Flask 앱 초기화
app = Flask(__name__)
# CORS 설정 수정
CORS(app, resources={
    r"/api/*": {
        "origins": "http://localhost:5173", # 프론트엔드 주소 명시
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# 파일 업로드 설정
ALLOWED_EXTENSIONS = {'txt'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def root():
    """
    루트 경로 - API 정보 제공
    """
    return jsonify({
        'status': 'success',
        'message': 'Audiobook Project API is running',
        'version': '1.0.0',
        'endpoints': {
            '/api/health': 'Check server status',
            '/api/extract_characters': 'Extract character information from novel text using Gemini API',
            '/api/upload/txt': 'Upload a TXT novel file',
            '/api/processed_texts/<file_id>': 'Get a specific processed text file',
            '/api/metadata': 'Get all processed texts metadata',
            '/api/metadata/<file_id>': 'Get metadata for a specific processed text',
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    서버 상태 확인용 엔드포인트
    """
    # GEMINI_API_KEY 직접 참조 대신 gemini_service 내부 로직에 의존하도록 변경 가능
    # 여기서는 환경변수 존재 유무만 간단히 체크
    gemini_api_key_present = os.getenv("GOOGLE_API_KEY") is not None
    return jsonify({
        'status': 'success',
        'message': 'Server is running!',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'api_keys': {
            'google': 'configured' if gemini_api_key_present else 'missing'
        }
    })

@app.route('/api/extract_characters', methods=['POST'])
def extract_characters_route():
    """
    소설 텍스트에서 등장인물 정보를 추출하는 엔드포인트.
    요청 본문:
        - text (str, optional): 분석할 소설 전체 텍스트.
        - file_id (str, optional): 저장된 텍스트 파일의 ID.
    둘 중 하나는 반드시 제공되어야 합니다. `text`가 우선됩니다.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is missing or not JSON"}), 400

    novel_text_content = data.get('text')
    file_id = data.get('file_id')

    if not novel_text_content and not file_id:
        return jsonify({"error": "Either 'text' or 'file_id' must be provided in the request body"}), 400

    if not novel_text_content and file_id:
        # file_id가 제공된 경우, 해당 파일의 내용을 읽어옴
        text_path = get_processed_text_path(file_id)
        if not text_path or not os.path.exists(text_path):
            return jsonify({"error": f"Processed text file with id '{file_id}' not found."}), 404
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                novel_text_content = f.read()
            if not novel_text_content.strip(): # 파일 내용이 비어있는 경우
                 return jsonify({"error": f"The file with id '{file_id}' is empty."}), 400
        except Exception as e:
            app.logger.error(f"Error reading processed file {file_id}: {str(e)}")
            return jsonify({"error": f"Could not read text content from file_id '{file_id}'."}), 500
    
    if not novel_text_content.strip(): # 최종적으로 텍스트 내용이 없는 경우 (직접 전달된 텍스트가 공백 등)
        return jsonify({"error": "Novel text content is empty or contains only whitespace."}), 400

    try:
        # gemini_service.py의 함수 호출
        characters_list = extract_characters_from_text(novel_text_content) # 성공 시 list 반환

        if isinstance(characters_list, list):
            return jsonify({
                "message": "Character extraction successful.",
                "characters": characters_list,
                "model": "gemini-2.0-flash" # 모델명은 예시
            }), 200
        else:
            app.logger.error(f"Character extraction returned unexpected type: {type(characters_list)}")
            return jsonify({"error": "Failed to extract characters due to unexpected response type."}), 500

    except ValueError as ve:
        app.logger.error(f"Character extraction failed (ValueError): {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except json.JSONDecodeError as jde:
        app.logger.error(f"Character extraction failed (JSONDecodeError): {str(jde)}")
        return jsonify({"error": f"Failed to parse character data from AI: {str(jde)}"}), 500
    except Exception as e:
        app.logger.error(f"Gemini character extraction failed (app.py): {str(e)}")
        client_error = {"error": "Failed to extract characters using Gemini."}
        # client_error['details'] = str(e) # 디버깅 시 주석 해제하여 상세 오류 확인 가능
        return jsonify(client_error), 500

@app.route('/api/upload/txt', methods=['POST'])
def upload_txt_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        original_filename = file.filename
        try:
            extracted_text = file.read().decode('utf-8')
            if not extracted_text.strip():
                return jsonify({"error": "File is empty or contains only whitespace."}), 400

            storage_result = save_processed_text(original_filename, extracted_text)
            
            if storage_result and 'id' in storage_result:
                file_id = storage_result['id']
                app.logger.info(f"File uploaded and saved: {file_id} for {original_filename}")
                return jsonify({
                    "message": f"File '{original_filename}' uploaded and saved successfully.",
                    "file_id": file_id,
                    "original_filename": original_filename,
                    "processed_filename": storage_result['filename'],
                    "text_preview": extracted_text[:200] + '...' if len(extracted_text) > 200 else extracted_text
                }), 200
            else:
                app.logger.error(f"Failed to save processed text for {original_filename}.")
                return jsonify({"error": "Failed to save processed text and metadata."}), 500
        except UnicodeDecodeError:
            app.logger.error(f"UnicodeDecodeError for file {original_filename}")
            return jsonify({"error": "Failed to decode file content. Please ensure the file is UTF-8 encoded."}), 400
        except Exception as e:
            app.logger.error(f"File processing failed for {original_filename}: {str(e)}")
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 500
    else:
        return jsonify({"error": "File type not allowed or invalid file."}), 400

@app.route('/api/analyze/characters/<file_id>', methods=['POST'])
def analyze_characters_route(file_id):
    """
    지정된 file_id의 텍스트를 읽어 등장인물 분석을 수행하고 결과를 저장합니다.
    """
    app.logger.info(f"Character analysis requested for file_id: {file_id}")
    text_path = get_processed_text_path(file_id)
    if not text_path or not os.path.exists(text_path):
        app.logger.error(f"Processed text file not found for id: {file_id}")
        return jsonify({"error": f"Processed text file with id '{file_id}' not found."}), 404
    
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            novel_text_content = f.read()
        if not novel_text_content.strip():
             app.logger.warning(f"File {file_id} is empty.")
             return jsonify({"error": f"The file with id '{file_id}' is empty."}), 400
    except Exception as e:
        app.logger.error(f"Error reading processed file {file_id}: {str(e)}")
        return jsonify({"error": f"Could not read text content from file_id '{file_id}'."}), 500

    try:
        characters_data = extract_characters_from_text(novel_text_content)
        if characters_data: # characters_data가 None이 아니면 성공으로 간주
            analysis_saved_filename = save_character_analysis(file_id, characters_data)
            if analysis_saved_filename:
                app.logger.info(f"Character analysis for {file_id} saved to {analysis_saved_filename}")
                return jsonify({
                    "message": "Character analysis successful.",
                    "file_id": file_id,
                    "analysis_file": analysis_saved_filename,
                    "model_info": "gemini-1.5-flash-latest (example)"
                }), 200
            else:
                app.logger.error(f"Failed to save character analysis file for {file_id}")
                return jsonify({"error": "Failed to save character analysis file."}), 500
        else: # characters_data가 None이거나 (gemini_service에서 빈 응답 등으로 인해) 또는 예상치 못한 falsy 값일 때
            app.logger.warning(f"Character analysis for {file_id} returned no data or unexpected data from service. Data: {characters_data}")
            return jsonify({"error": "Character analysis did not return expected data from service."}), 500
    except ValueError as ve: # API 키 누락, 빈 텍스트 입력, 또는 gemini_service 내에서 JSON 파싱 실패 등
        app.logger.error(f"Character analysis ValueError for {file_id}: {str(ve)}")
        return jsonify({"error": f"Character analysis input error: {str(ve)}"}), 400 # API 키 누락 등
    except RuntimeError as re:
        app.logger.error(f"Character analysis RuntimeError for {file_id}: {str(re)}")
        return jsonify({"error": f"Character analysis runtime error: {str(re)}"}), 500 # API 호출 실패 등
    except Exception as e:
        app.logger.error(f"Unexpected error during character analysis for {file_id}: {str(e)}")
        return jsonify({"error": f"Unexpected error during character analysis: {str(e)}"}), 500

@app.route('/api/analyze/structure/<file_id>', methods=['POST'])
def analyze_structure_route(file_id):
    """
    지정된 file_id의 텍스트를 읽어 소설 구조 분석을 수행하고 결과를 저장합니다.
    """
    app.logger.info(f"Structure analysis requested for file_id: {file_id}")
    text_path = get_processed_text_path(file_id)
    if not text_path or not os.path.exists(text_path):
        app.logger.error(f"Processed text file not found for id: {file_id}")
        return jsonify({"error": f"Processed text file with id '{file_id}' not found."}), 404
    
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            novel_text_content = f.read()
        if not novel_text_content.strip():
             app.logger.warning(f"File {file_id} is empty.")
             return jsonify({"error": f"The file with id '{file_id}' is empty."}), 400
    except Exception as e:
        app.logger.error(f"Error reading processed file {file_id}: {str(e)}")
        return jsonify({"error": f"Could not read text content from file_id '{file_id}'."}), 500

    try:
        structured_data = analyze_novel_structure(novel_text_content)
        if structured_data: # 현재 analyze_novel_structure는 성공 시 list/dict, 실패/빈 응답 시 None 또는 예외 발생
            analysis_saved_filename = save_novel_structure_analysis(file_id, structured_data)
            if analysis_saved_filename:
                app.logger.info(f"Novel structure analysis for {file_id} saved to {analysis_saved_filename}")
                return jsonify({
                    "message": "Novel structure analysis successful.",
                    "file_id": file_id,
                    "analysis_file": analysis_saved_filename,
                    "model_info": "gemini-1.5-flash-latest (example)"
                }), 200
            else:
                app.logger.error(f"Failed to save novel structure analysis file for {file_id}")
                return jsonify({"error": "Failed to save novel structure analysis file."}), 500
        else: # analyze_novel_structure가 None을 반환한 경우 (예: API 빈 응답)
            app.logger.warning(f"Novel structure analysis for {file_id} returned no data from service.")
            # gemini_service에서 예외를 발생시키지 않고 None을 반환하는 케이스가 있다면 이 부분이 실행될 수 있음.
            # 현재 gemini_service는 빈 응답 시 None을 반환하거나, 파싱 실패 시 ValueError를 발생시킴.
            return jsonify({"error": "Novel structure analysis did not return data from service."}), 500
    except ValueError as ve: # gemini_service 내에서 발생 (API 키, 빈 텍스트, JSON 파싱 실패 등)
        app.logger.error(f"Novel structure analysis ValueError for {file_id}: {str(ve)}")
        return jsonify({"error": f"Novel structure analysis input/parsing error: {str(ve)}"}), 400
    except RuntimeError as re: # gemini_service 내 Gemini API 호출 실패
        app.logger.error(f"Novel structure analysis RuntimeError for {file_id}: {str(re)}")
        return jsonify({"error": f"Novel structure analysis runtime error: {str(re)}"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error during novel structure analysis for {file_id}: {str(e)}")
        return jsonify({"error": f"Unexpected error during novel structure analysis: {str(e)}"}), 500

@app.route('/api/match/characters_voices/<file_id>', methods=['POST'])
def match_characters_voices_route(file_id):
    """
    소설 등장인물과 성우를 매칭하는 엔드포인트.
    """
    app.logger.info(f"Character-Voice matching requested for file_id: {file_id}")
    
    # 파일 ID 유효성 검사
    if not get_processed_text_path(file_id):
        app.logger.error(f"Processed text file not found for id: {file_id}")
        return jsonify({"error": f"Processed text file with id '{file_id}' not found."}), 404
    
    # 등장인물 분석 결과가 있는지 확인
    metadata = get_metadata(file_id)
    if not metadata or "character_analysis_file" not in metadata:
        app.logger.error(f"Character analysis not found for file_id: {file_id}")
        return jsonify({"error": "등장인물 분석이 먼저 필요합니다."}), 400
    
    # 소설 구조 분석 결과가 있는지 확인
    if not metadata or "structure_analysis_file" not in metadata:
        app.logger.error(f"Structure analysis not found for file_id: {file_id}")
        return jsonify({"error": "소설 구조 분석이 먼저 필요합니다."}), 400
    
    # 매칭 수행 (use_gemini 파라미터 제거)
    match_result = match_characters_with_voices(file_id)
    
    if not match_result.get("success"):
        app.logger.error(f"Matching failed: {match_result.get('error')}")
        return jsonify({"error": match_result.get("error")}), 500
    
    # 성공 응답
    return jsonify({
        "message": match_result.get("message"),
        "file_id": file_id,
        "matching_file": match_result.get("matching_file"),
        "character_voice_map": match_result.get("character_voice_map")
    }), 200

@app.route('/api/match/characters_voices/<file_id>', methods=['GET'])
def get_character_voice_mapping_route(file_id):
    """
    저장된 등장인물-성우 매칭 결과를 조회하는 엔드포인트
    """
    app.logger.info(f"Requesting character-voice mapping for file_id: {file_id}")
    
    # 매칭 결과 로드
    match_result = load_matching_result(file_id)
    
    if not match_result.get("success"):
        app.logger.error(f"Failed to load matching results: {match_result.get('error')}")
        return jsonify({"error": match_result.get("error")}), 404
    
    # 성공 응답
    return jsonify(match_result.get("data")), 200

@app.route('/api/voice_actors', methods=['GET'])
def get_voice_actors_route():
    """
    사용 가능한 성우 목록을 조회하는 엔드포인트
    """
    voice_actors = load_voice_actors()
    
    if not voice_actors:
        app.logger.warning("No voice actors found")
        return jsonify({"message": "성우 데이터가 없습니다.", "voice_actors": []}), 200
    
    # 성우 정보에 feature가, name, id 필드가 확실히 포함되어 있는지 확인
    for actor in voice_actors:
        # feature 필드가 없거나 빈 경우를 위한 기본값 설정
        if 'feature' not in actor or not actor['feature']:
            actor['feature'] = "미설정"
    
    return jsonify({
        "message": f"{len(voice_actors)}명의 성우 데이터를 찾았습니다.",
        "voice_actors": voice_actors
    }), 200

@app.route('/api/processed_texts/<file_id>', methods=['GET'])
def get_single_processed_text(file_id):
    text_path = get_processed_text_path(file_id)
    if not text_path or not os.path.exists(text_path):
        return jsonify({"error": f"Processed text file with id '{file_id}' not found."}), 404
    
    return send_from_directory(NOVELS_ORIGINAL_FOLDER, os.path.basename(text_path))

@app.route('/api/processed_texts/<file_id>', methods=['DELETE'])
def delete_processed_text(file_id):
    """
    지정된 file_id의 소설 파일 및 관련 메타데이터를 삭제합니다.
    모든 관련 폴더(app_data 내부)에서 해당 파일을 삭제합니다.
    """
    app.logger.info(f"Delete request for file_id: {file_id}")
    
    # 메타데이터에서 파일 정보 확인
    metadata = get_metadata()
    if file_id not in metadata:
        app.logger.error(f"File ID {file_id} not found in metadata")
        return jsonify({"error": f"File with id '{file_id}' not found."}), 404
    
    file_metadata = metadata[file_id]
    
    try:
        # 1. 원본 소설 파일 삭제
        saved_filename = file_metadata.get('saved_filename')
        if saved_filename:
            original_filepath = os.path.join(NOVELS_ORIGINAL_FOLDER, saved_filename)
            if os.path.exists(original_filepath):
                os.remove(original_filepath)
                app.logger.info(f"Deleted original file: {original_filepath}")
        
        # 2. 캐릭터 분석 파일 삭제
        character_analysis_file = file_metadata.get('character_analysis_file')
        if character_analysis_file:
            character_filepath = os.path.join(CHARACTER_ANALYSIS_FOLDER, character_analysis_file)
            if os.path.exists(character_filepath):
                os.remove(character_filepath)
                app.logger.info(f"Deleted character analysis file: {character_filepath}")
        
        # 3. 소설 구조 분석 파일 삭제
        structure_analysis_file = file_metadata.get('structure_analysis_file')
        if structure_analysis_file:
            structure_filepath = os.path.join(NOVELS_PROCESSED_FOLDER, structure_analysis_file)
            if os.path.exists(structure_filepath):
                os.remove(structure_filepath)
                app.logger.info(f"Deleted structure analysis file: {structure_filepath}")
        
        # 4. 오디오북 파일 삭제 (audio_output 폴더)
        audio_output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
        if os.path.exists(audio_output_dir):
            try:
                import shutil
                shutil.rmtree(audio_output_dir)
                app.logger.info(f"Deleted audiobook directory: {audio_output_dir}")
            except Exception as e:
                app.logger.error(f"Error deleting audiobook directory {audio_output_dir}: {str(e)}")
        
        # 5. 매칭된 소설 파일 삭제 (novels_matched 폴더 - from matching_service)
        novels_matched_folder = str(NOVELS_MATCHED_PATH)
        matched_filename = f"{file_id}_matching.json"
        matched_filepath = os.path.join(novels_matched_folder, matched_filename)
        if os.path.exists(matched_filepath):
            os.remove(matched_filepath)
            app.logger.info(f"Deleted matched novel file: {matched_filepath}")
        
        # 6. 메타데이터에서 항목 제거
        del metadata[file_id]
        save_metadata(metadata)
        app.logger.info(f"Removed metadata for file_id: {file_id}")
        
        return jsonify({
            "message": f"File with id '{file_id}' and related data successfully deleted.",
            "deleted_file_id": file_id
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error deleting file {file_id}: {str(e)}")
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500

@app.route('/api/metadata', methods=['GET'])
def get_all_metadata_route():
    all_metadata = get_metadata()
    return jsonify(all_metadata)

@app.route('/api/metadata/<file_id>', methods=['GET'])
def get_single_metadata_route(file_id):
    metadata_item = get_metadata(file_id)
    if metadata_item:
        return jsonify(metadata_item)
    return jsonify({"error": "Metadata not found for the given ID"}), 404

@app.route('/api/audiobook/generate/<file_id>', methods=['POST'])
def generate_audiobook_route(file_id):
    """
    지정된 file_id의 소설을 오디오북으로 생성하는 엔드포인트.
    
    요청 본문: 생성 관련 설정(선택적)
    - force (bool, optional): 이미 생성된 오디오북이 있을 경우 덮어쓸지 여부
    """
    try:
        # API 키 확인 및 디버깅
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        app.logger.info(f"ELEVENLABS_API_KEY 환경 변수 확인: {'설정됨' if elevenlabs_key else '설정되지 않음'}")
        app.logger.info(f"ELEVENLABS_API_KEY 길이: {len(elevenlabs_key) if elevenlabs_key else 0}")
        
        if not check_api_key():
            app.logger.error("ELEVENLABS_API_KEY가 환경 변수에 설정되어 있지 않습니다.")
            return jsonify({"error": "오디오북 생성에 필요한 ElevenLabs API 키가 설정되어 있지 않습니다."}), 400
        
        # 파일 ID 유효성 검사
        metadata = get_metadata()
        if file_id not in metadata:
            return jsonify({"error": f"소설 파일 ID '{file_id}'를 찾을 수 없습니다."}), 404
        
        # 매칭 결과 로드 (NOVELS_MATCHED_PATH 사용)
        matching_result_file = os.path.join(str(NOVELS_MATCHED_PATH), f"{file_id}_matching.json")
        if not os.path.exists(matching_result_file):
            return jsonify({"error": f"소설 파일 ID '{file_id}'에 대한 등장인물-성우 매칭 결과가 없습니다. 먼저 매칭을 수행해주세요."}), 404
        
        # 구조 분석 결과 로드
        structure_file = os.path.join(NOVELS_PROCESSED_FOLDER, f"{file_id}_structure.json")
        if not os.path.exists(structure_file):
            return jsonify({"error": f"소설 파일 ID '{file_id}'에 대한 구조 분석 결과가 없습니다. 먼저 분석을 수행해주세요."}), 404
        
        # 매칭 결과 로드
        try:
            with open(matching_result_file, 'r', encoding='utf-8') as f:
                matching_data = json.load(f)
            app.logger.info(f"매칭 결과 데이터 타입: {type(matching_data)}, 구조: {matching_data.keys() if isinstance(matching_data, dict) else '딕셔너리 아님'}")
        except Exception as e:
            app.logger.error(f"Error loading matching result for {file_id}: {str(e)}")
            return jsonify({"error": f"매칭 결과 파일 로드 중 오류가 발생했습니다: {str(e)}"}), 500
        
        # 구조 분석 결과 로드
        try:
            with open(structure_file, 'r', encoding='utf-8') as f:
                structure_data = json.load(f)
            app.logger.info(f"구조 분석 데이터 타입: {type(structure_data)}, 길이: {len(structure_data) if isinstance(structure_data, (list, dict)) else '배열/딕셔너리 아님'}")
        except Exception as e:
            app.logger.error(f"Error loading structure analysis for {file_id}: {str(e)}")
            return jsonify({"error": f"구조 분석 결과 파일 로드 중 오류가 발생했습니다: {str(e)}"}), 500
        
        # 오디오북 생성 데이터 구성
        character_voice_map = {}
        story_items = []
        
        # 매칭 데이터에서 character_voice_map 추출
        if isinstance(matching_data, dict) and "character_voice_map" in matching_data:
            character_voice_map = matching_data["character_voice_map"]
        elif isinstance(matching_data, dict):
            # 첫 번째 키가 character_voice_map일 가능성 확인
            for key, value in matching_data.items():
                if isinstance(value, dict):
                    character_voice_map = value
                    break
        
        # 구조 데이터에서 story_items 추출
        if isinstance(structure_data, list):
            # 구조 데이터가 리스트인 경우 그대로 사용
            story_items = structure_data
        elif isinstance(structure_data, dict) and "segments" in structure_data:
            # 구조 데이터가 딕셔너리이고 segments 키가 있는 경우
            story_items = structure_data["segments"]
        
        # 데이터 유효성 로깅
        app.logger.info(f"character_voice_map 항목 수: {len(character_voice_map)}")
        app.logger.info(f"story_items 항목 수: {len(story_items)}")
        
        # 오디오북 생성 데이터 구성
        story_data = {
            "character_voice_map": character_voice_map,
            "story_items": story_items
        }
        
        # 생성 요청 처리
        force = request.json.get('force', False) if request.is_json else False
        
        # 이미 생성된 오디오북 확인
        output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
        if os.path.exists(output_dir) and not force:
            # 이미 일부 파일이 생성된 경우, 생성 상태 확인
            status_result, _ = check_generation_status(file_id)
            
            # 생성된 세그먼트가 있고, 완료 또는 진행 중인 경우 알림
            if status_result.get("generated_segments", 0) > 0:
                return jsonify({
                    "message": "이미 오디오북 생성이 진행 중이거나 완료되었습니다. 덮어쓰려면 'force=true' 옵션을 사용하세요.",
                    "status": status_result.get("status"),
                    "generated_segments": status_result.get("generated_segments", 0),
                    "total_segments": status_result.get("total_segments", 0),
                    "file_id": file_id
                }), 200
        
        # 오디오북 생성 실행
        result, status_code = generate_complete_audiobook(file_id, story_data)
        
        if status_code != 200:
            # API 키 관련 오류 확인
            if 'API key' in str(result.get('error', '')):
                app.logger.error(f"ElevenLabs API 키 오류: {result.get('error')}")
                return jsonify({"error": "ElevenLabs API 키가 유효하지 않거나 설정되지 않았습니다. 관리자에게 문의하세요."}), 400
            return jsonify(result), status_code
        
        return jsonify({
            "message": "오디오북 생성이 완료되었습니다.",
            "generation_results": result
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error generating audiobook for {file_id}: {str(e)}")
        return jsonify({"error": f"오디오북 생성 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/audiobook/status/<file_id>', methods=['GET'])
def check_audiobook_status_route(file_id):
    """
    지정된 file_id의 오디오북 생성 상태를 확인하는 엔드포인트.
    """
    try:
        # 파일 ID 유효성 검사
        metadata = get_metadata()
        if file_id not in metadata:
            return jsonify({
                "file_id": file_id,
                "status": "error",
                "message": f"소설 파일 ID '{file_id}'를 찾을 수 없습니다.",
                "total_segments": 0,
                "generated_segments": 0,
                "audio_files": [],
                "segment_texts": {}
            }), 404
        
        # 생성 상태 확인
        status_result, status_code = check_generation_status(file_id)
        
        if status_code != 200:
            # 오류 상태라도 일관된 형식으로 응답 반환
            return jsonify({
                "file_id": file_id,
                "status": "error",
                "message": status_result.get("error", "오디오북 상태 확인 중 오류가 발생했습니다."),
                "total_segments": 0,
                "generated_segments": 0,
                "audio_files": [],
                "segment_texts": {}
            }), 200  # 오류 상태도 200으로 처리하여 프론트엔드에서 일관되게 처리
        
        # novels_matched 폴더에서 매칭된 데이터 로드하여 세그먼트 텍스트 추가
        segment_texts = {}
        matched_file = os.path.join(NOVELS_MATCHED_PATH, f"{file_id}_matching.json")
        
        if os.path.exists(matched_file):
            try:
                with open(matched_file, 'r', encoding='utf-8') as f:
                    matched_data = json.load(f)
                
                # 구조 분석된 스토리 아이템 찾기
                story_items = []
                if isinstance(matched_data, dict) and "story_items" in matched_data:
                    story_items = matched_data["story_items"]
                elif isinstance(matched_data, dict) and "segments" in matched_data:
                    story_items = matched_data["segments"]
                
                # 오디오 파일명과 텍스트 매핑
                for item in story_items:
                    if "order" in item and "text" in item:
                        filename = f"{int(item['order']):03d}.mp3"
                        segment_texts[filename] = item.get("text", "")
                        
                        # 화자 정보 추가 (있는 경우)
                        if "speaker" in item:
                            segment_texts[filename] = f"{item['speaker']}: {segment_texts[filename]}"
            except Exception as e:
                app.logger.error(f"Error loading matched data for {file_id}: {str(e)}")
                # 오류 발생해도 계속 진행 (텍스트 정보는 선택적)
        
        # 기존 status_result에 segment_texts 추가해서 반환
        status_result["segment_texts"] = segment_texts
        
        return jsonify(status_result), 200
        
    except Exception as e:
        app.logger.error(f"Error checking audiobook status for {file_id}: {str(e)}")
        return jsonify({
            "file_id": file_id,
            "status": "error",
            "message": f"오디오북 상태 확인 중 오류가 발생했습니다: {str(e)}",
            "total_segments": 0,
            "generated_segments": 0,
            "audio_files": [],
            "segment_texts": {}
        }), 200  # 오류 상태도 200으로 처리

@app.route('/api/audiobook/files/<file_id>/<segment_id>', methods=['GET'])
def get_audiobook_file_route(file_id, segment_id):
    """
    지정된 file_id와 segment_id에 해당하는 오디오 파일을 제공하는 엔드포인트.
    """
    try:
        # 파일 ID 유효성 검사
        metadata = get_metadata()
        if file_id not in metadata:
            return jsonify({"error": f"소설 파일 ID '{file_id}'를 찾을 수 없습니다."}), 404
        
        # 오디오 파일 디렉토리 확인
        output_dir = os.path.join(AUDIO_OUTPUT_FOLDER, file_id)
        if not os.path.exists(output_dir):
            return jsonify({"error": f"소설 파일 ID '{file_id}'에 대한 오디오북이 생성되지 않았습니다."}), 404
        
        # 세그먼트 ID를 정수로 변환 및 파일명 생성
        try:
            segment_number = int(segment_id)
            audio_filename = f"{segment_number:03d}.mp3"
        except ValueError:
            return jsonify({"error": f"유효하지 않은 세그먼트 ID입니다. 세그먼트 ID는 숫자여야 합니다."}), 400
        
        # 파일 존재 확인
        audio_file_path = os.path.join(output_dir, audio_filename)
        if not os.path.exists(audio_file_path):
            return jsonify({"error": f"요청한 오디오 파일을 찾을 수 없습니다."}), 404
        
        # 파일 전송
        return send_from_directory(output_dir, audio_filename, as_attachment=False)
        
    except Exception as e:
        app.logger.error(f"Error serving audiobook file for {file_id}, segment {segment_id}: {str(e)}")
        return jsonify({"error": f"오디오 파일 제공 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/elevenlabs/voices', methods=['GET'])
def get_elevenlabs_voices_route():
    """
    ElevenLabs에서 사용 가능한 음성 목록을 가져오는 엔드포인트.
    """
    try:
        # 음성 목록 가져오기
        voices_result, status_code = get_available_voices()
        
        if status_code != 200:
            return jsonify(voices_result), status_code
        
        return jsonify(voices_result), 200
        
    except Exception as e:
        app.logger.error(f"Error getting ElevenLabs voices: {str(e)}")
        return jsonify({"error": f"ElevenLabs 음성 목록 가져오기 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == '__main__':
    # 포트를 8000으로 변경
    port = int(os.getenv('PORT', 8000))
    print(f"서버가 http://localhost:{port} 에서 실행 중입니다.")
    app.run(debug=True, host='0.0.0.0', port=port) 