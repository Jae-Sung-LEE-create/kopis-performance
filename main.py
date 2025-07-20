from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, jsonify, session, g, send_file, make_response
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, text
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import uuid
import traceback
import cloudinary
import cloudinary.uploader
import requests
import time
import xml.etree.ElementTree as ET

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

# 데이터 분석을 위한 새로운 모델들

# 사용자 행동 추적 모델
class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 비로그인 사용자도 추적
    session_id = db.Column(db.String(100), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # view, like, comment, search, etc.
    performance_id = db.Column(db.Integer, db.ForeignKey('performance.id'), nullable=True)
    category = db.Column(db.String(50))
    location = db.Column(db.String(100))
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=func.now())

# A/B 테스트 모델
class ABTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    test_type = db.Column(db.String(50), nullable=False)  # title, image, description, price
    version_a = db.Column(db.Text, nullable=False)
    version_b = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, paused, completed
    created_at = db.Column(db.DateTime, default=func.now())

# A/B 테스트 결과 모델
class ABTestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('ab_test.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(10), nullable=False)  # A or B
    action = db.Column(db.String(50), nullable=False)  # view, click, conversion
    created_at = db.Column(db.DateTime, default=func.now())

# 트렌드 분석 모델
class TrendAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    analysis_date = db.Column(db.Date, nullable=False)
    total_performances = db.Column(db.Integer, default=0)
    total_views = db.Column(db.Integer, default=0)
    total_likes = db.Column(db.Integer, default=0)
    total_comments = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)
    growth_rate = db.Column(db.Float, default=0.0)
    hot_keywords = db.Column(db.Text)  # JSON 형태로 저장
    created_at = db.Column(db.DateTime, default=func.now())

# 리포트 모델
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly, custom
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    data = db.Column(db.Text)  # JSON 형태로 저장
    file_path = db.Column(db.String(300))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

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
    """데이터베이스 테이블 생성"""
    max_retries = 2  # 3에서 2로 줄임
    retry_delay = 1  # 2에서 1로 줄임
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                logger.info(f"Creating database tables... (attempt {attempt + 1}/{max_retries})")
                
                # Performance 테이블에 필수 컬럼 체크
                result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='performance'"))
                if result.fetchone():
                    result = db.session.execute(text("PRAGMA table_info(performance)"))
                    columns = [row[1] for row in result.fetchall()]
                    required = {'address', 'purchase_methods'}
                    if not required.issubset(set(columns)):
                        logger.warning("Performance table missing required columns. Dropping and recreating tables...")
                        db.drop_all()
                # 기존 테이블에 address 컬럼이 있는지 확인
                try:
                    # Performance 테이블이 존재하는지 확인
                    result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='performance'"))
                    if result.fetchone():
                        # address 컬럼이 있는지 확인
                        result = db.session.execute(text("PRAGMA table_info(performance)"))
                        columns = [row[1] for row in result.fetchall()]
                        if 'address' not in columns:
                            logger.warning("Performance table exists but missing 'address' column. Dropping and recreating tables...")
                            db.drop_all()
                            logger.info("All tables dropped successfully")
                except Exception as schema_check_error:
                    logger.info(f"Schema check failed (this is normal for new databases): {schema_check_error}")
                
                # 테이블 생성 (간소화된 연결 테스트)
                db.create_all()
                logger.info("Database tables created successfully!")
                
                return  # 성공하면 함수 종료
                
        except Exception as e:
            logger.error(f"Database creation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All database creation attempts failed!")
                raise

