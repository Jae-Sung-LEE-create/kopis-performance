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

interface HomeScreenProps {
  navigation: any;
}

const HomeScreen: React.FC<HomeScreenProps> = ({navigation}) => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#007bff" />
      
      <ScrollView style={styles.scrollView}>
        {/* 헤더 섹션 */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Icon name="theater-comedy" size={40} color="white" />
            <Text style={styles.title}>KOPIS 공연</Text>
            <Text style={styles.subtitle}>다양한 공연을 만나보세요</Text>
          </View>
        </View>

        {/* 메인 콘텐츠 */}
        <View style={styles.content}>
          {/* 빠른 액션 버튼들 */}
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => navigation.navigate('Performances')}>
              <Icon name="event" size={24} color="#007bff" />
              <Text style={styles.actionButtonText}>공연 목록</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => navigation.navigate('Submit')}>
              <Icon name="add-circle" size={24} color="#28a745" />
              <Text style={styles.actionButtonText}>공연 신청</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => navigation.navigate('Profile')}>
              <Icon name="person" size={24} color="#ffc107" />
              <Text style={styles.actionButtonText}>내 정보</Text>
            </TouchableOpacity>
          </View>

          {/* 통계 카드 */}
          <View style={styles.statsContainer}>
            <Text style={styles.sectionTitle}>오늘의 공연</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statCard}>
                <Text style={styles.statNumber}>15</Text>
                <Text style={styles.statLabel}>진행중</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statNumber}>8</Text>
                <Text style={styles.statLabel}>예정</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statNumber}>3</Text>
                <Text style={styles.statLabel}>신규</Text>
              </View>
            </View>
          </View>

          {/* 추천 공연 */}
          <View style={styles.recommendationsContainer}>
            <Text style={styles.sectionTitle}>추천 공연</Text>
            <View style={styles.recommendationCard}>
              <View style={styles.recommendationImage} />
              <View style={styles.recommendationContent}>
                <Text style={styles.recommendationTitle}>스트릿댄스 쇼케이스</Text>
                <Text style={styles.recommendationLocation}>홍대 거리</Text>
                <Text style={styles.recommendationDate}>2024.01.15 19:00</Text>
                <Text style={styles.recommendationPrice}>₩15,000</Text>
              </View>
            </View>
          </View>

          {/* 카테고리별 공연 */}
          <View style={styles.categoriesContainer}>
            <Text style={styles.sectionTitle}>카테고리별 공연</Text>
            <View style={styles.categoryGrid}>
              {['스트릿댄스', '힙합', '팝핑', '브레이킹', '왁킹', '락킹'].map((category, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.categoryCard}
                  onPress={() => navigation.navigate('Performances', {category})}>
                  <Text style={styles.categoryText}>{category}</Text>
                </TouchableOpacity>
              ))}
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
  scrollView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#007bff',
    paddingTop: 20,
    paddingBottom: 30,
  },
  headerContent: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 10,
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: 'white',
    opacity: 0.9,
  },
  content: {
    padding: 20,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 30,
  },
  actionButton: {
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
    minWidth: 80,
  },
  actionButtonText: {
    marginTop: 8,
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  statsContainer: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
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
  recommendationsContainer: {
    marginBottom: 30,
  },
  recommendationCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  recommendationImage: {
    height: 120,
    backgroundColor: '#e9ecef',
  },
  recommendationContent: {
    padding: 15,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  recommendationLocation: {
    fontSize: 14,
    color: '#666',
    marginBottom: 3,
  },
  recommendationDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 3,
  },
  recommendationPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007bff',
  },
  categoriesContainer: {
    marginBottom: 30,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    width: '48%',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2.22,
    elevation: 3,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
});

export default HomeScreen; 