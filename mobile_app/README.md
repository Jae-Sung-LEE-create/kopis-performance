# KOPIS 공연 모바일 앱

React Native로 개발된 KOPIS 공연 홍보 플랫폼의 모바일 앱입니다.

## 🚀 시작하기

### 1. 개발 환경 설정

```bash
# Node.js 설치 (v18 이상)
# https://nodejs.org/

# React Native CLI 설치
npm install -g @react-native-community/cli

# 프로젝트 클론
git clone <repository-url>
cd mobile_app

# 의존성 설치
npm install
```

### 2. 필요한 라이브러리

```bash
# 네비게이션
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context

# API 통신
npm install axios

# 로컬 저장소
npm install @react-native-async-storage/async-storage

# 이미지 처리
npm install react-native-image-picker
npm install react-native-fast-image

# 아이콘
npm install react-native-vector-icons

# 애니메이션
npm install react-native-gesture-handler react-native-reanimated

# QR 코드
npm install react-native-qrcode-scanner

# 푸시 알림
npm install @react-native-firebase/messaging

# 지도
npm install react-native-maps

# 소셜 공유
npm install react-native-share
```

### 3. 프로젝트 구조

```
src/
├── components/          # 재사용 가능한 컴포넌트
│   ├── PerformanceCard.tsx
│   ├── PerformanceDetail.tsx
│   ├── LoginForm.tsx
│   ├── SubmitForm.tsx
│   └── LoadingSpinner.tsx
├── screens/            # 화면 컴포넌트
│   ├── HomeScreen.tsx
│   ├── PerformanceListScreen.tsx
│   ├── PerformanceDetailScreen.tsx
│   ├── LoginScreen.tsx
│   ├── RegisterScreen.tsx
│   ├── ProfileScreen.tsx
│   ├── SubmitScreen.tsx
│   └── SettingsScreen.tsx
├── services/           # API 및 서비스
│   ├── api.ts
│   ├── auth.ts
│   └── storage.ts
├── navigation/         # 네비게이션 설정
│   └── AppNavigator.tsx
├── utils/             # 유틸리티 함수
│   ├── constants.ts
│   └── helpers.ts
├── types/             # TypeScript 타입 정의
│   └── index.ts
└── assets/            # 이미지, 폰트 등
    ├── images/
    └── fonts/
```

## 📱 주요 기능

### 1. 공연 목록/상세 보기
- 웹사이트와 동일한 공연 데이터 표시
- 카테고리별, 지역별 필터링
- 검색 기능
- 좋아요 기능

### 2. 공연 신청
- 카메라로 이미지 촬영
- GPS 위치 정보 자동 입력
- 실시간 미리보기
- 드래프트 저장

### 3. 사용자 인증
- 로그인/회원가입
- 소셜 로그인 (카카오, 구글)
- 자동 로그인
- 비밀번호 재설정

### 4. 푸시 알림
- 새로운 공연 알림
- 승인 상태 변경 알림
- 좋아요 알림
- 댓글 알림

### 5. 오프라인 지원
- 로컬 데이터베이스 (SQLite)
- 오프라인에서 기본 기능 사용
- 온라인 복귀 시 자동 동기화

## 🔧 개발 가이드

### 1. API 연동

```typescript
// services/api.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://kopis-performance.onrender.com/api/mobile';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// 요청 인터셉터 (토큰 추가)
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 처리)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 토큰 만료 시 로그아웃
      AsyncStorage.removeItem('authToken');
      // 로그인 화면으로 이동
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 2. 인증 관리

```typescript
// services/auth.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from './api';

export interface User {
  id: number;
  username: string;
  name: string;
  email: string;
  phone?: string;
  is_admin: boolean;
}

