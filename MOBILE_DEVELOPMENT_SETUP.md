# 📱 React Native 모바일 앱 개발 환경 설정 가이드

## 🎯 목표
기존 KOPIS 공연 웹사이트와 연동되는 React Native 모바일 앱을 개발합니다.

## 🛠️ 1단계: 필수 소프트웨어 설치

### 1.1 Node.js 설치
```bash
# Node.js 공식 사이트에서 다운로드
# https://nodejs.org/

# LTS 버전 (18.x 이상) 다운로드 및 설치
# Windows: .msi 파일 다운로드 후 설치
# macOS: .pkg 파일 다운로드 후 설치
# Linux: 패키지 매니저 사용

# 설치 확인
node --version  # v18.x.x 이상
npm --version   # 9.x.x 이상
```

### 1.2 React Native CLI 설치
```bash
# React Native CLI 전역 설치
npm install -g @react-native-community/cli

# 설치 확인
npx react-native --version
```

### 1.3 Android 개발 환경 (Android 앱 개발용)

#### Android Studio 설치
1. **Android Studio 다운로드**: https://developer.android.com/studio
2. **설치 시 선택사항**:
   - Android SDK
   - Android SDK Platform
   - Android Virtual Device
   - Performance (Intel HAXM)

#### 환경변수 설정 (Windows)
```bash
# 시스템 환경변수에 추가
ANDROID_HOME = C:\Users\USERNAME\AppData\Local\Android\Sdk
PATH += %ANDROID_HOME%\platform-tools
PATH += %ANDROID_HOME%\tools
PATH += %ANDROID_HOME%\tools\bin
```

#### Android SDK 설정
```bash
# Android Studio에서 SDK Manager 열기
# 다음 항목들 설치:
# - Android SDK Platform 33 (API Level 33)
# - Android SDK Build-Tools 33.0.0
# - Android Emulator
# - Android SDK Platform-Tools
```

### 1.4 iOS 개발 환경 (macOS만, iOS 앱 개발용)
```bash
# Xcode 설치 (App Store에서)
# Command Line Tools 설치
xcode-select --install

# CocoaPods 설치
sudo gem install cocoapods
```

## 🚀 2단계: 모바일 앱 프로젝트 설정

### 2.1 프로젝트 디렉토리로 이동
```bash
# 현재 프로젝트 디렉토리에서
cd mobile_app
```

### 2.2 의존성 설치
```bash
# npm 패키지 설치
npm install

# 또는 yarn 사용 시
yarn install
```

### 2.3 Metro 번들러 시작
```bash
# Metro 번들러 시작 (새 터미널에서)
npm start
# 또는
npx react-native start
```

## 📱 3단계: 앱 실행 및 테스트

### 3.1 Android 앱 실행
```bash
# Android 에뮬레이터 또는 실제 기기 연결 후
npm run android
# 또는
npx react-native run-android
```

### 3.2 iOS 앱 실행 (macOS만)
```bash
# iOS 시뮬레이터 또는 실제 기기 연결 후
npm run ios
# 또는
npx react-native run-ios
```

## 🔧 4단계: 개발 도구 설정

### 4.1 VS Code 확장 프로그램 설치
```bash
# 추천 확장 프로그램:
# - React Native Tools
# - TypeScript and JavaScript Language Features
# - ES7+ React/Redux/React-Native snippets
# - Prettier - Code formatter
# - ESLint
```

### 4.2 개발자 도구
```bash
# React Native Debugger 설치 (선택사항)
# https://github.com/jhen0409/react-native-debugger

# Flipper 설치 (디버깅 도구)
# https://fbflipper.com/
```

## 📁 5단계: 프로젝트 구조 이해

```
mobile_app/
├── android/                 # Android 네이티브 코드
├── ios/                    # iOS 네이티브 코드
├── src/
│   ├── components/         # 재사용 가능한 컴포넌트
│   ├── screens/           # 화면 컴포넌트
│   ├── services/          # API 서비스
│   ├── navigation/        # 네비게이션 설정
│   ├── types/            # TypeScript 타입 정의
│   └── utils/            # 유틸리티 함수
├── package.json           # 프로젝트 설정 및 의존성
├── tsconfig.json          # TypeScript 설정
└── README.md             # 프로젝트 문서
```

