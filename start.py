import os
from main import app, create_tables

# 데이터베이스 테이블 생성 및 관리자 계정 초기화
print("Starting application...")
try:
    create_tables()
    print("Database initialization completed")
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("Continuing with application startup...")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False) 