from webviz_config.webviz_plugin_subclasses._views import ViewABC

class FipFile(ViewABC):
    def __init__(self):
        super().__init__("Fipfile QC")
