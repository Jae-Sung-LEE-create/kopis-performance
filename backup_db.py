#!/usr/bin/env python3
"""
SQLite 데이터베이스 백업/복원 스크립트
개발 중 데이터를 보존하기 위한 도구입니다.
"""

import os
import shutil
import sqlite3
from datetime import datetime

def backup_database():
    """데이터베이스 백업"""
    source_db = 'app.db'
    if not os.path.exists(source_db):
        print("❌ 백업할 데이터베이스 파일이 없습니다.")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'app_backup_{timestamp}.db'
    
    try:
        shutil.copy2(source_db, backup_name)
        print(f"✅ 데이터베이스 백업 완료: {backup_name}")
        
        # 백업 파일 정보 출력
        size = os.path.getsize(backup_name)
        print(f"📁 백업 파일 크기: {size:,} bytes")
        
    except Exception as e:
        print(f"❌ 백업 실패: {e}")

def restore_database():
    """데이터베이스 복원"""
    # 백업 파일 목록 표시
    backup_files = [f for f in os.listdir('.') if f.startswith('app_backup_') and f.endswith('.db')]
    
    if not backup_files:
        print("❌ 복원할 백업 파일이 없습니다.")
        return
    
    print("📋 사용 가능한 백업 파일:")
    for i, file in enumerate(sorted(backup_files, reverse=True)):
        size = os.path.getsize(file)
        mtime = datetime.fromtimestamp(os.path.getmtime(file))
        print(f"  {i+1}. {file} ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    try:
        choice = int(input("\n복원할 백업 파일 번호를 선택하세요: ")) - 1
        if 0 <= choice < len(backup_files):
            backup_file = backup_files[choice]
            
            # 현재 데이터베이스 백업
            if os.path.exists('app.db'):
                current_backup = f'app_current_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                shutil.copy2('app.db', current_backup)
                print(f"📦 현재 데이터베이스 백업: {current_backup}")
            
            # 복원
            shutil.copy2(backup_file, 'app.db')
            print(f"✅ 데이터베이스 복원 완료: {backup_file}")
            
        else:
            print("❌ 잘못된 선택입니다.")
            
    except ValueError:
        print("❌ 숫자를 입력해주세요.")
    except Exception as e:
        print(f"❌ 복원 실패: {e}")

def list_backups():
    """백업 파일 목록 표시"""
    backup_files = [f for f in os.listdir('.') if f.startswith('app_backup_') and f.endswith('.db')]
    
    if not backup_files:
        print("📋 백업 파일이 없습니다.")
        return
    
    print("📋 백업 파일 목록:")
    for file in sorted(backup_files, reverse=True):
        size = os.path.getsize(file)
        mtime = datetime.fromtimestamp(os.path.getmtime(file))
        print(f"  📁 {file}")
        print(f"     크기: {size:,} bytes")
        print(f"     생성: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def main():
    """메인 함수"""
    print("🗄️  SQLite 데이터베이스 관리 도구")
    print("=" * 40)
    
    while True:
        print("\n📋 메뉴:")
        print("1. 데이터베이스 백업")
        print("2. 데이터베이스 복원")
        print("3. 백업 파일 목록")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == '1':
            backup_database()
        elif choice == '2':
            restore_database()
        elif choice == '3':
            list_backups()
        elif choice == '4':
            print("👋 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == '__main__':
    main() 