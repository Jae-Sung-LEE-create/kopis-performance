import requests

def test_login():
    """간단한 로그인 테스트"""
    print("=== 로그인 테스트 ===")
    
    # 서버가 실행 중인지 확인
    try:
        response = requests.get('http://localhost:8000')
        print(f"서버 상태: {response.status_code}")
    except:
        print("❌ 서버에 연결할 수 없습니다.")
        return
    
    # 로그인 시도
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post('http://localhost:8000/login', data=login_data)
        print(f"로그인 응답: {response.status_code}")
        print(f"리다이렉트 URL: {response.url}")
        
        if response.status_code == 302:
            print("✅ 로그인 성공!")
        else:
            print("❌ 로그인 실패")
            
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_login() 