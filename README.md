# Pass-Master-RAG 🎓
> **PDF 데이터를 활용한 지능형 기출 분석 RAG 시스템**

본 프로젝트는 정보처리기사 핵심 요약 데이터(PDF)를 정밀하게 파싱하여, 사용자 질문에 대해 근거 자료(출제 횟수, 중요도)를 바탕으로 답변하는 AI 튜터 시스템입니다.

---

## 🛠️ 기술 스택
* **Language:** Python 3.14.0
* **Vector DB:** ChromaDB (Persistent Storage)
* **LLM:** OpenAI GPT-4o / text-embedding-3-small
* **Environment:** `python-dotenv`, `pdfplumber`

---

## 🛠 세팅 방법
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
4. data 폴더에 pdf 파일 넣기

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

## 🛠️ 그외 스크립트 설명
`./src/parser.py`: 출제 날짜 추출 스크립트
`search_test.py`: vector_store.py 실행 후 벡터화 확인 테스트 질문 (정상 답변: [1순위] ID: 201 '사회 공학' 이후 3순위까지 답변)
---

## 🚀 Key Features & Pipeline

### 1. Data ETL (Extraction, Transformation, Loading)
* **PDF Parsing:** `pdfplumber`를 이용해 텍스트 추출 후 정규표현식(`re`)을 통해 301개의 섹션으로 분리.
* **Lookback Window Optimization:** 섹션 경계에서 기출 날짜 누락을 방지하기 위해 100자 내외의 `lookback_window` 전략 사용.
* **Metadata Enrichment:** 각 섹션별 `ID`, `중요도(A/B/C)`, `출제 횟수`, `기출 날짜`를 추출하여 구조화된 JSON 데이터 생성.

### 2. Vector Store Ingestion
* **Embedding:** OpenAI의 `text-embedding-3-small` 모델을 활용하여 텍스트를 고차원 벡터로 변환.
* **Data Integrity:** 빈 텍스트(`""`) 및 중복 ID 필터링 로직을 통해 `AuthenticationError` 및 `BadRequestError` 방지.
* **Storage:** ChromaDB를 사용하여 벡터와 메타데이터를 로컬에 저장.

### 3. RAG (Retrieval-Augmented Generation)
* **Semantic Search:** 질문의 의미를 분석하여 가장 연관성 높은 K개 섹션 추출.
* **Context Augmentation:** 검색된 지식 파편과 메타데이터를 LLM 프롬프트에 결합.
* **Generation:** GPT-4o를 통해 근거 데이터에 기반한 답변 생성 (Hallucination 최소화).



---

## 📈 Troubleshooting (Problem Solving)
* **데이터 밀림 현상:** 섹션 구분 시 날짜 정보가 다음 섹션으로 넘어가는 문제를 인덱스 기반 슬라이싱과 윈도우 크기 조정(150자→100자)으로 해결.
* **빈 텍스트 오류:** 데이터 전처리 과정에서 발생하는 공백 섹션을 사전 필터링하여 API 호출 에러 차단.
* **ID 무결성:** `upsert` 시 ID를 문자열로 강제 변환하고 중복을 체크하여 DB 안정성 확보.

---

## 📂 Project Structure
```text
Pass-Master-RAG/
├── src/
│   ├── chunker.py         # PDF 텍스트 파싱 및 JSON 생성
│   ├── vector_store.py    # ChromaDB 데이터 입고 (Embedding)
│   ├── search_test.py     # 검색 엔진 성능 테스트
│   └── main.py            # 최종 RAG 챗봇 실행 파일
├── data/
│   └── processed_chunks.json
├── db/                    # ChromaDB 저장소
└── .env                   # API Key 및 경로 설정
```

---

## 📝 Future Improvements
* **Hybrid Search:** 키워드(BM25)와 벡터 검색을 혼합하여 고유 명사 검색률 향상.
* **Analytics Router:** "가장 많이 출제된 것"과 같은 통계성 질문 시 메타데이터를 직접 집계하여 답변하는 로직 추가.
* **Web UI:** Streamlit을 활용한 사용자 친화적 인터페이스 구축.

---
