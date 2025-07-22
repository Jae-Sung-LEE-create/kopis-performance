import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  RefreshControl,
  TextInput,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {Performance} from '../types';
import api from '../services/api';

interface PerformanceListScreenProps {
  navigation: any;
  route: any;
}

const PerformanceListScreen: React.FC<PerformanceListScreenProps> = ({
  navigation,
  route,
}) => {
  const [performances, setPerformances] = useState<Performance[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  const loadPerformances = async (pageNum = 1, refresh = false) => {
    try {
      const params: any = {
        page: pageNum,
        per_page: 20,
      };

      if (searchText) {
        params.search = searchText;
      }

      if (selectedCategory) {
        params.category = selectedCategory;
      }

      const response = await api.get('/performances', {params});

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

  useEffect(() => {
    // 검색어나 카테고리가 변경되면 새로 로드
    if (!loading) {
      setPerformances([]);
      setPage(1);
      setHasMore(true);
      loadPerformances(1, true);
    }
  }, [searchText, selectedCategory]);

  const onRefresh = () => {
    setRefreshing(true);
    loadPerformances(1, true);
  };

  const loadMore = () => {
    if (hasMore && !loading) {
      loadPerformances(page + 1);
    }
  };

  const renderPerformance = ({item}: {item: Performance}) => (
    <TouchableOpacity
      style={styles.performanceCard}
      onPress={() => navigation.navigate('PerformanceDetail', {id: item.id})}>
      <View style={styles.cardImage}>
        {item.image_url ? (
          <Text style={styles.imagePlaceholder}>이미지</Text>
        ) : (
          <Icon name="event" size={40} color="#ccc" />
        )}
      </View>
      <View style={styles.cardContent}>
        <Text style={styles.cardTitle} numberOfLines={2}>
          {item.title}
        </Text>
        <Text style={styles.cardGroup} numberOfLines={1}>
          {item.group_name}
        </Text>
        <View style={styles.cardInfo}>
          <View style={styles.infoItem}>
            <Icon name="location-on" size={14} color="#666" />
            <Text style={styles.infoText}>{item.location}</Text>
          </View>
          <View style={styles.infoItem}>
            <Icon name="event" size={14} color="#666" />
            <Text style={styles.infoText}>{item.date}</Text>
          </View>
        </View>
        <View style={styles.cardFooter}>
          <Text style={styles.cardPrice}>₩{item.price}</Text>
          <View style={styles.likeContainer}>
            <Icon name="favorite" size={16} color="#ff6b6b" />
            <Text style={styles.likeCount}>{item.likes}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="공연 검색..."
          value={searchText}
          onChangeText={setSearchText}
        />
      </View>
      
      <View style={styles.categoryContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <TouchableOpacity
            style={[
              styles.categoryChip,
              selectedCategory === '' && styles.categoryChipActive,
            ]}
            onPress={() => setSelectedCategory('')}>
            <Text
              style={[
                styles.categoryChipText,
                selectedCategory === '' && styles.categoryChipTextActive,
              ]}>
              전체
            </Text>
          </TouchableOpacity>
          {['스트릿댄스', '힙합', '팝핑', '브레이킹', '왁킹', '락킹'].map(
            category => (
              <TouchableOpacity
                key={category}
                style={[
                  styles.categoryChip,
                  selectedCategory === category && styles.categoryChipActive,
                ]}
                onPress={() => setSelectedCategory(category)}>
                <Text
                  style={[
                    styles.categoryChipText,
                    selectedCategory === category && styles.categoryChipTextActive,
                  ]}>
                  {category}
                </Text>
              </TouchableOpacity>
            ),
          )}
        </ScrollView>
      </View>
    </View>
  );

  if (loading && page === 1) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
        <ActivityIndicator size="large" color="#007bff" />
        <Text style={styles.loadingText}>공연 목록을 불러오는 중...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      <FlatList
        data={performances}
        renderItem={renderPerformance}
        keyExtractor={item => item.id.toString()}
        ListHeaderComponent={renderHeader}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.1}
        ListFooterComponent={
          hasMore && (
            <View style={styles.loadingMore}>
              <ActivityIndicator size="small" color="#007bff" />
              <Text style={styles.loadingMoreText}>더 많은 공연을 불러오는 중...</Text>
            </View>
          )
        }
        ListEmptyComponent={
          !loading && (
            <View style={styles.emptyContainer}>
              <Icon name="event-busy" size={60} color="#ccc" />
              <Text style={styles.emptyText}>공연이 없습니다</Text>
              <Text style={styles.emptySubtext}>
                다른 검색어나 카테고리를 시도해보세요
              </Text>
            </View>
          )
        }
      />
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
  header: {
    backgroundColor: '#ffffff',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginBottom: 15,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    height: 40,
    fontSize: 16,
    color: '#333',
  },
  categoryContainer: {
    marginBottom: 10,
  },
  categoryChip: {
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  categoryChipActive: {
    backgroundColor: '#007bff',
    borderColor: '#007bff',
  },
  categoryChipText: {
    fontSize: 14,
    color: '#666',
  },
  categoryChipTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  performanceCard: {
    backgroundColor: '#ffffff',
    marginHorizontal: 15,
    marginVertical: 8,
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
  cardImage: {
    height: 120,
    backgroundColor: '#e9ecef',
    justifyContent: 'center',
    alignItems: 'center',
  },
  imagePlaceholder: {
    color: '#666',
    fontSize: 14,
  },
  cardContent: {
    padding: 15,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  cardGroup: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  cardInfo: {
    marginBottom: 10,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 3,
  },
  infoText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 5,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007bff',
  },
  likeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  likeCount: {
    fontSize: 12,
    color: '#666',
    marginLeft: 3,
  },
  loadingMore: {
    padding: 20,
    alignItems: 'center',
  },
  loadingMoreText: {
    marginTop: 8,
    fontSize: 14,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default PerformanceListScreen; 