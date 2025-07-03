from flask import Flask, request, render_template, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = 'your-secret-key-here'

# 데이터베이스 설정 - 배포 환경에서는 메모리 SQLite 사용
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite 연결 설정
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 공연 모델
class Performance(Base):
    __tablename__ = "performances"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    group_name = Column(String)
    description = Column(Text)
    location = Column(String)
    price = Column(String)
    date = Column(String)
    time = Column(String)
    contact_email = Column(String)
    video_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

@app.route('/')
def home():
    """홈페이지 - 공연 목록 표시"""
    db = SessionLocal()
    performances = db.query(Performance).filter(Performance.is_approved == True).order_by(Performance.created_at.desc()).all()
    db.close()
    
    return render_template("index.html", performances=performances)

@app.route('/admin')
def admin_panel():
    """관리자 패널 - 승인 대기 중인 공연 관리"""
    db = SessionLocal()
    pending_performances = db.query(Performance).filter(Performance.is_approved == False).order_by(Performance.created_at.desc()).all()
    approved_performances = db.query(Performance).filter(Performance.is_approved == True).order_by(Performance.created_at.desc()).all()
    db.close()
    
    return render_template("admin.html", 
                         pending_performances=pending_performances,
                         approved_performances=approved_performances)

@app.route('/admin/approve/<int:performance_id>', methods=['POST'])
def approve_performance(performance_id):
    """공연 승인"""
    db = SessionLocal()
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if performance:
        performance.is_approved = True
        db.commit()
    db.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject/<int:performance_id>', methods=['POST'])
def reject_performance(performance_id):
    """공연 거절"""
    db = SessionLocal()
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if performance:
        db.delete(performance)
        db.commit()
    db.close()
    return redirect(url_for('admin_panel'))

@app.route('/performance/<int:performance_id>')
def performance_detail(performance_id):
    """공연 상세 페이지"""
    db = SessionLocal()
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    db.close()
    
    if not performance or not performance.is_approved:
        return redirect(url_for('home'))
    
    return render_template("performance_detail.html", performance=performance)

@app.route('/submit', methods=['GET', 'POST'])
def submit_performance():
    """공연 신청 폼"""
    if request.method == 'POST':
        db = SessionLocal()
        
        performance = Performance(
            title=request.form['title'],
            group_name=request.form['group_name'],
            description=request.form['description'],
            location=request.form['location'],
            price=request.form['price'],
            date=request.form['date'],
            time=request.form['time'],
            contact_email=request.form['contact_email'],
            video_url=request.form.get('video_url'),
            image_url=request.form.get('image_url')
        )
        
        db.add(performance)
        db.commit()
        db.close()
        
        return redirect(url_for('submit_performance', success=True))
    
    return render_template("submit.html", success=request.args.get('success') == 'true')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False) 