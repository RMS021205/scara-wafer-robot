import numpy as np
import cv2
import pyrealsense2 as rs
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Firebase 초기화
cred = credentials.Certificate('/home/moas/google-drive/moas-45385-firebase-adminsdk-rzp7k-d54fbd59b5.json')  # 인증 정보 파일 경로 수정
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://moas-45385-default-rtdb.asia-southeast1.firebasedatabase.app/' 
})

# Firebase 데이터 참조
trigger_ref = db.reference('trigger')

# 파이프라인 설정
pipeline = rs.pipeline()
config = rs.config()

# 스트림 활성화
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

# align 객체 생성
align_to = rs.stream.color
align = rs.align(align_to)

try:
    while True:
        # Firebase에서 trigger 상태 가져오기
        trigger = trigger_ref.get()
        print(f"현재 트리거 값: {trigger}")  # 디버그 메시지 추가

        if trigger == 1:
            print("카메라 파이프라인 시작")  # 카메라 파이프라인 시작 알림
            # 파이프라인 시작
            pipeline.start(config)

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
            image_path = "/home/moas/google-drive/test_image_files/depth_color.png"

            # 깊이 이미지 저장
            cv2.imwrite(image_path, depth_color_image)

            print(f"깊이 이미지 저장 완료: {image_path}")

            # Firebase trigger 값을 0으로 리셋
            trigger_ref.set(0)

            # 파이프라인 중지
            pipeline.stop()
            print("카메라 파이프라인 중지 완료")

finally:
    # 종료 시 파이프라인 중지
    if pipeline:
        pipeline.stop()
        print("파이프라인이 안전하게 종료되었습니다.")

