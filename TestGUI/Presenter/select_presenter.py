import logging
from typing import List, Tuple

from TestGUI.Presenter.get_similarity_matrix import GetSimilarityMatrixMixin
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

logger = logging.getLogger(__name__)

class SelectMethodPresenterMixin(GetSimilarityMatrixMixin):

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
        self.on_load_all_clicked()
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

        self.show_loading_window()


    #todo: loading window

    def show_loading_window(self):
        selected_context = self.main_model.selected_context
        if not selected_context:
            self.main_view.display_error("Please select a context first")
            logger.error("Tried to load finds and models without context selected")
            return

        # 加载finds和models
        finds_list = list(self.main_model.finds_dict.values())
        models_list = self.main_model.a3dmodels_list

        # 创建加载窗口
        self.loading_window = LoadingWindow(
            self.main_view,
            self,
            total_finds=len(finds_list),
            total_models=len(models_list)
        )
        self.loading_window.show()

        # 初始化状态
        self.finds_measured = 0
        self.models_measured = 0
        self.similarity_matrix = None

        # 测量finds
        self.main_view.general_status.setText("Measuring finds in background")
        find_worker = self.main_model.load_finds(
            color_grid=self.main_view.current_color_grid()
        )

        # 连接finds worker信号
        find_worker.signals.progress.connect(self.on_find_progress)
        find_worker.signals.finished.connect(self.on_measure_finds_finished)
        find_worker.signals.error.connect(self.on_task_error)

        # 测量models
        self.main_view.general_status.setText("Measuring models in background")
        model_worker = self.main_model.load_a3dmodels()

        # 连接models worker信号
        model_worker.signals.progress.connect(self.on_model_progress)
        model_worker.signals.finished.connect(self.on_measure_models_finished)
        model_worker.signals.error.connect(self.on_task_error)

        # 启动工作线程
        self.threadpool.start(find_worker)
        self.threadpool.start(model_worker)

    def on_find_progress(self, progress_data):
        """处理find测量进度更新"""
        message, progress_percent, find_number = progress_data
        self.finds_measured += 1
        if self.loading_window:
            self.loading_window.update_finds_progress(
                self.finds_measured,
                len(self.finds_list))
            self.main_view.general_status.setText(message)

    def on_model_progress(self, progress_data):
        """处理model测量进度更新"""
        message, progress_percent, model_id = progress_data
        self.models_measured += 1
        if self.loading_window:
            self.loading_window.update_models_progress(
                self.models_measured,
                len(self.models_list))
        self.main_view.general_status.setText(message)

    def on_measure_finds_finished(self, message):
        """finds测量完成"""
        logger.info(message)
        self.finds_measurement_complete = True
        self.check_measurements_complete()

    def on_measure_models_finished(self, message):
        """models测量完成"""
        logger.info(message)
        self.models_measurement_complete = True
        self.check_measurements_complete()

    def check_measurements_complete(self):
        """检查所有测量是否完成"""
        if not (hasattr(self, 'finds_measurement_complete') or \
                not (hasattr(self, 'models_measurement_complete'))):
            return

        if self.finds_measurement_complete and self.models_measurement_complete:
            # 显示相似度矩阵计算状态
            if self.loading_window:
                self.loading_window.show_similarity_computation()

            # 计算相似度矩阵
            self.compute_similarity_matrix()

    #todo: finish measuring

    def compute_similarity_matrix(self):
        main_model: MainModel = self.main_model
        find_list, model_list = main_model.finds_list, main_model.a3dmodels_list

        #if self.loading_window:
            #self.loading_window.status_label_1.setText("Computing Similarity Matrix...")
        main_model.similarity_matrix = self.calculate_similarity_matrix(find_list, model_list)


        #def

        if self.loading_window:
            self.loading_window.show_recommending_matches()
        self.recommend_matches()
            #self.loading_window.progress_bar_1.setMaximum(len(matches))
            #self.loading_window.progress_bar_1.setValue(0)
            # 关闭加载窗口并打开验证窗口
            #self.loading_window.close()
            #self.show_validation_window(algorithm, model_filter)

    def recommend_matches(self):
        self.match_list = self.main_model.solve_matching()

        #if self.loading_window:
            #self.loading_window.status_label_1.setText("Recommending Automated Matches...")
        #def when finished
        if self.loading_window:
            self.loading_window.show_match_applying()
        self.apply_matches()

    def apply_matches(self, matches: List[Tuple[int, str, float]]):
        """应用匹配结果"""
        # 1. 显示应用匹配状态
        if self.loading_window:
            self.loading_window.status_label_1.setText("Applying Automated Matches...")
            self.loading_window.progress_bar_1.setMaximum(len(matches))
            self.loading_window.progress_bar_1.setValue(0)

        # 2. 先取消所有现有匹配
        self.unmatch_all_finds()

        # 3. 应用新匹配
        self.total_match_tasks = len(matches)
        self.completed_match_tasks = 0
        self.match_workers = []

        # 创建所有匹配任务
        for find_number, model_str, similarity in matches:
            # 创建数据库更新和文件拷贝任务
            worker = self.main_model.apply_match(find_number, model_str)
            if worker:
                worker.signals.progress.connect(self.on_file_task_progress)
                worker.signals.finished.connect(self.on_match_task_finished)
                worker.signals.error.connect(self.on_file_task_error)
                self.match_workers.append(worker)

                # 更新相似度分数
                find = self.main_model.finds_dict.get(find_number)
                if find:
                    find.similarity_score = similarity

        # 4. 启动所有匹配任务
        if self.match_workers:
            for worker in self.match_workers:
                self.threadpool.start(worker)
        else:
            self.on_all_match_tasks_finished()

    def unmatch_all_finds(self):
        """取消所有现有匹配"""
        # 收集所有有匹配的find
        finds_to_unmatch = [
            f for f in self.main_model.finds_dict.values() if f.is_matched
        ]

        if not finds_to_unmatch:
            return

        # 创建取消匹配任务
        self.total_unmatch_tasks = len(finds_to_unmatch)
        self.completed_unmatch_tasks = 0
        self.unmatch_workers = []

        # 显示取消匹配状态
        if self.loading_window:
            self.loading_window.status_label_1.setText("Removing Previous Matches...")
            self.loading_window.progress_bar_1.setMaximum(self.total_unmatch_tasks)
            self.loading_window.progress_bar_1.setValue(0)

        # 创建所有取消匹配任务
        for find in finds_to_unmatch:
            worker = self.main_model.apply_unmatch(find.find_number)
            if worker:
                worker.signals.progress.connect(self.on_file_task_progress)
                worker.signals.finished.connect(self.on_unmatch_task_finished)
                worker.signals.error.connect(self.on_file_task_error)
                self.unmatch_workers.append(worker)

        # 启动所有取消匹配任务
        if self.unmatch_workers:
            for worker in self.unmatch_workers:
                self.threadpool.start(worker)

    def on_match_task_finished(self, message):
        """单个匹配任务完成"""
        logger.info(message)
        self.completed_match_tasks += 1

        # 更新进度
        if self.loading_window:
            self.loading_window.progress_bar_1.setValue(self.completed_match_tasks)
            self.loading_window.status_label_1.setText(
                f"Applying match {self.completed_match_tasks}/{self.total_match_tasks}"
            )

        # 检查所有任务是否完成
        if self.completed_match_tasks >= self.total_match_tasks:
            self.on_all_match_tasks_finished()

    def on_unmatch_task_finished(self, message):
        """单个取消匹配任务完成"""
        logger.info(message)
        self.completed_unmatch_tasks += 1

        # 更新进度
        if self.loading_window:
            self.loading_window.progress_bar_1.setValue(self.completed_unmatch_tasks)
            self.loading_window.status_label_1.setText(
                f"Removing match {self.completed_unmatch_tasks}/{self.total_unmatch_tasks}"
            )

        # 检查所有任务是否完成
        if self.completed_unmatch_tasks >= self.total_unmatch_tasks:
            # 所有取消匹配完成，可以开始应用新匹配
            pass

    def on_all_match_tasks_finished(self):
        """所有匹配任务完成"""
        logger.info("所有匹配任务已完成")

        # 5. 完成处理
        if self.loading_window:
            self.loading_window.close()

        # 6. 更新UI并显示验证窗口
        self.main_view.general_status.setText("匹配应用完成")
        self.populate_finds()
        self.populate_unsorted_models()
        self.show_validation_window(self.matching_algorithm, self.model_filter)

    def on_file_task_progress(self, progress: Tuple[str, int]):
        """文件任务进度更新"""
        message, percent = progress
        self.main_view.display_progress((message, percent))

    def on_file_task_error(self, message: str):
        """文件任务错误处理"""
        self.main_view.display_progress((f"错误: {message}", 0))
        logger.error(message)



