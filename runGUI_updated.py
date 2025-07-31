import sys
from PyQt5.QtWidgets import QApplication

# 假设您的MainView类在main_view.py文件中
from TestGUI_Copy.view.main_view_test import MainView
from TestGUI_Copy.Presenter.select_presenter import SelectMethodPresenter
from TestGUI_Copy.model.model_test import Validation_Model_Test

from pathlib import Path
test_pic_path = Path("../TestGUI/assets_1/pic1.png")

if __name__ == "__main__":
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # 创建主窗口
    main_window = MainView()
    main_model = Validation_Model_Test()
    main_presenter = SelectMethodPresenter(main_window, main_model)
    # 设置窗口最小尺寸（可选）
    main_presenter.main_view.setMinimumSize(1100, 600)
    # 显示窗口
    main_presenter.main_view.show()

    main_presenter.main_view.display_find_photo("front",main_model.get_find(1)[0])
    main_presenter.main_view.display_find_photo("back", main_model.get_find(1)[1])

    # 执行应用
    sys.exit(app.exec_())