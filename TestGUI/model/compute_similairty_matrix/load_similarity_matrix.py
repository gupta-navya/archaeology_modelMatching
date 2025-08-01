from diskcache import Cache
from TestGUI.model.workers.calculate_similarity_worker import MissingSimilarityWorker

import logging
logger = logging.getLogger(__name__)

class ComputeSimilarityMixin:
    def __init__(self):
        # 初始化相似度矩阵缓存
        self.cache_sim_matrix = Cache("./cache/cache_sim_matrix")
        self.similarity_matrix = {}

    def load_similarity_matrix_from_cache(self):
        """从缓存加载相似度矩阵，未命中的项设为-1"""
        self.similarity_matrix = {}
        for find in self.finds_list:
            for model in self.a3dmodels_list:
                key = (find.find_number, str(model))
                # 尝试从缓存获取
                value = self.cache_sim_matrix.get(key, -1)
                self.similarity_matrix[key] = value

    def check_missing_keys(self):
        missing_keys = []
        for key, value in self.similarity_matrix.items():
            if value == -1:
                missing_keys.append(key)

        return missing_keys



    def compute_missing_similarity(self, missing_keys):
        """计算缺失的相似度"""
        missing_keys = self.check_missing_keys()
        if missing_keys:
            worker = MissingSimilarityWorker(
                missing_keys,
                self.main_model,
                self
            )
        return worker







