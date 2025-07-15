#!/usr/bin/env python3
"""
카테고리별 샘플 공연 데이터 생성 스크립트
각 카테고리별로 4개씩 실제 공연처럼 자연스러운 데이터를 생성합니다.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from main import app, db, User, Performance
from werkzeug.security import generate_password_hash

def create_category_samples():
    """카테고리별 샘플 공연 데이터 생성"""
    with app.app_context():
        print("🎭 카테고리별 샘플 공연 데이터 생성 중...")
        
        # 기존 공연 데이터 확인
        existing_count = Performance.query.count()
        print(f"현재 공연 데이터: {existing_count}개")
        
        # 사용자 확인 (admin 계정 사용)
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ admin 계정을 찾을 수 없습니다.")
            return
        
        # 카테고리별 기본 이미지 URL
        category_images = {
            '연극': [
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4'
            ],
            '뮤지컬': [
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35'
            ],
            '서양음악(클래식)': [
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d'
            ],
            '한국음악(국악)': [
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f'
            ],
            '대중음악': [
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d'
            ],
            '무용(서양/한국무용)': [
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f'
            ],
            '대중무용': [
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f'
            ],
            '서커스/마술': [
                'https://images.unsplash.com/photo-1503095396549-807759245b35',
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4'
            ],
            '복합': [
                'https://images.unsplash.com/photo-1511379938547-c1f69419868d',
                'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',
                'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4',
                'https://images.unsplash.com/photo-1503095396549-807759245b35'
            ]
        }
        
        # 연극 카테고리 샘플 데이터
        theater_samples = [
            {
                'title': '햄릿',
                'group_name': '서울연극단',
                'description': '셰익스피어의 대표작을 현대적으로 재해석한 작품입니다. 복수와 배신, 사랑과 죽음의 주제를 깊이 있게 다룹니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 23',
                'price': '20,000원',
                'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'time': '19:00~21:30',
                'contact_email': 'hamlet@seoultheater.com',
                'video_url': 'https://www.youtube.com/watch?v=example1',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/hamlet'
            },
            {
                'title': '오셀로',
                'group_name': '국립극단',
                'description': '질투와 오해로 인한 비극을 그린 셰익스피어의 명작입니다. 인간의 어두운 면을 예리하게 조명합니다.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '25,000원',
                'date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                'time': '20:00~22:30',
                'contact_email': 'othello@nationaltheater.com',
                'video_url': 'https://www.youtube.com/watch?v=example2',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/othello'
            },
            {
                'title': '로미오와 줄리엣',
                'group_name': '청춘극단',
                'description': '세계에서 가장 유명한 사랑 이야기를 젊은 배우들이 선보입니다. 현대적 무대 연출로 새로운 감동을 전합니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 94',
                'price': '15,000원',
                'date': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                'time': '18:30~20:30',
                'contact_email': 'romeo@youththeater.com',
                'video_url': 'https://www.youtube.com/watch?v=example3',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': '맥베스',
                'group_name': '어둠의극단',
                'description': '권력과 야망의 어두운 세계를 그린 셰익스피어의 대표작입니다. 강력한 무대 연출과 연기가 돋보입니다.',
                'location': '이태원',
                'address': '서울특별시 용산구 이태원로 145',
                'price': '18,000원',
                'date': (datetime.now() + timedelta(days=28)).strftime('%Y-%m-%d'),
                'time': '19:30~21:45',
                'contact_email': 'macbeth@darktheater.com',
                'video_url': 'https://www.youtube.com/watch?v=example4',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.melon.com/macbeth'
            }
        ]
        
        # 뮤지컬 카테고리 샘플 데이터
        musical_samples = [
            {
                'title': '레미제라블',
                'group_name': '브로드웨이뮤지컬',
                'description': '빅터 위고의 소설을 바탕으로 한 세계적인 뮤지컬입니다. 웅장한 음악과 감동적인 스토리를 선보입니다.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '80,000원',
                'date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
                'time': '19:30~22:30',
                'contact_email': 'lesmis@broadway.com',
                'video_url': 'https://www.youtube.com/watch?v=example5',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/lesmis'
            },
            {
                'title': '오페라의 유령',
                'group_name': '팬텀뮤지컬',
                'description': '파리 오페라극장을 배경으로 한 로맨틱한 뮤지컬입니다. 아름다운 음악과 화려한 무대가 돋보입니다.',
                'location': '세종문화회관',
                'address': '서울특별시 종로구 세종로 81-3',
                'price': '70,000원',
                'date': (datetime.now() + timedelta(days=17)).strftime('%Y-%m-%d'),
                'time': '20:00~23:00',
                'contact_email': 'phantom@opera.com',
                'video_url': 'https://www.youtube.com/watch?v=example6',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/phantom'
            },
            {
                'title': '캣츠',
                'group_name': '캣뮤지컬',
                'description': 'T.S. 엘리엇의 시를 바탕으로 한 뮤지컬입니다. 고양이들의 축제를 통해 인생의 의미를 되새겨봅니다.',
                'location': '올림픽공원',
                'address': '서울특별시 송파구 올림픽로 25',
                'price': '60,000원',
                'date': (datetime.now() + timedelta(days=24)).strftime('%Y-%m-%d'),
                'time': '19:00~21:30',
                'contact_email': 'cats@musical.com',
                'video_url': 'https://www.youtube.com/watch?v=example7',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.melon.com/cats'
            },
            {
                'title': '시카고',
                'group_name': '시카고뮤지컬',
                'description': '1920년대 시카고를 배경으로 한 재즈 뮤지컬입니다. 화려한 춤과 음악으로 관객을 사로잡습니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 45',
                'price': '55,000원',
                'date': (datetime.now() + timedelta(days=31)).strftime('%Y-%m-%d'),
                'time': '20:30~22:45',
                'contact_email': 'chicago@jazz.com',
                'video_url': 'https://www.youtube.com/watch?v=example8',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/chicago'
            }
        ]
        
        # 서양음악(클래식) 카테고리 샘플 데이터
        classical_samples = [
            {
                'title': '베토벤 교향곡 9번',
                'group_name': '서울필하모닉',
                'description': '베토벤의 마지막 교향곡으로, "환희의 송가"로 유명합니다. 웅장한 오케스트라와 합창단의 연주를 감상하세요.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '50,000원',
                'date': (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d'),
                'time': '20:00~22:30',
                'contact_email': 'beethoven@seoulphil.com',
                'video_url': 'https://www.youtube.com/watch?v=example9',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/beethoven9'
            },
            {
                'title': '모차르트 피아노 협주곡',
                'group_name': 'KBS교향악단',
                'description': '모차르트의 아름다운 피아노 협주곡을 세계적인 피아니스트와 함께하는 특별한 공연입니다.',
                'location': '세종문화회관',
                'address': '서울특별시 종로구 세종로 81-3',
                'price': '40,000원',
                'date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'time': '19:30~21:30',
                'contact_email': 'mozart@kbsorchestra.com',
                'video_url': 'https://www.youtube.com/watch?v=example10',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/mozart'
            },
            {
                'title': '차이콥스키 백조의 호수',
                'group_name': '국립발레단',
                'description': '클래식 발레의 대표작을 국립발레단이 선보입니다. 아름다운 음악과 우아한 춤동작을 감상하세요.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '60,000원',
                'date': (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d'),
                'time': '19:00~21:30',
                'contact_email': 'swanlake@nationalballet.com',
                'video_url': 'https://www.youtube.com/watch?v=example11',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.melon.com/swanlake'
            },
            {
                'title': '바흐 무반주 첼로 모음곡',
                'group_name': '서울챔버오케스트라',
                'description': '바흐의 무반주 첼로 모음곡을 세계적인 첼리스트가 연주합니다. 순수하고 깊이 있는 음악을 경험하세요.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 67',
                'price': '30,000원',
                'date': (datetime.now() + timedelta(days=29)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'bach@seoulchamber.com',
                'video_url': 'https://www.youtube.com/watch?v=example12',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            }
        ]
        
        # 한국음악(국악) 카테고리 샘플 데이터
        gugak_samples = [
            {
                'title': '판소리 춘향가',
                'group_name': '국립국악원',
                'description': '한국의 대표적인 판소리 춘향가를 명창이 선보입니다. 전통의 아름다움과 깊이를 느껴보세요.',
                'location': '국립국악원',
                'address': '서울특별시 서초구 남부순환로 2364',
                'price': '25,000원',
                'date': (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d'),
                'time': '19:30~21:30',
                'contact_email': 'chunhyang@nationalgugak.com',
                'video_url': 'https://www.youtube.com/watch?v=example13',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.gugak.go.kr/chunhyang'
            },
            {
                'title': '사물놀이 공연',
                'group_name': '사물놀이단',
                'description': '전통 사물놀이의 역동적인 리듬과 화려한 연주를 감상하세요. 한국의 전통 타악기의 진수를 선보입니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 89',
                'price': '20,000원',
                'date': (datetime.now() + timedelta(days=16)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'samulnori@traditional.com',
                'video_url': 'https://www.youtube.com/watch?v=example14',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': '가야금 산조',
                'group_name': '가야금앙상블',
                'description': '한국의 대표적인 전통악기 가야금의 아름다운 선율을 감상하세요. 산조의 깊이 있는 음악을 경험합니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 156',
                'price': '15,000원',
                'date': (datetime.now() + timedelta(days=23)).strftime('%Y-%m-%d'),
                'time': '19:00~20:30',
                'contact_email': 'gayageum@ensemble.com',
                'video_url': 'https://www.youtube.com/watch?v=example15',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/gayageum'
            },
            {
                'title': '국악 오페라 심청가',
                'group_name': '국악오페라단',
                'description': '전통 판소리를 현대적으로 재해석한 국악 오페라입니다. 심청의 효심과 사랑 이야기를 감상하세요.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '35,000원',
                'date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'time': '19:30~22:00',
                'contact_email': 'simcheong@koreanopera.com',
                'video_url': 'https://www.youtube.com/watch?v=example16',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/simcheong'
            }
        ]
        
        # 대중음악 카테고리 샘플 데이터
        pop_samples = [
            {
                'title': 'K-POP 콘서트',
                'group_name': 'K-POP스타즈',
                'description': '인기 K-POP 아티스트들의 화려한 무대를 감상하세요. 최신 댄스곡과 팝송을 선보입니다.',
                'location': '올림픽공원',
                'address': '서울특별시 송파구 올림픽로 25',
                'price': '80,000원',
                'date': (datetime.now() + timedelta(days=11)).strftime('%Y-%m-%d'),
                'time': '19:00~22:00',
                'contact_email': 'kpop@concert.com',
                'video_url': 'https://www.youtube.com/watch?v=example17',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.melon.com/kpopconcert'
            },
            {
                'title': '재즈 나이트',
                'group_name': '재즈클럽',
                'description': '분위기 있는 재즈 클럽에서 라이브 재즈 음악을 감상하세요. 와인과 함께하는 특별한 밤을 선사합니다.',
                'location': '이태원',
                'address': '서울특별시 용산구 이태원로 234',
                'price': '30,000원',
                'date': (datetime.now() + timedelta(days=18)).strftime('%Y-%m-%d'),
                'time': '21:00~23:00',
                'contact_email': 'jazz@club.com',
                'video_url': 'https://www.youtube.com/watch?v=example18',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': '록 페스티벌',
                'group_name': '록밴드',
                'description': '힘찬 록 음악과 함께하는 페스티벌입니다. 여러 록 밴드들의 화려한 공연을 감상하세요.',
                'location': '한강공원',
                'address': '서울특별시 영등포구 여의대로 330',
                'price': '50,000원',
                'date': (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'),
                'time': '18:00~22:00',
                'contact_email': 'rock@festival.com',
                'video_url': 'https://www.youtube.com/watch?v=example19',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/rockfestival'
            },
            {
                'title': '어쿠스틱 콘서트',
                'group_name': '어쿠스틱뮤지션',
                'description': '따뜻한 어쿠스틱 음악을 감상하세요. 기타와 보컬의 아름다운 하모니를 경험합니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 178',
                'price': '25,000원',
                'date': (datetime.now() + timedelta(days=32)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'acoustic@music.com',
                'video_url': 'https://www.youtube.com/watch?v=example20',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/acoustic'
            }
        ]
        
        # 무용(서양/한국무용) 카테고리 샘플 데이터
        dance_samples = [
            {
                'title': '발레 공연 - 백조의 호수',
                'group_name': '서울발레단',
                'description': '클래식 발레의 대표작을 서울발레단이 선보입니다. 우아하고 아름다운 춤동작을 감상하세요.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '60,000원',
                'date': (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d'),
                'time': '19:30~22:00',
                'contact_email': 'ballet@seoulballet.com',
                'video_url': 'https://www.youtube.com/watch?v=example21',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/ballet'
            },
            {
                'title': '현대무용 공연',
                'group_name': '현대무용단',
                'description': '자유롭고 창의적인 현대무용을 감상하세요. 독창적인 안무와 표현력을 선보입니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 123',
                'price': '35,000원',
                'date': (datetime.now() + timedelta(days=19)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'modern@dance.com',
                'video_url': 'https://www.youtube.com/watch?v=example22',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/moderndance'
            },
            {
                'title': '한국무용 - 승무',
                'group_name': '한국무용단',
                'description': '전통 한국무용의 아름다움을 감상하세요. 승무의 우아하고 신비로운 춤동작을 선보입니다.',
                'location': '국립국악원',
                'address': '서울특별시 서초구 남부순환로 2364',
                'price': '30,000원',
                'date': (datetime.now() + timedelta(days=26)).strftime('%Y-%m-%d'),
                'time': '19:00~20:30',
                'contact_email': 'korean@dance.com',
                'video_url': 'https://www.youtube.com/watch?v=example23',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': '탭댄스 쇼',
                'group_name': '탭댄스크루',
                'description': '화려한 탭댄스 쇼를 감상하세요. 리듬감 넘치는 발걸음과 화려한 무대를 선보입니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 200',
                'price': '25,000원',
                'date': (datetime.now() + timedelta(days=33)).strftime('%Y-%m-%d'),
                'time': '20:30~22:00',
                'contact_email': 'tap@dance.com',
                'video_url': 'https://www.youtube.com/watch?v=example24',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.melon.com/tapdance'
            }
        ]
        
        # 대중무용 카테고리 샘플 데이터
        popular_dance_samples = [
            {
                'title': '힙합 댄스 배틀',
                'group_name': '힙합크루',
                'description': '전국 힙합댄서들이 모여 실력을 겨루는 배틀 대회입니다. 치열한 경쟁과 화려한 무대를 감상하세요.',
                'location': '올림픽공원',
                'address': '서울특별시 송파구 올림픽로 25',
                'price': '20,000원',
                'date': (datetime.now() + timedelta(days=13)).strftime('%Y-%m-%d'),
                'time': '18:00~22:00',
                'contact_email': 'hiphop@battle.com',
                'video_url': 'https://www.youtube.com/watch?v=example25',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/hiphopbattle'
            },
            {
                'title': '스트릿댄스 쇼케이스',
                'group_name': '스트릿크루',
                'description': '다양한 스트릿댄스 장르를 선보이는 쇼케이스입니다. 브레이킹, 팝핑, 락킹 등 다양한 댄스 스타일을 감상하실 수 있습니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 222',
                'price': '15,000원',
                'date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
                'time': '19:00~21:00',
                'contact_email': 'street@showcase.com',
                'video_url': 'https://www.youtube.com/watch?v=example26',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': 'K-POP 댄스 커버',
                'group_name': 'K-POP댄스팀',
                'description': '인기 K-POP 곡들의 댄스를 커버하는 공연입니다. 정확한 안무와 화려한 퍼포먼스를 선보입니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 145',
                'price': '18,000원',
                'date': (datetime.now() + timedelta(days=27)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'kpop@cover.com',
                'video_url': 'https://www.youtube.com/watch?v=example27',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/kpopcover'
            },
            {
                'title': '댄스 스포츠 대회',
                'group_name': '댄스스포츠협회',
                'description': '우아하고 화려한 댄스스포츠 대회입니다. 왈츠, 탱고, 차차차 등 다양한 댄스를 감상하세요.',
                'location': '세종문화회관',
                'address': '서울특별시 종로구 세종로 81-3',
                'price': '25,000원',
                'date': (datetime.now() + timedelta(days=34)).strftime('%Y-%m-%d'),
                'time': '19:30~22:00',
                'contact_email': 'dancesport@competition.com',
                'video_url': 'https://www.youtube.com/watch?v=example28',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.melon.com/dancesport'
            }
        ]
        
        # 서커스/마술 카테고리 샘플 데이터
        circus_samples = [
            {
                'title': '서커스 쇼',
                'group_name': '서커스단',
                'description': '화려하고 신기한 서커스 쇼를 감상하세요. 곡예, 저글링, 마술 등 다양한 공연을 선보입니다.',
                'location': '올림픽공원',
                'address': '서울특별시 송파구 올림픽로 25',
                'price': '40,000원',
                'date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                'time': '19:00~21:00',
                'contact_email': 'circus@show.com',
                'video_url': 'https://www.youtube.com/watch?v=example29',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/circus'
            },
            {
                'title': '마술 쇼',
                'group_name': '마술사',
                'description': '신기하고 놀라운 마술 쇼를 감상하세요. 카드 마술, 동전 마술, 환상적인 마술을 선보입니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 167',
                'price': '30,000원',
                'date': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'magic@show.com',
                'video_url': 'https://www.youtube.com/watch?v=example30',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': '일루전 쇼',
                'group_name': '일루전마스터',
                'description': '최신 기술을 활용한 일루전 쇼를 감상하세요. 홀로그램과 특수효과로 만드는 환상적인 무대를 선보입니다.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '50,000원',
                'date': (datetime.now() + timedelta(days=28)).strftime('%Y-%m-%d'),
                'time': '19:30~21:30',
                'contact_email': 'illusion@show.com',
                'video_url': 'https://www.youtube.com/watch?v=example31',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/illusion'
            },
            {
                'title': '어린이 마술쇼',
                'group_name': '어린이마술사',
                'description': '어린이들을 위한 재미있는 마술쇼입니다. 참여형 마술과 재미있는 퍼포먼스를 선보입니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 244',
                'price': '20,000원',
                'date': (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d'),
                'time': '14:00~15:30',
                'contact_email': 'kids@magic.com',
                'video_url': 'https://www.youtube.com/watch?v=example32',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.melon.com/kidsmagic'
            }
        ]
        
        # 복합 카테고리 샘플 데이터
        mixed_samples = [
            {
                'title': '멀티미디어 공연',
                'group_name': '멀티미디어아트',
                'description': '음악, 무용, 영상, 조명이 어우러진 멀티미디어 공연입니다. 최신 기술과 예술의 만남을 경험하세요.',
                'location': '예술의전당',
                'address': '서울특별시 서초구 남부순환로 2406',
                'price': '45,000원',
                'date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'time': '20:00~22:00',
                'contact_email': 'multimedia@art.com',
                'video_url': 'https://www.youtube.com/watch?v=example33',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.interpark.com/multimedia'
            },
            {
                'title': '퍼포먼스 아트',
                'group_name': '퍼포먼스아티스트',
                'description': '현대 미술과 공연이 결합된 퍼포먼스 아트를 감상하세요. 독창적이고 실험적인 작품을 선보입니다.',
                'location': '대학로',
                'address': '서울특별시 종로구 대학로 12길 189',
                'price': '25,000원',
                'date': (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d'),
                'time': '19:30~21:00',
                'contact_email': 'performance@art.com',
                'video_url': 'https://www.youtube.com/watch?v=example34',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매'],
                'ticket_url': None
            },
            {
                'title': '뮤지컬 + 댄스',
                'group_name': '뮤지컬댄스팀',
                'description': '뮤지컬과 댄스가 결합된 특별한 공연입니다. 노래와 춤이 어우러진 화려한 무대를 선보입니다.',
                'location': '홍대',
                'address': '서울특별시 마포구 와우산로 266',
                'price': '35,000원',
                'date': (datetime.now() + timedelta(days=29)).strftime('%Y-%m-%d'),
                'time': '20:00~21:30',
                'contact_email': 'musicaldance@show.com',
                'video_url': 'https://www.youtube.com/watch?v=example35',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['현장구매', '사이트구매'],
                'ticket_url': 'https://ticket.yes24.com/musicaldance'
            },
            {
                'title': '클래식 + 재즈',
                'group_name': '클래식재즈앙상블',
                'description': '클래식과 재즈가 만나는 특별한 공연입니다. 두 장르의 아름다운 조화를 감상하세요.',
                'location': '세종문화회관',
                'address': '서울특별시 종로구 세종로 81-3',
                'price': '40,000원',
                'date': (datetime.now() + timedelta(days=36)).strftime('%Y-%m-%d'),
                'time': '19:30~21:00',
                'contact_email': 'classicjazz@ensemble.com',
                'video_url': 'https://www.youtube.com/watch?v=example36',
                'image_url': '/static/kopis_map.jpg',
                'purchase_methods': ['사이트구매'],
                'ticket_url': 'https://ticket.melon.com/classicjazz'
            }
        ]
        
        # 샘플 데이터를 카테고리별로 정리
        category_samples = {
            '연극': theater_samples,
            '뮤지컬': musical_samples,
            '서양음악(클래식)': classical_samples,
            '한국음악(국악)': gugak_samples,
            '대중음악': pop_samples,
            '무용(서양/한국무용)': dance_samples,
            '대중무용': popular_dance_samples,
            '서커스/마술': circus_samples,
            '복합': mixed_samples
        }
        
        # 데이터베이스에 저장
        created_count = 0
        for category, samples in category_samples.items():
            for i, sample in enumerate(samples):
                # 중복 확인
                existing = Performance.query.filter_by(title=sample['title']).first()
                if existing:
                    print(f"⏭️  이미 존재: {sample['title']}")
                    continue
                
                # 구매방법 JSON 변환
                purchase_methods_json = json.dumps(sample['purchase_methods'], ensure_ascii=False)
                
                # 공연 생성
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
                    is_approved=True
                )
                
                db.session.add(performance)
                created_count += 1
                print(f"✅ 생성: {sample['title']} ({category})")
        
        db.session.commit()
        print(f"\n🎉 완료! {created_count}개의 샘플 공연이 생성되었습니다.")

if __name__ == '__main__':
    try:
        create_category_samples()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 