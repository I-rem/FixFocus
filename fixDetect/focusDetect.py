import sys
import csv
import os
import cv2
import mediapipe as mp
import time
import math
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QMenuBar, QAction, QMenu, QMessageBox
from PyQt5.QtMultimedia import QSound
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class DikkatTakibiApp(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.mp_drawing = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)

        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  

        self.dikkatli = 0
        self.dikkatsiz = 0
        self.uyari_sayisi = 0
        self.start_time = time.time()
        self.dikkatsiz_start_time = None

        self.setWindowTitle("🧠 Dikkat Takibi")
        self.setGeometry(100, 100, 1280, 800)  

        # Menü çubuğu
        self.menu_bar = self.menuBar()

        # Ayarlar menüsü
        self.settings_menu = self.create_menu("Ayarlar", self.menu_bar)
        self.menu_bar.addMenu(self.settings_menu)

        # Grafik menüsü
        self.graph_menu = self.create_menu("Grafikler", self.settings_menu)
        self.graph_action_show = QAction("Grafiği Göster", self)
        self.graph_action_show.triggered.connect(self.open_graph_window)
        self.graph_menu.addAction(self.graph_action_show)
        self.settings_menu.addMenu(self.graph_menu)

        # Tema menüsü
        self.theme_menu = self.create_menu("Tema", self.settings_menu)
        self.theme_action_light = QAction("Light Tema", self)
        self.theme_action_light.triggered.connect(self.set_light_theme)
        self.theme_action_dark = QAction("Dark Tema", self)
        self.theme_action_dark.triggered.connect(self.set_dark_theme)
        self.theme_menu.addAction(self.theme_action_light)
        self.theme_menu.addAction(self.theme_action_dark)
        self.settings_menu.addMenu(self.theme_menu)

        # Görüntü alanı
        self.video_label = QLabel(self)
        self.video_label.setStyleSheet("border: 5px solid #4CAF50; border-radius: 10px;")

        # Skor ve uyarı göstergeleri
        self.skor_label = QLabel("Skor: %0.0f" % 0)
        self.uyari_label = QLabel("Uyarı Sayısı: 0")
        self.skor_label.setStyleSheet("font-size: 20px; color: #2ECC71; font-weight: bold;")
        self.uyari_label.setStyleSheet("font-size: 20px; color: #E74C3C; font-weight: bold;")

        # Layout 
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.skor_label)
        info_layout.addWidget(self.uyari_label)

        self.layout = QVBoxLayout()
        self.layout.addLayout(info_layout)
        self.layout.addWidget(self.video_label)

        widget = QWidget(self)
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Verileri tutacak listeler
        self.skor_data = []
        self.time_data = []

        # Grafik penceresi
        self.graph_window = None

        # Varsayılan tema light mode
        self.is_dark_mode = False
        self.load_theme("\\style\\light_mode.qss")

        # Menü çubuğunu pencerede göster
        self.setMenuBar(self.menu_bar)

        # Sesli uyarı
        self.sound = QSound("uyari.mp3")

        # Log dosyası
        self.csv_file = "log.csv"
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Zaman", "Dikkatli", "Dikkatsiz", "Skor", "Uyari Sayisi"])

    def create_menu(self, menu_name, parent_menu):
        """Özel bir menü oluştur ve genişliği artır."""
        menu = QMenu(menu_name, parent_menu)
        return menu

    def load_theme(self, theme_file):
        """Belirtilen QSS dosyasını yükler ve uygular."""
        try:
            with open(theme_file, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print(f"Hata: '{theme_file}' dosyası bulunamadı.")

    def set_light_theme(self):
        """Light tema uygular."""
        self.load_theme("\\style\\light_mode.qss")
        self.is_dark_mode = False

    def set_dark_theme(self):
        """Dark tema uygular."""
        self.load_theme("C\\style\\dark_mode.qss")
        self.is_dark_mode = True

    def open_graph_window(self):
        """Grafiği ayrı bir pencerede göster."""
        if self.graph_window is None:
            self.graph_window = QWidget()
            self.graph_window.setWindowTitle("Dikkat Grafiği")
            self.graph_window.setGeometry(200, 200, 600, 400)

            # Matplotlib Widget'i oluştur
            self.fig, self.ax = plt.subplots(figsize=(5, 3))
            self.ax.set_title("Dikkat Durumu")
            self.ax.set_xlabel("Zaman (sn)")
            self.ax.set_ylabel("Dikkatli Yüzdesi")

            # Grafik widget'i
            self.canvas = FigureCanvas(self.fig)
            layout = QVBoxLayout()
            layout.addWidget(self.canvas)
            self.graph_window.setLayout(layout)

        self.graph_window.show()
        self.update_graph()

    def update_graph(self):
        """Grafiği güncelle."""
        if self.graph_window and self.graph_window.isVisible():
            self.ax.clear()
            self.ax.plot(self.time_data, self.skor_data, label="Dikkat Skoru", color="green")
            self.ax.set_title("Dikkat Durumu")
            self.ax.set_xlabel("Zaman (sn)")
            self.ax.set_ylabel("Dikkatli Yüzdesi")
            self.ax.legend(loc="upper left")
            self.canvas.draw_idle()

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

        # Dynamically adjust the green border size to match the camera frame size
        self.video_label.setStyleSheet(f"border: 5px solid #4CAF50; border-radius: 10px; "
                                       f"width: {width}px; height: {height}px;")

        # Verileri kaydet
        self.skor_data.append(skor)
        self.time_data.append(time.time() - self.start_time)

        # Grafik güncelle
        self.update_graph()

        # Log dosyasına yaz
        with open(self.csv_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([time.strftime("%H:%M:%S"), self.dikkatli, self.dikkatsiz, f"%{skor:.1f}", self.uyari_sayisi])

        # Dikkatsiz süre kontrolü
        self.check_dikkatsiz_sure()

    def check_dikkatsiz_sure(self):
        if self.dikkatsiz_start_time:
            elapsed = time.time() - self.dikkatsiz_start_time
            if elapsed >= 30:
                self.show_dikkatsiz_bildirim()
                self.dikkatsiz_start_time = None

    def show_dikkatsiz_bildirim(self):
        self.uyari_sayisi += 1
        self.sound.play()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Dikkatsizsiniz!")
        msg.setWindowTitle("Uyarı")
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DikkatTakibiApp()
    window.show()
    sys.exit(app.exec_())
