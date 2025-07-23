import os
import sys
import logging
import time
from main import app, create_tables, create_sample_data_if_needed

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # 무한루프 방지를 위한 타임아웃 설정
    start_time = time.time()
    timeout = 30  # 30초 타임아웃
    
    try:
        # 애플리케이션 컨텍스트 내에서 실행 (타임아웃 적용)
        with app.app_context():
            logger.info("Starting application initialization...")
            
            # 데이터베이스 초기화 시도 (타임아웃 체크)
            if time.time() - start_time < timeout:
                try:
                    create_tables()
                    logger.info("Database tables created successfully!")
                except Exception as e:
                    logger.error(f"Database table creation failed: {e}")
                    logger.warning("Continuing without database tables.")
                
                # 샘플 데이터 생성 시도 (타임아웃 체크)
                if time.time() - start_time < timeout:
                    try:
                        create_sample_data_if_needed()
                        logger.info("Sample data initialization completed!")
                    except Exception as e:
                        logger.error(f"Sample data creation failed: {e}")
                        logger.warning("Continuing without sample data initialization.")
                else:
                    logger.warning("Timeout reached, skipping sample data creation.")
            else:
                logger.warning("Timeout reached, skipping database initialization.")
            
            logger.info("Database initialization completed successfully!")
            
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        logger.warning("Server will start without full initialization.")
    
    # 서버 시작 - 렌더 환경변수 PORT 사용
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    
    try:
        # 렌더 배포를 위한 설정 (무한루프 방지)
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