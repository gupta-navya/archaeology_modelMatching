import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict
from typing import List, Tuple, Dict


def global_optimal_matching(similarity_matrix: Dict[Tuple[int, str], float]) -> List[Tuple[int, str, float]]:
    """
    全局最优匹配算法（匈牙利算法）

    参数:
        similarity_matrix: 相似度矩阵，键为(find_number, model_str)，值为相似度分数

    返回:
        匹配列表[(find_number, model_str, similarity)]
    """
    # 提取唯一的find和model
    finds = sorted(set(f for f, _ in similarity_matrix.keys()))
    models = sorted(set(m for _, m in similarity_matrix.keys()))

    # 创建成本矩阵（行：finds，列：models）
    n = len(finds)
    m = len(models)
    max_dim = max(n, m)
    cost_matrix = np.zeros((max_dim, max_dim))

    # 填充成本矩阵（使用负相似度，因为匈牙利算法解决最小化问题）
    find_idx = {f: i for i, f in enumerate(finds)}
    model_idx = {m: i for i, m in enumerate(models)}

    for (find, model), sim in similarity_matrix.items():
        if find in find_idx and model in model_idx:
            i = find_idx[find]
            j = model_idx[model]
            cost_matrix[i, j] = -sim  # 使用负相似度

    # 使用匈牙利算法求解
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # 收集匹配结果
    matches = []
    for i, j in zip(row_ind, col_ind):
        if i < n and j < m:
            find = finds[i]
            model = models[j]
            sim = -cost_matrix[i, j]  # 恢复正相似度
            if sim > 0:  # 只保留有效匹配
                matches.append((find, model, sim))

    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


def greedy_matching(similarity_matrix: Dict[Tuple[int, str], float]) -> List[Tuple[int, str, float]]:
    """
    贪心匹配算法

    参数:
        similarity_matrix: 相似度矩阵，键为(find_number, model_str)，值为相似度分数

    返回:
        匹配列表[(find_number, model_str, similarity)]
    """
    # 按相似度降序排序所有可能的匹配
    all_pairs = sorted(
        [(f, m, s) for (f, m), s in similarity_matrix.items()],
        key=lambda x: x[2],
        reverse=True
    )

    matched_finds = set()
    matched_models = set()
    matches = []

    # 从最高相似度开始匹配
    for find, model, sim in all_pairs:
        if find not in matched_finds and model not in matched_models:
            matches.append((find, model, sim))
            matched_finds.add(find)
            matched_models.add(model)

    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


def reciprocal_best_matching(similarity_matrix: Dict[Tuple[int, str], float]) -> List[Tuple[int, str, float]]:
    """
    双向最优匹配算法（Reciprocal Best Matching）

    参数:
        similarity_matrix: 相似度矩阵，键为(find_number, model_str)，值为相似度分数

    返回:
        匹配列表[(find_number, model_str, similarity)]
    """
    # 构建find->model和model->find的最佳匹配映射
    find_best_model = {}
    model_best_find = {}

    # 每个find找到最佳model
    find_to_models = defaultdict(list)
    for (f, m), s in similarity_matrix.items():
        find_to_models[f].append((m, s))

    for find, models in find_to_models.items():
        # 按相似度降序排序
        models.sort(key=lambda x: x[1], reverse=True)
        if models:
            best_model, best_sim = models[0]
            find_best_model[find] = (best_model, best_sim)

    # 每个model找到最佳find
    model_to_finds = defaultdict(list)
    for (f, m), s in similarity_matrix.items():
        model_to_finds[m].append((f, s))

    for model, finds in model_to_finds.items():
        # 按相似度降序排序
        finds.sort(key=lambda x: x[1], reverse=True)
        if finds:
            best_find, best_sim = finds[0]
            model_best_find[model] = (best_find, best_sim)

    # 找出双向最优匹配
    matches = []
    matched_finds = set()
    matched_models = set()

    for find, (model, sim) in find_best_model.items():
        if find in matched_finds or model in matched_models:
            continue

        # 检查是否双向最优
        if model in model_best_find:
            best_find_for_model, _ = model_best_find[model]
            if best_find_for_model == find:
                matches.append((find, model, sim))
                matched_finds.add(find)
                matched_models.add(model)

    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches