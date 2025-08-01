from PyQt5.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QFrame
from PyQt5 import uic
from TestGUI.view.mixins.image_window_test import OpenImageMixin
from TestGUI.view.mixins.ply_window_test import PlyWindowMixin
import pathlib
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap


class ValidateMatchingWindow(QDialog,OpenImageMixin,PlyWindowMixin):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.init_variables()
        self.init_widgets()
        uic.loadUi("TestGUI_Copy/view/ui_files/ValidateMatching.ui", self)
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

        if True:
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


    def set_general_information(self, context_name, total_finds, total_models, automatches):

        self.context_value.setText(str(context_name))
        self.total_finds_value.setText(str(total_finds))
        self.total_models_value.setText(str(total_models))


        self.auto_matches_value.setText(str(automatches))
        self.validation_progress.setMaximum(automatches)

        self.validated_value.setText("0")
        self.validation_progress.setValue(0)
        #self.max_check_value = 0


    def display_general_information(self, current_progress, automatches):

        self.auto_matches_value.setText(str(automatches))
        self.validated_value.setText(str(current_progress))

        self.validation_progress.setMaximum(automatches)
        self.validation_progress.setValue(0)

        #self.max_check_value = max(self.max_check_value, auto_matches_value + 3)
        #self.validation_progress.setValue(self.max_check_value)
        #self.validated_value.setText(str(self.max_check_value))



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


    def update_find_match_info(self, find_index, model_index, similarity, index):
        find_match_info = getattr(self, f"match_info_{index}")
        similarity_info = getattr(self, f"similarity_score_{index}")
        find_match_info.setText(
        f"<span style='color: red;'>Find {find_index} is matched with model {model_index}</span>"
        )

        similarity_info.setText(
            f"<span style='color: red;'>Similarity Score: {similarity}</span>"
        )

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


    def display_frame_color(self, frame_id: int, color_flag: int):
        """Sets the border color of the specified frame based on the frame_id.

        Args:
            frame_id (int): The ID of the frame to modify.
            color (str): The color to set the border. Supported colors: 'red', 'yellow', 'blue', 'green'.
        """
        # Define a dictionary to map color names to CSS color codes
        color_map = {
            1 : 'yellow',
            2 : 'orange',
            3 : 'orange',
            4 : 'blue',
            5 : 'red',
            6 : 'green'
        }

        # Check if the specified frame_id is valid
        if 1 <= frame_id <= 3:
            frame = getattr(self, f"validate_match_frame{frame_id}", None)
            if isinstance(frame, QFrame):
                # Set the border color using the CSS style without affecting child widgets
                color_code = color_map.get(color_flag)
                if color_code:
                    frame.setStyleSheet(f"QFrame#validate_match_frame{frame_id} {{ border: 2px solid {color_code}; }}")
                else:
                    print(f"Color '{str(color_flag)}' is not supported.")
            else:
                print(f"Frame {frame_id} does not exist.")
        else:
            print(f"Invalid frame_id: {frame_id}. Must be between 1 and 3.")

    def clear_frame_color(self, frame_id: int):
        """Clears the border color of the specified frame based on the frame_id.

        Args:
            frame_id (int): The ID of the frame to modify.
        """
        # Check if the specified frame_id is valid
        if 1 <= frame_id <= 3:
            frame = getattr(self, f"validate_match_frame{frame_id}", None)
            if isinstance(frame, QFrame):
                # Reset the border style to default
                frame.setStyleSheet("")  # Clear the style sheet
            else:
                print(f"Frame {frame_id} does not exist.")
        else:
            print(f"Invalid frame_id: {frame_id}. Must be between 1 and 3.")



