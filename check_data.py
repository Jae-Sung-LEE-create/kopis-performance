import pickle
import os
from datetime import datetime

# User 클래스 정의
class User:
    def __init__(self, name, username, email, password_hash, is_admin=False):
        self.id = None
        self.name = name
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = datetime.utcnow()

# Performance 클래스 정의
class Performance:
    def __init__(self, title, group_name, description, location, price, date, time, contact_email, video_url=None, image_url=None, user_id=None):
        self.id = None
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
        self.user_id = user_id
        self.is_approved = False
        self.created_at = datetime.utcnow()

def check_data():
    print("=== 데이터 상태 확인 ===")
    
    # performances.pkl 확인
    performances_file = 'data/performances.pkl'
    if os.path.exists(performances_file):
        with open(performances_file, 'rb') as f:
            performances = pickle.load(f)
        print(f"공연 데이터 개수: {len(performances)}")
        for p in performances:
            print(f"  - ID: {p.id}, 제목: {p.title}, 승인: {p.is_approved}")
    else:
        print("performances.pkl 파일이 없습니다.")
    
    # users.pkl 확인
    users_file = 'data/users.pkl'
    if os.path.exists(users_file):
        with open(users_file, 'rb') as f:
            users = pickle.load(f)
        print(f"사용자 데이터 개수: {len(users)}")
        for u in users:
            print(f"  - ID: {u.id}, 이름: {u.name}, 아이디: {u.username}")
    else:
        print("users.pkl 파일이 없습니다.")

if __name__ == "__main__":
    check_data() 