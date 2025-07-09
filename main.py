from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
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
elif not database_url:
    # 로컬 개발용 SQLite 데이터베이스
    database_url = 'sqlite:///app.db'

logger.info(f"Database URL: {database_url}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

# SQLAlchemy 초기화
db = SQLAlchemy()
db.init_app(app)

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
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())

def create_tables():
    """데이터베이스 테이블 생성"""
    try:
        with app.app_context():
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully!")
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
            db.session.execute('SELECT 1')
            approved_performances = Performance.query.filter_by(is_approved=True).all()
            logger.info(f"Found {len(approved_performances)} approved performances")
            return render_template("index.html", performances=approved_performances)
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            return render_template("index.html", performances=[])
            
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
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True) 