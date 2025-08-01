# todo
import logging
from typing import Dict, Tuple, List
from model.models import ObjectFind, A3DModel
from presenter.mixins.calculate_similarity.calculate_individual_similarities import CalculateIndividualSimilaritiesMixin

logger = logging.getLogger(__name__)

class GetSimilarityMatrixMixin(CalculateIndividualSimilaritiesMixin):
    def calculate_similarity(self, find: ObjectFind, model: A3DModel) -> float:
        """计算单个find和model之间的相似度"""
        # 确保测量数据已计算
        if not find.is_measured or not model.is_measured:
            logger.warning("测量数据未计算完整，无法计算相似度")
            return 0.0

        # 计算三个相似度指标
        area_sim = self.get_area_similarity(
            model.area,
            find.area_front,
            find.area_back
        )

        wl_sim = self.get_width_length_similarity(
            model.width, model.length,
            find.width_front, find.length_front,
            find.width_back, find.length_back
        )

        contour_sim = self.get_contour_similarity(
            model.contour,
            find.contour_front,
            find.contour_back
        )

        # 加权平均得到最终相似度
        return area_sim * 1.2 + wl_sim * 0.2 + contour_sim * 0.7



    def calculate_similarity_matrix(self,
                find_list: List[ObjectFind],
                a3dmodel_list: List[A3DModel],
    ) -> Dict[Tuple[int, str], float]:
        """
        Calculate similarity matrix between all finds and 3D models

        Args:
            find_list: List of measured ObjectFind instances
            a3dmodel_list: List of measured A3DModel instances
            similarity_calculator: Object with calculate_similarity method

        Returns:
            Dictionary with keys (find_repr, model_repr) and similarity scores
        """
        similarity_matrix = {}
        for find in find_list:
            for model in a3dmodel_list:
                score = self.calculate_similarity(find, model)
                similarity_matrix[(find.find_number, str(model))] = score

        return similarity_matrix

    def calculate_average(self):
        # 计算矩阵的平均值
        total_value = sum(self.similarity_matrix.values())
        count = len(self.similarity_matrix)
        return total_value / count if count > 0 else 0