export interface LoginResponse {
  success: boolean;
  user: User;
  message: string;
}

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    
    if (response.data.success) {
      await AsyncStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  },

  async register(userData: {
    username: string;
    password: string;
    name: string;
    email: string;
    phone?: string;
  }): Promise<LoginResponse> {
    const response = await api.post('/auth/register', userData);
    
    if (response.data.success) {
      await AsyncStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  },

  async logout(): Promise<void> {
    await AsyncStorage.removeItem('user');
    await AsyncStorage.removeItem('authToken');
  },

  async getCurrentUser(): Promise<User | null> {
    const userStr = await AsyncStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};
```

### 3. 공연 목록 컴포넌트

```typescript
// screens/PerformanceListScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import api from '../services/api';
import PerformanceCard from '../components/PerformanceCard';

interface Performance {
  id: number;
  title: string;
  group_name: string;
  category: string;
  location: string;
  date: string;
  time: string;
  price: string;
  image_url?: string;
  description: string;
  likes: number;
}

export default function PerformanceListScreen({ navigation }) {
  const [performances, setPerformances] = useState<Performance[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const loadPerformances = async (pageNum = 1, refresh = false) => {
    try {
      const response = await api.get('/performances', {
        params: {
          page: pageNum,
          per_page: 20,
        },
      });

      if (response.data.success) {
        if (refresh) {
          setPerformances(response.data.performances);
        } else {
          setPerformances(prev => [...prev, ...response.data.performances]);
        }
        
        setHasMore(response.data.pagination.has_next);
        setPage(pageNum);
      }
    } catch (error) {
      console.error('공연 목록 로드 오류:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadPerformances();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadPerformances(1, true);
  };

  const loadMore = () => {
    if (hasMore && !loading) {
      loadPerformances(page + 1);
    }
  };

  const renderPerformance = ({ item }: { item: Performance }) => (
    <PerformanceCard
      performance={item}
      onPress={() => navigation.navigate('PerformanceDetail', { id: item.id })}
    />
  );

  if (loading && page === 1) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={performances}
        renderItem={renderPerformance}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.1}
        ListFooterComponent={
          hasMore && (
            <View style={styles.loadingMore}>
              <ActivityIndicator size="small" color="#007bff" />
            </View>
          )
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingMore: {
    padding: 20,
    alignItems: 'center',
  },
});
```

## 🚀 빌드 및 배포

### 1. Android 빌드

```bash
# Android Studio 설치 후
cd android
./gradlew assembleRelease
```

### 2. iOS 빌드

```bash
# Xcode 설치 후
cd ios
pod install
npx react-native run-ios --configuration Release
```

### 3. 앱스토어 배포

#### Google Play Store
1. Google Play Console 계정 생성
2. 앱 등록 및 정보 입력
3. APK/AAB 파일 업로드
4. 심사 대기 및 출시

#### Apple App Store
1. Apple Developer 계정 생성
2. App Store Connect에서 앱 등록
3. IPA 파일 업로드
4. 심사 대기 및 출시

## 📊 성능 최적화

### 1. 이미지 최적화
- FastImage 사용으로 캐싱 최적화
- 이미지 크기 조정
- 지연 로딩 구현

### 2. 네트워크 최적화
- API 응답 캐싱
- 요청 중복 방지
- 오프라인 지원

### 3. 메모리 최적화
- 컴포넌트 메모이제이션
- 불필요한 리렌더링 방지
- 이미지 메모리 관리

## 🔒 보안

### 1. 데이터 보호
- 민감한 정보 암호화 저장
- 네트워크 통신 HTTPS 사용
- 토큰 기반 인증

### 2. 앱 보안
- 코드 난독화
- 디버그 모드 비활성화
- 루트/탈옥 감지

## 📈 분석 및 모니터링

### 1. 사용자 행동 분석
- Firebase Analytics 연동
- 사용자 플로우 추적
- 성능 메트릭 수집

### 2. 오류 모니터링
- Crashlytics 연동
- 실시간 오류 알림
- 성능 병목 지점 식별

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 