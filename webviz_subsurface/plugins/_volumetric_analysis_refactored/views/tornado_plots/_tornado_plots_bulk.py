from webviz_config.webviz_plugin_subclasses._views import ViewABC

class TornadoPlotsBulk(ViewABC):
    def __init__(self) -> None:
        super().__init__("Bulk vs STOIIP/GIIP")
