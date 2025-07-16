#!/usr/bin/env python3
"""
공연 추천 시스템
사용자 선호도와 공연 데이터를 기반으로 한 맞춤형 공연 추천 시스템
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
import json

class PerformanceRecommender:
    """공연 추천 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        
    def create_user_profile(self, user_preferences: Dict) -> Dict:
        """사용자 프로필 생성"""
        profile = {
            'preferred_categories': user_preferences.get('categories', []),
            'preferred_locations': user_preferences.get('locations', []),
            'price_range': user_preferences.get('price_range', 'all'),
            'preferred_time': user_preferences.get('time', 'all'),
            'interests': user_preferences.get('interests', []),
            'viewing_history': user_preferences.get('viewing_history', []),
            'ratings': user_preferences.get('ratings', {})
        }
        return profile
    
    def calculate_content_similarity(self, performance1: Dict, performance2: Dict) -> float:
        """콘텐츠 기반 유사도 계산"""
        # 카테고리 유사도
        category_similarity = 1.0 if performance1.get('category') == performance2.get('category') else 0.0
        
        # 지역 유사도
        location_similarity = 1.0 if performance1.get('location') == performance2.get('location') else 0.0
        
        # 가격 유사도 (가격대별)
        price1 = self._extract_price(performance1.get('price', '0'))
        price2 = self._extract_price(performance2.get('price', '0'))
        price_similarity = self._calculate_price_similarity(price1, price2)
        
        # 설명 텍스트 유사도
        text_similarity = self._calculate_text_similarity(
            performance1.get('description', ''),
            performance2.get('description', '')
        )
        
        # 가중 평균 계산
        similarity = (
            category_similarity * 0.3 +
            location_similarity * 0.2 +
            price_similarity * 0.2 +
            text_similarity * 0.3
        )
        
        return similarity
    
    def _extract_price(self, price_str: str) -> float:
        """가격 문자열에서 숫자 추출"""
        try:
            return float(price_str.replace(',', '').replace('원', ''))
        except:
            return 0.0
    
    def _calculate_price_similarity(self, price1: float, price2: float) -> float:
        """가격 유사도 계산"""
        if price1 == 0 or price2 == 0:
            return 0.5
        
        # 가격대별 분류
        def get_price_range(price):
            if price <= 20000:
                return 'low'
            elif price <= 50000:
                return 'medium'
            else:
                return 'high'
        
        range1 = get_price_range(price1)
        range2 = get_price_range(price2)
        
        return 1.0 if range1 == range2 else 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """텍스트 유사도 계산"""
        if not text1 or not text2:
            return 0.0
        
        try:
            # TF-IDF 벡터화
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0
    
    def recommend_by_preferences(self, user_profile: Dict, performances: List[Dict], top_n: int = 10) -> List[Dict]:
        """사용자 선호도 기반 추천"""
        recommendations = []
        
        for performance in performances:
            score = 0
            
            # 카테고리 매칭
            if performance.get('category') in user_profile.get('preferred_categories', []):
                score += 3
            
            # 지역 매칭
            if performance.get('location') in user_profile.get('preferred_locations', []):
                score += 2
            
            # 가격대 매칭
            price = self._extract_price(performance.get('price', '0'))
            user_price_range = user_profile.get('price_range', 'all')
            
            if user_price_range == 'all':
                score += 1
            elif user_price_range == 'low' and price <= 20000:
                score += 2
            elif user_price_range == 'medium' and 20000 < price <= 50000:
                score += 2
            elif user_price_range == 'high' and price > 50000:
                score += 2
            
            # 시간대 매칭
            performance_time = performance.get('time', '')
            user_time = user_profile.get('preferred_time', 'all')
            
            if user_time == 'all':
                score += 1
            elif user_time in performance_time:
                score += 1
            
            # 관람 이력 기반 점수
            if performance.get('title') in user_profile.get('viewing_history', []):
                score -= 1  # 이미 본 공연은 점수 감소
            
            # 평점 기반 점수
            performance_id = performance.get('id')
            if performance_id in user_profile.get('ratings', {}):
                rating = user_profile['ratings'][performance_id]
                score += (rating - 2.5) * 0.5  # 평균보다 높으면 점수 증가
            
            recommendations.append({
                'performance': performance,
                'score': score,
                'reason': self._generate_recommendation_reason(performance, user_profile)
            })
        
        # 점수순 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:top_n]
    
    def recommend_by_collaborative_filtering(self, user_id: int, user_ratings: Dict, 
                                          all_ratings: Dict, performances: List[Dict], 
                                          top_n: int = 10) -> List[Dict]:
        """협업 필터링 기반 추천"""
        # 사용자-공연 평점 매트릭스 생성
        users = list(set([rating['user_id'] for rating in all_ratings]))
        performance_ids = list(set([rating['performance_id'] for rating in all_ratings]))
        
        # 평점 매트릭스 생성
        rating_matrix = np.zeros((len(users), len(performance_ids)))
        
        for rating in all_ratings:
            user_idx = users.index(rating['user_id'])
            perf_idx = performance_ids.index(rating['performance_id'])
            rating_matrix[user_idx][perf_idx] = rating['rating']
        
        # 현재 사용자 인덱스
        if user_id in users:
            user_idx = users.index(user_id)
            
            # 다른 사용자와의 유사도 계산
            similarities = []
            for i, other_user_ratings in enumerate(rating_matrix):
                if i != user_idx:
                    similarity = cosine_similarity(
                        [rating_matrix[user_idx]], 
                        [other_user_ratings]
                    )[0][0]
                    similarities.append((i, similarity))
            
            # 유사도순 정렬
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 유사 사용자들의 평점을 기반으로 추천
            recommendations = []
            for performance in performances:
                if performance.get('id') in performance_ids:
                    perf_idx = performance_ids.index(performance.get('id'))
                    
                    # 현재 사용자가 아직 평가하지 않은 공연만
                    if rating_matrix[user_idx][perf_idx] == 0:
                        predicted_rating = 0
                        total_similarity = 0
                        
                        for similar_user_idx, similarity in similarities[:5]:  # 상위 5명
                            if similarity > 0:
                                predicted_rating += rating_matrix[similar_user_idx][perf_idx] * similarity
                                total_similarity += similarity
                        
                        if total_similarity > 0:
                            predicted_rating /= total_similarity
                            
                            recommendations.append({
                                'performance': performance,
                                'predicted_rating': predicted_rating,
                                'reason': f"유사한 사용자들이 평균 {predicted_rating:.1f}점을 주었습니다."
                            })
            
            # 예측 평점순 정렬
            recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
            return recommendations[:top_n]
        
        return []
    
    def recommend_by_popularity(self, performances: List[Dict], top_n: int = 10) -> List[Dict]:
        """인기도 기반 추천"""
        # 인기도 점수 계산
        popularity_scores = []
        
        for performance in performances:
            score = 0
            
            # 좋아요 수
            score += performance.get('likes', 0) * 2
            
            # 댓글 수
            score += len(performance.get('comments', [])) * 1
            
            # 최근 공연일수록 점수 증가
            try:
                perf_date = datetime.strptime(performance.get('date', ''), '%Y-%m-%d')
                days_until = (perf_date - datetime.now()).days
                if days_until >= 0:  # 아직 공연하지 않은 공연
                    score += max(0, 30 - days_until)  # 가까울수록 높은 점수
            except:
                pass
            
            # 카테고리별 가중치
            category_weights = {
                '뮤지컬': 1.2,
                '연극': 1.1,
                '대중음악': 1.0,
                '서양음악(클래식)': 0.9,
                '무용(서양/한국무용)': 0.8,
                '한국음악(국악)': 0.7,
                '대중무용': 0.6,
                '서커스/마술': 0.5,
                '복합': 0.8
            }
            
            category = performance.get('category', '')
            weight = category_weights.get(category, 1.0)
            score *= weight
            
            popularity_scores.append({
                'performance': performance,
                'score': score,
                'reason': f"인기 공연 (좋아요: {performance.get('likes', 0)}, 댓글: {len(performance.get('comments', []))})"
            })
        
        # 점수순 정렬
        popularity_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return popularity_scores[:top_n]
    
    def recommend_by_diversity(self, performances: List[Dict], top_n: int = 10) -> List[Dict]:
        """다양성 기반 추천 (다양한 카테고리/지역)"""
        # 카테고리별로 분류
        category_groups = {}
        for performance in performances:
            category = performance.get('category', '기타')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(performance)
        
        # 각 카테고리에서 상위 공연 선택
        recommendations = []
        max_per_category = max(1, top_n // len(category_groups))
        
        for category, category_performances in category_groups.items():
            # 카테고리 내에서 인기도순 정렬
            sorted_performances = sorted(
                category_performances,
                key=lambda x: (x.get('likes', 0), len(x.get('comments', []))),
                reverse=True
            )
            
            for i, performance in enumerate(sorted_performances[:max_per_category]):
                recommendations.append({
                    'performance': performance,
                    'score': len(category_groups) - i,  # 카테고리 다양성 점수
                    'reason': f"다양한 장르 추천 - {category}"
                })
        
        # 점수순 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:top_n]
    
    def _generate_recommendation_reason(self, performance: Dict, user_profile: Dict) -> str:
        """추천 이유 생성"""
        reasons = []
        
        if performance.get('category') in user_profile.get('preferred_categories', []):
            reasons.append("선호하는 카테고리")
        
        if performance.get('location') in user_profile.get('preferred_locations', []):
            reasons.append("선호하는 지역")
        
        price = self._extract_price(performance.get('price', '0'))
        user_price_range = user_profile.get('price_range', 'all')
        
        if user_price_range != 'all':
            if user_price_range == 'low' and price <= 20000:
                reasons.append("선호하는 가격대")
            elif user_price_range == 'medium' and 20000 < price <= 50000:
                reasons.append("선호하는 가격대")
            elif user_price_range == 'high' and price > 50000:
                reasons.append("선호하는 가격대")
        
        if reasons:
            return f"추천 이유: {', '.join(reasons)}"
        else:
            return "새로운 공연을 발견해보세요!"

class RecommendationEngine:
    """통합 추천 엔진"""
    
    def __init__(self):
        self.recommender = PerformanceRecommender()
        self.logger = logging.getLogger(__name__)
    
    def get_hybrid_recommendations(self, user_id: int, user_profile: Dict, 
                                 performances: List[Dict], user_ratings: List[Dict] = None,
                                 top_n: int = 20) -> Dict:
        """하이브리드 추천 (여러 방법 조합)"""
        recommendations = {
            'preference_based': [],
            'collaborative': [],
            'popularity_based': [],
            'diversity_based': [],
            'hybrid': []
        }
        
        # 1. 선호도 기반 추천
        recommendations['preference_based'] = self.recommender.recommend_by_preferences(
            user_profile, performances, top_n // 4
        )
        
        # 2. 인기도 기반 추천
        recommendations['popularity_based'] = self.recommender.recommend_by_popularity(
            performances, top_n // 4
        )
        
        # 3. 다양성 기반 추천
        recommendations['diversity_based'] = self.recommender.recommend_by_diversity(
            performances, top_n // 4
        )
        
        # 4. 협업 필터링 (평점 데이터가 있는 경우)
        if user_ratings:
            recommendations['collaborative'] = self.recommender.recommend_by_collaborative_filtering(
                user_id, user_profile.get('ratings', {}), user_ratings, performances, top_n // 4
            )
        
        # 5. 하이브리드 추천 (모든 방법 조합)
        all_recommendations = []
        
        # 각 방법별로 가중치 적용
        for rec in recommendations['preference_based']:
            all_recommendations.append({
                'performance': rec['performance'],
                'score': rec['score'] * 0.4,  # 선호도 기반 가중치
                'method': 'preference',
                'reason': rec['reason']
            })
        
        for rec in recommendations['popularity_based']:
            all_recommendations.append({
                'performance': rec['performance'],
                'score': rec['score'] * 0.3,  # 인기도 기반 가중치
                'method': 'popularity',
                'reason': rec['reason']
            })
        
        for rec in recommendations['diversity_based']:
            all_recommendations.append({
                'performance': rec['performance'],
                'score': rec['score'] * 0.2,  # 다양성 기반 가중치
                'method': 'diversity',
                'reason': rec['reason']
            })
        
        for rec in recommendations['collaborative']:
            all_recommendations.append({
                'performance': rec['performance'],
                'score': rec['predicted_rating'] * 0.1,  # 협업 필터링 가중치
                'method': 'collaborative',
                'reason': rec['reason']
            })
        
        # 중복 제거 및 점수 합산
        performance_scores = {}
        for rec in all_recommendations:
            perf_id = rec['performance'].get('id')
            if perf_id not in performance_scores:
                performance_scores[perf_id] = {
                    'performance': rec['performance'],
                    'total_score': 0,
                    'methods': [],
                    'reasons': []
                }
            
            performance_scores[perf_id]['total_score'] += rec['score']
            performance_scores[perf_id]['methods'].append(rec['method'])
            performance_scores[perf_id]['reasons'].append(rec['reason'])
        
        # 최종 하이브리드 추천
        hybrid_recs = list(performance_scores.values())
        hybrid_recs.sort(key=lambda x: x['total_score'], reverse=True)
        
        recommendations['hybrid'] = hybrid_recs[:top_n]
        
        return recommendations
    
    def get_personalized_recommendations(self, user_id: int, user_profile: Dict, 
                                       performances: List[Dict]) -> List[Dict]:
        """개인화된 추천 (사용자 상황에 맞춤)"""
        # 사용자 상황 분석
        current_time = datetime.now()
        recommendations = []
        
        for performance in performances:
            score = 0
            reasons = []
            
            try:
                perf_date = datetime.strptime(performance.get('date', ''), '%Y-%m-%d')
                days_until = (perf_date - current_time).days
                
                # 시간적 근접성
                if 0 <= days_until <= 7:
                    score += 5
                    reasons.append("이번 주 공연")
                elif 8 <= days_until <= 30:
                    score += 3
                    reasons.append("이번 달 공연")
                
                # 계절적 적합성
                current_month = current_time.month
                perf_month = perf_date.month
                
                if current_month in [12, 1, 2] and perf_month in [12, 1, 2]:
                    score += 2
                    reasons.append("겨울 공연")
                elif current_month in [3, 4, 5] and perf_month in [3, 4, 5]:
                    score += 2
                    reasons.append("봄 공연")
                elif current_month in [6, 7, 8] and perf_month in [6, 7, 8]:
                    score += 2
                    reasons.append("여름 공연")
                elif current_month in [9, 10, 11] and perf_month in [9, 10, 11]:
                    score += 2
                    reasons.append("가을 공연")
                
            except:
                pass
            
            # 선호도 매칭
            if performance.get('category') in user_profile.get('preferred_categories', []):
                score += 3
                reasons.append("선호 카테고리")
            
            if performance.get('location') in user_profile.get('preferred_locations', []):
                score += 2
                reasons.append("선호 지역")
            
            if score > 0:
                recommendations.append({
                    'performance': performance,
                    'score': score,
                    'reasons': reasons
                })
        
        # 점수순 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:10]

def main():
    """테스트 실행"""
    # 샘플 사용자 프로필
    user_profile = {
        'categories': ['뮤지컬', '연극'],
        'locations': ['서울', '경기'],
        'price_range': 'medium',
        'time': 'all',
        'interests': ['음악', '연극'],
        'viewing_history': ['햄릿', '오셀로'],
        'ratings': {1: 4, 2: 5, 3: 3}
    }
    
    # 샘플 공연 데이터
    sample_performances = [
        {
            'id': 1,
            'title': '레미제라블',
            'category': '뮤지컬',
            'location': '서울',
            'price': '80,000원',
            'date': '2024-12-15',
            'time': '19:30',
            'description': '빅터 위고의 소설을 바탕으로 한 세계적인 뮤지컬',
            'likes': 150,
            'comments': [{'user_id': 1, 'content': '훌륭한 공연이었습니다!'}]
        },
        {
            'id': 2,
            'title': '햄릿',
            'category': '연극',
            'location': '서울',
            'price': '50,000원',
            'date': '2024-12-20',
            'time': '20:00',
            'description': '셰익스피어의 대표작',
            'likes': 120,
            'comments': []
        }
    ]
    
    # 추천 엔진 테스트
    engine = RecommendationEngine()
    
    # 하이브리드 추천
    recommendations = engine.get_hybrid_recommendations(
        user_id=1,
        user_profile=user_profile,
        performances=sample_performances
    )
    
    print("=== 추천 결과 ===")
    for method, recs in recommendations.items():
        print(f"\n{method.upper()} 추천:")
        for i, rec in enumerate(recs[:3]):
            if 'performance' in rec:
                print(f"  {i+1}. {rec['performance']['title']} - {rec.get('reason', '추천')}")

if __name__ == '__main__':
    main() 