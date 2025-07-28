from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QPixmap


class ImageWindow(QWidget):
    """This QWidget is shown when a person click on findFrontPhoto_l or findBackPhoto_l"""

    def __init__(self, current_image_path):
        super().__init__()

        current_view = self
        current_view.label = QLabel(f"{current_image_path}")

        # 1. Loading from the image path to the pixmap, then to the label.
        pixmap = QPixmap(current_image_path)
        pixmap = pixmap.scaledToWidth(720)
        current_view.label.setPixmap(pixmap)

        # 2. Loading from the image label to the layout.
        layout = QVBoxLayout()
        layout.addWidget(current_view.label)
        current_view.setLayout(layout)


class OpenImageMixin:
    def set_up_images_pop_up_validate(self):
        """使图片区域可点击，点击时弹出大图"""
        validation_window = self

        # 为每个图片控件绑定事件并传递索引
        for i in range(1, 4):
            getattr(validation_window, f"findfrontphoto_{i}").mousePressEvent = (
                lambda event, idx=i: self.open_image_validate(event, "front", idx)
            )
            getattr(validation_window, f"findbackphoto_{i}").mousePressEvent = (
                lambda event, idx=i: self.open_image_validate(event, "back", idx)
            )

    def set_up_images_pop_up_edit(self):
        """This function makes the two image sections of the PYQT web interface clickable,
        when clicked, the image will pop out in a larger window.
        """
        main_view = self
        main_view.findfrontphoto_v.mousePressEvent = main_view.open_image_front
        main_view.findbackphoto_v.mousePressEvent = main_view.open_image_back

    def open_image_validate(self, event, image_type, index):
        """
        通用图片打开函数
        :param event: 鼠标事件
        :param image_type: 'front'或'back'
        :param index: 图片索引(1/2/3)
        """

        validation_window = self
        current_image = getattr(validation_window, f"current_image_{image_type}_{index}")
        current_window = getattr(validation_window, f"find{image_type}photo_{index}")
        if current_window.pixmap() and not current_window.pixmap().isNull():
            validation_window.wid = ImageWindow(current_image)
            validation_window.wid.show()

        '''
        # 确保存在图像字典
        if not hasattr(self, "image_dict"):
            self.image_dict = {}

        # 构造字典键名
        key = f"{image_type}_{index}"

        # 检查图像是否存在
        if key in self.image_dict and self.image_dict[key] is not None:
            # 创建并显示图片窗口
            self.wid = ImageWindow(self.image_dict[key])
            self.wid.show()
        '''


    def open_image_front(self, event):
        """This function is a callback when the front image is being clicked,
        the image will pop out in a larger window

        Args:
            event (signal): A signal that the front image is clicked
        """
        edit_window = self
        if edit_window.findfrontphoto_v.pixmap():
            edit_window.wid = ImageWindow(edit_window.current_image_front)
            edit_window.wid.show()

    def open_image_back(self, event):
        """This function is a callback when the back image is being clicked,
        the image will pop out in a larger window

        Args:
            event (signal): A signal that the back image is clicked
        """
        edit_window = self
        if edit_window.findbackphoto_v.pixmap():
            edit_window.wid = ImageWindow(edit_window.current_image_back)
            edit_window.wid.show()