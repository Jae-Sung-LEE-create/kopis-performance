import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {Performance} from '../types';
import api from '../services/api';

interface PerformanceDetailScreenProps {
  navigation: any;
  route: any;
}

const PerformanceDetailScreen: React.FC<PerformanceDetailScreenProps> = ({
  navigation,
  route,
}) => {
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);

  const {id} = route.params;

  useEffect(() => {
    loadPerformanceDetail();
  }, [id]);

  const loadPerformanceDetail = async () => {
    try {
      const response = await api.get(`/performances/${id}`);
      if (response.data.success) {
        setPerformance(response.data.performance);
      }
    } catch (error) {
      console.error('공연 상세 로드 오류:', error);
      Alert.alert('오류', '공연 정보를 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    try {
      const response = await api.post(`/performances/${id}/like`);
      if (response.data.success) {
        setLiked(!liked);
        if (performance) {
          setPerformance({
            ...performance,
            likes: liked ? performance.likes - 1 : performance.likes + 1,
          });
        }
      }
    } catch (error) {
      console.error('좋아요 오류:', error);
      Alert.alert('오류', '좋아요를 처리할 수 없습니다.');
    }
  };

  const handleShare = () => {
    if (performance) {
      const shareText = `${performance.title}\n${performance.group_name}\n${performance.location}\n${performance.date}`;
      // 실제 공유 기능 구현
      Alert.alert('공유', '공연 정보를 공유합니다.');
    }
  };

  const handleContact = () => {
    if (performance?.contact) {
      Linking.openURL(`tel:${performance.contact}`);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
        <ActivityIndicator size="large" color="#007bff" />
        <Text style={styles.loadingText}>공연 정보를 불러오는 중...</Text>
      </SafeAreaView>
    );
  }

  if (!performance) {
    return (
      <SafeAreaView style={styles.errorContainer}>
        <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
        <Icon name="error" size={60} color="#dc3545" />
        <Text style={styles.errorText}>공연을 찾을 수 없습니다</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.retryButtonText}>뒤로 가기</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#007bff" />
      
      <ScrollView style={styles.scrollView}>
        {/* 헤더 이미지 */}
        <View style={styles.headerImage}>
          {performance.image_url ? (
            <Text style={styles.imagePlaceholder}>공연 이미지</Text>
          ) : (
            <View style={styles.defaultImage}>
              <Icon name="event" size={80} color="#ffffff" />
            </View>
          )}
        </View>

        {/* 공연 정보 */}
        <View style={styles.content}>
          <View style={styles.titleSection}>
            <Text style={styles.title}>{performance.title}</Text>
            <Text style={styles.groupName}>{performance.group_name}</Text>
          </View>

          {/* 액션 버튼들 */}
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.actionButton, liked && styles.likedButton]}
              onPress={handleLike}>
              <Icon
                name={liked ? 'favorite' : 'favorite-border'}
                size={24}
                color={liked ? '#ffffff' : '#ff6b6b'}
              />
              <Text style={[styles.actionButtonText, liked && styles.likedButtonText]}>
                {liked ? '좋아요 취소' : '좋아요'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
              <Icon name="share" size={24} color="#007bff" />
              <Text style={styles.actionButtonText}>공유</Text>
            </TouchableOpacity>

            {performance.contact && (
              <TouchableOpacity style={styles.actionButton} onPress={handleContact}>
                <Icon name="phone" size={24} color="#28a745" />
                <Text style={styles.actionButtonText}>연락</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* 상세 정보 */}
          <View style={styles.detailsSection}>
            <Text style={styles.sectionTitle}>공연 정보</Text>
            
            <View style={styles.detailItem}>
              <Icon name="location-on" size={20} color="#666" />
              <View style={styles.detailContent}>
                <Text style={styles.detailLabel}>장소</Text>
                <Text style={styles.detailValue}>{performance.location}</Text>
              </View>
            </View>

            <View style={styles.detailItem}>
              <Icon name="event" size={20} color="#666" />
              <View style={styles.detailContent}>
                <Text style={styles.detailLabel}>날짜</Text>
                <Text style={styles.detailValue}>{performance.date}</Text>
              </View>
            </View>

            <View style={styles.detailItem}>
              <Icon name="access-time" size={20} color="#666" />
              <View style={styles.detailContent}>
                <Text style={styles.detailLabel}>시간</Text>
                <Text style={styles.detailValue}>{performance.time || '미정'}</Text>
              </View>
            </View>

            <View style={styles.detailItem}>
              <Icon name="attach-money" size={20} color="#666" />
              <View style={styles.detailContent}>
                <Text style={styles.detailLabel}>가격</Text>
                <Text style={styles.detailValue}>₩{performance.price}</Text>
              </View>
            </View>

            {performance.category && (
              <View style={styles.detailItem}>
                <Icon name="category" size={20} color="#666" />
                <View style={styles.detailContent}>
                  <Text style={styles.detailLabel}>카테고리</Text>
                  <Text style={styles.detailValue}>{performance.category}</Text>
                </View>
              </View>
            )}
          </View>

          {/* 설명 */}
          {performance.description && (
            <View style={styles.descriptionSection}>
              <Text style={styles.sectionTitle}>공연 소개</Text>
              <Text style={styles.description}>{performance.description}</Text>
            </View>
          )}

          {/* 통계 */}
          <View style={styles.statsSection}>
            <Text style={styles.sectionTitle}>통계</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{performance.likes}</Text>
                <Text style={styles.statLabel}>좋아요</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{performance.views || 0}</Text>
                <Text style={styles.statLabel}>조회수</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{performance.comments || 0}</Text>
                <Text style={styles.statLabel}>댓글</Text>
              </View>
            </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  errorText: {
    marginTop: 16,
    fontSize: 18,
    color: '#dc3545',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#007bff',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  headerImage: {
    height: 200,
    backgroundColor: '#007bff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  imagePlaceholder: {
    color: '#ffffff',
    fontSize: 16,
  },
  defaultImage: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: 20,
  },
  titleSection: {
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  groupName: {
    fontSize: 16,
    color: '#666',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 30,
    paddingVertical: 15,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  actionButton: {
    alignItems: 'center',
    padding: 10,
  },
  likedButton: {
    backgroundColor: '#ff6b6b',
    borderRadius: 8,
    padding: 10,
  },
  actionButtonText: {
    marginTop: 5,
    fontSize: 12,
    color: '#666',
  },
  likedButtonText: {
    color: '#ffffff',
  },
  detailsSection: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
    backgroundColor: '#ffffff',
    padding: 15,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2.22,
    elevation: 3,
  },
  detailContent: {
    marginLeft: 15,
    flex: 1,
  },
  detailLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  descriptionSection: {
    marginBottom: 30,
  },
  description: {
    fontSize: 16,
    color: '#333',
    lineHeight: 24,
    backgroundColor: '#ffffff',
    padding: 15,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2.22,
    elevation: 3,
  },
  statsSection: {
    marginBottom: 30,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 20,
    borderRadius: 12,
    flex: 1,
    marginHorizontal: 5,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007bff',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
});

export default PerformanceDetailScreen; 