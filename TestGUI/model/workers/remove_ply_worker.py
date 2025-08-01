from pathlib import Path
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
import logging
logger = logging.getLogger(__name__)

class RemovePlyWorkerSignals(QObject):
    """文件删除工作线程信号"""
    progress = pyqtSignal(tuple)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)


class RemovePlyWorker(QRunnable):
    def __init__(self, directory: Path, find_number: int):
        super().__init__()
        self.directory = directory
        self.find_number = find_number
        self.signals = RemovePlyWorkerSignals()

    @pyqtSlot()
    def run(self):
        """删除指定目录下的所有PLY文件"""
        try:
            # 检查目录是否存在
            if not self.directory.exists() or not self.directory.is_dir():
                self.signals.error.emit(f"目录不存在: {self.directory}")
                return

            # 获取所有PLY文件
            ply_files = list(self.directory.glob("*.ply"))
            total = len(ply_files)

            if total == 0:
                self.signals.finished.emit(f"没有文件需要删除: {self.directory}")
                return

            # 删除文件
            for i, file_path in enumerate(ply_files):
                msg = f"删除文件: {file_path.name}"
                self.signals.progress.emit((msg, int((i + 1) / total * 100)))
                try:
                    file_path.unlink()  # 删除文件
                except Exception as e:
                    logger.error(f"删除文件失败: {file_path}: {e}")
                    self.signals.error.emit(f"删除失败: {file_path.name}")

            # 尝试删除空目录
            try:
                if not any(self.directory.iterdir()):
                    self.directory.rmdir()
                    self.signals.progress.emit(("删除空目录", 100))
            except Exception as e:
                logger.warning(f"无法删除目录: {self.directory}: {e}")

            self.signals.finished.emit(
                f"已删除 {total} 个文件: find {self.find_number}"
            )
        except Exception as e:
            logger.error(f"文件删除任务失败: {e}")
            self.signals.error.emit(f"文件删除失败: {e}")