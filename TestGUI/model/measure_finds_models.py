from TestGUI.model.workers.measure_model_worker import MeasureModelWorker
from model.models import A3DModel
from model.workers.measure_find_worker import MeasureFindWorker


class LoadMissingFind3DModelMixin:
    # 3d model: self.cache_3d
    # 2d photo: self.measure_cache

    def measure_a3dmodel(self, a3dmodel: A3DModel):
        """测量单个3D模型的方法"""
        # 使用现有的测量方法
        return a3dmodel.measure(self.ply_window, self.cache_3d)


    def measure_specific_finds(self, finds_to_measure, color_grid):
        if color_grid.lower() == "default":
            cg = self.predictors["colorgrid"]
        elif color_grid.lower() == "24colorcard":
            cg = self.predictors["colorgrid_24"]
        else:
            raise ValueError(f"Invalid color grid type {color_grid}")
        """加载特定的finds"""
        worker = MeasureFindWorker(
            finds_to_measure,
            self.predictors["ceramics"],
            cg,
            self.measure_cache,
        )
        return worker

    def measure_specific_models(self, models_to_measure):
        """加载特定的models"""
        worker = MeasureModelWorker(
            models_to_measure,
            self.measure_a3dmodel
        )
        return worker


    def ensure_similarity_matrix_complete(self, color_grid):
        """确保相似度矩阵完整，如有缺失则计算缺失项"""
        # 1. 加载缓存
        self.load_similarity_matrix_from_cache()

        # 2. 检查缺失项
        missing_keys, missing_finds, missing_models = self.get_missing_matches()

        if missing_keys:

            find_worker, model_worker = self.load_missing_finds_and_models(
                missing_finds, missing_models, color_grid)

            # 连接信号
            self.connect_workers_signals(find_worker, model_worker)

            # 启动worker
            self.threadpool.start(find_worker)
            self.threadpool.start(model_worker)

            return False  # 表示计算未完成
        else:
            return True  # 表示矩阵已完整

    def connect_workers_signals(self, find_worker, model_worker):
        """连接worker的信号"""
        # 当所有worker完成时触发计算缺失相似度
        self.workers_completed = 0
        self.expected_workers = 2

        def on_worker_finished():
            self.workers_completed += 1
            if self.workers_completed == self.expected_workers:
                self.compute_missing_similarity()

        find_worker.signals.finished.connect(on_worker_finished)
        model_worker.signals.finished.connect(on_worker_finished)