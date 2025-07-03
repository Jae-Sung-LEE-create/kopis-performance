from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import os
import json

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = 'your-secret-key-here'

# 간단한 메모리 기반 데이터 저장소
performances = []
performance_id_counter = 1

# 공연 모델 (딕셔너리 기반)
class Performance:
    def __init__(self, title, group_name, description, location, price, date, time, contact_email, video_url=None, image_url=None):
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
        self.is_approved = False
        self.created_at = datetime.utcnow()

@app.route('/')
def home():
    """홈페이지 - 공연 목록 표시"""
    approved_performances = [p for p in performances if p.is_approved]
    return render_template("index.html", performances=approved_performances)

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
            image_url=request.form.get('image_url')
        )
        
        performances.append(performance)
        return redirect(url_for('submit_performance', success=True))
    
    return render_template("submit.html", success=request.args.get('success') == 'true')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False) 