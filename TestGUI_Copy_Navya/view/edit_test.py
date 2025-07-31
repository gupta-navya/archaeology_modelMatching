from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QFrame
from PyQt5 import uic
from TestGUI_Copy.view.mixins.image_window_test import OpenImageMixin
from TestGUI_Copy.view.mixins.ply_window_test import PlyWindowMixin
import pathlib
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap


class EditMatchingWindow(QDialog, OpenImageMixin, PlyWindowMixin):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_widgets()
        self.init_variables()

        uic.loadUi("TestGUI_Copy/view/ui_files/EditMatching.ui", self)
        self.presenter = presenter
        self.set_up_images_pop_up_edit()
        self.set_up_ply_window_edit()
        # self.setWindowModality(Qt.ApplicationModal)

    def init_variables(self):
        self.current_model_1 = ""
        self.current_model_2 = ""
        self.current_model_3 = ""
        self.current_model_4 = ""
        self.current_model_5 = ""
        self.current_model_6 = ""

    def init_widgets(self):
        self.findbackphoto_v: QLabel = None
        self.findfrontphoto_v: QLabel = None

        self.findid_v: QLabel = None
        self.update_button: QPushButton = None

        # Model 1 widgets
        self.model_id1: QLabel = None
        self.model1: QLabel = None
        self.similarity_score1: QLabel = None

        # Model 2 widgets
        self.model_id2: QLabel = None
        self.model2: QLabel = None
        self.similarity_score2: QLabel = None

        # Model 3 widgets
        self.model_id3: QLabel = None
        self.model3: QLabel = None
        self.similarity_score3: QLabel = None

        # Model 4 widgets
        self.model_id4: QLabel = None
        self.model4: QLabel = None
        self.similarity_score4: QLabel = None

        # Model 5 widgets
        self.model_id5: QLabel = None
        self.model5: QLabel = None
        self.similarity_score5: QLabel = None

        # Model 6 widgets
        self.model_id6: QLabel = None
        self.model6: QLabel = None
        self.similarity_score6: QLabel = None

        self.previous_button: QPushButton = None
        self.next_button: QPushButton = None

    def update_model_match_info(self, model_index, similarity, index):
        model_id = getattr(self, f"model_id{index}")
        similarity_info = getattr(self, f"similarity_score{index}")
        model_id.setText(f"{model_index}")
        similarity_info.setText(f"Similarity Score: {similarity}")

    def clear_model_match_info(self):
        for index in range(1, 7):  # Changed from 5 to 7 to handle 6 models
            model_id = getattr(self, f"model_id{index}")
            similarity_info = getattr(self, f"similarity_score{index}")
            model_id.setText("no model")
            similarity_info.setText("no similarity")

    def display_find_photo(self, side: str, photo_path: pathlib.Path):
        """This function displays the photo of the selected find on the GUI

        Args:
            side (str): The side of the photo to display. Must be "front" or "back"
        """
        try:
            photo = Image.open(photo_path).convert("RGB")
        except (FileNotFoundError, IOError, OSError, TypeError, ValueError) as e:
            print("error:", e)
            return

        # Check if widgets exist
        if side == "front" and not self.findfrontphoto_v:
            print("错误: findfrontphoto_v 控件未找到!")
            return
        elif side == "back" and not self.findbackphoto_v:
            print("错误: findbackphoto_v 控件未找到!")
            return

        im_qt = ImageQt(photo)
        pix_map = QPixmap.fromImage(im_qt)
        if side == "front":
            self.findfrontphoto_v.setPixmap(
                pix_map.scaledToWidth(self.findfrontphoto_v.width())
            )
            self.current_image_front = str(photo_path)
        else:
            self.findbackphoto_v.setPixmap(
                pix_map.scaledToWidth(self.findbackphoto_v.width())
            )
            self.current_image_back = str(photo_path)

    def clear_find_photos(self):
        self.findfrontphoto_v.clear()
        self.findbackphoto_v.clear()
        self.current_image_front = ""
        self.current_image_back = ""

    def display_model_frame_color(self, index, color):
        """
        Sets the border color for the model frame at position `index` (1 to 6).
        
        Args:
            index (int): Display slot index (1–6).
            color (str): Desired border color (e.g., 'red', 'green').
        """
        color_map = {
            'red': 'red',     # for model matched with another find
            'yellow': 'yellow',  # for model unmatched in database
            'blue': 'blue',
            'green': 'green'  # for model matched with current find
        }
        color = color_map.get(color, 'gray')

        frame_name = f"checkmodel{index}"
        frame = getattr(self, frame_name, None)

        if frame:
            frame.setStyleSheet(
                f"QFrame#{frame_name} {{ border: 2px solid {color}; border-radius: 8px; }}"
            )
        else:
            print(f"Frame '{frame_name}' not found.")

    def clear_model_frame_color(self, index: int):
        """
        Clears the border color of a specific model frame (checkmodel{index}).

        Args:
            index (int): The index of the frame to reset (1 to 6).
        """
        if 1 <= index <= 6:  # Changed from 4 to 6 to handle 6 models
            frame_name = f"checkmodel{index}"
            frame = getattr(self, frame_name, None)
            if isinstance(frame, QFrame):
                frame.setStyleSheet("")  # Clear border style
            else:
                print(f"Frame '{frame_name}' does not exist or is not a QFrame.")
        else:
            print(f"Invalid index: {index}. Must be between 1 and 6.")