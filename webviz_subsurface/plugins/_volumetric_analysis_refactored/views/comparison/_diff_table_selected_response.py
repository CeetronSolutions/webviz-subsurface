from webviz_config.webviz_plugin_subclasses._views import ViewABC

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class DiffTableSelectedResponse(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel):
        super().__init__("Difference table for selected response")
        self.volumes_model = volumes_model
