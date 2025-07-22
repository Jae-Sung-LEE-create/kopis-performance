import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {AppNavigatorProps, User} from '../types';

// 스크린 컴포넌트들 (실제 구현 시 import)
const HomeScreen = () => null;
const PerformanceListScreen = () => null;
const PerformanceDetailScreen = () => null;
const LoginScreen = () => null;
const RegisterScreen = () => null;
const ProfileScreen = () => null;
const SubmitScreen = () => null;
const SettingsScreen = () => null;

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// 인증 스택 (로그인/회원가입)
const AuthStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
    }}>
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

// 메인 탭 네비게이션
const MainTabNavigator = () => (
  <Tab.Navigator
    screenOptions={({route}) => ({
      tabBarIcon: ({focused, color, size}) => {
        let iconName: string;

        switch (route.name) {
          case 'Home':
            iconName = 'home';
            break;
          case 'Performances':
            iconName = 'event';
            break;
          case 'Submit':
            iconName = 'add-circle';
            break;
          case 'Profile':
            iconName = 'person';
            break;
          default:
            iconName = 'help';
        }

        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#007bff',
      tabBarInactiveTintColor: 'gray',
      headerShown: false,
    })}>
    <Tab.Screen 
      name="Home" 
      component={HomeScreen}
      options={{title: '홈'}}
    />
    <Tab.Screen 
      name="Performances" 
      component={PerformanceListScreen}
      options={{title: '공연'}}
    />
    <Tab.Screen 
      name="Submit" 
      component={SubmitScreen}
      options={{title: '신청'}}
    />
    <Tab.Screen 
      name="Profile" 
      component={ProfileScreen}
      options={{title: '프로필'}}
    />
  </Tab.Navigator>
);

// 메인 스택 네비게이션
const MainStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: {
        backgroundColor: '#007bff',
      },
      headerTintColor: '#fff',
      headerTitleStyle: {
        fontWeight: 'bold',
      },
    }}>
    <Stack.Screen 
      name="MainTabs" 
      component={MainTabNavigator}
      options={{headerShown: false}}
    />
    <Stack.Screen 
      name="PerformanceDetail" 
      component={PerformanceDetailScreen}
      options={{title: '공연 상세'}}
    />
    <Stack.Screen 
      name="Settings" 
      component={SettingsScreen}
      options={{title: '설정'}}
    />
  </Stack.Navigator>
);

const AppNavigator: React.FC<AppNavigatorProps> = ({
  user,
  onLogin,
  onLogout,
  isConnected,
}) => {
  return (
    <Stack.Navigator screenOptions={{headerShown: false}}>
      {user ? (
        <Stack.Screen name="Main" component={MainStack} />
      ) : (
        <Stack.Screen name="Auth" component={AuthStack} />
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator; 