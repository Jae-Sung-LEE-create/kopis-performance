import pickle
import os
from werkzeug.security import generate_password_hash, check_password_hash

def debug_login():
    print("=== 로그인 디버그 ===")
    
    # 데이터 파일 경로
    users_file = 'data/users.pkl'
    
    if not os.path.exists(users_file):
        print("❌ users.pkl 파일이 없습니다!")
        return
    
    try:
        # 사용자 데이터 로드
        with open(users_file, 'rb') as f:
            users = pickle.load(f)
        
        print(f"✅ 사용자 데이터 로드 성공: {len(users)}명")
        
        # 각 사용자 정보 출력
        for i, user in enumerate(users):
            print(f"\n사용자 {i+1}:")
            print(f"  ID: {user.id}")
            print(f"  이름: {user.name}")
            print(f"  아이디: {user.username}")
            print(f"  이메일: {user.email}")
            print(f"  관리자: {user.is_admin}")
            print(f"  비밀번호 해시: {user.password_hash}")
            
            # admin123 비밀번호로 테스트
            if user.username == 'admin':
                test_password = 'admin123'
                is_correct = check_password_hash(user.password_hash, test_password)
                print(f"  admin123 비밀번호 테스트: {is_correct}")
                
                # 새로운 해시 생성해서 비교
                new_hash = generate_password_hash('admin123')
                print(f"  새로운 해시: {new_hash}")
                print(f"  새 해시로 테스트: {check_password_hash(new_hash, 'admin123')}")
        
        # admin 계정 찾기
        admin_user = None
        for user in users:
            if user.username == 'admin':
                admin_user = user
                break
        
        if admin_user:
            print(f"\n✅ admin 계정 발견!")
            print(f"관리자 권한: {admin_user.is_admin}")
            
            # 비밀번호 테스트
            test_password = 'admin123'
            is_correct = check_password_hash(admin_user.password_hash, test_password)
            print(f"admin123 비밀번호 확인: {is_correct}")
            
            if not is_correct:
                print("❌ 비밀번호가 일치하지 않습니다!")
                print("새로운 관리자 계정을 생성하겠습니다...")
                
                # 새로운 관리자 계정 생성
                new_admin_hash = generate_password_hash('admin123')
                admin_user.password_hash = new_admin_hash
                admin_user.is_admin = True
                
                # 저장
                with open(users_file, 'wb') as f:
                    pickle.dump(users, f)
                
                print("✅ 새로운 관리자 계정으로 업데이트 완료!")
        else:
            print("❌ admin 계정을 찾을 수 없습니다!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_login() 