from typing import List
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import html
import webviz_core_components as wcc


class Settings(SettingsGroupABC):
    def __init__(self) -> None:
        super().__init__("Settings")

    def layout(self) -> List[Component]:
        return [
            self.colorby_selector(),
            self.axis_focus_selector(),
            self.remove_zero_responses(),
            self.remove_non_highlighted_data(),
        ]

    def colorby_selector(self) -> html.Div:
        return html.Div(
            style={"margin": "10px 0px"},
            children=wcc.RadioItems(
                label="Color plots on",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Color by",
                },
                options=[
                    {"label": "Highlighted", "value": "highlighted"},
                    {"label": "1st level of investigation", "value": "groups"},
                ],
                labelStyle={"display": "inline-flex", "margin-right": "5px"},
                value="highlighted",
            ),
        )

    def axis_focus_selector(self) -> html.Div:
        return wcc.Checklist(
            id={
                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                "settings_id": self.get_unique_id().to_string(),
                "selector": "Axis focus",
            },
            options=[{"label": "Focus diff plots on highlighted", "value": "focus"}],
            value=["focus"],
        )

    def remove_zero_responses(self) -> html.Div:
        return wcc.Checklist(
            id={
                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                "settings_id": self.get_unique_id().to_string(),
                "selector": "Remove zeros",
            },
            options=[{"label": "Remove data with no volume", "value": "remove"}],
            value=["remove"],
        )

    def remove_non_highlighted_data(self) -> html.Div:
        return wcc.Checklist(
            id={
                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                "settings_id": self.get_unique_id().to_string(),
                "selector": "Remove non-highlighted",
            },
            options=[
                {"label": "Display only highlighted data in table", "value": "remove"}
            ],
            value=[],
        )
