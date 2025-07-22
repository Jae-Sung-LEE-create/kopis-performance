# 웹사이트 + 모바일 앱 연동 계획

## 🎯 목표
- 기존 웹사이트 (https://kopis-performance.onrender.com) 유지
- 모바일 앱 추가 개발 (React Native)
- 웹사이트와 앱 간 완전한 데이터 연동
- QR 코드를 통한 앱 다운로드 제공

## 📱 아키텍처 구성

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   웹사이트      │    │   모바일 앱     │    │   공통 백엔드   │
│                 │    │                 │    │                 │
│ • 홈페이지      │    │ • 네이티브 UI   │    │ • Flask API     │
│ • 관리자 패널   │    │ • 푸시 알림     │    │ • 데이터베이스  │
│ • 공연 신청     │    │ • 카메라 기능   │    │ • 파일 업로드   │
│ • 분석 대시보드 │    │ • 오프라인 지원 │    │ • 인증 시스템   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   QR 코드       │
                    │   앱 다운로드   │
                    └─────────────────┘
```

## 🔧 1단계: Flask API 확장

### 1.1 모바일용 API 엔드포인트 추가
```python
# main.py에 추가할 API 라우트들

# 공연 관련 API
@app.route('/api/mobile/performances', methods=['GET'])
def api_performances():
    """모바일용 공연 목록 API"""
    # 기존 웹사이트와 동일한 데이터 제공

@app.route('/api/mobile/performances/<int:performance_id>', methods=['GET'])
def api_performance_detail(performance_id):
    """모바일용 공연 상세 API"""

@app.route('/api/mobile/performances', methods=['POST'])
def api_create_performance():
    """모바일용 공연 신청 API"""

# 인증 관련 API
@app.route('/api/mobile/auth/login', methods=['POST'])
def api_login():
    """모바일용 로그인 API"""

@app.route('/api/mobile/auth/register', methods=['POST'])
def api_register():
    """모바일용 회원가입 API"""

# 사용자 관련 API
@app.route('/api/mobile/user/profile', methods=['GET'])
def api_user_profile():
    """모바일용 사용자 프로필 API"""

@app.route('/api/mobile/user/performances', methods=['GET'])
def api_user_performances():
    """모바일용 내 공연 목록 API"""
```

### 1.2 JWT 토큰 인증 시스템 추가
```python
# JWT 토큰 기반 인증으로 웹/앱 통합 인증
import jwt
from datetime import datetime, timedelta

def generate_token(user_id):
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None
```

## 📱 2단계: React Native 앱 개발

### 2.1 프로젝트 구조
```
KopisMobileApp/
├── src/
│   ├── components/
│   │   ├── PerformanceCard.tsx      # 공연 카드 컴포넌트
│   │   ├── PerformanceDetail.tsx    # 공연 상세 컴포넌트
│   │   ├── LoginForm.tsx           # 로그인 폼
│   │   └── SubmitForm.tsx          # 공연 신청 폼
│   ├── screens/
│   │   ├── HomeScreen.tsx          # 홈 화면
│   │   ├── PerformanceListScreen.tsx # 공연 목록
│   │   ├── PerformanceDetailScreen.tsx # 공연 상세
│   │   ├── LoginScreen.tsx         # 로그인 화면
│   │   ├── ProfileScreen.tsx       # 프로필 화면
│   │   └── SubmitScreen.tsx        # 공연 신청 화면
│   ├── services/
│   │   ├── api.ts                  # API 통신
│   │   ├── auth.ts                 # 인증 관리
│   │   └── storage.ts              # 로컬 저장소
│   ├── navigation/
│   │   └── AppNavigator.tsx        # 네비게이션
│   └── utils/
│       └── constants.ts            # 상수 정의
├── android/                        # Android 설정
├── ios/                           # iOS 설정
└── package.json
```

### 2.2 주요 기능
- **공연 목록/상세 보기**: 웹사이트와 동일한 데이터
- **공연 신청**: 카메라로 이미지 촬영, GPS 위치 정보
- **푸시 알림**: 새로운 공연, 승인 상태 변경 알림
- **오프라인 지원**: 인터넷 없이도 기본 기능 사용
- **소셜 공유**: 공연 정보를 SNS에 공유

## 🔗 3단계: 웹사이트와 앱 연동

### 3.1 웹사이트에 앱 다운로드 섹션 추가
```html
<!-- templates/index.html에 추가 -->
<div class="mobile-app-section">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-6">
                <h2>모바일 앱으로 더 편리하게!</h2>
                <p>QR 코드를 스캔하여 모바일 앱을 다운로드하세요.</p>
                <div class="qr-code">
                    <img src="{{ url_for('static', filename='qr-code.png') }}" alt="앱 다운로드 QR코드">
                </div>
                <div class="app-links">
                    <a href="#" class="btn btn-primary">
                        <i class="fab fa-google-play"></i> Google Play
                    </a>
                    <a href="#" class="btn btn-primary">
                        <i class="fab fa-apple"></i> App Store
                    </a>
                </div>
            </div>
            <div class="col-md-6">
                <img src="{{ url_for('static', filename='mobile-app-preview.png') }}" alt="모바일 앱 미리보기">
            </div>
        </div>
    </div>
</div>
```

### 3.2 데이터 동기화
- **실시간 동기화**: 웹사이트에서 공연 신청 → 앱에서 즉시 확인
- **앱에서 신청**: 앱에서 공연 신청 → 웹사이트 관리자 패널에서 확인
- **좋아요/댓글**: 웹사이트와 앱에서 동일하게 반영
- **사용자 프로필**: 웹사이트와 앱에서 동일한 프로필 정보

## 📱 4단계: QR 코드 및 앱 배포

### 4.1 QR 코드 생성
```python
# QR 코드 생성 API
@app.route('/api/qr-code')
def generate_qr_code():
    """앱 다운로드 QR 코드 생성"""
    import qrcode
    from io import BytesIO
    import base64
    
    # 앱 다운로드 링크
    app_download_url = "https://play.google.com/store/apps/details?id=com.kopis.mobile"
    
    # QR 코드 생성
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(app_download_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 이미지를 base64로 인코딩
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({'qr_code': img_str})
```

### 4.2 앱스토어 배포
- **Google Play Store**: Android 앱 배포
- **Apple App Store**: iOS 앱 배포
- **내부 테스트**: 베타 테스터를 통한 사전 테스트

## 🚀 5단계: 고급 기능

### 5.1 푸시 알림 시스템
```python
# Firebase Cloud Messaging 연동
@app.route('/api/mobile/notifications/register', methods=['POST'])
def register_push_token():
    """푸시 알림 토큰 등록"""
    user_id = get_current_user_id()
    token = request.json.get('token')
    
    # 토큰을 데이터베이스에 저장
    user = User.query.get(user_id)
    user.push_token = token
    db.session.commit()
    
    return jsonify({'success': True})

def send_push_notification(user_id, title, body, data=None):
    """푸시 알림 전송"""
    user = User.query.get(user_id)
    if user and user.push_token:
        # Firebase FCM을 통해 알림 전송
        pass
```

### 5.2 오프라인 지원
- **로컬 데이터베이스**: SQLite를 사용한 오프라인 데이터 저장
- **동기화**: 온라인 복귀 시 자동 데이터 동기화
- **캐싱**: 이미지 및 데이터 캐싱으로 빠른 로딩

## 📊 6단계: 분석 및 모니터링

### 6.1 사용자 행동 분석
- **웹사이트 vs 앱 사용률**: 어떤 플랫폼을 더 선호하는지
- **사용자 경험**: 각 플랫폼별 사용 패턴 분석
- **성능 모니터링**: 앱 성능 및 오류 추적

### 6.2 A/B 테스트
- **UI/UX 테스트**: 웹사이트와 앱의 사용자 경험 비교
- **기능 테스트**: 새로운 기능의 효과 측정

## 💰 예상 비용 및 일정

### 개발 비용
- **React Native 앱 개발**: $15,000 - $25,000
- **API 확장 및 테스트**: $5,000 - $8,000
- **앱스토어 등록**: $100 (Google Play) + $99 (Apple)
- **서버 확장**: $50 - $100/월

### 개발 일정
- **1-2주**: API 확장 및 테스트
- **4-6주**: React Native 앱 개발
- **1-2주**: 앱스토어 등록 및 배포
- **총 6-10주**: 완전한 모바일 앱 출시

## 🎯 최종 결과

### 사용자 경험
- **웹사이트**: 데스크톱에서 편리한 관리 및 상세 분석
- **모바일 앱**: 이동 중에도 편리한 공연 확인 및 신청
- **완전한 연동**: 어느 플랫폼에서든 동일한 데이터 접근

### 비즈니스 효과
- **사용자 증가**: 모바일 사용자 확보
- **사용성 향상**: 다양한 접근 방법 제공
- **브랜드 강화**: 전문적인 모바일 앱으로 신뢰도 향상

이렇게 구현하면 기존 웹사이트를 그대로 유지하면서 모바일 앱을 추가로 제공할 수 있으며, 두 플랫폼이 완전히 연동되어 사용자에게 일관된 경험을 제공할 수 있습니다. 