# -*- coding: utf-8 -*-
import os
import numpy as np
import tensorflow as tf
import time
import cv2
import tkinter as tk
from PIL import Image, ImageTk
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import firebase_admin
from firebase_admin import credentials, firestore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pyrealsense2 as rs

# Google Drive 마운트 (Colab 환경에서 사용)
from google.colab import drive
drive.mount('/content/gdrive')

# Firebase Admin SDK 초기화
cred_path = '/content/gdrive/MyDrive/moas-383a3-firebase-adminsdk-ucoh0-124d3f807a.json'
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://moas-383a3-default-rtdb.firebaseio.com/'
    })
    print("Firebase 초기화 완료")
else:
    raise FileNotFoundError(f"Firebase 인증 파일이 존재하지 않습니다: {cred_path}")

# 카메라 파이프라인 설정
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
align_to = rs.stream.color
align = rs.align(align_to)

# 데이터셋 경로 설정
root_dir = '/content/gdrive/MyDrive/dataset/wafer_image/'
train_dir = '/content/gdrive/MyDrive/dataset/wafer_image/train'
test_image_dir = os.path.join(root_dir, 'test/test_image_files/')
IMG_WIDTH = 224
IMG_HEIGHT = 224
batch_size = 64  # 적절한 배치 크기 설정

# 데이터 증강 및 학습용 데이터 생성기
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    validation_split=0.15  # 15%는 검증 데이터
)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(IMG_WIDTH, IMG_HEIGHT),
    batch_size=batch_size,
    class_mode='sparse',
    subset='training'
)

validation_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(IMG_WIDTH, IMG_HEIGHT),
    batch_size=batch_size,
    class_mode='sparse',
    subset='validation'
)

# MobileNetV2 모델 로드 및 구성
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(IMG_WIDTH, IMG_HEIGHT, 3))
model = Sequential()
model.add(base_model)
model.add(Flatten())
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(2, activation='softmax'))

# 모델 컴파일
model.compile(
    loss='sparse_categorical_crossentropy',
    optimizer=tf.keras.optimizers.Adam(1e-4),
    metrics=['accuracy']
)

# 모델 학습
history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=15,
    callbacks=[EarlyStopping(monitor='val_loss', patience=5), ModelCheckpoint('best_model.keras', monitor='val_accuracy', save_best_only=True)]
)

# Keras 형식으로 모델 저장
model.save('/content/gdrive/MyDrive/dataset/saved_model.keras')  # Keras 형식으로 저장

# Firebase 업데이트 함수
def update_firebase(pred_str, probability):
    db = firestore.client()
    doc_ref = db.collection('predictions').document('last_prediction')
    doc_ref.set({
        'prediction': pred_str,
        'accuracy': probability
    })
    print("Firebase에 업데이트 완료")

def predict_and_update_firebase(image_path):
    if os.path.exists(image_path) and not os.path.isdir(image_path):  # 이미지 파일인지 확인
        # 이미지 로드 및 전처리
        img = tf.io.read_file(image_path)
        img = tf.image.decode_png(img, channels=3)
        img = tf.image.resize(img, [IMG_WIDTH, IMG_HEIGHT])
        img = img / 255.0  # 정규화
        img_array = tf.expand_dims(img, 0)  # 배치 차원 추가

        # 예측 수행
        try:
            with tf.device('/GPU:0'):  # GPU에서 강제 실행
                pred = model.predict(img_array)
        except RuntimeError:
            print("GPU를 사용할 수 없습니다. CPU로 예측을 수행합니다.")
            pred = model.predict(img_array)

        # 예측된 클래스 및 정확도 계산
        class_names = ['broken', 'normal']
        pred_str = class_names[np.argmax(pred)]  # 가장 높은 확률을 가진 클래스 선택
        probability = "{0:0.2f}".format(100 * max(pred[0]))  # 정확도 계산

        # 콘솔에 예측 결과 출력
        print(f"Predicted: {pred_str}, Accuracy: {probability}%")

        # Firebase에 결과 업데이트
        update_firebase(pred_str, probability)
    else:
        print(f"이미지 파일을 찾을 수 없습니다: {image_path}")

