import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

def test_search(query):
    # 1. 환경 설정
    API_KEY = os.getenv("OPENAI_API_KEY")
    DB_PATH = os.getenv("DB_PATH", "db/pass_master_db")
    
    client = chromadb.PersistentClient(path=DB_PATH)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=API_KEY,
        model_name="text-embedding-3-small"
    )

    # 2. 컬렉션 로드
    collection = client.get_collection(
        name="juchungki_exam",
        embedding_function=openai_ef
    )

    # 3. 검색 수행 (유사한 상위 3개 추출)
    print(f"\n[Q] 질문: {query}")
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    # 4. 결과 출력
    print("-" * 50)
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        
        print(f"[{i+1}순위] ID: {meta['id']} | 제목: {meta['title']} (유사도 거리: {distance:.4f})")
        print(f"내용 요약: {doc[:150]}...")
        print("-" * 50)

if __name__ == "__main__":
    # 테스트하고 싶은 질문을 던져보세요!
    test_search("사회 공학이 뭐야?")
    # test_search("버전 관리 도구 중 분산 저장소 방식 설명해줘")