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