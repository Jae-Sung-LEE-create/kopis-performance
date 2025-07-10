from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, jsonify
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

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = 'your-secret-key-here'

# 데이터베이스 설정
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    # PostgreSQL 설정 - 더 안정적인 연결 설정
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 10,
        'max_overflow': 5,
        'pool_size': 5,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'kopis-performance',
            'options': '-c statement_timeout=30000'  # 30초 타임아웃
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
    category = db.Column(db.String(50))  # 카테고리 필드 추가
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

def create_tables():
    """데이터베이스 테이블 생성"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                logger.info(f"Creating database tables... (attempt {attempt + 1}/{max_retries})")
                
                # 데이터베이스 연결 테스트
                db.session.execute(text('SELECT 1'))
                db.session.commit()
                logger.info("Database connection test successful")
                
                # 테이블 생성
                db.create_all()
                logger.info("Database tables created successfully!")
                
                # 관리자 계정 자동 생성
                try:
                    admin = User.query.filter_by(username='admin').first()
                    if not admin:
                        logger.info("Creating admin user...")
                        admin_user = User(
                            name='관리자',
                            username='admin',
                            email='admin@admin.com',
                            phone='010-0000-0000',
                            password_hash=generate_password_hash('admin123'),
                            is_admin=True
                        )
                        db.session.add(admin_user)
                        db.session.commit()
                        logger.info("Admin user created successfully!")
                    else:
                        logger.info("Admin user already exists!")
                except Exception as user_error:
                    logger.error(f"Error creating admin user: {user_error}")
                
                return  # 성공하면 함수 종료
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                import time
                time.sleep(retry_delay)
                retry_delay *= 2  # 지수 백오프
            else:
                logger.error(f"Failed to create tables after {max_retries} attempts")
                logger.error(f"Final error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

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
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        date_filter = request.args.get('date_filter', '')
        location = request.args.get('location', '')
        price_filter = request.args.get('price_filter', '')
        
        logger.info(f"Filters - Category: {category}, Search: {search}, Date: {date_filter}, Location: {location}, Price: {price_filter}")
        
        # 데이터베이스 연결 확인
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            logger.info("Database connection successful")
            
            # 기본 쿼리 (승인된 공연만)
            query = Performance.query.filter_by(is_approved=True)
            
            # 카테고리 필터
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
                query = query.filter(Performance.location.ilike(f"%{location}%"))
            
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
            
            # 이미지 URL 디버깅
            for performance in approved_performances:
                if performance.image_url:
                    logger.info(f"Performance '{performance.title}' has image: {performance.image_url}")
                else:
                    logger.info(f"Performance '{performance.title}' has no image")
            
            # 템플릿 렌더링 시도
            try:
                return render_template("index.html", 
                                     performances=approved_performances, 
                                     selected_category=category,
                                     search=search,
                                     date_filter=date_filter,
                                     location=location,
                                     price_filter=price_filter)
            except Exception as template_error:
                logger.error(f"Template error: {template_error}")
                # 템플릿 렌더링 실패 시 기본 HTML 반환
                return create_fallback_html(approved_performances)
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            logger.error(f"Database traceback: {traceback.format_exc()}")
            # 데이터베이스 오류 시 기본 페이지 반환
            return create_error_page("데이터베이스 연결 오류", "잠시 후 다시 시도해주세요.")
            
    except Exception as e:
        logger.error(f"Unexpected error in home route: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return create_error_page("서버 오류", "잠시 후 다시 시도해주세요.")

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
    """서버 상태 확인"""
    try:
        # 데이터베이스 연결 테스트
        db_status = "healthy"
        db_error = None
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            logger.info("Health check: Database connection successful")
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
            logger.error(f"Health check: Database connection failed - {e}")
        
        # 공연 데이터 확인
        performance_count = 0
        try:
            performance_count = Performance.query.count()
            logger.info(f"Health check: Found {performance_count} performances")
        except Exception as e:
            logger.error(f"Health check: Performance query failed - {e}")
        
        # 환경 변수 확인
        env_vars = {
            'DATABASE_URL': 'set' if os.getenv('DATABASE_URL') else 'not set',
            'CLOUDINARY_CLOUD_NAME': 'set' if os.getenv('CLOUDINARY_CLOUD_NAME') else 'not set',
            'CLOUDINARY_API_KEY': 'set' if os.getenv('CLOUDINARY_API_KEY') else 'not set',
            'CLOUDINARY_API_SECRET': 'set' if os.getenv('CLOUDINARY_API_SECRET') else 'not set'
        }
        
        health_data = {
            'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'status': db_status,
                'error': db_error,
                'performance_count': performance_count
            },
            'environment': env_vars,
            'version': '1.0.0'
        }
        
        status_code = 200 if db_status == 'healthy' else 503
        return health_data, status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

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
        performance = Performance(
            title=request.form['title'],
            group_name=request.form['group_name'],
            description=request.form['description'],
            location=request.form['location'],
            address=request.form.get('address'),  # 상세 주소 저장
            price=request.form['price'],
            date=request.form['date'],
            time=f"{request.form['start_time']}~{request.form['end_time']}",
            contact_email=request.form['contact_email'],
            video_url=request.form.get('video_url'),
            image_url=image_url,
            category=request.form['category'],  # 카테고리 저장
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

if __name__ == '__main__':
    app.run(debug=True) 