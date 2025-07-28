from TestGUI.model.workers.measure_model_worker import MeasureModelWorker


class LoadAll3DModelMixin:
    def load_a3dmodels_automated(self) -> MeasureModelWorker:
        """加载3D模型并返回测量工作线程"""
        self.a3dmodels_dict = {str(m): m for m in self.selected_context.list_models()}
        self.selected_a3dmodel_str = (
            list(self.a3dmodels_dict.keys())[0] if self.a3dmodels_dict else None
        )

        # 创建并返回测量工作线程
        worker = MeasureModelWorker(
            a3dmodel_list=self.a3dmodels_list,
            measurement_function=self.measure_a3dmodel
        )
        return worker

    def measure_a3dmodel(self, a3dmodel: A3DModel):
        """测量单个3D模型的方法"""
        # 使用现有的测量方法
        return a3dmodel.measure(self.ply_window, self.measure_cache)