import logging
import pathlib
import random
from typing import List

import numpy as np
from PIL import Image
import psycopg2


class ValidateMatchMixin:



    def recommand_models(self, find_index, num):  # [(model, sim)]
        # 获取与给定 find_index 相关的相似性值
        similarities = [
            (model_index, self.get_similarity(find_index, model_index))
            for model_index in self.model_dir.keys()
            # if model_index not in self. model_find_dir.keys()
        ]
        # 按相似性值排序，并选择前 num 个模型
        if len(similarities) > num:
            recommended_models = sorted(similarities, key=lambda item: item[1], reverse=True)[:num]
        else:
            recommended_models = sorted(similarities, key=lambda item: item[1], reverse=True)

        return recommended_models






