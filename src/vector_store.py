import json
import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# 1. .env 파일의 내용을 로드하고 os.getenv()를 통해 환경 변수를 가져옵니다.
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = os.getenv("DB_PATH", "db/pass_master_db") # 기본값 설정 가능
DATA_PATH = os.getenv("DATA_PATH", "data/processed_chunks.json")

def ingest_data():
    if not API_KEY:
        print("[!] API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    # 2. JSON 데이터 로드
    if not os.path.exists(DATA_PATH):
        print(f"[!] {DATA_PATH} 파일이 없습니다. 먼저 chunker.py를 실행하세요.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"[*] 환경 변수 로드 완료. DATA 경로: {DATA_PATH}")

    # 3. ChromaDB 및 임베딩 함수 설정 (OpenAI 모델 사용)
    # 비용이 가장 저렴하고 성능이 좋은 text-embedding-3-small 모델을 씁니다.
    client = chromadb.PersistentClient(path=DB_PATH)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=API_KEY,
        model_name="text-embedding-3-small"
    )

    # 4. 컬렉션 생성 (이미 있으면 가져옴)
    collection = client.get_or_create_collection(
        name="juchungki_exam",
        embedding_function=openai_ef
    )

    # 5. 데이터 준비 및 메타데이터 정제
    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        doc = chunk["document"]
        meta = chunk["metadata"]
        
        # ChromaDB는 빈 리스트를 메타데이터로 받지 못함
        if not meta.get("exam_dates") or len(meta["exam_dates"]) == 0:
            meta["exam_dates"] = ["None"]
            
        documents.append(doc)
        metadatas.append(meta)
        
        ids.append(str(meta["id"]))
    # documents = [c["document"] for c in chunks]
    # metadatas = [c["metadata"] for c in chunks]
    # ids = [c["metadata"]["id"] for c in chunks]

    # 6. DB 저장 (Upsert: 없으면 추가, 있으면 업데이트)
    print(f"[*] {len(ids)}개의 조각을 벡터화하여 DB에 저장 중...")
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"[*] 저장 완료! DB 경로: {DB_PATH}")

# --------------------------------------------------
# [추가] 하이브리드 검색 함수 (Read 로직)
# --------------------------------------------------
def hybrid_query(collection, query_text, n_results=5):
    """
    벡터 검색(의미) + 키워드 매칭(고유명사) 가중치를 결합한 검색
    """
    # 1. 벡터 검색 수행 (임베딩 유사도 기반)
    vector_results = collection.query(
        query_texts=[query_text],
        n_results=n_results * 2  # 후보군을 넓게 뽑아 리랭킹 준비
    )
    
    docs = vector_results['documents'][0]
    metas = vector_results['metadatas'][0]
    distances = vector_results['distances'][0]
    
    # 2. 키워드 부스팅 (Keyword Boosting)
    # 질문의 키워드가 문서에 직접 포함되면 거리 점수를 깎아서(유사도 높임) 순위 상승
    keywords = query_text.split()
    hybrid_candidates = []
    
    for i, doc in enumerate(docs):
        score = distances[i] # 기본 거리값 (작을수록 좋음)
        
        # 키워드 매칭 시 보너스 (가중치 0.1은 테스트하며 조절)
        match_count = sum(1 for kw in keywords if kw.lower() in doc.lower())
        score -= (match_count * 0.1) 
        
        hybrid_candidates.append((doc, metas[i], score))
    
    # 3. 보정된 점수 기준으로 재정렬
    hybrid_candidates.sort(key=lambda x: x[2])
    
    # 4. 최종 결과 포맷팅 (ChromaDB 결과 형식과 유사하게 반환)
    return {
        'documents': [[x[0] for x in hybrid_candidates[:n_results]]],
        'metadatas': [[x[1] for x in hybrid_candidates[:n_results]]],
        'scores': [[x[2] for x in hybrid_candidates[:n_results]]]
    }

if __name__ == "__main__":
    ingest_data()