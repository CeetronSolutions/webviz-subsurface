from typing import Type, Union

from dash.development.base_component import Component  # type: ignore

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC


class MapViewElements:
    MAP_GRAPH = "map_graph"
    FORMATONS_GRAPH = "formations_graph"


class Map(ViewElementABC):
    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(flex_grow, screenshot_filename)

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(id=self.register_component_uuid(MapViewElements.MAP_GRAPH))


class FormationsGraph(ViewElementABC):
    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(flex_grow, screenshot_filename)

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(
            id=self.register_component_uuid(MapViewElements.FORMATONS_GRAPH)
        )


class RftMap(ViewABC):
    def __init__(self) -> None:
        super().__init__("RFT Map")

        row = self.add_row()
        row.add_view_element(Map(), "map")
