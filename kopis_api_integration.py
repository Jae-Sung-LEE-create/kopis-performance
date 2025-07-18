#!/usr/bin/env python3
"""
KOPIS API 연동 시스템
공연예술통합전산망(KOPIS) 데이터를 활용한 공연시장 분석 및 발전 도구
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

load_dotenv()

class KOPISAPIClient:
    """KOPIS API 클라이언트"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('KOPIS_API_KEY')
        self.base_url = "http://www.kopis.or.kr/openApi/restful"
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("KOPIS API 키가 설정되지 않았습니다.")
    
    def get_performance_list(self, 
                           start_date: str = None, 
                           end_date: str = None,
                           category: str = None,
                           location: str = None,
                           limit: int = 100) -> List[Dict]:
        """공연 목록 조회"""
        if not self.api_key:
            return []
        
        # 기본 날짜 설정 (최근 1개월)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y%m%d')
        
        params = {
            'service': self.api_key,
            'stdate': start_date,
            'eddate': end_date,
            'rows': limit,
            'cpage': 1
        }
        
        if category:
            params['catecode'] = self._get_category_code(category)
        if location:
            params['area'] = self._get_area_code(location)
        
        try:
            response = requests.get(f"{self.base_url}/pblprfr", params=params)
            response.raise_for_status()
            
            # XML 응답을 파싱 (간단한 파싱)
            data = self._parse_xml_response(response.text)
            return data
            
        except Exception as e:
            self.logger.error(f"KOPIS API 호출 실패: {e}")
            return []
    
    def get_performance_detail(self, performance_id: str) -> Optional[Dict]:
        """공연 상세 정보 조회"""
        if not self.api_key:
            return None
        
        params = {
            'service': self.api_key,
            'mt20id': performance_id
        }
        
        try:
            response = requests.get(f"{self.base_url}/pblprfr/{performance_id}", params=params)
            response.raise_for_status()
            
            # 상세 정보 전용 파싱 메서드 사용
            data = self._parse_detail_xml_response(response.text)
            return data
            
        except Exception as e:
            self.logger.error(f"공연 상세 정보 조회 실패: {e}")
            return None
    
    def get_venue_list(self, location: str = None) -> List[Dict]:
        """공연장 목록 조회"""
        if not self.api_key:
            return []
        
        params = {
            'service': self.api_key,
            'rows': 100,
            'cpage': 1
        }
        
        if location:
            params['area'] = self._get_area_code(location)
        
        try:
            response = requests.get(f"{self.base_url}/prfplc", params=params)
            response.raise_for_status()
            
            data = self._parse_xml_response(response.text)
            return data
            
        except Exception as e:
            self.logger.error(f"공연장 목록 조회 실패: {e}")
            return []
    
    def _get_category_code(self, category: str) -> str:
        """카테고리 코드 매핑"""
        category_mapping = {
            '연극': 'AAAA',
            '뮤지컬': 'AAAB',
            '서양음악(클래식)': 'CCCA',
            '한국음악(국악)': 'CCCB',
            '대중음악': 'CCCC',
            '무용(서양/한국무용)': 'BBBA',
            '대중무용': 'BBBB',
            '서커스/마술': 'EEEA',
            '복합': 'EEEE'
        }
        return category_mapping.get(category, '')
    
    def _get_area_code(self, location: str) -> str:
        """지역 코드 매핑"""
        area_mapping = {
            '서울': '11',
            '부산': '21',
            '대구': '22',
            '인천': '23',
            '광주': '24',
            '대전': '25',
            '울산': '26',
            '세종': '29',
            '경기': '31',
            '강원': '32',
            '충북': '33',
            '충남': '34',
            '전북': '35',
            '전남': '36',
            '경북': '37',
            '경남': '38',
            '제주': '39'
        }
        return area_mapping.get(location, '')
    
    def _parse_xml_response(self, xml_text: str) -> List[Dict]:
        """XML 응답을 파싱하여 딕셔너리 리스트로 변환"""
        try:
            root = ET.fromstring(xml_text)
            performances = []
            
            # 공연 목록 파싱
            for db in root.findall('.//db'):
                perf_data = {}
                
                # 기본 정보 추출
                perf_data['kopis_id'] = self._get_text(db, 'mt20id')
                perf_data['title'] = self._get_text(db, 'prfnm')
                perf_data['group_name'] = self._get_text(db, 'prfpdfrom')
                perf_data['date'] = self._get_text(db, 'prfpdfrom')
                perf_data['end_date'] = self._get_text(db, 'prfpdto')
                perf_data['location'] = self._get_text(db, 'fcltynm')
                perf_data['address'] = self._get_text(db, 'adres')
                perf_data['category'] = self._get_text(db, 'genrenm')
                perf_data['price'] = self._get_text(db, 'pcseguidance')
                perf_data['image_url'] = self._get_text(db, 'poster')
                perf_data['description'] = self._get_text(db, 'sty')
                perf_data['time'] = self._get_text(db, 'dtguidance')
                
                # 예매처 정보 추출 (KOPIS API 실제 필드명)
                perf_data['ticket_url'] = self._get_text(db, 'ticket_url')  # 예매 URL
                perf_data['booking_phone'] = self._get_text(db, 'telno')  # 예매 전화번호
                perf_data['booking_website'] = self._get_text(db, 'relateurl')  # 관련 URL
                perf_data['contact_email'] = self._get_text(db, 'email')  # 연락처 이메일
                
                # 필수 필드가 있는 경우만 추가
                if perf_data['title'] and perf_data['kopis_id']:
                    performances.append(perf_data)
            
            self.logger.info(f"XML 파싱 완료: {len(performances)}개의 공연 데이터 추출")
            return performances
            
        except Exception as e:
            self.logger.error(f"XML 파싱 실패: {e}")
            return []
    
    def _parse_detail_xml_response(self, xml_text: str) -> Optional[Dict]:
        """공연 상세 정보 XML 파싱"""
        try:
            root = ET.fromstring(xml_text)
            db = root.find('.//db')
            
            if db is None:
                return None
            
            detail_data = {}
            
            # 기본 정보
            detail_data['kopis_id'] = self._get_text(db, 'mt20id')
            detail_data['title'] = self._get_text(db, 'prfnm')
            detail_data['group_name'] = self._get_text(db, 'prfpdfrom')
            detail_data['date'] = self._get_text(db, 'prfpdfrom')
            detail_data['end_date'] = self._get_text(db, 'prfpdto')
            detail_data['location'] = self._get_text(db, 'fcltynm')
            detail_data['address'] = self._get_text(db, 'adres')
            detail_data['category'] = self._get_text(db, 'genrenm')
            detail_data['price'] = self._get_text(db, 'pcseguidance')
            detail_data['image_url'] = self._get_text(db, 'poster')
            detail_data['description'] = self._get_text(db, 'sty')
            detail_data['time'] = self._get_text(db, 'dtguidance')
            
            # 예매처 정보 (상세 정보에서 더 정확한 정보)
            detail_data['ticket_url'] = self._get_text(db, 'ticket_url')
            detail_data['booking_phone'] = self._get_text(db, 'telno')
            detail_data['booking_website'] = self._get_text(db, 'relateurl')
            detail_data['contact_email'] = self._get_text(db, 'email')
            
            # KOPIS 예매처 시스템 정보
            detail_data['booking_system'] = self._get_text(db, 'booking_system')
            detail_data['booking_links'] = self._get_text(db, 'booking_links')
            
            return detail_data
            
        except Exception as e:
            self.logger.error(f"상세 정보 XML 파싱 실패: {e}")
            return None
    
    def _get_text(self, element, tag: str) -> str:
        """XML 요소에서 텍스트 추출"""
        child = element.find(tag)
        return child.text if child is not None else ''

