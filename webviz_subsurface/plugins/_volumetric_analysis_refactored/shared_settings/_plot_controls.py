from typing import List, Optional, Type
from xml.dom.minidom import Element
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import ALL, Input, Output, State, callback, html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from .._layout_elements import ElementIds


class PlotControls(SettingsGroupABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Plot controls")
        self.volumes_model = volumes_model
        self.selectors = ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]

    def layout(self) -> List[Component]:
        return self.plot_selector_dropdowns()

    def plot_selector_dropdowns(self) -> List[html.Div]:
        """Makes dropdowns for each selector"""

        dropdowns: List[html.Div] = []
        value: Optional[str] = None

        for selector in [
            "Plot type",
            "X Response",
            "Y Response",
            "Subplots",
            "Color by",
        ]:
            if selector == "Plot type":
                elements = ["histogram", "scatter", "distribution", "box", "bar"]
                value = elements[0]
            if selector == "X Response":
                elements = self.volumes_model.responses
                value = elements[0]
            if selector == "Y Response":
                elements = self.volumes_model.responses
                value = None
            if selector == "Subplots":
                elements = [x for x in self.volumes_model.selectors if x != "REAL"]
                value = None
            if selector == "Color by":
                elements = [x for x in self.volumes_model.selectors if x != "REAL"]
                value = "ENSEMBLE"

            dropdowns.append(
                wcc.Dropdown(
                    label=selector,
                    id={"id": self.get_uuid().to_string(), "selector": selector},
                    options=[{"label": elm, "value": elm} for elm in elements],
                    value=value,
                    clearable=selector in ["Subplots", "Color by", "Y Response"],
                    disabled=selector == "Y Response",
                )
            )
        return dropdowns