## 🎨 6단계: 첫 번째 화면 개발

### 6.1 홈 화면 생성
```typescript
// src/screens/HomeScreen.tsx
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';

const HomeScreen = ({navigation}) => {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>KOPIS 공연</Text>
        <Text style={styles.subtitle}>다양한 공연을 만나보세요</Text>
      </View>
      
      <View style={styles.content}>
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate('Performances')}>
          <Text style={styles.buttonText}>공연 목록 보기</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate('Submit')}>
          <Text style={styles.buttonText}>공연 신청하기</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    padding: 20,
    backgroundColor: '#007bff',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: 'white',
    opacity: 0.8,
  },
  content: {
    padding: 20,
  },
  button: {
    backgroundColor: '#007bff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default HomeScreen;
```

### 6.2 네비게이션에 화면 추가
```typescript
// src/navigation/AppNavigator.tsx 수정
import HomeScreen from '../screens/HomeScreen';

// 기존 코드에서 HomeScreen 컴포넌트 교체
const HomeScreen = () => <HomeScreen />;
```

## 🔗 7단계: API 연동 테스트

### 7.1 API 서비스 테스트
```typescript
// src/services/api.ts에서 API 테스트
import api from './api';

// 공연 목록 가져오기 테스트
const testAPI = async () => {
  try {
    const response = await api.get('/performances');
    console.log('API 응답:', response.data);
  } catch (error) {
    console.error('API 오류:', error);
  }
};

// 컴포넌트에서 호출
useEffect(() => {
  testAPI();
}, []);
```

## 🧪 8단계: 테스트 및 디버깅

### 8.1 개발자 메뉴 열기
```bash
# Android: Ctrl + M 또는 Cmd + M
# iOS: Cmd + D
# 또는 디바이스에서 흔들기
```

### 8.2 디버깅 옵션
- **Reload**: 앱 새로고침
- **Debug**: Chrome 개발자 도구로 디버깅
- **Enable Hot Reloading**: 코드 변경 시 자동 새로고침
- **Show Inspector**: UI 요소 검사

## 📱 9단계: 실제 기기에서 테스트

### 9.1 Android 기기
```bash
# 1. 기기에서 개발자 옵션 활성화
# 2. USB 디버깅 활성화
# 3. USB로 컴퓨터에 연결
# 4. 앱 실행
npm run android
```

### 9.2 iOS 기기 (macOS만)
```bash
# 1. Xcode에서 기기 등록
# 2. USB로 연결
# 3. 앱 실행
npm run ios
```

## 🚀 10단계: 빌드 및 배포 준비

### 10.1 Android 릴리즈 빌드
```bash
cd android
./gradlew assembleRelease
```

### 10.2 iOS 릴리즈 빌드 (macOS만)
```bash
cd ios
xcodebuild -workspace KopisMobileApp.xcworkspace \
  -scheme KopisMobileApp \
  -configuration Release \
  -destination generic/platform=iOS \
  -archivePath KopisMobileApp.xcarchive archive
```

## 🎯 다음 단계

### 단기 목표 (1-2주)
1. ✅ 개발 환경 설정
2. 🔄 기본 화면 구현
3. 🔄 API 연동 테스트
4. 🔄 네비게이션 구현

### 중기 목표 (3-4주)
1. 🔄 모든 화면 구현
2. 🔄 사용자 인증 구현
3. 🔄 이미지 업로드 기능
4. 🔄 오프라인 지원

### 장기 목표 (1-2개월)
1. 🔄 앱스토어 배포 준비
2. 🔄 성능 최적화
3. 🔄 사용자 테스트
4. 🔄 실제 배포

## 🆘 문제 해결

### 일반적인 문제들
1. **Metro 번들러 오류**: `npm start --reset-cache`
2. **Android 빌드 오류**: `cd android && ./gradlew clean`
3. **iOS 빌드 오류**: `cd ios && pod install`
4. **의존성 문제**: `npm install` 또는 `yarn install`

### 도움말
- **React Native 공식 문서**: https://reactnative.dev/
- **GitHub Issues**: 프로젝트 저장소에서 이슈 확인
- **Stack Overflow**: 개발 관련 질문 검색

이제 모바일 앱 개발을 시작할 준비가 완료되었습니다! 🎉 