# KOPIS 공연 홍보 플랫폼

대학생 댄스동아리와 스트릿댄스 크루들의 공연을 홍보하는 웹 플랫폼입니다.

## 🚀 배포 URL

- **프로덕션**: https://kopis-performance.onrender.com
- **헬스 체크**: https://kopis-performance.onrender.com/health

## 🛠️ 개발 환경 설정

### 1. 저장소 클론
```bash
git clone https://github.com/Jae-Sung-LEE-create/kopis-performance.git
cd kopis-performance
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:
```env
DATABASE_URL=sqlite:///app.db
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 5. 서버 실행
```bash
python start.py
```

서버가 `http://127.0.0.1:8000`에서 실행됩니다.

## 📊 데이터 관리

### 개발용 샘플 데이터 생성
```bash
python init_dev_data.py
```

**테스트 계정:**
- `admin` / `admin123` (관리자)
- `dancer1` / `test123`
- `crew2` / `test123`
- `street3` / `test123`

### 데이터베이스 백업/복원
```bash
python backup_db.py
```

**기능:**
- 데이터베이스 백업
- 백업 파일 복원
- 백업 파일 목록 확인

## 🔧 주요 기능

### 사용자 기능
- 회원가입/로그인
- 공연 신청 및 관리
- 내 공연 현황 확인

### 관리자 기능
- 공연 승인/거절
- 공연 삭제
- 전체 공연 관리

### 공연 정보
- 공연명, 팀명, 설명
- 장소, 날짜, 시간
- 가격, 연락처
- 이미지 업로드 (Cloudinary)
- 홍보 동영상 링크

## 🗄️ 데이터베이스

### 개발 환경
- **SQLite**: `app.db` 파일
- 데이터는 로컬에 저장
- 개발 중 데이터 보존을 위해 백업 권장

### 프로덕션 환경
- **PostgreSQL**: Render 제공
- 환경 변수 `DATABASE_URL`로 설정

## 📁 프로젝트 구조

```
kopis-performance/
├── main.py              # 메인 애플리케이션
├── start.py             # 서버 시작 스크립트
├── init_dev_data.py     # 샘플 데이터 생성
├── backup_db.py         # 데이터베이스 백업/복원
├── requirements.txt     # Python 의존성
├── render.yaml          # Render 배포 설정
├── templates/           # HTML 템플릿
├── static/              # 정적 파일
└── data/                # 데이터 파일
```

## 🚨 주의사항

### 개발 환경에서 데이터 보존
1. **`.gitignore`**에 `*.db`가 포함되어 있어 SQLite 파일은 Git에 추적되지 않습니다.
2. 개발 중 중요한 데이터가 있다면 `python backup_db.py`로 백업하세요.
3. 서버 재시작 시 데이터가 초기화될 수 있습니다.

### 환경 변수
- **로컬 개발**: `.env` 파일 사용
- **프로덕션**: Render 환경 변수 설정

## 🔍 문제 해결

### 웹사이트 로딩 문제
1. `/health` 엔드포인트로 서버 상태 확인
2. 로그 확인: `python start.py` 실행 시 출력되는 로그
3. 데이터베이스 연결 확인

### 데이터베이스 문제
1. `python backup_db.py`로 백업
2. `python init_dev_data.py`로 샘플 데이터 재생성
3. `app.db` 파일 삭제 후 서버 재시작

## 📝 업데이트 로그

### 2024-07-10
- 데이터베이스 연결 안정성 개선
- 에러 핸들링 강화
- 개발용 데이터 관리 도구 추가
- 헬스 체크 엔드포인트 개선

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 