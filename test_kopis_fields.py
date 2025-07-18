#!/usr/bin/env python3
"""
KOPIS API 필드명 확인 테스트
"""

import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

def test_kopis_api():
    """KOPIS API 응답 확인"""
    api_key = os.getenv('KOPIS_API_KEY', 'bbfe976d316347c8928fe3a2169ab8fe')
    if not api_key:
        print("❌ KOPIS_API_KEY가 설정되지 않았습니다.")
        return
    
    print(f"🔑 API 키: {api_key[:10]}...")
    
    # 1. 공연 목록 API 테스트
    print("\n📋 1. 공연 목록 API 테스트")
    url = "http://www.kopis.or.kr/openApi/restful/pblprfr"
    params = {
        'service': api_key,
        'stdate': '20241201',
        'eddate': '20241231',
        'rows': 5,
        'cpage': 1
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        print(f"✅ 응답 상태: {response.status_code}")
        
        # XML 파싱
        root = ET.fromstring(response.content)
        print(f"📊 총 공연 수: {len(root.findall('.//db'))}")
        
        # 첫 번째 공연의 모든 필드 확인
        first_performance = root.find('.//db')
        if first_performance is not None:
            print("\n🔍 첫 번째 공연의 모든 필드:")
            for child in first_performance:
                print(f"  {child.tag}: {child.text}")
        
    except Exception as e:
        print(f"❌ 공연 목록 API 오류: {e}")
    
    # 2. 공연 상세 정보 API 테스트
    print("\n📋 2. 공연 상세 정보 API 테스트")
    # 먼저 공연 ID 가져오기
    try:
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        first_performance = root.find('.//db')
        
        if first_performance is not None:
            mt20id = first_performance.find('mt20id')
            if mt20id is not None and mt20id.text:
                performance_id = mt20id.text
                print(f"🎭 테스트할 공연 ID: {performance_id}")
                
                # 상세 정보 조회
                detail_url = f"http://www.kopis.or.kr/openApi/restful/pblprfr/{performance_id}"
                detail_params = {'service': api_key}
                
                detail_response = requests.get(detail_url, params=detail_params)
                detail_response.raise_for_status()
                
                detail_root = ET.fromstring(detail_response.content)
                detail_performance = detail_root.find('.//db')
                
                if detail_performance is not None:
                    print("\n🔍 상세 정보의 모든 필드:")
                    for child in detail_performance:
                        print(f"  {child.tag}: {child.text}")
                else:
                    print("❌ 상세 정보를 찾을 수 없습니다.")
            else:
                print("❌ 공연 ID를 찾을 수 없습니다.")
        else:
            print("❌ 공연 데이터를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 상세 정보 API 오류: {e}")

if __name__ == "__main__":
    test_kopis_api() 