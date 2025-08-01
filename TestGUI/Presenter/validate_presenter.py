from typing import Tuple

from TestGUI.model.workers.remove_ply_worker import RemovePlyWorker
from TestGUI.view.validate_test import ValidateMatchingWindow
from TestGUI.view.edit_test import EditMatchingWindow

from view.main_view import MainView

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

from model.main_model import MainModel
from model.models import ObjectFind, A3DModel
from model.workers.fix_move_ply_worker import FixMovePlyWorker
from presenter.main_presenter import MainPresenter
import logging
logger = logging.getLogger(__name__)
#core:
#self.match_list
#self.is_validated_dir = {}

class ValidateMatchesPresenterMixin:

    ''''''
    # todo: validation window presenter
    # self.match_list
    def show_validation_window(self: MainPresenter):
        """显示验证匹配窗口"""
        self.validate_window = ValidateMatchingWindow(self.main_view, self)
        self.validate_window.show()


        self.validation_window.set_general_information(
            context_name = str(self.main_model.selected_context),
            total_find = len(self.main_model.finds_dict),
            total_models = len(self.main_model.a3dmodels_dict),
            automatches = len(self.match_list)
        )

        self.is_validated_dict = {match: False for match in self.match_list}
        self.match_status_dict = self.main_model.get_match_status_dict(self.match_list)


        self.display_match_index = 0
        self.max_display_index = 3
        self.display_matches(self.display_match_index)

        self.validate_window.display_general_information(
            current_progress = self.max_display_index,
            automatches = len(self.match_list)
        )



        # 连接双击事件
        for i in range(1, 4):
            frame = getattr(self.validate_window, f"validate_match_frame{i}")
            frame.mouseDoubleClickEvent = lambda event, frame_id=i: self.handle_frame_double_click(frame_id)

        # 连接完成按钮
        self.validate_window.finish_button.clicked.connect(self.close_validation)
        self.validate_window.previous_button.clicked.connect(self.handle_previous_button_validate)
        self.validate_window.next_button.clicked.connect(self.handle_next_button_validate)

    def closeEvent(self, event):
        # 在关闭对话框时调用指定的槽函数
        self.closeEvent()
        event.accept()  # 接受关闭事件

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
            self.apply_confirm_matches(self.display_match_index)

            self.display_match_index += 3
            self.max_display_index = max(self.max_display_index, self.display_match_index + 3)

            self.display_matches(self.display_match_index)
            self.display_match_color(self.display_match_index)

            self.validate_window.display_general_information(
                current_progress=self.max_display_index,
                automatches=len(self.match_list)
            )

    def apply_confirm_matches(self, start_index):
        list_length = len(self.match_list)
        if start_index <= list_length - 1:
            match = self.match_list[start_index + 0]
            self.apply_update_match(match)

        if start_index + 1 <= list_length - 1:
            match = self.match_list[start_index + 1]
            self.apply_update_match(match)

        if start_index + 2 <= list_length - 1:
            match = self.match_list[start_index + 2]
            self.apply_update_match(match)

    def display_match(self, match: Tuple[int, str, float], frame_id):
        find_number, model_str, similarity = match
        self.validate_window.update_find_match_info(find_number, model_str, similarity, 1)

        main_model: MainModel = self.main_model
        objectfind = main_model.finds_dict[find_number]
        a3dmodel: A3DModel = main_model.a3dmodels_dict[model_str]

        back_photo_path = objectfind.photo_path(side='back')
        front_photo_path = objectfind.photo_path(side='front')
        self.validate_window.display_find_photo("back", frame_id, back_photo_path)
        self.validate_window.display_find_photo("front", frame_id, front_photo_path)

        ply_path = a3dmodel.get_file("mesh")
        self.validate_window.display_model_screenshot(frame_id, ply_path=ply_path)
        # self.validate_window.current_image_back_1 = self.model.get_find(find_index_1)[0]
        # self.validate_window.current_image_front_1 = self.model.get_find(find_index_1)[1]
        # self.validate_window.display_find_photo("back", 1, self.validate_window.current_image_back_1)
        # self.validate_window.display_find_photo("front", 1, self.validate_window.current_image_front_1)

    def display_matches(self: MainPresenter, start_index):
        if self.validate_window is None: return
        if self.match_list is None: return
        self.clear_matches()

        list_length = len(self.match_list)
        if start_index <= list_length - 1:
            match = self.match_list[start_index + 0]
            self.display_match(match, 1)

        if start_index + 1 <= list_length - 1:
            match = self.match_list[start_index + 1]
            self.display_match(match, 2)

        if start_index + 2 <= list_length - 1:
            match = self.match_list[start_index + 2]
            self.display_match(match, 3)

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

    def display_match_color(self, start_index):

        list_length = len(self.match_list)
        if start_index <= list_length - 1: #status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index],5)
            self.validate_window.display_frame_color(1,status_flag )
            is_validated_flag_1 = self.is_validated_dict[self.match_list[start_index]]
        else:
            self.validate_window.clear_frame_color(1)
            is_validated_flag_1 = False

        if start_index + 1 <= list_length - 1:
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 1], 5)
            self.validate_window.display_frame_color(2, status_flag)
            is_validated_flag_2 = self.is_validated_dict[self.match_list[start_index + 1]]
        else:
            self.validate_window.clear_frame_color(2)
            is_validated_flag_2 = False

        if start_index + 2 <= list_length - 1:
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 2], 5)
            self.validate_window.display_frame_color(3, status_flag)
            is_validated_flag_3 = self.is_validated_dict[self.match_list[start_index + 2]]
        else:
            self.validate_window.clear_frame_color(3)
            is_validated_flag_3 = False

        if (start_index <= self.max_display_index - 1) and is_validated_flag_1:
            self.validate_window.display_frame_color(1,6)

        if (start_index + 1<= self.max_display_index - 1) and is_validated_flag_2:
            self.validate_window.display_frame_color(2, 6)

        if (start_index + 2 <= self.max_display_index - 1) and is_validated_flag_3:
            self.validate_window.display_frame_color(3, 6)

    def close_validation(self):
        """关闭验证窗口返回主界面"""
        if self.validate_window:
            self.apply_confirm_matches(self.display_match_index)
            #self.validate_window.validation_progress.setValue(0)
            #self.validate_window.validation_progress.setMaximum(50)
            self.match_list = []
            self.match_status_dict = {}
            self.display_match_index = 0
            self.max_display_index = 3

            self.validate_window.close()
            self.validate_window = None

    def apply_single_match(self, match: Tuple[int,str,float]):

        self.is_validated_dict[match] = True

        find_index, model_str, _ = match
        logger.info(f"Confirming Match: {find_index} - {model_str}")

        worker:FixMovePlyWorker = self.main_model.apply_match(find_index)
        #worker.signals.progress.connect(self.on_task_progress)
        worker.signals.finished.connect(self.on_apply_update_match_finished)
        #worker.signals.error.connect(self.on_apply_update_match_error)
        self.threadpool.start(worker)

    def apply_update_match(self, match: Tuple[int,str,float]):
        """处理更新匹配按钮"""
        find_num, new_model_str, _ = match

        "deal with the backend"
        new_model:A3DModel =self.main_model.a3dmodels_dict[new_model_str]
        if new_model.is_matched:
            old_find_num = new_model.get_matches(self.conn.cursor)[0] #[1,2,3]
            if old_find_num != find_num:
                self.apply_single_unmatch(old_find_num, new_model_str, 0)

        current_find:ObjectFind = self.main_model.finds_dict[find_num]
        if current_find.is_matched:
            current_model_str = current_find.get_match_str()
            if current_model_str != new_model_str:
                self.apply_single_unmatch(find_num, current_model_str, 0)

        self.apply_single_match((find_num, new_model_str, 0))
        self.remove_and_replace_match_list(find_num, new_model_str)

        "update validate window"
        self.match_status_dict[(find_num, new_model_str)] = 6
        self.display_matches(self.display_match_index)
        self.display_match_color(self.display_match_index)
        self.validate_window.display_general_information(
            current_progress = self.max_display_index,
            automatches = len(self.match_list)
        )

    def apply_single_unmatch(self, match: Tuple[int,str,float]):
        self.is_validated_dict.pop(match)
        self.match_list.remove(match)

        find_index, model_str, _ = match
        logger.info(f"Decoupling Match: {find_index} - {model_str}")

        worker:RemovePlyWorker = self.main_model.apply_unmatch(find_index)
        self.threadpool.start(worker)

    def on_apply_update_match_finished(self, info:str):
        logger.info(info)





    #todo: edit window presenter

    def handle_match_frame_double_click(self, match_frame_id):
        match_index = self.display_match_index + (match_frame_id - 1)
        match = self.match_list[match_index]
        self.current_edit_match = match

        find_number, model_str, similarity = match
        find_number = self.model.get_find(find_number)

        self.model_score_list = self.main_model.recommend_models(find_number, self.selected_model_fiter, 20)
        self.model_status_dict = self.main_model.get_match_status_dict(find_number, self.model_score_list, self.match_list)

        self.show_edit_window()

    def show_edit_window(self):
        self.edit_window = EditMatchingWindow(self.validate_window, self)
        self.edit_window.show()

        find_number, model_str, similarity = self.current_edit_match
        objectfind = self.mainmodel.finds_dict[find_number]

        self.edit_window.findid_v.setText(f"Find ID: {find_number}")
        self.edit_window.clear_find_photos()
        back_photo_path = objectfind.photo_path(side='back')
        front_photo_path = objectfind.photo_path(side='front')
        self.edit_window.display_find_photo("back",  back_photo_path)
        self.edit_window.display_find_photo("front",  front_photo_path)


        self.display_model_index = 0
        self.completed_tasks = 0
        self.display_models(self.display_model_index)

        # 冻结验证窗口
        self.validate_window.setEnabled(False)
        self.edit_window.setEnabled(True)
        self.edit_window.update_button.setEnabled(False)


        # 连接按钮
        self.edit_window.update_button.clicked.connect(self.handle_update_match)
        self.edit_window.rejected.connect(self.close_edit)
        self.set_up_model_selection()

        self.edit_window.previous_button.clicked.connect(self.handle_previous_button_edit)
        self.edit_window.next_button.clicked.connect(self.handle_next_button_edit)

    def set_up_model_selection(self):
        if self.edit_window:
            """设置模型选择事件"""
            for i in range(1, 7):
                frame = getattr(self, f"validate_match_frame{i}", None)
                if frame:
                    frame.mouseDoubleClickEvent = lambda event, idx=i: self.handle_model_frame_clicked(idx)


    def display_model(self,model_score, frame_id):
        model_str, similarity = model_score

        self.edit_window.update_model_match_info(model_str, similarity, frame_id)

        ply_path = self.main_model.a3dmodels_dict[model_str].get_file("mesh")
        self.edit_window.display_model_screenshot(frame_id, ply_path=ply_path)

        setattr(self, f"current_model_str_{frame_id}", model_str)

        '''
            odel_index_2 = self.model_list[start_index + 1][0]
            similarity_2 = self.model_list[start_index + 1][1]

            self.edit_window.current_model_2 = self.model.get_model(model_index_2)
            self.edit_window.update_model_match_info(model_index_2, similarity_2, 2)
            self.edit_window.display_model_screenshot(2)
        '''

    def display_models(self, start_index):
        if self.edit_window is None:
            print("self.edit_window is None")
            return
        if self.model_list is None:
            print("self.model_list is None")
            return
        self.clear_models()

        list_length = len(self.model_list)

        if start_index + 0<= list_length - 1:
            model_score = self.model_list[start_index]
            self.display_model(model_score, 1)

        if start_index + 1 <= list_length - 1:
            model_score = self.model_list[start_index + 1]
            self.display_model(model_score, 2)

        if start_index + 2 <= list_length - 1:
            model_score = self.model_list[start_index + 2]
            self.display_model(model_score, 3)

        if start_index + 3 <= list_length - 1:
            model_score = self.model_list[start_index + 3]
            self.display_model(model_score, 4)

        if start_index + 4 <= list_length - 1:
            model_score = self.model_list[start_index + 4]
            self.display_model(model_score, 5)

        if start_index + 5 <= list_length - 1:
            model_score = self.model_list[start_index + 5]
            self.display_model(model_score, 6)

    def clear_models(self):
        if self.validate_window is None: return
        self.edit_window.init_variables()
        for i in range(1,7):
            setattr(self,  f"current_model_str_{i}", None)
        # Optionally, you can also call a method to update the display
        #self.edit_window.clear_find_photos()
        self.edit_window.clear_model_screenshot(1)
        self.edit_window.clear_model_screenshot(2)
        self.edit_window.clear_model_screenshot(3)
        self.edit_window.clear_model_screenshot(4)
        self.edit_window.clear_model_screenshot(5)
        self.edit_window.clear_model_screenshot(6)
        self.edit_window.clear_model_match_info()

    def display_model_color(self, start_index):

        # Get all recommended matches (each is: (find, model, sim))
        list_length = len(self.model_score_list)
        if start_index <= list_length - 1:  # status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 0], 2)
            self.edit_window.display_frame_color(1, status_flag)

        if start_index + 1 <= list_length - 1:  # status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 1], 2)
            self.edit_window.display_frame_color(2, status_flag)

        if start_index + 2 <= list_length - 1:  # status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 2], 2)
            self.edit_window.display_frame_color(3, status_flag)

        if start_index + 3 <= list_length - 1:  # status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 3], 2)
            self.edit_window.display_frame_color(4, status_flag)

        if start_index + 4 <= list_length - 1:  # status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 4], 2)
            self.edit_window.display_frame_color(5, status_flag)

        if start_index + 5 <= list_length - 1:  # status
            status_flag = self.match_status_dict.get(self.match_status_dict[start_index + 5], 2)
            self.edit_window.display_frame_color(6, status_flag)


    def handle_previous_button_edit(self):
        if self.display_model_index - 4 < 0:
            QMessageBox.warning(self.edit_window, "Warning", "You have reached the beginning.")
        else:
            self.display_model_index -= 4
            self.display_models(self.display_model_index)
            self.display_match_color(self.display_model_index)

    def handle_next_button_edit(self):
        if self.display_model_index + 4 >= len(self.match_list):
            QMessageBox.warning(self.validate_window, "Warning", "You have reached the end.")
        else:
            self.display_model_index += 4
            self.display_models(self.display_model_index)
            self.display_match_color(self.display_model_index)

    def handle_model_frame_clicked(self, model_frame_id: int):
        """处理模型帧的点击事件"""
        # 设置选中的模型
        model_str = getattr(self, f"current_model_str_{model_frame_id}", None)
        self.selected_model_str_for_updating = model_str

        if self.model_status_dict[model_str] == 1:
            pass
        else:
        # 高亮显示选中的模型
            self.edit_window.display_model_frame_color(model_frame_id, 6)
            self.edit_window.update_button.setEnabled(True)

    def remove_and_replace_match_list(self, find_number, model_str):

        match_list = self.match_list
        similarity_score = self.main_model.simialrity_matrix[(find_number, model_str)]
        new_match = (find_number, model_str, similarity_score)

        updated_list = []
        for index, match in enumerate(match_list):
            # 如果匹配 int_value，插入 new_tuple
            if match[0] == find_number:
                updated_list.append(new_match)
            # 如果匹配 str_value，跳过该元组
            elif match[1] == model_str:
                self.max_display_index -= 1
                if index < self.display_match_index:
                    self.display_match_index -= 1
                continue
            else:
                # 保留原元组
                updated_list.append(match)

        self.match_list = updated_list

    def handle_update_match(self):
        """处理更新匹配按钮"""
        find_num = self.current_edit_match[0]
        new_model_str = self.selected_model_str_for_updating
        self.apply_update_match((find_num, new_model_str, 0))
        self.close_edit()


    def close_edit(self):
        """关闭验证窗口返回主界面"""
        if self.edit_window:
            self.edit_window.close()
            self.edit_window = None
            self.validate_window.setEnabled(True)

    '''
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

    '''










