#!/usr/bin/env python3
"""
공연시장 발전을 위한 추가 기능들
KOPIS 데이터를 활용한 공연시장 고도화 서비스
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple
import requests
from collections import defaultdict

class MarketDevelopmentAnalyzer:
    """공연시장 발전 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_market_gaps(self, performances: List[Dict]) -> Dict:
        """시장 공백 분석"""
        df = pd.DataFrame(performances)
        
        # 카테고리별 공백 분석
        category_gaps = self._analyze_category_gaps(df)
        
        # 지역별 공백 분석
        location_gaps = self._analyze_location_gaps(df)
        
        # 가격대별 공백 분석
        price_gaps = self._analyze_price_gaps(df)
        
        # 시간대별 공백 분석
        time_gaps = self._analyze_time_gaps(df)
        
        return {
            'category_gaps': category_gaps,
            'location_gaps': location_gaps,
            'price_gaps': price_gaps,
            'time_gaps': time_gaps,
            'opportunities': self._identify_opportunities(category_gaps, location_gaps, price_gaps, time_gaps)
        }
    
    def _analyze_category_gaps(self, df: pd.DataFrame) -> Dict:
        """카테고리별 공백 분석"""
        category_counts = df['category'].value_counts()
        total_performances = len(df)
        
        # 평균 비율 계산
        avg_ratio = 1.0 / len(category_counts)
        
        gaps = {}
        for category, count in category_counts.items():
            ratio = count / total_performances
            gap_score = avg_ratio - ratio
            
            gaps[category] = {
                'current_count': count,
                'current_ratio': ratio,
                'expected_ratio': avg_ratio,
                'gap_score': gap_score,
                'opportunity_level': 'high' if gap_score > 0.05 else 'medium' if gap_score > 0.02 else 'low'
            }
        
        return gaps
    
    def _analyze_location_gaps(self, df: pd.DataFrame) -> Dict:
        """지역별 공백 분석"""
        location_counts = df['location'].value_counts()
        total_performances = len(df)
        
        # 지역별 인구 대비 분석 (간단한 가중치)
        population_weights = {
            '서울': 0.2, '부산': 0.1, '대구': 0.08, '인천': 0.08,
            '광주': 0.05, '대전': 0.05, '울산': 0.04, '경기': 0.15,
            '강원': 0.03, '충북': 0.03, '충남': 0.04, '전북': 0.03,
            '전남': 0.03, '경북': 0.04, '경남': 0.05, '제주': 0.02
        }
        
        gaps = {}
        for location, count in location_counts.items():
            current_ratio = count / total_performances
            expected_ratio = population_weights.get(location, 0.02)
            gap_score = expected_ratio - current_ratio
            
            gaps[location] = {
                'current_count': count,
                'current_ratio': current_ratio,
                'expected_ratio': expected_ratio,
                'gap_score': gap_score,
                'opportunity_level': 'high' if gap_score > 0.02 else 'medium' if gap_score > 0.01 else 'low'
            }
        
        return gaps
    
    def _analyze_price_gaps(self, df: pd.DataFrame) -> Dict:
        """가격대별 공백 분석"""
        # 가격 데이터 정제
        df['price_numeric'] = df['price'].str.extract('(\d+)').astype(float)
        
        price_ranges = {
            '저가': (0, 20000),
            '중가': (20000, 50000),
            '고가': (50000, float('inf'))
        }
        
        gaps = {}
        total_performances = len(df)
        
        for range_name, (min_price, max_price) in price_ranges.items():
            count = len(df[(df['price_numeric'] >= min_price) & (df['price_numeric'] < max_price)])
            ratio = count / total_performances
            expected_ratio = 0.33  # 균등 분포 가정
            
            gap_score = expected_ratio - ratio
            
            gaps[range_name] = {
                'current_count': count,
                'current_ratio': ratio,
                'expected_ratio': expected_ratio,
                'gap_score': gap_score,
                'opportunity_level': 'high' if abs(gap_score) > 0.1 else 'medium' if abs(gap_score) > 0.05 else 'low'
            }
        
        return gaps
    
    def _analyze_time_gaps(self, df: pd.DataFrame) -> Dict:
        """시간대별 공백 분석"""
        # 시간대 분류
        def classify_time(time_str):
            if '19:' in time_str or '20:' in time_str:
                return '저녁'
            elif '14:' in time_str or '15:' in time_str:
                return '오후'
            elif '10:' in time_str or '11:' in time_str:
                return '오전'
            else:
                return '기타'
        
        df['time_period'] = df['time'].apply(classify_time)
        time_counts = df['time_period'].value_counts()
        total_performances = len(df)
        
        gaps = {}
        for time_period, count in time_counts.items():
            ratio = count / total_performances
            expected_ratio = 0.25  # 균등 분포 가정
            
            gap_score = expected_ratio - ratio
            
            gaps[time_period] = {
                'current_count': count,
                'current_ratio': ratio,
                'expected_ratio': expected_ratio,
                'gap_score': gap_score,
                'opportunity_level': 'high' if abs(gap_score) > 0.1 else 'medium' if abs(gap_score) > 0.05 else 'low'
            }
        
        return gaps
    
    def _identify_opportunities(self, category_gaps: Dict, location_gaps: Dict, 
                              price_gaps: Dict, time_gaps: Dict) -> List[Dict]:
        """시장 기회 식별"""
        opportunities = []
        
        # 카테고리 기회
        for category, gap_data in category_gaps.items():
            if gap_data['opportunity_level'] == 'high':
                opportunities.append({
                    'type': 'category',
                    'target': category,
                    'description': f"{category} 카테고리의 공연 수가 부족합니다.",
                    'recommendation': f"{category} 공연을 더 많이 기획해보세요.",
                    'priority': 'high'
                })
        
        # 지역 기회
        for location, gap_data in location_gaps.items():
            if gap_data['opportunity_level'] == 'high':
                opportunities.append({
                    'type': 'location',
                    'target': location,
                    'description': f"{location} 지역의 공연 수가 부족합니다.",
                    'recommendation': f"{location} 지역에서의 공연을 고려해보세요.",
                    'priority': 'high'
                })
        
        # 가격대 기회
        for price_range, gap_data in price_gaps.items():
            if gap_data['opportunity_level'] == 'high':
                opportunities.append({
                    'type': 'price',
                    'target': price_range,
                    'description': f"{price_range} 가격대의 공연이 부족합니다.",
                    'recommendation': f"{price_range} 가격대의 공연을 기획해보세요.",
                    'priority': 'medium'
                })
        
        return opportunities

