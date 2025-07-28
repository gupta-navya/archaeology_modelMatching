from TestGUI.view.select_test import SelectMethodWindow
from TestGUI.view.select_test import SelectAlgorithmWindow
from TestGUI.view.select_test import LoadingWindow
from TestGUI.view.validate_test import ValidateMatchingWindow
from TestGUI.view.edit_test import EditMatchingWindow
from TestGUI.model.model_test import Validation_Model_Test
from TestGUI.view.main_view_test import MainView

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

from model.main_model import MainModel
from model.models import ObjectFind, A3DModel
from presenter.main_presenter import MainPresenter


class ValidateMatchesPresenterMixin:
    ''''''
    # todo: validation window presenter

    def show_validation_window(self: MainPresenter, algorithm, model_filter):
        """显示验证匹配窗口"""
        self.validate_window = ValidateMatchingWindow(self.main_view, self)
        self.validate_window.show()

        # 设置验证进度
        self.match_list = self.model.solve_matching()
        self.validate_window.validation_progress.setValue(0)
        self.validate_window.validation_progress.setMaximum(40)


        self.display_match_index = 0
        self.display_matches(self.display_match_index)


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

    def handle_next_button_validate(self):
        if self.display_match_index + 3 >= len(self.match_list):
            QMessageBox.warning(self.validate_window, "Warning", "You have reached the end.")
        else:
            for i in range(self.display_match_index,self. display_match_index + 3):
                self.set_match_validated(i)

            self.display_match_index += 3
            self.display_matches(self.display_match_index)

    def set_match_validated(self, num):
        find_index = self.match_list[num][0]
        find:ObjectFind = self.main_model.finds_dict(find_index)
        find.is_validated = True

        #model_index = self.match_list[num][1]
       # similarity_1 = self.match_list[num][2]

    def display_matches(self, start_index):
        if self.validate_window is None: return
        if self.match_list is None: return
        self.clear_matches()

        main_model: MainModel = self.main_model



        list_length = len(self.match_list)
        if start_index <= list_length - 1:
            find_index_1 = self.match_list[start_index][0]
            model_index_1 = self.match_list[start_index][1]

            find_1: ObjectFind = main_model.finds_dict[find_index_1]
            model_1 : A3DModel = main_model.a3dmodels_dict[model_index_1]


            similarity_1= self.match_list[start_index][2]

            self.validate_window.current_model_1 = self.model.get_model(model_index_1)
            self.validate_window.display_model_screenshot(1)

            self.validate_window.update_find_match_info(find_1,1)


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


    #todo: edit window presenter

    def handle_match_frame_double_click(self, match_frame_id):
        match_index = self.display_match_index + (match_frame_id - 1)
        find_index, model_index, _ = self.match_list[match_index]
        find_path = self.model.get_find(find_index)

        self.find_index = find_index
        self.model_index = model_index

        self.model_list = self.model.recommand_models(find_index, 10)
        self.edit_window = EditMatchingWindow(self.validate_window, self)
        self.edit_window.show()

        #to be replace
        self.edit_window.clear_find_photos()
        self.edit_window.display_find_photo("back", find_path[0])
        self.edit_window.display_find_photo("front", find_path[1])
        self.edit_window.findid_v.setText(f"Find ID: {find_index}")

        self.display_model_index = 0
        self.completed_tasks = 0

        self.display_models(self.display_model_index)


        # 冻结验证窗口
        self.validate_window.setEnabled(False)
        self.edit_window.setEnabled(True)
        self.edit_window.update_button.setEnabled(False)
        # 连接更新按钮
        self.edit_window.update_button.clicked.connect(self.handle_update_match)
        self.edit_window.rejected.connect(self.close_edit)
        self.set_up_model_selection()

        self.edit_window.previous_button.clicked.connect(self.handle_previous_button_edit)
        self.edit_window.next_button.clicked.connect(self.handle_next_button_edit)

    #todo:

    def set_up_model_selection(self):
        if self.edit_window:
            """设置模型选择事件"""
            for i in range(1, 5):
                frame = getattr(self, f"validate_match_frame{i}", None)
                if frame:
                    frame.mouseDoubleClickEvent = lambda event, idx=i: self.handle_model_frame_clicked(idx)

    def handle_model_frame_clicked(self, model_frame_id: int):
        """处理模型帧的点击事件"""
        # 设置选中的模型
        model_str = getattr(self.edit_window, f"current_model_{model_frame_id}", None)
        self.selected_model_str_for_updating = model_str

        # 高亮显示选中的模型
        self.edit_window.highlight_selected_model(model_frame_id)
        self.edit_window.update_button.setEnabled(True)



    def display_models(self, start_index):
        if self.edit_window is None:
            print("self.edit_window is None")
            return
        if self.model_list is None:
            print("self.model_list is None")
            return
        self.clear_models()


        list_length = len(self.model_list)
        if start_index <= list_length - 1:

            model_index_1 = self.model_list[start_index][0]
            similarity_1 = self.model_list[start_index][1]


            self.edit_window.current_model_1 = self.model.get_model(model_index_1)
            self.edit_window.update_model_match_info(model_index_1,similarity_1,1)
            self.edit_window.display_model_screenshot(1)


        if start_index + 1 <= list_length - 1:

            model_index_2 = self.model_list[start_index + 1][0]
            similarity_2 = self.model_list[start_index + 1][1]

            self.edit_window.current_model_2 = self.model.get_model(model_index_2)
            self.edit_window.update_model_match_info(model_index_2, similarity_2, 2)
            self.edit_window.display_model_screenshot(2)

        if start_index + 2 <= list_length - 1:

            model_index_3 = self.model_list[start_index + 2][0]
            similarity_3 = self.model_list[start_index + 2][1]

            self.edit_window.current_model_3 = self.model.get_model(model_index_3)
            self.edit_window.update_model_match_info(model_index_3, similarity_3, 3)
            self.edit_window.display_model_screenshot(3)

        if start_index + 3 <= list_length - 1:

            model_index_4 = self.model_list[start_index + 3][0]
            similarity_4 = self.model_list[start_index + 3][1]

            self.edit_window.current_model_4 = self.model.get_model(model_index_4)
            self.edit_window.update_model_match_info(model_index_4, similarity_4, 4)
            self.edit_window.display_model_screenshot(4)

    def clear_models(self):
        if self.validate_window is None: return
        self.edit_window.init_variables()
        # Optionally, you can also call a method to update the display
        #self.edit_window.clear_find_photos()
        self.edit_window.clear_model_screenshot(1)
        self.edit_window.clear_model_screenshot(2)
        self.edit_window.clear_model_screenshot(3)
        self.edit_window.clear_model_screenshot(4)
        self.edit_window.clear_model_match_info()

    def handle_previous_button_edit(self):
        if self.display_model_index - 4 < 0:
            QMessageBox.warning(self.edit_window, "Warning", "You have reached the beginning.")
        else:
            self.display_model_index -= 4
            self.display_models(self.display_model_index)

    def handle_next_button_edit(self):
        if self.display_model_index + 4 >= len(self.match_list):
            QMessageBox.warning(self.validate_window, "Warning", "You have reached the end.")
        else:
            self.display_model_index += 4
            self.display_models(self.display_model_index)

    def handle_update_match(self):
        """处理更新匹配按钮"""
        if self.edit_window:
            find_number = self.find_index
            old_model_str = self.model_index
            new_model_str = self.selected_model_str_for_updating
            self.model_workers = []

            worker = self.main_model.apply_unmatch(find_number)
            if worker:
                worker.signals.progress.connect(self.ignore_signals)
                worker.signals.finished.connect(self.on_unmatch_model_task_finished)
                worker.signals.error.connect(self.on_file_task_error)
                self.unmatch_workers.append(worker)

            worker = self.main_model.apply_match(find_number, new_model_str)
            if worker:
                worker.signals.progress.connect(self.ignore_signals)
                worker.signals.finished.connect(self.on_match_model_task_finished)
                worker.signals.error.connect(self.on_file_task_error)
                self.model_workers.append(worker)

                # 更新相似度分数
                find = self.main_model.finds_dict.get(find_number)
                if find:
                    find.similarity_score = self.main_model.similarity_matrix[find_number][new_model_str]

            # 启动所有(取消)匹配任务
            if self.model_workers:
                for worker in self.model_workers:
                    self.threadpool.start(worker)

            #self.edit_window.update_button.setEnabled(false)


    def close_edit(self):
        """关闭验证窗口返回主界面"""
        if self.edit_window:
            self.edit_window.close()
            self.edit_window = None
            self.validate_window.setEnabled(True)

    def ignore_signals(self):
        pass
    def on_match_task_finished(self, message):
        """单个匹配任务完成"""
        #logger.info(message)
        self.completed_tasks += 1

        # 更新进度
        #if self.loading_window:

        # 检查所有任务是否完成
        if self.completed_match_tasks >= 2:
            self.on_all_match_model_tasks_finished()

    def on_unmatch_model_task_finished(self, message):
        """单个取消匹配任务完成"""
        #logger.info(message)
        self.completed_tasks += 1
        # 更新进度
        #if self.loading_window:

        # 检查所有任务是否完成
        if self.completed_unmatch_tasks >= 2:
            self.on_all_match_model_tasks_finished()
            pass

    def on_all_match_model_tasks_finished(self):
        """所有匹配任务完成"""
        #logger.info("所有匹配任务已完成")
        self.completed_tasks = 0
        self.close_edit()











