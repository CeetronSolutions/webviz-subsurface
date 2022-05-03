from webviz_config.webviz_plugin_subclasses._views import ViewABC

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class QCPlots(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel):
        super().__init__("QC plots")
        self.volumes_model = volumes_model
