#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
기존 공연 데이터에 메인 카테고리를 추가합니다.
"""

import os
import sys
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app, db, Performance, detect_region_from_address

def migrate_categories():
    """기존 공연 데이터에 메인 카테고리를 추가하는 마이그레이션"""
    
    with app.app_context():
        try:
            # 기존 공연 데이터 조회
            performances = Performance.query.all()
            
            print(f"총 {len(performances)}개의 공연 데이터를 마이그레이션합니다...")
            
            # 각 공연에 메인 카테고리 및 region 추가
            for performance in performances:
                # region 자동 채우기
                if not performance.region and performance.address:
                    performance.region = detect_region_from_address(performance.address)
                    print(f"공연 '{performance.title}'의 지역(region) 자동 채움: {performance.region}")
                if not performance.main_category:
                    # 기존 카테고리를 기반으로 메인 카테고리 설정
                    if performance.category in ['연극', '뮤지컬', '서양음악(클래식)', '한국음악(국악)', 
                                               '대중음악', '무용(서양/한국무용)', '대중무용', '서커스/마술', '복합']:
                        performance.main_category = '공연'
                    else:
                        # 기본값으로 공연 설정
                        performance.main_category = '공연'
                    print(f"공연 '{performance.title}'에 메인 카테고리 '{performance.main_category}' 추가")
            
            # 변경사항 저장
            db.session.commit()
            print("마이그레이션이 완료되었습니다!")
            
        except Exception as e:
            print(f"마이그레이션 중 오류 발생: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_categories() 