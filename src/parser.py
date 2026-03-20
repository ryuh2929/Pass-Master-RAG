import pdfplumber
import re
import os
import glob

def get_all_exam_dates(file_pattern):
    # '24.7', '20.10' 등의 패턴을 찾는 정규표현식
    date_pattern = re.compile(r'(?<!\d)\d{2}\.(?:1[0-2]|[1-9])(?!\d)')
    found_dates = set()

    # 와일드카드 패턴에 맞는 모든 파일 경로 리스트 가져오기
    pdf_files = glob.glob(file_pattern)

    if not pdf_files:
        print(f"[!] '{file_pattern}' 패턴에 일치하는 파일이 없습니다.")
        return []

    print(f"[*] 총 {len(pdf_files)}개의 파일을 찾았습니다: {pdf_files}")

    for pdf_path in pdf_files:
        print(f"[*] '{pdf_path}' 분석 중...")
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # 텍스트 추출
                text = page.extract_text()
                if text:
                    # 1. 패턴에 맞는 형태 모두 찾기
                    matches = date_pattern.findall(text)
                    # 2. '14.6'은 제외
                    filtered_matches = [d for d in matches if d != '14.6']
                    found_dates.update(filtered_matches)

    # 정렬 로직 (연도.월 순서)
    sorted_dates = sorted(
        list(found_dates), 
        key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))
    )
    return sorted_dates

if __name__ == "__main__":
    # PDF 파일 경로 (data 폴더 안에 넣어두세요)
    PATH_PATTERN = "data/*.pdf"
    result = get_all_exam_dates(PATH_PATTERN)
    
    print("\n--- 추출된 날짜 리스트 ---")
    print(result)
    print("--------------------------")