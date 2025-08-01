
from typing import List,Tuple

from TestGUI.model.recommend_matches_and_models.matching_algorithm import global_optimal_matching, greedy_matching, reciprocal_best_matching
from model.main_model import MainModel
from model.models import ObjectFind, A3DModel


import logging
logger = logging.getLogger(__name__)

class RecommandMatchMixin:

    def solve_matching(self: MainModel, algorithm: str, model_filter_flag: str):
        """解决匹配问题并应用结果"""
        # 1. 获取相似度矩阵
        similarity_matrix = self.similarity_matrix()

        # 2. 根据选择的算法计算匹配
        if algorithm == "global_optimal":
            matches : List[Tuple[int, str, float]] = global_optimal_matching(similarity_matrix)
        elif algorithm == "greedy":
            matches : List[Tuple[int, str, float]]= greedy_matching(similarity_matrix)
        elif algorithm == "reciprocal":
            matches : List[Tuple[int, str, float]]= reciprocal_best_matching(similarity_matrix)
        else:
            logger.error(f"未知算法: {algorithm}")
            return

        logger.info(f"Solve the matches based on {algorithm}")

        if model_filter_flag == "all":
            return matches
        elif model_filter_flag == "unmatched":
            for match in matches:
                find_number, a3dmodel_str, _ = match
                find: ObjectFind = self.finds_dict[find_number]
                model: a3dmodel_str = self.a3dmodels_dict[a3dmodel_str]
                if find.is_matched or model.is_matched:
                    matches.remove(match)
            return matches

    def get_match_status(self, match) -> int:
        find_num, model_str, _ = match
        object_find: ObjectFind = self.finds_dict[find_num]
        a3dmodel: A3DModel = self.a3dmodels_dict[model_str]

        # status 1 : 两个都没有
        if (not object_find.is_matched) and (not a3dmodel.is_matched):
            return 1 #yellow
        elif (not object_find.is_matched) and a3dmodel.is_matched:
            return 2 #
        elif object_find.is_matched and (not a3dmodel.is_matched):
            return 3
        elif object_find.get_match_str == str(a3dmodel):
            return 4
        else:
            return 5

    def get_match_status_dict(self, matches):
        return {match : self.get_match_status(match) for match in matches}



    def recommend_models(self: MainModel, find_number: int, model_filter_flag, num: int = 10) -> list[
        tuple[int, float]]:

        model_score_list = []
        for a3dmodel in self.a3dmodels_list:
            model_str = str(a3dmodel)
            similarity_score:float = self.similarity_matrix[(find_number,model_str)]
            model_score_list.append((model_str, similarity_score))
        # 按相似度降序排序
        model_score_list.sort(key=lambda x: x[1], reverse=True)

        if model_filter_flag == "all":
            if len(model_score_list) > num:
                return model_score_list[:num]
            else:
                return model_score_list
        else: #model_filter_flag == "unmatched":
            for model_score_match in model_score_list:
                model_str, score = model_score_match
                a3dmodel = self.a3dmodels_dict.get(model_str)
                if a3dmodel.ismatched:
                    matched_find = next((f for f in a3dmodel.matched_finds), None)
                    if matched_find == find_number:
                        pass
                    else:
                        model_score_list.remove(model_score_match)
            if len(model_score_list) > num:
                return model_score_list[:num]
            else:
                return model_score_list


    def get_model_status(self:MainModel, find_number, model_str, matches):

        a3dmodel = self.a3dmodels_dict[model_str]
        recommend_find_model_set = {(match[0], match[1]) for match in matches}
        recommend_model_set = {match[1] for match in matches}

        if a3dmodel.is_matched:
            matched_find = next((f for f in a3dmodel.matched_finds), None)
            if matched_find == find_number:
                return 5
            else:
                return 4

        elif model_str in recommend_model_set:
            if (find_number, model_str) in recommend_find_model_set:
                return 1
            else:
                return 3
        else:
            return 2

    def get_model_status_dict(self, find_number, model_score_list, matches):
        return {model_str : self.get_model_status(find_number, model_str, matches) for model_str,_ in model_score_list}












    #def cache_matching_info_single(self, find_number):
        #{find: model, sim}
        #pass

    #def cache_matching_info(self):
        #for match in matches:
            #self.cache_matching_info(match)






