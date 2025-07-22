import AsyncStorage from '@react-native-async-storage/async-storage';
import api from './api';
import {User, LoginResponse, RegisterResponse} from '../types';

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await api.post('/auth/login', {
        username,
        password,
      });
      
      if (response.data.success) {
        await AsyncStorage.setItem('user', JSON.stringify(response.data.user));
        // 실제 JWT 토큰이 있다면 여기에 저장
        // await AsyncStorage.setItem('authToken', response.data.token);
      }
      
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || '로그인 중 오류가 발생했습니다.');
    }
  },

  async register(userData: {
    username: string;
    password: string;
    name: string;
    email: string;
    phone?: string;
  }): Promise<RegisterResponse> {
    try {
      const response = await api.post('/auth/register', userData);
      
      if (response.data.success) {
        await AsyncStorage.setItem('user', JSON.stringify(response.data.user));
        // 실제 JWT 토큰이 있다면 여기에 저장
        // await AsyncStorage.setItem('authToken', response.data.token);
      }
      
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || '회원가입 중 오류가 발생했습니다.');
    }
  },

  async logout(): Promise<void> {
    try {
      await AsyncStorage.removeItem('user');
      await AsyncStorage.removeItem('authToken');
    } catch (error) {
      console.error('로그아웃 오류:', error);
    }
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const userStr = await AsyncStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('사용자 정보 로드 오류:', error);
      return null;
    }
  },

  async updateUser(userData: Partial<User>): Promise<void> {
    try {
      const currentUser = await this.getCurrentUser();
      if (currentUser) {
        const updatedUser = {...currentUser, ...userData};
        await AsyncStorage.setItem('user', JSON.stringify(updatedUser));
      }
    } catch (error) {
      console.error('사용자 정보 업데이트 오류:', error);
    }
  },
}; 