# GUI 설정
class ImageUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Semiconductor Process Monitoring')
        self.root.geometry('1920x1080')  # 전체 화면 크기 설정

        # 데이터 표시할 라벨 생성
        self.wafer_var = tk.StringVar()
        self.accuracy_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.weight_state_var = tk.StringVar()
        
        self.create_data_label(self.root, "Wafer", self.wafer_var, 1250, 220, 490, 140, "#F5F5F5", "#000000")
        self.create_data_label(self.root, "Weight", self.weight_var, 1250, 390, 490, 140, "#F5F5F5", "#000000")
        self.create_data_label(self.root, "Accuracy", self.accuracy_var, 1250, 560, 490, 140, "#F5F5F5", "#000000")
        self.create_data_label(self.root, "State", self.weight_state_var, 1250, 730, 490, 140, "#F5F5F5", "#000000")

        # 웨이퍼 이미지를 표시할 라벨 생성
        self.image_label = tk.Label(self.root)
        self.image_label.place(x=100, y=100, width=850, height=850)

        # 비동기 스레드 풀 생성
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        # 데이터를 주기적으로 업데이트하고 UI를 새로고침
        self.update_data_and_ui()

    def create_data_label(self, parent, text, variable, x, y, width, height, bg_color, fg_color):
        frame = tk.Frame(parent, bg=bg_color, bd=0, relief=tk.FLAT, width=width, height=height)
        frame.place(x=x, y=y)
        frame.pack_propagate(False)
        label = tk.Label(frame, textvariable=variable, font=('Helvetica', 35, 'bold'), bg=bg_color, fg=fg_color)
        label.pack(fill=tk.BOTH, expand=True)

    def update_data_and_ui(self):
        """Firebase에서 데이터를 가져와 UI를 업데이트하는 함수"""
        self.executor.submit(self.fetch_and_update_ui)  # 비동기로 작업 처리
        self.root.after(1000, self.update_data_and_ui)  # 1초마다 업데이트

    def fetch_and_update_ui(self):
        """Firebase에서 데이터를 가져오고, 변경된 경우에만 UI를 업데이트하는 함수"""
        new_wafer = db.reference('wafer').get()
        new_accuracy = db.reference('accuracy').get()
        new_weight = db.reference('weight').get()
        new_weight_state = db.reference('weight_state').get()
        image_path = db.reference('image_path').get()

        # 데이터가 변경된 경우에만 UI 업데이트
        if new_wafer != self.wafer_var.get():
            self.wafer_var.set(f"Wafer: {new_wafer}")
        if new_accuracy != self.accuracy_var.get():
            self.accuracy_var.set(f"Accuracy: {new_accuracy} %")
        if new_weight != self.weight_var.get():
            self.weight_var.set(f"Weight: {new_weight} g")
        if new_weight_state != self.weight_state_var.get():
            self.weight_state_var.set(f"State: {new_weight_state}")
        if image_path and os.path.exists(image_path):
            self.update_image(image_path)

        # UI 즉시 갱신
        self.root.update_idletasks()

    def update_image(self, image_path):
        """이미지 경로를 기반으로 이미지를 업데이트하는코드의 남은 부분을 완성하고, 전체 통합 코드를 아래에 제공합니다. 이 코드는 Jetson Nano에서 카메라를 통해 이미지를 캡처하고, GUI를 통해 해당 이미지를 표시하며, Google Colab에서 실시간으로 이미지 판별 및 Firebase 업데이트를 수행합니다.

### 최종 통합 코드 (계속)

```python
    def update_image(self, image_path):
        """이미지 경로를 기반으로 이미지를 업데이트하는 함수"""
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)

                # 이미지 모드가 'RGB'가 아니면 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                img = img.resize((850, 850), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.config(image=img_tk)
                self.image_label.image = img_tk
                print(f"새로운 이미지로 업데이트: {image_path}")
            except Exception as e:
                print(f"이미지 로드 중 오류: {e}")
        else:
            print(f"이미지를 찾을 수 없습니다: {image_path}")

# 카메라 코드 실행
trigger_ref = db.reference('trigger')

# 카메라 파이프라인 시작
pipeline.start(config)

try:
    while True:
        # Firebase에서 trigger 상태 가져오기
        trigger = trigger_ref.get()
        print(f"현재 트리거 값: {trigger}")  # 디버그 메시지 추가

        if trigger == 1:
            print("카메라 파이프라인 시작")  # 카메라 파이프라인 시작 알림
            
            # 프레임 받기
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)

            # Depth 프레임 가져오기
            depth_frame = aligned_frames.get_depth_frame()

            if not depth_frame:
                print("깊이 프레임을 가져오는 데 실패했습니다.")
                continue

            # 컬러맵 설정 및 depth 프레임을 컬러맵으로 변환
            colorizer = rs.colorizer()
            colorizer.set_option(rs.option.color_scheme, 0)  # 다른 컬러맵 옵션으로 테스트 (0, 1, 2 등)
            depth_color_image = np.asanyarray(colorizer.colorize(depth_frame).get_data())

            # 이미지 저장 경로
            image_path = "/home/moas/google-drive/dataset/wafer_image/test/test_image_files/depth_color.png"

            # 깊이 이미지 저장
            cv2.imwrite(image_path, depth_color_image)

            print(f"깊이 이미지 저장 완료: {image_path}")

            # Firebase trigger 값을 0으로 리셋
            trigger_ref.set(0)

            # 이미지 판별 및 Firebase 업데이트
            predict_and_update_firebase(image_path)

            # 파이프라인 중지
            pipeline.stop()
            print("카메라 파이프라인 중지 완료")

finally:
    # 종료 시 파이프라인 중지
    if pipeline:
        pipeline.stop()
        print("파이프라인이 안전하게 종료되었습니다.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageUpdaterApp(root)
    root.mainloop()

