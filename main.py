from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, jsonify, session, g
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
    likes = db.Column(db.Integer, default=0)  # 좋아요 수
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship('User', backref='performances')

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

def detect_region_from_address(address):
    """주소에서 지역을 자동으로 감지하는 함수"""
    if not address:
        return None
    
    address_lower = address.lower()
    
    # 지역 매핑
    region_mapping = {
        '서울특별시': ['서울특별시', '서울시', '서울'],
        '경기도': ['경기도', '경기'],
        '강원도': ['강원도', '강원'],
        '인천광역시': ['인천광역시', '인천시', '인천'],
        '충청남도': ['충청남도', '충남'],
        '충청북도': ['충청북도', '충북'],
        '세종특별자치시': ['세종특별자치시', '세종시', '세종'],
        '대전광역시': ['대전광역시', '대전시', '대전'],
        '경상북도': ['경상북도', '경북'],
        '대구광역시': ['대구광역시', '대구시', '대구'],
        '전라북도': ['전라북도', '전북'],
        '경상남도': ['경상남도', '경남'],
        '울산광역시': ['울산광역시', '울산시', '울산'],
        '부산광역시': ['부산광역시', '부산시', '부산'],
        '광주광역시': ['광주광역시', '광주시', '광주'],
        '전라남도': ['전라남도', '전남'],
        '제주도': ['제주도', '제주특별자치도', '제주시', '제주']
    }
    
    for region, keywords in region_mapping.items():
        for keyword in keywords:
            if keyword in address_lower:
                return region
    
    return None

def create_tables():
    """데이터베이스 테이블 생성"""
    max_retries = 2  # 3에서 2로 줄임
    retry_delay = 1  # 2에서 1로 줄임
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                logger.info(f"Creating database tables... (attempt {attempt + 1}/{max_retries})")
                
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
        if User.query.count() == 0:
            # admin 계정과 샘플 사용자 생성
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

            # 샘플 공연 데이터 생성
            sample_performances = [
                {
                    'title': '스트릿댄스 쇼케이스',
                    'group_name': '스트릿크루',
                    'description': '다양한 스트릿댄스 장르를 선보이는 쇼케이스입니다. 힙합, 브레이킹, 팝핑 등 다양한 댄스 스타일을 감상하실 수 있습니다.',
                    'location': '홍대 클럽',
                    'address': '서울특별시 마포구 홍익로 1',
                    'price': '무료',
                    'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'time': '19:00~21:00',
                    'contact_email': 'street@test.com',
                    'video_url': 'https://www.youtube.com/watch?v=example1',
                    'is_approved': True
                }
            ]
            for perf_data in sample_performances:
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
                    user_id=created_users[1].id,  # dancer1 계정으로 설정
                    is_approved=perf_data['is_approved']
                )
                db.session.add(performance)
            db.session.commit()
            print('✅ 모든 계정(admin + 샘플) 및 공연 자동 생성 완료!')
        else:
            print('샘플 계정 자동 생성: 이미 사용자 데이터가 있습니다.')

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
        
        # 필터 파라미터 받기
        main_category = request.args.get('main_category')
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        date_filter = request.args.get('date_filter', '')
        location = request.args.get('location', '')
        price_filter = request.args.get('price_filter', '')
        
        logger.info(f"Filters - Main Category: {main_category}, Category: {category}, Search: {search}, Date: {date_filter}, Location: {location}, Price: {price_filter}")
        
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
                
                if date_filter == 'this_week':
                    # 이번 주 (월요일부터 일요일까지)
                    days_since_monday = today.weekday()
                    monday = today - timedelta(days=days_since_monday)
                    sunday = monday + timedelta(days=6)
                    query = query.filter(
                        db.and_(
                            Performance.date >= monday.strftime('%Y-%m-%d'),
                            Performance.date <= sunday.strftime('%Y-%m-%d')
                        )
                    )
                elif date_filter == 'this_month':
                    # 이번 달
                    first_day = today.replace(day=1)
                    if today.month == 12:
                        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                    query = query.filter(
                        db.and_(
                            Performance.date >= first_day.strftime('%Y-%m-%d'),
                            Performance.date <= last_day.strftime('%Y-%m-%d')
                        )
                    )
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
                    query = query.filter(
                        db.and_(
                            Performance.date >= first_day.strftime('%Y-%m-%d'),
                            Performance.date <= last_day.strftime('%Y-%m-%d')
                        )
                    )
            
            # 지역 필터
            if location:
                query = query.filter(Performance.location == location)
            
            # 가격 필터
            if price_filter:
                if price_filter == 'free':
                    query = query.filter(
                        db.or_(
                            Performance.price.ilike('%무료%'),
                            Performance.price.ilike('%free%'),
                            Performance.price == '무료'
                        )
                    )
                elif price_filter == 'paid':
                    query = query.filter(
                        db.and_(
                            ~Performance.price.ilike('%무료%'),
                            ~Performance.price.ilike('%free%'),
                            Performance.price != '무료'
                        )
                    )
                elif price_filter == 'discount':
                    query = query.filter(
                        db.or_(
                            Performance.price.ilike('%할인%'),
                            Performance.price.ilike('%discount%'),
                            Performance.price.ilike('%학생%'),
                            Performance.price.ilike('%student%')
                        )
                    )
            
            # 최신순 정렬
            approved_performances = query.order_by(Performance.created_at.desc()).all()
            logger.info(f"Found {len(approved_performances)} filtered performances")
            
            # 템플릿 렌더링
            return render_template("index.html", 
                                 performances=approved_performances, 
                                 selected_main_category=main_category,
                                 selected_category=category,
                                 search=search,
                                 date_filter=date_filter,
                                 location=location,
                                 price_filter=price_filter)
                
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
    
    pending_performances = Performance.query.filter_by(is_approved=False).all()
    approved_performances = Performance.query.filter_by(is_approved=True).all()
    
    return render_template("admin.html", 
                         pending_performances=pending_performances,
                         approved_performances=approved_performances,
                         users=User.query.all())

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
        
        performance = Performance(
            title=request.form['title'],
            group_name=request.form['group_name'],
            description=request.form['description'],
            location=location,  # 자동 감지된 지역 또는 수동 입력
            address=address,  # 상세 주소 저장
            price=request.form['price'],
            date=request.form['date'],
            time=f"{request.form['start_time']}~{request.form['end_time']}",
            contact_email=request.form['contact_email'],
            video_url=request.form.get('video_url'),
            image_url=image_url,
            main_category=request.form['main_category'],  # 메인 카테고리 저장
            category=request.form['category'],  # 세부 카테고리 저장
            ticket_url=request.form.get('ticket_url'),  # 티켓 예매 링크 저장
            user_id=current_user.id
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