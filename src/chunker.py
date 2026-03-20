import pdfplumber
import glob
import re

def chunk_pdf_text(full_text, valid_dates):
    """
    full_text: pdfplumber로 추출한 전체 텍스트
    valid_dates: 아까 추출한 34개의 기출 날짜 세트 (set)
    """
    # 1. 소제목 패턴: 숫자3자리 + 제목 + 중요도(A/B/C)
    # 예: 001 나선형 모형 B 
    section_pattern = re.compile(r'(\d{3})\s+(.+?)\s+([A-C]?)(\n|$)')
    
    # 2. 섹션별로 쪼개기 위해 매칭되는 지점(index) 찾기
    matches = list(section_pattern.finditer(full_text))
    chunks = []

    for i in range(len(matches)):
        start_idx = matches[i].start()
        # 다음 섹션이 있으면 거기까지, 없으면 끝까지
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
        
        # 해당 섹션의 전체 텍스트 (번호 + 제목 + 본문 포함)
        section_text = full_text[start_idx:end_idx].strip()
        
        # 메타데이터 추출
        item_id = matches[i].group(1)
        title = matches[i].group(2).strip()
        importance = matches[i].group(3).strip() or "N/A"
        
        # 3. 본문 내 날짜 매핑 (세부 항목 날짜까지 싹 긁어모음)
        # 아까 만든 date_pattern을 재사용하여 본문의 모든 날짜 추출
        found_in_section = set(re.findall(r'(?<!\d)\d{2}\.(?:1[0-2]|[1-9])(?!\d)', section_text))
        
        # 우리가 가진 34개 유효 날짜 리스트와 교집합 확인
        actual_exam_dates = sorted(list(found_in_section.intersection(valid_dates)))
        
        # 결과 딕셔너리 생성
        chunks.append({
            "document": section_text,  # LLM이 읽을 본문 (대단원 정보는 나중에 추가 가능)
            "metadata": {
                "id": item_id,
                "title": title,
                "importance": importance,
                "exam_dates": actual_exam_dates,
                "occurrence_count": len(actual_exam_dates),
                "is_practical": any(d in ['20.5','20.7','20.10','20.11','21.4','21.7','21.10','22.5','22.10','23.4','23.10','24.4','24.10','25.4','25.7','25.11'] for d in actual_exam_dates) # 실기 날짜 포함 여부
            }
        })

    return chunks

def extract_full_text(file_pattern):
    """
    PDF 파일을 열어서 모든 페이지의 텍스트를 하나의 문자열로 합칩니다.
    """
    full_text = ""

    # 와일드카드 패턴에 맞는 모든 파일 경로 리스트 가져오기
    pdf_files = glob.glob(file_pattern)
    
    if not pdf_files:
        print(f"[!] 파일을 찾을 수 없습니다: {file_pattern}")
        return ""

    print(f"[*] 총 {len(pdf_files)}개의 파일을 찾았습니다: {pdf_files}")
    
    for pdf_path in pdf_files:# 변수명을 pdf_path로 명확히 수정
        # [수정 포인트] pdfplumber.open()으로 파일을 먼저 열어야 합니다!
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"[*] '{pdf_path}' 분석 중 (총 {total_pages}페이지)...")
            
            for i, page in enumerate(pdf.pages):
                # 텍스트 추출
                page_text = page.extract_text()
                
                if page_text:
                    # 페이지 간 구분자 추가 (나중에 디버깅하기 쉬움)
                    full_text += f"\n--- PAGE {i+1} ---\n" 
                    full_text += page_text

                # 진행률 표시 (119페이지라 시간이 좀 걸릴 수 있음)
                if (i + 1) % 20 == 0 or (i + 1) == total_pages:
                    print(f"[*] 진행도: {i + 1}/{total_pages} 페이지 완료")

    print(f"[*] 추출 완료! 총 글자 수: {len(full_text)}자")
    return full_text

if __name__ == "__main__":
    # PDF 파일 경로 (data 폴더 안에 넣어두세요)
    PATH_PATTERN = "data/*.pdf"
    result = extract_full_text(PATH_PATTERN)

    print("\n--- 추출된 전체 텍스트 일부 ---")
    print(result[:100])  # 처음 100자만 출력 (디버깅용)

    valid_dates = set(['20.5', '20.6', '20.7', '20.8', '20.9', '20.10', '20.11', '21.3', '21.4', '21.5', '21.7', '21.8', '21.10', '22.3', '22.4', '22.5', '22.7', '22.10', '23.2', '23.4', '23.5', '23.7', '23.10', '24.2', '24.4', '24.5', '24.7', '24.10', '25.2', '25.4', '25.5', '25.7', '25.8', '25.11'])

    chunk = chunk_pdf_text(result, valid_dates)
    print("\n--- 첫 번째 청크 예시 ---")
    if chunk:   # 청크가 존재할 때만 출력
        print(chunk[0])