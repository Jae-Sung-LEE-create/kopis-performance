#!/usr/bin/env python3
"""
공연시장 분석 대시보드
KOPIS 데이터를 활용한 실시간 공연시장 분석 및 시각화
"""

import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List
import logging

class MarketAnalyticsDashboard:
    """공연시장 분석 대시보드 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_category_distribution_chart(self, category_data: Dict) -> go.Figure:
        """카테고리별 분포 차트"""
        categories = list(category_data.keys())
        counts = list(category_data.values())
        
        fig = go.Figure(data=[
            go.Pie(
                labels=categories,
                values=counts,
                hole=0.3,
                marker_colors=px.colors.qualitative.Set3
            )
        ])
        
        fig.update_layout(
            title="공연 카테고리별 분포",
            title_x=0.5,
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_monthly_trend_chart(self, monthly_data: Dict) -> go.Figure:
        """월별 트렌드 차트"""
        months = list(monthly_data.keys())
        counts = list(monthly_data.values())
        
        fig = go.Figure(data=[
            go.Scatter(
                x=months,
                y=counts,
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            )
        ])
        
        fig.update_layout(
            title="월별 공연 수 트렌드",
            title_x=0.5,
            xaxis_title="월",
            yaxis_title="공연 수",
            height=400
        )
        
        return fig
    
    def create_location_distribution_chart(self, location_data: Dict) -> go.Figure:
        """지역별 분포 차트"""
        locations = list(location_data.keys())
        counts = list(location_data.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=locations,
                y=counts,
                marker_color='#ff7f0e'
            )
        ])
        
        fig.update_layout(
            title="지역별 공연 분포",
            title_x=0.5,
            xaxis_title="지역",
            yaxis_title="공연 수",
            height=400
        )
        
        return fig
    
    def create_price_analysis_chart(self, price_data: Dict) -> go.Figure:
        """가격 분석 차트"""
        price_ranges = list(price_data.get('price_ranges', {}).keys())
        counts = list(price_data.get('price_ranges', {}).values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=price_ranges,
                y=counts,
                marker_color=['#2ca02c', '#d62728', '#9467bd']
            )
        ])
        
        fig.update_layout(
            title="가격대별 공연 분포",
            title_x=0.5,
            xaxis_title="가격대",
            yaxis_title="공연 수",
            height=400
        )
        
        return fig
    
    def create_comprehensive_dashboard(self, analytics_data: Dict) -> go.Figure:
        """종합 대시보드 생성"""
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '카테고리별 분포',
                '월별 트렌드',
                '지역별 분포',
                '가격대별 분포'
            ),
            specs=[
                [{"type": "pie"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )
        
        # 카테고리별 분포 (파이 차트)
        categories = list(analytics_data.get('category_distribution', {}).keys())
        category_counts = list(analytics_data.get('category_distribution', {}).values())
        
        fig.add_trace(
            go.Pie(
                labels=categories,
                values=category_counts,
                hole=0.3,
                marker_colors=px.colors.qualitative.Set3
            ),
            row=1, col=1
        )
        
        # 월별 트렌드 (선 차트)
        months = list(analytics_data.get('monthly_trends', {}).keys())
        monthly_counts = list(analytics_data.get('monthly_trends', {}).values())
        
        fig.add_trace(
            go.Scatter(
                x=months,
                y=monthly_counts,
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ),
            row=1, col=2
        )
        
        # 지역별 분포 (막대 차트)
        locations = list(analytics_data.get('location_distribution', {}).keys())
        location_counts = list(analytics_data.get('location_distribution', {}).values())
        
        fig.add_trace(
            go.Bar(
                x=locations,
                y=location_counts,
                marker_color='#ff7f0e'
            ),
            row=2, col=1
        )
        
        # 가격대별 분포 (막대 차트)
        price_ranges = list(analytics_data.get('price_analysis', {}).get('price_ranges', {}).keys())
        price_counts = list(analytics_data.get('price_analysis', {}).get('price_ranges', {}).values())
        
        fig.add_trace(
            go.Bar(
                x=price_ranges,
                y=price_counts,
                marker_color=['#2ca02c', '#d62728', '#9467bd']
            ),
            row=2, col=2
        )
        
        # 레이아웃 업데이트
        fig.update_layout(
            title="공연시장 종합 분석 대시보드",
            title_x=0.5,
            height=800,
            showlegend=False
        )
        
        return fig
    
    def generate_insights(self, analytics_data: Dict) -> List[str]:
        """데이터 기반 인사이트 생성"""
        insights = []
        
        # 전체 공연 수 기반 인사이트
        total_performances = analytics_data.get('total_performances', 0)
        if total_performances > 0:
            insights.append(f"현재 총 {total_performances}개의 공연이 등록되어 있습니다.")
        
        # 카테고리별 인사이트
        category_data = analytics_data.get('category_distribution', {})
        if category_data:
            most_popular_category = max(category_data, key=category_data.get)
            insights.append(f"가장 인기 있는 공연 카테고리는 '{most_popular_category}'입니다.")
        
        # 지역별 인사이트
        location_data = analytics_data.get('location_distribution', {})
        if location_data:
            most_active_location = max(location_data, key=location_data.get)
            insights.append(f"가장 활발한 공연 지역은 '{most_active_location}'입니다.")
        
        # 가격 분석 인사이트
        price_data = analytics_data.get('price_analysis', {})
        if price_data:
            avg_price = price_data.get('average_price', 0)
            if avg_price > 0:
                insights.append(f"평균 공연 가격은 {avg_price:,.0f}원입니다.")
            
            price_ranges = price_data.get('price_ranges', {})
            if price_ranges:
                most_common_price_range = max(price_ranges, key=price_ranges.get)
                insights.append(f"가장 많은 공연이 '{most_common_price_range}' 가격대에 집중되어 있습니다.")
        
        return insights
    
    def export_dashboard_html(self, analytics_data: Dict, filename: str = "market_dashboard.html"):
        """대시보드를 HTML 파일로 내보내기"""
        try:
            # 종합 대시보드 생성
            dashboard = self.create_comprehensive_dashboard(analytics_data)
            
            # 인사이트 생성
            insights = self.generate_insights(analytics_data)
            
            # HTML 템플릿 생성
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>공연시장 분석 대시보드</title>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        color: #333;
                    }}
                    .insights {{
                        background-color: #e8f4fd;
                        padding: 20px;
                        border-radius: 5px;
                        margin-bottom: 30px;
                    }}
                    .insights h3 {{
                        color: #0066cc;
                        margin-top: 0;
                    }}
                    .insights ul {{
                        margin: 0;
                        padding-left: 20px;
                    }}
                    .insights li {{
                        margin-bottom: 10px;
                        line-height: 1.5;
                    }}
                    .chart-container {{
                        margin-bottom: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎭 공연시장 분석 대시보드</h1>
                        <p>생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
                    </div>
                    
                    <div class="insights">
                        <h3>📊 주요 인사이트</h3>
                        <ul>
                            {''.join([f'<li>{insight}</li>' for insight in insights])}
                        </ul>
                    </div>
                    
                    <div class="chart-container">
                        {dashboard.to_html(full_html=False, include_plotlyjs=True)}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # HTML 파일 저장
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"대시보드가 {filename}에 저장되었습니다.")
            return filename
            
        except Exception as e:
            self.logger.error(f"대시보드 내보내기 실패: {e}")
            return None

class PerformancePredictor:
    """공연 성과 예측 모델"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def predict_performance_success(self, performance_data: Dict) -> Dict:
        """공연 성공 가능성 예측"""
        # 간단한 예측 모델 (실제로는 머신러닝 모델 사용)
        score = 0
        factors = []
        
        # 카테고리별 점수
        category_scores = {
            '뮤지컬': 8,
            '연극': 7,
            '대중음악': 6,
            '서양음악(클래식)': 5,
            '무용(서양/한국무용)': 4,
            '한국음악(국악)': 3,
            '대중무용': 2,
            '서커스/마술': 1,
            '복합': 5
        }
        
        category = performance_data.get('category', '')
        if category in category_scores:
            score += category_scores[category]
            factors.append(f"카테고리 ({category}): +{category_scores[category]}점")
        
        # 지역별 점수
        location_scores = {
            '서울': 8,
            '부산': 6,
            '대구': 5,
            '인천': 4,
            '광주': 4,
            '대전': 3,
            '울산': 3,
            '경기': 7,
            '강원': 2,
            '충북': 2,
            '충남': 2,
            '전북': 2,
            '전남': 2,
            '경북': 2,
            '경남': 3,
            '제주': 4
        }
        
        location = performance_data.get('location', '')
        if location in location_scores:
            score += location_scores[location]
            factors.append(f"지역 ({location}): +{location_scores[location]}점")
        
        # 가격 분석
        price = performance_data.get('price', '0')
        try:
            price_numeric = float(price.replace(',', '').replace('원', ''))
            if price_numeric <= 20000:
                score += 3
                factors.append("가격 (저가): +3점")
            elif price_numeric <= 50000:
                score += 5
                factors.append("가격 (중가): +5점")
            else:
                score += 2
                factors.append("가격 (고가): +2점")
        except:
            pass
        
        # 성공 확률 계산 (0-100%)
        success_probability = min(score * 5, 100)
        
        return {
            'success_probability': success_probability,
            'score': score,
            'factors': factors,
            'recommendations': self._generate_recommendations(score, performance_data)
        }
    
    def _generate_recommendations(self, score: int, performance_data: Dict) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        if score < 10:
            recommendations.append("더 인기 있는 카테고리로 변경을 고려해보세요.")
            recommendations.append("서울이나 주요 도시에서의 공연을 검토해보세요.")
        
        if score < 15:
            recommendations.append("가격 정책을 재검토해보세요.")
            recommendations.append("마케팅 전략을 강화해보세요.")
        
        if score >= 20:
            recommendations.append("현재 조건이 좋습니다. 홍보에 집중하세요.")
        
        return recommendations