class VenueOptimizer:
    """공연장 최적화 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_venue_utilization(self, performances: List[Dict], venues: List[Dict]) -> Dict:
        """공연장 활용도 분석"""
        # 공연장별 공연 수 집계
        venue_performance_counts = defaultdict(int)
        venue_revenue = defaultdict(float)
        
        for performance in performances:
            venue_name = performance.get('venue', 'Unknown')
            venue_performance_counts[venue_name] += 1
            
            # 수익 계산 (간단한 추정)
            price = self._extract_price(performance.get('price', '0'))
            venue_revenue[venue_name] += price * 0.7  # 70% 수익률 가정
        
        # 공연장별 분석
        venue_analysis = {}
        for venue in venues:
            venue_name = venue.get('name', 'Unknown')
            performance_count = venue_performance_counts[venue_name]
            total_revenue = venue_revenue[venue_name]
            
            # 활용도 점수 계산
            capacity = venue.get('capacity', 100)
            utilization_score = min(performance_count / 10, 1.0)  # 월 10회 기준
            
            venue_analysis[venue_name] = {
                'performance_count': performance_count,
                'total_revenue': total_revenue,
                'utilization_score': utilization_score,
                'capacity': capacity,
                'recommendations': self._generate_venue_recommendations(performance_count, total_revenue, capacity)
            }
        
        return venue_analysis
    
    def _extract_price(self, price_str: str) -> float:
        """가격 추출"""
        try:
            return float(price_str.replace(',', '').replace('원', ''))
        except:
            return 0.0
    
    def _generate_venue_recommendations(self, performance_count: int, 
                                      total_revenue: float, capacity: int) -> List[str]:
        """공연장별 권장사항 생성"""
        recommendations = []
        
        if performance_count < 5:
            recommendations.append("공연 빈도를 늘려보세요.")
        
        if total_revenue < 10000000:  # 1000만원
            recommendations.append("수익성을 높이기 위한 전략이 필요합니다.")
        
        if capacity > 500 and performance_count < 10:
            recommendations.append("대형 공연장의 특성을 활용한 공연을 고려해보세요.")
        
        return recommendations

class AudienceInsightAnalyzer:
    """관객 인사이트 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_audience_preferences(self, performances: List[Dict], 
                                   audience_data: List[Dict]) -> Dict:
        """관객 선호도 분석"""
        # 카테고리별 관객 선호도
        category_preferences = defaultdict(list)
        
        for audience in audience_data:
            category = audience.get('preferred_category')
            rating = audience.get('rating', 0)
            if category and rating > 0:
                category_preferences[category].append(rating)
        
        # 평균 평점 계산
        category_avg_ratings = {}
        for category, ratings in category_preferences.items():
            category_avg_ratings[category] = np.mean(ratings)
        
        # 연령대별 선호도
        age_preferences = defaultdict(list)
        for audience in audience_data:
            age_group = audience.get('age_group')
            rating = audience.get('rating', 0)
            if age_group and rating > 0:
                age_preferences[age_group].append(rating)
        
        age_avg_ratings = {}
        for age_group, ratings in age_preferences.items():
            age_avg_ratings[age_group] = np.mean(ratings)
        
        return {
            'category_preferences': category_avg_ratings,
            'age_preferences': age_avg_ratings,
            'insights': self._generate_audience_insights(category_avg_ratings, age_avg_ratings)
        }
    
    def _generate_audience_insights(self, category_ratings: Dict, age_ratings: Dict) -> List[str]:
        """관객 인사이트 생성"""
        insights = []
        
        # 카테고리별 인사이트
        if category_ratings:
            best_category = max(category_ratings, key=category_ratings.get)
            worst_category = min(category_ratings, key=category_ratings.get)
            
            insights.append(f"가장 인기 있는 카테고리는 '{best_category}'입니다.")
            insights.append(f"'{worst_category}' 카테고리의 개선이 필요합니다.")
        
        # 연령대별 인사이트
        if age_ratings:
            target_age = max(age_ratings, key=age_ratings.get)
            insights.append(f"'{target_age}' 연령대의 만족도가 가장 높습니다.")
        
        return insights

