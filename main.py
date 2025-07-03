from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json
from typing import Optional
import uvicorn

app = FastAPI(title="KOPIS 공연 홍보 플랫폼", description="대중무용 공연 홍보 서비스")

# 데이터베이스 설정 - 배포 환경에서는 PostgreSQL 사용
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite 연결 설정 수정
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

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
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization error: {e}")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """홈페이지 - 공연 목록 표시"""
    db = SessionLocal()
    performances = db.query(Performance).filter(Performance.is_approved == True).order_by(Performance.created_at.desc()).all()
    db.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "performances": performances
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """관리자 패널 - 승인 대기 중인 공연 관리"""
    db = SessionLocal()
    pending_performances = db.query(Performance).filter(Performance.is_approved == False).order_by(Performance.created_at.desc()).all()
    approved_performances = db.query(Performance).filter(Performance.is_approved == True).order_by(Performance.created_at.desc()).all()
    db.close()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "pending_performances": pending_performances,
        "approved_performances": approved_performances
    })

@app.post("/admin/approve/{performance_id}")
async def approve_performance(performance_id: int):
    """공연 승인"""
    db = SessionLocal()
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if performance:
        performance.is_approved = True
        db.commit()
    db.close()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/reject/{performance_id}")
async def reject_performance(performance_id: int):
    """공연 거절"""
    db = SessionLocal()
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    if performance:
        db.delete(performance)
        db.commit()
    db.close()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/performance/{performance_id}", response_class=HTMLResponse)
async def performance_detail(request: Request, performance_id: int):
    """공연 상세 페이지"""
    db = SessionLocal()
    performance = db.query(Performance).filter(Performance.id == performance_id).first()
    db.close()
    
    if not performance or not performance.is_approved:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("performance_detail.html", {
        "request": request,
        "performance": performance
    })

@app.get("/submit", response_class=HTMLResponse)
async def submit_form(request: Request):
    """공연 신청 폼"""
    return templates.TemplateResponse("submit.html", {"request": request})

@app.post("/submit")
async def submit_performance(
    title: str = Form(...),
    group_name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    price: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    contact_email: str = Form(...),
    video_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None)
):
    """공연 신청 처리"""
    db = SessionLocal()
    
    performance = Performance(
        title=title,
        group_name=group_name,
        description=description,
        location=location,
        price=price,
        date=date,
        time=time,
        contact_email=contact_email,
        video_url=video_url,
        image_url=image_url
    )
    
    db.add(performance)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/submit?success=true", status_code=303)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=port,
        reload=False,
        workers=1
    ) 