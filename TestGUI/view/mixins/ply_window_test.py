import open3d as o3d
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent
import pathlib
import sys
import os

class PlyWindowMixin:

    def set_up_ply_window_validation(self):
        self.ply_visualizers = {}
        self.full_visualizers = {}
        self.model1.mousePressEvent = lambda e: self.on_ply_label_clicked(1)
        self.model2.mousePressEvent = lambda e: self.on_ply_label_clicked(2)
        self.model3.mousePressEvent = lambda e: self.on_ply_label_clicked(3)

    def set_up_ply_window_edit(self):
        self.ply_visualizers = {}
        self.full_visualizers = {}
        self.model1.mousePressEvent = lambda e: self.on_ply_label_clicked(1)
        self.model2.mousePressEvent = lambda e: self.on_ply_label_clicked(2)
        self.model3.mousePressEvent = lambda e: self.on_ply_label_clicked(3)
        self.model4.mousePressEvent = lambda e: self.on_ply_label_clicked(4)
        self.model5.mousePressEvent = lambda e: self.on_ply_label_clicked(5)
        self.model6.mousePressEvent = lambda e: self.on_ply_label_clicked(6)

    def display_model_screenshot(self, index: int, ply_path):
        """在指定位置显示点云截图"""
        if not ply_path or not ply_path.exists():
            print("there is no plypath")
            getattr(self, f"model{index}").clear()
            setattr(self, f"current_model_{index}", "")
            return
        # 创建或获取可视化器
        if index not in self.ply_visualizers:
            vis = o3d.visualization.Visualizer()
            vis.create_window(visible=False, width=800, height=600)
            vis.get_render_option().point_size = 5
            self.ply_visualizers[index] = vis

        vis = self.ply_visualizers[index]
        vis.clear_geometries()

        try:
            # 加载点云 - 确保使用字符串路径
            pcd = o3d.io.read_point_cloud(str(ply_path))
            if not pcd.has_points():
                print("Point cloud has no points")
                raise ValueError("Point cloud has no points")

            vis.add_geometry(pcd)

            # 设置视角
            ctr = vis.get_view_control()
            ctr.change_field_of_view(step=-9)
            ctr.set_zoom(0.8)

            # 捕获截图
            image = vis.capture_screen_float_buffer(do_render=True)
            image = np.asarray(image)
            image = (image * 255).astype(np.uint8)

            # 转换为QPixmap
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height,
                             bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # 显示在标签上
            label = getattr(self, f"model{index}")
            label.setPixmap(
                pixmap.scaled(label.width(), label.height(),
                              Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            print(f"This class is: {type(self).__name__}")
            print(f"model{index} --- {str(ply_path)}")

            # 保存当前模型路径
            #setattr(self, f"current_model_{index}", str(ply_path))

        except Exception as e:
            print(f"Error loading point cloud: {e}")
            getattr(self, f"model{index}").setText("Error loading model")
            setattr(self, f"current_model_{index}", "")

    def clear_model_screenshot(self, index: int):
        """清除指定位置的模型截图"""
        label = getattr(self, f"model{index}")
        label.clear()
        setattr(self, f"current_model_{index}", "")

        # 清理可视化器
        '''
        if index in self.ply_visualizers:
            try:
                self.ply_visualizers[index].destroy_window()
            except:
                pass  # 如果窗口已经关闭，忽略错误
            del self.ply_visualizers[index]
        '''

    def on_ply_label_clicked(self, index: int):
        """点击截图时加载完整Open3D窗口（使用Qt定时器）"""
        ply_path = getattr(self, f"current_model_{index}")
        if not ply_path:
            return

        # 如果窗口已存在，先关闭它
        if index in self.full_visualizers:
            try:
                self.full_visualizers[index].destroy_window()
            except:
                pass
            del self.full_visualizers[index]

        try:
            # 创建完整窗口
            vis = o3d.visualization.Visualizer()
            vis.create_window(window_name=f"3D Model {index}", width=1024, height=768)

            # 加载点云
            pcd = o3d.io.read_point_cloud(str(ply_path))
            vis.add_geometry(pcd)

            # 设置视角
            ctr = vis.get_view_control()
            ctr.change_field_of_view(step=-9)

            # 存储可视化器
            self.full_visualizers[index] = vis

            # 创建定时器来更新窗口
            timer = QTimer(self)
            timer.timeout.connect(lambda: self.update_full_window(index))
            timer.start(50)  # 20 FPS

            # 存储定时器引用
            vis.timer = timer

        except Exception as e:
            print(f"Error opening point cloud viewer: {e}")
            import traceback
            traceback.print_exc()

    def update_full_window(self, index: int):
        """更新完整Open3D窗口"""
        if index not in self.full_visualizers:
            return

        vis = self.full_visualizers[index]
        try:
            if not vis.poll_events():
                # 窗口已关闭
                vis.timer.stop()
                vis.destroy_window()
                del self.full_visualizers[index]
            else:
                vis.update_renderer()
        except Exception as e:
            print(f"Error updating Open3D window: {e}")
            try:
                vis.timer.stop()
                vis.destroy_window()
            except:
                pass
            if index in self.full_visualizers:
                del self.full_visualizers[index]