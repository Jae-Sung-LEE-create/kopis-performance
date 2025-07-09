import os
from main import app, create_tables

if __name__ == "__main__":
    # 데이터베이스 테이블 생성
    create_tables()
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False) 