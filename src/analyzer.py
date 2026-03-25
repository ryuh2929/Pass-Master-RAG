import json
import os

class StatsAnalyzer:
    def __init__(self, json_path=None):
        # 기본 경로 설정 (main.py에서 상대 경로로 접근하기 위함)
        if json_path is None:
            json_path = os.getenv("DATA_PATH", "data/processed_chunks.json")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def get_top_n(self, n=5):
        # 출제 횟수 기준 상위 N개 추출
        sorted_data = sorted(self.data, key=lambda x: x.get('occurrence_count', 0), reverse=True)

        # 특정 카테고리(필기/실기 등) 필터링 로직 확장 가능
        return sorted_data[:n]