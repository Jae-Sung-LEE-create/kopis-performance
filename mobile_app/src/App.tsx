import React, {useEffect, useState} from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import SplashScreen from 'react-native-splash-screen';
import NetInfo from 'react-native-netinfo';

import AppNavigator from './navigation/AppNavigator';
import {authService} from './services/auth';
import {User} from './types';

const App = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    initializeApp();
    setupNetworkListener();
  }, []);

  const initializeApp = async () => {
    try {
      // 스플래시 스크린 표시
      SplashScreen.show();

      // 사용자 정보 로드
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);

      // 2초 후 스플래시 스크린 숨김
      setTimeout(() => {
        SplashScreen.hide();
        setIsLoading(false);
      }, 2000);
    } catch (error) {
      console.error('앱 초기화 오류:', error);
      SplashScreen.hide();
      setIsLoading(false);
    }
  };

  const setupNetworkListener = () => {
    NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected ?? true);
    });
  };

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    await authService.logout();
    setUser(null);
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007bff" />
        <Text style={styles.loadingText}>KOPIS 공연 앱을 시작합니다...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            인터넷 연결이 없습니다. 일부 기능이 제한될 수 있습니다.
          </Text>
        </View>
      )}

      <NavigationContainer>
        <AppNavigator
          user={user}
          onLogin={handleLogin}
          onLogout={handleLogout}
          isConnected={isConnected}
        />
      </NavigationContainer>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666666',
  },
  offlineBanner: {
    backgroundColor: '#ff6b6b',
    padding: 8,
    alignItems: 'center',
  },
  offlineText: {
    color: '#ffffff',
    fontSize: 12,
    textAlign: 'center',
  },
});

export default App; 