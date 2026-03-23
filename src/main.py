import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 1. 환경 변수 및 클라이언트 설정
API_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = os.getenv("DB_PATH", "db/pass_master_db")

if not API_KEY:
    raise ValueError("[!] .env 파일에 OPENAI_API_KEY를 설정하세요.")

# ChromaDB 클라이언트 (Retriever)
chroma_client = chromadb.PersistentClient(path=DB_PATH)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY,
    model_name="text-embedding-3-small"
)

# OpenAI 클라이언트 (Generator) - GPT-4o 사용 권장
llm_client = OpenAI(api_key=API_KEY)

def get_rag_response(query):
    # --------------------------------------------------
    # 단계 1: 데이터 검색 (Retrieval)
    # --------------------------------------------------
    collection = chroma_client.get_collection(
        name="juchungki_exam",
        embedding_function=openai_ef
    )

    # 유사도 높은 상위 2개 섹션 추출 (너무 많으면 비용 상승 및 혼란)
    results = collection.query(
        query_texts=[query],
        n_results=2
    )

    # 검색된 내용이 없으면 조기 종료
    if not results['documents'][0]:
        return "죄송합니다. 해당 내용에 대한 기출 데이터가 없습니다."

    # --------------------------------------------------
    # 단계 2: 프롬프트 구성 (Prompt Engineering)
    # --------------------------------------------------
    # 검색된 데이터를 GPT가 읽기 좋은 '문맥(Context)'으로 변환
    context = ""
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        context += f"[참고 자료 {i+1}]\n"
        context += f"ID: {meta['id']} | 제목: {meta['title']} | 중요도: {meta['importance']}\n"
        context += f"출제 횟수: {meta['occurrence_count']}회 | 기출 날짜: {', '.join(meta['exam_dates'])}\n"
        context += f"내용: {doc}\n\n"

    # 시스템 프롬프트: GPT의 역할과 규칙 정의 (핵심!)
    system_prompt = """
    당신은 '정처기 합격 마스터'라는 이름의 AI 튜터입니다. 
    사용자는 정보처리기사 기출 데이터를 기반으로 공부하고 있습니다.
    반드시 제공된 [참고 자료]의 내용만을 바탕으로 정확하게 답변해야 합니다.
    자료에 없는 내용은 절대로 추측하여 지어내지 마세요.
    답변은 친절하고 이해하기 쉽게 구조화하여 작성해 주세요.
    가장 중요한 것은 '제공된 데이터의 정확성'입니다.
    """

    # 유저 프롬프트: 질문과 문맥 전달
    user_prompt = f"""
    [질문]: {query}

    [참고 자료]:
    {context}
    """

    # --------------------------------------------------
    # 단계 3: 답변 생성 (Generation) - GPT-4o 호출
    # --------------------------------------------------
    print(f"[*] GPT-4o에게 질문을 던집니다... (검색된 ID: {results['metadatas'][0][0]['id']})")
    
    response = llm_client.chat.completions.create(
        model="gpt-4o", # 성능과 가성비가 가장 좋은 모델
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1, # 창의성 낮춤 (사실 기반 답변 유도)
        max_tokens=800 # 답변 길이 제한
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print("="*50)
    print(" 정처기 합격 마스터 RAG 챗봇 초기화 완료")
    print(" (종료하려면 'exit' 입력)")
    print("="*50)

    while True:
        user_input = input("\n[Q] 질문을 입력하세요: ")
        if user_input.lower() == 'exit':
            break
            
        try:
            answer = get_rag_response(user_input)
            print(f"\n[A] 답변:\n{answer}")
            print("-" * 50)
        except Exception as e:
            print(f"[!] 오류 발생: {e}")