def create_sample_data_if_needed():
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

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# 기본 라우트들
@app.route('/')
def home():
    """홈페이지"""
    try:
        logger.info("Accessing home page")
        
        # 사용자 활동 추적
        track_user_activity('view_home')
        
        # 필터 파라미터 받기
        main_category = request.args.get('main_category')
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        date_filter = request.args.get('date_filter', '')
        location = request.args.get('location', '')
        price_filter = request.args.get('price_filter', '')
        price_range = request.args.get('price_range', '')
        price_min = request.args.get('price_min', '')
        price_max = request.args.get('price_max', '')
        
        logger.info(f"Filters - Main Category: {main_category}, Category: {category}, Search: {search}, Date: {date_filter}, Location: {location}, Price: {price_filter}")
        
        # 추천 시스템 파라미터
        recommendation_type = request.args.get('recommendation', '')
        
        # KOPIS 데이터 연동 파라미터
        kopis_sync = request.args.get('kopis_sync', 'false').lower() == 'true'
        
        # 데이터베이스 연결 확인 (간소화)
        try:
            # 기본 쿼리 (승인된 공연만)
            query = Performance.query.filter_by(is_approved=True)
            
            # 메인 카테고리 필터
            if main_category and main_category != '전체':
                query = query.filter_by(main_category=main_category)
            
            # 세부 카테고리 필터
            if category and category != '전체':
                query = query.filter_by(category=category)
            
            # 검색 필터 (제목 또는 팀명)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    db.or_(
                        Performance.title.ilike(search_term),
                        Performance.group_name.ilike(search_term)
                    )
                )
            
            # 날짜 필터
            if date_filter:
                from datetime import datetime, timedelta
                today = datetime.now().date()
                
                def parse_performance_date(date_str):
                    """공연 날짜 문자열을 파싱하여 날짜 객체로 변환"""
                    if not date_str:
                        return None
                    
                    # 다양한 날짜 형식 처리
                    date_formats = [
                        '%Y-%m-%d',      # 2024-12-15
                        '%Y.%m.%d',      # 2024.12.15
                        '%Y/%m/%d',      # 2024/12/15
                        '%Y년 %m월 %d일', # 2024년 12월 15일
                        '%Y년%m월%d일',   # 2024년12월15일
                        '%Y-%m-%d ~ %Y-%m-%d',  # 2024-12-15 ~ 2024-12-20
                        '%Y.%m.%d ~ %Y.%m.%d',  # 2024.12.15 ~ 2024.12.20
                    ]
                    
                    # 범위 형식 처리 (시작일만 추출)
                    if ' ~ ' in date_str:
                        date_str = date_str.split(' ~ ')[0].strip()
                    
                    for fmt in date_formats:
                        try:
                            return datetime.strptime(date_str, fmt).date()
                        except ValueError:
                            continue
                    
                    # 숫자만 추출해서 시도
                    import re
                    numbers = re.findall(r'\d+', date_str)
                    if len(numbers) >= 3:
                        try:
                            year = int(numbers[0])
                            month = int(numbers[1])
                            day = int(numbers[2])
                            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                                return datetime(year, month, day).date()
                        except ValueError:
                            pass
                    
                    return None
                
                def is_date_in_range(performance_date, start_date, end_date):
                    """공연 날짜가 지정된 범위 내에 있는지 확인"""
                    if not performance_date:
                        return False
                    
                    # 공연 날짜가 범위 내에 있는지 확인
                    return start_date <= performance_date <= end_date
                
                if date_filter == 'this_week':
                    # 이번 주 (월요일부터 일요일까지)
                    days_since_monday = today.weekday()
                    monday = today - timedelta(days=days_since_monday)
                    sunday = monday + timedelta(days=6)
                    
                    # Python에서 필터링 (날짜 파싱 필요)
                    all_performances = query.order_by(Performance.created_at.desc()).all()
                    approved_performances = []
                    
                    for performance in all_performances:
                        perf_date = parse_performance_date(performance.date)
                        if perf_date and is_date_in_range(perf_date, monday, sunday):
                            approved_performances.append(performance)
                    
                    logger.info(f"This week filter applied: {monday} ~ {sunday}, found {len(approved_performances)} performances")
                    
                elif date_filter == 'this_month':
                    # 이번 달
                    first_day = today.replace(day=1)
                    if today.month == 12:
                        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                    
                    # Python에서 필터링
                    all_performances = query.order_by(Performance.created_at.desc()).all()
                    approved_performances = []
                    
                    for performance in all_performances:
                        perf_date = parse_performance_date(performance.date)
                        if perf_date and is_date_in_range(perf_date, first_day, last_day):
                            approved_performances.append(performance)
                    
                    logger.info(f"This month filter applied: {first_day} ~ {last_day}, found {len(approved_performances)} performances")
                    
                elif date_filter == 'next_month':
                    # 다음 달
                    if today.month == 12:
                        first_day = today.replace(year=today.year + 1, month=1, day=1)
                        last_day = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
                    else:
                        first_day = today.replace(month=today.month + 1, day=1)
                        if today.month == 11:
                            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                        else:
                            last_day = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
                    
                    # Python에서 필터링
                    all_performances = query.order_by(Performance.created_at.desc()).all()
                    approved_performances = []
                    
                    for performance in all_performances:
                        perf_date = parse_performance_date(performance.date)
                        if perf_date and is_date_in_range(perf_date, first_day, last_day):
                            approved_performances.append(performance)
                    
                    logger.info(f"Next month filter applied: {first_day} ~ {last_day}, found {len(approved_performances)} performances")
                
                else:
                    # 날짜 필터가 적용되지 않은 경우 기본 쿼리 사용
                    approved_performances = query.order_by(Performance.created_at.desc()).all()
            else:
                # 날짜 필터가 없는 경우 기본 쿼리 사용
                approved_performances = query.order_by(Performance.created_at.desc()).all()
            
            # 지역 필터 - 주소에서 지역 감지하여 필터링
            if location:
                # 지역별 키워드 매핑
                region_keywords = {
                    '서울특별시': ['서울특별시', '서울시', '서울', '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'],
                    '경기도': ['경기도', '경기', '수원시', '성남시', '의정부시', '안양시', '부천시', '광명시', '평택시', '동두천시', '안산시', '고양시', '과천시', '구리시', '남양주시', '오산시', '시흥시', '군포시', '의왕시', '하남시', '용인시', '파주시', '이천시', '안성시', '김포시', '화성시', '광주시', '여주시'],
                    '강원도': ['강원도', '강원', '춘천시', '원주시', '강릉시', '동해시', '태백시', '속초시', '삼척시'],
                    '인천광역시': ['인천광역시', '인천시', '인천'],
                    '충청남도': ['충청남도', '충남', '천안시', '공주시', '보령시', '아산시', '서산시', '논산시', '계룡시', '당진시'],
                    '충청북도': ['충청북도', '충북', '청주시', '충주시', '제천시'],
                    '세종특별자치시': ['세종특별자치시', '세종시', '세종'],
                    '대전광역시': ['대전광역시', '대전시', '대전'],
                    '경상북도': ['경상북도', '경북', '포항시', '경주시', '김천시', '안동시', '구미시', '영주시', '영천시', '상주시', '문경시', '경산시'],
                    '대구광역시': ['대구광역시', '대구시', '대구'],
                    '전라북도': ['전라북도', '전북', '전주시', '군산시', '익산시', '정읍시', '남원시', '김제시'],
                    '경상남도': ['경상남도', '경남', '창원시', '진주시', '통영시', '사천시', '김해시', '밀양시', '거제시', '양산시'],
                    '울산광역시': ['울산광역시', '울산시', '울산'],
                    '부산광역시': ['부산광역시', '부산시', '부산'],
                    '광주광역시': ['광주광역시', '광주시', '광주'],
                    '전라남도': ['전라남도', '전남', '목포시', '여수시', '순천시', '나주시', '광양시'],
                    '제주도': ['제주도', '제주특별자치도', '제주시', '제주', '서귀포시']
                }
                
                if location in region_keywords:
                    # 해당 지역의 키워드들로 주소 필터링
                    keywords = region_keywords[location]
                    filtered_performances = []
                    
                    for performance in approved_performances:
                        address = performance.address or ''
                        location_name = performance.location or ''
                        
                        # 주소나 장소명에 키워드가 포함되어 있는지 확인
                        for keyword in keywords:
                            if keyword in address or keyword in location_name:
                                filtered_performances.append(performance)
                                break
                    
                    approved_performances = filtered_performances
                    logger.info(f"Region filter '{location}' applied, found {len(approved_performances)} performances")
            
            # 가격 필터 - Python에서 처리
            if price_filter:
                filtered_performances = []
                
                for performance in approved_performances:
                    price = performance.price or ''
                    
                    if price_filter == 'free':
                        if '무료' in price.lower() or 'free' in price.lower() or price == '무료':
                            filtered_performances.append(performance)
                    elif price_filter == 'paid':
                        if not ('무료' in price.lower() or 'free' in price.lower()) and price != '무료':
                            filtered_performances.append(performance)
                    elif price_filter == 'discount':
                        if any(keyword in price.lower() for keyword in ['할인', 'discount', '학생', 'student']):
                            filtered_performances.append(performance)
                
                approved_performances = filtered_performances
                logger.info(f"Price filter '{price_filter}' applied, found {len(approved_performances)} performances")
            
            # 가격 범위 필터 - price_range 파라미터 처리
            if price_range:
                if price_range == 'custom':
                    # 사용자 지정 범위는 price_min, price_max로 처리됨
                    pass
                else:
                    # 미리 정의된 범위 파싱
                    try:
                        range_min, range_max = price_range.split('-')
                        price_min = range_min
                        price_max = range_max
                    except ValueError:
                        logger.warning(f"Invalid price_range format: {price_range}")
                        price_range = ''
            
            # 가격 범위 필터 - Python에서 처리 (가격 문자열 파싱 필요)
            if price_min or price_max:
                def filter_by_price_range(performance):
                    if not performance.price:
                        return False
                    
                    # 가격에서 숫자만 추출
                    import re
                    price_str = performance.price.replace(',', '').replace('원', '').replace('₩', '').strip()
                    
                    # 무료인 경우
                    if '무료' in performance.price.lower() or 'free' in performance.price.lower():
                        price_num = 0
                    else:
                        # 숫자만 추출
                        numbers = re.findall(r'\d+', price_str)
                        if not numbers:
                            return False
                        price_num = int(numbers[0])
                    
                    # 범위 체크
                    if price_min and price_num < int(price_min):
                        return False
                    if price_max and price_num > int(price_max):
                        return False
                    
                    return True
                
                # 현재까지의 결과에 가격 범위 필터 적용
                filtered_performances = [p for p in approved_performances if filter_by_price_range(p)]
                approved_performances = filtered_performances
                
                logger.info(f"Price range filter: {price_min or '0'} ~ {price_max or '∞'} applied, found {len(approved_performances)} performances")
            
            logger.info(f"Final result: {len(approved_performances)} performances after all filters")
            
            # 템플릿 렌더링
            response = make_response(render_template("index.html", 
                                 performances=approved_performances, 
                                 selected_main_category=main_category,
                                 selected_category=category,
                                 search=search,
                                 date_filter=date_filter,
                                 location=location,
                                 price_filter=price_filter,
                                 price_range=price_range,
                                 price_min=price_min,
                                 price_max=price_max))
            
            # 캐시 무효화 헤더 추가 (뒤로가기 문제 해결)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            # 데이터베이스 오류 시 기본 페이지 반환
            return create_error_page("데이터베이스 연결 오류", "잠시 후 다시 시도해주세요.")
            
    except Exception as e:
        logger.error(f"Unexpected error in home route: {e}")
        return create_error_page("서버 오류", "잠시 후 다시 시도해주세요.")

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
    """관리자 패널 - 승인 대기 중인 공연 관리"""
    # 관리자 권한 확인
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
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
    
    # 템플릿 렌더링
    response = make_response(render_template("admin.html", 
                         pending_performances=pending_performances,
                         approved_performances=approved_performances,
                         filtered_pending_count=filtered_pending_count,
                         filtered_approved_count=filtered_approved_count,
                         filtered_rejected_count=filtered_rejected_count,
                         filtered_total_count=filtered_total_count,
                         monthly_chart_data=monthly_chart_data,
                         category_chart_data=category_chart_data))
    
    # 캐시 무효화 헤더 추가
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
    performance = Performance.query.get(performance_id)
    
    if not performance or not performance.is_approved:
        return redirect(url_for('home'))
    
    # 사용자 활동 추적
    track_user_activity('view_performance', performance_id, performance.category, performance.location)
    
    return render_template("performance_detail.html", performance=performance)

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
            track_user_activity('unlike', performance_id, performance.category, performance.location)
        else:
            # 좋아요 추가
            new_like = UserLike(user_id=current_user.id, performance_id=performance_id)
            db.session.add(new_like)
            performance.likes += 1
            liked = True
            track_user_activity('like', performance_id, performance.category, performance.location)
        
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

