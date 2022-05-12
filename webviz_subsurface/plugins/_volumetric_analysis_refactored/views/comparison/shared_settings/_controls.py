from typing import List
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import html, dcc
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class Controls(SettingsGroupABC):
    def __init__(self, compare_on: str, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Controls")
        self.volumes_model = volumes_model
        self.compare_on = compare_on

    def layout(self) -> List[Component]:
        options = self.comparison_options()
        return [
            wcc.Dropdown(
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "value1",
                },
                label=f"{self.compare_on} A",
                optionHeight=50,
                options=options,
                value=options[0]["value"],
                clearable=False,
            ),
            wcc.Dropdown(
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "value2",
                },
                optionHeight=50,
                label=f"{self.compare_on} B",
                options=options,
                value=options[-1]["value"],
                clearable=False,
            ),
            dcc.Input(
                style={"display": "none"},
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "compare_on",
                },
                value=self.compare_on,
            ),
            html.Div(
                f"Difference = {self.compare_on} B - {self.compare_on} A",
                style={
                    "font-size": "15px",
                    "margin-top": "5px",
                    "color": "#007079",
                },
            ),
            self.response_selector(),
            self.group_by_selector(),
            self.diff_mode_selector(),
            self.highlight_controls(),
        ]

    def diff_mode_selector(self) -> html.Div:
        return html.Div(
            style={"margin-top": "10px"},
            children=wcc.RadioItems(
                label="Difference mode",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Diff mode",
                },
                options=[
                    {"label": "Percent", "value": "diff (%)"},
                    {"label": "True value", "value": "diff"},
                ],
                labelStyle={"display": "inline-flex", "margin-right": "5px"},
                value="diff (%)",
            ),
        )

    def highlight_controls(self) -> html.Div:
        return html.Div(
            style={"margin-top": "10px"},
            children=[
                html.Label(
                    "Data highlight criterias", className="webviz-underlined-label"
                ),
                html.Div(
                    children=[
                        wcc.Label("Absolute diff (%) above:"),
                        dcc.Input(
                            id={
                                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                                "settings_id": self.get_unique_id().to_string(),
                                "selector": "Accept value",
                            },
                            type="number",
                            required=True,
                            value=5,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        wcc.Label("Ignore response values below:"),
                        dcc.Input(
                            id={
                                "plugin_id": self.get_unique_id().get_plugin_uuid(),
                                "settings_id": self.get_unique_id().to_string(),
                                "selector": "Ignore <",
                            },
                            type="number",
                            required=True,
                            value=0,
                            persistence=True,
                            persistence_type="session",
                            debounce=True,
                        ),
                    ]
                ),
            ],
        )

    def comparison_options(self) -> list:
        if (
            self.compare_on == "Ensemble"
            and "SENSNAME_CASE" in self.volumes_model.selectors
        ):
            elements = []
            for ens in self.volumes_model.ensembles:
                for sens in self.volumes_model.ensemble_sensitivities[ens]:
                    elements.append("|".join([ens, sens]))
            return [{"label": i.replace("|", ":  "), "value": i} for i in elements]

        if self.compare_on == "Source":
            elements = self.volumes_model.sources
        elif self.compare_on == "Ensemble":
            elements = self.volumes_model.ensembles
        elif self.compare_on == "Sensitivity":
            elements = list(self.volumes_model.ensemble_sensitivities.values())[0]
        return [{"label": i, "value": i} for i in elements]

    def response_selector(
        self,
    ) -> html.Div:
        return html.Div(
            style={"margin-top": "10px"},
            children=wcc.Dropdown(
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Response",
                },
                label="Response",
                options=[
                    {"label": i, "value": i} for i in self.volumes_model.responses
                ],
                value=self.volumes_model.volume_columns[0],
                clearable=False,
            ),
        )

    def group_by_selector(self) -> html.Div:
        available_selectors = [
            x
            for x in self.volumes_model.region_selectors
            + ["FACIES", "REAL", "FLUID_ZONE"]
            if x in self.volumes_model.selectors
            and self.volumes_model.dataframe[x].nunique() > 1
        ]
        return html.Div(
            style={"margin-top": "10px"},
            children=wcc.Dropdown(
                label="Investigate differences on level",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Group by",
                },
                options=[{"label": elm, "value": elm} for elm in available_selectors],
                value=[],
                placeholder="Total",
                multi=True,
                clearable=False,
            ),
        )
