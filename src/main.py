import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
from src.analyzer import StatsAnalyzer
from src.vector_store import hybrid_query

load_dotenv()

# 1. 환경 변수 및 클라이언트 설정
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "pass_master_db")

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
    # get_collection 대신 안전하게 생성/가져오기 사용
    collection = chroma_client.get_or_create_collection(
        name="juchungki_exam",
        embedding_function=openai_ef
    )

    # 만약 데이터가 하나도 없다면 안내 메시지 출력
    if collection.count() == 0:
        return "현재 데이터베이스에 기출 데이터가 로드되지 않았습니다. 관리자에게 문의하세요."

    # 유사도 높은 상위 5개 섹션 추출 (너무 많으면 비용 상승 및 혼란)
    results = hybrid_query(
        collection=collection,
        query_text=query,
        n_results=5  # 결과 개수를 조금 넉넉히 가져온 뒤
    )

    # 검색된 내용이 없으면 조기 종료
    if not results['documents'][0]:
        return "죄송합니다. 해당 내용에 대한 기출 데이터가 없습니다."
    
    # [Re-ranking 로직] 제목에 검색어가 포함된 것을 리스트 최상단으로 이동
    docs = results['documents'][0]
    metas = results['metadatas'][0]

    combined = list(zip(docs, metas))
    # 제목(title)에 검색어가 포함되어 있으면 우선순위(0), 아니면 (1)로 정렬
    clean_query = query.replace(" ", "").lower() #공백 제거, 소문자 변환
    combined.sort(key=lambda x: 0 if clean_query in x[1].get('title', '').replace(" ", "").lower() else 1)

    # 상위 2개 추출
    final_docs = [c[0] for c in combined[:2]]
    final_metas = [c[1] for c in combined[:2]]

    # --------------------------------------------------
    # 단계 2: 프롬프트 구성 (Prompt Engineering)
    # --------------------------------------------------
    # 검색된 데이터를 GPT가 읽기 좋은 '문맥(Context)'으로 변환
    context = ""
    
    # 실기 시험 날짜 리스트
    PRACTICAL_DATES = ['20.5', '20.7', '20.10', '20.11', '21.4', '21.7', '21.10', '22.5', '22.10', '23.4', '23.10', '24.4', '24.7', '24.10', '25.4', '25.7', '25.11']

    # results['documents'][0] 대신 정렬된 final_docs를 사용
    for i in range(len(final_docs)):
        doc = final_docs[i]
        meta = final_metas[i]

        # 전체 날짜 중 실기 날짜만 필터링
        all_dates = meta.get('exam_dates', [])
        actual_practical_dates = [d for d in all_dates if d in PRACTICAL_DATES]
        
        # 실기 기록 여부에 따른 텍스트 생성
        if actual_practical_dates:
            practical_info = f"실기 출제 기록 있음 (해당 날짜: {', '.join(actual_practical_dates)})"
        else:
            practical_info = "실기 출제 기록 없음 (필기 전용)"

        context += f"[참고 자료 {i+1}]\n"
        context += f"ID: {meta['id']} | 제목: {meta['title']} | 중요도: {meta['importance']}\n"
        context += f"구분: {practical_info}\n"
        context += f"전체(필기 포함) 기출 횟수: {meta['occurrence_count']}회 | 전체(필기 포함) 기출 날짜: {', '.join(meta['exam_dates'])}\n"
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

    [실기 시험 판별 원칙]
    1. 사용자가 '실기' 출제 여부를 물을 경우, 반드시 각 자료의 [구분] 항목에 적힌 '실기 출제 날짜'만 언급하세요.
    2. [구분]에 '실기 출제 기록 없음'이라고 적혀 있다면, 다른 날짜 데이터가 있더라도 절대로 실기에 나왔다고 답변해서는 안 됩니다.
    3. 실기 출제 날짜를 나열할 때는 제공된 [구분] 안의 날짜만 사용하고, '필기' 날짜와 섞어서 답변하지 마세요.
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
    """통계 기반 답변 생성 (실기/전체 모드 자동 분기)"""
    # 질문에 '실기'가 포함 여부 판단
    is_practical_mode = '실기' in query

    # 상위 5개 추출
    top_data = analyzer.get_top_n(5, is_practical_only=is_practical_mode)

    mode_text = "실기 시험" if is_practical_mode else "전체(필기+실기)"
    
    # LLM에게 전달할 통계용 시스템 프롬프트
    stats_system_prompt = """
    당신은 '정처기 데이터 분석관'입니다. 
    제공된 [{mode_text}] 기준 통계 데이터를 바탕으로 출제 경향을 분석하여 보고서 형식으로 답변하세요.
    - 순위와 출제 횟수를 명확히 표기하세요.
    - 제목 바로 옆에 [ID: 번호]를 반드시 표기하세요.
    - 학습자가 어떤 파트(ID)를 집중적으로 공부해야 할지 전략을 제시하세요.
    """
    
    context = f"다음은 {mode_text} 기출 데이터 통계입니다:\n"
    for i, (item, count) in enumerate(top_data, 1):
        # 계층 구조 반영: item['metadata']에서 추출
        meta = item.get('metadata', {})
        item_id = meta.get('id', 'N/A')
        item_title = meta.get('title', '제목 없음')
        if is_practical_mode:
            # 실기 모드일 경우 위에서 계산한 _temp_count를 사용
            count
        else:
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