@app.route('/kopis-sync')
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

# ============================================================================
# 데이터 분석 및 인사이트 라우트들
# ============================================================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """관리자 실시간 대시보드"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        # 실시간 데이터 수집
        dashboard_data = get_real_time_dashboard_data()
        audience_data = get_audience_analysis_data()
        trend_data = get_trend_prediction_data()
        
        return render_template('admin_dashboard.html',
                             dashboard_data=dashboard_data,
                             audience_data=audience_data,
                             trend_data=trend_data)
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash('대시보드 로딩 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/audience-analysis')
@login_required
def audience_analysis():
    """관객 분석 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        audience_data = get_audience_analysis_data()
        return render_template('audience_analysis.html', data=audience_data)
    except Exception as e:
        logger.error(f"Audience analysis error: {e}")
        flash('관객 분석 로딩 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/trend-prediction')
@login_required
def trend_prediction():
    """트렌드 예측 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        trend_data = get_trend_prediction_data()
        return render_template('trend_prediction.html', data=trend_data)
    except Exception as e:
        logger.error(f"Trend prediction error: {e}")
        flash('트렌드 예측 로딩 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/ab-testing')
@login_required
def ab_testing():
    """A/B 테스트 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        ab_data = get_ab_test_data()
        return render_template('ab_testing.html', data=ab_data)
    except Exception as e:
        logger.error(f"A/B testing error: {e}")
        flash('A/B 테스트 로딩 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/performance-analytics')
@login_required
def performance_analytics():
    """공연별 성과 분석 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        analytics_data = get_performance_analytics()
        return render_template('performance_analytics.html', data=analytics_data)
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        flash('성과 분석 로딩 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/reports')
@login_required
def reports():
    """리포트 관리 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        # 기존 리포트 목록
        reports_list = Report.query.filter_by(created_by=current_user.id).order_by(Report.created_at.desc()).all()
        return render_template('reports.html', reports=reports_list)
    except Exception as e:
        logger.error(f"Reports error: {e}")
        flash('리포트 로딩 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/create-report', methods=['POST'])
@login_required
def create_report():
    """리포트 생성"""
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    try:
        report_type = request.form.get('report_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        if not all([report_type, start_date_str, end_date_str]):
            return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        report_id = generate_report(report_type, start_date, end_date, current_user.id)
        
        if report_id:
            flash('리포트가 성공적으로 생성되었습니다.', 'success')
            return jsonify({'success': True, 'report_id': report_id})
        else:
            return jsonify({'error': '리포트 생성에 실패했습니다.'}), 500
            
    except Exception as e:
        logger.error(f"Create report error: {e}")
        return jsonify({'error': '리포트 생성 중 오류가 발생했습니다.'}), 500

@app.route('/admin/download-report/<int:report_id>')
@login_required
def download_report(report_id):
    """리포트 다운로드"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    try:
        report = Report.query.get_or_404(report_id)
        
        # JSON 데이터를 CSV로 변환
        import csv
        from io import StringIO
        
        data = json.loads(report.data)
        output = StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        writer.writerow(['리포트 정보'])
        writer.writerow(['리포트 타입', report.report_type])
        writer.writerow(['시작일', report.start_date])
        writer.writerow(['종료일', report.end_date])
        writer.writerow(['생성일', report.created_at])
        writer.writerow([])
        
        # 대시보드 데이터
        if 'dashboard_data' in data:
            writer.writerow(['실시간 대시보드'])
            dashboard = data['dashboard_data']
            writer.writerow(['오늘 등록된 공연', dashboard.get('today_performances', 0)])
            writer.writerow(['실시간 방문자', dashboard.get('recent_visitors', 0)])
            writer.writerow(['예매율', f"{dashboard.get('booking_rate', 0)}%"])
            writer.writerow(['인기 카테고리', dashboard.get('popular_category', '기타')])
            writer.writerow([])
        
        # 성과 데이터
        if 'performance_data' in data and 'performance_data' in data['performance_data']:
            writer.writerow(['공연별 성과'])
            writer.writerow(['제목', '카테고리', '조회수', '좋아요', '댓글', '전환율'])
            for perf in data['performance_data']['performance_data']:
                writer.writerow([
                    perf.get('title', ''),
                    perf.get('category', ''),
                    perf.get('views', 0),
                    perf.get('likes', 0),
                    perf.get('comments', 0),
                    f"{perf.get('conversion_rate', 0)}%"
                ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=report_{report_id}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Download report error: {e}")
        flash('리포트 다운로드 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('reports'))

@app.route('/admin/create-ab-test', methods=['POST'])
@login_required
def create_ab_test():
    """A/B 테스트 생성"""
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        test_type = request.form.get('test_type')
        version_a = request.form.get('version_a')
        version_b = request.form.get('version_b')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        if not all([name, test_type, version_a, version_b, start_date_str, end_date_str]):
            return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M')
        
        ab_test = ABTest(
            name=name,
            description=description,
            test_type=test_type,
            version_a=version_a,
            version_b=version_b,
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(ab_test)
        db.session.commit()
        
        flash('A/B 테스트가 성공적으로 생성되었습니다.', 'success')
        return jsonify({'success': True, 'test_id': ab_test.id})
        
    except Exception as e:
        logger.error(f"Create A/B test error: {e}")
        return jsonify({'error': 'A/B 테스트 생성 중 오류가 발생했습니다.'}), 500

@app.route('/admin/track-ab-test', methods=['POST'])
def track_ab_test():
    """A/B 테스트 결과 추적"""
    try:
        test_id = request.form.get('test_id')
        version = request.form.get('version')
        action = request.form.get('action')
        
        if not all([test_id, version, action]):
            return jsonify({'error': '필수 정보가 누락되었습니다.'}), 400
        
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        result = ABTestResult(
            test_id=test_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=session_id,
            version=version,
            action=action
        )
        
        db.session.add(result)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Track A/B test error: {e}")
        return jsonify({'error': 'A/B 테스트 추적 중 오류가 발생했습니다.'}), 500

@app.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """실시간 대시보드 데이터 API"""
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    try:
        dashboard_data = get_real_time_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"API dashboard data error: {e}")
        return jsonify({'error': '데이터 로딩 중 오류가 발생했습니다.'}), 500

# KOPIS URL 생성 함수 추가
def generate_kopis_url(kopis_id):
    """KOPIS 공연 페이지 URL 생성"""
    if not kopis_id:
        return None
    return f"https://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?mt20id={kopis_id}"

# ============================================================================
# 데이터 분석 및 인사이트 유틸리티 함수들
# ============================================================================

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import uuid

def track_user_activity(activity_type, performance_id=None, category=None, location=None):
    """사용자 활동 추적"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        activity = UserActivity(
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=session_id,
            activity_type=activity_type,
            performance_id=performance_id,
            category=category,
            location=location,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Activity tracking error: {e}")

def get_real_time_dashboard_data():
    """실시간 대시보드 데이터"""
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 오늘 등록된 공연
        today_performances = Performance.query.filter(
            func.date(Performance.created_at) == today
        ).count()
        
        # 실시간 방문자 (최근 1시간)
        recent_visitors = UserActivity.query.filter(
            UserActivity.created_at >= datetime.now() - timedelta(hours=1)
        ).distinct(UserActivity.session_id).count()
        
        # 이번 주 예매율 (좋아요 기준)
        week_start = today - timedelta(days=today.weekday())
        week_performances = Performance.query.filter(
            func.date(Performance.created_at) >= week_start
        ).all()
        
        total_likes = sum(p.likes for p in week_performances)
        total_performances = len(week_performances)
        booking_rate = (total_likes / total_performances * 100) if total_performances > 0 else 0
        
        # 인기 카테고리
        popular_category = db.session.query(
            Performance.category,
            func.count(Performance.id).label('count')
        ).filter(
            func.date(Performance.created_at) >= week_start
        ).group_by(Performance.category).order_by(
            func.count(Performance.id).desc()
        ).first()
        
        return {
            'today_performances': today_performances,
            'recent_visitors': recent_visitors,
            'booking_rate': round(booking_rate, 1),
            'popular_category': popular_category[0] if popular_category else '기타'
        }
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        return {}

def get_audience_analysis_data():
    """관객 분석 데이터"""
    try:
        # 연령대별 선호도 (시뮬레이션 데이터)
        age_preferences = {
            '20대': {'뮤지컬': 45, '연극': 30, '무용': 15, '기타': 10},
            '30대': {'뮤지컬': 40, '연극': 35, '무용': 20, '기타': 5},
            '40대': {'뮤지컬': 35, '연극': 40, '무용': 15, '기타': 10},
            '50대+': {'뮤지컬': 30, '연극': 45, '무용': 10, '기타': 15}
        }
        
        # 성별별 관심도
        gender_preferences = {
            '남성': {'뮤지컬': 35, '연극': 40, '무용': 15, '기타': 10},
            '여성': {'뮤지컬': 50, '연극': 30, '무용': 15, '기타': 5}
        }
        
        # 지역별 관객 분포
        location_distribution = {
            '서울': 45,
            '경기': 25,
            '부산': 10,
            '대구': 8,
            '기타': 12
        }
        
        # 시간대별 활동 패턴
        hourly_pattern = {
            '09-12': 15,
            '12-15': 25,
            '15-18': 30,
            '18-21': 20,
            '21-24': 10
        }
        
        return {
            'age_preferences': age_preferences,
            'gender_preferences': gender_preferences,
            'location_distribution': location_distribution,
            'hourly_pattern': hourly_pattern
        }
    except Exception as e:
        logger.error(f"Audience analysis error: {e}")
        return {}

def get_trend_prediction_data():
    """트렌드 예측 데이터"""
    try:
        # 향후 3개월 전망
        future_trends = {
            '뮤지컬': {'growth': 15, 'confidence': 85},
            '연극': {'growth': 8, 'confidence': 78},
            '무용': {'growth': 5, 'confidence': 72},
            '기타': {'growth': 12, 'confidence': 80}
        }
        
        # 카테고리별 트렌드 (최근 6개월)
        category_trends = {
            '뮤지컬': [10, 12, 15, 18, 20, 22],
            '연극': [8, 9, 10, 12, 14, 16],
            '무용': [5, 6, 7, 8, 9, 10],
            '기타': [3, 4, 6, 8, 10, 12]
        }
        
        # 핫 키워드
        hot_keywords = [
            {'keyword': '환경친화적 공연', 'growth': 200},
            {'keyword': 'AI 공연', 'growth': 150},
            {'keyword': '소셜미디어 공연', 'growth': 120},
            {'keyword': 'VR 공연', 'growth': 100},
            {'keyword': '인터랙티브 공연', 'growth': 90}
        ]
        
        return {
            'future_trends': future_trends,
            'category_trends': category_trends,
            'hot_keywords': hot_keywords
        }
    except Exception as e:
        logger.error(f"Trend prediction error: {e}")
        return {}

def get_ab_test_data():
    """A/B 테스트 데이터"""
    try:
        # 진행 중인 테스트
        active_tests = ABTest.query.filter_by(status='active').all()
        
        # 테스트 결과 요약
        test_results = []
        for test in active_tests:
            results_a = ABTestResult.query.filter_by(
                test_id=test.id, version='A'
            ).count()
            results_b = ABTestResult.query.filter_by(
                test_id=test.id, version='B'
            ).count()
            
            conversions_a = ABTestResult.query.filter_by(
                test_id=test.id, version='A', action='conversion'
            ).count()
            conversions_b = ABTestResult.query.filter_by(
                test_id=test.id, version='B', action='conversion'
            ).count()
            
            conversion_rate_a = (conversions_a / results_a * 100) if results_a > 0 else 0
            conversion_rate_b = (conversions_b / results_b * 100) if results_b > 0 else 0
            
            test_results.append({
                'id': test.id,
                'name': test.name,
                'type': test.test_type,
                'participants_a': results_a,
                'participants_b': results_b,
                'conversion_rate_a': round(conversion_rate_a, 2),
                'conversion_rate_b': round(conversion_rate_b, 2),
                'improvement': round(conversion_rate_b - conversion_rate_a, 2) if conversion_rate_a > 0 else 0
            })
        
        return {
            'active_tests': active_tests,
            'test_results': test_results
        }
    except Exception as e:
        logger.error(f"A/B test data error: {e}")
        return {}

def get_performance_analytics():
    """공연별 성과 분석"""
    try:
        # 공연별 성과 데이터
        performances = Performance.query.filter_by(is_approved=True).all()
        performance_data = []
        
        for perf in performances:
            views = UserActivity.query.filter_by(
                performance_id=perf.id, activity_type='view'
            ).count()
            
            likes = perf.likes
            comments = Comment.query.filter_by(performance_id=perf.id).count()
            
            # 전환율 계산 (좋아요 / 조회수)
            conversion_rate = (likes / views * 100) if views > 0 else 0
            
            performance_data.append({
                'id': perf.id,
                'title': perf.title,
                'category': perf.category,
                'views': views,
                'likes': likes,
                'comments': comments,
                'conversion_rate': round(conversion_rate, 2)
            })
        
        # 사용자 행동 분석
        total_sessions = UserActivity.query.distinct(UserActivity.session_id).count()
        avg_session_duration = 204  # 시뮬레이션 데이터 (초)
        bounce_rate = 23  # 시뮬레이션 데이터 (%)
        return_rate = 67  # 시뮬레이션 데이터 (%)
        
        return {
            'performance_data': performance_data,
            'user_behavior': {
                'total_sessions': total_sessions,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate,
                'return_rate': return_rate
            }
        }
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        return {}

def generate_report(report_type, start_date, end_date, user_id):
    """리포트 생성"""
    try:
        # 리포트 데이터 수집
        dashboard_data = get_real_time_dashboard_data()
        audience_data = get_audience_analysis_data()
        trend_data = get_trend_prediction_data()
        performance_data = get_performance_analytics()
        
        report_data = {
            'report_type': report_type,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'dashboard_data': dashboard_data,
            'audience_data': audience_data,
            'trend_data': trend_data,
            'performance_data': performance_data
        }
        
        # 리포트 저장
        report_name = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report = Report(
            name=report_name,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            data=json.dumps(report_data, ensure_ascii=False),
            created_by=user_id
        )
        db.session.add(report)
        db.session.commit()
        
        return report.id
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return None

if __name__ == "__main__":
    try:
        # 데이터베이스 테이블 생성 시도 (타임아웃 최소화)
        logger.info("Starting application initialization...")
        create_tables()
        create_sample_data_if_needed()  # 샘플 계정 자동 생성
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Server will start without database initialization. Some features may not work.")
        # 데이터베이스 초기화 실패해도 서버는 시작
        pass
    app.run(debug=True) 