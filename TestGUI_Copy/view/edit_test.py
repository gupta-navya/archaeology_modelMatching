from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton
from PyQt5 import uic
from TestGUI_Copy.view.mixins.image_window_test import OpenImageMixin
from TestGUI_Copy.view.mixins.ply_window_test import PlyWindowMixin
import pathlib
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap


class EditMatchingWindow(QDialog,OpenImageMixin,PlyWindowMixin):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_widgets()
        self.init_variables()

        uic.loadUi("./view/ui_files/EditMatching.ui", self)
        self.presenter = presenter
        self.set_up_images_pop_up_edit()
        self.set_up_ply_window_edit()
        #self.setWindowModality(Qt.ApplicationModal)

    def init_variables(self):
        self.current_model_1 = ""
        self.current_model_2 = ""
        self.current_model_3 = ""
        self.current_model_4 = ""

    def init_widgets(self):
        self.findbackphoto_v: QLabel = None
        self.findfrontphoto_v: QLabel = None

        self.findid_v: QLabel = None
        self.update_button: QPushButton = None

        self.model_id1: QLabel = None
        self.model1: QLabel = None
        self.similarity_score1: QLabel = None

        self.model_id2: QLabel = None
        self.model2: QLabel = None
        self.similarity_score2: QLabel = None

        self.model_id3: QLabel = None
        self.model3: QLabel = None
        self.similarity_score3: QLabel = None

        self.model_id4: QLabel = None
        self.model4: QLabel = None
        self.similarity_score4: QLabel = None

        self.previous_button: QPushButton = None
        self.next_button: QPushButton = None



    def update_model_match_info(self, model_index, similarity, index):
        model_id = getattr(self, f"model_id{index}")
        similarity_info = getattr(self, f"similarity_score{index}")
        model_id.setText(
            f"{model_index}"
        )
        similarity_info.setText(
            f"Similarity Score: {similarity}"
        )

    def clear_model_match_info(self):
        for index in range(1,5):
            model_id = getattr(self, f"model_id{index}")
            similarity_info = getattr(self, f"similarity_score{index}")
            model_id.setText(
                "no model"
            )
            similarity_info.setText(
                "no similarity"
            )

    def display_find_photo(self, side: str, photo_path: pathlib.Path):
        """This function displays the photo of the selected find on the GUI

        Args:
            side (str): The side of the photo to display. Must be "front" or "back"
        """
        try:
            photo = Image.open(photo_path).convert("RGB")
        except (FileNotFoundError, IOError, OSError, TypeError, ValueError) as e:
            print("error:", e)
            #self.clear_find_photos()
            #self.display_error(f"Error opening photo: {e}")
            return

        # 检查控件是否有效
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


