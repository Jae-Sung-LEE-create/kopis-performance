import os
import sys
import logging
from main import app, create_tables

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # 데이터베이스 테이블 생성 시도 (타임아웃 최소화)
        logger.info("Starting application initialization...")
        create_tables()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Server will start without database initialization. Some features may not work.")
        # 데이터베이스 초기화 실패해도 서버는 시작
        pass
    
    # 서버 시작 - 렌더 환경변수 PORT 사용
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    
    try:
        # 렌더 배포를 위한 설정 (타임아웃 최소화)
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=False, 
            threaded=True,
            use_reloader=False  # 렌더에서는 리로더 비활성화
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1) 