
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


    def init_widgets(self):
        self.title_label: QLabel = None
        self.manual_button: QPushButton = None
        self.automated_button: QPushButton = None

class SelectAlgorithmWindow(QDialog):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_widgets()
        uic.loadUi("./view/ui_files/SelectAlgorithm.ui", self)
        self.presenter = presenter

        # 连接按钮信号


    def init_widgets(self):
        self.title_label: QLabel = None

        self.algorithm_combo: QComboBox = None
        self.models_combo: QComboBox = None

        self.filter_button: QPushButton = None
        self.load_button: QPushButton = None
        self.back_button: QPushButton = None

    def show_missing_info(self, missing, total):
        self.title_label.setText(f"Incomplete Similarity Matrix: {total - missing}/{total}")

    def show_complete_info(self, total):
        self.title_label.setText(f"Complete Similarity Matrix: {total} in total")


class LoadingWindow(QDialog):
    def __init__(self, parent, presenter):
        self.status_label_1: QLabel = None
        self.progress_bar_1: QProgressBar = None
        self.status_label_2: QLabel = None
        self.progress_bar_2: QProgressBar = None
        self.status_label_3: QLabel = None

        super().__init__(parent)
        uic.loadUi("./view/ui_files/Loading.ui", self)
        self.presenter = presenter
        self.status_label_3.setVisible(False)

        # 设置进度条初始值
        #self.progress_bar_1.setMaximum(total_finds)
        #self.progress_bar_1.setValue(0)
        #self.progress_bar_2.setMaximum(total_models)
        #self.progress_bar_2.setValue(0)

        # 初始化状态标签
        #self.status_label_1.setText(f"Measuring Finds: 0/{total_finds}")
        #self.status_label_2.setText(f"Measuring Models: 0/{total_models}")


    def show_finds_measurement(self, total):

        self.status_label_1.setVisible(True)
        self.progress_bar_1.setVisible(True)

        self.status_label_2.setVisible(True)
        self.progress_bar_2.setVisible(True)

        self.status_label_3.setVisible(False)


        self.status_label_1.setText(f"Measuring Missing Finds: 0/{total}")
        self.progress_bar_1.setMaximum(total)

    def show_models_measurement(self, total):
        self.status_label_1.setVisible(True)
        self.progress_bar_1.setVisible(True)

        self.status_label_2.setVisible(True)
        self.progress_bar_2.setVisible(True)

        self.status_label_3.setVisible(False)


        self.status_label_2.setText(f"Measuring Missing Models: 0/{total}")
        self.progress_bar_2.setMaximum(total)

    def update_finds_progress(self, current, total):
        """更新finds测量进度"""
        self.progress_bar_1.setValue(current)
        self.status_label_1.setText(f"Measuring Missing Finds: {current}/{total}")

    def update_models_progress(self, current, total):
        """更新models测量进度"""
        self.progress_bar_2.setValue(current)
        self.status_label_2.setText(f"Measuring Missing Models: {current}/{total}")


    def show_similarity_computation(self, total):
        """显示相似度矩阵计算状态"""
        self.status_label_1.setVisible(True)
        self.progress_bar_1.setVisible(True)

        self.status_label_2.setVisible(True)
        self.progress_bar_2.setVisible(False)

        self.status_label_3.setVisible(False)


        self.status_label_1.setText(f"Calculating Similarities: 0 / {total}")
        self.progress_bar_1.setMaximum(total)
        self.progress_bar_1.setValue(0)
        self.status_label_2.setText(f"")

    def update_show_similarity_computation(self, current, total, find_number, model_id):
        self.status_label_1.setText(f"Calculating Similarities: {current} / {total}")
        self.progress_bar_1.setValue(current)
        self.status_label_2.setText(f"Calculated Match: {find_number} ↔ {model_id} ")

    def show_recommending_matches(self):
        """显示推荐矩阵计算状态"""
        self.status_label_3.setText("Recommending Matches...")
        self.status_label_3.setVisible(True)
        self.status_label_1.setVisible(False)
        self.status_label_2.setVisible(False)
        self.progress_bar_1.setVisible(False)
        self.progress_bar_2.setVisible(False)

    def show_match_applying(self, total_matches):
        """显示匹配应用状态"""
        self.status_label_1.setText("Applying Automated Matches...")
        self.status_label_1.setVisible(True)
        self.status_label_2.setVisible(False)
        self.status_label_3.setVisible(False)
        self.progress_bar_1.setVisible(True)
        self.progress_bar_2.setVisible(False)
        self.progress_bar_1.setMaximum(total_matches)
        self.progress_bar_1.setValue(0)

    def show_unmatch_removing(self, total_unmatches):
        """显示取消匹配状态"""
        self.status_label_1.setText("Removing Previous Matches...")
        self.status_label_1.setVisible(True)
        self.status_label_2.setVisible(False)
        self.status_label_3.setVisible(False)
        self.progress_bar_1.setVisible(True)
        self.progress_bar_2.setVisible(False)
        self.progress_bar_1.setMaximum(total_unmatches)
        self.progress_bar_1.setValue(0)
