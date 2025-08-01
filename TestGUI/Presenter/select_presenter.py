
import logging
from typing import List, Tuple

from TestGUI.model.workers.calculate_similarity_worker import MissingSimilarityWorker
from TestGUI.view.select_test import SelectMethodWindow
from TestGUI.view.select_test import SelectAlgorithmWindow
from TestGUI.view.select_test import LoadingWindow

from model.main_model import MainModel
from presenter.main_presenter import MainPresenter

logger = logging.getLogger(__name__)


class SelectMethodPresenterMixin():
    def __init__(self):
        self.selected_algorithm = "reciprocal"
        self.selected_model_fiter= "all" #unmatched

    #todo: method selection
    def show_method_selection(self):
        """显示匹配方法选择窗口"""
        self.method_window = SelectMethodWindow(self.main_view, self)
        self.method_window.show()
        self.method_window.manual_button.clicked.connect(self.handle_manual_selected)
        self.method_window.automated_button.clicked.connect(self.handle_automated_selected)

    def handle_manual_selected(self):
        """处理手动匹配选择"""
        self.on_load_all_clicked()
        self.method_window.close()

    def handle_automated_selected(self):
        """处理自动匹配选择"""
        self.main_model.load_finds_automated()
        self.main_model.load_a3dmodel_automated()

        self.main_model.load_similarity_matrix_from_cache()
        self.missing_keys = self.main_model.check_missing_keys()

        self.show_algorithm_selection()
        self.method_window.close()

    # todo: algorithm selection
    def show_algorithm_selection(self):
        """显示算法选择窗口"""
        self.algorithm_window = SelectAlgorithmWindow(self.main_view, self)
        self.algorithm_window.show()

        total_length = len(self.main_model.similarity_matrix)
        missing_length = len(self.missing_keys)

        if self.missing_keys:
            self.algorithm_window.show_missing_info(missing_length,total_length)
        else:
            self.algorithm_window.show_complete_info(total_length)

        self.algorithm_window.load_button.clicked.connect(self.handle_load_button)
        self.algorithm_window.back_button.clicked.connect(self.handle_back_button)

    def handle_load_button(self):
        self.selected_algorithm  = self.algorithm_window.algorithm_combo.currentText()
        self.selected_model_fiter= self.algorithm_window.models_combo.currentText()

        self.algorithm_window.close()
        self.show_loading_window()

    def handle_back_button(self):
        """处理返回按钮"""
        self.algorithm_window.close()
        self.show_method_selection()

    # todo: show loading window
    def show_loading_window(self):
        # 初始化状态
        self.finds_measured = 0
        self.models_measured = 0

        # 创建加载窗口
        self.loading_window = LoadingWindow(
            self.main_view,
            self,
        )
        self.loading_window.show()
        self.load_cache_and_check_completeness()

    def load_cache_and_check_completeness(self):

        if not self.missing_keys:
            # 缓存完整，直接进入推荐匹配
            logger.info("相似度矩阵缓存完整，跳过计算")
            if self.loading_window:
                self.loading_window.show_recommending_matches()
            self.recommend_matches()
        else:
            # 缓存不完整，需要测量相关对象
            logger.info(f"相似度矩阵有 {len(self.missing_keys)} 个缺失项，将重新计算")
            self.prepare_for_missing_similarity_calculation()

    def prepare_for_missing_similarity_calculation(self):
        """准备缺失相似度计算所需的数据"""
        # 收集需要测量的find和model
        self.missing_find_numbers = set()
        self.missing_model_ids = set()

        for find_num, model_str in self.missing_keys:
            self.missing_find_numbers.add(find_num)
            self.missing_model_ids.add(model_str)

        # 初始化计数器
        self.measured_finds = 0
        self.measured_models = 0

        # 测量缺失的finds
        self.measure_missing_finds()
        # 测量缺失的models
        self.measure_missing_models()

    # todo: measure finds and models
    def measure_missing_finds(self):
        """测量缺失的finds"""
        if not self.missing_find_numbers:
            self.on_missing_finds_finished()
            return

        #self.main_view.general_status.setText("测量缺失的finds...")

        if self.loading_window:
            self.loading_window.show_finds_measurement(len(self.missing_find_numbers))

        # 获取需要测量的finds
        finds_to_measure = [
            f for f in self.main_model.finds_list
            if f.find_number in self.missing_find_numbers
        ]

        if not finds_to_measure:
            self.on_missing_finds_finished()
            return

        # 创建find worker
        find_worker = self.main_model.measure_specific_finds(
            finds_to_measure,
            color_grid=self.main_view.current_color_grid()
        )

        # 连接信号
        find_worker.signals.progress.connect(self.on_missing_find_progress)
        find_worker.signals.finished.connect(self.on_missing_finds_finished)
        find_worker.signals.error.connect(self.on_task_error)

        # 启动工作线程
        self.threadpool.start(find_worker)

    def measure_missing_models(self):
        """测量缺失的models"""
        if not self.missing_model_ids:
            self.on_missing_models_finished()
            return

        #self.main_view.general_status.setText("测量缺失的models...")

        if self.loading_window:
            self.loading_window.show_models_measurement(len(self.missing_model_ids))

        # 获取需要测量的models
        models_to_measure = [
            m for m in self.main_model.a3dmodels_list
            if str(m) in self.missing_model_ids
        ]

        if not models_to_measure:
            self.on_missing_models_finished()
            return

        # 创建model worker
        model_worker = self.main_model.load_specific_models(models_to_measure)

        # 连接信号
        model_worker.signals.progress.connect(self.on_missing_model_progress)
        model_worker.signals.finished.connect(self.on_missing_models_finished)
        model_worker.signals.error.connect(self.on_task_error)

        # 启动工作线程
        self.threadpool.start(model_worker)

    def on_missing_find_progress(self, progress_data):
        """处理缺失find测量进度更新"""
        message, progress_percent, find_number = progress_data
        self.measured_finds += 1
        if self.loading_window:
            self.loading_window.update_finds_progress(self.measured_finds, len(self.missing_find_numbers))

        #self.main_view.general_status.setText(message)

    def on_missing_model_progress(self, progress_data):
        """处理缺失model测量进度更新"""
        message, progress_percent, model_id = progress_data
        self.measured_models += 1
        if self.loading_window:
            self.loading_window.update_finds_progress(self.measured_models, len(self.missing_model_ids))
        #self.main_view.general_status.setText(message)

    def on_missing_finds_finished(self, message="缺失finds测量完成"):
        """缺失finds测量完成"""
        logger.info(message)
        self.finds_measurement_complete = True
        self.check_missing_measurements_complete()

    def on_missing_models_finished(self, message="缺失models测量完成"):
        """缺失models测量完成"""
        logger.info(message)
        self.models_measurement_complete = True
        self.check_missing_measurements_complete()

    # todo: compute missing similarities
    def check_missing_measurements_complete(self):
        """检查所有缺失对象的测量是否完成"""
        if not hasattr(self, 'finds_measurement_complete') or \
                not hasattr(self, 'models_measurement_complete'):
            return

        if self.finds_measurement_complete and self.models_measurement_complete:
            # 显示相似度矩阵计算状态
            if self.loading_window:
                self.loading_window.show_similarity_computation()

            self.measured_finds = 0
            self.measured_models = 0
            # 计算缺失的相似度分数
            self.compute_missing_similarity()

    def compute_missing_similarity(self):
        """计算缺失的相似度分数"""
        logger.info(f"开始计算 {len(self.missing_keys)} 个缺失的相似度分数")

        if self.loading_window:
            self.loading_window.show_similarity_computation(len(self.missing_keys))

        # 创建并配置worker
        self.missing_worker = MissingSimilarityWorker(
            self.missing_keys,
            self.main_model,
            self  # 因为继承了GetSimilarityMatrixMixin
        )
        self.missing_worker.signals.progress.connect(self.on_missing_similarity_progress)
        self.missing_worker.signals.finished.connect(self.on_missing_similarity_finished)
        self.missing_worker.signals.error.connect(self.on_similarity_error)

        # 启动worker
        self.threadpool.start(self.missing_worker)

    def on_missing_similarity_progress(self, progress_data):
        """处理缺失相似度计算进度"""
        current_count, total_count, find_number, model_id = progress_data
        if self.loading_window:
            self.loading_window.update_show_similarity_computation(current_count, total_count, find_number, model_id)

    def on_missing_similarity_finished(self):
        """缺失相似度计算完成"""
        logger.info("缺失相似度计算完成")
        if self.loading_window:
            self.loading_window.show_recommending_matches()
        self.recommend_matches()

    def on_similarity_error(self, error_message):
        """处理相似度计算错误"""
        logger.error(f"相似度计算错误: {error_message}")
        if self.loading_window:
            self.loading_window.close()
        self.main_view.display_error(f"相似度计算错误: {error_message}")

    # todo: recommand matches
    def recommend_matches(self:MainPresenter):
        algorithm, model_filter = self.selected_algorithm,self.selected_model_fiter
        self.match_list = self.main_model.solve_matching(algorithm, model_filter)

        #if self.loading_window:
            #self.loading_window.show_match_applying()
        #self.apply_matches(self.match_list)
        self.show_validation_window()
