export interface User {
  id: number;
  username: string;
  name: string;
  email: string;
  phone?: string;
  is_admin: boolean;
  created_at?: string;
}

export interface Performance {
  id: number;
  title: string;
  group_name: string;
  category: string;
  location: string;
  address?: string;
  date: string;
  time: string;
  price: string;
  image_url?: string;
  description: string;
  contact_email?: string;
  purchase_methods?: string[];
  video_url?: string;
  ticket_url?: string;
  booking_phone?: string;
  booking_website?: string;
  likes: number;
  is_approved: boolean;
  created_at?: string;
  is_kopis_synced?: boolean;
}

export interface LoginResponse {
  success: boolean;
  user: User;
  message: string;
}

export interface RegisterResponse {
  success: boolean;
  user: User;
  message: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PerformancesResponse {
  success: boolean;
  performances: Performance[];
  pagination: PaginationInfo;
}

export interface PerformanceDetailResponse {
  success: boolean;
  performance: Performance;
}

export interface LikeResponse {
  success: boolean;
  is_liked: boolean;
  likes_count: number;
  message: string;
}

export interface CategoriesResponse {
  success: boolean;
  categories: string[];
}

export interface LocationsResponse {
  success: boolean;
  locations: string[];
}

export interface QRCodeResponse {
  success: boolean;
  qr_code: string;
  download_url: string;
}

export interface NavigationProps {
  navigation: any;
  route: any;
}

export interface AppNavigatorProps {
  user: User | null;
  onLogin: (user: User) => void;
  onLogout: () => void;
  isConnected: boolean;
} 