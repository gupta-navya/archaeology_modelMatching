from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton
from PyQt5 import uic
from TestGUI.view.mixins.image_window_test import OpenImageMixin
from TestGUI.view.mixins.ply_window_test import PlyWindowMixin
import pathlib
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap

from model.models import ObjectFind


class ValidateMatchingWindow(QDialog,OpenImageMixin,PlyWindowMixin):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_variables()
        self.init_widgets()
        uic.loadUi("./view/ui_files/ValidateMatching.ui", self)
        self.presenter = presenter
        self.set_up_images_pop_up_validate()
        self.set_up_ply_window_validation()
        #self.setWindowModality(Qt.ApplicationModal)

    def init_variables(self):
        self.current_image_front_1 = ""
        self.current_image_back_1 = ""
        self.current_image_front_2 = ""
        self.current_image_back_2 = ""
        self.current_image_front_3 = ""
        self.current_image_back_3 = ""

        self.current_model_1 = ""
        self.current_model_2 = ""
        self.current_model_3 = ""

    def init_widgets(self):
        self.context_value: QLabel = None
        self.total_finds_value: QLabel = None
        self.total_models_value: QLabel = None
        self.auto_matches_value: QLabel = None
        self.validated_value: QLabel = None
        self.validation_progress: QProgressBar = None

        self.findbackphoto_1: QLabel = None
        self.findfrontphoto_1: QLabel = None
        self.match_info_1: QLabel = None
        self.similarity_score_1: QLabel = None
        self.model1: QLabel = None

        self.findbackphoto_2: QLabel = None
        self.findfrontphoto_2: QLabel = None
        self.match_info_2: QLabel = None
        self.similarity_score_2: QLabel = None
        self.model2: QLabel = None

        self.findbackphoto_3: QLabel = None
        self.findfrontphoto_3: QLabel = None
        self.match_info_3: QLabel = None
        self.similarity_score_3: QLabel = None
        self.model3: QLabel = None

        self.previous_button: QPushButton = None
        self.next_button: QPushButton = None
        self.finish_button: QPushButton = None

    def display_find_photo(self, side: str, index: int, photo_path: pathlib.Path):
        """This function displays the photo of the selected find on the GUI

        Args:
            side (str): The side of the photo to display. Must be "front" or "back"
        """
        try:
            photo = Image.open(photo_path).convert("RGB")
        except (FileNotFoundError, IOError, OSError, TypeError, ValueError) as e:
            self.clear_find_photos()
            #self.display_error(f"Error opening photo: {e}")
            return

        im_qt = ImageQt(photo)
        pix_map = QPixmap.fromImage(im_qt)
        current_container = getattr(self, f"find{side}photo_{index}")
        current_container.setPixmap(
            pix_map.scaledToWidth(current_container.width())
        )

        setattr(self,f"current_image_{side}_{index}",str(photo_path))

    def clear_find_photos(self, index: int):
        current_container_front = getattr(self, f"findfrontphoto_{index}")
        current_container_back = getattr(self, f"findbackphoto_{index}")
        current_container_front.clear()
        current_container_back.clear()
        setattr(self, f"current_image_front_{index}", "")
        setattr(self, f"current_image_back_{index}", "")
    '''
    def update_find_match_info(self, find_index, model_index, similarity, index):
        find_match_info = getattr(self, f"match_info_{index}")
        similarity_info = getattr(self, f"similarity_score_{index}")
        find_match_info.setText(
            f"Find {find_index} is matched with model {model_index}"
        )
        similarity_info.setText(
            f"Similarity Score: {similarity}"
        )
    '''
    def update_find_match_info(self, find: ObjectFind, index):
        find_match_info = getattr(self, f"match_info_{index}")
        similarity_info = getattr(self, f"similarity_score_{index}")
        if find is None:
            self.clear_find_info()
            return
        if find.is_matched and not find.is_validated:
            find_match_info.setText(
                f"<span style='color: red;'>Find {find.find_number} is matched with model {find.get_match_str()}</span>"
            )
            similarity_info.setText(
                f"Similarity Score: {find.similarity_score}"
            )

        if find.is_matched and find.is_validated:
            find_match_info.setText(
                f"<span style='color: green;'>Find {find.find_number} is matched with model {find.get_match_str()}</span>"
            )
            similarity_info.setText(
                f"Similarity Score: {find.similarity_score}"
            )

        else:
            self.find_match_info.setText(f"Find {find.find_number} is NOT MATCHED")
            self.update_button.setEnabled(True)
            self.unmatch_find_button.setEnabled(False)
            self.set_find_color(find.find_number, "black")

    def clear_model_match_info(self):
        for index in range(1,4):
            find_match_info = getattr(self, f"match_info_{index}")
            similarity_info = getattr(self, f"similarity_score_{index}")

            find_match_info.setText(
                f""
            )
            similarity_info.setText(
                f""
            )




