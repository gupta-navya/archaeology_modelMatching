import logging
from typing import List
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
from model.models import A3DModel

logger = logging.getLogger(__name__)


class MeasureModelWorkerSignals(QObject):
    """Signals emitted by MeasureModelWorker"""
    progress = pyqtSignal(tuple)  # (message, progress_percentage, model_id)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    result = pyqtSignal(str)


class MeasureModelWorker(QRunnable):
    def __init__(
            self,
            a3dmodel_list: List[A3DModel],
            measurement_function
    ):
        super().__init__()
        self.a3dmodel_list = a3dmodel_list
        self.measurement_function = measurement_function
        self.signals = MeasureModelWorkerSignals()

    @pyqtSlot()
    def run(self):
        """Measures 3D models and updates their properties"""
        count = 0
        total = len(self.a3dmodel_list)

        for a3dmodel in self.a3dmodel_list:
            try:
                logger.debug(f"Measuring 3D model {a3dmodel}")
                # Perform actual measurement using the provided function
                measurement_result = self.measurement_function(a3dmodel)

                # Update model properties (assuming A3DModel has these attributes)
                a3dmodel.area = measurement_result["area"]
                a3dmodel.width = measurement_result["width"]
                a3dmodel.length = measurement_result["length"]
                a3dmodel.contour = measurement_result["contour"]
                #a3dmodel.is_measured = True

                count += 1
                progress_percent = int(count / total * 100)
                self.signals.progress.emit(
                    (f"Measured model {a3dmodel}", progress_percent, str(a3dmodel)))
            except Exception as e:
                logger.error(f"Failed to measure model {a3dmodel}: {e}")
                self.signals.error.emit(f"Failed to measure model {a3dmodel}")

        self.signals.finished.emit("Finished measuring 3D models")