def main():
    """테스트 실행"""
    # 샘플 데이터
    sample_data = {
        'category_distribution': {
            '연극': 25,
            '뮤지컬': 30,
            '서양음악(클래식)': 15,
            '한국음악(국악)': 10,
            '대중음악': 20
        },
        'monthly_trends': {
            1: 50, 2: 45, 3: 60, 4: 55, 5: 70, 6: 65
        },
        'location_distribution': {
            '서울': 40,
            '부산': 15,
            '대구': 10,
            '인천': 8,
            '경기': 12
        },
        'price_analysis': {
            'average_price': 35000,
            'median_price': 30000,
            'min_price': 10000,
            'max_price': 100000,
            'price_ranges': {
                '저가': 30,
                '중가': 45,
                '고가': 25
            }
        },
        'total_performances': 100
    }
    
    # 대시보드 생성
    dashboard = MarketAnalyticsDashboard()
    
    # HTML 대시보드 생성
    filename = dashboard.export_dashboard_html(sample_data)
    print(f"대시보드가 생성되었습니다: {filename}")
    
    # 예측 모델 테스트
    predictor = PerformancePredictor()
    test_performance = {
        'category': '뮤지컬',
        'location': '서울',
        'price': '50,000원'
    }
    
    prediction = predictor.predict_performance_success(test_performance)
    print("\n=== 공연 성공 예측 ===")
    print(f"성공 확률: {prediction['success_probability']:.1f}%")
    print(f"총점: {prediction['score']}점")
    print("요인:")
    for factor in prediction['factors']:
        print(f"  - {factor}")
    print("권장사항:")
    for rec in prediction['recommendations']:
        print(f"  - {rec}")

if __name__ == '__main__':
    main() 