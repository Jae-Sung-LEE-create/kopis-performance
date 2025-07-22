import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  TextInput,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import api from '../services/api';

interface SubmitScreenProps {
  navigation: any;
}

const SubmitScreen: React.FC<SubmitScreenProps> = ({navigation}) => {
  const [formData, setFormData] = useState({
    title: '',
    group_name: '',
    location: '',
    date: '',
    time: '',
    price: '',
    category: '',
    description: '',
    contact: '',
  });

  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!formData.title || !formData.group_name || !formData.location) {
      Alert.alert('오류', '필수 항목을 모두 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/performances', formData);
      if (response.data.success) {
        Alert.alert('성공', '공연이 성공적으로 등록되었습니다!', [
          {
            text: '확인',
            onPress: () => navigation.navigate('Home'),
          },
        ]);
      }
    } catch (error) {
      console.error('공연 등록 오류:', error);
      Alert.alert('오류', '공연 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Icon name="add-circle" size={40} color="#007bff" />
          <Text style={styles.title}>공연 신청</Text>
          <Text style={styles.subtitle}>새로운 공연을 등록해주세요</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>공연 제목 *</Text>
            <TextInput
              style={styles.input}
              value={formData.title}
              onChangeText={text => setFormData({...formData, title: text})}
              placeholder="공연 제목을 입력하세요"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>그룹명 *</Text>
            <TextInput
              style={styles.input}
              value={formData.group_name}
              onChangeText={text => setFormData({...formData, group_name: text})}
              placeholder="그룹명을 입력하세요"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>장소 *</Text>
            <TextInput
              style={styles.input}
              value={formData.location}
              onChangeText={text => setFormData({...formData, location: text})}
              placeholder="공연 장소를 입력하세요"
            />
          </View>

          <View style={styles.row}>
            <View style={[styles.inputGroup, styles.halfWidth]}>
              <Text style={styles.label}>날짜</Text>
              <TextInput
                style={styles.input}
                value={formData.date}
                onChangeText={text => setFormData({...formData, date: text})}
                placeholder="YYYY-MM-DD"
              />
            </View>

            <View style={[styles.inputGroup, styles.halfWidth]}>
              <Text style={styles.label}>시간</Text>
              <TextInput
                style={styles.input}
                value={formData.time}
                onChangeText={text => setFormData({...formData, time: text})}
                placeholder="HH:MM"
              />
            </View>
          </View>

          <View style={styles.row}>
            <View style={[styles.inputGroup, styles.halfWidth]}>
              <Text style={styles.label}>가격</Text>
              <TextInput
                style={styles.input}
                value={formData.price}
                onChangeText={text => setFormData({...formData, price: text})}
                placeholder="0"
                keyboardType="numeric"
              />
            </View>

            <View style={[styles.inputGroup, styles.halfWidth]}>
              <Text style={styles.label}>카테고리</Text>
              <TextInput
                style={styles.input}
                value={formData.category}
                onChangeText={text => setFormData({...formData, category: text})}
                placeholder="스트릿댄스, 힙합 등"
              />
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>연락처</Text>
            <TextInput
              style={styles.input}
              value={formData.contact}
              onChangeText={text => setFormData({...formData, contact: text})}
              placeholder="전화번호 또는 이메일"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>공연 설명</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={formData.description}
              onChangeText={text => setFormData({...formData, description: text})}
              placeholder="공연에 대한 자세한 설명을 입력하세요"
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
          </View>

          <TouchableOpacity
            style={[styles.submitButton, loading && styles.submitButtonDisabled]}
            onPress={handleSubmit}
            disabled={loading}>
            <Text style={styles.submitButtonText}>
              {loading ? '등록 중...' : '공연 등록하기'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#ffffff',
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 10,
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  form: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  halfWidth: {
    width: '48%',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
  },
  textArea: {
    height: 100,
  },
  submitButton: {
    backgroundColor: '#007bff',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  submitButtonDisabled: {
    backgroundColor: '#6c757d',
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default SubmitScreen; 