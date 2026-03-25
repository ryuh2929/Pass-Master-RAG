import json

class StatsAnalyzer:
    def __init__(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def get_top_n(self, n=10, category=None):
        # 출제 횟수(occurrence_count) 기준으로 정렬
        sorted_data = sorted(self.data, key=lambda x: x.get('occurrence_count', 0), reverse=True)
        
        # 특정 카테고리(필기/실기 등) 필터링 로직 확장 가능
        return sorted_data[:n]