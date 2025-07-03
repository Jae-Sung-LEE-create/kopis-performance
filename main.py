from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = 'your-secret-key-here'

# Flask-Login 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 간단한 메모리 기반 데이터 저장소
performances = []
performance_id_counter = 1
users = []
user_id_counter = 1

# 사용자 모델
class User(UserMixin):
    def __init__(self, name, username, email, password_hash, is_admin=False):
        global user_id_counter
        self.id = user_id_counter
        user_id_counter += 1
        self.name = name
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = datetime.utcnow()

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == int(user_id):
            return user
    return None

# 공연 모델 (딕셔너리 기반)
class Performance:
    def __init__(self, title, group_name, description, location, price, date, time, contact_email, video_url=None, image_url=None, user_id=None):
        global performance_id_counter
        self.id = performance_id_counter
        performance_id_counter += 1
        self.title = title
        self.group_name = group_name
        self.description = description
        self.location = location
        self.price = price
        self.date = date
        self.time = time
        self.contact_email = contact_email
        self.video_url = video_url
        self.image_url = image_url
        self.user_id = user_id  # 신청한 사용자 ID
        self.is_approved = False
        self.created_at = datetime.utcnow()

@app.route('/')
def home():
    """홈페이지 - 공연 목록 표시"""
    approved_performances = [p for p in performances if p.is_approved]
    return render_template("index.html", performances=approved_performances)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입"""
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 유효성 검사
        if password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return render_template('register.html')
        
        # 아이디 형식 검사 (영문, 숫자, 언더스코어만)
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('아이디는 영문, 숫자, 언더스코어만 사용 가능합니다.', 'error')
            return render_template('register.html')
        
        # 아이디 중복 확인
        for user in users:
            if user.username == username:
                flash('이미 사용 중인 아이디입니다.', 'error')
                return render_template('register.html')
        
        # 이메일 중복 확인
        for user in users:
            if user.email == email:
                flash('이미 사용 중인 이메일입니다.', 'error')
                return render_template('register.html')
        
        # 새 사용자 생성
        password_hash = generate_password_hash(password)
        new_user = User(name, username, email, password_hash)
        users.append(new_user)
        
        flash('회원가입이 완료되었습니다! 로그인해주세요.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 사용자 찾기
        user = None
        for u in users:
            if u.username == username:
                user = u
                break
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('로그인되었습니다!', 'success')
            return redirect(url_for('home'))
        else:
            flash('사용자명 또는 비밀번호가 올바르지 않습니다.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """로그아웃"""
    logout_user()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('home'))

@app.route('/my-performances')
@login_required
def my_performances():
    """내 공연 신청 현황"""
    # 현재 사용자가 신청한 공연들 찾기 (사용자 ID로 매칭)
    my_performances = [p for p in performances if p.user_id == current_user.id]
    return render_template('my_performances.html', performances=my_performances)

@app.route('/admin')
def admin_panel():
    """관리자 패널 - 승인 대기 중인 공연 관리"""
    pending_performances = [p for p in performances if not p.is_approved]
    approved_performances = [p for p in performances if p.is_approved]
    
    return render_template("admin.html", 
                         pending_performances=pending_performances,
                         approved_performances=approved_performances)

@app.route('/admin/approve/<int:performance_id>', methods=['POST'])
def approve_performance(performance_id):
    """공연 승인"""
    for performance in performances:
        if performance.id == performance_id:
            performance.is_approved = True
            break
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject/<int:performance_id>', methods=['POST'])
def reject_performance(performance_id):
    """공연 거절"""
    global performances
    performances = [p for p in performances if p.id != performance_id]
    return redirect(url_for('admin_panel'))

@app.route('/performance/<int:performance_id>')
def performance_detail(performance_id):
    """공연 상세 페이지"""
    performance = None
    for p in performances:
        if p.id == performance_id:
            performance = p
            break
    
    if not performance or not performance.is_approved:
        return redirect(url_for('home'))
    
    return render_template("performance_detail.html", performance=performance)

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_performance():
    """공연 신청 폼"""
    if request.method == 'POST':
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
            image_url=request.form.get('image_url'),
            user_id=current_user.id
        )
        
        performances.append(performance)
        flash('공연 신청이 완료되었습니다! 관리자 승인 후 홈페이지에 표시됩니다.', 'success')
        return redirect(url_for('submit_performance'))
    
    return render_template("submit.html")

if __name__ == "__main__":
    # 기본 관리자 계정 생성 (첫 실행 시에만)
    if not users:
        admin_password_hash = generate_password_hash('admin123')
        admin_user = User('관리자', 'admin', 'admin@example.com', admin_password_hash, is_admin=True)
        users.append(admin_user)
        print("기본 관리자 계정이 생성되었습니다:")
        print("이름: 관리자")
        print("아이디: admin")
        print("비밀번호: admin123")
    
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False) 