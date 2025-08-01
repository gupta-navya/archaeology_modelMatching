
import logging
from typing import List, Tuple
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
from model.models import ObjectFind, A3DModel

logger = logging.getLogger(__name__)


class MissingSimilarityWorkerSignals(QObject):
    """Signals emitted by MissingSimilarityWorker"""
    progress = pyqtSignal(tuple)  # (current_count, total_count, find_number, model_id)
    finished = pyqtSignal()
    error = pyqtSignal(str)


class MissingSimilarityWorker(QRunnable):
    def __init__(
            self,
            missing_keys: List[Tuple[int, str]],
            main_model,
            similarity_calculator
    ):
        super().__init__()
        self.missing_keys = missing_keys
        self.main_model = main_model
        self.similarity_calculator = similarity_calculator
        self.signals = MissingSimilarityWorkerSignals()

    @pyqtSlot()
    def run(self):
        """计算缺失的相似度分数"""
        total = len(self.missing_keys)
        current = 0

        try:
            for key in self.missing_keys:
                find_num, model_str = key

                # 获取find和model对象
                find = next((f for f in self.main_model.finds_list if f.find_number == find_num), None)
                model = next((m for m in self.main_model.a3dmodels_list if str(m) == model_str), None)

                if find is None or model is None:
                    logger.warning(f"Could not find find or model for key {key}")
                    current += 1
                    continue

                if not find.is_measured or not model.is_measured:
                    logger.warning(f"Find {find_num} or model {model_str} is not measured")
                    # 如果未测量，我们跳过，但缓存中会保持-1？或者可以设置为0？这里我们跳过
                    current += 1
                    continue

                # 计算相似度
                score = self.similarity_calculator.calculate_similarity(find, model)

                # 更新到缓存和当前矩阵
                self.main_model.update_similarity_score_to_cache(find_num, model_str, score)

                current += 1
                self.signals.progress.emit((current, total, find_num, model_str))

            self.signals.finished.emit()
        except Exception as e:
            logger.exception("Error computing missing similarity scores")
            self.signals.error.emit(str(e))


