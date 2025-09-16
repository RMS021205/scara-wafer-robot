import serial
import time
import firebase_admin
from firebase_admin import credentials, db
import os
import urllib3
import requests

# 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SSL 인증서 검증 비활성화
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Firebase 초기화
cred = credentials.Certificate('/home/moas/moas-45385-firebase-adminsdk-rzp7k-d54fbd59b5.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://moas-45385-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# 시리얼 통신 초기화
ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=10
)
ser.isOpen()

def update_firebase(data_type, value):
    """Firebase 데이터베이스 업데이트 함수"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            dir_ref = db.reference()
            dir_ref.update({data_type: value})
            print(f"Firebase 업데이트 성공 - {data_type}: {value}")
            return
        except Exception:
            print(f"Firebase 업데이트 실패 ({retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            time.sleep(1)  # 재시도 전 1초 대기
            
    print(f"최대 재시도 횟수 초과 - {data_type}: {value}")

# 메인 루프
while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()
        key, value = data.split(':')
        key = key.strip()
        value = value.strip()
        
        if key == 'weight':
            update_firebase('trigger', 1)
            update_firebase('weight', float(value))
        elif key == 'weight_state':
            update_firebase('weight_state', value)
        elif key == 'wafer':
            update_firebase('wafer', value)
        elif key == 'accuracy':
            update_firebase('accuracy', value)
        
    time.sleep(0.1)
