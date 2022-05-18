import pandas as pd

from webviz_config.webviz_plugin_subclasses import (
    ViewABC,
    ViewElementABC,
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import Input, Output, callback, html
import webviz_core_components as wcc

from ...utils.table_and_figure_utils import create_data_table, create_table_columns
from ..._layout_elements import ElementIds


class DataTable(ViewElementABC):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return html.Div(
            id=self.register_component_unique_id(
                ElementIds.InplaceDistributions.CustomPlotting.PropertyTable.TABLE
            ),
            children=[],
        )


class TableControls(SettingsGroupABC):
    def __init__(self) -> None:
        super().__init__("Table controls")

    def layout(self) -> Component:
        return wcc.Checklist(
            id=self.register_component_uuid(
                ElementIds.FipFile.Table.Controls.GROUP_TABLE_CHECKBOX
            ),
            options=[
                {"label": "Group table on set", "value": "grouped"},
            ],
            value=["grouped"],
        )


class FipFileTable(ViewABC):
    def __init__(self, disjoint_set_df: pd.DataFrame) -> None:
        super().__init__("Table")

        self.disjoint_set_df = disjoint_set_df

        self.add_settings_group(TableControls(), ElementIds.FipFile.Table.Controls.ID)

        self.add_view_element(DataTable(), ElementIds.FipFile.Table.TABLE)

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.view_element(ElementIds.FipFile.Table.TABLE)
                .get_unique_id()
                .to_string(),
                "children",
            ),
            Input(
                self.settings_group(ElementIds.FipFile.Table.Controls.ID)
                .component_unique_id(
                    ElementIds.FipFile.Table.Controls.GROUP_TABLE_CHECKBOX
                )
                .to_string(),
                "value",
            ),
            Input(self.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_table(group_table: bool, filters: dict) -> Component:
            filters = {
                key: filters[key]
                for key in filters
                if key in ["REGION", "ZONE", "FIPNUM", "SET"]
            }

            df = self.disjoint_set_df[["SET", "FIPNUM", "REGION", "ZONE", "REGZONE"]]

            for filt, values in filters.items():
                df = df.loc[df[filt].isin(values)]

            if group_table:
                df["FIPNUM"] = df["FIPNUM"].astype(str)
                df = df.groupby(["SET"]).agg(lambda x: ", ".join(set(x))).reset_index()

            df = df.sort_values(by=["SET"])

            return create_data_table(
                columns=create_table_columns(df.columns),
                data=df.to_dict("records"),
                table_id={"table_id": "disjointset-info"},
                style_cell_conditional=[
                    {"if": {"column_id": ["SET", "FIPNUM"]}, "width": "10%"},
                    {"if": {"column_id": ["ZONE", "REGION"]}, "width": "20%"},
                ],
                style_cell={
                    "whiteSpace": "normal",
                    "textAlign": "left",
                    "height": "auto",
                },
            )
