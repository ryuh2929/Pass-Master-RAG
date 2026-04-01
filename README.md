# 🎓 Pass-Master-RAG 
> **PDF 데이터를 활용한 지능형 기출 분석 RAG 시스템**

본 프로젝트는 정보처리기사 핵심 요약 데이터(PDF)를 정밀하게 파싱하여, 사용자 질문에 대해 근거 자료(출제 횟수, 중요도)를 바탕으로 답변하는 AI 튜터 시스템입니다.

---

## 💬 Streamlit 페이지
<img width="787" height="819" alt="image" src="https://github.com/user-attachments/assets/d4bd8f67-8ce8-465e-95b0-ce0fbc1fbc76" />

---

<img width="775" height="489" alt="image" src="https://github.com/user-attachments/assets/cc7d4207-9abb-43ee-8c61-416eef04d8e8" />

---

<img width="770" height="348" alt="image" src="https://github.com/user-attachments/assets/235685ee-804f-4ad7-bf5a-5a6743c4259d" />

---

## 💻 터미널 구동 화면
<img width="862" height="267" alt="image" src="https://github.com/user-attachments/assets/a860ea72-97cc-4a52-a156-1dfe89dc5c23" />
<img width="896" height="618" alt="image" src="https://github.com/user-attachments/assets/f8b476c7-3f3c-4fc9-a235-86d00cd8c6a6" />
<img width="895" height="297" alt="image" src="https://github.com/user-attachments/assets/796c2716-e210-4993-8115-c8466f78c9a3" />
<img width="888" height="246" alt="image" src="https://github.com/user-attachments/assets/100c58ab-1339-4b87-9c23-d685e1d36693" />

---

## 🛠️ 기술 스택
### 🔹 Language & Environment
- **Python 3.14.0+**: 메인 개발 언어 및 데이터 전처리
- **python-dotenv**: 환경 변수 및 API Key 관리
- **pdfplumber**: PDF 텍스트 추출 및 구조화

### 🔹 AI & Data Pipeline
- **LLM**: OpenAI **GPT-4o** (추론 및 답변 생성)
- **Embedding**: **text-embedding-3-small** (고성능 벡터 임베딩)
- **Vector DB**: **ChromaDB** (Persistent Storage를 통한 로컬 데이터 영구 저장)
- **RAG Logic**: BM25(키워드) + Vector(시맨틱) **하이브리드 검색** 구현

### 🔹 Deployment & UI
- **Frontend**: **Streamlit** (대화형 데이터 분석 웹 인터페이스)
- **Cloud**: **Streamlit Cloud** (지속적 배포 및 호스팅)
- **Version Control**: Git / GitHub (브랜치 기반 데이터 격리 관리)

---

## ⚙️ 세팅 방법
1. 가상환경 생성 및 활성화(Windows):
   ```bash
   python -m venv venv
   source venv/Scripts/activate
   ``` 
2. 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. 환경 변수 설정 (.env)
   프로젝트 루트 디렉토리에 .env 파일을 생성하고 아래 내용을 입력
   ```
   OPENAI_API_KEY=여기에 본인의 openAI API를 입력
   DB_PATH=db/pass_master_db
   DATA_PATH=data/processed_chunks.json
   ```
4. 데이터 준비: `/data` 폴더에 pdf 파일 넣기


## 🏃 실행 순서
```bash
# 1. PDF 파일을 텍스트로 파싱 및 JSON 형식으로 /data/processed_chunks.json에 저장
python3 ./src/chunker.py

# 2. 파싱된 데이터 검증 (누락 및 중복 ID 체크 - 선택 사항)
python3 ./src/check_ids.py

# 3. JSON 데이터를 vector DB로 /db/pass_master_db/에 저장
python3 ./src/vector_store.py

# 4. RAG 실행
python3 ./src/main.py
```


## ✨ Streamlit 실행 (로컬)
```bash
streamlit run app.py
```


## 🔍 그 외 스크립트 설명

`./src/parser.py`: 출제 날짜 추출 스크립트

`search_test.py`: vector_store.py 실행 후 벡터화 확인 테스트 (정상 답변: [1순위] ID: 201 '사회 공학' 이후 3순위까지 출력)

---

## 🚀 주요 기능 및 파이프라인

### 1. 데이터 전처리 (Extraction, Transformation, Loading)
* **PDF Parsing:** `pdfplumber`를 이용해 텍스트 추출 후 정규표현식(`re`)을 통해 301개의 섹션으로 분리
* **Lookback Window 최적화:** 섹션 경계에서 기출 날짜 누락을 방지하기 위해 100자 내외의 `lookback_window` 전략 사용
* **Metadata 강화:** 각 섹션별 `ID`, `중요도(A/B/C)`, `출제 횟수`, `기출 날짜`를 추출하여 구조화된 JSON 데이터 생성

### 2. 벡터 DB화
* **Embedding:** OpenAI의 `text-embedding-3-small` 모델을 활용하여 텍스트를 고차원 벡터로 변환
* **Data Integrity:** 빈 텍스트(`""`) 및 중복 ID 필터링 로직을 통해 `AuthenticationError` 및 `BadRequestError` 방지
* **Storage:** ChromaDB를 사용하여 벡터와 메타데이터를 로컬에 저장

### 3. RAG 시스템 구축
* **의미 기반 검색:** 질문의 의미를 분석하여 가장 연관성 높은 K개 섹션 추출
* **컨텍스트 강화:** 검색된 지식 파편과 메타데이터를 결합하여 LLM에 전달
* **답변 생성:** GPT-4o를 통해 근거 데이터에 기반한 답변 생성 (Hallucination 최소화)

---

## 📈 트러블 슈팅
* **PDF 1, 2단 레이아웃 문제:** 페이지 중앙 좌표 기준으로 물리적으로 분할하여 추출, 1단 레이아웃 페이지는 체크 후 예외 처리
* **데이터 밀림 현상:** 섹션 구분 시 날짜 정보가 다음 섹션으로 넘어가는 문제를 인덱스 기반 슬라이싱과 윈도우 크기 조정(150자→100자)으로 해결
* **빈 텍스트 오류:** 데이터 전처리 과정에서 발생하는 공백 섹션을 사전 필터링하여 API 호출 에러 차단
* **ID 무결성:** `upsert` 시 ID를 문자열로 강제 변환하고 중복을 체크하여 DB 안정성 확보
* **타이틀 일치 우선:** 질문과 유사한 단어가 여러번 나오면 벡터 유사도가 더 높아 답변 우선 순위가 높아지는 문제를 제목 일치 기반의 Re-ranking 로직 구현으로 해결

---

## ✅ 향후 개선 계획
### 🔹 1단계: 핵심 엔진 구축 (완료)
* [x] ~~**하이브리드 검색:** 키워드(BM25)와 벡터 검색을 혼합하여 고유 명사 검색률 향상~~ (추가 완료)
* [x] ~~**통계 전용 라우터:** "가장 많이 출제된 것"과 같은 통계성 질문 시 메타데이터를 직접 집계하여 답변하는 로직 추가~~ (추가 완료)
* [x] ~~**웹 UI:** Streamlit을 활용한 사용자 친화적 인터페이스 구축~~ (추가 완료)

### 🔸 2단계: 시스템 고도화 (계획)
- [ ] **LangGraph 리팩토링**: 에이전틱 워크플로우를 통한 답변 자가 검수 로직 도입
- [ ] **RAGas 정량 평가**: 답변의 충실도 및 관련성 지표 측정 및 데이터셋 구축
- [ ] **멀티 세션 관리**: 사용자별 대화 히스토리 저장 및 맥락 유지 기능 추가

