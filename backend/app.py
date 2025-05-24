from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
# import google.generativeai as genai # gemini_service.py에서 처리하므로 app.py에서 직접 임포트 불필요
import uuid
import json

# 서비스 모듈 가져오기
from services.gemini_service import generate_text, extract_characters_from_text, analyze_novel_structure
from services.text_storage_service import save_processed_text, get_processed_text_path, get_metadata, save_character_analysis, save_novel_structure_analysis
# 매칭 서비스 모듈 가져오기 (voice_actor_service 기능 포함)
from services.matching_service import match_characters_with_voices, load_matching_result, load_voice_actors

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
# UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads') # 주석 처리 또는 삭제
# PROCESSED_TEXTS_FOLDER는 text_storage_service 내부에서 BASE_STORAGE_PATH로 관리됨
ALLOWED_EXTENSIONS = {'txt'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # 주석 처리 또는 삭제
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# uploads 폴더가 없으면 생성 -> text_storage_service.py에서 app_data 및 하위 폴더 생성 로직으로 대체됨
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

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
            '/api/gemini/generate': 'Generate text using Gemini API',
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

# --- Gemini API 엔드포인트 --- 

@app.route('/api/gemini/generate', methods=['POST'])
def gemini_generate_route():
    """
    Gemini API로 텍스트 생성 엔드포인트 (gemini_service.py 사용)
    """
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Prompt is required"}), 400
    
    prompt = data['prompt']
    # system_instruction = data.get('system_instruction', None) # 이 라인은 더 이상 직접 사용되지 않음
    
    try:
        # gemini_service.py의 함수 호출 (system_instruction 인자 제거)
        generated_text_content = generate_text(prompt)
        
        # gemini_service.generate_text는 성공 시 문자열을 반환, 
        # API 키가 없으면 "오류: ..." 문자열을 반환, 그 외 API 오류 시 예외 발생.
        if generated_text_content.startswith("오류:"):
            app.logger.error(f"Gemini text generation failed due to service warning: {generated_text_content}")
            return jsonify({"error": generated_text_content}), 500 # 또는 400 Bad Request 등 상황에 맞게
        else:
            # 성공적으로 텍스트가 생성된 경우
            # 모델 정보는 현재 generate_text에서 반환하지 않으므로, 필요하다면 gemini_service 수정 필요
            return jsonify({"generated_text": generated_text_content, "model": "gemini-2.0-flash"}) # 모델명은 예시
    except Exception as e:
        # gemini_service.py에서 발생한 예외를 여기서 처리
        app.logger.error(f"Gemini text generation failed: {str(e)}")
        return jsonify({"error": f"Failed to generate text using Gemini: {str(e)}"}), 500

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

# --- 새로운 API 엔드포인트: 인물-성우 매칭 ---

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


# --- 추가: 사용 가능한 성우 목록 조회 API ---

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

# --- Processed Text & Metadata Endpoints ---
@app.route('/api/processed_texts/<file_id>', methods=['GET'])
def get_single_processed_text(file_id):
    filepath = get_processed_text_path(file_id)
    if filepath and os.path.exists(filepath):
        # 보안을 위해 실제 파일 시스템 경로 대신 파일 스트림을 직접 반환하거나, 
        # 여기서는 내용을 읽어서 JSON으로 반환 (대용량 파일 주의)
        # return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"file_id": file_id, "content": content})
        except Exception as e:
            return jsonify({"error": f"Could not read file: {str(e)}"}), 500
    return jsonify({"error": "Processed text file not found"}), 404

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

if __name__ == '__main__':
    # 포트를 8000으로 변경
    port = int(os.getenv('PORT', 8000))
    print(f"서버가 http://localhost:{port} 에서 실행 중입니다.")
    app.run(debug=True, host='0.0.0.0', port=port) 