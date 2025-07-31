from TestGUI_Copy.view.select_test import SelectMethodWindow
from TestGUI_Copy.view.select_test import SelectAlgorithmWindow
from TestGUI_Copy.view.select_test import LoadingWindow
from TestGUI_Copy.view.validate_test import ValidateMatchingWindow
from TestGUI_Copy.view.edit_test import EditMatchingWindow
from TestGUI_Copy.model.model_test import Validation_Model_Test
from TestGUI_Copy.view.main_view_test import MainView

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer


class SelectMethodPresenter:
    def __init__(self, main_view: MainView, model: Validation_Model_Test = None):
        self.main_view = main_view
        self.model = model

        self.method_window : SelectMethodWindow = None
        self.algorithm_window : SelectAlgorithmWindow = None

        self.loading_window : LoadingWindow = None

        self.validate_window : ValidateMatchingWindow = None
        self.match_list = []

        self.edit_window : EditMatchingWindow = None
        self.model_list = []

        self.max_display_index = 0



        # 连接主视图的加载按钮信号
        self.main_view.load_all.clicked.connect(self.show_method_selection)

    ''''''

    def show_method_selection(self):
        """显示匹配方法选择窗口"""
        self.method_window = SelectMethodWindow(self.main_view, self)
        self.method_window.show()

    def show_algorithm_selection(self):
        """显示算法选择窗口"""
        self.algorithm_window = SelectAlgorithmWindow(self.main_view, self)
        self.algorithm_window.show()

    def handle_manual_selected(self):
        """处理手动匹配选择"""
        #self.main_view.manual_load()  # 调用原加载功能
        self.method_window.close()

    def handle_automated_selected(self):
        """处理自动匹配选择"""
        self.show_algorithm_selection()
        self.method_window.close()

    def handle_back_button(self):
        """处理返回按钮"""
        self.algorithm_window.close()
        self.show_method_selection()

    def handle_load_button(self, algorithm, model_filter):
        """处理加载按钮"""
        self.algorithm_window.close()
        #self.MainModel.solve(algorithm, model_filter)
        self.show_loading_window(algorithm, model_filter)


    def show_loading_window(self, algorithm, model_filter):
        """显示加载进度窗口"""

        total_features = 60
        self.loading_window = LoadingWindow(self.main_view, self, total_features)
        self.loading_window.show()

        self.model.get_random_matches(10)


        # 启动进度条定时器 模拟异步函数
        self.progress_value = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(lambda: self.update_loading_progress(algorithm, model_filter))
        self.loading_timer.start(5)  # 每50ms更新一次进度

    def update_loading_progress(self, algorithm, model_filter):
        """更新加载进度"""
        self.progress_value += 1
        features = min(60, self.progress_value * 60 // 100)
        self.loading_window.update_loading_progress(features)

        if self.progress_value >= 100:
            self.loading_timer.stop()
            self.loading_window.close()
            self.show_validation_window(algorithm, model_filter)


    # todo: validation_window
    def show_validation_window(self, algorithm, model_filter):
        """显示验证匹配窗口"""
        self.validate_window = ValidateMatchingWindow(self.main_view, self)
        self.validate_window.show()

        # 设置验证进度

        self.validate_window.init_general_information()
        self.match_list = self.model.recommand_matches(10)



        self.display_match_index = 0
        self.display_matches(self.display_match_index)
        self.display_match_color(self.display_match_index)

        # 连接双击事件
        for i in range(1, 4):
            frame = getattr(self.validate_window, f"validate_match_frame{i}")
            frame.mouseDoubleClickEvent = lambda event, frame_id=i: self.handle_frame_double_click(frame_id)

        # 连接完成按钮
        self.validate_window.finish_button.clicked.connect(self.close_validation)
        self.validate_window.previous_button.clicked.connect(self.handle_previous_button_validate)
        self.validate_window.next_button.clicked.connect(self.handle_next_button_validate)



    def handle_previous_button_validate(self):
        if self.display_match_index - 3 < 0:
            QMessageBox.warning(self.validate_window, "Warning", "You have reached the beginning.")
        else:
            self.display_match_index -= 3
            self.display_matches(self.display_match_index)
            self.display_match_color(self.display_match_index)


    def handle_next_button_validate(self):
        if self.display_match_index + 3 >= len(self.match_list):
            QMessageBox.warning(self.validate_window, "Warning", "You have reached the end.")
        else:
            self.validate_window.display_general_information(self.display_match_index)
            self.display_match_index += 3
            self.max_display_index = max(self.display_match_index, self.max_display_index)
            self.display_matches(self.display_match_index)
            self.display_match_color(self.display_match_index)




    def display_match_color(self, start_index):
        list_length = len(self.match_list)
        if start_index <= list_length - 1: #status
            self.validate_window.display_frame_color(1,"yellow")
        else: self.validate_window.clear_frame_color(1)

        if start_index + 1 <= list_length - 1:
            self.validate_window.display_frame_color(2,"yellow")
        else:
            self.validate_window.clear_frame_color(2)

        if start_index + 2 <= list_length - 1:
            self.validate_window.display_frame_color(3,"yellow")
        else:
            self.validate_window.clear_frame_color(3)

        if start_index <= self.max_display_index - 1:
            self.validate_window.display_frame_color(1,"green")

        if start_index + 1<= self.max_display_index - 1:
            self.validate_window.display_frame_color(2, "green")

        if start_index + 2 <= self.max_display_index - 1:
            self.validate_window.display_frame_color(3, "green")


    def display_model_color(self, index: int, find: int, model_id: int):
        """
        Displays the correct border color for a model shown in EditMatchingWindow,
        based on its relation to the current find.

        Args:
            index (int): Display slot index (1–4).
            find (int): Current find ID.
            model_id (int): Model ID being evaluated.
        """
        # Get all recommended matches (each is: (find, model, sim))
        all_matches = self.model.recommand_matches(num=200) 

        # Check if model_id is part of any match
        matched_model_ids = [match[1] for match in all_matches]

        if model_id in matched_model_ids:
            # Find the match involving the current find
            match_for_find = next((match for match in all_matches if match[0] == find), None)
            if match_for_find:
                if match_for_find[1] == model_id:
                    # Green: model is matched with current find
                    self.edit_window.display_model_frame_color(index, "green")
                else:
                    # Red: model is matched with another find
                    self.edit_window.display_model_frame_color(index, "red")
            else:
                # Model is matched, but not to this find — so it's red
                self.edit_window.display_model_frame_color(index, "red")
        else:
            # Model is not matched at all
            self.edit_window.display_model_frame_color(index, "yellow")

    def display_matches(self, start_index):
        if self.validate_window is None: return
        if self.match_list is None: return
        self.clear_matches()


        list_length = len(self.match_list)
        if start_index <= list_length - 1:
            find_index_1 = self.match_list[start_index][0]
            model_index_1 = self.match_list[start_index][1]
            similarity_1= self.match_list[start_index][2]

            self.validate_window.current_model_1 = self.model.get_model(model_index_1)
            self.validate_window.display_model_screenshot(1)
            self.validate_window.update_find_match_info(find_index_1, model_index_1, similarity_1,1)


            self.validate_window.current_image_back_1 = self.model.get_find(find_index_1)[0]
            self.validate_window.current_image_front_1 = self.model.get_find(find_index_1)[1]
            self.validate_window.display_find_photo("back", 1, self.validate_window.current_image_back_1)
            self.validate_window.display_find_photo("front", 1, self.validate_window.current_image_front_1)
        if start_index + 1 <= list_length - 1:
            find_index_2 = self.match_list[start_index + 1][0]

            model_index_2 = self.match_list[start_index + 1][1]
            similarity_2= self.match_list[start_index + 1][2]

            self.validate_window.current_model_2 = self.model.get_model(model_index_2)
            self.validate_window.display_model_screenshot(2)

            self.validate_window.update_find_match_info(find_index_2,model_index_2, similarity_2,2)

            self.validate_window.current_image_back_2 = self.model.get_find(find_index_2)[0]
            self.validate_window.current_image_front_2 = self.model.get_find(find_index_2)[1]
            self.validate_window.display_find_photo("back", 2, self.validate_window.current_image_back_2)
            self.validate_window.display_find_photo("front", 2, self.validate_window.current_image_front_2)
        if start_index + 2 <= list_length - 1:
            find_index_3 = self.match_list[start_index + 2][0]
            model_index_3 = self.match_list[start_index + 2][1]
            similarity_3= self.match_list[start_index + 2][2]

            self.validate_window.current_model_3 = self.model.get_model(model_index_3)
            self.validate_window.display_model_screenshot(3)

            self.validate_window.update_find_match_info(find_index_3, model_index_3, similarity_3, 3)

            self.validate_window.current_image_back_3 = self.model.get_find(find_index_3)[0]
            self.validate_window.current_image_front_3 = self.model.get_find(find_index_3)[1]
            self.validate_window.display_find_photo("back", 3, self.validate_window.current_image_back_3)
            self.validate_window.display_find_photo("front", 3, self.validate_window.current_image_front_3)

    def clear_matches(self):
        if self.validate_window is None: return
        self.validate_window.init_variables()
        # Optionally, you can also call a method to update the display
        self.validate_window.clear_find_photos(1)
        self.validate_window.clear_find_photos(2)
        self.validate_window.clear_find_photos(3)

        self.validate_window.clear_model_screenshot(1)
        self.validate_window.clear_model_screenshot(2)
        self.validate_window.clear_model_screenshot(3)

        self.validate_window.clear_model_match_info()

    def close_validation(self):
        """关闭验证窗口返回主界面"""
        if self.validate_window:
            self.validate_window.validation_progress.setValue(0)
            self.validate_window.validation_progress.setMaximum(50)
            self.match_list = []
            self.display_match_index = 0

            self.validate_window.close()
            self.validate_window = None

    #todo: edit_window

    def handle_frame_double_click(self, frame_id):
        match_index = self.display_match_index + (frame_id - 1)
        find_index, model_index, _ = self.match_list[match_index]
        find_path = self.model.get_find(find_index)


        self.model_list = self.model.recommand_models(find_index, 10)

        self.edit_window = EditMatchingWindow(self.validate_window, self)

        self.edit_window.show()

        #to be replace
        self.edit_window.clear_find_photos()
        self.edit_window.display_find_photo("back", find_path[0])
        self.edit_window.display_find_photo("front", find_path[1])
        self.edit_window.findid_v.setText(f"Find ID: {find_index}")
        self.display_model_index = 0
        self.display_models(self.display_model_index)



        # 冻结验证窗口
        self.validate_window.setEnabled(False)
        self.edit_window.setEnabled(True)



        # 连接更新按钮
        self.edit_window.update_button.clicked.connect(self.handle_update_match)
        self.edit_window.rejected.connect(self.close_edit)


        self.edit_window.previous_button.clicked.connect(self.handle_previous_button_edit)
        self.edit_window.next_button.clicked.connect(self.handle_next_button_edit)



    def handle_previous_button_edit(self):
        if self.display_model_index - 6 < 0:
            QMessageBox.warning(self.edit_window, "Warning", "You have reached the beginning.")
        else:
            self.display_model_index -= 6
            self.display_models(self.display_model_index)

    def handle_next_button_edit(self):
        if self.display_model_index + 6 >= len(self.match_list):
            QMessageBox.warning(self.validate_window, "Warning", "You have reached the end.")
        else:
            self.display_model_index += 6
            self.display_models(self.display_model_index)


    def display_models(self, start_index):
        if self.edit_window is None:
            print("self.edit_window is None")
            return
        if self.model_list is None:
            print("self.model_list is None")
            return

        self.clear_models()

        list_length = len(self.model_list)
        find_id_text = self.edit_window.findid_v.text().replace("Find ID: ", "")
        find_id = int(find_id_text)

        for i in range(6):  # Changed from 4 to 6 (slots 1 to 6)
            list_index = start_index + i
            slot_number = i + 1  # Frame slot numbers are 1-indexed

            if list_index < list_length:
                model_id, similarity = self.model_list[list_index]

                model_data = self.model.get_model(model_id)
                setattr(self.edit_window, f"current_model_{slot_number}", model_data)
                self.edit_window.update_model_match_info(model_id, similarity, slot_number)
                self.edit_window.display_model_screenshot(slot_number)

                # Apply frame color based on match status
                self.display_model_color(slot_number, find_id, model_id)
            else:
                # Clear frame styling and any residual content
                self.edit_window.clear_model_frame_color(slot_number)

    # Update clear_models:
    def clear_models(self):
        if self.edit_window is None: 
            return
            
        # Initialize variables for all 6 models
        self.edit_window.current_model_1 = ""
        self.edit_window.current_model_2 = ""
        self.edit_window.current_model_3 = ""
        self.edit_window.current_model_4 = ""
        self.edit_window.current_model_5 = ""
        self.edit_window.current_model_6 = ""
        
        # Clear all model screenshots
        for i in range(1, 7):  # Changed from 5 to 7
            self.edit_window.clear_model_screenshot(i)
            self.edit_window.clear_model_frame_color(i)
        
        # Clear model match info
        self.edit_window.clear_model_match_info()

    def handle_update_match(self):
        """处理更新匹配按钮"""
        if self.edit_window:
            self.edit_window.close()
            self.edit_window = None

            # 解冻验证窗口
            self.validate_window.setEnabled(True)


    def close_edit(self):
        """关闭验证窗口返回主界面"""
        if self.edit_window:
            self.edit_window.close()
            self.edit_window = None
            self.validate_window.setEnabled(True)




