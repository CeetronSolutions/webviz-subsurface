from typing import List
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class TornadoControls(SettingsGroupABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Tornado controls")
        self.volumes_model = volumes_model
        self.sens_columns = ["REAL", "SENSNAME", "SENSCASE", "SENSTYPE", "SENSNAME_CASE"]

    def layout(self) -> List[Component]:
        return [wcc.Dropdown(
            label="Response",
            id={"id": self.get_uuid().to_string(), "selector": "Response"},
            clearable=False,
            options=[{"label": i, "value": i} for i in self.volumes_model.responses],
            value=self.volumes_model.responses[0],
        ),
        wcc.SelectWithLabel(
            label="Sensitivity filter",
            collapsible=True,
            open_details=False,
            id={"id": self.get_uuid().to_string(), "selector": "Sensitivities"},
            options=[{"label": i, "value": i} for i in self.volumes_model.sensitivities],
            value=self.volumes_model.sensitivities,
            size=min(15, len(self.volumes_model.sensitivities)),
        ),
        wcc.Dropdown(
            label="Subplots",
            id={"id": self.get_uuid().to_string(), "selector": "Subplots"},
            clearable=True,
            options=[
                {"label": i, "value": i}
                for i in [
                    x
                    for x in self.volumes_model.selectors
                    if x not in self.sens_columns and self.volumes_model.dataframe[x].nunique() > 1
                ]
            ],
        ),
        html.Div(
            style={"margin-top": "10px"},
            children=wcc.RadioItems(
                label="Visualization below tornado:",
                id={"id": self.get_uuid().to_string(), "selector": "bottom_viz"},
                options=[
                    {"label": "Table", "value": "table"},
                    {"label": "Realization plot", "value": "realplot"},
                    {"label": "None", "value": "none"},
                ],
                vertical=False,
                value="table",
            ),
        ),]
