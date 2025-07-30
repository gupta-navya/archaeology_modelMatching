
from PyQt5.QtWidgets import QDialog, QPushButton, QLabel, QComboBox, QProgressBar
from PyQt5 import uic
import pathlib

class SelectMethodWindow(QDialog,):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_widgets()
        uic.loadUi("./view/ui_files/SelectMethod.ui", self)
        self.presenter = presenter

        # 连接按钮信号
        self.manual_button.clicked.connect(self.handle_manual)
        self.automated_button.clicked.connect(self.handle_automated)

    def init_widgets(self):
        self.title_label: QLabel = None
        self.manual_button: QPushButton = None
        self.automated_button: QPushButton = None

    def handle_manual(self):
        self.presenter.handle_manual_selected()

    def handle_automated(self):
        self.presenter.handle_automated_selected()

class SelectAlgorithmWindow(QDialog):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_widgets()
        uic.loadUi("./view/ui_files/SelectAlgorithm.ui", self)
        self.presenter = presenter

        # 连接按钮信号
        self.load_button.clicked.connect(self.handle_load)
        self.back_button.clicked.connect(self.handle_back)

    def init_widgets(self):
        self.title_label: QLabel = None
        self.algorithm_combo: QComboBox = None
        self.models_combo: QComboBox = None
        self.filter_button: QPushButton = None
        self.load_button: QPushButton = None
        self.back_button: QPushButton = None


    def handle_load(self):
        algorithm = self.algorithm_combo.currentText()
        model_filter = self.models_combo.currentText()
        self.presenter.handle_load_button(algorithm, model_filter)

    def handle_back(self):
        self.presenter.handle_back_button()

class LoadingWindow(QDialog):
    def __init__(self, parent, presenter, total_features = 60):
        self.status_label: QLabel = None
        self.progress_bar: QProgressBar = None
        super().__init__(parent)
        uic.loadUi("./view/ui_files/Loading.ui", self)
        self.presenter = presenter
        self.total_features = total_features
        self.progress_bar.setMaximum(self.total_features)

        #self.setWindowModality(Qt.ApplicationModal)
    def update_loading_progress(self, current_features):
        self.progress_bar.setValue(current_features)
        self.status_label.setText(f"Solving Features: {current_features}/{self.total_features}")
