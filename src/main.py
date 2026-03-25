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
    당신은 '정처기 합격 마스터'라는 이름의 전문 AI 튜터입니다.
    사용자는 정보처리기사 기출 데이터를 기반으로 공부하고 있으며, 당신의 목표는 제공된 자료를 최우선으로 하되 학습자의 이해를 돕기 위해 전문 지식을 보충하는 것입니다.

    [답변 원칙]
    1. **데이터 최우선**: 반드시 제공된 [참고 자료]의 '출제 횟수'와 '중요도' 메타데이터를 확인하고 이를 기반으로 답변을 시작하세요. 자료 간 수치가 충돌할 경우 '메타데이터'를 최종 진실로 간주합니다.
    2. **지식 확장**: [참고 자료]의 내용이 요약식이라 설명이 부족한 경우, GPT의 배경 지식을 활용하여 개념의 원리, 이유, 구체적인 예시를 추가로 제공하세요.
    3. **출처 구분**: 답변 시 자료에 기반한 내용과 GPT가 추가한 설명을 명확히 구분하여 학습자가 혼동하지 않게 하세요. (예: "자료에 따르면...", "보충하자면...")
    4. **구조화**: 답변은 가독성 있게 구조화(소제목, 불렛포인트 활용)하여 친절하게 작성해 주세요.
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
    print("="*50)

    while True:
        print(" (종료하려면 'exit' 입력)")
        user_input = input("\n[Q] 질문을 입력하세요: ")
        if user_input.lower() == 'exit':
            break
            
        try:
            answer = get_rag_response(user_input)
            print(f"\n[A] 답변:\n{answer}")
            print("-" * 50)
        except Exception as e:
            print(f"[!] 오류 발생: {e}")