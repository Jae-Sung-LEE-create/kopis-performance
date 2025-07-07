import os
from main import app, create_tables

# 데이터베이스 테이블 생성 및 관리자 계정 초기화
create_tables()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False) 