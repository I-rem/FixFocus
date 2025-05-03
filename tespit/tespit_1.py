import sys
import cv2
import mediapipe as mp
import time
import math
import csv
import os
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox, QHBoxLayout
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent  # Import QMediaPlayer for MP3 playback

class DikkatTakibiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.mp_drawing = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)

        self.dikkatli = 0
        self.dikkatsiz = 0
        self.uyari_sayisi = 0
        self.start_time = time.time()
        self.dikkatsiz_start_time = None

        self.setWindowTitle("🧠 Dikkat Takibi")
        self.setGeometry(100, 100, 1000, 700)

        # Görüntü alanı
        self.video_label = QLabel(self)

        # Skor ve uyarı göstergeleri
        self.skor_label = QLabel("Skor: %0.0f" % 0)
        self.uyari_label = QLabel("Uyarı Sayısı: 0")
        self.skor_label.setStyleSheet("font-size: 16px; color: green;")
        self.uyari_label.setStyleSheet("font-size: 16px; color: red;")

        # Layout
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.skor_label)
        info_layout.addWidget(self.uyari_label)

        self.layout = QVBoxLayout()
        self.layout.addLayout(info_layout)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.dikkatsiz_timer = QTimer(self)
        self.dikkatsiz_timer.timeout.connect(self.check_dikkatsiz_sure)
        self.dikkatsiz_timer.start(1000)

        # Log dosyası
        self.csv_file = "log.csv"
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Zaman", "Dikkatli", "Dikkatsiz", "Skor", "Uyari Sayisi"])

        # MP3 ses çalma
        self.player = QMediaPlayer(self)
        self.sound = QMediaContent(QUrl.fromLocalFile("uyari.mp3"))  # MP3 dosyasını yüklüyoruz
        self.player.setMedia(self.sound)

    def calculate_head_pose(self, landmarks):
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        dx = abs(left_eye.x - right_eye.x)
        dy = abs(left_eye.y - right_eye.y)
        return math.degrees(math.atan2(dy, dx))

    def update_frame(self):
        success, frame = self.cap.read()
        if not success:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        durum = ""
        renk = (255, 255, 0)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
                )
                pitch = self.calculate_head_pose(face_landmarks.landmark)
                if pitch < 10:
                    self.dikkatli += 1
                    self.dikkatsiz_start_time = None
                    durum = "Dikkatli"
                    renk = (0, 255, 0)
                else:
                    self.dikkatsiz += 1
                    if self.dikkatsiz_start_time is None:
                        self.dikkatsiz_start_time = time.time()
                    durum = "Dikkatsiz"
                    renk = (0, 0, 255)

                cv2.putText(frame, durum, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, renk, 2)

        try:
            skor = (self.dikkatli / (self.dikkatli + self.dikkatsiz)) * 100
        except ZeroDivisionError:
            skor = 0.0

        # GUI metin güncelleme
        self.skor_label.setText(f"Skor: %{skor:.1f}")
        self.uyari_label.setText(f"Uyarı Sayısı: {self.uyari_sayisi}")

        # PyQt video güncelle
        height, width, channel = frame.shape
        q_image = QImage(frame.data, width, height, 3 * width, QImage.Format_BGR888)
        self.video_label.setPixmap(QPixmap.fromImage(q_image))

        # CSV log
        with open(self.csv_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([time.strftime("%H:%M:%S"), self.dikkatli, self.dikkatsiz, f"%{skor:.1f}", self.uyari_sayisi])

    def check_dikkatsiz_sure(self):
        if self.dikkatsiz_start_time:
            elapsed = time.time() - self.dikkatsiz_start_time
            if elapsed >= 30:
                self.show_dikkatsiz_bildirim()
                self.dikkatsiz_start_time = None

    def show_dikkatsiz_bildirim(self):
        self.uyari_sayisi += 1
        self.player.play()  # MP3 ses çalıyoruz
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Dikkatli Ol!")
        msg.setText("30 saniyeden fazla dikkatsiz kaldınız!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        self.cap.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DikkatTakibiApp()
    window.show()
    sys.exit(app.exec_())
