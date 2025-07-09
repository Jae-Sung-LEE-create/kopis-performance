from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
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
    # PostgreSQL 설정
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 5,
        'max_overflow': 0,
        'pool_size': 3,
        'connect_args': {
            'connect_timeout': 5,
            'application_name': 'kopis-performance'
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
    price = db.Column(db.String(50))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    video_url = db.Column(db.String(300))
    image_url = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship('User', backref='performances')

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
    try:
        with app.app_context():
            logger.info("Creating database tables...")
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
                
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

# 기본 라우트들
@app.route('/')
def home():
    """홈페이지"""
    try:
        logger.info("Accessing home page")
        
        # 데이터베이스 연결 확인
        try:
            db.session.execute(text('SELECT 1'))
            approved_performances = Performance.query.filter_by(is_approved=True).all()
            logger.info(f"Found {len(approved_performances)} approved performances")
            
            # 템플릿 렌더링 시도
            try:
                return render_template("index.html", performances=approved_performances)
            except Exception as template_error:
                logger.error(f"Template error: {template_error}")
                # 템플릿 렌더링 실패 시 기본 HTML 반환
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>공연 정보</title>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .performance {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                        .title {{ font-size: 18px; font-weight: bold; color: #333; }}
                        .info {{ color: #666; margin: 5px 0; }}
                    </style>
                </head>
                <body>
                    <h1>공연 정보</h1>
                    <p>총 {len(approved_performances)}개의 공연이 있습니다.</p>
                """
                
                for performance in approved_performances:
                    html_content += f"""
                    <div class="performance">
                        <div class="title">{performance.title}</div>
                        <div class="info">그룹: {performance.group_name}</div>
                        <div class="info">장소: {performance.location}</div>
                        <div class="info">날짜: {performance.date}</div>
                        <div class="info">시간: {performance.time}</div>
                        <div class="info">가격: {performance.price}</div>
                    </div>
                    """
                
                html_content += """
                </body>
                </html>
                """
                return html_content
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>공연 정보</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                    .message { color: #666; }
                </style>
            </head>
            <body>
                <h1>공연 정보</h1>
                <p class="message">현재 공연 정보를 불러올 수 없습니다.</p>
                <p class="message">잠시 후 다시 시도해주세요.</p>
            </body>
            </html>
            """
            
    except Exception as e:
        logger.error(f"Home page error: {e}")
        return "서비스 점검 중입니다.", 503

@app.route('/test')
def test_page():
    """테스트 페이지"""
    return "Flask 애플리케이션이 정상 작동 중입니다!"

@app.route('/health')
def health_check():
    """헬스체크"""
    try:
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500

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
            ext = image.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            upload_dir = os.path.join('static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image.save(os.path.join(upload_dir, filename))
            image_url = f"/static/uploads/{filename}"
        
        performance = Performance(
            title=request.form['title'],
            group_name=request.form['group_name'],
            description=request.form['description'],
            location=request.form['location'],
            price=request.form['price'],
            date=request.form['date'],
            time=f"{request.form['start_time']}~{request.form['end_time']}",
            contact_email=request.form['contact_email'],
            video_url=request.form.get('video_url'),
            image_url=image_url,
            user_id=current_user.id
        )
        db.session.add(performance)
        db.session.commit()
        flash('공연 신청이 완료되었습니다! 관리자 승인 후 홈페이지에 표시됩니다.', 'success')
        return redirect(url_for('submit_performance'))
    
    # 오늘 날짜를 YYYY-MM-DD 형식으로 전달
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template("submit.html", today_date=today_date)

@app.route('/performance/<int:performance_id>')
def performance_detail(performance_id):
    """공연 상세 페이지"""
    performance = Performance.query.get(performance_id)
    
    if not performance or not performance.is_approved:
        return redirect(url_for('home'))
    
    return render_template("performance_detail.html", performance=performance)

if __name__ == '__main__':
    app.run(debug=True) 