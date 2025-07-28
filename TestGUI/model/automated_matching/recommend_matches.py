import logging
from typing import List,Tuple

from TestGUI.model.automated_matching.matching_algorithm import global_optimal_matching, greedy_matching, reciprocal_best_matching
from TestGUI.model.workers.remove_ply_worker import RemovePlyWorker
from model.main_model import MainModel
from model.models import ObjectFind, A3DModel
from model.workers.fix_move_ply_worker import FixMovePlyWorker

logger = logging.getLogger(__name__)

class RecommandMatchMixin:

    def solve_matching(self: MainModel, algorithm: str):
        """解决匹配问题并应用结果"""
        # 1. 获取相似度矩阵
        similarity_matrix = self.similarity_matrix()

        # 2. 根据选择的算法计算匹配
        if algorithm == "global_optimal":
            matches = global_optimal_matching(similarity_matrix)
        elif algorithm == "greedy":
            matches = greedy_matching(similarity_matrix)
        elif algorithm == "reciprocal":
            matches = reciprocal_best_matching(similarity_matrix)
        else:
            logger.error(f"未知算法: {algorithm}")
            return

        return matches

        ## 3. 应用匹配结果
        #apply_matches(self.main_model, matches)

        # 4. 更新UI
        #self.populate_finds()
        #self.populate_unsorted_models()

        # 5. 显示成功消息
        #self.main_view.display_info(f"应用 {algorithm} 匹配算法完成，共匹配 {len(matches)} 对")

    def unmatch_random_find(self, find:ObjectFind):
        if find is None:
            logger.debug("No find with number %s", find.find_number)
            return False
        old_match: A3DModel = self.a3dmodels_dict[find.get_match_str()]
        if old_match is None:
            logger.debug("No 3d model with %s", find.get_match_str())
            return False
        find.clear_match(self.conn)
        old_match.matched_finds = old_match.get_matches(self.conn.cursor())
        return True

    def match_random_find_with_random_a3dmodel(self, find:ObjectFind, a3dmodel:A3DModel):
        if find is None or a3dmodel is None:
            logger.error("No find or model selected")
            return False
        if find.is_matched:
            logger.error("Attempted to set a match for a find that already has one")
            logger.error("call clear_match_for_find first")
            return False
        find.set_match(
            self.conn,
            a3dmodel.batch_year,
            a3dmodel.batch_number,
            a3dmodel.batch_piece,
        )
        a3dmodel.matched_finds = a3dmodel.get_matches(self.conn.cursor())
        return True

    def clear_all_finds(self: MainModel):
        main_model = self
        for find in main_model.finds_dict.values():
            if find.is_matched:
                main_model.clear_match_for_find(find.find_number)

    def apply_match(self, find_number: int, model_str: str) -> FixMovePlyWorker:
        """应用单个匹配（数据库更新 + 文件拷贝）

        返回:
            FixMovePlyWorker: 文件拷贝工作线程
        """
        find:ObjectFind = self.finds_dict.get(find_number)
        model:A3DModel = self.a3dmodels_dict.get(model_str)
        if not find or not model:
            logger.error(f"无效的匹配: find={find_number}, model={model_str}")
            return None


        # 1. 在类中set_match()
        success = self.match_random_find_with_random_a3dmodel(find,model)
        if not success:
            logger.error(f"无法更新数据库: find={find_number}, model={model_str}")
            return None

        # 2. 创建目标文件夹
        models_dir = find.models_directory()
        models_dir.mkdir(parents=True, exist_ok=True)

        # 3. 准备文件拷贝任务
        mesh_path = model.get_file("mesh")
        orig_path = model.get_file("full")
        original_destination = models_dir / "a.ply"
        mesh_destination = models_dir / "a_0_3_mesh.ply"
        pairs = [(orig_path, original_destination), (mesh_path, mesh_destination)]

        # 4. 创建并返回文件拷贝工作线程
        return FixMovePlyWorker(pairs, model_str, find_number)

    def apply_unmatch(self, find_number: int) -> RemovePlyWorker:
        """取消单个匹配（数据库更新 + 文件删除）

        返回:
            RemovePlyWorker: 文件删除工作线程
        """
        find = self.finds_dict.get(find_number)
        if not find:
            logger.error(f"找不到find: {find_number}")
            return None

        success = self.unmatch_random_find(find)
        if not success:
            logger.error(f"无法清除数据库匹配: find={find_number}")
            return None

        # 3. 创建文件删除工作线程
        return RemovePlyWorker(find.models_directory(), find_number)


    def recommend_models(self, find_number: int, num: int = 10) -> List[Tuple[str, float]]:
        """
        为指定find推荐相似度最高的模型

        参数:
            find_number: find编号
            num: 推荐模型数量

        返回:
            模型列表[(model_str, similarity_score)]
        """
        find = self.finds_dict.get(find_number)
        if not find or not find.is_measured:
            logger.warning(f"无法推荐模型: find {find_number} 未测量或不存在")
            return []

        # 计算所有模型的相似度
        model_scores = []
        for model in self.a3dmodels_list:
            if not model.is_measured:
                continue

            # 计算相似度
            score = self.calculate_similarity(find, model)
            model_scores.append((str(model), score))

        # 按相似度降序排序
        model_scores.sort(key=lambda x: x[1], reverse=True)

        # 排除已匹配但未验证的模型
        recommended = []
        for model_str, score in model_scores:
            model = self.a3dmodels_dict.get(model_str)
            if not model:
                continue

            # 检查模型是否已被匹配但未验证
            if model.is_matched:
                matched_find = next((f for f in model.matched_finds), None)
                if matched_find and not self.finds_dict[matched_find].is_validated:
                    continue

            recommended.append((model_str, score))
            if len(recommended) >= num:
                break

        return recommended
