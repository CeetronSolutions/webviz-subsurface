from typing import List, Optional, Type
from xml.dom.minidom import Element
from webviz_config.webviz_plugin_subclasses import (
    ViewABC,
    ViewElementABC,
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import Input, Output, State, callback, html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ..._layout_elements import ElementIds


class StockOilTankPlot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return html.Div(
            children=[
                html.Div(
                    id=self.register_component_uuid("custom-plotting"),
                    style={"display": "block"},
                ),
                html.Div(
                    id=self.register_component_uuid("plots-per-zone"),
                    style={"display": "none"},
                ),
                html.Div(
                    id=self.register_component_uuid("convergence-plot"),
                    style={"display": "none"},
                ),
            ]
        )

    def set_callbacks(self) -> None:
        return None


class InplaceDistributionsPlotsPerZoneRegion(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        selectors = "/".join(
            [
                x.lower()
                for x in ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]
                if x in volumes_model.selectors
            ]
        )
        super().__init__(f"Plots per {selectors}")

        self.add_view_element(StockOilTankPlot(), "StockOilTankPlot")
