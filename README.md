# KOPIS 공연 홍보 플랫폼

대중무용의 접근성을 높이고 대학생 댄스동아리, 스트릿댄스 크루들의 공연을 홍보하는 웹 플랫폼입니다.

## 🎯 프로젝트 목적

- 대중무용의 티켓예매수와 공연건수 부족 문제 해결
- 대학생 댄스동아리와 스트릿댄스 크루들의 공연 홍보 지원
- 공연예술통합전산망(KOPIS) 데이터 활용한 공연시장 발전 기여

## ✨ 주요 기능

### 🎭 공연 신청 및 관리
- 온라인 공연 신청 폼
- 홍보 동영상 및 이미지 업로드 지원
- 관리자 승인 시스템

### 📱 사용자 인터페이스
- 반응형 웹 디자인
- 공연 목록 및 상세 페이지
- 검색 및 필터링 기능

### 🔧 관리자 기능
- 공연 신청 승인/거절
- 공연 정보 관리
- 통계 대시보드

## 🛠 기술 스택

- **Backend**: FastAPI (Python)
- **Database**: SQLite (개발용) / PostgreSQL (배포용)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Template Engine**: Jinja2

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 애플리케이션 실행
```bash
python main.py
```

### 3. 웹 브라우저에서 접속
```
http://localhost:8000
```

## 🌐 배포 방법

### Railway 배포 (추천)
1. [Railway](https://railway.app) 계정 생성
2. GitHub 저장소 연결
3. 자동 배포 완료

### Vercel 배포
1. [Vercel](https://vercel.com) 계정 생성
2. 프로젝트 import
3. 배포 설정 완료

## 📁 프로젝트 구조

```
├── main.py                 # FastAPI 메인 애플리케이션
├── admin_app.py           # 관리자 데스크톱 프로그램
├── requirements.txt        # Python 의존성
├── Procfile              # 배포 설정
├── railway.json          # Railway 설정
├── templates/             # HTML 템플릿
│   ├── base.html         # 기본 레이아웃
│   ├── index.html        # 홈페이지
│   ├── submit.html       # 공연 신청 폼
│   ├── admin.html        # 관리자 패널
│   └── performance_detail.html  # 공연 상세 페이지
├── static/               # 정적 파일 (CSS, JS, 이미지)
└── README.md            # 프로젝트 설명서
```

## 🎪 사용 방법

### 공연 신청하기
1. `/submit` 페이지 접속
2. 공연 정보 입력 (제목, 팀명, 설명, 장소, 가격, 날짜, 시간, 연락처)
3. 홍보 동영상 URL 및 이미지 URL 입력 (선택사항)
4. 신청서 제출

### 관리자 기능
1. `dist/admin_app.exe` 실행 (데스크톱 프로그램)
2. 승인 대기 중인 공연 확인
3. 승인 또는 거절 처리
4. 승인된 공연 관리

### 공연 정보 확인
1. 홈페이지에서 공연 목록 확인
2. 공연 카드 클릭하여 상세 정보 확인
3. 예매 문의를 위한 연락처 정보 확인

## 🔮 향후 개발 계획

- [ ] 이메일 자동 발송 시스템
- [ ] 지도 API 연동 (공연장 위치 표시)
- [ ] 소셜 미디어 연동
- [ ] 실시간 알림 시스템
- [ ] 모바일 앱 개발
- [ ] 결제 시스템 연동

## 📞 문의

프로젝트 관련 문의사항이 있으시면 언제든 연락주세요.

---

**KOPIS 공연 홍보 플랫폼** - 대중무용의 새로운 시작 🎭 