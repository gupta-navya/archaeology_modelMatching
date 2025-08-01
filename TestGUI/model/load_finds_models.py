class LoadMissingFind3DModelMixin:

    def load_finds_automated(self, color_grid: str):

        self.finds_dict = {
            f.find_number: f
            for f in self.selected_context.list_finds(self.conn.cursor())
        }
        self.selected_find_number = (
            list(self.finds_dict.keys())[0] if self.finds_dict else None
        )

    def load_a3dmodels_automated(self):

        self.a3dmodels_dict = {str(m): m for m in self.selected_context.list_models()}
        self.selected_a3dmodel_str = (
            list(self.a3dmodels_dict.keys())[0] if self.a3dmodels_dict else None
        )





