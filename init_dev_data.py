#!/usr/bin/env python3
"""
개발용 샘플 데이터 초기화 스크립트
로컬 개발 환경에서 테스트용 데이터를 생성합니다.
"""

import os
import sys
from datetime import datetime, timedelta
from main import app, db, User, Performance
from werkzeug.security import generate_password_hash

def create_sample_data():
    """샘플 데이터 생성"""
    with app.app_context():
        print("🗄️  개발용 샘플 데이터 생성 중...")
        
        # 기존 데이터 삭제 (선택사항)
        if input("기존 데이터를 모두 삭제하시겠습니까? (y/N): ").lower() == 'y':
            Performance.query.delete()
            User.query.filter(User.username != 'admin').delete()
            db.session.commit()
            print("✅ 기존 데이터 삭제 완료")
        
        # 샘플 사용자 생성
        sample_users = [
            {
                'name': '김댄서',
                'username': 'dancer1',
                'email': 'dancer1@test.com',
                'phone': '010-1111-1111',
                'password': 'test123'
            },
            {
                'name': '이크루',
                'username': 'crew2',
                'email': 'crew2@test.com',
                'phone': '010-2222-2222',
                'password': 'test123'
            },
            {
                'name': '박스트릿',
                'username': 'street3',
                'email': 'street3@test.com',
                'phone': '010-3333-3333',
                'password': 'test123'
            }
        ]
        
        created_users = []
        for user_data in sample_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    name=user_data['name'],
                    username=user_data['username'],
                    email=user_data['email'],
                    phone=user_data['phone'],
                    password_hash=generate_password_hash(user_data['password'])
                )
                db.session.add(user)
                created_users.append(user)
                print(f"👤 사용자 생성: {user_data['name']} ({user_data['username']})")
        
        db.session.commit()
        
        # 샘플 공연 데이터 생성
        sample_performances = [
            {
                'title': '스트릿댄스 쇼케이스',
                'group_name': '스트릿크루',
                'description': '다양한 스트릿댄스 장르를 선보이는 쇼케이스입니다. 힙합, 브레이킹, 팝핑 등 다양한 댄스 스타일을 감상하실 수 있습니다.',
                'location': '홍대 클럽',
                'price': '무료',
                'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'time': '19:00~21:00',
                'contact_email': 'street@test.com',
                'video_url': 'https://www.youtube.com/watch?v=example1',
                'is_approved': True
            },
            {
                'title': '대학 댄스동아리 공연',
                'group_name': '대학댄스팀',
                'description': '대학 댄스동아리 학생들이 준비한 창작 댄스 공연입니다. 젊은 감각과 열정이 담긴 무대를 선보입니다.',
                'location': '대학 강당',
                'price': '5,000원',
                'date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                'time': '18:00~20:00',
                'contact_email': 'university@test.com',
                'video_url': 'https://www.youtube.com/watch?v=example2',
                'is_approved': True
            },
            {
                'title': '힙합 댄스 배틀',
                'group_name': '힙합크루',
                'description': '전국 힙합댄서들이 모여 실력을 겨루는 배틀 대회입니다. 치열한 경쟁과 화려한 무대를 감상하세요.',
                'location': '올림픽공원',
                'price': '10,000원',
                'date': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                'time': '14:00~18:00',
                'contact_email': 'hiphop@test.com',
                'video_url': 'https://www.youtube.com/watch?v=example3',
                'is_approved': False  # 승인 대기 중
            }
        ]
        
        for i, perf_data in enumerate(sample_performances):
            existing_perf = Performance.query.filter_by(title=perf_data['title']).first()
            if not existing_perf:
                # 사용자 할당 (승인된 공연은 첫 번째 사용자, 대기 중인 공연은 두 번째 사용자)
                user_index = 0 if perf_data['is_approved'] else 1
                user = created_users[user_index] if len(created_users) > user_index else created_users[0]
                
                performance = Performance(
                    title=perf_data['title'],
                    group_name=perf_data['group_name'],
                    description=perf_data['description'],
                    location=perf_data['location'],
                    price=perf_data['price'],
                    date=perf_data['date'],
                    time=perf_data['time'],
                    contact_email=perf_data['contact_email'],
                    video_url=perf_data['video_url'],
                    user_id=user.id,
                    is_approved=perf_data['is_approved']
                )
                db.session.add(performance)
                status = "승인됨" if perf_data['is_approved'] else "승인 대기"
                print(f"🎭 공연 생성: {perf_data['title']} ({status})")
        
        db.session.commit()
        
        print("\n✅ 샘플 데이터 생성 완료!")
        print(f"📊 생성된 데이터:")
        print(f"   - 사용자: {len(created_users)}명")
        print(f"   - 공연: {len(sample_performances)}개")
        print(f"   - 승인된 공연: {len([p for p in sample_performances if p['is_approved']])}개")
        print(f"   - 승인 대기: {len([p for p in sample_performances if not p['is_approved']])}개")
        
        print("\n🔑 테스트 계정:")
        for user_data in sample_users:
            print(f"   - {user_data['username']} / {user_data['password']}")
        print("   - admin / admin123 (관리자)")

if __name__ == '__main__':
    try:
        create_sample_data()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1) 