"""API 서버 상태 테스트"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SUNOAPI_KEY")
url = "https://api.sunoapi.org/api/v1/generate/credit"

print("서버 상태 확인 중...")

try:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 200:
            print(f"✅ 서버 정상! 크레딧: {data.get('data')}")
        else:
            print(f"⚠️ API 오류: {data.get('msg')}")
    elif response.status_code == 524:
        print("❌ 서버 타임아웃 (524) - 아직 불안정")
    else:
        print(f"❌ 오류: {response.status_code}")

except requests.exceptions.Timeout:
    print("❌ 요청 타임아웃 - 서버 응답 없음")
except requests.exceptions.ConnectionError:
    print("❌ 연결 실패 - 서버 다운 또는 네트워크 문제")
except Exception as e:
    print(f"❌ 오류: {e}")
