#!/usr/bin/env python3
"""
데이터 분석 기능을 위한 데이터베이스 마이그레이션 스크립트
새로운 테이블들을 생성하고 기존 데이터를 보존합니다.
"""

import os
import sys
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db, User, Performance, UserEvent, ABTest, ABTestResult, TrendData, UserProfile

def create_analytics_tables():
    """데이터 분석을 위한 새로운 테이블들을 생성합니다."""
    print("🔧 데이터 분석 테이블 생성 중...")
    
    with app.app_context():
        try:
            # 새로운 테이블들 생성
            db.create_all()
            print("✅ 모든 테이블이 성공적으로 생성되었습니다.")
            
            # 테이블 목록 확인
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 생성된 테이블 목록: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 테이블 생성 중 오류 발생: {e}")
            return False

def create_sample_data():
    """샘플 데이터를 생성합니다."""
    print("📊 샘플 데이터 생성 중...")
    
    with app.app_context():
        try:
            # 기존 사용자들에 대한 프로필 생성
            users = User.query.all()
            for user in users:
                # 이미 프로필이 있는지 확인
                if not hasattr(user, 'profile') or user.profile is None:
                    profile = UserProfile(
                        user_id=user.id,
                        age_group='20s',  # 기본값
                        gender='other',   # 기본값
                        region='서울',    # 기본값
                        interests='["뮤지컬", "연극"]'  # 기본 관심사
                    )
                    db.session.add(profile)
            
            # 샘플 트렌드 데이터 생성
            today = datetime.now().date()
            categories = ['뮤지컬', '연극', '무용', '클래식']
            
            for i in range(30):  # 최근 30일 데이터
                date = today - timedelta(days=i)
                for category in categories:
                    trend_data = TrendData(
                        date=date,
                        category=category,
                        views=100 + (i * 10) + hash(category) % 50,
                        likes=20 + (i * 2) + hash(category) % 20,
                        comments=5 + (i * 1) + hash(category) % 10,
                        conversions=2 + (i * 1) + hash(category) % 5,
                        revenue=10000 + (i * 1000) + hash(category) % 5000
                    )
                    db.session.add(trend_data)
            
            # 샘플 A/B 테스트 생성
            ab_test = ABTest(
                test_name="공연 제목 A/B 테스트",
                test_type="title",
                variant_a="감동적인 뮤지컬 공연",
                variant_b="최고의 뮤지컬 공연",
                status="active"
            )
            db.session.add(ab_test)
            
            # A/B 테스트 결과 샘플 데이터
            for i in range(7):  # 최근 7일 데이터
                date = datetime.now() - timedelta(days=i)
                
                # A 버전 결과
                result_a = ABTestResult(
                    test_id=1,
                    variant='A',
                    views=100 + (i * 10),
                    clicks=20 + (i * 2),
                    conversions=5 + (i * 1),
                    timestamp=date
                )
                db.session.add(result_a)
                
                # B 버전 결과
                result_b = ABTestResult(
                    test_id=1,
                    variant='B',
                    views=95 + (i * 12),
                    clicks=22 + (i * 3),
                    conversions=6 + (i * 1),
                    timestamp=date
                )
                db.session.add(result_b)
            
            db.session.commit()
            print("✅ 샘플 데이터가 성공적으로 생성되었습니다.")
            
        except Exception as e:
            print(f"❌ 샘플 데이터 생성 중 오류 발생: {e}")
            db.session.rollback()

def verify_tables():
    """생성된 테이블들을 확인합니다."""
    print("🔍 테이블 확인 중...")
    
    with app.app_context():
        try:
            # 각 테이블의 레코드 수 확인
            tables_info = [
                ('UserEvent', UserEvent),
                ('ABTest', ABTest),
                ('ABTestResult', ABTestResult),
                ('TrendData', TrendData),
                ('UserProfile', UserProfile)
            ]
            
            for table_name, model in tables_info:
                count = model.query.count()
                print(f"📊 {table_name}: {count}개 레코드")
            
            print("✅ 모든 테이블이 정상적으로 생성되었습니다.")
            
        except Exception as e:
            print(f"❌ 테이블 확인 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 데이터 분석 기능 마이그레이션 시작")
    print("=" * 50)
    
    # 1. 테이블 생성
    if not create_analytics_tables():
        print("❌ 마이그레이션 실패")
        return
    
    # 2. 샘플 데이터 생성
    create_sample_data()
    
    # 3. 테이블 확인
    verify_tables()
    
    print("=" * 50)
    print("🎉 데이터 분석 기능 마이그레이션 완료!")
    print("이제 관리자 패널에서 데이터 분석 기능을 사용할 수 있습니다.")

if __name__ == "__main__":
    from datetime import timedelta
    main() 