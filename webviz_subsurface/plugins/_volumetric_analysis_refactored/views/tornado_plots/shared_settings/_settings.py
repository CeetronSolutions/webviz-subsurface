from typing import List

from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class Settings(SettingsGroupABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Settings")
        self.volumes_model = volumes_model

    def layout(self) -> List[Component]:
        return [
            self.scale_selector(),
            self.checkboxes_settings(),
            self.labels_display(),
            self.reference_selector(),
        ]

    def scale_selector(self) -> wcc.Dropdown:
        return wcc.Dropdown(
            label="Scale:",
            id={
                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                "settings_id": self.get_unique_id().to_string(),
                "selector": "Scale",
            },
            options=[
                {"label": "Relative value (%)", "value": "Percentage"},
                {"label": "Relative value", "value": "Absolute"},
                {"label": "True value", "value": "True"},
            ],
            value="Percentage",
            clearable=False,
        )

    def checkboxes_settings(self) -> html.Div:
        return html.Div(
            style={"margin-top": "10px", "margin-bottom": "10px"},
            children=[
                wcc.Checklist(
                    id={
                        "plugin_id": self.get_unique_id().get_plugin_uuid(),
                        "settings_id": self.get_unique_id().to_string(),
                        "selector": selector,
                    },
                    options=[{"label": label, "value": "selected"}],
                    value=["selected"] if selected else [],
                )
                for label, selector, selected in [
                    ("Color by sensitivity", "color_by_sens", True),
                    ("Shared subplot X axis", "Shared axis", False),
                    ("Show realization points", "real_scatter", False),
                    ("Show reference on tornado", "torn_ref", True),
                    ("Remove sensitivities with no impact", "Remove no impact", True),
                ]
            ],
        )

    def labels_display(self) -> html.Div:
        return html.Div(
            style={"margin-bottom": "10px"},
            children=[
                wcc.RadioItems(
                    label="Label options:",
                    id={
                        "plugin_id": self.get_unique_id().get_plugin_uuid(),
                        "settings_id": self.get_unique_id().to_string(),
                        "selector": "labeloptions",
                    },
                    options=[
                        {"label": "detailed", "value": "detailed"},
                        {"label": "simple", "value": "simple"},
                        {"label": "hide", "value": "hide"},
                    ],
                    vertical=False,
                    value="simple",
                ),
            ],
        )

    def reference_selector(self) -> wcc.Dropdown:
        return wcc.Dropdown(
            label="Reference:",
            id={
                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                "settings_id": self.get_unique_id().to_string(),
                "selector": "Reference",
            },
            options=[
                {"label": elm, "value": elm} for elm in self.volumes_model.sensitivities
            ],
            value="rms_seed"
            if "rms_seed" in self.volumes_model.sensitivities
            else self.volumes_model.sensitivities[0],
            clearable=False,
        )
