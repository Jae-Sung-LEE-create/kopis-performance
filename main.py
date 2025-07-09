from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import uuid
import traceback

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = 'your-secret-key-here'

# 기본 라우트들
@app.route('/')
def home():
    """홈페이지"""
    try:
        return "홈페이지가 정상 작동 중입니다!"
    except Exception as e:
        logger.error(f"Home page error: {e}")
        return "서비스 점검 중입니다.", 503

@app.route('/test')
def test_page():
    """테스트 페이지"""
    return "Flask 애플리케이션이 정상 작동 중입니다!"

@app.route('/health')
def health_check():
    """헬스체크"""
    return {'status': 'healthy', 'message': 'Basic Flask app is running'}, 200

if __name__ == '__main__':
    app.run(debug=True) 