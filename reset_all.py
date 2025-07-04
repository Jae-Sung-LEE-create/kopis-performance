import os
import shutil

def reset_all():
    """모든 데이터를 완전히 초기화"""
    print("=== 완전 초기화 시작 ===")
    
    # data 폴더 삭제
    if os.path.exists('data'):
        shutil.rmtree('data')
        print("✅ data 폴더 삭제 완료")
    
    # __pycache__ 폴더 삭제
    if os.path.exists('__pycache__'):
        shutil.rmtree('__pycache__')
        print("✅ __pycache__ 폴더 삭제 완료")
    
    # 새로운 data 폴더 생성
    os.makedirs('data', exist_ok=True)
    print("✅ 새로운 data 폴더 생성 완료")
    
    print("\n=== 초기화 완료 ===")
    print("이제 main.py를 실행하면 새로운 관리자 계정이 생성됩니다.")
    print("관리자 계정: admin / admin123")

if __name__ == "__main__":
    reset_all() 