from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, jsonify, session, g, send_file, make_response
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, text
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid
import traceback
import cloudinary
import cloudinary.uploader
import requests
import time
import xml.etree.ElementTree as ET
import json
from openpyxl import Workbook

from flask_babel import Babel

load_dotenv()

# 로깅 설정 (먼저 설정)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 카카오 OAuth 설정
KAKAO_CLIENT_ID = os.getenv('KAKAO_CLIENT_ID')
KAKAO_CLIENT_SECRET = os.getenv('KAKAO_CLIENT_SECRET')
KAKAO_REDIRECT_URI = os.getenv('KAKAO_REDIRECT_URI', 'http://localhost:10000/auth/kakao/callback')

# 카카오 OAuth 설정 검증
if not KAKAO_CLIENT_ID or KAKAO_CLIENT_ID == 'your_kakao_rest_api_key':
    logger.warning("KAKAO_CLIENT_ID not set or using placeholder value")
    KAKAO_CLIENT_ID = None

if not KAKAO_CLIENT_SECRET or KAKAO_CLIENT_SECRET == 'your_kakao_client_secret':
    logger.warning("KAKAO_CLIENT_SECRET not set or using placeholder value")
    KAKAO_CLIENT_SECRET = None

# 구글 OAuth 설정
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:10000/auth/google/callback')

# 구글 OAuth 설정 검증
if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == 'your_google_client_id':
    logger.warning("GOOGLE_CLIENT_ID not set or using placeholder value")
    # 테스트용 더미 값 설정 (실제 사용 시 제거)
    GOOGLE_CLIENT_ID = 'test_google_client_id' if os.getenv('FLASK_ENV') == 'development' else None

if not GOOGLE_CLIENT_SECRET or GOOGLE_CLIENT_SECRET == 'your_google_client_secret':
    logger.warning("GOOGLE_CLIENT_SECRET not set or using placeholder value")
    # 테스트용 더미 값 설정 (실제 사용 시 제거)
    GOOGLE_CLIENT_SECRET = 'test_google_client_secret' if os.getenv('FLASK_ENV') == 'development' else None

# KOPIS OAuth 설정
KOPIS_API_KEY = os.getenv('KOPIS_API_KEY', 'bbfe976d316347c8928fe3a2169ab8fe')

# KOPIS API 설정 검증
if not KOPIS_API_KEY or KOPIS_API_KEY == 'your_kopis_api_key':
    logger.warning("KOPIS_API_KEY not set or using placeholder value")
    KOPIS_API_KEY = 'bbfe976d316347c8928fe3a2169ab8fe'  # 기본값으로 설정

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = 'your-secret-key-here'

# 다국어 지원 설정
LANGUAGES = ['ko', 'en', 'ja', 'zh']
BABEL_DEFAULT_LOCALE = 'ko'

@app.before_request
def set_language():
    lang = session.get('lang', 'ko')
    if request.method == 'POST' and 'lang' in request.form:
        lang = request.form['lang']
        if lang not in LANGUAGES:
            lang = 'ko'
        session['lang'] = lang
    g.lang = lang

@app.route('/set_language', methods=['POST'])
def set_language_route():
    lang = request.form.get('lang', 'ko')
    if lang not in LANGUAGES:
        lang = 'ko'
    session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

# 데이터베이스 설정
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    # PostgreSQL 설정 - 더 안정적인 연결 설정
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 600,  # 300에서 600으로 증가
        'pool_timeout': 20,   # 10에서 20으로 증가
        'max_overflow': 10,   # 5에서 10으로 증가
        'pool_size': 10,      # 5에서 10으로 증가
        'connect_args': {
            'connect_timeout': 20,  # 10에서 20으로 증가
            'application_name': 'kopis-performance',
            'options': '-c statement_timeout=60000'  # 30초에서 60초로 증가
        }
    }
    logger.info(f"Using PostgreSQL: {database_url}")
else:
    # 로컬 개발용 SQLite 데이터베이스
    database_url = 'sqlite:///app.db'
    logger.info(f"Using SQLite: {database_url}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy 초기화
db = SQLAlchemy()
db.init_app(app)

# Flask-Login 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User 모델
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())

    def get_id(self):
        return str(self.id)

# Performance 모델
class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    group_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    address = db.Column(db.String(200))  # 상세 주소 (지도용)
    price = db.Column(db.String(50))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    video_url = db.Column(db.String(300))
    image_url = db.Column(db.String(300))
    main_category = db.Column(db.String(20))  # 메인 카테고리 (공연/대회)
    category = db.Column(db.String(50))  # 세부 카테고리
    ticket_url = db.Column(db.String(300))  # 티켓 예매 링크
    booking_phone = db.Column(db.String(50))  # 예매 전화번호
    booking_website = db.Column(db.String(300))  # 예매 웹사이트
    likes = db.Column(db.Integer, default=0)  # 좋아요 수
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    purchase_methods = db.Column(db.String(100), default='["현장구매"]')  # 구매방법 (JSON 문자열)
    
    # KOPIS 연동 필드
    kopis_id = db.Column(db.String(50))  # KOPIS 고유 ID
    kopis_venue_id = db.Column(db.String(50))  # KOPIS 공연장 ID
    kopis_synced_at = db.Column(db.DateTime)  # KOPIS 동기화 시간

    user = db.relationship('User', backref='performances')
    
    @property
    def kopis_url(self):
        """KOPIS 공연 페이지 URL"""
        return generate_kopis_url(self.kopis_id)
    
    @property
    def is_kopis_synced(self):
        """KOPIS에서 동기화된 공연인지 확인"""
        return bool(self.kopis_id and self.kopis_synced_at)

