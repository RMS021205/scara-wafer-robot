import tkinter as tk
from PIL import Image, ImageTk
import firebase_admin
from firebase_admin import credentials, db
import os
import concurrent.futures
import time

class ImageUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Semiconductor Process Monitoring')
        self.root.geometry('1920x1080')  # 전체 화면 크기 설정

        # Firebase 인증 정보 (경로를 환경에 맞게 수정)
        cred = credentials.Certificate('/home/moas/google-drive/moas-45385-firebase-adminsdk-rzp7k-d54fbd59b5.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://moas-45385-default-rtdb.asia-southeast1.firebasedatabase.app/'})

        # Firebase 데이터 참조 설정
        self.wafer_ref = db.reference('wafer')
        self.accuracy_ref = db.reference('accuracy')
        self.weight_ref = db.reference('weight')
        self.weight_state_ref = db.reference('weight_state')
        self.image_path_ref = db.reference('image_path')

        # 배경 이미지 설정
        try:
            self.bg_image = Image.open("/home/moas/Desktop/background.jpg")
            print("배경 이미지 로드 성공")
        except Exception as e:
            print(f"배경 이미지 로드 중 오류: {e}")
            return

        self.update_background()  # 배경 이미지 업데이트

        # 라벨에 표시할 데이터 변수 초기화
        self.wafer_var = tk.StringVar()
        self.accuracy_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.weight_state_var = tk.StringVar()

        # 데이터를 표시할 라벨 생성
        self.create_data_label(self.root, "Wafer", self.wafer_var, 1250, 220, 490, 140, "#F5F5F5", "#000000")
        self.create_data_label(self.root, "Weight", self.weight_var, 1250, 390, 490, 140, "#F5F5F5", "#000000")
        self.create_data_label(self.root, "Accuracy", self.accuracy_var, 1250, 560, 490, 140, "#F5F5F5", "#000000")
        self.create_data_label(self.root, "State", self.weight_state_var, 1250, 730, 490, 140, "#F5F5F5", "#000000")

        # 웨이퍼 이미지를 표시할 라벨 생성
        self.image_label = tk.Label(self.root)
        self.image_label.place(x=100, y=100, width=850, height=850)

        # 창 크기가 변경될 때 호출되는 함수
        self.root.bind("<Configure>", self.on_resize)

        # 비동기 스레드 풀 생성
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        # 데이터를 주기적으로 업데이트하고 UI를 새로고침
        self.update_data_and_ui()

    def update_background(self):
        """창 크기에 맞게 배경 이미지를 업데이트하는 함수"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        resized_bg = self.bg_image.resize((width, height), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(resized_bg)
        print(f"배경 이미지 크기: {width}x{height}")

        if hasattr(self, 'background_label'):
            self.background_label.config(image=self.bg_photo)
            self.background_label.image = self.bg_photo
        else:
            self.background_label = tk.Label(self.root, image=self.bg_photo)
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.background_label.lower()  # 배경을 다른 위젯 뒤로 이동

    def on_resize(self, event):
        """창 크기 변경 이벤트를 처리하는 함수"""
        self.update_background()

    def create_data_label(self, parent, text, variable, x, y, width, height, bg_color, fg_color):
        """데이터를 표시할 라벨을 생성하는 함수"""
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
        new_wafer = self.wafer_ref.get()
        new_accuracy = self.accuracy_ref.get()
        new_weight = self.weight_ref.get()
        new_weight_state = self.weight_state_ref.get()
        image_path = self.image_path_ref.get()

        # 데이터가 변경된 경우에만 UI 업데이트
        if new_wafer != self.wafer_var.get():
            self.update_wafer(new_wafer)
        if new_accuracy != self.accuracy_var.get():
            self.update_accuracy(new_accuracy)
        if new_weight != self.weight_var.get():
            self.update_weight(new_weight)
        if new_weight_state != self.weight_state_var.get():
            self.update_weight_state(new_weight_state)
        if image_path:  # 이미지 경로가 있을 경우에만 업데이트
            self.update_image(image_path)

        # UI 즉시 갱신
        self.root.update_idletasks()

    def update_wafer(self, wafer):
        """웨이퍼 상태를 업데이트하는 함수"""
        formatted_text = f"Wafer  : {wafer}"
        self.wafer_var.set(formatted_text)

    def update_accuracy(self, accuracy):
        """정확도를 업데이트하는 함수"""
        formatted_text = f"Accuracy  : {accuracy} %"
        self.accuracy_var.set(formatted_text)

    def update_weight(self, weight):
        """웨이트 값을 업데이트하는 함수"""
        formatted_text = f"Weight  : {weight} g"
        self.weight_var.set(formatted_text)

    def update_weight_state(self, weight_state):
        """웨이트 상태를 업데이트하는 함수"""
        formatted_text = f"State  : {weight_state}"
        self.weight_state_var.set(formatted_text)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageUpdaterApp(root)
    root.mainloop()

