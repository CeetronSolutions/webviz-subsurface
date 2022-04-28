from typing import List
from webviz_config import WebvizConfigTheme
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class Settings(SettingsGroupABC):
    def __init__(
        self, volumes_model: InplaceVolumesModel, theme: WebvizConfigTheme
    ) -> None:
        super().__init__("Settings")
        self.volumes_model = volumes_model
        self.theme = theme

    def layout(self) -> List[Component]:
        theme_colors = self.theme.plotly_theme.get("layout", {}).get("colorway", [])
        return [
            self.remove_fluid_annotation(),
            self.subplot_xaxis_range(),
            self.histogram_options(),
            html.Span("Colors", style={"font-weight": "bold"}),
            wcc.ColorScales(
                id={"id": self.get_uuid().to_string(), "settings": "Colorscale"},
                colorscale=theme_colors,
                fixSwatches=True,
                nSwatches=12,
            ),
        ]

    def remove_fluid_annotation(
        self,
    ) -> html.Div:
        return html.Div(
            style={
                "margin-bottom": "10px",
                "display": "none"
                if self.volumes_model.volume_type == "dynamic"
                else "block",
            },
            children=wcc.Checklist(
                id={"id": self.get_uuid().to_string(), "selector": "Fluid annotation"},
                options=[{"label": "Show fluid annotation", "value": "Show"}],
                value=["Show"] if self.volumes_model.volume_type != "dynamic" else [],
            ),
        )

    def subplot_xaxis_range(self) -> html.Div:
        axis_matches_layout = []
        for axis in ["X axis", "Y axis"]:
            axis_matches_layout.append(
                html.Div(
                    children=wcc.Checklist(
                        id={
                            "id": self.get_uuid().to_string(),
                            "selector": f"{axis} matches",
                        },
                        options=[{"label": f"Equal {axis} range", "value": "Equal"}],
                        value=["Equal"],
                    )
                )
            )
        return html.Div(
            children=[
                html.Span("Subplot options:", style={"font-weight": "bold"}),
                html.Div(style={"margin-bottom": "10px"}, children=axis_matches_layout),
            ]
        )

    def histogram_options(self) -> html.Div:
        return html.Div(
            children=[
                wcc.RadioItems(
                    label="Barmode:",
                    id={"id": self.get_uuid().to_string(), "selector": "barmode"},
                    options=[
                        {"label": "overlay", "value": "overlay"},
                        {"label": "group", "value": "group"},
                        {"label": "stack", "value": "stack"},
                    ],
                    labelStyle={"display": "inline-flex", "margin-right": "5px"},
                    value="overlay",
                ),
                wcc.Slider(
                    label="Histogram bins:",
                    id={"id": self.get_uuid().to_string(), "selector": "hist_bins"},
                    value=15,
                    min=1,
                    max=30,
                ),
            ]
        )
