import sys
import open3d as o3d
import numpy as np

# 创建一个点云
import open3d as o3d

def display_ply(ply_path):
    # 读取 PLY 文件
    mesh = o3d.io.read_triangle_mesh(ply_path)

    # 检查是否成功读取
    if mesh.is_empty():
        print("Failed to load PLY file.")
        return

    # 创建可视化窗口
    o3d.visualization.draw_geometries([mesh], window_name="PLY Viewer")

# 示例用法
ply_path = "../TestGUI/assets_1/1/3d/gp/a_0_3_mesh.ply"  # 替换为你的 PLY 文件路径
display_ply(ply_path)