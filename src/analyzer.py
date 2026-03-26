import json
import os

class StatsAnalyzer:
    # 실기 시험 날짜 리스트
    PRACTICAL_DATES = ['20.5', '20.7', '20.10', '20.11', '21.4', '21.7', '21.10', '22.5', '22.10', '23.4', '23.10', '24.4', '24.10', '25.4', '25.7', '25.11']

    def __init__(self, json_path=None):
        # 기본 경로 설정 (main.py에서 상대 경로로 접근하기 위함)
        if json_path is None:
            json_path = os.getenv("DATA_PATH", "data/processed_chunks.json")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def get_top_n(self, n=5, is_practical_only=False):
        # 출제 횟수 기준 상위 N개 추출
        # is_practical_only=True 일 경우 실기 날짜에 포함된 횟수만 계산하여 정렬
        # item['metadata']['occurrence_count']를 기준으로 정렬
        filtered_list = []

        for item in self.data:
            meta = item.get('metadata', {})
            if is_practical_only:
                # 실기 날짜에 포함된 횟수만 계산
                practical_count = sum(1 for date in meta.get('exam_dates', []) if date in self.PRACTICAL_DATES)
                if practical_count > 0:
                    filtered_list.append((item, practical_count))
            else:
                filtered_list.append((item, meta.get('occurrence_count', 0)))
        
        # occurrence_count 기준으로 정렬 (실기 여부에 따라 다르게 계산된 count 사용)
        sorted_data = sorted(
            filtered_list, 
            key=lambda x: x[1], 
            reverse=True
        )

        # 특정 카테고리(필기/실기 등) 필터링 로직 확장 가능
        return sorted_data[:n]