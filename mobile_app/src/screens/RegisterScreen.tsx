import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  TextInput,
  Alert,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import api from '../services/api';

interface RegisterScreenProps {
  navigation: any;
}

const RegisterScreen: React.FC<RegisterScreenProps> = ({navigation}) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!formData.name || !formData.email || !formData.password) {
      Alert.alert('오류', '모든 필수 항목을 입력해주세요.');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      Alert.alert('오류', '비밀번호가 일치하지 않습니다.');
      return;
    }

    if (formData.password.length < 6) {
      Alert.alert('오류', '비밀번호는 6자 이상이어야 합니다.');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/auth/register', {
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });

      if (response.data.success) {
        Alert.alert('성공', '회원가입이 완료되었습니다!', [
          {
            text: '확인',
            onPress: () => navigation.navigate('Login'),
          },
        ]);
      }
    } catch (error) {
      console.error('회원가입 오류:', error);
      Alert.alert('오류', '회원가입에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      <ScrollView style={styles.scrollView}>
        <View style={styles.content}>
          <View style={styles.header}>
            <Icon name="person-add" size={80} color="#007bff" />
            <Text style={styles.title}>회원가입</Text>
            <Text style={styles.subtitle}>KOPIS 공연에 가입하여 다양한 공연을 만나보세요</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>이름 *</Text>
              <TextInput
                style={styles.input}
                value={formData.name}
                onChangeText={text => setFormData({...formData, name: text})}
                placeholder="이름을 입력하세요"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>이메일 *</Text>
              <TextInput
                style={styles.input}
                value={formData.email}
                onChangeText={text => setFormData({...formData, email: text})}
                placeholder="이메일을 입력하세요"
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>비밀번호 *</Text>
              <TextInput
                style={styles.input}
                value={formData.password}
                onChangeText={text => setFormData({...formData, password: text})}
                placeholder="비밀번호를 입력하세요 (6자 이상)"
                secureTextEntry
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>비밀번호 확인 *</Text>
              <TextInput
                style={styles.input}
                value={formData.confirmPassword}
                onChangeText={text => setFormData({...formData, confirmPassword: text})}
                placeholder="비밀번호를 다시 입력하세요"
                secureTextEntry
              />
            </View>

            <TouchableOpacity
              style={[styles.registerButton, loading && styles.registerButtonDisabled]}
              onPress={handleRegister}
              disabled={loading}>
              <Text style={styles.registerButtonText}>
                {loading ? '가입 중...' : '회원가입'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.loginButton}
              onPress={() => navigation.navigate('Login')}>
              <Text style={styles.loginButtonText}>
                이미 계정이 있으신가요? 로그인
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    color: '#333',
  },
  registerButton: {
    backgroundColor: '#007bff',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  registerButtonDisabled: {
    backgroundColor: '#6c757d',
  },
  registerButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loginButton: {
    alignItems: 'center',
    marginTop: 20,
  },
  loginButtonText: {
    color: '#007bff',
    fontSize: 16,
  },
});

export default RegisterScreen; 