class MarketTrendPredictor:
    """시장 트렌드 예측기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def predict_market_trends(self, historical_data: List[Dict], 
                            forecast_periods: int = 12) -> Dict:
        """시장 트렌드 예측"""
        df = pd.DataFrame(historical_data)
        
        # 월별 공연 수 트렌드
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly_counts = df.groupby('month').size()
        
        # 간단한 선형 트렌드 예측
        if len(monthly_counts) > 1:
            x = np.arange(len(monthly_counts))
            y = monthly_counts.values
            
            # 선형 회귀
            coeffs = np.polyfit(x, y, 1)
            trend_slope = coeffs[0]
            
            # 향후 예측
            future_x = np.arange(len(monthly_counts), len(monthly_counts) + forecast_periods)
            future_y = np.polyval(coeffs, future_x)
            
            trend_prediction = {
                'current_trend': '상승' if trend_slope > 0 else '하락' if trend_slope < 0 else '안정',
                'trend_strength': abs(trend_slope),
                'forecast': future_y.tolist(),
                'confidence': self._calculate_confidence(len(monthly_counts), trend_slope)
            }
        else:
            trend_prediction = {
                'current_trend': '데이터 부족',
                'trend_strength': 0,
                'forecast': [],
                'confidence': 0
            }
        
        # 카테고리별 트렌드
        category_trends = self._analyze_category_trends(df)
        
        return {
            'overall_trend': trend_prediction,
            'category_trends': category_trends,
            'recommendations': self._generate_trend_recommendations(trend_prediction, category_trends)
        }
    
    def _analyze_category_trends(self, df: pd.DataFrame) -> Dict:
        """카테고리별 트렌드 분석"""
        category_trends = {}
        
        for category in df['category'].unique():
            category_data = df[df['category'] == category]
            monthly_counts = category_data.groupby(pd.to_datetime(category_data['date']).dt.to_period('M')).size()
            
            if len(monthly_counts) > 1:
                x = np.arange(len(monthly_counts))
                y = monthly_counts.values
                coeffs = np.polyfit(x, y, 1)
                trend_slope = coeffs[0]
                
                category_trends[category] = {
                    'trend': '상승' if trend_slope > 0 else '하락' if trend_slope < 0 else '안정',
                    'strength': abs(trend_slope)
                }
        
        return category_trends
    
    def _calculate_confidence(self, data_points: int, trend_slope: float) -> float:
        """예측 신뢰도 계산"""
        # 간단한 신뢰도 계산 (데이터 포인트 수와 트렌드 강도 기반)
        base_confidence = min(data_points / 12, 1.0)  # 12개월 이상 데이터가 있으면 최대 신뢰도
        trend_confidence = min(abs(trend_slope) / 10, 1.0)  # 트렌드 강도 기반
        
        return (base_confidence + trend_confidence) / 2
    
    def _generate_trend_recommendations(self, overall_trend: Dict, category_trends: Dict) -> List[str]:
        """트렌드 기반 권장사항"""
        recommendations = []
        
        if overall_trend['current_trend'] == '상승':
            recommendations.append("시장이 성장하고 있습니다. 공연 수를 늘려보세요.")
        elif overall_trend['current_trend'] == '하락':
            recommendations.append("시장이 하락하고 있습니다. 차별화된 전략이 필요합니다.")
        
        # 카테고리별 권장사항
        growing_categories = [cat for cat, trend in category_trends.items() if trend['trend'] == '상승']
        if growing_categories:
            recommendations.append(f"성장하는 카테고리: {', '.join(growing_categories)}")
        
        return recommendations

class MarketDevelopmentReport:
    """시장 발전 리포트 생성기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.market_analyzer = MarketDevelopmentAnalyzer()
        self.venue_optimizer = VenueOptimizer()
        self.audience_analyzer = AudienceInsightAnalyzer()
        self.trend_predictor = MarketTrendPredictor()
    
    def generate_comprehensive_report(self, performances: List[Dict], 
                                    venues: List[Dict] = None,
                                    audience_data: List[Dict] = None,
                                    historical_data: List[Dict] = None) -> str:
        """종합 시장 발전 리포트 생성"""
        report_sections = []
        
        # 1. 시장 공백 분석
        market_gaps = self.market_analyzer.analyze_market_gaps(performances)
        report_sections.append(self._format_market_gaps_section(market_gaps))
        
        # 2. 공연장 최적화 분석
        if venues:
            venue_analysis = self.venue_optimizer.analyze_venue_utilization(performances, venues)
            report_sections.append(self._format_venue_analysis_section(venue_analysis))
        
        # 3. 관객 인사이트
        if audience_data:
            audience_insights = self.audience_analyzer.analyze_audience_preferences(performances, audience_data)
            report_sections.append(self._format_audience_insights_section(audience_insights))
        
        # 4. 시장 트렌드 예측
        if historical_data:
            trend_analysis = self.trend_predictor.predict_market_trends(historical_data)
            report_sections.append(self._format_trend_analysis_section(trend_analysis))
        
        # 5. 종합 권장사항
        report_sections.append(self._format_recommendations_section(market_gaps))
        
        # 리포트 조합
        full_report = f"""
# 🎭 공연시장 발전 종합 리포트

**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}
**분석 대상 공연 수**: {len(performances)}개

{''.join(report_sections)}

---
*본 리포트는 KOPIS 데이터를 기반으로 생성되었습니다.*
        """
        
        return full_report
    
    def _format_market_gaps_section(self, market_gaps: Dict) -> str:
        """시장 공백 분석 섹션 포맷"""
        section = """
## 📊 시장 공백 분석

### 카테고리별 공백
"""
        
        for category, gap_data in market_gaps['category_gaps'].items():
            if gap_data['opportunity_level'] == 'high':
                section += f"- **{category}**: {gap_data['current_count']}개 (기대: {gap_data['expected_ratio']:.1%})\n"
        
        section += "\n### 지역별 공백\n"
        for location, gap_data in market_gaps['location_gaps'].items():
            if gap_data['opportunity_level'] == 'high':
                section += f"- **{location}**: {gap_data['current_count']}개 (기대: {gap_data['expected_ratio']:.1%})\n"
        
        return section
    
    def _format_venue_analysis_section(self, venue_analysis: Dict) -> str:
        """공연장 분석 섹션 포맷"""
        section = "\n## 🏢 공연장 활용도 분석\n"
        
        for venue, analysis in venue_analysis.items():
            section += f"\n### {venue}\n"
            section += f"- 공연 수: {analysis['performance_count']}개\n"
            section += f"- 활용도 점수: {analysis['utilization_score']:.1%}\n"
            section += f"- 권장사항: {', '.join(analysis['recommendations'])}\n"
        
        return section
    
    def _format_audience_insights_section(self, audience_insights: Dict) -> str:
        """관객 인사이트 섹션 포맷"""
        section = "\n## 👥 관객 인사이트\n"
        
        section += "\n### 주요 인사이트\n"
        for insight in audience_insights['insights']:
            section += f"- {insight}\n"
        
        return section
    
    def _format_trend_analysis_section(self, trend_analysis: Dict) -> str:
        """트렌드 분석 섹션 포맷"""
        section = "\n## 📈 시장 트렌드 예측\n"
        
        overall_trend = trend_analysis['overall_trend']
        section += f"\n### 전체 시장 트렌드\n"
        section += f"- 현재 트렌드: {overall_trend['current_trend']}\n"
        section += f"- 예측 신뢰도: {overall_trend['confidence']:.1%}\n"
        
        return section
    
    def _format_recommendations_section(self, market_gaps: Dict) -> str:
        """권장사항 섹션 포맷"""
        section = "\n## 💡 시장 발전 권장사항\n"
        
        for opportunity in market_gaps['opportunities']:
            section += f"\n### {opportunity['type'].title()} 기회\n"
            section += f"- **{opportunity['target']}**: {opportunity['description']}\n"
            section += f"- 권장사항: {opportunity['recommendation']}\n"
        
        return section

def main():
    """테스트 실행"""
    # 샘플 데이터
    sample_performances = [
        {
            'title': '레미제라블',
            'category': '뮤지컬',
            'location': '서울',
            'price': '80,000원',
            'date': '2024-12-15',
            'venue': '예술의전당'
        },
        {
            'title': '햄릿',
            'category': '연극',
            'location': '서울',
            'price': '50,000원',
            'date': '2024-12-20',
            'venue': '대학로'
        }
    ]
    
    # 시장 발전 리포트 생성
    report_generator = MarketDevelopmentReport()
    report = report_generator.generate_comprehensive_report(sample_performances)
    
    print(report)
    
    # 파일로 저장
    with open('market_development_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n시장 발전 리포트가 생성되었습니다: market_development_report.md")

if __name__ == '__main__':
    main() 