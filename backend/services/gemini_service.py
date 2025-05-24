import os
import json
import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig  # Updated import based on common usage
from datetime import datetime
from pathlib import Path

# Gemini API 키를 환경 변수에서 로드
API_KEY = os.environ.get("GOOGLE_API_KEY")

# API 키 설정 (애플리케이션 시작 시 한 번 실행)
if API_KEY:
    genai.configure(api_key=API_KEY)

# 매칭 결과 저장 경로 설정
BASE_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MATCHING_RESULT_PATH = BASE_PATH / 'app_data' / 'matching_result'

# 매칭 결과 폴더 확인 및 생성
if not os.path.exists(MATCHING_RESULT_PATH):
    os.makedirs(MATCHING_RESULT_PATH)
    logging.info(f"매칭 결과 폴더 생성: {MATCHING_RESULT_PATH}")

# --- 일반 텍스트 생성 함수 ---
def generate_text(prompt: str, model_name: str = "gemini-2.0-flash", max_output_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    Gemini API를 사용하여 일반 텍스트를 생성합니다.

    Args:
        prompt (str): 모델에 전달할 프롬프트 텍스트입니다.
        model_name (str, optional): 사용할 모델의 이름입니다. Defaults to "gemini-2.0-flash".
        max_output_tokens (int, optional): 생성할 최대 토큰 수입니다. Defaults to 500.
        temperature (float, optional): 생성 시 샘플링 온도로, 0과 1 사이의 값입니다. Defaults to 0.7.

    Returns:
        str: 생성된 텍스트입니다.

    Raises:
        Exception: API 호출 또는 기타 오류 발생 시.
    """
    if not API_KEY:
        return "오류: GEMINI_API_KEY가 설정되지 않았습니다."
        
    try:
        model = genai.GenerativeModel(model_name)
        config = GenerationConfig(
            max_output_tokens=max_output_tokens,
            temperature=0.7
        )
        response = model.generate_content(
            contents=[prompt], # 콘텐츠는 항상 리스트 형태로 전달
            generation_config=config
        )
        return response.text
    except Exception as e:
        print(f"텍스트 생성 중 오류 발생: {e}")
        # 프론트엔드에서 오류를 적절히 처리할 수 있도록 예외를 다시 발생시키거나 오류 메시지를 반환합니다.
        raise

# --- 소설 등장인물 분석 지시사항 ---
SYSTEM_PROMPT_CHARACTER_EXTRACTION = """# 소설 등장인물 분석 지시사항

당신은 소설 텍스트를 분석하여 주요 등장인물들의 정보를 추출하는 전문가입니다.
CRITICAL: 분석 결과를 반드시 JSON 형식으로만 출력하세요. 추가적인 설명이나 마크다운 코드 블록 등은 사용하지 마세요. ONLY VALID JSON IS ALLOWED.

## 분석 규칙:

1. 소설 전체 텍스트에서 반복적으로 등장하거나 이야기 전개에 중요한 역할을 하는 **주요 등장인물**들을 식별하세요.
2. 각 인물에 대해 다음 정보를 추출하세요:
    - **name**: 인물의 이름 (가장 일반적으로 불리는 이름).
    - **description**: 인물의 주요 특징. 간략한 외모 묘사, 성격, 다른 인물과의 관계, 작중 역할 등을 포함할 수 있습니다. (1-2 문장으로 요약)
    - **speech_pattern**: 인물의 특징적인 말투나 자주 사용하는 어투, 또는 대표적인 짧은 대사 예시. 이를 통해 인물의 성격이나 감정 상태를 짐작할 수 있어야 합니다. (1-2개 예시)
3. 존댓말/반말 여부, 특정 어휘 사용 빈도 등도 말투 특징에 포함될 수 있습니다.

## 출력 형식:

정확히 다음 JSON 구조로만 출력하세요. 각 인물 정보는 배열의 요소가 됩니다.

```json
[
  {
    "name": "인물 이름",
    "description": "인물에 대한 간략한 설명 (외모, 성격, 역할 등)",
    "speech_pattern": "특징적인 말투 또는 대표적인 짧은 대사 예시 (예: \\"알겠습니다, 도련님.\\", \\"흥, 내가 그런 걸 할 줄 알고?\\")"
  },
  {
    "name": "다른 인물 이름",
    "description": "...",
    "speech_pattern": "..."
  }
]
```

## 예시:

입력 텍스트 (일부 발췌):

"어서 오너라, 나의 오랜 친구여." 백작이 낮은 목소리로 말했다. 그는 은발에 날카로운 눈매를 가졌으며, 언제나 검은색 정장을 고집했다.
"백작님, 또 무슨 꿍꿍이십니까?" 젊은 탐정, 에단이 의심스러운 눈초리로 물었다. 에단은 언제나 활기차고 직설적이었다.
"에단, 자네는 항상 너무 급해. 차나 한잔 들게나." 백작은 여유롭게 웃었다.

예상 출력:

```json
[
  {
    "name": "백작",
    "description": "은발과 날카로운 눈매를 가진 중년 남성. 검은 정장을 선호하며, 여유롭고 속내를 잘 드러내지 않는 성격이다. 에단의 오랜 친구이자 조력자 혹은 경쟁자일 수 있다.",
    "speech_pattern": "\"어서 오너라, 나의 오랜 친구여.\", \"자네는 항상 너무 급해.\""
  },
  {
    "name": "에단",
    "description": "젊은 남성 탐정. 활기차고 직설적인 성격으로, 백작을 다소 의심하면서도 사건 해결을 위해 협력하는 모습을 보인다.",
    "speech_pattern": "\"백작님, 또 무슨 꿍꿍이십니까?\""
  }
]
```
CRITICAL: 분석 결과를 반드시 JSON 형식으로만 출력하세요. 추가적인 설명이나 마크다운 코드 블록 등은 사용하지 마세요. ONLY VALID JSON IS ALLOWED."""

def extract_characters_from_text(novel_text: str, model_name: str = "gemini-2.0-flash") -> list:
    """
    소설 텍스트에서 Gemini API와 지정된 시스템 프롬프트를 사용하여 등장인물 정보를 추출합니다.

    Args:
        novel_text (str): 분석할 소설 텍스트 전체입니다.
        model_name (str, optional): 사용할 모델의 이름입니다. Defaults to "gemini-2.0-flash".

    Returns:
        list: 추출된 등장인물 정보 객체(딕셔너리)의 리스트입니다.

    Raises:
        Exception: API 호출, JSON 파싱 또는 기타 오류 발생 시.
    """
    if not API_KEY:
        # 실제 애플리케이션에서는 빈 리스트나 특정 오류 객체를 반환할 수 있습니다.
        raise ValueError("오류: GEMINI_API_KEY가 설정되지 않아 등장인물 추출을 진행할 수 없습니다.")

    try:
        # 시스템 프롬프트와 함께 모델 초기화
        # 구조화된 JSON 출력을 위해 temperature를 낮게 설정하는 것을 고려 (예: 0.1)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT_CHARACTER_EXTRACTION,
            generation_config=GenerationConfig(temperature=0.1)
        )
        
        response = model.generate_content(contents=[novel_text]) # 소설 텍스트를 contents로 전달
        
        raw_json_output = response.text.strip()
        
        # 모델이 간혹 JSON을 마크다운 코드 블록으로 감싸는 경우가 있어 제거 로직 추가
        if raw_json_output.startswith("```json"):
            raw_json_output = raw_json_output[len("```json"):].strip()
        if raw_json_output.endswith("```"):
            raw_json_output = raw_json_output[:-len("```")].strip()
            
        parsed_characters = json.loads(raw_json_output)
        
        # if not isinstance(parsed_characters, list):
        #     print(f"경고: 등장인물 정보가 리스트 형태가 아닙니다 (실제 타입: {type(parsed_characters)}). 모델이 지시사항을 정확히 따르지 않았을 수 있습니다.")
        #     # 필요에 따라 오류를 발생시키거나, 단일 객체인 경우 리스트로 감싸는 등의 처리를 할 수 있습니다.
        #     # raise ValueError("등장인물 분석 결과가 예상된 리스트 형식이 아닙니다.")

        return parsed_characters
    except json.JSONDecodeError as e:
        print(f"Gemini 응답에서 JSON 디코딩 중 오류 발생: {e}")
        # 디버깅을 위해 원본 응답 텍스트를 로깅할 수 있습니다.
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"원본 응답 텍스트: {response.text}")
        raise
    except Exception as e:
        print(f"등장인물 추출 중 오류 발생: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"오류 발생 시 원본 응답 텍스트: {response.text}")
        elif 'response' in locals() and hasattr(response, 'prompt_feedback'):
             print(f"오류 발생 시 프롬프트 피드백: {response.prompt_feedback}")
        raise

# --- 소설 텍스트 구조 분석 함수 --- 
STRUCTURE_ANALYSIS_SYSTEM_INSTRUCTION = """
# 소설 텍스트 구조적 분석 지시사항

당신은 소설 텍스트를 분석하여 각 문장의 유형, 화자, 감정 및 어조를 식별하는 전문가입니다. 
CRITICAL: 분석 결과를 반드시 JSON 형식으로만 출력하세요. 추가 설명이나 마크다운 코드 블록 등은 사용하지 마세요. ONLY VALID JSON IS ALLOWED.

## 분석 규칙:

1. 텍스트를 문장 또는 의미 단위로 분할하세요.
2. 각 단위를 다음 유형 중 하나로 분류하세요:
   - "dialogue": 인물의 대화 (따옴표로 표시된 경우가 많음)
   - "narration": 일반적인 서술이나 설명
   - "sfx": 효과음이나 의성어/의태어

3. 화자 식별:
   - 대화의 경우, 누가 말했는지 분석하세요 (문맥에서 파악)
   - 내레이션의 경우, "Narrator"로 지정
   - 효과음의 경우, "SFX"로 지정

4. 감정 태깅:
   - Ekman의 6가지 기본 감정 중 하나를 선택: "기쁨", "슬픔", "공포", "분노", "혐오", "놀람"
   - 뚜렷한 감정이 없는 경우 "중립"으로 태깅

5. 어조 태깅:
   - 문장의 말투, 전달 방식을 나타내는 어조 태그 부여
   - 예: "차분함", "긴장됨", "흥분됨", "격앙됨", "엄숙함", "공손함", "위협적", "애원함" 등
   - 억양, 구두점, 어휘 선택 등을 고려하여 결정

6. 표현 가이드 작성:
   - 화자의 감정과 어조를 생생하게 표현하기 위한 자연어 설명 제공
   - 목소리 톤, 발화 속도, 강조점, 억양 변화 등을 포함
   - 딥보이스 AI가 이 대사를 어떻게 읽어야 할지 안내하는 구체적 설명
   - 예: "작은 목소리로 떨리게 말하며 문장 끝을 올리는 듯한 불안한 어조", "힘있고 단호하게 말하되 마지막 단어를 강조"

## 출력 형식:
정확히 다음 JSON 구조로만 출력하세요:

```json
[
  {
    "order": 1,
    "type": "dialogue|narration|sfx",
    "speaker": "캐릭터명|Narrator|SFX",
    "text": "실제 텍스트",
    "emotion": "기쁨|슬픔|공포|분노|혐오|놀람|중립",
    "tone": "어조 태그",
    "expression_guide": "감정과 어조를 자연어로 상세히 설명"
  },
  {
    "order": 2,
    ...
  }
]

```

## 예시:

입력 텍스트:

```

"무슨 일이 있었던 거야?" 민지가 걱정스럽게 물었다.
철수는 한숨을 내쉬었다. "별거 아니야. 그냥... 좀 피곤해."
쏴아아- 빗소리가 점점 거세졌다.
"오늘... 이상한 꿈을 꿨어." 그가 마침내 입을 열었다.

```

예상 출력:

```json

json
[
  {
    "order": 1,
    "type": "dialogue",
    "speaker": "민지",
    "text": "무슨 일이 있었던 거야?",
    "emotion": "공포",
    "tone": "염려됨",
    "expression_guide": "약간 높은 톤으로 시작하고 문장 끝을 올리며, 다급함과 걱정이 섞인 목소리로 말합니다. '무슨'과 '있었던'에 약간의 강조를 둡니다."
  },
  {
    "order": 2,
    "type": "narration",
    "speaker": "Narrator",
    "text": "민지가 걱정스럽게 물었다.",
    "emotion": "중립",
    "tone": "차분함",
    "expression_guide": "담담하고 균일한 톤으로 읽되, '걱정스럽게'라는 단어에 살짝 힘을 주어 상황의 감정을 전달합니다."
  },
  {
    "order": 3,
    "type": "narration",
    "speaker": "Narrator",
    "text": "철수는 한숨을 내쉬었다.",
    "emotion": "슬픔",
    "tone": "지친듯함",
    "expression_guide": "문장을 읽기 전에 작은 한숨을 넣고, 약간 느린 속도로 낮은 톤을 유지하며 지친 느낌을 표현합니다."
  },
  {
    "order": 4,
    "type": "dialogue",
    "speaker": "철수",
    "text": "별거 아니야. 그냥... 좀 피곤해.",
    "emotion": "슬픔",
    "tone": "망설임",
    "expression_guide": "지친 목소리로 시작하고 '그냥' 후에 잠시 멈춤(...)을 표현합니다. 말의 속도가 느리고 에너지가 없으며, 문장의 끝을 살짝 흐리듯 마무리합니다."
  },
  {
    "order": 5,
    "type": "sfx",
    "speaker": "SFX",
    "text": "쿵!",
    "emotion": "중립",
    "tone": "강렬함",
    "expression_guide": "갑작스럽고 큰 소리로, 단호하게 '쿵'을 발음하고 느낌표를 표현하기 위해 소리의 울림을 줍니다."
  },
  {
    "order": 6,
    "type": "narration",
    "speaker": "Narrator",
    "text": "갑자기 어딘가에서 큰 소리가 들렸다.",
    "emotion": "놀람",
    "tone": "긴장됨",
    "expression_guide": "'갑자기'를 강조하고 문장 전체를 약간 빠른 속도로 읽습니다. 약간의 긴장감을 주는 톤을 유지하며 '큰 소리'에 강세를 둡니다."
  }
]

```

CRITICAL: 분석 결과를 반드시 JSON 형식으로만 출력하세요. 추가 설명이나 마크다운 코드 블록 등은 사용하지 마세요. ONLY VALID JSON IS ALLOWED.

이제 아래 텍스트를 분석해 주세요:

[소설 텍스트]
"""

def analyze_novel_structure(novel_text_content: str, model_name: str = "gemini-2.0-flash"):
    """
    소설 텍스트를 분석하여 문장 유형, 화자, 감정, 어조 등을 포함하는 구조화된 데이터를 반환합니다.
    Args:
        novel_text_content (str): 분석할 소설의 전체 텍스트입니다.
    Returns:
        list or dict: 각 문장/단위에 대한 분석 정보(딕셔너리)를 담은 리스트 또는 오류 시 딕셔너리.
                      성공 시 반환 타입은 list. 오류 메시지를 포함하는 경우 dict.
    """

    if not API_KEY:
        # logging.error("GEMINI_API_KEY가 설정되지 않아 소설 구조 분석을 진행할 수 없습니다.")
        # raise ValueError("오류: GEMINI_API_KEY가 설정되지 않아 소설 구조 분석을 진행할 수 없습니다.")
        # API 키 부재 시 일관된 오류 처리 방식으로 변경 (예: ValueError 발생 또는 특정 오류 객체 반환)
        # 여기서는 이전 코드의 print문을 유지하고, 필요 시 로깅 또는 예외 발생으로 수정 가능
        print("오류: GEMINI_API_KEY가 설정되지 않아 소설 구조 분석을 진행할 수 없습니다.")
        return {"error": "GEMINI_API_KEY is not configured."}


    try:
        # 참고: system_instruction 인자는 genai.GenerativeModel 생성 시점에 전달하는 것이 일반적입니다.
        # generate_content 호출 시에는 contents만 전달합니다.
        # temperature와 같은 생성 설정은 GenerationConfig 객체를 통해 모델 생성자 또는 generate_content에 전달할 수 있습니다.
        model = genai.GenerativeModel(
            model_name=model_name, # "gemini-pro" 대신 인자로 받은 model_name 사용
            system_instruction=STRUCTURE_ANALYSIS_SYSTEM_INSTRUCTION,
            generation_config=GenerationConfig(temperature=0.1) # temperature 0.1로 하드코딩
        )
        
        # logging.debug(f"소설 구조 분석 요청: 모델={model_name}, 첫 100자={novel_text_content[:100]}")
        response = model.generate_content(contents=[novel_text_content]) # contents는 리스트 형태로 전달
        
        # logging.debug(f"Gemini API 응답 수신 (구조 분석): {response.text[:200]}...")
        raw_json_output = response.text.strip()
        
        # 모델이 간혹 JSON을 마크다운 코드 블록으로 감싸는 경우가 있어 제거 로직 추가
        if raw_json_output.startswith("```json"):
            raw_json_output = raw_json_output[7:] # "```json\n"
        if raw_json_output.endswith("```"):
            raw_json_output = raw_json_output[:-3]
        cleaned_json_text = raw_json_output.strip()
        
        # 추가 디버깅: 정리된 텍스트 출력
        # logging.debug(f"Cleaned JSON text for structure analysis: {cleaned_json_text[:500]}")

        try:
            analyzed_data = json.loads(cleaned_json_text)

            # 아래의 isinstance 등 형식 검증 로직을 제거하거나 주석 처리합니다.
            # if not isinstance(analyzed_data, list): 
            #     logging.warning(f"analyze_novel_structure: Data is not a list (actual type: {type(analyzed_data)}).")
            #     # 다른 검증 로직이 있다면 그것도 제거/주석 처리
            #     # raise ValueError("Novel structure analysis result is not in the expected list format.")
            
            return analyzed_data
        except json.JSONDecodeError as e:
            logging.error(f"Gemini 구조 분석 응답 JSON 파싱 실패: {e}")
            logging.error(f"파싱 시도한 텍스트 (앞 500자): {cleaned_json_text[:500]}")
            # 오류 발생 시, 파싱 전 텍스트를 반환하여 app.py에서 확인할 수 있도록 함 (또는 None)
            # 혹은 여기서 직접 예외를 발생시켜 호출부에서 처리
            raise ValueError(f"AI 응답이 유효한 JSON이 아닙니다. 내용: {cleaned_json_text[:200]}...")
    except Exception as e:
        logging.error(f"Gemini 구조 분석 API 호출 중 오류 발생: {e}")
        # 특정 예외 유형에 따라 더 구체적인 오류 처리 가능
        # 예: API 할당량 초과, 인증 오류 등
        # 여기서는 포괄적인 예외를 발생시켜 호출부에서 처리하도록 함
        raise RuntimeError(f"Gemini API 호출 중 오류: {str(e)}")



    # ... (기존 테스트 코드 이어서) 

# --- 소설 등장인물-성우 매칭을 위한 시스템 지시문 ---
CHARACTER_VOICE_MATCHING_SYSTEM_INSTRUCTION = """
# 소설 등장인물-성우 매칭 지시사항

당신은 소설 등장인물의 특성을 분석하여 가장 적합한 성우를 매칭하는 전문가입니다.
CRITICAL: 매칭 결과를 반드시 JSON 형식으로만 출력하세요. 추가 설명이나 마크다운 코드 블록 등은 사용하지 마세요. ONLY VALID JSON IS ALLOWED.

## 매칭 규칙:

1. 각 등장인물의 특성(성격, 나이, 성별 등)을 분석하세요.
2. 성우 목록에서 각 성우의 특성(feature)을 확인하세요.
3. 다음 기준으로 가장 적합한 성우를 매칭하세요:
   - 성별 일치 (Gender match)
   - 나이대 적합성 (Age group appropriateness)
   - 성격/특성 일치 (Character traits match)
   - 목소리 특성과 캐릭터 이미지 조화 (Voice characteristics alignment)

4. 각 등장인물에게 반드시 하나의 성우를 매칭하세요.
5. 내레이터(Narrator) 역할이 있는 경우 적절한 성우를 매칭하세요.
6. 등장인물의 특성이 불분명한 경우 가장 중립적인 성우를 선택하세요.

## 출력 형식:
정확히 다음 JSON 구조로만 출력하세요:

```json
{
  "character_name1": "actor_id1",
  "character_name2": "actor_id2",
  "Narrator": "actor_id3"
}
```

반드시 성우의 ID값(id 필드)을 사용하세요. 성우 이름이 아닌 고유 ID가 필요합니다.

CRITICAL: 매칭 결과를 반드시 JSON 형식으로만 출력하세요. 추가 설명이나 마크다운 코드 블록 등은 사용하지 마세요. ONLY VALID JSON IS ALLOWED.
"""

def save_matching_result(character_voice_map, voice_actors, file_id):
    """
    매칭 결과를 지정된 경로에 JSON 파일로 저장합니다.
    
    Args:
        character_voice_map (dict): 등장인물 이름을 키로, 성우 ID를 값으로 하는 매핑 딕셔너리
        voice_actors (list): 성우 정보 객체의 리스트
        file_id (str): 소설 파일 ID
        
    Returns:
        str: 저장된 파일 경로
    """
    try:
        # 파일 이름을 소설 ID로 지정
        filename = f"{file_id}_matching.json"
        file_path = MATCHING_RESULT_PATH / filename
        
        # 성우 ID를 키로 가진 사전 생성 (빠른 참조용)
        voice_actor_dict = {actor['id']: actor for actor in voice_actors}
        
        # 저장할 데이터 준비 - 각 등장인물별 매칭된 성우 ID와 해당 성우의 feature 포함
        enhanced_mapping = {}
        for character_name, actor_id in character_voice_map.items():
            if actor_id in voice_actor_dict:
                # 성우 ID와 함께 feature 정보 저장
                enhanced_mapping[character_name] = {
                    "actor_id": actor_id,
                    "actor_name": voice_actor_dict[actor_id].get('name', ''),
                    "feature": voice_actor_dict[actor_id].get('feature', '')
                }
            else:
                # 매칭된 성우를 찾을 수 없는 경우 ID만 저장
                enhanced_mapping[character_name] = {
                    "actor_id": actor_id,
                    "actor_name": "",
                    "feature": ""
                }
        
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_mapping, ensure_ascii=False, indent=2, fp=f)
            
        logging.info(f"매칭 결과를 저장했습니다: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logging.error(f"매칭 결과 저장 중 오류 발생: {e}")
        return None

def match_characters_with_voice_actors(characters, voice_actors, file_id=None, model_name: str = "gemini-2.0-flash", temperature: float = 0.1) -> dict:
    """
    등장인물과 성우를 매칭하여 최적의 조합을 찾아 반환합니다.
    
    Args:
        characters (list): 등장인물 정보 객체의 리스트
        voice_actors (list): 성우 정보 객체의 리스트
        file_id (str, optional): 소설 파일 ID. 저장 시 파일명으로 사용됩니다.
        model_name (str, optional): 사용할 모델의 이름입니다. Defaults to "gemini-2.0-flash".
        temperature (float, optional): 생성 시 샘플링 온도로, 0과 1 사이의 값입니다. Defaults to 0.1.
        
    Returns:
        dict: 등장인물 이름을 키로, 성우 ID를 값으로 하는 매핑 딕셔너리
    
    Raises:
        ValueError: API 키가 없는 경우
        Exception: API 호출 오류 또는 응답 파싱 오류
    """
    if not API_KEY:
        logging.error("GOOGLE_API_KEY가 설정되지 않아 등장인물-성우 매칭을 진행할 수 없습니다.")
        raise ValueError("GOOGLE_API_KEY is not configured.")
        
    try:
        # 프롬프트 생성을 위한 데이터 준비
        characters_json = json.dumps(characters, ensure_ascii=False, indent=2)
        voice_actors_json = json.dumps(voice_actors, ensure_ascii=False, indent=2)
        
        # Gemini API 프롬프트
        prompt = f"""
        주어진 소설 등장인물과 성우 목록을 분석하여, 각 등장인물에게 가장 적합한 성우를 매칭해주세요.

        성우 목록:
        {voice_actors_json}
        
        등장인물 목록:
        {characters_json}

        각 등장인물의 성격과 특성을 분석하고, 성우의 목소리 특성(feature)과 가장 잘 어울리는 조합을 찾아주세요.
        Narrator(내레이터) 역할에도 적절한 성우를 배정해주세요.
        
        결과는 등장인물 이름을 키로, 성우의 ID 값을 값으로 하는 JSON 객체 형태로 반환해주세요.
        """
        
        # 시스템 지시문과 함께 모델 초기화
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=CHARACTER_VOICE_MATCHING_SYSTEM_INSTRUCTION,
            generation_config=GenerationConfig(temperature=temperature)
        )
        
        logging.info(f"등장인물-성우 매칭 요청: 등장인물 {len(characters)}명, 성우 {len(voice_actors)}명, 모델={model_name}")
        response = model.generate_content(contents=[prompt])
        
        # JSON 형식의 응답 파싱
        raw_json_output = response.text.strip()
        
        # 모델이 간혹 JSON을 마크다운 코드 블록으로 감싸는 경우가 있어 제거 로직 추가
        if raw_json_output.startswith("```json"):
            raw_json_output = raw_json_output[len("```json"):].strip()
        if raw_json_output.endswith("```"):
            raw_json_output = raw_json_output[:-len("```")].strip()
        
        try:
            character_voice_map = json.loads(raw_json_output)
            logging.info(f"등장인물-성우 매칭 성공: {len(character_voice_map)} 매핑")
            
            # 매칭 결과를 JSON 파일로 저장 (file_id가 제공된 경우에만)
            if file_id:
                save_path = save_matching_result(character_voice_map, voice_actors, file_id)
                if save_path:
                    logging.info(f"매칭 결과가 저장되었습니다: {save_path}")
            
            return character_voice_map
        except json.JSONDecodeError as e:
            logging.error(f"Gemini 응답 JSON 파싱 오류: {e}")
            logging.error(f"파싱 시도한 텍스트 (앞 200자): {raw_json_output[:200]}")
            raise ValueError(f"AI 응답이 유효한 JSON이 아닙니다. 내용: {raw_json_output[:200]}...")
            
    except json.JSONDecodeError as e:
        logging.error(f"Gemini 응답 JSON 파싱 오류: {e}")
        # 디버깅을 위해 원본 응답 텍스트를 로깅
        if 'response' in locals() and hasattr(response, 'text'):
            logging.error(f"원본 응답 텍스트: {response.text}")
        raise
    except Exception as e:
        logging.error(f"Gemini를 사용한 매칭 중 오류 발생: {str(e)}")
        if 'response' in locals() and hasattr(response, 'text'):
            logging.error(f"오류 발생 시 원본 응답 텍스트: {response.text}")
        raise
