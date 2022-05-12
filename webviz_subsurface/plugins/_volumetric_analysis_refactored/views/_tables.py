from typing import List, Tuple
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
    ViewABC,
    ViewElementABC,
)
from dash.development.base_component import Component

from dash import Input, Output, callback
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from .._layout_elements import ElementIds

from ..utils.table_and_figure_utils import make_tables


class TableControls(SettingsGroupABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Table controls")
        self.volumes_model = volumes_model
        self.selectors = ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]

    def layout(self) -> List[Component]:
        responses = (
            self.volumes_model.volume_columns + self.volumes_model.property_columns
        )
        return [
            wcc.Dropdown(
                label="Table type",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Table type",
                },
                options=[
                    {"label": elm, "value": elm}
                    for elm in ["Statistics table", "Mean table"]
                ],
                value="Mean table",
                clearable=False,
            ),
            wcc.Dropdown(
                label="Group by",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "Group by",
                },
                options=[
                    {"label": elm, "value": elm} for elm in self.volumes_model.selectors
                ],
                value=None,
                multi=True,
                clearable=False,
            ),
            wcc.SelectWithLabel(
                label="Responses",
                id={
                    "plugin_id": self.get_unique_id().get_plugin_uuid(),
                    "settings_id": self.get_unique_id().to_string(),
                    "selector": "table_responses",
                },
                options=[{"label": i, "value": i} for i in responses],
                value=responses,
                size=min(20, len(responses)),
            ),
        ]


class DataTable(ViewElementABC):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return []


class Tables(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Tables")

        self.volumes_model = volumes_model

        column = self.add_column()

        self.response_table = DataTable()
        column.add_view_element(
            self.response_table,
            ElementIds.InplaceDistributions.CustomPlotting.ResponseTable.ID,
        )

        self.property_table = DataTable()
        column.add_view_element(
            self.property_table,
            ElementIds.InplaceDistributions.CustomPlotting.PropertyTable.ID,
        )

        self.add_settings_group(TableControls(volumes_model), ElementIds.Tables.SETTING)

    def set_callbacks(self) -> None:
        @callback(
            Output(self.response_table.get_unique_id().to_string(), "children"),
            Output(self.response_table.get_unique_id().to_string(), "hidden"),
            Output(self.property_table.get_unique_id().to_string(), "children"),
            Output(self.property_table.get_unique_id().to_string(), "hidden"),
            Input(self.get_store_unique_id(ElementIds.Stores.TABLES), "data"),
            Input(self.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_table(
            selections: dict, filters: dict
        ) -> Tuple[Component, bool, Component, bool]:
            table_groups = (
                ["ENSEMBLE", "REAL"]
                if selections["Table type"] == "Statistics table"
                else ["ENSEMBLE"]
            )
            if selections["Group by"] is not None:
                table_groups.extend(
                    [x for x in selections["Group by"] if x not in table_groups]
                )
            dframe = self.volumes_model.get_df(filters=filters, groups=table_groups)

            tables = make_tables(
                dframe=dframe,
                responses=selections["table_responses"],
                groups=selections["Group by"],
                view_height=85,
                table_type=selections["Table type"],
                volumemodel=self.volumes_model,
                selections=selections,
                filters=filters,
            )

            response_table_hidden = True
            property_table_hidden = True

            if len(tables) > 0 and tables[0] is not None:
                response_table_hidden = False
            if len(tables) > 1 and tables[1] is not None:
                property_table_hidden = False

            return (
                tables[0] if len(tables) > 0 and tables[0] is not None else [],
                response_table_hidden,
                tables[1] if len(tables) > 1 and tables[1] is not None else [],
                property_table_hidden,
            )
