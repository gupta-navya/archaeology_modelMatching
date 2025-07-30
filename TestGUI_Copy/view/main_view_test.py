# import ctypes
import logging
import pathlib
import subprocess
import time
from typing import List, Tuple

# opengl_path = r".\computation\opengl32.dll"
# ctypes.cdll.LoadLibrary(opengl_path)

import open3d as o3d

from PyQt5.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QListWidget,
    QTreeView,
    QSpinBox,
    QLabel,
    QComboBox,
    QPushButton,
    QProgressBar,
    QListWidgetItem, )

from PyQt5.QtGui import QPixmap, QColor, QStandardItemModel, QStandardItem
from PyQt5 import uic, QtCore
from PIL import Image
from PIL.ImageQt import ImageQt

#import win32gui

from view.mixins.image_window import OpenImageMixin
from TestGUI.view.mixins.ply_window_test import PlyWindowMixin
from model.models import A3DModel, ObjectFind

logger = logging.getLogger(__name__)


class MainView(QMainWindow, OpenImageMixin, PlyWindowMixin):
    """The MainView contains all the GUI related functions and classes

    Args:
        QMainWindow (QMainWindow): Making the MainView a QWidget that can load a
        ui file and display things.

        PlyWindowMixin (class): Mixin that initializes the window that displays 3d models in it.

         (class): Mixin that allows the users to click on an
        Image to see it full size.
    """

    def __init__(self):
        """This constructor loads the ply to the ui file, set up the 3d model window,
        and make it the images pop when you click on them.
        """
        super().__init__()

        # declare the widgets that will be used.
        # These will be filled in when MainWindow.ui is loaded
        self.finds_list: QListWidget = None
        self.unsorted_model_list: QTreeView = None
        self.sorted_model_list: QTreeView = None
        self.find_start: QSpinBox = None
        self.find_end: QSpinBox = None
        self.year: QSpinBox = None
        self.batch_start: QSpinBox = None
        self.batch_end: QSpinBox = None
        self.load_all: QPushButton = None

        self.context_display: QLabel = None

        self.findFrontPhoto_l: QLabel = None
        self.findBackPhoto_l: QLabel = None

        self.selected_find_info: QLabel = None

        self.color_grid_select: QComboBox = None
        self.model: QLabel = None
        self.find_match_info: QLabel = None
        self.model_match_info: QLabel = None
        self.update_button: QPushButton = None
        self.unmatch_find_button: QPushButton = None
        self.unmatch_model_button: QPushButton = None
        self.general_status: QLabel = None
        self.task_status: QLabel = None
        # self.test_task_button: QPushButton = None
        self.task_progress: QProgressBar = None

        self.current_pcd = None
        logger.info("Loading MainWindow.ui")
        now = time.time()
        uic.loadUi("./view/ui_files/MainWindow.ui", self)
        self.initialize_sorted_models()
        self.initialize_unsorted_models()
        logger.info("MainWindow.ui loaded in %s seconds", (f"{time.time() - now:0.4f}"))
        now = time.time()
        logger.info("Setting up ply window")
        #self.set_up_ply_window()
        logger.info("Ply window set up in %s seconds", (f"{time.time() - now:0.4f}"))
        logger.info("Setting up images pop up")
        now = time.time()
        self.set_up_images_pop_up()
        logger.info("Images pop up set up in %s seconds", (f"{time.time() - now:0.4f}"))
        self.current_image_front = ""
        self.current_image_back = ""

        ## append the version to the window title
        version = self.get_version()
        self.setWindowTitle(f"Sherd Match Assistance Version: {version}")

    def get_version(self):
        try:
            cwd = pathlib.Path(__file__).parent
            result = subprocess.run(
                ["git", "describe", "--tags", "--always", "--dirty"],
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd,
            )
            version = result.stdout.strip()
            logger.info("Version: %s", version)
            return version
        except subprocess.CalledProcessError as e:
            logger.error("Error getting version: %s", e.stderr)
            return "Unknown"

    def display_error(self, message: str):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()

    def display_find_photo(self, side: str, photo_path: pathlib.Path):
        """This function displays the photo of the selected find on the GUI

        Args:
            side (str): The side of the photo to display. Must be "front" or "back"
        """
        try:
            photo = Image.open(photo_path).convert("RGB")
        except (FileNotFoundError, IOError, OSError, TypeError, ValueError) as e:
            logger.error("Error opening photo at %s: %s", photo_path, e)
            self.clear_find_photos()
            self.display_error(f"Error opening photo: {e}")
            return

        im_qt = ImageQt(photo)
        pix_map = QPixmap.fromImage(im_qt)
        if side == "front":
            self.findFrontPhoto_l.setPixmap(
                pix_map.scaledToWidth(self.findFrontPhoto_l.width())
            )
            self.current_image_front = str(photo_path)
        else:
            self.findBackPhoto_l.setPixmap(
                pix_map.scaledToWidth(self.findBackPhoto_l.width())
            )
            self.current_image_back = str(photo_path)

    def clear_find_photos(self):
        self.findFrontPhoto_l.clear()
        self.findBackPhoto_l.clear()
        self.current_image_front = ""
        self.current_image_back = ""

    def display_find_details(self, find: ObjectFind):
        """This function displays the details of the selected find on the GUI

        Args:
            find (ObjectFind): The find object to display
        """
        if find is None:
            self.clear_find_info()
            return
        self.selected_find_info.setText(
            f"Find: {find.find_number}\nMaterial: {find.material}\nCategory: {find.category}"
        )
        self.update_find_match_info(find)

        self.display_find_photo("front", find.photo_path("front"))
        self.display_find_photo("back", find.photo_path("back"))

    def update_find_match_info(self, find: ObjectFind):
        if find is None:
            self.clear_find_info()
            return
        if find.is_matched:
            self.find_match_info.setText(
                f"Find {find.find_number} is matched with model {find.get_match_str()}"
            )
            self.update_button.setEnabled(False)
            self.update_button.setToolTip(
                "Make sure find and model are both unmatched before updating."
            )
            self.unmatch_find_button.setEnabled(True)
            self.set_find_color(find.find_number, "red")
        else:
            self.find_match_info.setText(f"Find {find.find_number} is NOT MATCHED")
            self.update_button.setEnabled(True)
            self.unmatch_find_button.setEnabled(False)
            self.set_find_color(find.find_number, "black")

    def display_model_details(self, model: A3DModel):
        self.model_match_info.styleSheet = "color: black"
        if model is None:
            self.clear_model_info()
            return
        self.update_model_match_info(model)
        model_path = model.get_file("full")
        self.clear_ply_window()
        self.current_pcd = o3d.io.read_point_cloud(str(model_path))
        self.ply_window.get_render_option().point_size = 5
        self.ply_window.add_geometry(self.current_pcd)
        self.ply_window.update_geometry(self.current_pcd)

    def update_model_match_info(self, model: A3DModel):
        if model is None:
            self.clear_model_info()
            return
        if model.is_matched:
            msg = ""
            multiple_models = len(model.matched_finds) > 1
            if multiple_models:
                msg = "MODEL IS MATCHED TO MORE THAN 1 FIND!!!\n"
                self.model_match_info.styleSheet = "color: red"
            finds = ", ".join(str(f) for f in model.matched_finds)
            msg += f"Model {model} is matched with find{'s' if multiple_models else ''} {finds}"
            self.model_match_info.setText(msg)
            self.unmatch_model_button.setEnabled(True)
            self.update_button.setEnabled(False)
            self.update_button.setToolTip(
                "Make sure find and model are both unmatched before updating."
            )
            self.model_match_info.setText(msg)
            self.set_sorted_model_color(str(model), "red")
            self.set_unsorted_model_color(
                model.batch_year, model.batch_number, model.batch_piece, "red"
            )
        else:
            self.model_match_info.setText(f"Model {model} is NOT MATCHED")
            self.unmatch_model_button.setEnabled(False)
            self.update_button.setEnabled(True)
            self.set_sorted_model_color(str(model), "black")
            self.set_unsorted_model_color(
                model.batch_year, model.batch_number, model.batch_piece, "black"
            )

    def clear_find_info(self):
        self.clear_find_photos()
        self.selected_find_info.setText("")
        self.find_match_info.setText("No find selected")
        self.update_button.setEnabled(False)
        self.update_button.setToolTip("Select a find and a model to update.")

    def clear_model_info(self):
        self.model_match_info.setText("No model selected")
        self.unmatch_model_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.update_button.setToolTip("Select a find and a model to update.")
        self.clear_ply_window()

    def clear_interface(self):
        """Clear all the texts, and selects, images displayed and 3d models from the interface."""

        self.context_display.setText("")
        self.clear_find_info()
        self.clear_model_info()

        self.clear_sorted_models()
        self.clear_unsorted_models()
        # self.reset_ply_selection_model()
        self.finds_list.setCurrentItem(None)
        self.finds_list.clear()

    def confirm(self, message: str, on_confirm):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("Confirm")
        msg.setInformativeText(message)
        msg.setWindowTitle("Confirm")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.buttonClicked.connect(on_confirm)
        msg.exec_()

    def set_find_color(self, find_number: int, color: str):
        find_item = self.finds_list.findItems(str(find_number), QtCore.Qt.MatchExactly)[
            0
        ]
        find_item.setForeground(QColor(color))

    def set_unsorted_model_color(
        self, batch_year: int, batch_number: int, batch_piece: int, color: str
    ):
        # set the piece number to color in the tree view under batch_year -> batch_number
        q_model = self.unsorted_model_list.model()
        for i in range(q_model.rowCount()):
            for j in range(q_model.item(i).rowCount()):
                for k in range(q_model.item(i).child(j).rowCount()):
                    if (
                        int(q_model.item(i).text()) == batch_year
                        and int(q_model.item(i).child(j).text()) == batch_number
                        and int(q_model.item(i).child(j).child(k).text()) == batch_piece
                    ):
                        q_model.item(i).child(j).child(k).setForeground(QColor(color))

    def set_sorted_model_color(self, model_str: str, color: str):
        # set the piece number to color in the tree view under batch_year -> batch_number
        q_model = self.sorted_model_list.model()
        for i in range(q_model.rowCount()):
            if q_model.item(i).text() == model_str:
                q_model.item(i).setForeground(QColor(color))

    def initialize_unsorted_models(self):
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Models"])
        self.unsorted_model_list.setModel(model)

    def clear_unsorted_models(self):
        self.unsorted_model_list.selectionModel().model().removeRows(
            0, self.unsorted_model_list.selectionModel().model().rowCount()
        )

    def initialize_sorted_models(self):
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Models"])
        self.sorted_model_list.setModel(model)

    def clear_sorted_models(self):
        self.sorted_model_list.selectionModel().model().removeRows(
            0, self.sorted_model_list.selectionModel().model().rowCount()
        )

    def list_sorted_models(self, sorted_models: List[A3DModel]):
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Models"])
        for a3dmodel in sorted_models:
            title = str(a3dmodel)
            item = QStandardItem(title)
            item.setData(title, QtCore.Qt.UserRole)
            if a3dmodel.is_matched:
                item.setForeground(QColor("red"))
            model.appendRow(item)
        self.sorted_model_list.setModel(model)

    def list_finds(self, finds: List[ObjectFind]):
        self.finds_list.clear()
        for find in finds:
            item = QListWidgetItem(str(find.find_number))
            if find.is_matched:
                item.setForeground(QColor("red"))
            self.finds_list.addItem(item)

    def clear_finds_list(self):
        self.finds_list.clear()

    def set_status(self, text: str):
        self.general_status.setText(text)

    def set_find_year_filters(
        self, min_year: int, max_year: int, min_find: int, max_find: int
    ):
        self.find_start.setMinimum(min_find)
        self.find_start.setMaximum(max_find)
        self.find_start.setValue(min_find)
        self.find_end.setMinimum(min_find)
        self.find_end.setMaximum(max_find)
        self.find_end.setValue(max_find)
        self.year.setMinimum(min_year)
        self.year.setMaximum(max_year)
        self.year.setValue(min_year)
        self.year.setReadOnly(min_year == max_year)

    def set_batch_filters(self, min_batch: int, max_batch: int):
        self.batch_start.setMinimum(min_batch)
        self.batch_start.setMaximum(max_batch)
        self.batch_start.setValue(min_batch)
        self.batch_end.setMinimum(min_batch)
        self.batch_end.setMaximum(max_batch)
        self.batch_end.setValue(max_batch)



    def display_progress(self, progress: Tuple[str, int]):
        self.task_status.setText(progress[0])
        self.task_progress.setValue(progress[1])

    def current_color_grid(self):
        return self.color_grid_select.currentText()
