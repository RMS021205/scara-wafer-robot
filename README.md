# 🛠 반도체 웨이퍼 공정 자동화 및 모니터링 시스템
[프로젝트 동영상 보기](https://www.youtube.com/watch?v=tviXzWfLnSM)
## 📖 프로젝트 개요
본 프로젝트는 **반도체 웨이퍼 공정의 자동화와 실시간 모니터링**을 구현한 시스템입니다.  
- **Arduino**: 모터, 액추에이터, 로드셀을 제어하여 웨이퍼를 층별로 이동 및 분류  
- **Intel RealSense Depth 카메라**: 웨이퍼 이미지 및 깊이 데이터 캡처  
- **Python GUI + Firebase**: 실시간 데이터 모니터링 및 상태 표시  
- **딥러닝 모델 (MobileNetV2)**: 웨이퍼 정상/파손 판별  

---

## 🛠 주요 기능

### 1️⃣ Arduino 제어
- Herkulex 모터, Z 액추에이터, 그리퍼 제어  
- 웨이퍼 층별 이동 및 배치  
- 로드셀 기반 무게 측정  
- 정상/파손 웨이퍼 자동 분류  

### 2️⃣ Python GUI (Tkinter)
- 웨이퍼 상태, 무게, 판별 정확도 실시간 표시  
- 뎁스 이미지 포함 웨이퍼 이미지 표시  
- 비동기 처리로 UI와 데이터 동시 갱신  

### 3️⃣ Python 시리얼 → Firebase
- Arduino 데이터 수신  
- Firebase 실시간 데이터베이스 업데이트  

### 4️⃣ RealSense 뎁스 카메라
- Firebase trigger 기반 이미지 캡처  
- 깊이 데이터를 컬러맵으로 변환 후 저장  
- 저장된 이미지 경로 Firebase 업데이트  

### 5️⃣ 딥러닝 기반 웨이퍼 판별
- MobileNetV2 기반 이미지 분류 모델  
- 정상/파손 웨이퍼 예측  
- 예측 결과 및 정확도 Firebase 업데이트  

---

## ⚙️ 요구사항

### Hardware
- Arduino (Herkulex 모터 및 Z 액추에이터)  
- Intel RealSense Depth 카메라  
- 로드셀  

### Software
- Python 3.8 이상  
- 주요 라이브러리:  
  `firebase-admin`, `pyserial`, `opencv-python`, `numpy`, `Pillow`, `watchdog`, `tensorflow`, `keras`, `pyrealsense2`  
- Tkinter (Python 표준 라이브러리)  
- Arduino IDE (Herkulex 라이브러리 포함)  

---

## 🚀 설치 및 실행 가이드

### 1️⃣ Arduino
- Arduino 코드 업로드  
- 모터/액추에이터/로드셀 연결 확인  

### 2️⃣ Python 라이브러리 설치

pip install firebase-admin pyserial opencv-python numpy Pillow watchdog tensorflow keras pyrealsense2
### 3️⃣ Firebase 설정

Admin SDK 인증 파일 준비

### 4️⃣ 실행 순서

Arduino 전원 ON

Python 시리얼 → Firebase 스크립트 실행

RealSense 뎁스 카메라 캡처 스크립트 실행

GUI 스크립트 실행

필요 시 딥러닝 모델 학습 및 예측 실행

### 5️⃣ 사용법
---
Arduino 슬레이브로 웨이퍼 층별 이동 및 그리퍼 작동

로드셀로 웨이퍼 무게 측정 → 정상/파손 판별

시리얼 데이터 Firebase 전송

GUI에서 실시간 웨이퍼 상태 확인

Trigger 신호 발생 시 RealSense 뎁스 카메라로 깊이 이미지 캡처

딥러닝 모델로 웨이퍼 판별 → Firebase 업데이트
