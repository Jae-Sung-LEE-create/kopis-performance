import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface ProfileScreenProps {
  navigation: any;
}

const ProfileScreen: React.FC<ProfileScreenProps> = ({navigation}) => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Icon name="person" size={60} color="#ffffff" />
          </View>
          <Text style={styles.name}>사용자</Text>
          <Text style={styles.email}>user@example.com</Text>
        </View>

        <View style={styles.content}>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>내 활동</Text>
            
            <TouchableOpacity style={styles.menuItem}>
              <Icon name="favorite" size={24} color="#ff6b6b" />
              <Text style={styles.menuText}>좋아요한 공연</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem}>
              <Icon name="event" size={24} color="#007bff" />
              <Text style={styles.menuText}>내가 등록한 공연</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem}>
              <Icon name="history" size={24} color="#28a745" />
              <Text style={styles.menuText}>최근 본 공연</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>설정</Text>
            
            <TouchableOpacity style={styles.menuItem}>
              <Icon name="notifications" size={24} color="#ffc107" />
              <Text style={styles.menuText}>알림 설정</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem}>
              <Icon name="language" size={24} color="#17a2b8" />
              <Text style={styles.menuText}>언어 설정</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem}>
              <Icon name="help" size={24} color="#6f42c1" />
              <Text style={styles.menuText}>도움말</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>계정</Text>
            
            <TouchableOpacity style={styles.menuItem}>
              <Icon name="edit" size={24} color="#007bff" />
              <Text style={styles.menuText}>프로필 수정</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem}>
              <Icon name="lock" size={24} color="#dc3545" />
              <Text style={styles.menuText}>비밀번호 변경</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem}>
              <Icon name="logout" size={24} color="#6c757d" />
              <Text style={styles.menuText}>로그아웃</Text>
              <Icon name="chevron-right" size={24} color="#ccc" />
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
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#007bff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  email: {
    fontSize: 16,
    color: '#666',
  },
  content: {
    padding: 20,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2.22,
    elevation: 3,
  },
  menuText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    marginLeft: 15,
  },
});

export default ProfileScreen; 