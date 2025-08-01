from TestGUI.model.workers.remove_ply_worker import RemovePlyWorker
from model.main_model import MainModel
from model.models import ObjectFind, A3DModel
from model.workers.fix_move_ply_worker import FixMovePlyWorker
import logging
logger = logging.getLogger(__name__)

class ApplyMatchMixin:

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

        logger.info(f"Successfully match {find} with {a3dmodel} in database")
        return True

    def unmatch_random_find(self, find: ObjectFind):
        if find is None:
            logger.debug("No find with number %s", find.find_number)
            return False
        old_match: A3DModel = self.a3dmodels_dict[find.get_match_str()]
        if old_match is None:
            logger.debug("No 3d model with %s", find.get_match_str())
            return False

        find.clear_match(self.conn)
        old_match.matched_finds = old_match.get_matches(self.conn.cursor())

        logger.info(f"Successfully unmatch {find} with {old_match} in database")
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
            logger.error(f"Invalid Match: find={find_number}, model={model_str}")
            return None


        # 1. 在类中set_match() -> 数据库操作
        success = self.match_random_find_with_random_a3dmodel(find,model)
        if not success:
            logger.error(f"Can not get to database: find={find_number}, model={model_str}")
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

    '''
    def apply_matches(self, matches: List[Tuple[int, str, float]]):
        """应用匹配结果"""
        # 1. 显示应用匹配状态
        if self.loading_window:
            self.loading_window.status_label_1.setText("应用自动匹配...")
            self.loading_window.progress_bar_1.setMaximum(len(matches))
            self.loading_window.progress_bar_1.setValue(0)

        # 2. 先取消所有现有匹配
        self.unmatch_all_finds()

        # 3. 应用新匹配
        self.total_match_tasks = len(matches)
        self.completed_match_tasks = 0
        self.match_workers = []

        # 创建所有匹配任务
        for find_number, model_str, similarity in matches:
            # 创建数据库更新和文件拷贝任务
            worker = self.main_model.apply_match(find_number, model_str)
            if worker:
                worker.signals.progress.connect(self.on_file_task_progress)
                worker.signals.finished.connect(self.on_match_task_finished)
                worker.signals.error.connect(self.on_file_task_error)
                self.match_workers.append(worker)

                # 更新相似度分数
                find = self.main_model.finds_dict.get(find_number)
                if find:
                    find.similarity_score = similarity

        # 4. 启动所有匹配任务
        if self.match_workers:
            for worker in self.match_workers:
                self.threadpool.start(worker)
        else:
            self.on_all_match_tasks_finished()
    '''