# 사용자별 좋아요 정보
class UserLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    performance_id = db.Column(db.Integer, db.ForeignKey('performance.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # 중복 좋아요 방지
    __table_args__ = (db.UniqueConstraint('user_id', 'performance_id', name='unique_user_performance_like'),)

# 댓글 모델
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 별점 (1-5)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    performance_id = db.Column(db.Integer, db.ForeignKey('performance.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship('User', backref='comments')
    performance = db.relationship('Performance', backref='comments')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 템플릿 필터 추가
@app.template_filter('nl2br')
def nl2br_filter(text):
    """줄바꿈을 <br> 태그로 변환"""
    if text:
        return text.replace('\n', '<br>')
    return text

@app.template_filter('loads')
def loads_filter(s):
    import json
    return json.loads(s) if s else []

class KopisAPIClient:
    """KOPIS API 클라이언트"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://www.kopis.or.kr/openApi/restful"
        self.logger = logging.getLogger(__name__)
    
    def get_performances(self, start_date=None, end_date=None, page=1, rows=100):
        """공연 목록 조회"""
        try:
            # 기본값 설정
            if not start_date:
                start_date = datetime.now().strftime('%Y%m%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=30)).strftime('%Y%m%d')
            
            params = {
                'service': self.api_key,
                'stdate': start_date,
                'eddate': end_date,
                'cpage': page,
                'rows': rows,
                'prfstate': '02'  # 공연예정
            }
            
            response = requests.get(f"{self.base_url}/pblprfr", params=params)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            performances = []
            
            for db in root.findall('.//db'):
                performance = {
                    'mt20id': self._get_text(db, 'mt20id'),
                    'prfnm': self._get_text(db, 'prfnm'),
                    'prfpdfrom': self._get_text(db, 'prfpdfrom'),
                    'prfpdto': self._get_text(db, 'prfpdto'),
                    'fcltynm': self._get_text(db, 'fcltynm'),
                    'poster': self._get_text(db, 'poster'),
                    'genrenm': self._get_text(db, 'genrenm'),
                    'prfstate': self._get_text(db, 'prfstate'),
                    'openrun': self._get_text(db, 'openrun')
                }
                performances.append(performance)
            
            return performances
            
        except Exception as e:
            self.logger.error(f"Error fetching performances: {e}")
            return []
    
    def get_performance_detail(self, mt20id):
        """공연 상세 정보 조회"""
        try:
            params = {
                'service': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/pblprfr/{mt20id}", params=params)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            db = root.find('.//db')
            
            if db is not None:
                detail = {
                    'mt20id': self._get_text(db, 'mt20id'),
                    'mt10id': self._get_text(db, 'mt10id'),
                    'prfnm': self._get_text(db, 'prfnm'),
                    'prfpdfrom': self._get_text(db, 'prfpdfrom'),
                    'prfpdto': self._get_text(db, 'prfpdto'),
                    'fcltynm': self._get_text(db, 'fcltynm'),
                    'prfcast': self._get_text(db, 'prfcast'),
                    'prfcrew': self._get_text(db, 'prfcrew'),
                    'prfruntime': self._get_text(db, 'prfruntime'),
                    'prfage': self._get_text(db, 'prfage'),
                    'entrpsnm': self._get_text(db, 'entrpsnm'),
                    'pcseguidance': self._get_text(db, 'pcseguidance'),
                    'poster': self._get_text(db, 'poster'),
                    'story': self._get_text(db, 'story'),
                    'genrenm': self._get_text(db, 'genrenm'),
                    'prfstate': self._get_text(db, 'prfstate'),
                    'openrun': self._get_text(db, 'openrun'),
                    'dtguidance': self._get_text(db, 'dtguidance'),
                    'styurls': [url.text for url in db.findall('.//styurl')]
                }
                return detail
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching performance detail: {e}")
            return None
    
    def _get_text(self, element, tag):
        """XML 요소에서 텍스트 추출"""
        found = element.find(tag)
        return found.text if found is not None else ''

def map_kopis_to_performance(kopis_data):
    """KOPIS 데이터를 내부 Performance 모델로 매핑"""
    
    # 장르 매핑
    genre_mapping = {
        '연극': '연극',
        '뮤지컬': '뮤지컬',
        '클래식': '서양음악(클래식)',
        '국악': '한국음악(국악)',
        '대중음악': '대중음악',
        '무용': '무용(서양/한국무용)',
        '대중무용': '대중무용',
        '서커스/마술': '서커스/마술',
        '복합': '복합'
    }
    
    # 날짜 형식 변환
    try:
        start_date = datetime.strptime(kopis_data['prfpdfrom'], '%Y.%m.%d').strftime('%Y-%m-%d')
        end_date = datetime.strptime(kopis_data['prfpdto'], '%Y.%m.%d').strftime('%Y-%m-%d')
        date_range = f"{start_date} ~ {end_date}"
    except:
        date_range = f"{kopis_data.get('prfpdfrom', '')} ~ {kopis_data.get('prfpdto', '')}"
    
    # 장르 분류
    genre = kopis_data.get('genrenm', '')
    mapped_genre = genre_mapping.get(genre, '복합')
    
    # 메인 카테고리 결정
    main_category = '공연'  # 기본값
    
    performance = {
        'title': kopis_data.get('prfnm', ''),
        'group_name': kopis_data.get('entrpsnm', ''),
        'description': kopis_data.get('story', ''),
        'location': kopis_data.get('fcltynm', ''),
        'address': '',  # KOPIS에서 제공하지 않음
        'price': '가격 정보 없음',  # KOPIS에서 제공하지 않음
        'date': date_range,
        'time': kopis_data.get('dtguidance', ''),
        'contact_email': '',  # KOPIS에서 제공하지 않음
        'video_url': '',  # KOPIS에서 제공하지 않음
        'image_url': kopis_data.get('poster', ''),
        'main_category': main_category,
        'category': mapped_genre,
        'ticket_url': '',  # KOPIS에서 제공하지 않음
        'is_approved': True,  # KOPIS 데이터는 자동 승인
        'kopis_id': kopis_data.get('mt20id', ''),  # KOPIS 고유 ID 저장
        'kopis_venue_id': kopis_data.get('mt10id', ''),  # KOPIS 공연장 ID
        'kopis_synced_at': datetime.now()
    }
    
    return performance

def detect_region_from_address(address):
    """주소에서 지역을 자동으로 감지하는 함수"""
    if not address:
        return None
    
    address_lower = address.lower()
    
    # 지역 매핑 - 더 정확한 매칭을 위해 우선순위와 키워드 개선
    region_mapping = {
        '서울특별시': ['서울특별시', '서울시', '서울', '서울특별', '서울시청', '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'],
        '경기도': ['경기도', '경기', '수원시', '성남시', '의정부시', '안양시', '부천시', '광명시', '평택시', '동두천시', '안산시', '고양시', '과천시', '구리시', '남양주시', '오산시', '시흥시', '군포시', '의왕시', '하남시', '용인시', '파주시', '이천시', '안성시', '김포시', '화성시', '광주시', '여주시', '양평군', '고양군', '연천군', '포천군', '가평군'],
        '강원도': ['강원도', '강원', '춘천시', '원주시', '강릉시', '동해시', '태백시', '속초시', '삼척시', '홍천군', '횡성군', '영월군', '평창군', '정선군', '철원군', '화천군', '양구군', '인제군', '고성군', '양양군'],
        '인천광역시': ['인천광역시', '인천시', '인천', '중구', '동구', '미추홀구', '연수구', '남동구', '부평구', '계양구', '서구', '강화군', '옹진군'],
        '충청남도': ['충청남도', '충남', '천안시', '공주시', '보령시', '아산시', '서산시', '논산시', '계룡시', '당진시', '금산군', '부여군', '서천군', '청양군', '홍성군', '예산군', '태안군'],
        '충청북도': ['충청북도', '충북', '청주시', '충주시', '제천시', '보은군', '옥천군', '영동군', '증평군', '진천군', '괴산군', '음성군', '단양군'],
        '세종특별자치시': ['세종특별자치시', '세종시', '세종', '세종특별자치'],
        '대전광역시': ['대전광역시', '대전시', '대전', '동구', '중구', '서구', '유성구', '대덕구'],
        '경상북도': ['경상북도', '경북', '포항시', '경주시', '김천시', '안동시', '구미시', '영주시', '영천시', '상주시', '문경시', '경산시', '군위군', '의성군', '청송군', '영양군', '영덕군', '청도군', '고령군', '성주군', '칠곡군', '예천군', '봉화군', '울진군', '울릉군'],
        '대구광역시': ['대구광역시', '대구시', '대구', '중구', '동구', '서구', '남구', '북구', '수성구', '달서구', '달성군'],
        '전라북도': ['전라북도', '전북', '전주시', '군산시', '익산시', '정읍시', '남원시', '김제시', '완주군', '진안군', '무주군', '장수군', '임실군', '순창군', '고창군', '부안군'],
        '경상남도': ['경상남도', '경남', '창원시', '진주시', '통영시', '사천시', '김해시', '밀양시', '거제시', '양산시', '의령군', '함안군', '창녕군', '고성군', '남해군', '하동군', '산청군', '함양군', '거창군', '합천군'],
        '울산광역시': ['울산광역시', '울산시', '울산', '중구', '남구', '동구', '북구', '울주군'],
        '부산광역시': ['부산광역시', '부산시', '부산', '중구', '서구', '동구', '영도구', '부산진구', '동래구', '남구', '북구', '해운대구', '사하구', '금정구', '강서구', '연제구', '수영구', '사상구', '기장군'],
        '광주광역시': ['광주광역시', '광주시', '광주', '동구', '서구', '남구', '북구', '광산구'],
        '전라남도': ['전라남도', '전남', '목포시', '여수시', '순천시', '나주시', '광양시', '담양군', '곡성군', '구례군', '고흥군', '보성군', '화순군', '장흥군', '강진군', '해남군', '영암군', '무안군', '함평군', '영광군', '장성군', '완도군', '진도군', '신안군'],
        '제주도': ['제주도', '제주특별자치도', '제주시', '제주', '제주특별자치', '서귀포시']
    }
    
    # 정확한 매칭을 위해 더 긴 키워드부터 검사
    for region, keywords in region_mapping.items():
        for keyword in sorted(keywords, key=len, reverse=True):
            if keyword in address_lower:
                logger.debug(f"Address '{address}' matched region '{region}' with keyword '{keyword}'")
                return region
    
    logger.debug(f"Address '{address}' could not be matched to any region")
    return None

def create_tables():
    """데이터베이스 테이블 생성 (무한 루프 방지)"""
    try:
        with app.app_context():
            logger.info("Checking database schema...")
            
            # 기존 테이블 확인
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='performance'"))
            if result.fetchone():
                # 기존 테이블이 있으면 컬럼 확인
                result = db.session.execute(text("PRAGMA table_info(performance)"))
                columns = [row[1] for row in result.fetchall()]
                
                # booking_phone 컬럼이 없으면 스킵
                if 'booking_phone' not in columns:
                    logger.warning("Database schema mismatch detected. Skipping initialization to prevent infinite loop.")
                    return False
            
            # 테이블 생성
            db.create_all()
            logger.info("Database tables created successfully!")
            return True
                
    except Exception as e:
        logger.error(f"Database creation failed: {e}")
        logger.warning("Continuing without database initialization to prevent infinite loop.")
        return False

def create_sample_data_if_needed():
    try:
        with app.app_context():
            from datetime import datetime, timedelta
            # 사용자 샘플 생성 (기존과 동일)
            if User.query.count() == 0:
                sample_users = [
                    {
                        'name': '관리자',
                        'username': 'admin',
                        'email': 'admin@admin.com',
                        'phone': '010-0000-0000',
                        'password': 'admin123',
                        'is_admin': True
                    },
                    {
                        'name': '김댄서',
                        'username': 'dancer1',
                        'email': 'dancer1@test.com',
                        'phone': '010-1111-1111',
                        'password': 'test123',
                        'is_admin': False
                    },
                    {
                        'name': '이크루',
                        'username': 'crew2',
                        'email': 'crew2@test.com',
                        'phone': '010-2222-2222',
                        'password': 'test123',
                        'is_admin': False
                    },
                    {
                        'name': '박스트릿',
                        'username': 'street3',
                        'email': 'street3@test.com',
                        'phone': '010-3333-3333',
                        'password': 'test123',
                        'is_admin': False
                    }
                ]
                created_users = []
                for user_data in sample_users:
                    user = User(
                        name=user_data['name'],
                        username=user_data['username'],
                        email=user_data['email'],
                        phone=user_data['phone'],
                        password_hash=generate_password_hash(user_data['password']),
                        is_admin=user_data['is_admin']
                    )
                    db.session.add(user)
                    created_users.append(user)
                db.session.commit()
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            return
        # 카테고리별 샘플 공연 데이터
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
                    'ticket_url': 'https://ticket.interpark.com/example1',
                    'booking_phone': '02-1234-5678',
                    'booking_website': 'https://booking.naver.com/example1',
                    'main_category': '공연',
                    'category': '연극',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["사이트구매", "전화구매"]'
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
                    'ticket_url': 'https://ticket.yes24.com/example2',
                    'booking_phone': '02-2345-6789',
                    'booking_website': 'https://booking.naver.com/example2',
                    'main_category': '공연',
                    'category': '연극',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["사이트구매", "전화구매"]'
                },
                {
                    'title': '오이디푸스',
                    'group_name': '고전극단',
                    'description': '고대 그리스 비극의 대표작을 현대적으로 재해석.',
                    'location': '국립극장',
                    'address': '서울특별시 중구 장충단로 59',
                    'price': '40,000원',
                    'date': '2024-12-22',
                    'time': '18:00',
                    'contact_email': 'oedipus@classic.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '연극',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '갈매기',
                    'group_name': '체홉극단',
                    'description': '러시아 문학의 거장 체홉의 대표작.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '35,000원',
                    'date': '2024-12-28',
                    'time': '17:00',
                    'contact_email': 'seagull@chekhov.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '연극',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
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
                    'ticket_url': 'https://ticket.interpark.com/example3',
                    'main_category': '공연',
                    'category': '뮤지컬',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
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
                    'ticket_url': 'https://ticket.interpark.com/example4',
                    'main_category': '공연',
                    'category': '뮤지컬',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '위키드',
                    'group_name': '그린위치',
                    'description': '마법의 세계를 그린 환상적인 뮤지컬.',
                    'location': '블루스퀘어',
                    'address': '서울특별시 용산구 이태원로 294',
                    'price': '100,000원',
                    'date': '2025-01-05',
                    'time': '20:00',
                    'contact_email': 'wicked@musical.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '뮤지컬',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '맘마미아!',
                    'group_name': 'ABBA뮤지컬',
                    'description': 'ABBA의 명곡으로 꾸며진 신나는 뮤지컬.',
                    'location': 'LG아트센터',
                    'address': '서울특별시 강남구 논현로 508',
                    'price': '85,000원',
                    'date': '2025-01-10',
                    'time': '19:30',
                    'contact_email': 'mamma@musical.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '뮤지컬',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '서양음악(클래식)': [
                {
                    'title': '클래식 스타 콘서트',
                    'group_name': '서울필하모닉',
                    'description': '세계적인 클래식 스타들이 함께하는 콘서트.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '70,000원',
                    'date': '2025-01-12',
                    'time': '19:00',
                    'contact_email': 'classicstar@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '서양음악(클래식)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
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
                    'ticket_url': 'https://ticket.interpark.com/example8',
                    'main_category': '공연',
                    'category': '클래식',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '쇼팽 피아노 리사이틀',
                    'group_name': '쇼팽스페셜',
                    'description': '쇼팽의 명곡을 감상할 수 있는 피아노 리사이틀.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '55,000원',
                    'date': '2025-01-03',
                    'time': '20:00',
                    'contact_email': 'chopin@recital.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '클래식',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '비발디 사계',
                    'group_name': '바로크앙상블',
                    'description': '비발디의 사계를 연주하는 바로크 음악회.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '45,000원',
                    'date': '2025-01-08',
                    'time': '19:30',
                    'contact_email': 'vivaldi@baroque.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '클래식',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '한국음악(국악)': [
                {
                    'title': '국악 한마당',
                    'group_name': '국립국악원',
                    'description': '전통 국악의 진수를 느낄 수 있는 무대.',
                    'location': '국립국악원',
                    'address': '서울특별시 서초구 남부순환로 2364',
                    'price': '30,000원',
                    'date': '2025-01-15',
                    'time': '19:30',
                    'contact_email': 'gugak@korea.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '한국음악(국악)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '명주 콘서트',
                    'group_name': '국악단',
                    'description': '명주의 아름다움을 느낄 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '40,000원',
                    'date': '2025-01-20',
                    'time': '19:00',
                    'contact_email': 'gugak@korea.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '한국음악(국악)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '현대국악 페스티벌',
                    'group_name': '현대국악단',
                    'description': '현대 국악의 다양성을 보여주는 페스티벌.',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '50,000원',
                    'date': '2025-01-25',
                    'time': '19:30',
                    'contact_email': 'gugak@korea.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '한국음악(국악)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '국악 예술 콘서트',
                    'group_name': '국악단',
                    'description': '국악의 예술성을 느낄 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '45,000원',
                    'date': '2025-01-30',
                    'time': '19:30',
                    'contact_email': 'gugak@korea.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '한국음악(국악)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '대중음악': [
                {
                    'title': 'K-POP 페스티벌',
                    'group_name': 'K-POP스타즈',
                    'description': '최고의 K-POP 아티스트들이 한자리에!',
                    'location': '올림픽공원',
                    'address': '서울특별시 송파구 올림픽로 424',
                    'price': '120,000원',
                    'date': '2025-02-01',
                    'time': '18:00',
                    'contact_email': 'kpop@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중음악',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '대중음악 콘서트',
                    'group_name': '대중음악단',
                    'description': '다양한 장르의 대중음악을 함께 즐길 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '60,000원',
                    'date': '2025-02-05',
                    'time': '19:30',
                    'contact_email': 'popularmusic@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중음악',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '대중음악 페스티벌',
                    'group_name': '댄스유나이티드',
                    'description': '다양한 장르의 대중무용을 한자리에서!',
                    'location': '코엑스',
                    'address': '서울특별시 강남구 영동대로 513',
                    'price': '무료',
                    'date': '2025-02-15',
                    'time': '17:00',
                    'contact_email': 'popdance@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중음악',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '대중음악 예술 콘서트',
                    'group_name': '대중음악단',
                    'description': '다양한 장르의 대중음악을 예술적으로 감상할 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '70,000원',
                    'date': '2025-02-10',
                    'time': '19:30',
                    'contact_email': 'popularmusic@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중음악',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '무용(서양/한국무용)': [
                {
                    'title': '현대무용 갈라',
                    'group_name': '서울무용단',
                    'description': '현대무용의 아름다움을 느낄 수 있는 갈라 공연.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '40,000원',
                    'date': '2025-02-10',
                    'time': '19:30',
                    'contact_email': 'dance@modern.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '무용(서양/한국무용)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '한국무용 콘서트',
                    'group_name': '한국무용단',
                    'description': '한국무용의 아름다움을 느낄 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '50,000원',
                    'date': '2025-02-15',
                    'time': '19:30',
                    'contact_email': 'koreandance@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '무용(서양/한국무용)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '무용 페스티벌',
                    'group_name': '무용단',
                    'description': '다양한 장르의 무용을 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '60,000원',
                    'date': '2025-02-20',
                    'time': '19:00',
                    'contact_email': 'dancefestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '무용(서양/한국무용)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '무용 예술 콘서트',
                    'group_name': '무용단',
                    'description': '무용의 예술성을 느낄 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '70,000원',
                    'date': '2025-02-25',
                    'time': '19:30',
                    'contact_email': 'danceconcert@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '무용(서양/한국무용)',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '대중무용': [
                {
                    'title': '스트릿댄스 페스티벌',
                    'group_name': '댄스유나이티드',
                    'description': '다양한 장르의 대중무용을 한자리에서!',
                    'location': '코엑스',
                    'address': '서울특별시 강남구 영동대로 513',
                    'price': '무료',
                    'date': '2025-02-15',
                    'time': '17:00',
                    'contact_email': 'popdance@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중무용',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '댄스 페스티벌',
                    'group_name': '댄스유나이티드',
                    'description': '다양한 장르의 댄스를 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '80,000원',
                    'date': '2025-02-20',
                    'time': '19:00',
                    'contact_email': 'dancefestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중무용',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '대중무용 예술 콘서트',
                    'group_name': '댄스유나이티드',
                    'description': '다양한 장르의 댄스를 예술적으로 감상할 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '90,000원',
                    'date': '2025-02-25',
                    'time': '19:30',
                    'contact_email': 'danceconcert@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중무용',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '대중무용 페스티벌',
                    'group_name': '댄스유나이티드',
                    'description': '다양한 장르의 댄스를 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '100,000원',
                    'date': '2025-03-01',
                    'time': '18:00',
                    'contact_email': 'dancefestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '대중무용',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '서커스/마술': [
                {
                    'title': '매직 서커스',
                    'group_name': '월드매직팀',
                    'description': '세계 최고의 마술사와 서커스 아티스트가 함께하는 무대.',
                    'location': '잠실실내체육관',
                    'address': '서울특별시 송파구 올림픽로 25',
                    'price': '60,000원',
                    'date': '2025-02-20',
                    'time': '19:00',
                    'contact_email': 'magic@circus.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '서커스/마술',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '마술 페스티벌',
                    'group_name': '마술단',
                    'description': '다양한 장르의 마술을 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '70,000원',
                    'date': '2025-02-25',
                    'time': '19:00',
                    'contact_email': 'magicfestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '서커스/마술',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '서커스 예술 콘서트',
                    'group_name': '서커스단',
                    'description': '서커스의 예술성을 느낄 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '80,000원',
                    'date': '2025-03-01',
                    'time': '19:30',
                    'contact_email': 'circusconcert@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '서커스/마술',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '서커스 페스티벌',
                    'group_name': '서커스단',
                    'description': '다양한 장르의 서커스를 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '90,000원',
                    'date': '2025-03-05',
                    'time': '18:00',
                    'contact_email': 'circusfestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '서커스/마술',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
            '복합': [
                {
                    'title': '퓨전 아트쇼',
                    'group_name': '아트퓨전팀',
                    'description': '여러 장르가 융합된 새로운 형태의 공연.',
                    'location': '블루스퀘어',
                    'address': '서울특별시 용산구 이태원로 294',
                    'price': '55,000원',
                    'date': '2025-02-25',
                    'time': '20:00',
                    'contact_email': 'fusion@artshow.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '복합',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '복합 페스티벌',
                    'group_name': '복합단',
                    'description': '다양한 장르의 공연을 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '100,000원',
                    'date': '2025-03-10',
                    'time': '19:00',
                    'contact_email': 'complexfestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '복합',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '복합 예술 콘서트',
                    'group_name': '복합단',
                    'description': '다양한 장르의 공연을 예술적으로 감상할 수 있는 콘서트.',
                    'location': '세종문화회관',
                    'address': '서울특별시 종로구 세종로 81-3',
                    'price': '110,000원',
                    'date': '2025-03-15',
                    'time': '19:30',
                    'contact_email': 'complexconcert@concert.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '복합',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                },
                {
                    'title': '복합 페스티벌',
                    'group_name': '복합단',
                    'description': '다양한 장르의 공연을 한자리에서!',
                    'location': '예술의전당',
                    'address': '서울특별시 서초구 남부순환로 2406',
                    'price': '120,000원',
                    'date': '2025-03-20',
                    'time': '18:00',
                    'contact_email': 'complexfestival@festival.com',
                    'video_url': '',
                    'ticket_url': '',
                    'main_category': '공연',
                    'category': '복합',
                    'image_url': '/static/kopis_map.jpg',
                    'purchase_methods': '["현장구매"]'
                }
            ],
        }
        for category, performances in categories.items():
            # 각 카테고리별 4개 공연 중 앞 2개는 사이트구매, 뒤 2개는 현장구매로 설정
            for i, perf_data in enumerate(performances):
                perf_data = perf_data.copy()  # 원본 변형 방지
                if i < 2:
                    perf_data['purchase_methods'] = '["사이트구매"]'
                    perf_data['ticket_url'] = perf_data['ticket_url'] or f"https://tickets.example.com/{category}_{i+1}"
                else:
                    perf_data['purchase_methods'] = '["현장구매"]'
                    perf_data['ticket_url'] = ''
                # 이미 해당 제목의 공연이 있으면 건너뜀
                if Performance.query.filter_by(title=perf_data['title']).first():
                    continue
                performance = Performance(
                    title=perf_data['title'],
                    group_name=perf_data['group_name'],
                    description=perf_data['description'],
                    location=perf_data['location'],
                    address=perf_data['address'],
                    price=perf_data['price'],
                    date=perf_data['date'],
                    time=perf_data['time'],
                    contact_email=perf_data['contact_email'],
                    video_url=perf_data['video_url'],
                    image_url=perf_data['image_url'],
                    main_category=perf_data['main_category'],
                    category=perf_data['category'],
                    ticket_url=perf_data['ticket_url'],
                    booking_phone=perf_data.get('booking_phone', ''),
                    booking_website=perf_data.get('booking_website', ''),
                    user_id=admin_user.id,
                    is_approved=True,
                    purchase_methods=perf_data['purchase_methods']
                )
                db.session.add(performance)
        db.session.commit()
        logger.info('✅ 카테고리별 샘플 공연 데이터 생성 완료!')
    except Exception as e:
        logger.error(f"Sample data creation failed: {e}")
        logger.warning("Continuing without sample data initialization.")

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# 기본 라우트들
@app.route('/')
def home():
    """홈페이지 - 승인된 공연 목록"""
    try:
        # 사용자 이벤트 추적 (로그인한 사용자만)
        if current_user.is_authenticated:
            track_user_event(
                user_id=current_user.id,
                event_type='view',
                metadata={'page': 'home'}
            )
        
        # 필터 파라미터 받기
        category_filter = request.args.get('category_filter', '전체기간')
        
        # 기본 쿼리 (승인된 공연만)
        query = Performance.query.filter_by(is_approved=True)
        
        # 카테고리 필터 적용
        if category_filter and category_filter != '전체기간':
            if category_filter == '이번주':
                # 이번 주 공연 필터링
                today = datetime.now().date()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                query = query.filter(Performance.date >= week_start, Performance.date <= week_end)
            elif category_filter == '이번달':
                # 이번 달 공연 필터링
                today = datetime.now().date()
                month_start = today.replace(day=1)
                if today.month == 12:
                    month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                query = query.filter(Performance.date >= month_start, Performance.date <= month_end)
            elif category_filter == '다음달':
                # 다음 달 공연 필터링
                today = datetime.now().date()
                if today.month == 12:
                    next_month_start = today.replace(year=today.year + 1, month=1, day=1)
                    next_month_end = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
                else:
                    next_month_start = today.replace(month=today.month + 1, day=1)
                    if today.month == 11:
                        next_month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        next_month_end = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
                query = query.filter(Performance.date >= next_month_start, Performance.date <= next_month_end)
            else:
                # 일반 카테고리 필터링
                query = query.filter_by(category=category_filter)
        
        # 최신순으로 정렬
        performances = query.order_by(Performance.created_at.desc()).all()
        
        # 템플릿 렌더링
        response = make_response(render_template("index.html", 
                             performances=performances, 
                             selected_category=category_filter))
        
        # 캐시 무효화 헤더 추가
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"홈페이지 오류: {e}")
        flash('홈페이지를 불러오는 중 오류가 발생했습니다.', 'error')
        return render_template("index.html", performances=[], selected_category='전체기간')

@app.route('/home')
def home_redirect():
    """홈페이지 리다이렉트 - 렌더 배포용"""
    return redirect(url_for('home'))

@app.route('/ping')
def ping():
    """간단한 핑 엔드포인트 - 렌더 헬스체크용"""
    return jsonify({'status': 'ok', 'message': 'pong'}), 200

def create_fallback_html(performances):
    """템플릿 렌더링 실패 시 기본 HTML 생성"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KOPIS 공연 홍보 플랫폼</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .performance-card {{ border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .performance-title {{ font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px; }}
            .performance-info {{ color: #666; margin: 5px 0; }}
            .performance-image {{ max-width: 200px; max-height: 150px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-music me-2"></i>KOPIS 공연 홍보 플랫폼
                </a>
            </div>
        </nav>
        
        <div class="container my-5">
            <div class="row">
                <div class="col-12">
                    <h1 class="text-center mb-4">
                        <i class="fas fa-music me-2"></i>공연 정보
                    </h1>
                    <p class="text-center text-muted mb-4">총 {len(performances)}개의 공연이 있습니다.</p>
                </div>
            </div>
    """
    
    for performance in performances:
        html_content += f"""
            <div class="performance-card">
                <div class="row">
                    <div class="col-md-3">
        """
        if performance.image_url:
            html_content += f'<img src="{performance.image_url}" alt="{performance.title}" class="performance-image img-fluid">'
        else:
            html_content += '<div class="bg-light d-flex align-items-center justify-content-center" style="height: 150px;"><i class="fas fa-music fa-3x text-muted"></i></div>'
        
        html_content += f"""
                    </div>
                    <div class="col-md-9">
                        <div class="performance-title">{performance.title}</div>
                        <div class="performance-info"><i class="fas fa-users me-2"></i>그룹: {performance.group_name}</div>
                        <div class="performance-info"><i class="fas fa-map-marker-alt me-2"></i>장소: {performance.location}</div>
                        <div class="performance-info"><i class="fas fa-calendar me-2"></i>날짜: {performance.date}</div>
                        <div class="performance-info"><i class="fas fa-clock me-2"></i>시간: {performance.time}</div>
                        <div class="performance-info"><i class="fas fa-ticket-alt me-2"></i>가격: {performance.price}</div>
                        <div class="performance-info"><i class="fas fa-align-left me-2"></i>설명: {performance.description[:100]}{'...' if len(performance.description) > 100 else ''}</div>
                    </div>
                </div>
            </div>
        """
    
    html_content += """
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html_content

def create_error_page(title, message):
    """에러 페이지 생성"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KOPIS 공연 홍보 플랫폼 - 오류</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-music me-2"></i>KOPIS 공연 홍보 플랫폼
                </a>
            </div>
        </nav>
        
        <div class="container my-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <i class="fas fa-exclamation-triangle fa-4x text-warning mb-4"></i>
                    <h2>{title}</h2>
                    <p class="text-muted">{message}</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-redo me-2"></i>새로고침
                    </button>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html_content

@app.route('/test')
def test_page():
    """테스트 페이지"""
    return "Flask 애플리케이션이 정상 작동 중입니다!"

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트 - 렌더 배포용"""
    try:
        # 매우 간단한 데이터베이스 연결 테스트 (타임아웃 최소화)
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        # 데이터베이스 오류가 있어도 서버는 정상이므로 200 반환
        logger.warning(f"Health check database warning: {e}")
        return jsonify({
            'status': 'healthy',
            'database': 'warning',
            'message': 'Database connection issue, but server is running',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 사용자 찾기
        user = User.query.filter_by(username=username).first()
        
        if user:
            # 비밀번호 확인
            is_password_correct = check_password_hash(user.password_hash, password)
            
            if is_password_correct:
                login_user(user)
                flash('로그인되었습니다!', 'success')
                return redirect(url_for('home'))
            else:
                flash('사용자명 또는 비밀번호가 올바르지 않습니다.', 'error')
        else:
            flash('사용자명 또는 비밀번호가 올바르지 않습니다.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입"""
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        phone = request.form.get('phone', '')
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 유효성 검사
        if password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return render_template('register.html')
        
        # 아이디 중복 확인
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 사용 중인 아이디입니다.', 'error')
            return render_template('register.html')
        
        # 이메일 중복 확인
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('이미 사용 중인 이메일입니다.', 'error')
            return render_template('register.html')
        
        # 새 사용자 생성
        password_hash = generate_password_hash(password)
        new_user = User(
            name=name,
            username=username,
            email=email,
            phone=phone,
            password_hash=password_hash
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다! 로그인해주세요.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """로그아웃"""
    logout_user()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
def admin_panel():
    """관리자 패널 - 승인 대기 중인 공연 관리 및 데이터 분석"""
    # 관리자 권한 확인
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    try:
        # 필터 파라미터 받기
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_filter = request.args.get('category_filter')
        
        # 기본 쿼리
        pending_query = Performance.query.filter_by(is_approved=False)
        approved_query = Performance.query.filter_by(is_approved=True)
        
        # 날짜 필터 적용
        if start_date:
            pending_query = pending_query.filter(Performance.date >= start_date)
            approved_query = approved_query.filter(Performance.date >= start_date)
        
        if end_date:
            pending_query = pending_query.filter(Performance.date <= end_date)
            approved_query = approved_query.filter(Performance.date <= end_date)
        
        # 카테고리 필터 적용
        if category_filter:
            pending_query = pending_query.filter_by(category=category_filter)
            approved_query = approved_query.filter_by(category=category_filter)
        
        # 필터링된 결과 가져오기
        pending_performances = pending_query.all()
        approved_performances = approved_query.all()
        
        # 필터링된 통계 계산
        filtered_pending_count = len(pending_performances)
        filtered_approved_count = len(approved_performances)
        filtered_rejected_count = 0  # 거절된 공연은 DB에서 삭제되므로 0
        filtered_total_count = filtered_pending_count + filtered_approved_count + filtered_rejected_count
        
        # 차트 데이터 생성 (필터 적용)
        monthly_chart_data = get_monthly_chart_data(start_date, end_date, category_filter)
        category_chart_data = get_category_chart_data(start_date, end_date, category_filter)
        
        # 데이터 분석 데이터 가져오기
        real_time_stats = get_real_time_stats()
        audience_analysis = get_audience_analysis()
        trend_prediction = get_trend_prediction()
        performance_stats = get_performance_statistics()
        category_trends = get_category_trends()
        
        # 템플릿 렌더링
        response = make_response(render_template("admin.html", 
                             pending_performances=pending_performances,
                             approved_performances=approved_performances,
                             filtered_pending_count=filtered_pending_count,
                             filtered_approved_count=filtered_approved_count,
                             filtered_rejected_count=filtered_rejected_count,
                             filtered_total_count=filtered_total_count,
                             monthly_chart_data=monthly_chart_data,
                             category_chart_data=category_chart_data,
                             real_time_stats=real_time_stats,
                             audience_analysis=audience_analysis,
                             trend_prediction=trend_prediction,
                             performance_stats=performance_stats,
                             category_trends=category_trends))
        
        # 캐시 무효화 헤더 추가
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"관리자 패널 오류: {e}")
        flash('관리자 패널을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('home'))

def get_monthly_chart_data(start_date=None, end_date=None, category_filter=None):
    """월별 공연 등록 차트 데이터 (필터 적용)"""
    from datetime import datetime, timedelta
    import calendar
    
    # 최근 12개월 데이터
    months = []
    data = []
    
    for i in range(11, -1, -1):
        date = datetime.now() - timedelta(days=30*i)
        year = date.year
        month = date.month
        
        # 해당 월의 시작일과 종료일
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 기본 쿼리
        query = Performance.query
        
        # 필터 적용
        if start_date:
            query = query.filter(Performance.date >= start_date)
        if end_date:
            query = query.filter(Performance.date <= end_date)
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        # 해당 월의 공연 수 (공연일 기준)
        count = query.filter(
            Performance.date >= month_start.strftime('%Y-%m-%d'),
            Performance.date <= month_end.strftime('%Y-%m-%d')
        ).count()
        
        months.append(f"{year}-{month:02d}")
        data.append(count)
    
    return {
        'labels': months,
        'data': data
    }

def get_category_chart_data(start_date=None, end_date=None, category_filter=None):
    """카테고리별 공연 차트 데이터 (필터 적용)"""
    categories = ['연극', '뮤지컬', '서양음악(클래식)', '한국음악(국악)', 
                 '대중음악', '무용(서양/한국무용)', '대중무용', '서커스/마술', '복합']
    
    data = []
    for category in categories:
        # 기본 쿼리
        query = Performance.query.filter_by(category=category)
        
        # 필터 적용
        if start_date:
            query = query.filter(Performance.date >= start_date)
        if end_date:
            query = query.filter(Performance.date <= end_date)
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        count = query.count()
        data.append(count)
    
    return {
        'labels': categories,
        'data': data
    }

@app.route('/admin/approve/<int:performance_id>', methods=['POST'])
def approve_performance(performance_id):
    """공연 승인"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    performance = Performance.query.get(performance_id)
    if performance:
        performance.is_approved = True
        db.session.commit()
        flash('공연이 승인되었습니다.', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject/<int:performance_id>', methods=['POST'])
def reject_performance(performance_id):
    """공연 거절"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    performance = Performance.query.get(performance_id)
    if performance:
        db.session.delete(performance)
        db.session.commit()
        flash('공연이 거절되었습니다.', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<int:performance_id>', methods=['POST'])
def delete_performance(performance_id):
    """공연 삭제"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    performance = Performance.query.get(performance_id)
    if performance:
        # 이미지 파일도 삭제
        if performance.image_url:
            try:
                # Cloudinary URL에서 파일 이름만 추출
                image_path = performance.image_url.split('/')[-1]
                if image_path:
                    public_id = image_path.rsplit('.', 1)[0] # .확장자 제거
                    cloudinary.uploader.destroy(public_id)
                    logger.info(f"Deleted image from Cloudinary: {public_id}")
            except Exception as e:
                logger.error(f"Error deleting image from Cloudinary: {e}")
        
        db.session.delete(performance)
        db.session.commit()
        flash('공연이 삭제되었습니다.', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/my-performances')
@login_required
def my_performances():
    """내 공연 신청 현황"""
    # 현재 사용자가 신청한 공연들 찾기
    my_performances = Performance.query.filter_by(user_id=current_user.id).all()
    return render_template('my_performances.html', performances=my_performances)

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_performance():
    """공연 신청 폼"""
    if request.method == 'POST':
        image_url = None
        if 'image_file' in request.files and request.files['image_file'].filename:
            image = request.files['image_file']
            logger.info(f"Image upload: {image.filename}")
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = image.filename.rsplit('.', 1)[-1].lower()
            if ext not in allowed_extensions:
                flash('지원하지 않는 이미지 형식입니다. (PNG, JPG, JPEG, GIF, WEBP만 가능)', 'error')
                return redirect(url_for('submit_performance'))
            try:
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']
                logger.info(f"Cloudinary image uploaded: {image_url}")
            except Exception as e:
                logger.error(f"Cloudinary upload error: {e}")
                flash('이미지 업로드 중 오류가 발생했습니다.', 'error')
                return redirect(url_for('submit_performance'))
        # 주소에서 지역 자동 감지
        address = request.form.get('address')
        detected_region = detect_region_from_address(address)
        
        # 지역 설정 (주소에서 감지된 지역이 있으면 사용, 없으면 수동 입력 사용)
        location = detected_region if detected_region else request.form['location']
        
        # 구매방법 처리
        purchase_methods = request.form.getlist('purchase_methods')
        import json
        purchase_methods_json = json.dumps(purchase_methods, ensure_ascii=False)

        # 가격 처리 (콤마 제거 후 숫자만 저장)
        price_raw = request.form.get('price_raw', '')
        if price_raw:
            price = price_raw
        else:
            # price_raw가 없으면 기존 price에서 콤마 제거
            price = request.form['price'].replace(',', '')
        
        performance = Performance(
            title=request.form['title'],
            group_name=request.form['group_name'],
            description=request.form['description'],
            location=location,  # 자동 감지된 지역 또는 수동 입력
            address=address,  # 상세 주소 저장
            price=price,  # 숫자만 저장
            date=request.form['date'],
            time=f"{request.form['start_time']}~{request.form['end_time']}",
            contact_email=request.form['contact_email'],
            video_url=request.form.get('video_url'),
            image_url=image_url,
            main_category=request.form['main_category'],  # 메인 카테고리 저장
            category=request.form['category'],  # 세부 카테고리 저장
            ticket_url=request.form.get('ticket_url'),  # 티켓 예매 링크 저장
            user_id=current_user.id,
            purchase_methods=purchase_methods_json
        )
        db.session.add(performance)
        db.session.commit()
        logger.info(f"Performance created with image_url: {image_url}")
        flash('공연 신청이 완료되었습니다! 관리자 승인 후 홈페이지에 표시됩니다.', 'success')
        return redirect(url_for('submit_performance'))
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template("submit.html", today_date=today_date)

@app.route('/performance/<int:performance_id>')
def performance_detail(performance_id):
    """공연 상세 페이지"""
    try:
        performance = Performance.query.get_or_404(performance_id)
        
        # 사용자 이벤트 추적 (로그인한 사용자만)
        if current_user.is_authenticated:
            track_user_event(
                user_id=current_user.id,
                event_type='view',
                performance_id=performance_id,
                metadata={'page': 'performance_detail'}
            )
        
        return render_template('performance_detail.html', performance=performance)
    except Exception as e:
        logger.error(f"공연 상세 페이지 오류: {e}")
        flash('공연 정보를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('home'))

@app.route('/like/<int:performance_id>', methods=['POST'])
@login_required
def toggle_like(performance_id):
    """공연 좋아요 토글"""
    try:
        performance = Performance.query.get(performance_id)
        if not performance:
            return jsonify({'success': False, 'error': '공연을 찾을 수 없습니다.'})
        
        # 이미 좋아요를 눌렀는지 확인
        existing_like = UserLike.query.filter_by(
            user_id=current_user.id, 
            performance_id=performance_id
        ).first()
        
        if existing_like:
            # 좋아요 취소
            db.session.delete(existing_like)
            performance.likes -= 1
            liked = False
        else:
            # 좋아요 추가
            new_like = UserLike(user_id=current_user.id, performance_id=performance_id)
            db.session.add(new_like)
            performance.likes += 1
            liked = True
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'likes': performance.likes, 
            'liked': liked
        })
        
    except Exception as e:
        logger.error(f"Like toggle error: {e}")
        return jsonify({'success': False, 'error': '오류가 발생했습니다.'})

# 카카오 OAuth 라우트들
@app.route('/login/kakao')
def kakao_login():
    """카카오 로그인 시작"""
    try:
        # 카카오 API 키 확인
        if not KAKAO_CLIENT_ID or not KAKAO_CLIENT_SECRET:
            logger.error("Kakao API keys not configured")
            flash('카카오 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요.', 'error')
            return redirect(url_for('login'))
        
        # 카카오 OAuth 인증 URL 생성
        auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code"
        logger.info(f"Redirecting to Kakao OAuth: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Kakao login error: {e}")
        flash('카카오 로그인 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))

@app.route('/register/kakao')
def kakao_register():
    """카카오 회원가입 시작 (로그인과 동일한 플로우)"""
    return redirect(url_for('kakao_login'))

@app.route('/auth/kakao/callback')
def kakao_callback():
    """카카오 OAuth 콜백 처리"""
    try:
        # 카카오 API 키 확인
        if not KAKAO_CLIENT_ID or not KAKAO_CLIENT_SECRET:
            logger.error("Kakao API keys not configured in callback")
            flash('카카오 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요.', 'error')
            return redirect(url_for('login'))
        
        # 인증 코드 받기
        code = request.args.get('code')
        if not code:
            flash('카카오 인증에 실패했습니다.', 'error')
            return redirect(url_for('login'))
        
        logger.info(f"Received Kakao authorization code: {code}")
        
        # 액세스 토큰 요청
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_CLIENT_ID,
            'client_secret': KAKAO_CLIENT_SECRET,
            'code': code,
            'redirect_uri': KAKAO_REDIRECT_URI
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        access_token = token_info.get('access_token')
        if not access_token:
            flash('카카오 액세스 토큰을 받지 못했습니다.', 'error')
            return redirect(url_for('login'))
        
        logger.info("Successfully obtained Kakao access token")
        
        # 사용자 정보 요청
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        logger.info(f"Kakao user info: {user_info}")
        
        # 카카오 사용자 ID
        kakao_id = str(user_info['id'])
        
        # 사용자 정보 추출
        kakao_account = user_info.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        
        # 이름 (닉네임 우선, 없으면 카카오 ID 사용)
        name = profile.get('nickname') or f"카카오사용자{kakao_id[-4:]}"
        
        # 이메일 (선택적 동의)
        email = kakao_account.get('email') or f"kakao_{kakao_id}@kakao.com"
        
        # 전화번호 (선택적 동의)
        phone = kakao_account.get('phone_number') or None
        
        # 기존 사용자 확인 (카카오 ID로)
        existing_user = User.query.filter_by(username=f"kakao_{kakao_id}").first()
        
        if existing_user:
            # 기존 사용자 로그인
            login_user(existing_user)
            flash('카카오로 로그인되었습니다!', 'success')
            logger.info(f"Existing Kakao user logged in: {existing_user.username}")
        else:
            # 새 사용자 생성
            new_user = User(
                name=name,
                username=f"kakao_{kakao_id}",
                email=email,
                phone=phone,
                password_hash=generate_password_hash(f"kakao_{kakao_id}_{uuid.uuid4()}")  # 랜덤 비밀번호
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            flash('카카오로 회원가입 및 로그인되었습니다!', 'success')
            logger.info(f"New Kakao user created and logged in: {new_user.username}")
        
        return redirect(url_for('home'))
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Kakao API request error: {e}")
        flash('카카오 서버와의 통신 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Kakao callback error: {e}")
        flash('카카오 로그인 처리 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))

# 구글 OAuth 라우트들
@app.route('/login/google')
def google_login():
    """구글 로그인 시작"""
    try:
        # 구글 API 키 확인
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.error("Google API keys not configured")
            flash('구글 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요.', 'error')
            return redirect(url_for('login'))
        
        # 구글 OAuth 인증 URL 생성
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=openid%20email%20profile"
        logger.info(f"Redirecting to Google OAuth: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Google login error: {e}")
        flash('구글 로그인 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))

@app.route('/register/google')
def google_register():
    """구글 회원가입 시작 (로그인과 동일한 플로우)"""
    return redirect(url_for('google_login'))

@app.route('/auth/google/callback')
def google_callback():
    """구글 OAuth 콜백 처리"""
    try:
        # 구글 API 키 확인
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.error("Google API keys not configured in callback")
            flash('구글 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요.', 'error')
            return redirect(url_for('login'))
        
        # 인증 코드 받기
        code = request.args.get('code')
        if not code:
            flash('구글 인증에 실패했습니다.', 'error')
            return redirect(url_for('login'))
        
        logger.info(f"Received Google authorization code: {code}")
        
        # 액세스 토큰 요청
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'redirect_uri': GOOGLE_REDIRECT_URI
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        access_token = token_info.get('access_token')
        if not access_token:
            flash('구글 액세스 토큰을 받지 못했습니다.', 'error')
            return redirect(url_for('login'))
        
        logger.info("Successfully obtained Google access token")
        
        # 사용자 정보 요청
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        logger.info(f"Google user info: {user_info}")
        
        # 구글 사용자 ID
        google_id = str(user_info['id'])
        
        # 사용자 정보 추출
        name = user_info.get('name') or f"구글사용자{google_id[-4:]}"
        email = user_info.get('email') or f"google_{google_id}@google.com"
        
        # 기존 사용자 확인 (구글 ID로)
        existing_user = User.query.filter_by(username=f"google_{google_id}").first()
        
        if existing_user:
            # 기존 사용자 로그인
            login_user(existing_user)
            flash('구글로 로그인되었습니다!', 'success')
            logger.info(f"Existing Google user logged in: {existing_user.username}")
        else:
            # 새 사용자 생성
            new_user = User(
                name=name,
                username=f"google_{google_id}",
                email=email,
                phone=None,
                password_hash=generate_password_hash(f"google_{google_id}_{uuid.uuid4()}")  # 랜덤 비밀번호
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            flash('구글로 회원가입 및 로그인되었습니다!', 'success')
            logger.info(f"New Google user created and logged in: {new_user.username}")
        
        return redirect(url_for('home'))
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Google API request error: {e}")
        flash('구글 서버와의 통신 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        flash('구글 로그인 처리 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))

@app.route('/admin/bulk-approve', methods=['POST'])
def bulk_approve_performances():
    """공연 일괄 승인"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'})
    
    try:
        data = request.get_json()
        performance_ids = data.get('performance_ids', [])
        
        if not performance_ids:
            return jsonify({'success': False, 'error': '선택된 공연이 없습니다.'})
        
        # 선택된 공연들을 승인
        performances = Performance.query.filter(Performance.id.in_(performance_ids)).all()
        for performance in performances:
            performance.is_approved = True
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{len(performances)}개의 공연이 승인되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Bulk approve error: {e}")
        return jsonify({'success': False, 'error': '오류가 발생했습니다.'})

@app.route('/admin/bulk-reject', methods=['POST'])
def bulk_reject_performances():
    """공연 일괄 거절"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'})
    
    try:
        data = request.get_json()
        performance_ids = data.get('performance_ids', [])
        
        if not performance_ids:
            return jsonify({'success': False, 'error': '선택된 공연이 없습니다.'})
        
        # 선택된 공연들을 삭제 (거절)
        performances = Performance.query.filter(Performance.id.in_(performance_ids)).all()
        for performance in performances:
            # 이미지 파일도 삭제
            if performance.image_url:
                try:
                    image_path = performance.image_url.split('/')[-1]
                    if image_path:
                        public_id = image_path.rsplit('.', 1)[0]
                        cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    logger.error(f"Error deleting image from Cloudinary: {e}")
            
            db.session.delete(performance)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{len(performances)}개의 공연이 거절되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Bulk reject error: {e}")
        return jsonify({'success': False, 'error': '오류가 발생했습니다.'})

@app.route('/admin/export/excel')
def export_excel():
    """공연 데이터 Excel 내보내기 (CSV 형식으로 대체)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    try:
        from io import StringIO
        from datetime import datetime
        import csv
        
        # 필터 파라미터 받기
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_filter = request.args.get('category_filter')
        
        # 쿼리 구성
        query = Performance.query
        
        if start_date:
            query = query.filter(Performance.date >= start_date)
        if end_date:
            query = query.filter(Performance.date <= end_date)
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        performances = query.all()
        
        # CSV 데이터 생성
        output = StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        writer.writerow([
            'ID', '제목', '팀명', '설명', '장소', '주소', '가격', '날짜', '시간',
            '연락처', '비디오URL', '이미지URL', '메인카테고리', '카테고리', 
            '티켓URL', '좋아요수', '승인상태', '신청자', '신청자이메일', '등록일'
        ])
        
        # 데이터 작성
        for perf in performances:
            user = User.query.get(perf.user_id)
            writer.writerow([
                perf.id,
                perf.title,
                perf.group_name,
                perf.description or '',
                perf.location or '',
                perf.address or '',
                perf.price or '',
                perf.date or '',
                perf.time or '',
                perf.contact_email or '',
                perf.video_url or '',
                perf.image_url or '',
                perf.main_category or '',
                perf.category or '',
                perf.ticket_url or '',
                perf.likes,
                '승인됨' if perf.is_approved else '대기중',
                user.name if user else '알 수 없음',
                user.email if user else '알 수 없음',
                perf.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        filename = f"공연데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Excel export error: {e}")
        flash('데이터 내보내기 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/export/csv')
def export_csv():
    """공연 데이터 CSV 내보내기"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    try:
        from io import StringIO
        from datetime import datetime
        import csv
        
        # 필터 파라미터 받기
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_filter = request.args.get('category_filter')
        
        # 쿼리 구성
        query = Performance.query
        
        if start_date:
            query = query.filter(Performance.date >= start_date)
        if end_date:
            query = query.filter(Performance.date <= end_date)
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        performances = query.all()
        
        # CSV 데이터 생성
        output = StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        writer.writerow([
            'ID', '제목', '팀명', '설명', '장소', '주소', '가격', '날짜', '시간',
            '연락처', '비디오URL', '이미지URL', '메인카테고리', '카테고리', 
            '티켓URL', '좋아요수', '승인상태', '신청자', '신청자이메일', '등록일'
        ])
        
        # 데이터 작성
        for perf in performances:
            user = User.query.get(perf.user_id)
            writer.writerow([
                perf.id,
                perf.title,
                perf.group_name,
                perf.description or '',
                perf.location or '',
                perf.address or '',
                perf.price or '',
                perf.date or '',
                perf.time or '',
                perf.contact_email or '',
                perf.video_url or '',
                perf.image_url or '',
                perf.main_category or '',
                perf.category or '',
                perf.ticket_url or '',
                perf.likes,
                '승인됨' if perf.is_approved else '대기중',
                user.name if user else '알 수 없음',
                user.email if user else '알 수 없음',
                perf.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        filename = f"공연데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        flash('CSV 내보내기 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/analytics')
@login_required
def analytics_dashboard():
    """공연시장 분석 대시보드"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        # 공연 데이터 수집
        performances = Performance.query.filter_by(is_approved=True).all()
        performances_data = []
        
        for perf in performances:
            performances_data.append({
                'title': perf.title,
                'category': perf.category,
                'location': perf.location,
                'price': perf.price,
                'date': perf.date,
                'likes': perf.likes,
                'comments': len(perf.comments) if hasattr(perf, 'comments') else 0
            })
        
        # 간단한 분석 데이터 생성
        categories = {}
        locations = {}
        total_performances = len(performances_data)
        
        for perf in performances_data:
            # 카테고리별 통계
            category = perf['category'] or '기타'
            categories[category] = categories.get(category, 0) + 1
            
            # 지역별 통계
            location = perf['location'] or '기타'
            locations[location] = locations.get(location, 0) + 1
        
        # 시장 공백 분석 (간단한 버전)
        market_gaps = {
            'category_gaps': categories,
            'location_gaps': locations,
            'total_performances': total_performances,
            'opportunities': [
                '대중무용 카테고리 확대 필요',
                '홍대 지역 공연 활성화',
                '무료 공연 프로그램 개발'
            ]
        }
        
        return render_template('analytics.html', 
                             market_gaps=market_gaps,
                             total_performances=total_performances,
                             categories=categories,
                             locations=locations)
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        flash('분석 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/recommendations')
@login_required
def get_recommendations():
    """개인화된 공연 추천"""
    try:
        from performance_recommendation_system import RecommendationEngine
        
        # 사용자 프로필 생성
        user_profile = {
            'categories': [],  # 사용자 선호 카테고리 (향후 확장)
            'locations': [],   # 사용자 선호 지역 (향후 확장)
            'price_range': 'all',
            'time': 'all',
            'interests': [],
            'viewing_history': [],
            'ratings': {}
        }
        
        # 공연 데이터 수집
        performances = Performance.query.filter_by(is_approved=True).all()
        performances_data = []
        
        for perf in performances:
            performances_data.append({
                'id': perf.id,
                'title': perf.title,
                'category': perf.category,
                'location': perf.location,
                'price': perf.price,
                'date': perf.date,
                'time': perf.time,
                'description': perf.description,
                'likes': perf.likes,
                'comments': []
            })
        
        # 추천 엔진 실행
        engine = RecommendationEngine()
        recommendations = engine.get_hybrid_recommendations(
            user_id=current_user.id,
            user_profile=user_profile,
            performances=performances_data
        )
        
        return render_template('recommendations.html', 
                             recommendations=recommendations,
                             user_profile=user_profile)
        
    except ImportError as e:
        logger.error(f"Recommendation module import error: {e}")
        flash('추천 시스템을 불러올 수 없습니다.', 'error')
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        flash('추천 시스템 오류가 발생했습니다.', 'error')
        return redirect(url_for('home'))

@app.route('/market-report')
@login_required
def generate_market_report():
    """시장 발전 리포트 생성"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        # 공연 데이터 수집
        performances = Performance.query.filter_by(is_approved=True).all()
        performances_data = []
        
        for perf in performances:
            performances_data.append({
                'title': perf.title,
                'category': perf.category,
                'location': perf.location,
                'price': perf.price,
                'date': perf.date,
                'venue': perf.location,
                'likes': perf.likes
            })
        
        # 간단한 리포트 생성
        report = f"""# 🎭 공연시장 발전 리포트

**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}
**분석 대상 공연 수**: {len(performances_data)}개

## 📊 시장 현황 분석

### 카테고리별 분포
"""
        
        # 카테고리별 통계
        categories = {}
        for perf in performances_data:
            category = perf['category'] or '기타'
            categories[category] = categories.get(category, 0) + 1
        
        for category, count in categories.items():
            percentage = (count / len(performances_data)) * 100
            report += f"- **{category}**: {count}개 ({percentage:.1f}%)\n"
        
        report += f"""
### 지역별 분포
"""
        
        # 지역별 통계
        locations = {}
        for perf in performances_data:
            location = perf['location'] or '기타'
            locations[location] = locations.get(location, 0) + 1
        
        for location, count in locations.items():
            percentage = (count / len(performances_data)) * 100
            report += f"- **{location}**: {count}개 ({percentage:.1f}%)\n"
        
        report += f"""
## 🎯 시장 기회 분석

### 발견된 기회 요소
1. **대중무용 카테고리 확대**: 현재 대중무용 공연이 부족하여 확대 필요
2. **홍대 지역 활성화**: 홍대 지역의 공연 문화 활성화 기회
3. **무료 공연 프로그램**: 접근성 향상을 위한 무료 공연 프로그램 개발

### 권장사항
1. 대중무용 카테고리 공연자 모집 강화
2. 홍대 지역 공연장 협력 관계 구축
3. 무료 공연 프로그램 개발 및 지원

---
*본 리포트는 {datetime.now().strftime('%Y년 %m월 %d일')} 기준으로 생성되었습니다.*
"""
        
        # 리포트 파일 저장
        report_filename = f"market_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(f"static/{report_filename}", 'w', encoding='utf-8') as f:
            f.write(report)
        
        flash(f'시장 발전 리포트가 생성되었습니다: {report_filename}', 'success')
        return redirect(url_for('analytics_dashboard'))
        
    except Exception as e:
        logger.error(f"Market report error: {e}")
        flash('시장 리포트 생성 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/kopis-sync', methods=['GET', 'POST'])
@login_required
def kopis_sync():
    """KOPIS 데이터 동기화"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        from kopis_api_integration import KOPISDataImporter
        from datetime import datetime
        
        # 성능 최적화된 동기화 (상세 정보 조회 비활성화)
        importer = KOPISDataImporter(db.session)
        imported_count = importer.import_performances(
            fetch_details=False,  # 성능 향상을 위해 상세 정보 조회 비활성화
            batch_size=50         # 배치 크기 설정
        )
        
        if imported_count > 0:
            flash(f'KOPIS 데이터 {imported_count}개가 성공적으로 동기화되었습니다. (성능 최적화 모드)', 'success')
            logger.info(f'KOPIS 동기화 완료: {imported_count}개 공연 추가')
        else:
            flash('동기화할 새로운 KOPIS 데이터가 없습니다. (이미 모든 데이터가 동기화되어 있습니다)', 'info')
            logger.info('KOPIS 동기화: 새로운 데이터 없음')
        
        # 동기화 후 홈페이지로 리다이렉션 (캐시 무효화)
        response = redirect(url_for('home'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except ImportError as e:
        logger.error(f"KOPIS module import error: {e}")
        flash('KOPIS 모듈을 불러올 수 없습니다.', 'error')
        return redirect(url_for('admin_panel'))
    except Exception as e:
        logger.error(f"KOPIS sync error: {e}")
        flash('KOPIS 동기화 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

# KOPIS URL 생성 함수 추가
def generate_kopis_url(kopis_id):
    """KOPIS 공연 페이지 URL 생성"""
    if not kopis_id:
        return None
    return f"https://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?mt20id={kopis_id}"

# 데이터 분석을 위한 모델들
class UserEvent(db.Model):
    """사용자 행동 추적"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_type = db.Column(db.String(50))  # 'view', 'like', 'comment', 'purchase'
    performance_id = db.Column(db.Integer, db.ForeignKey('performance.id'))
    timestamp = db.Column(db.DateTime, default=func.now())
    event_data = db.Column(db.Text)  # JSON 형태의 추가 데이터
    
    user = db.relationship('User', backref='events')
    performance = db.relationship('Performance', backref='events')

class PerformanceStats(db.Model):
    """공연별 상세 통계"""
    id = db.Column(db.Integer, primary_key=True)
    performance_id = db.Column(db.Integer, db.ForeignKey('performance.id'))
    date = db.Column(db.Date, nullable=False)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    ticket_clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    performance = db.relationship('Performance', backref='stats')

class CategoryTrend(db.Model):
    """카테고리별 트렌드 분석"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_performances = db.Column(db.Integer, default=0)
    total_views = db.Column(db.Integer, default=0)
    total_likes = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=func.now())

class TrendData(db.Model):
    """트렌드 분석 데이터"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50))
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=func.now())

class UserProfile(db.Model):
    """사용자 프로필 확장"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    age_group = db.Column(db.String(20))  # '10s', '20s', '30s', '40s', '50s+'
    gender = db.Column(db.String(10))  # 'male', 'female', 'other'
    region = db.Column(db.String(50))
    interests = db.Column(db.Text)  # JSON 형태의 관심사
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship('User', backref='profile', uselist=False)

# 템플릿 헬퍼 함수들
def format_date(date_obj):
    """안전한 날짜 포맷팅"""
    if date_obj and hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%Y-%m-%d')
    elif date_obj:
        return str(date_obj)
    else:
        return '미정'

def format_datetime(datetime_obj):
    """안전한 날짜시간 포맷팅"""
    if datetime_obj and hasattr(datetime_obj, 'strftime'):
        return datetime_obj.strftime('%Y-%m-%d %H:%M')
    elif datetime_obj:
        return str(datetime_obj)
    else:
        return '알 수 없음'

# 템플릿에 함수 등록
app.jinja_env.globals.update(format_date=format_date, format_datetime=format_datetime)

# 데이터 분석 유틸리티 함수들
def track_user_event(user_id, event_type, performance_id=None, metadata=None):
    """사용자 이벤트 추적"""
    try:
        event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            performance_id=performance_id,
            event_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(event)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"이벤트 추적 실패: {e}")
        return False

def get_real_time_stats():
    """실시간 통계 데이터"""
    try:
        today = datetime.now().date()
        
        # 오늘 등록된 공연 수
        today_performances = Performance.query.filter(
            func.date(Performance.created_at) == today
        ).count()
        
        # 오늘 방문자 수 (고유 사용자)
        today_visitors = db.session.query(func.count(func.distinct(UserEvent.user_id))).filter(
            func.date(UserEvent.timestamp) == today,
            UserEvent.event_type == 'view'
        ).scalar() or 0
        
        # 이번 주 예매율 (좋아요 기준)
        week_start = today - timedelta(days=today.weekday())
        week_performances = Performance.query.filter(
            func.date(Performance.created_at) >= week_start
        ).count()
        
        week_likes = db.session.query(func.sum(UserEvent.id)).filter(
            func.date(UserEvent.timestamp) >= week_start,
            UserEvent.event_type == 'like'
        ).scalar() or 0
        
        booking_rate = (week_likes / week_performances * 100) if week_performances > 0 else 0
        
        # 인기 카테고리
        popular_category = db.session.query(Performance.category, func.count(Performance.id)).filter(
            func.date(Performance.created_at) >= week_start
        ).group_by(Performance.category).order_by(func.count(Performance.id).desc()).first()
        
        return {
            'today_performances': today_performances,
            'today_visitors': today_visitors,
            'booking_rate': round(booking_rate, 1),
            'popular_category': popular_category[0] if popular_category else '없음'
        }
    except Exception as e:
        logger.error(f"실시간 통계 조회 실패: {e}")
        return {
            'today_performances': 0,
            'today_visitors': 0,
            'booking_rate': 0,
            'popular_category': '없음'
        }

def get_audience_analysis():
    """관객 분석 데이터"""
    try:
        # 연령대별 선호도 (시뮬레이션 데이터)
        age_preferences = {
            '20s': {'뮤지컬': 45, '연극': 30, '무용': 25},
            '30s': {'연극': 40, '뮤지컬': 35, '클래식': 25},
            '40s': {'클래식': 50, '연극': 30, '뮤지컬': 20},
            '50s+': {'클래식': 60, '연극': 25, '뮤지컬': 15}
        }
        
        # 성별별 관심도
        gender_preferences = {
            'female': {'뮤지컬': 55, '연극': 25, '무용': 20},
            'male': {'연극': 45, '뮤지컬': 35, '클래식': 20}
        }
        
        # 지역별 분포
        region_distribution = {
            '서울': 60,
            '경기': 25,
            '부산': 8,
            '기타': 7
        }
        
        return {
            'age_preferences': age_preferences,
            'gender_preferences': gender_preferences,
            'region_distribution': region_distribution
        }
    except Exception as e:
        logger.error(f"관객 분석 조회 실패: {e}")
        return {}

def get_trend_prediction():
    """트렌드 예측 데이터"""
    try:
        # 향후 3개월 전망
        future_trends = {
            '뮤지컬': {'growth': 15, 'reason': '여름 휴가 시즌'},
            '연극': {'growth': 8, 'reason': '가을 문화 시즌'},
            '무용': {'growth': 5, 'reason': '안정적 성장'},
            '클래식': {'growth': 12, 'reason': '겨울 시즌'}
        }
        
        # 핫 키워드
        hot_keywords = [
            {'keyword': '환경친화적 공연', 'growth': 200},
            {'keyword': 'AI 공연', 'growth': 150},
            {'keyword': '소셜미디어 공연', 'growth': 120},
            {'keyword': 'VR 공연', 'growth': 100}
        ]
        
        return {
            'future_trends': future_trends,
            'hot_keywords': hot_keywords
        }
    except Exception as e:
        logger.error(f"트렌드 예측 조회 실패: {e}")
        return {}

def get_performance_statistics():
    """공연별 상세 통계 조회"""
    try:
        # 최근 30일간의 통계
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        stats = db.session.query(
            Performance.id,
            Performance.title,
            Performance.category,
            func.sum(PerformanceStats.views).label('total_views'),
            func.sum(PerformanceStats.likes).label('total_likes'),
            func.sum(PerformanceStats.comments).label('total_comments'),
            func.sum(PerformanceStats.ticket_clicks).label('total_ticket_clicks'),
            func.avg(Comment.rating).label('avg_rating')
        ).outerjoin(PerformanceStats, Performance.id == PerformanceStats.performance_id)\
         .outerjoin(Comment, Performance.id == Comment.performance_id)\
         .filter(PerformanceStats.date >= start_date)\
         .group_by(Performance.id, Performance.title, Performance.category)\
         .order_by(func.sum(PerformanceStats.views).desc())\
         .limit(10).all()
        
        return [{
            'id': stat.id,
            'title': stat.title,
            'category': stat.category,
            'total_views': stat.total_views or 0,
            'total_likes': stat.total_likes or 0,
            'total_comments': stat.total_comments or 0,
            'total_ticket_clicks': stat.total_ticket_clicks or 0,
            'avg_rating': round(stat.avg_rating, 1) if stat.avg_rating else 0,
            'engagement_rate': round(((stat.total_likes or 0) + (stat.total_comments or 0)) / (stat.total_views or 1) * 100, 2)
        } for stat in stats]
    except Exception as e:
        app.logger.error(f"공연 통계 조회 오류: {e}")
        return []

def get_category_trends():
    """카테고리별 트렌드 분석"""
    try:
        # 최근 7일간의 카테고리별 트렌드
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        trends = db.session.query(
            Performance.category,
            func.count(Performance.id).label('total_performances'),
            func.sum(Performance.likes).label('total_likes'),
            func.avg(Comment.rating).label('avg_rating')
        ).outerjoin(Comment, Performance.id == Comment.performance_id)\
         .filter(Performance.created_at >= start_date)\
         .group_by(Performance.category)\
         .order_by(func.count(Performance.id).desc())\
         .all()
        
        return [{
            'category': trend.category or '기타',
            'total_performances': trend.total_performances,
            'total_likes': trend.total_likes or 0,
            'avg_rating': round(trend.avg_rating, 1) if trend.avg_rating else 0,
            'popularity_score': (trend.total_performances * 0.4) + ((trend.total_likes or 0) * 0.4) + ((trend.avg_rating or 0) * 0.2)
        } for trend in trends]
    except Exception as e:
        app.logger.error(f"카테고리 트렌드 조회 오류: {e}")
        return []

@app.route('/admin/performance-stats')
@login_required
def performance_stats():
    """공연별 상세 통계 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        performance_stats = get_performance_statistics()
        category_trends = get_category_trends()
        
        return render_template('performance_stats.html', 
                             performance_stats=performance_stats,
                             category_trends=category_trends)
    except Exception as e:
        app.logger.error(f"공연 통계 페이지 오류: {e}")
        flash('통계 데이터를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/export-stats/excel')
@login_required
def export_performance_stats_excel():
    """공연 통계 엑셀 내보내기"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        performance_stats = get_performance_statistics()
        category_trends = get_category_trends()
        
        # 엑셀 파일 생성
        wb = Workbook()
        
        # 공연별 통계 시트
        ws1 = wb.active
        ws1.title = "공연별 통계"
        ws1.append(['공연명', '카테고리', '조회수', '좋아요', '댓글', '티켓클릭', '평점', '참여율(%)'])
        
        for stat in performance_stats:
            ws1.append([
                stat['title'],
                stat['category'],
                stat['total_views'],
                stat['total_likes'],
                stat['total_comments'],
                stat['total_ticket_clicks'],
                stat['avg_rating'],
                stat['engagement_rate']
            ])
        
        # 카테고리 트렌드 시트
        ws2 = wb.create_sheet("카테고리 트렌드")
        ws2.append(['카테고리', '공연 수', '총 좋아요', '평균 평점', '인기도 점수'])
        
        for trend in category_trends:
            ws2.append([
                trend['category'],
                trend['total_performances'],
                trend['total_likes'],
                trend['avg_rating'],
                round(trend['popularity_score'], 2)
            ])
        
        # 파일 저장
        filename = f"performance_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(app.static_folder, 'exports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        wb.save(filepath)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        app.logger.error(f"통계 엑셀 내보내기 오류: {e}")
        flash('엑셀 파일 생성 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

# AI 채팅 어시스턴트 관련 함수들
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict

# AI 대화 컨텍스트 관리
class AIConversationContext:
    def __init__(self):
        self.conversation_history = []
        self.user_preferences = {
            'favorite_categories': defaultdict(int),
            'favorite_locations': defaultdict(int),
            'price_range': None,
            'last_searches': [],
            'interaction_count': 0
        }
        self.current_context = {
            'last_query': None,
            'last_results': [],
            'current_topic': None,
            'mood': 'neutral'
        }
    
    def add_interaction(self, user_query, ai_response, performances=None):
        """대화 기록 추가 및 사용자 선호도 학습"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_query': user_query,
            'ai_response': ai_response,
            'performances': performances
        })
        
        # 사용자 선호도 학습
        self._learn_user_preferences(user_query, performances)
        self.user_preferences['interaction_count'] += 1
        
        # 컨텍스트 업데이트
        self.current_context['last_query'] = user_query
        self.current_context['last_results'] = performances or []
        
        # 대화 기록 최대 10개 유지
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
    
    def _learn_user_preferences(self, query, performances):
        """사용자 선호도 학습"""
        if not performances:
            return
        
        # 카테고리 선호도 학습
        for performance in performances:
            if performance.category:
                self.user_preferences['favorite_categories'][performance.category] += 1
            
            # 지역 선호도 학습
            if performance.location:
                self.user_preferences['favorite_locations'][performance.location] += 1
        
        # 최근 검색 기록 저장
        self.user_preferences['last_searches'].append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'result_count': len(performances)
        })
        
        # 최근 5개 검색만 유지
        if len(self.user_preferences['last_searches']) > 5:
            self.user_preferences['last_searches'].pop(0)
    
    def get_user_preferences(self):
        """사용자 선호도 반환"""
        return {
            'top_categories': sorted(
                self.user_preferences['favorite_categories'].items(),
                key=lambda x: x[1], reverse=True
            )[:3],
            'top_locations': sorted(
                self.user_preferences['favorite_locations'].items(),
                key=lambda x: x[1], reverse=True
            )[:3],
            'interaction_count': self.user_preferences['interaction_count']
        }
    
    def get_conversation_context(self):
        """현재 대화 컨텍스트 반환"""
        return {
            'history_length': len(self.conversation_history),
            'last_query': self.current_context['last_query'],
            'last_result_count': len(self.current_context['last_results']),
            'user_preferences': self.get_user_preferences()
        }

# 전역 AI 컨텍스트 (실제로는 세션별로 관리해야 함)
ai_context = AIConversationContext()

def parse_user_query(query):
    """사용자 질문을 파싱하여 검색 조건 추출 (고도화된 버전)"""
    query = query.lower().strip()
    
    # 기본 검색 조건
    conditions = {
        'location': None,
        'price_range': None,
        'date_range': None,
        'category': None,
        'keywords': [],
        'exclude_category': None,
        'price_min': None,
        'price_max': None,
        'age_group': None,
        'mood': None
    }
    
    # 지역 추출 (확장된 키워드)
    location_keywords = {
        '서울': ['서울', '서울시', '서울특별시'],
        '부산': ['부산', '부산시', '부산광역시'],
        '대구': ['대구', '대구시', '대구광역시'],
        '인천': ['인천', '인천시', '인천광역시'],
        '광주': ['광주', '광주시', '광주광역시'],
        '대전': ['대전', '대전시', '대전광역시'],
        '울산': ['울산', '울산시', '울산광역시'],
        '세종': ['세종', '세종시', '세종특별시'],
        '강남': ['강남', '강남구', '강남역', '강남대로'],
        '홍대': ['홍대', '홍대입구', '홍대역', '홍익대'],
        '명동': ['명동', '명동역', '명동길'],
        '잠실': ['잠실', '잠실역', '잠실로'],
        '강북': ['강북', '강북구', '강북역'],
        '신촌': ['신촌', '신촌역', '신촌로'],
        '이태원': ['이태원', '이태원역', '이태원로'],
        '동대문': ['동대문', '동대문역', '동대문시장'],
        '종로': ['종로', '종로구', '종로역'],
        '마포': ['마포', '마포구', '마포역'],
        '용산': ['용산', '용산구', '용산역'],
        '영등포': ['영등포', '영등포구', '영등포역']
    }
    
    for location, keywords in location_keywords.items():
        for keyword in keywords:
            if keyword in query:
                conditions['location'] = location
                break
        if conditions['location']:
            break
    
    # 가격대 추출 (더 정교한 처리)
    price_patterns = [
        (r'무료|0원|공짜|free', 'free'),
        (r'1만원?대?|1만\s*원?|1만원\s*이하', 'low'),
        (r'2만원?대?|2만\s*원?|2만원\s*이하', 'low'),
        (r'3만원?대?|3만\s*원?|3만원\s*이하', 'medium'),
        (r'4만원?대?|4만\s*원?|4만원\s*이하', 'medium'),
        (r'5만원?대?|5만\s*원?|5만원\s*이하', 'high'),
        (r'6만원?대?|6만\s*원?|6만원\s*이하', 'high'),
        (r'7만원?대?|7만\s*원?|7만원\s*이하', 'premium'),
        (r'8만원?대?|8만\s*원?|8만원\s*이하', 'premium'),
        (r'9만원?대?|9만\s*원?|9만원\s*이하', 'premium'),
        (r'10만원?대?|10만\s*원?|10만원\s*이하', 'premium'),
        (r'10만원?\s*이상|10만원?\s*초과', 'premium')
    ]
    
    import re
    for pattern, price_range in price_patterns:
        if re.search(pattern, query):
            conditions['price_range'] = price_range
            break
    
    # 가격 범위 추출 (예: 3-5만원)
    price_range_match = re.search(r'(\d+)만원?\s*[-~]\s*(\d+)만원?', query)
    if price_range_match:
        conditions['price_min'] = int(price_range_match.group(1))
        conditions['price_max'] = int(price_range_match.group(2))
    
    # 날짜 추출 (확장된 키워드)
    date_patterns = [
        (r'오늘|today|금일', 'today'),
        (r'내일|tomorrow|명일', 'tomorrow'),
        (r'모레|day\s*after\s*tomorrow', 'day_after_tomorrow'),
        (r'이번주|이번\s*주|this\s*week|금주', 'this_week'),
        (r'다음주|다음\s*주|next\s*week|내주', 'next_week'),
        (r'이번달|이번\s*달|this\s*month|금월', 'this_month'),
        (r'다음달|다음\s*달|next\s*month|내월', 'next_month'),
        (r'주말|weekend|토일', 'weekend'),
        (r'평일|weekday|월화수목금', 'weekday'),
        (r'곧|soon|빨리|급하게', 'soon'),
        (r'나중에|later|시간\s*많음', 'later')
    ]
    
    for pattern, date_range in date_patterns:
        if re.search(pattern, query):
            conditions['date_range'] = date_range
            break
    
    # 카테고리 추출 (확장된 키워드)
    category_keywords = {
        '뮤지컬': ['뮤지컬', 'musical', '뮤지컬공연', '뮤지컬쇼'],
        '연극': ['연극', 'play', '드라마', '극', '연극공연'],
        '콘서트': ['콘서트', 'concert', '음악회', '공연', '라이브'],
        '클래식': ['클래식', 'classical', '교향악', '실내악', '오케스트라'],
        '오페라': ['오페라', 'opera', '가극'],
        '발레': ['발레', 'ballet', '무용', '춤'],
        '무용': ['무용', 'dance', '현대무용', '한국무용'],
        '전시': ['전시', 'exhibition', '미술관', '갤러리', '아트'],
        '축제': ['축제', 'festival', '페스티벌', '행사'],
        '뮤지컬': ['뮤지컬', 'musical', '뮤지컬공연'],
        '연극': ['연극', 'play', '드라마', '극'],
        '콘서트': ['콘서트', 'concert', '음악회', '라이브'],
        '클래식': ['클래식', 'classical', '교향악'],
        '오페라': ['오페라', 'opera', '가극'],
        '발레': ['발레', 'ballet', '무용'],
        '무용': ['무용', 'dance', '현대무용'],
        '전시': ['전시', 'exhibition', '미술관'],
        '축제': ['축제', 'festival', '페스티벌']
    }
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in query:
                conditions['category'] = category
                break
        if conditions['category']:
            break
    
    # 제외할 카테고리 추출
    exclude_patterns = [
        (r'뮤지컬\s*말고|뮤지컬\s*제외|뮤지컬\s*빼고', '뮤지컬'),
        (r'연극\s*말고|연극\s*제외|연극\s*빼고', '연극'),
        (r'콘서트\s*말고|콘서트\s*제외|콘서트\s*빼고', '콘서트'),
        (r'클래식\s*말고|클래식\s*제외|클래식\s*빼고', '클래식')
    ]
    
    for pattern, exclude_category in exclude_patterns:
        if re.search(pattern, query):
            conditions['exclude_category'] = exclude_category
            break
    
    # 연령대 추출
    age_patterns = [
        (r'10대|10살|10대\s*학생', '10s'),
        (r'20대|20살|20대\s*대학생', '20s'),
        (r'30대|30살|30대\s*직장인', '30s'),
        (r'40대|40살|40대\s*성인', '40s'),
        (r'50대|50살|50대\s*중년', '50s'),
        (r'어린이|아이|키즈|children|kids', 'children'),
        (r'청소년|중고등학생|teen', 'teen'),
        (r'성인|어른|adult', 'adult'),
        (r'노인|어르신|elderly', 'elderly')
    ]
    
    for pattern, age_group in age_patterns:
        if re.search(pattern, query):
            conditions['age_group'] = age_group
            break
    
    # 분위기/무드 추출
    mood_patterns = [
        (r'신나는|활기찬|energetic|fun', 'energetic'),
        (r'감동적인|감동|touching|moving', 'touching'),
        (r'재미있는|재밌는|funny|fun', 'fun'),
        (r'로맨틱한|로맨틱|romantic|사랑', 'romantic'),
        (r'슬픈|우울한|sad|melancholy', 'sad'),
        (r'긴장감|스릴|thrilling|exciting', 'thrilling'),
        (r'평화로운|차분한|calm|peaceful', 'calm'),
        (r'고급스러운|세련된|elegant|sophisticated', 'elegant'),
        (r'힐링|치유|healing|therapeutic', 'healing')
    ]
    
    for pattern, mood in mood_patterns:
        if re.search(pattern, query):
            conditions['mood'] = mood
            break
    
    # 키워드 추출 (확장된 버전)
    positive_keywords = ['추천', '좋은', '인기', '핫한', '신나는', '감동적인', '재미있는', '보여줘', '알려줘', '찾아줘', '보고싶어', '가고싶어', '궁금해', '어떤', '뭐가', '뭔가']
    for keyword in positive_keywords:
        if keyword in query:
            conditions['keywords'].append(keyword)
    
    return conditions

def analyze_performance_data():
    """공연 데이터 분석 및 인사이트 생성"""
    try:
        # 전체 공연 통계
        total_performances = Performance.query.filter_by(is_approved=True).count()
        
        # 카테고리별 통계
        categories = db.session.query(Performance.category, db.func.count(Performance.id)).\
            filter_by(is_approved=True).\
            group_by(Performance.category).\
            order_by(db.func.count(Performance.id).desc()).all()
        
        # 지역별 통계
        locations = db.session.query(Performance.location, db.func.count(Performance.id)).\
            filter_by(is_approved=True).\
            group_by(Performance.location).\
            order_by(db.func.count(Performance.id).desc()).all()
        
        # 인기 공연 (좋아요 수 기준)
        popular_performances = Performance.query.filter_by(is_approved=True).\
            order_by(Performance.likes.desc()).limit(5).all()
        
        # 최근 공연
        recent_performances = Performance.query.filter_by(is_approved=True).\
            order_by(Performance.date.desc()).limit(5).all()
        
        return {
            'total_count': total_performances,
            'categories': categories,
            'locations': locations,
            'popular': popular_performances,
            'recent': recent_performances
        }
    except Exception as e:
        app.logger.error(f"공연 데이터 분석 오류: {e}")
        return None

def generate_personalized_recommendations(user_preferences, conditions):
    """개인화된 추천 생성"""
    try:
        query = Performance.query.filter_by(is_approved=True)
        
        # 사용자 선호도 기반 가중치 적용
        recommendations = []
        
        # 선호 카테고리 기반 추천
        if user_preferences.get('top_categories'):
            for category, weight in user_preferences['top_categories']:
                category_performances = query.filter(Performance.category.contains(category)).\
                    order_by(Performance.likes.desc()).limit(3).all()
                recommendations.extend(category_performances)
        
        # 선호 지역 기반 추천
        if user_preferences.get('top_locations'):
            for location, weight in user_preferences['top_locations']:
                location_performances = query.filter(Performance.location.contains(location)).\
                    order_by(Performance.likes.desc()).limit(2).all()
                recommendations.extend(location_performances)
        
        # 중복 제거 및 정렬
        unique_recommendations = list({p.id: p for p in recommendations}.values())
        unique_recommendations.sort(key=lambda x: x.likes, reverse=True)
        
        return unique_recommendations[:5]
        
    except Exception as e:
        app.logger.error(f"개인화 추천 오류: {e}")
        return []

def search_performances_by_ai(conditions):
    """AI 조건에 따른 공연 검색 (고도화된 버전)"""
    try:
        query = Performance.query.filter_by(is_approved=True)
        
        # 지역 필터 (더 정교한 처리)
        if conditions['location']:
            location = conditions['location']
            if location in ['강남', '홍대', '명동', '잠실', '강북', '신촌', '이태원', '동대문', '종로', '마포', '용산', '영등포']:
                # 서울 지역별 세부 검색
                if location == '강남':
                    query = query.filter(
                        (Performance.address.contains('강남')) |
                        (Performance.location.contains('강남')) |
                        (Performance.address.contains('서초'))
                    )
                elif location == '홍대':
                    query = query.filter(
                        (Performance.address.contains('홍대')) |
                        (Performance.location.contains('홍대')) |
                        (Performance.address.contains('마포'))
                    )
                elif location == '명동':
                    query = query.filter(
                        (Performance.address.contains('명동')) |
                        (Performance.location.contains('명동')) |
                        (Performance.address.contains('중구'))
                    )
                else:
                    query = query.filter(
                        (Performance.address.contains(location)) |
                        (Performance.location.contains(location))
                    )
            else:
                # 다른 도시 검색
                query = query.filter(
                    (Performance.location.contains(location)) |
                    (Performance.address.contains(location))
                )
        
        # 가격대 필터 (더 정교한 처리)
        if conditions['price_range']:
            price_range = conditions['price_range']
            if price_range == 'free':
                query = query.filter(
                    (Performance.price.contains('무료')) |
                    (Performance.price.contains('0원')) |
                    (Performance.price.contains('공짜'))
                )
            elif price_range == 'low':
                query = query.filter(
                    (Performance.price.contains('1만')) |
                    (Performance.price.contains('2만')) |
                    (Performance.price.contains('무료'))
                )
            elif price_range == 'medium':
                query = query.filter(
                    (Performance.price.contains('3만')) |
                    (Performance.price.contains('4만')) |
                    (Performance.price.contains('2만'))
                )
            elif price_range == 'high':
                query = query.filter(
                    (Performance.price.contains('5만')) |
                    (Performance.price.contains('6만')) |
                    (Performance.price.contains('4만'))
                )
            elif price_range == 'premium':
                query = query.filter(
                    (Performance.price.contains('7만')) |
                    (Performance.price.contains('8만')) |
                    (Performance.price.contains('9만')) |
                    (Performance.price.contains('10만'))
                )
        
        # 가격 범위 필터 (예: 3-5만원)
        if conditions['price_min'] and conditions['price_max']:
            # 가격 문자열에서 숫자 추출하여 범위 검색
            # 실제 구현에서는 가격 필드를 숫자로 저장하는 것이 좋음
            pass
        
        # 날짜 필터 (확장된 처리)
        if conditions['date_range']:
            today = datetime.now().date()
            date_range = conditions['date_range']
            
            if date_range == 'today':
                query = query.filter(Performance.date == today.strftime('%Y-%m-%d'))
            elif date_range == 'tomorrow':
                tomorrow = today + timedelta(days=1)
                query = query.filter(Performance.date == tomorrow.strftime('%Y-%m-%d'))
            elif date_range == 'day_after_tomorrow':
                day_after = today + timedelta(days=2)
                query = query.filter(Performance.date == day_after.strftime('%Y-%m-%d'))
            elif date_range == 'this_week':
                end_of_week = today + timedelta(days=7)
                query = query.filter(Performance.date >= today.strftime('%Y-%m-%d'))
                query = query.filter(Performance.date <= end_of_week.strftime('%Y-%m-%d'))
            elif date_range == 'next_week':
                next_week_start = today + timedelta(days=7)
                next_week_end = today + timedelta(days=14)
                query = query.filter(Performance.date >= next_week_start.strftime('%Y-%m-%d'))
                query = query.filter(Performance.date <= next_week_end.strftime('%Y-%m-%d'))
            elif date_range == 'this_month':
                end_of_month = today.replace(day=28) + timedelta(days=4)
                end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
                query = query.filter(Performance.date >= today.strftime('%Y-%m-%d'))
                query = query.filter(Performance.date <= end_of_month.strftime('%Y-%m-%d'))
            elif date_range == 'next_month':
                next_month_start = today.replace(day=1) + timedelta(days=32)
                next_month_start = next_month_start.replace(day=1)
                next_month_end = next_month_start.replace(day=28) + timedelta(days=4)
                next_month_end = next_month_end.replace(day=1) - timedelta(days=1)
                query = query.filter(Performance.date >= next_month_start.strftime('%Y-%m-%d'))
                query = query.filter(Performance.date <= next_month_end.strftime('%Y-%m-%d'))
            elif date_range == 'weekend':
                # 주말 필터링 (실제로는 요일 정보가 필요)
                pass
            elif date_range == 'soon':
                # 곧 (1주일 이내)
                end_soon = today + timedelta(days=7)
                query = query.filter(Performance.date >= today.strftime('%Y-%m-%d'))
                query = query.filter(Performance.date <= end_soon.strftime('%Y-%m-%d'))
        
        # 카테고리 필터
        if conditions['category']:
            category = conditions['category']
            query = query.filter(Performance.category.contains(category))
        
        # 제외할 카테고리 필터
        if conditions['exclude_category']:
            exclude_category = conditions['exclude_category']
            query = query.filter(~Performance.category.contains(exclude_category))
        
        # 연령대별 필터 (간접적)
        if conditions['age_group']:
            age_group = conditions['age_group']
            if age_group == 'children':
                # 어린이 공연 키워드
                query = query.filter(
                    (Performance.category.contains('어린이')) |
                    (Performance.title.contains('어린이')) |
                    (Performance.category.contains('키즈'))
                )
            elif age_group == 'teen':
                # 청소년 공연 키워드
                query = query.filter(
                    (Performance.category.contains('청소년')) |
                    (Performance.title.contains('청소년'))
                )
        
        # 분위기/무드 필터 (간접적)
        if conditions['mood']:
            mood = conditions['mood']
            mood_keywords = {
                'energetic': ['신나는', '활기찬', '댄스', '힙합'],
                'touching': ['감동', '드라마', '로맨스'],
                'fun': ['코미디', '재미', '웃음'],
                'romantic': ['로맨스', '사랑', '로맨틱'],
                'sad': ['드라마', '슬픈', '감동'],
                'thrilling': ['스릴', '액션', '긴장'],
                'calm': ['클래식', '힐링', '평화'],
                'elegant': ['클래식', '오페라', '발레'],
                'healing': ['힐링', '치유', '마음']
            }
            
            if mood in mood_keywords:
                keywords = mood_keywords[mood]
                mood_filter = query.filter(
                    *[Performance.title.contains(keyword) | Performance.category.contains(keyword) for keyword in keywords]
                )
                if mood_filter.count() > 0:
                    query = mood_filter
        
        # 정렬 (다양한 기준)
        if conditions['keywords'] and any(keyword in ['인기', '핫한', '좋은'] for keyword in conditions['keywords']):
            # 인기도 기준 정렬
            query = query.order_by(Performance.likes.desc())
        elif conditions['date_range'] in ['soon', 'today', 'tomorrow']:
            # 날짜순 정렬 (급한 경우)
            query = query.order_by(Performance.date.asc())
        else:
            # 기본 정렬 (좋아요 수 + 날짜)
            query = query.order_by(Performance.likes.desc(), Performance.date.asc())
        
        # 결과 수 조정 (조건에 따라)
        limit_count = 5
        if conditions['date_range'] in ['today', 'tomorrow']:
            limit_count = 3  # 오늘/내일은 적은 수
        elif len(conditions['keywords']) > 2:
            limit_count = 7  # 많은 키워드가 있으면 더 많은 결과
        
        results = query.limit(limit_count).all()
        
        return results
        
    except Exception as e:
        app.logger.error(f"AI 공연 검색 오류: {e}")
        return []

def understand_user_intent(query, context):
    """사용자 의도 파악 및 대화 맥락 이해"""
    query_lower = query.lower()
    
    # 대화 의도 분류
    intents = {
        'greeting': ['안녕', '하이', 'hello', 'hi', '반가워', '처음'],
        'farewell': ['잘가', '바이', 'goodbye', 'bye', '그만', '끝'],
        'thanks': ['고마워', '감사', 'thank', 'thanks', '좋아'],
        'help': ['도움', 'help', '어떻게', '방법', '사용법'],
        'search': ['찾아', '검색', '보여', '추천', '알려', '궁금'],
        'compare': ['비교', '어떤게', '더', 'vs', 'versus'],
        'complaint': ['별로', '좋지', '싫어', '아니', 'no'],
        'praise': ['좋아', '멋져', '최고', 'great', 'awesome'],
        'question': ['뭐', '무엇', '어떤', '언제', '어디', '왜', '어떻게']
    }
    
    detected_intent = 'search'  # 기본값
    for intent, keywords in intents.items():
        if any(keyword in query_lower for keyword in keywords):
            detected_intent = intent
            break
    
    # 대화 맥락 분석
    conversation_context = context.get_conversation_context()
    
    # 이전 대화와의 연관성 확인
    follow_up = False
    if conversation_context['last_query']:
        last_query = conversation_context['last_query'].lower()
        # 이전 질문에 대한 후속 질문인지 확인
        follow_up_keywords = ['그거', '그것', '그', '이거', '이것', '이', '저거', '저것', '저', '다른', '더', '또', '또한']
        if any(keyword in query_lower for keyword in follow_up_keywords):
            follow_up = True
    
    return {
        'intent': detected_intent,
        'follow_up': follow_up,
        'context': conversation_context
    }

def generate_contextual_response(user_query, performances, context):
    """컨텍스트 기반 지능형 응답 생성"""
    intent_analysis = understand_user_intent(user_query, context)
    intent = intent_analysis['intent']
    follow_up = intent_analysis['follow_up']
    
    # 의도별 맞춤 응답
    if intent == 'greeting':
        return generate_greeting_response(context)
    elif intent == 'farewell':
        return generate_farewell_response(context)
    elif intent == 'thanks':
        return generate_thanks_response(context)
    elif intent == 'help':
        return generate_help_response(context)
    elif intent == 'complaint':
        return generate_complaint_response(context)
    elif intent == 'praise':
        return generate_praise_response(context)
    else:
        return generate_search_response(user_query, performances, context, follow_up)

def generate_greeting_response(context):
    """인사 응답 생성"""
    conversation_context = context.get_conversation_context()
    interaction_count = conversation_context['user_preferences']['interaction_count']
    
    greetings = [
        "안녕하세요! 공연 추천 AI 어시스턴트입니다! 🎭✨",
        "반갑습니다! 오늘도 멋진 공연을 찾아드릴게요! 🎪🌟",
        "어서오세요! 어떤 공연을 찾고 계신가요? 🎵💫",
        "환영합니다! 공연 세계로 함께 떠나볼까요? 🎬🎉"
    ]
    
    if interaction_count == 0:
        message = random.choice(greetings)
        message += "\n\n처음 뵙는 분이시네요! 다음과 같이 물어보세요:"
        message += "\n• '서울에서 5만원대 뮤지컬 추천해줘'"
        message += "\n• '이번 주말에 볼만한 공연 있어?'"
        message += "\n• '무료로 볼 수 있는 공연 찾아줘'"
    else:
        message = random.choice(greetings)
        message += f"\n\n오늘 {interaction_count}번째로 만나뵙네요! 😊"
        
        # 개인화된 추천
        if conversation_context['user_preferences']['top_categories']:
            top_category = conversation_context['user_preferences']['top_categories'][0][0]
            message += f"\n\n{top_category}을 좋아하시는 것 같아요! 오늘도 {top_category} 공연을 찾아드릴까요?"
    
    return {
        'message': message,
        'suggestions': ['인기 공연 보기', '전체 공연 보기', '무료 공연 보기']
    }

def generate_farewell_response(context):
    """작별 인사 응답 생성"""
    farewells = [
        "안녕히 가세요! 또 멋진 공연으로 찾아뵙겠습니다! 👋✨",
        "다음에 또 만나요! 공연 즐기세요! 🎭💫",
        "좋은 하루 되세요! 공연으로 행복한 시간 보내세요! 🌟🎪",
        "또 오세요! 언제든지 공연 추천해드릴게요! 🎵😊"
    ]
    
    return {
        'message': random.choice(farewells),
        'suggestions': []
    }

def generate_thanks_response(context):
    """감사 응답 생성"""
    thanks_responses = [
        "천만에요! 도움이 되어서 기뻐요! 😊✨",
        "별 말씀을요! 더 좋은 공연을 찾아드릴게요! 🎭💫",
        "감사합니다! 저도 즐거웠어요! 🎪🌟",
        "도움이 되었다니 다행이에요! 또 찾아주세요! 🎵💖"
    ]
    
    return {
        'message': random.choice(thanks_responses),
        'suggestions': ['더 많은 공연 보기', '인기 공연 보기']
    }

def generate_help_response(context):
    """도움말 응답 생성"""
    help_message = """🎭 **공연 AI 어시스턴트 사용법** 🎭

**기본 검색:**
• "서울에서 뮤지컬 추천해줘"
• "5만원대 공연 찾아줘"
• "이번 주말에 볼만한 것"

**고급 검색:**
• "강남에서 3-5만원대 다음주 뮤지컬"
• "뮤지컬 말고 연극으로"
• "20대가 좋아할 만한 로맨틱한 공연"

**특별 검색:**
• "무료 공연"
• "인기 공연"
• "곧 끝나는 공연"

**대화:**
• "안녕하세요" - 인사
• "고마워" - 감사
• "도움" - 사용법

무엇이든 편하게 물어보세요! 🎪✨"""

    return {
        'message': help_message,
        'suggestions': ['인기 공연 보기', '전체 공연 보기', '무료 공연 보기']
    }

def generate_complaint_response(context):
    """불만 응답 생성"""
    complaint_responses = [
        "아쉽네요... 😔 다른 조건으로 찾아드릴까요?",
        "죄송해요! 더 좋은 공연을 찾아보겠습니다! 🤗",
        "그렇다면 다른 장르나 지역은 어떠세요? 💡",
        "아쉽지만, 다른 옵션도 많아요! 다시 찾아볼까요? ✨"
    ]
    
    return {
        'message': random.choice(complaint_responses),
        'suggestions': ['다른 카테고리 보기', '다른 지역 보기', '전체 공연 보기']
    }

def generate_praise_response(context):
    """칭찬 응답 생성"""
    praise_responses = [
        "정말 기뻐요! 더 좋은 공연을 찾아드릴게요! 🎉✨",
        "감사합니다! 저도 즐거워요! 🎭💫",
        "좋아하신다니 다행이에요! 더 추천해드릴게요! 🎪🌟",
        "와! 정말 기뻐요! 또 찾아주세요! 🎵💖"
    ]
    
    return {
        'message': random.choice(praise_responses),
        'suggestions': ['더 많은 공연 보기', '인기 공연 보기', '새로운 공연 보기']
    }

def generate_search_response(user_query, performances, context, follow_up):
    """검색 결과 응답 생성 (지능형)"""
    conversation_context = context.get_conversation_context()
    
    # 데이터 분석
    performance_data = analyze_performance_data()
    
    if not performances:
        return generate_no_result_response(user_query, context, performance_data)
    
    # 개인화된 추천 추가
    user_preferences = conversation_context['user_preferences']
    personalized_recs = generate_personalized_recommendations(user_preferences, {})
    
    # 응답 생성
    if len(performances) == 1:
        return generate_single_result_response(performances[0], context, follow_up)
    else:
        return generate_multiple_results_response(performances, context, follow_up, personalized_recs)

def generate_no_result_response(user_query, context, performance_data):
    """검색 결과 없음 응답"""
    conversation_context = context.get_conversation_context()
    
    # 데이터 기반 제안
    suggestions = []
    if performance_data:
        if performance_data['categories']:
            top_category = performance_data['categories'][0][0]
            suggestions.append(f"{top_category} 공연 보기")
        
        if performance_data['popular']:
            suggestions.append("인기 공연 보기")
        
        if performance_data['recent']:
            suggestions.append("최신 공연 보기")
    
    # 개인화된 제안
    if conversation_context['user_preferences']['top_categories']:
        top_category = conversation_context['user_preferences']['top_categories'][0][0]
        suggestions.append(f"{top_category} 공연 더 보기")
    
    no_result_messages = [
        "아쉽게도 조건에 맞는 공연을 찾지 못했어요. 😅\n\n다른 조건으로 다시 물어보시거나, 전체 공연 목록을 확인해보세요!",
        "죄송해요! 해당 조건의 공연이 없네요. 🤔\n\n지역이나 날짜를 바꿔서 검색해보시는 건 어떨까요?",
        "음... 그런 조건의 공연은 아직 등록되지 않았어요. 😊\n\n전체 공연 목록에서 마음에 드는 공연을 찾아보세요!",
        "조건을 조금 바꿔서 다시 물어보시는 건 어떨까요? 💡\n\n다른 키워드로 검색해보시면 좋은 공연을 찾을 수 있을 거예요!"
    ]
    
    return {
        'message': random.choice(no_result_messages),
        'suggestions': suggestions[:5]
    }

def generate_single_result_response(performance, context, follow_up):
    """단일 결과 응답 생성"""
    conversation_context = context.get_conversation_context()
    
    # 카테고리별 맞춤 응답
    category_emojis = {
        '뮤지컬': '🎵',
        '연극': '🎬', 
        '콘서트': '🎤',
        '클래식': '🎻',
        '오페라': '🎭',
        '발레': '🩰',
        '무용': '💃',
        '전시': '🖼️',
        '축제': '🎪'
    }
    
    emoji = category_emojis.get(performance.category, '🎭')
    
    # 개인화된 메시지
    personalization = ""
    if conversation_context['user_preferences']['top_categories']:
        top_category = conversation_context['user_preferences']['top_categories'][0][0]
        if performance.category and top_category in performance.category:
            personalization = "\n\n이런 종류의 공연을 좋아하시는 것 같아요! 😊"
    
    # 가격대별 반응
    price_reaction = ""
    if performance.price:
        if '무료' in performance.price:
            price_reaction = "\n\n무료라니 정말 좋네요! 🎉"
        elif any(x in performance.price for x in ['1만', '2만']):
            price_reaction = "\n\n합리적인 가격이에요! 👍"
        elif any(x in performance.price for x in ['5만', '6만']):
            price_reaction = "\n\n퀄리티 대비 괜찮은 가격이에요! 💎"
    
    # 평점 시스템
    likes = performance.likes or 0
    if likes > 50:
        stars = "★★★★★"
        rating_text = "매우 인기!"
    elif likes > 30:
        stars = "★★★★☆"
        rating_text = "인기 공연!"
    elif likes > 10:
        stars = "★★★☆☆"
        rating_text = "괜찮은 공연!"
    else:
        stars = "★★☆☆☆"
        rating_text = "새로운 공연!"
    
    message = f"🎭 **{performance.title}**{personalization}\n\n"
    message += f"{emoji} **장르**: {performance.category or '공연'}\n"
    message += f"📍 **장소**: {performance.location}\n"
    message += f"📅 **날짜**: {performance.date}\n"
    message += f"💰 **가격**: {performance.price}\n"
    message += f"⭐ **평점**: {stars} ({rating_text}){price_reaction}\n\n"
    
    if follow_up:
        message += "이 공연은 어떠세요? 더 자세한 정보를 원하시면 공연 제목을 클릭해보세요! 🎪"
    else:
        message += "정말 멋진 공연이네요! 더 자세한 정보를 원하시면 공연 제목을 클릭해보세요! ✨"
    
    return {
        'message': message,
        'performances': [performance],
        'suggestions': ['더 많은 공연 보기', '비슷한 공연 보기', '인기 공연 보기']
    }

def generate_multiple_results_response(performances, context, follow_up, personalized_recs):
    """다중 결과 응답 생성"""
    conversation_context = context.get_conversation_context()
    
    # 개인화된 인사
    personalization = ""
    if conversation_context['user_preferences']['interaction_count'] > 3:
        personalization = "오랜 고객님이시네요! "
    
    message = f"{personalization}🎭 조건에 맞는 공연을 **{len(performances)}개** 찾았어요!\n\n"
    
    # 상위 3개 공연 상세 표시
    category_emojis = {
        '뮤지컬': '🎵',
        '연극': '🎬', 
        '콘서트': '🎤',
        '클래식': '🎻',
        '오페라': '🎭',
        '발레': '🩰',
        '무용': '💃',
        '전시': '🖼️',
        '축제': '🎪'
    }
    
    for i, performance in enumerate(performances[:3], 1):
        emoji = category_emojis.get(performance.category, '🎭')
        message += f"**{i}. {emoji} {performance.title}**\n"
        message += f"   📍 {performance.location} | 📅 {performance.date} | 💰 {performance.price}\n\n"
    
    if len(performances) > 3:
        remaining = len(performances) - 3
        message += f"...그 외 **{remaining}개**의 공연이 더 있어요! 🎪\n\n"
    
    # 개인화된 추천 추가
    if personalized_recs and len(personalized_recs) > 0:
        message += "💡 **개인화 추천**:\n"
        for i, rec in enumerate(personalized_recs[:2], 1):
            emoji = category_emojis.get(rec.category, '🎭')
            message += f"   {emoji} {rec.title} ({rec.category})\n"
        message += "\n"
    
    # 상황별 메시지
    if len(performances) >= 5:
        message += "정말 다양한 공연들이 있네요! 마음에 드는 공연을 선택해보세요! ✨"
    else:
        message += "더 자세한 정보를 원하시면 공연 제목을 클릭해보세요! 🎪"
    
    # 추천 제안
    suggestions = ['더 많은 공연 보기', '다른 조건으로 검색', '인기 공연 보기']
    
    # 조건별 추가 제안
    if any('무료' in p.price for p in performances if p.price):
        suggestions.append('무료 공연 더 보기')
    if any('뮤지컬' in p.category for p in performances if p.category):
        suggestions.append('뮤지컬 더 보기')
    if any('콘서트' in p.category for p in performances if p.category):
        suggestions.append('콘서트 더 보기')
    
    return {
        'message': message,
        'performances': performances,
        'suggestions': suggestions[:5]
    }

def generate_ai_response(user_query, performances):
    """AI 응답 생성 (ChatGPT 수준 고도화)"""
    # 컨텍스트 기반 응답 생성
    response = generate_contextual_response(user_query, performances, ai_context)
    
    # 대화 기록 추가
    ai_context.add_interaction(user_query, response, performances)
    
    return response
    
    no_result_templates = [
        "아쉽게도 조건에 맞는 공연을 찾지 못했어요. 😅",
        "죄송해요! 해당 조건의 공연이 없네요. 🤔",
        "음... 그런 조건의 공연은 아직 등록되지 않았어요. 😊",
        "조건을 조금 바꿔서 다시 물어보시는 건 어떨까요? 💡"
    ]
    
    suggestion_templates = [
        "다른 조건으로 다시 물어보시거나, 전체 공연 목록을 확인해보세요!",
        "지역이나 날짜를 바꿔서 검색해보시는 건 어떨까요?",
        "전체 공연 목록에서 마음에 드는 공연을 찾아보세요!",
        "다른 키워드로 검색해보시면 좋은 공연을 찾을 수 있을 거예요!"
    ]
    
    if not performances:
        greeting = random.choice(greeting_templates)
        no_result = random.choice(no_result_templates)
        suggestion = random.choice(suggestion_templates)
        
        return {
            'message': f"{greeting}\n\n{no_result}\n\n{suggestion}",
            'suggestions': [
                '전체 공연 보기',
                '다른 지역 검색',
                '다른 가격대 검색',
                '다른 날짜 검색',
                '인기 공연 보기'
            ]
        }
    
    # 성공적인 검색 결과 응답
    greeting = random.choice(greeting_templates)
    
    if len(performances) == 1:
        performance = performances[0]
        
        # 공연별 맞춤 응답
        if performance.category and '뮤지컬' in performance.category:
            category_emoji = "🎵"
            category_text = "멋진 뮤지컬"
        elif performance.category and '연극' in performance.category:
            category_emoji = "🎬"
            category_text = "감동적인 연극"
        elif performance.category and '콘서트' in performance.category:
            category_emoji = "🎤"
            category_text = "신나는 콘서트"
        elif performance.category and '클래식' in performance.category:
            category_emoji = "🎻"
            category_text = "우아한 클래식"
        else:
            category_emoji = "🎭"
            category_text = "흥미로운 공연"
        
        # 가격대별 반응
        price_reaction = ""
        if performance.price and '무료' in performance.price:
            price_reaction = "무료라니 정말 좋네요! 🎉"
        elif performance.price and any(x in performance.price for x in ['1만', '2만']):
            price_reaction = "합리적인 가격이에요! 👍"
        elif performance.price and any(x in performance.price for x in ['5만', '6만']):
            price_reaction = "퀄리티 대비 괜찮은 가격이에요! 💎"
        
        message = f"{greeting}\n\n"
        message += f"{category_emoji} **{performance.title}**\n\n"
        message += f"📍 **장소**: {performance.location}\n"
        message += f"📅 **날짜**: {performance.date}\n"
        message += f"💰 **가격**: {performance.price}\n"
        
        # 평점 표시 (좋아요 수 기반)
        likes = performance.likes or 0
        if likes > 50:
            stars = "★★★★★"
            rating_text = "매우 인기!"
        elif likes > 30:
            stars = "★★★★☆"
            rating_text = "인기 공연!"
        elif likes > 10:
            stars = "★★★☆☆"
            rating_text = "괜찮은 공연!"
        else:
            stars = "★★☆☆☆"
            rating_text = "새로운 공연!"
        
        message += f"⭐ **평점**: {stars} ({rating_text})\n\n"
        
        if price_reaction:
            message += f"{price_reaction}\n\n"
        
        message += f"이 {category_text}은 어떠세요? 더 자세한 정보를 원하시면 공연 제목을 클릭해보세요! 🎪"
        
    else:
        # 여러 공연 결과
        message = f"{greeting}\n\n"
        message += f"🎭 조건에 맞는 공연을 **{len(performances)}개** 찾았어요!\n\n"
        
        # 상위 3개 공연 상세 표시
        for i, performance in enumerate(performances[:3], 1):
            # 카테고리별 이모지
            if performance.category and '뮤지컬' in performance.category:
                emoji = "🎵"
            elif performance.category and '연극' in performance.category:
                emoji = "🎬"
            elif performance.category and '콘서트' in performance.category:
                emoji = "🎤"
            elif performance.category and '클래식' in performance.category:
                emoji = "🎻"
            else:
                emoji = "🎭"
            
            message += f"**{i}. {emoji} {performance.title}**\n"
            message += f"   📍 {performance.location} | 📅 {performance.date} | 💰 {performance.price}\n\n"
        
        if len(performances) > 3:
            remaining = len(performances) - 3
            message += f"...그 외 **{remaining}개**의 공연이 더 있어요! 🎪\n\n"
        
        # 추천 메시지
        if len(performances) >= 5:
            message += "정말 다양한 공연들이 있네요! 마음에 드는 공연을 선택해보세요! ✨"
        else:
            message += "더 자세한 정보를 원하시면 공연 제목을 클릭해보세요! 🎪"
    
    # 추천 제안
    suggestions = []
    if len(performances) > 0:
        suggestions.extend([
            '더 많은 공연 보기',
            '다른 조건으로 검색',
            '인기 공연 보기'
        ])
        
        # 조건별 추가 제안
        if any('무료' in p.price for p in performances if p.price):
            suggestions.append('무료 공연 더 보기')
        if any('뮤지컬' in p.category for p in performances if p.category):
            suggestions.append('뮤지컬 더 보기')
        if any('콘서트' in p.category for p in performances if p.category):
            suggestions.append('콘서트 더 보기')
    
    return {
        'message': message,
        'performances': performances,
        'suggestions': suggestions[:5]  # 최대 5개 제안
    }

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """AI 채팅 API (ChatGPT 수준)"""
    try:
        data = request.get_json()
        user_query = data.get('message', '').strip()
        
        if not user_query:
            return jsonify({
                'success': False,
                'message': '메시지를 입력해주세요.'
            })
        
        # 사용자 의도 분석
        intent_analysis = understand_user_intent(user_query, ai_context)
        
        # 검색이 필요한 경우에만 공연 검색
        if intent_analysis['intent'] in ['search', 'question']:
            # 사용자 질문 파싱
            conditions = parse_user_query(user_query)
            
            # 공연 검색
            performances = search_performances_by_ai(conditions)
        else:
            # 대화형 응답의 경우 공연 검색 없음
            performances = []
        
        # AI 응답 생성
        response = generate_ai_response(user_query, performances)
        
        # 디버깅 정보 추가 (개발용)
        if app.debug:
            response['debug'] = {
                'intent': intent_analysis['intent'],
                'follow_up': intent_analysis['follow_up'],
                'conditions': conditions if intent_analysis['intent'] in ['search', 'question'] else None,
                'context': ai_context.get_conversation_context()
            }
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        app.logger.error(f"AI 채팅 오류: {e}")
        return jsonify({
            'success': False,
            'message': '죄송해요! 잠시 문제가 생겼어요. 다시 시도해주세요! 😅'
        })

if __name__ == "__main__":
    try:
        # 데이터베이스 테이블 생성 시도 (무한 루프 방지)
        logger.info("Starting application initialization...")
        create_tables()
        create_sample_data_if_needed()  # 샘플 계정 자동 생성
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Server will start without database initialization. Some features may not work.")
        # 데이터베이스 초기화 실패해도 서버는 시작
        pass
    
    # 무한 루프 방지를 위한 안전한 서버 시작
    try:
        app.run(debug=False, host='0.0.0.0', port=10000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}") 