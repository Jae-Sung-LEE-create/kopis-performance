# 추가 기재 항목 및 참고 자료

## 1. 추가 기재 항목 및 내용

### 1.1 기술적 구현
- **Flask 웹 애플리케이션**: Python Flask 기반 RESTful API 설계
- **KOPIS API 연동**: 한국공연예술진흥원 공연정보 실시간 동기화
- **카카오 소셜 로그인**: OAuth 2.0 기반 사용자 인증
- **데이터 분석**: Pandas, Plotly를 활용한 공연 데이터 분석 및 시각화
- **추천 시스템**: Scikit-learn 기반 개인화 추천 알고리즘

### 1.2 사용자 경험 및 보안
- **반응형 웹 디자인**: 모바일 퍼스트 접근법, CSS Grid/Flexbox 활용
- **웹 접근성**: WCAG 2.1 가이드라인 준수
- **보안**: HTTPS, SQL Injection 방지, XSS 공격 방지
- **개인정보보호**: 최소한의 정보 수집, 데이터 암호화

### 1.3 성능 및 확장성
- **성능 최적화**: 이미지 최적화, 캐싱 전략, 데이터베이스 인덱싱
- **모듈화 설계**: MVC 패턴, 컴포넌트 기반 개발
- **배포**: Docker 컨테이너화, CI/CD 파이프라인

## 2. 활용 데이터 출처

### 2.1 공식 API
- **KOPIS API**: https://www.kopis.or.kr/openApi/restful/pblprfr
  - 전국 공연장 정보, 공연 일정, 예매 정보
  - 실시간 업데이트, 공공데이터 포털 무료 제공
- **공공데이터 포털**: https://www.data.go.kr/
  - 문화체육관광부 공연예술 통계
  - 서울시 문화시설 정보

### 2.2 외부 서비스
- **카카오 로그인 API**: OAuth 2.0 인증, 사용자 기본 정보
- **YouTube Data API**: 공연 홍보 영상 임베딩
- **Unsplash API**: 공연 이미지 샘플 데이터

### 2.3 통계 데이터
- **문화체육관광부**: 연도별 공연 관객 수, 매출액, 공연장 수
- **한국문화관광연구원**: 문화 소비 패턴, 선호도 조사

## 3. 참고문헌

### 3.1 기술 문서
1. **Flask Documentation** (2024) - https://flask.palletsprojects.com/
2. **SQLAlchemy Documentation** (2024) - https://docs.sqlalchemy.org/
3. **CSS Grid Layout** (2024) - MDN Web Docs
4. **Python for Data Analysis** (2017) - Wes McKinney, O'Reilly Media
5. **Scikit-learn User Guide** (2024) - https://scikit-learn.org/

### 3.2 공연예술 및 플랫폼
6. **한국공연예술진흥원 연차보고서** (2023)
7. **문화체육관광부 공연예술 통계** (2023)
8. **Digital Transformation in Arts and Culture** (2022) - Ben Walmsley, Routledge
9. **Platform Revolution** (2016) - Geoffrey G. Parker, W. W. Norton & Company

### 3.3 사용자 경험 및 보안
10. **Don't Make Me Think** (2014) - Steve Krug, New Riders
11. **Web Accessibility Guidelines** (2024) - W3C WAI
12. **OWASP Top Ten** (2021) - https://owasp.org/Top10/
13. **개인정보보호법 해설서** (2023) - 개인정보보호위원회

### 3.4 학술 논문
14. **"A Survey of Collaborative Filtering Techniques"** (2009) - Su, X., Khoshgoftaar, T.M.
15. **"Digital Platforms in the Cultural Sector"** (2020) - Ben Walmsley, Cultural Trends

### 3.5 온라인 리소스
16. **Stack Overflow** (2024) - https://stackoverflow.com/
17. **GitHub** (2024) - https://github.com/
18. **Material Design Guidelines** (2024) - https://material.io/design

---

*이 문서는 KOPIS 기반 공연 플랫폼 개발 프로젝트의 핵심 기술, 데이터 출처, 참고 자료를 간결하게 정리한 것입니다.* 