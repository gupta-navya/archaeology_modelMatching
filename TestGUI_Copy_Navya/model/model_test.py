import logging
import pathlib
import random
from typing import List

import numpy as np
from PIL import Image
import psycopg2


class Validation_Model_Test:

    def __init__(self):
        self.path = pathlib.Path("TestGUI_Copy/assets")
        self.find_dir = self.list_finds(1,10)
        self.model_dir = self.list_models(1, 10)
        self.similarity_matrix = self.generate_similarity_matrix(0,2)
        self.find_model_dir = {}  # {find : model}
        self.model_find_dir = {}  # {model : find}
        self.is_validated = {}

    def init_validated(self):
        return {i: False for i in range(len(self.find_model_dir))}

    def get_find(self, index = 1):
        return (
            self.path / f"{index}" / "photos" / "1-3000.jpg",
            self.path / f"{index}" / "photos" / "2-3000.jpg"
        )
    def get_model(self, index = 1) -> pathlib.Path:
        return self.path / f"{index}" / "3d" / "gp" / "a_0_3_mesh.ply"

    def list_finds(self, min_find=1, max_find=10):
        return {i: self.get_find(i) for i in range(min_find, max_find + 1)}

    def list_models(self, min_find=1, max_find=10):
        return {i: self.get_model(i) for i in range(min_find, max_find + 1)}

    def generate_similarity_matrix(self, min, max):
        # 创建一个字典，键是 (find_index, model_index)，值是 [0, 2) 之间的随机数
        return {
            (find_index, model_index): random.uniform(min, max)
            for find_index in self.find_dir.keys()
            for model_index in self.model_dir.keys()
        }

    def get_similarity(self, find_index, model_index):
        # 根据给定的索引返回相似性值
        return self.similarity_matrix.get((find_index, model_index), None)

    def calculate_average(self):
        # 计算矩阵的平均值
        total_value = sum(self.similarity_matrix.values())
        count = len(self.similarity_matrix)
        return total_value / count if count > 0 else 0

    def set_match (self, find, model):
        self.find_model_dir[find] = model
        self.model_find_dir[model] = find

    def remove_match(self, find, model):
        # 从 find_model_dir 中移除匹配
        if find in self.find_model_dir:
            del self.find_model_dir[find]

        # 从 model_find_dir 中移除匹配
        if model in self.model_find_dir:
            del self.model_find_dir[model]


    def get_random_matches(self, num):
        available_finds  = [find_index  for find_index  in self.find_dir.keys()  if find_index  not in self.find_model_dir.keys()]
        available_models = [model_index for model_index in self.model_dir.keys() if model_index not in self.model_find_dir.keys()]
        for _ in range(num):
            # 如果没有可用的 finds 或 models，停止匹配
            if not available_finds or not available_models:break
            # 随机选择一个 find 和一个 model
            find = random.choice(available_finds)
            model = random.choice(available_models)
            # 存储匹配对
            self.set_match(find, model)
            # 从可用列表中移除已匹配的元素
            available_finds.remove(find)
            available_models.remove(model)

    def recommand_matches(self, num): #[(find, model, sim)]
        # 获取与给定 find_index 相关的相似性值
        matches = [(find, self.find_model_dir[find], self.get_similarity(find,self.find_model_dir[find]))for find in self.find_dir.keys()]

        if len(matches) > num:
            recommended_matches = sorted(matches, key=lambda item: item[2], reverse=True)[:num]
        else:
            recommended_matches = sorted(matches, key=lambda item: item[2], reverse=True)

        return recommended_matches

    def recommand_models(self, find_index, num): #[(model, sim)]
        # 获取与给定 find_index 相关的相似性值
        similarities = [
            (model_index,self.get_similarity(find_index, model_index))
            for model_index in self.model_dir.keys()
            #if model_index not in self. model_find_dir.keys()
        ]
        # 按相似性值排序，并选择前 num 个模型
        if len(similarities) > num:
            recommended_models = sorted(similarities, key=lambda item: item[1], reverse=True)[:num]
        else:
            recommended_models = sorted(similarities, key=lambda item: item[1], reverse=True)

        return recommended_models









