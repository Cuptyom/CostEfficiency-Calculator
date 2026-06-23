import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест PySide6")
        self.setGeometry(300, 300, 400, 300)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.label = QLabel("Нажми кнопку 👇", alignment=Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 20px; padding: 20px;")
        layout.addWidget(self.label)
        
        button = QPushButton("Нажми меня!")
        button.setStyleSheet("font-size: 16px; padding: 10px;")
        button.clicked.connect(self.on_click)
        layout.addWidget(button)
    
    def on_click(self):
        self.label.setText("✅ Всё работает!") #komment Vani


#комментарий от Артёма
app = QApplication(sys.argv)
window = TestWindow()
window.show()
sys.exit(app.exec())