# AI 기반 오디오북 생성 시스템

인공지능을 활용하여 소설 텍스트를 자연스러운 오디오북으로 변환하는 시스템입니다.

## 프로젝트 개요

이 프로젝트는 소설 텍스트 파일을 업로드하고, AI를 활용하여 대화, 내레이션, 효과음 등으로 구조화한 후, 적합한 성우 음성으로 오디오북을 생성하는 시스템을 개발합니다.

## 주요 기능

- 텍스트 파일 업로드 및 소설 내용 추출
- Gemini API를 이용한 텍스트 분석 및 구조화
- 등장인물에 맞는 최적의 성우 음성 매칭
- ElevenLabs API를 통한 자연스러운 음성 합성
- 오디오북 플레이어 및 편집 인터페이스

## 기술 스택

- **프론트엔드**: React (Vite)
- **백엔드**: Flask (Python)
- **AI API**: Google Gemini 2.5, ElevenLabs

## 프로젝트 진행 상황

### 전체 진행률
- 태스크: 15개 중 2개 완료 (13.3%)
- 서브태스크: 23개 중 15개 완료 (65.2%)

### 완료된 작업
- ✅ 파일 업로드 및 텍스트 추출 시스템 구현
- ✅ Gemini API를 이용한 인물-음성 매칭 시스템 구현

### 진행 중인 작업
- 🔄 기본 웹 인터페이스 구현

### 다음 작업
- 프로젝트 초기 설정 및 개발 환경 구성 완료
- Gemini API를 이용한 텍스트 분석 및 전처리 시스템 구현
- ElevenLabs API를 이용한 음성 생성 시스템 구현

## 설치 및 실행 방법

### 백엔드 설정
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 프론트엔드 설정
```bash
cd frontend
npm install
npm run dev
```

## 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다. 