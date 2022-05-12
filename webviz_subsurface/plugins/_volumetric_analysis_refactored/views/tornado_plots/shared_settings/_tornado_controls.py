from typing import Any, List, Optional
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC, LayoutUniqueId
from dash.development.base_component import Component

from dash import html, ALL, Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ...._layout_elements import ElementIds
from ..utils import update_relevant_components


class TornadoControls(SettingsGroupABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Tornado controls")
        self.volumes_model = volumes_model
        self.sens_columns = [
            "REAL",
            "SENSNAME",
            "SENSCASE",
            "SENSTYPE",
            "SENSNAME_CASE",
        ]

    def layout(self) -> List[Component]:
        return [
            wcc.Dropdown(
                label="Response",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Response",
                },
                clearable=False,
                options=[
                    {"label": i, "value": i} for i in self.volumes_model.responses
                ],
                value=self.volumes_model.responses[0],
            ),
            wcc.SelectWithLabel(
                label="Sensitivity filter",
                collapsible=True,
                open_details=False,
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Sensitivities",
                },
                options=[
                    {"label": i, "value": i} for i in self.volumes_model.sensitivities
                ],
                value=self.volumes_model.sensitivities,
                size=min(15, len(self.volumes_model.sensitivities)),
            ),
            wcc.Dropdown(
                label="Subplots",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Subplots",
                },
                clearable=True,
                options=[
                    {"label": i, "value": i}
                    for i in [
                        x
                        for x in self.volumes_model.selectors
                        if x not in self.sens_columns
                        and self.volumes_model.dataframe[x].nunique() > 1
                    ]
                ],
            ),
            html.Div(
                style={"margin-top": "10px"},
                children=wcc.RadioItems(
                    label="Visualization below tornado:",
                    id={
                        "plugin_id": self.get_unique_id().get_plugin_uuid(),
                        "settings_id": self.get_unique_id().to_string(),
                        "selector": "bottom_viz",
                    },
                    options=[
                        {"label": "Table", "value": "table"},
                        {"label": "Realization plot", "value": "realplot"},
                        {"label": "None", "value": "none"},
                    ],
                    vertical=False,
                    value="table",
                ),
            ),
        ]

    def set_callbacks(self) -> None:
        @callback(
            Output(
                {
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": ALL,
                },
                "options",
            ),
            Output(
                {
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Output(
                {
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": ALL,
                },
                "disabled",
            ),
            Input("webviz-content-manager", "activeViewId"),
            State(
                {
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": ALL,
                },
                "id",
            ),
            State(
                {
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            State(self.get_store_unique_id(ElementIds.Stores.TORNADO_PLOTS), "data"),
        )
        def _update_tornado_selections(
            active_view_id: str,
            selector_ids: list,
            selector_values: list,
            previous_selection: Optional[dict],
        ) -> tuple:
            custom_tornado_plots_uuid = LayoutUniqueId(
                self.get_unique_id().get_plugin_uuid(),
                ElementIds.TornadoPlots.Custom.ID,
            )
            bulk_tornado_plots_uuid = LayoutUniqueId(
                self.get_unique_id().get_plugin_uuid(),
                ElementIds.TornadoPlots.BulkVsStoiipGiip.ID,
            )
            if (
                active_view_id
                not in [
                    custom_tornado_plots_uuid.to_string(),
                    bulk_tornado_plots_uuid.to_string(),
                ]
                or previous_selection is None
            ):
                raise PreventUpdate

            initial_page_load = active_view_id not in previous_selection

            selections: Any = (
                previous_selection
                if previous_selection
                else {
                    id_value["selector"]: values
                    for id_value, values in zip(selector_ids, selector_values)
                }
            )

            settings = {}
            if active_view_id == bulk_tornado_plots_uuid.to_string():
                volume_options = [
                    x for x in ["STOIIP", "GIIP"] if x in self.volumes_model.responses
                ]
                settings["Response"] = {
                    "options": [{"label": i, "value": i} for i in volume_options],
                    "value": volume_options[0]
                    if initial_page_load
                    else selections["Response"],
                    "disabled": len(volume_options) == 1,
                }
            else:
                responses = [
                    x for x in self.volumes_model.responses if x not in ["BO", "BG"]
                ]
                settings["Response"] = {
                    "options": [{"label": i, "value": i} for i in responses],
                    "disabled": False,
                    "value": selections["Response"],
                }

            settings["bottom_viz"] = {"value": selections["bottom_viz"]}

            disable_subplots = active_view_id != custom_tornado_plots_uuid.to_string()
            settings["Subplots"] = {
                "disabled": disable_subplots,
                "value": None if disable_subplots else selections["Subplots"],
            }

            return tuple(
                update_relevant_components(
                    id_list=selector_ids,
                    update_info=[
                        {
                            "new_value": values.get(prop, no_update),
                            "conditions": {"selector": selector},
                        }
                        for selector, values in settings.items()
                    ],
                )
                for prop in ["options", "value", "disabled"]
            )
