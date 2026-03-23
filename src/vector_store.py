import json
import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# 1. 초기 설정
API_KEY = "YOUR_OPENAI_API_KEY"  # 실제 키로 교체하거나 .env 사용 권장
DB_PATH = "db/pass_master_db"
DATA_PATH = "data/processed_chunks.json"

def ingest_data():
    # 2. JSON 데이터 로드
    if not os.path.exists(DATA_PATH):
        print(f"[!] {DATA_PATH} 파일이 없습니다. 먼저 chunker.py를 실행하세요.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

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

    # 5. 데이터 준비
    documents = [c["document"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [c["metadata"]["id"] for c in chunks]

    # 6. DB 저장 (Upsert: 없으면 추가, 있으면 업데이트)
    print(f"[*] {len(ids)}개의 조각을 벡터화하여 DB에 저장 중...")
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"[*] 저장 완료! DB 경로: {DB_PATH}")

if __name__ == "__main__":
    ingest_data()