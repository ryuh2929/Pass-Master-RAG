import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
from analyzer import StatsAnalyzer

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
    당신은 '정처기 합격 마스터' 전문 AI 튜터입니다. 
    제공된 [참고 자료]를 최우선으로 하며, 불필요한 사족 없이 핵심만 전달합니다.

    [답변 원칙]
    1. **데이터 지표 필수 명시**: 답변 서두에 [ID], [출제 횟수], [중요도]를 요약 제시하여 학습자가 우선순위를 즉각 파악하게 합니다.
    2. **엄격한 정보 출처 구분**: 
    - [요약 정보]: 제공된 자료 내의 텍스트와 기출 날짜를 요약합니다. (예: "데이터 [ID: 번호]에 따르면...")
    - [심화 학습]: 자료에 없는 원리나 상세 예시가 질문 해결에 **반드시** 필요한 경우에만 작성하세요. 
    3. **중복 및 사족 금지 (중요)**: 
    - 답변의 마지막에 앞에서 했던 내용을 다시 정리하거나 요약하는 **맺음말을 절대로 작성하지 마세요.**
    - [요약 정보]와 [심화 학습]에서 내용이 겹친다면, [요약 정보]를 우선하고 [심화 학습]에서는 새로운 정보만 다룹니다.
    4. **구조화 및 언어**: 모든 답변은 한국어로 작성하며, 수험생 수준에 맞춰 소제목과 불렛포인트를 활용해 간결하게 작성하세요. 텍스트의 나열보다 가독성을 최우선으로 합니다.
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

# analyzer 인스턴스 생성
analyzer = StatsAnalyzer()

def is_statistical_query(query):
    # 통계 의도를 파악하는 키워드 정의
    keywords = ['순위', '가장 많이', '빈출', 'TOP', '통계', '중요한']
    return any(kw in query for kw in keywords)

def get_stats_response(query):
    """통계 기반 답변 생성"""
    top_data = analyzer.get_top_n(5) # 상위 5개 추출
    
    # LLM에게 전달할 통계용 시스템 프롬프트
    stats_system_prompt = """
    당신은 '정처기 데이터 분석관'입니다. 
    제공된 통계 데이터를 바탕으로 출제 경향을 분석하여 보고서 형식으로 답변하세요.
    - 순위와 출제 횟수를 명확히 표기하세요.
    - 각 순위의 제목 출력 시, 반드시 제목 바로 옆에 ID를 붙여서 표기하세요.
    - 학습자가 어떤 파트(ID)를 집중적으로 공부해야 할지 전략을 제시하세요.
    """
    
    context = "다음은 기출 데이터 통계입니다:\n"
    for i, item in enumerate(top_data, 1):
        # 계층 구조 반영: item['metadata']에서 추출
        meta = item.get('metadata', {})
        item_id = meta.get('id', 'N/A')
        item_title = meta.get('title', '제목 없음')
        count = meta.get('occurrence_count', 0)
        importance = meta.get('importance', '미정')
        
        context += f"{i}위. [ID: {item_id}] {item_title} - {count}회 출제 (중요도: {importance})\n"

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": stats_system_prompt},
            {"role": "user", "content": f"질문: {query}\n\n{context}"}
        ],
        temperature=0.1
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
            
        try:# 의도 파악 로직 (Intent Routing)
            if is_statistical_query(user_input):
                print("[*] 통계 분석 모드로 답변을 생성합니다...")
                answer = get_stats_response(user_input)
            else:
                answer = get_rag_response(user_input)
                
            print(f"\n[A] 답변:\n{answer}")
            print("-" * 50)
        except Exception as e:
            print(f"[!] 오류 발생: {e}")