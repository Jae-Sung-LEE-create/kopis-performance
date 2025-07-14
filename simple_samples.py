#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app, db, User, Performance, detect_region_from_address
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def create_simple_samples():
    """간단한 샘플 데이터 생성"""
    with app.app_context():
        print("🎭 간단한 샘플 공연 데이터 생성 중...")
        
        # 기존 데이터 확인
        existing_count = Performance.query.count()
        print(f"현재 공연 수: {existing_count}")
        
        # 기존 데이터 삭제
        if existing_count > 0:
            print("기존 공연 데이터를 삭제하고 새로 생성합니다...")
            Performance.query.delete()
            db.session.commit()
        
        # admin 사용자 찾기
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            return
        
        # 카테고리별 샘플 데이터
        categories = {
            '연극': [
                {
                    'title': '햄릿',
                    'group_name': '서울연극단',
                    'description': '셰익스피어의 대표작을 현대적으로 재해석한 작품입니다.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '50,000원',
                    'date': '2024-12-15',
                    'time': '19:30',
                    'contact_email': 'hamlet@seoultheater.com',
                    'video_url': 'https://www.youtube.com/watch?v=example1',
                    'ticket_url': 'https://ticket.interpark.com/example1'
                },
                {
                    'title': '로미오와 줄리엣',
                    'group_name': '청춘연극회',
                    'description': '사랑과 운명의 비극을 아름답게 그린 작품입니다.',
                    'location': '대학로 소극장',
                    'address': '서울특별시 종로구 대학로 12길 23',
                    'price': '30,000원',
                    'date': '2024-12-20',
                    'time': '20:00',
                    'contact_email': 'romeo@youththeater.com',
                    'video_url': 'https://www.youtube.com/watch?v=example2',
                    'ticket_url': 'https://ticket.interpark.com/example2'
                }
            ],
            '뮤지컬': [
                {
                    'title': '레 미제라블',
                    'group_name': '한국뮤지컬컴퍼니',
                    'description': '빅토르 위고의 소설을 원작으로 한 세계적인 뮤지컬입니다.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '80,000원',
                    'date': '2024-12-25',
                    'time': '19:00',
                    'contact_email': 'lesmis@koreanmusical.com',
                    'video_url': 'https://www.youtube.com/watch?v=example3',
                    'ticket_url': 'https://ticket.interpark.com/example3'
                },
                {
                    'title': '오페라의 유령',
                    'group_name': '팬텀뮤지컬',
                    'description': '파리의 오페라 하우스를 배경으로 한 미스터리 뮤지컬입니다.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '90,000원',
                    'date': '2024-12-30',
                    'time': '19:30',
                    'contact_email': 'phantom@phantommusical.com',
                    'video_url': 'https://www.youtube.com/watch?v=example4',
                    'ticket_url': 'https://ticket.interpark.com/example4'
                }
            ],
            '스트릿댄스': [
                {
                    'title': '힙합 배틀',
                    'group_name': '스트릿크루',
                    'description': '최고의 힙합 댄서들이 모여 펼치는 배틀 쇼입니다.',
                    'location': '홍대 클럽',
                    'address': '서울특별시 마포구 홍익로 1',
                    'price': '무료',
                    'date': '2024-12-10',
                    'time': '21:00',
                    'contact_email': 'battle@streetcrew.com',
                    'video_url': 'https://www.youtube.com/watch?v=example5',
                    'ticket_url': ''
                },
                {
                    'title': '브레이킹 쇼케이스',
                    'group_name': '브레이킹팀',
                    'description': '브레이킹의 모든 요소를 보여주는 쇼케이스입니다.',
                    'location': '강남 댄스스튜디오',
                    'address': '서울특별시 강남구 테헤란로 123',
                    'price': '20,000원',
                    'date': '2024-12-12',
                    'time': '20:30',
                    'contact_email': 'showcase@breakingteam.com',
                    'video_url': 'https://www.youtube.com/watch?v=example6',
                    'ticket_url': 'https://ticket.interpark.com/example6'
                }
            ],
            '클래식': [
                {
                    'title': '베토벤 교향곡 9번',
                    'group_name': '서울교향악단',
                    'description': '베토벤의 마지막 교향곡을 연주합니다.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '60,000원',
                    'date': '2024-12-18',
                    'time': '19:00',
                    'contact_email': 'beethoven@seoulsymphony.com',
                    'video_url': 'https://www.youtube.com/watch?v=example7',
                    'ticket_url': 'https://ticket.interpark.com/example7'
                },
                {
                    'title': '모차르트 피아노 협주곡',
                    'group_name': '모차르트앙상블',
                    'description': '모차르트의 아름다운 피아노 협주곡을 감상하세요.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '50,000원',
                    'date': '2024-12-22',
                    'time': '19:30',
                    'contact_email': 'mozart@mozartensemble.com',
                    'video_url': 'https://www.youtube.com/watch?v=example8',
                    'ticket_url': 'https://ticket.interpark.com/example8'
                }
            ]
        }
        
        # 카테고리별 이미지 URL
        category_images = {
            '연극': [
                'https://images.unsplash.com/photo-1503095396549-807759245b35?w=800',
                'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800'
            ],
            '뮤지컬': [
                'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800'
            ],
            '스트릿댄스': [
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?w=800',
                'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800'
            ],
            '클래식': [
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=800'
            ]
        }
        
        created_count = 0
        
        for category, samples in categories.items():
            print(f"📝 {category} 카테고리 생성 중...")
            
            for i, sample in enumerate(samples):
                try:
                    region = detect_region_from_address(sample['address'])
                    performance = Performance(
                        title=sample['title'],
                        group_name=sample['group_name'],
                        description=sample['description'],
                        location=sample['location'],
                        address=sample['address'],
                        price=sample['price'],
                        date=sample['date'],
                        time=sample['time'],
                        contact_email=sample['contact_email'],
                        video_url=sample['video_url'],
                        image_url=category_images[category][i],
                        main_category='공연',
                        category=category,
                        ticket_url=sample['ticket_url'],
                        user_id=admin_user.id,
                        is_approved=True,
                        region=region
                    )
                    
                    db.session.add(performance)
                    created_count += 1
                    print(f"  ✅ {sample['title']} 생성 완료")
                    
                except Exception as e:
                    print(f"  ❌ {sample['title']} 생성 실패: {e}")
                    continue
        
        try:
            db.session.commit()
            print(f"\n🎉 총 {created_count}개의 샘플 공연이 성공적으로 생성되었습니다!")
            print("✅ 카테고리별 샘플 데이터 생성 완료!")
            
        except Exception as e:
            print(f"❌ 데이터베이스 저장 실패: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_simple_samples() 