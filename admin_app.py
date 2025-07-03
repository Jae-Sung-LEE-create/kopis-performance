import sys
import sqlite3
import os
import pickle
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QTabWidget, QMessageBox,
                             QHeaderView, QTextEdit, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 데이터베이스 파일 경로를 더 확실하게 설정
        # exe 파일이 실행되는 위치와 관계없이 항상 올바른 경로를 찾도록
        if getattr(sys, 'frozen', False):
            # exe 파일로 실행될 때
            application_path = os.path.dirname(sys.executable)
        else:
            # Python 스크립트로 실행될 때
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        # 상위 디렉토리로 이동 (dist 폴더에서 실행될 경우)
        if os.path.basename(application_path) == 'dist':
            application_path = os.path.dirname(application_path)
        
        self.db_path = os.path.join(application_path, "kopis_performances.db")
        print(f"데이터베이스 경로: {self.db_path}")
        print(f"데이터베이스 파일 존재: {os.path.exists(self.db_path)}")
        
        self.init_database()  # 데이터베이스 초기화 추가
        self.init_ui()
        self.load_data()
        
        # 30초마다 데이터 새로고침
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(30000)  # 30초
        
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # performances 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    description TEXT,
                    location TEXT,
                    price TEXT,
                    date TEXT,
                    time TEXT,
                    contact_email TEXT,
                    video_url TEXT,
                    image_url TEXT,
                    is_approved BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            print("데이터베이스 초기화 완료")
            
        except Exception as e:
            print(f"데이터베이스 초기화 오류: {e}")
        
    def init_ui(self):
        self.setWindowTitle("KOPIS 공연 홍보 플랫폼 - 관리자")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QVBoxLayout(central_widget)
        
        # 제목
        title_label = QLabel("🎭 KOPIS 공연 홍보 플랫폼 - 관리자 패널")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 승인 대기 탭
        self.create_pending_tab()
        
        # 승인된 공연 탭
        self.create_approved_tab()
        
        # 통계 탭
        self.create_stats_tab()
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.load_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(refresh_btn)
        
    def create_pending_tab(self):
        pending_widget = QWidget()
        layout = QVBoxLayout(pending_widget)
        
        # 제목
        title = QLabel("⏳ 승인 대기 중인 공연")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #e74c3c; margin: 10px;")
        layout.addWidget(title)
        
        # 테이블
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(8)
        self.pending_table.setHorizontalHeaderLabels([
            "ID", "공연명", "팀명", "장소", "날짜", "시간", "연락처", "작업"
        ])
        self.pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.pending_table)
        
        self.tab_widget.addTab(pending_widget, "승인 대기")
        
    def create_approved_tab(self):
        approved_widget = QWidget()
        layout = QVBoxLayout(approved_widget)
        
        # 제목
        title = QLabel("✅ 승인된 공연")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #27ae60; margin: 10px;")
        layout.addWidget(title)
        
        # 테이블
        self.approved_table = QTableWidget()
        self.approved_table.setColumnCount(7)
        self.approved_table.setHorizontalHeaderLabels([
            "ID", "공연명", "팀명", "장소", "날짜", "시간", "가격"
        ])
        self.approved_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.approved_table)
        
        self.tab_widget.addTab(approved_widget, "승인된 공연")
        
    def create_stats_tab(self):
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # 제목
        title = QLabel("📊 통계")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # 통계 정보
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.stats_text)
        
        self.tab_widget.addTab(stats_widget, "통계")
        
    def load_data(self):
        try:
            # 웹사이트의 pickle 데이터 파일 경로
            data_dir = os.path.join(os.path.dirname(self.db_path), "data")
            performances_file = os.path.join(data_dir, "performances.pkl")
            
            if not os.path.exists(performances_file):
                print(f"데이터 파일이 없습니다: {performances_file}")
                self.update_pending_table([])
                self.update_approved_table([])
                self.update_stats(0, 0, 0)
                return
            
            # pickle 파일에서 공연 데이터 로드
            with open(performances_file, 'rb') as f:
                performances = pickle.load(f)
            
            # 승인 대기 중인 공연
            pending_data = []
            for p in performances:
                if not p.is_approved:
                    pending_data.append([
                        p.id, p.title, p.group_name, p.location, 
                        p.date, p.time, p.contact_email
                    ])
            
            # 승인된 공연
            approved_data = []
            for p in performances:
                if p.is_approved:
                    approved_data.append([
                        p.id, p.title, p.group_name, p.location, 
                        p.date, p.time, p.price
                    ])
            
            # 테이블 업데이트
            self.update_pending_table(pending_data)
            self.update_approved_table(approved_data)
            
            # 통계 업데이트
            self.update_stats(len(pending_data), len(approved_data), len(performances))
            
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            QMessageBox.warning(self, "오류", f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    
    def update_pending_table(self, data):
        self.pending_table.setRowCount(len(data))
        
        for row, (id, title, group_name, location, date, time, contact_email) in enumerate(data):
            self.pending_table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.pending_table.setItem(row, 1, QTableWidgetItem(title))
            self.pending_table.setItem(row, 2, QTableWidgetItem(group_name))
            self.pending_table.setItem(row, 3, QTableWidgetItem(location))
            self.pending_table.setItem(row, 4, QTableWidgetItem(date))
            self.pending_table.setItem(row, 5, QTableWidgetItem(time))
            self.pending_table.setItem(row, 6, QTableWidgetItem(contact_email))
            
            # 버튼 위젯
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)
            
            approve_btn = QPushButton("✅ 승인")
            approve_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            approve_btn.clicked.connect(lambda checked, pid=id: self.approve_performance(pid))
            
            reject_btn = QPushButton("❌ 거절")
            reject_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            reject_btn.clicked.connect(lambda checked, pid=id: self.reject_performance(pid))
            
            button_layout.addWidget(approve_btn)
            button_layout.addWidget(reject_btn)
            button_layout.addStretch()
            
            self.pending_table.setCellWidget(row, 7, button_widget)
    
    def update_approved_table(self, data):
        self.approved_table.setRowCount(len(data))
        
        for row, (id, title, group_name, location, date, time, price) in enumerate(data):
            self.approved_table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.approved_table.setItem(row, 1, QTableWidgetItem(title))
            self.approved_table.setItem(row, 2, QTableWidgetItem(group_name))
            self.approved_table.setItem(row, 3, QTableWidgetItem(location))
            self.approved_table.setItem(row, 4, QTableWidgetItem(date))
            self.approved_table.setItem(row, 5, QTableWidgetItem(time))
            self.approved_table.setItem(row, 6, QTableWidgetItem(price))
    
    def update_stats(self, pending_count, approved_count, total_count):
        if total_count == 0:
            approve_rate = "N/A"
        else:
            approve_rate = f"{(approved_count/total_count*100):.1f}%"
        stats_text = f"""
📊 KOPIS 공연 홍보 플랫폼 통계

🎭 총 공연 신청: {total_count}건
⏳ 승인 대기 중: {pending_count}건
✅ 승인 완료: {approved_count}건
📈 승인률: {approve_rate} (총 {total_count}건 중)

🕐 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 관리 팁:
• 승인 대기 중인 공연을 검토하여 적절히 승인/거절하세요
• 공연 정보가 정확한지 확인하세요
• 부적절한 내용이 있는 경우 거절하세요
        """
        self.stats_text.setText(stats_text)
    
    def approve_performance(self, performance_id):
        try:
            # 웹사이트의 pickle 데이터 파일 경로
            data_dir = os.path.join(os.path.dirname(self.db_path), "data")
            performances_file = os.path.join(data_dir, "performances.pkl")
            
            if not os.path.exists(performances_file):
                QMessageBox.warning(self, "오류", "데이터 파일을 찾을 수 없습니다.")
                return
            
            # pickle 파일에서 공연 데이터 로드
            with open(performances_file, 'rb') as f:
                performances = pickle.load(f)
            
            # 해당 공연 찾아서 승인
            for p in performances:
                if p.id == performance_id:
                    p.is_approved = True
                    break
            
            # 업데이트된 데이터 저장
            with open(performances_file, 'wb') as f:
                pickle.dump(performances, f)
            
            QMessageBox.information(self, "승인 완료", f"공연 ID {performance_id}가 승인되었습니다.")
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"승인 처리 중 오류가 발생했습니다: {str(e)}")
    
    def reject_performance(self, performance_id):
        reply = QMessageBox.question(self, "거절 확인", 
                                   f"공연 ID {performance_id}를 거절하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 웹사이트의 pickle 데이터 파일 경로
                data_dir = os.path.join(os.path.dirname(self.db_path), "data")
                performances_file = os.path.join(data_dir, "performances.pkl")
                
                if not os.path.exists(performances_file):
                    QMessageBox.warning(self, "오류", "데이터 파일을 찾을 수 없습니다.")
                    return
                
                # pickle 파일에서 공연 데이터 로드
                with open(performances_file, 'rb') as f:
                    performances = pickle.load(f)
                
                # 해당 공연 제거
                performances = [p for p in performances if p.id != performance_id]
                
                # 업데이트된 데이터 저장
                with open(performances_file, 'wb') as f:
                    pickle.dump(performances, f)
                
                QMessageBox.information(self, "거절 완료", f"공연 ID {performance_id}가 거절되었습니다.")
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"거절 처리 중 오류가 발생했습니다: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 모던한 스타일
    
    # 애플리케이션 스타일
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ecf0f1;
        }
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #bdc3c7;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
        QTableWidget {
            gridline-color: #bdc3c7;
            selection-background-color: #3498db;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QHeaderView::section {
            background-color: #34495e;
            color: white;
            padding: 8px;
            border: none;
        }
    """)
    
    window = AdminApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 