class PerformanceAnalytics:
    """공연 데이터 분석 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_market_trends(self, performances: List[Dict]) -> Dict:
        """공연시장 트렌드 분석"""
        if not performances:
            return {}
        
        df = pd.DataFrame(performances)
        
        # 카테고리별 공연 수
        category_counts = df['category'].value_counts().to_dict()
        
        # 월별 공연 수
        df['month'] = pd.to_datetime(df['date']).dt.month
        monthly_counts = df['month'].value_counts().sort_index().to_dict()
        
        # 지역별 공연 수
        location_counts = df['location'].value_counts().to_dict()
        
        # 평균 가격 분석
        price_analysis = self._analyze_prices(df)
        
        return {
            'category_distribution': category_counts,
            'monthly_trends': monthly_counts,
            'location_distribution': location_counts,
            'price_analysis': price_analysis,
            'total_performances': len(performances)
        }
    
    def _analyze_prices(self, df: pd.DataFrame) -> Dict:
        """가격 분석"""
        try:
            # 가격 데이터 정제 (숫자만 추출)
            df['price_numeric'] = df['price'].str.extract(r'(\d+)').astype(float)
            
            return {
                'average_price': df['price_numeric'].mean(),
                'median_price': df['price_numeric'].median(),
                'min_price': df['price_numeric'].min(),
                'max_price': df['price_numeric'].max(),
                'price_ranges': {
                    '저가': len(df[df['price_numeric'] <= 20000]),
                    '중가': len(df[(df['price_numeric'] > 20000) & (df['price_numeric'] <= 50000)]),
                    '고가': len(df[df['price_numeric'] > 50000])
                }
            }
        except Exception as e:
            self.logger.error(f"가격 분석 실패: {e}")
            return {}
    
    def generate_market_report(self, analytics_data: Dict) -> str:
        """시장 분석 리포트 생성"""
        report = []
        report.append("# 공연시장 분석 리포트")
        report.append(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 전체 공연 수
        report.append(f"## 전체 공연 수: {analytics_data.get('total_performances', 0)}개")
        report.append("")
        
        # 카테고리별 분포
        report.append("## 카테고리별 공연 분포")
        for category, count in analytics_data.get('category_distribution', {}).items():
            report.append(f"- {category}: {count}개")
        report.append("")
        
        # 지역별 분포
        report.append("## 지역별 공연 분포")
        for location, count in analytics_data.get('location_distribution', {}).items():
            report.append(f"- {location}: {count}개")
        report.append("")
        
        # 가격 분석
        price_analysis = analytics_data.get('price_analysis', {})
        if price_analysis:
            report.append("## 가격 분석")
            report.append(f"- 평균 가격: {price_analysis.get('average_price', 0):,.0f}원")
            report.append(f"- 중간값 가격: {price_analysis.get('median_price', 0):,.0f}원")
            report.append(f"- 최저 가격: {price_analysis.get('min_price', 0):,.0f}원")
            report.append(f"- 최고 가격: {price_analysis.get('max_price', 0):,.0f}원")
            report.append("")
            
            report.append("### 가격대별 분포")
            for range_name, count in price_analysis.get('price_ranges', {}).items():
                report.append(f"- {range_name}: {count}개")
        
        return "\n".join(report)

class KOPISDataImporter:
    """KOPIS 데이터 임포트 클래스"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.kopis_client = KOPISAPIClient()
        self.logger = logging.getLogger(__name__)
        
        # Performance 모델 import
        try:
            from main import Performance
            self.Performance = Performance
        except ImportError:
            self.logger.error("Performance 모델을 import할 수 없습니다.")
            self.Performance = None
    
    def import_performances(self, start_date: str = None, end_date: str = None) -> int:
        """KOPIS 데이터를 로컬 데이터베이스로 임포트"""
        try:
            # 실제 KOPIS API 호출
            performances = self.kopis_client.get_performance_list(start_date, end_date)
            self.logger.info(f"KOPIS API에서 {len(performances)}개의 공연 데이터를 가져왔습니다.")
            
            imported_count = 0
            for perf_data in performances:
                try:
                    # 중복 확인 (제목으로 체크)
                    existing = self.db_session.query(self.Performance).filter_by(
                        title=perf_data.get('title', '')
                    ).first()
                    
                    if existing:
                        self.logger.info(f"이미 존재하는 공연: {perf_data.get('title', '')}")
                        continue
                    
                    # 공연 상세 정보 가져오기 (예매처 정보 포함)
                    if perf_data.get('kopis_id'):
                        detail_data = self.kopis_client.get_performance_detail(perf_data['kopis_id'])
                        if detail_data:
                            # 상세 정보에서 예매처 정보 업데이트
                            perf_data['ticket_url'] = detail_data.get('ticket_url', perf_data.get('ticket_url', ''))
                            perf_data['booking_phone'] = detail_data.get('booking_phone', '')
                            perf_data['booking_website'] = detail_data.get('booking_website', '')
                            perf_data['contact_email'] = detail_data.get('contact_email', '')
                    
                    # 구매 방법 설정 (예매처 정보 기반)
                    purchase_methods = []
                    if perf_data.get('ticket_url'):
                        purchase_methods.append('사이트구매')
                    if perf_data.get('booking_phone'):
                        purchase_methods.append('전화구매')
                    if not purchase_methods:
                        purchase_methods.append('현장구매')
                    
                    # 새로운 공연 데이터 생성
                    performance = self.Performance(
                        title=perf_data.get('title', ''),
                        group_name=perf_data.get('group_name', ''),
                        description=perf_data.get('description', ''),
                        location=perf_data.get('location', ''),
                        address=perf_data.get('address', ''),
                        price=perf_data.get('price', ''),
                        date=perf_data.get('date', ''),
                        time=perf_data.get('time', ''),
                        contact_email=perf_data.get('contact_email', ''),
                        video_url=perf_data.get('video_url', ''),
                        image_url=perf_data.get('image_url', ''),
                        main_category='공연',
                        category=perf_data.get('category', ''),
                        ticket_url=perf_data.get('ticket_url', ''),
                        purchase_methods=json.dumps(purchase_methods),
                        is_approved=True,
                        kopis_id=perf_data.get('kopis_id', ''),
                        kopis_synced_at=datetime.now()
                    )
                    
                    self.db_session.add(performance)
                    imported_count += 1
                    self.logger.info(f"새로운 공연 추가: {perf_data.get('title', '')} (예매처: {', '.join(purchase_methods)})")
                    
                except Exception as e:
                    self.logger.error(f"공연 데이터 임포트 실패: {e}")
                    continue
            
            self.db_session.commit()
            self.logger.info(f"총 {imported_count}개의 새로운 공연이 성공적으로 임포트되었습니다.")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"KOPIS 데이터 임포트 중 오류 발생: {e}")
            return 0

def main():
    """메인 실행 함수"""
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # KOPIS API 클라이언트 테스트
    client = KOPISAPIClient()
    
    # 최근 공연 데이터 조회
    performances = client.get_performance_list()
    print(f"조회된 공연 수: {len(performances)}")
    
    # 분석 실행
    analytics = PerformanceAnalytics()
    analytics_data = analytics.analyze_market_trends(performances)
    
    # 리포트 생성
    report = analytics.generate_market_report(analytics_data)
    print(report)
    
    # 리포트 파일 저장
    with open('market_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("분석 완료! market_report.md 파일을 확인하세요.")

if __name__ == '__main__':
    main() 