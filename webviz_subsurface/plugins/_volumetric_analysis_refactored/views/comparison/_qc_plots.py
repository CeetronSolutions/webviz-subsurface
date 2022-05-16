from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import webviz_core_components as wcc
from dash.development.base_component import Component
from dash import Input, Output, callback, html
from dash.exceptions import PreventUpdate
from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
from webviz_subsurface._figures import create_figure

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ..._layout_elements import ElementIds
from ...utils.table_and_figure_utils import (
    add_correlation_line,
)

from .utils import find_higlighted_real_count


class Plot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return wcc.Graph(
            id=self.register_component_unique_id(ElementIds.Comparison.GRAPH),
            config={"displayModeBar": False},
            style={"height": "30vh"},
        )


class HighlightedData(ViewElementABC):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return []


class QCPlots(ViewABC):
    def __init__(self, compare_on: str, volumes_model: InplaceVolumesModel):
        super().__init__("QC plots")
        self.volumes_model = volumes_model
        self.compare_on = compare_on

        column = self.add_column()
        column.add_view_element(Plot(), ElementIds.Comparison.QCPlots.PLOT_DIFF_VS_REAL)
        row = column.make_row(row_id=ElementIds.Comparison.QCPlots.ROW)
        row.add_view_element(
            Plot(), ElementIds.Comparison.QCPlots.PLOT_DIFF_VS_RESPONSE
        )
        row.add_view_element(Plot(), ElementIds.Comparison.QCPlots.PLOT_CORRELATION)
        column.add_view_element(
            HighlightedData(), ElementIds.Comparison.QCPlots.HIGHLIGHTED_DATA
        )

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.PLOT_DIFF_VS_REAL)
                .component_unique_id(ElementIds.Comparison.GRAPH)
                .to_string(),
                "figure",
            ),
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.PLOT_DIFF_VS_REAL)
                .get_unique_id()
                .to_string(),
                "hidden",
            ),
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.PLOT_DIFF_VS_RESPONSE)
                .component_unique_id(ElementIds.Comparison.GRAPH)
                .to_string(),
                "figure",
            ),
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.PLOT_DIFF_VS_RESPONSE)
                .component_unique_id(ElementIds.Comparison.GRAPH)
                .to_string(),
                "hidden",
            ),
            Output(
                self.layout_element(ElementIds.Comparison.QCPlots.ROW)
                .get_unique_id()
                .to_string(),
                "hidden",
            ),
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.PLOT_CORRELATION)
                .component_unique_id(ElementIds.Comparison.GRAPH)
                .to_string(),
                "figure",
            ),
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.PLOT_CORRELATION)
                .get_unique_id()
                .to_string(),
                "hidden",
            ),
            Output(
                self.view_element(ElementIds.Comparison.QCPlots.HIGHLIGHTED_DATA)
                .get_unique_id()
                .to_string(),
                "children",
            ),
            Input(
                self.get_store_unique_id(f"{self.compare_on.lower()}_comparison"),
                "data",
            ),
            Input(self.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_page_ens_comp(
            selections: dict,
            filters: dict,
        ) -> Tuple[dict, bool, dict, bool, bool, dict, bool, html.Div]:
            if selections is None:
                raise PreventUpdate

            return self.comparison_callback(
                compare_on="SENSNAME_CASE"
                if self.compare_on == "Sensitivity"
                else "ENSEMBLE",
                selections=selections,
                filters=filters,
            )

    def comparison_callback(
        self,
        compare_on: str,
        selections: dict,
        filters: dict,
    ) -> Tuple[dict, bool, dict, bool, bool, dict, bool, html.Div]:
        if selections["value1"] == selections["value2"]:
            return (
                {},
                True,
                {},
                True,
                True,
                {},
                True,
                html.Div("Comparison between equal data"),
            )

        filters = { key: filters[key] for key in filters.keys() if key not in ["FIPNUM", "SET"] }

        # Handle None in highlight criteria input
        for key in ["Accept value", "Ignore <"]:
            selections[key] = selections[key] if selections[key] is not None else 0

        groupby = selections["Group by"] if selections["Group by"] is not None else []
        group_on_fluid = "FLUID_ZONE" in groupby
        # for hc responses and bo/bg the data should be grouped
        # on fluid zone to avoid misinterpretations
        if (
            selections["Response"] in self.volumes_model.hc_responses + ["BO", "BG"]
            and "FLUID_ZONE" not in groupby
        ):
            groupby.append("FLUID_ZONE")

        if compare_on == "SOURCE" or "REAL" in groupby:
            diffdf_real = self.create_comparison_df(
                self.volumes_model,
                compare_on=compare_on,
                selections=selections,
                filters=filters,
                responses=[selections["Response"]],
                groups=groupby + (["REAL"] if "REAL" not in groupby else []),
                rename_diff_col=True,
            )

        if "REAL" not in groupby:
            diffdf_group = self.create_comparison_df(
                self.volumes_model,
                compare_on=compare_on,
                selections=selections,
                filters=filters,
                responses=[selections["Response"]],
                groups=groupby,
                rename_diff_col=True,
            )
            if compare_on == "SOURCE" and not diffdf_group.empty:
                # Add column with number of highlighted realizations
                diffdf_group["💡 reals"] = diffdf_group.apply(
                    lambda row: find_higlighted_real_count(row, diffdf_real, groupby),
                    axis=1,
                )

        df = diffdf_group if "REAL" not in groupby else diffdf_real

        if df.empty:
            return (
                {},
                True,
                {},
                True,
                True,
                {},
                True,
                html.Div("No data left after filtering"),
            )

        if "|" in selections["value1"]:
            ens1, sens1 = selections["value1"].split("|")
            ens2, sens2 = selections["value2"].split("|")
            value1, value2 = (sens1, sens2) if ens1 == ens2 else (ens1, ens2)
        else:
            value1, value2 = selections["value1"], selections["value2"]

        resp1 = f"{selections['Response']} {value1}"
        resp2 = f"{selections['Response']} {value2}"

        scatter_corr = self.create_scatterfig(
            df=df, x=resp1, y=resp2, selections=selections, groupby=groupby
        )
        scatter_corr = add_correlation_line(
            figure=scatter_corr, xy_min=df[resp1].min(), xy_max=df[resp1].max()
        )
        scatter_diff_vs_response = self.create_scatterfig(
            df=df,
            x=resp1,
            y=selections["Diff mode"],
            selections=selections,
            groupby=groupby,
            diff_mode=selections["Diff mode"],
        )
        scatter_diff_vs_real = (
            self.create_scatterfig(
                df=diffdf_real,
                x="REAL",
                y=selections["Diff mode"],
                selections=selections,
                groupby=groupby,
                diff_mode=selections["Diff mode"],
            )
            if compare_on == "SOURCE"
            else None
        )
        barfig_non_highlighted = self.create_barfig(
            df=df[df["highlighted"] == "yes"],
            groupby=groupby
            if group_on_fluid
            else [x for x in groupby if x != "FLUID_ZONE"],
            diff_mode=selections["Diff mode"],
            colorcol=resp1,
        )

        return (
            scatter_diff_vs_real if scatter_diff_vs_real is not None else {},
            scatter_diff_vs_real is None,
            scatter_diff_vs_response if scatter_diff_vs_response is not None else {},
            scatter_diff_vs_response is None,
            scatter_diff_vs_real is None and scatter_diff_vs_response is None,
            scatter_corr if scatter_corr is not None else {},
            scatter_corr is None,
            html.Div("No data within highlight criteria")
            if barfig_non_highlighted is None
            else html.Div(
                [
                    wcc.Header("Highlighted data"),
                    wcc.Graph(
                        config={"displayModeBar": False},
                        style={"height": "25vh"},
                        figure=barfig_non_highlighted,
                    ),
                ]
            ),
        )

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    def create_comparison_df(
        self,
        volumemodel: InplaceVolumesModel,
        compare_on: str,
        responses: list,
        selections: dict,
        filters: dict,
        groups: list,
        abssort_on: str = "diff (%)",
        rename_diff_col: bool = False,
    ) -> pd.DataFrame:

        filters_subset = {
            key: value for key, value in filters.items() if key in ["REGION", "ZONE"]
        }

        resp = selections["Response"]
        adiitional_groups = [
            x
            for x in ["SOURCE", "ENSEMBLE", "SENSNAME_CASE"]
            if x in volumemodel.selectors
        ]
        groups = groups + adiitional_groups
        df = volumemodel.get_df(filters_subset, groups=groups)

        # filter dataframe and set values to compare against
        if not "|" in selections["value1"]:
            value1, value2 = selections["value1"], selections["value2"]
            df = df[df[compare_on].isin([value1, value2])]
        else:
            ens1, sens1 = selections["value1"].split("|")
            ens2, sens2 = selections["value2"].split("|")
            if ens1 == ens2:
                compare_on = "SENSNAME_CASE"
            value1, value2 = (sens1, sens2) if ens1 == ens2 else (ens1, ens2)

            df = df[
                ((df["ENSEMBLE"] == ens1) & (df["SENSNAME_CASE"] == sens1))
                | ((df["ENSEMBLE"] == ens2) & (df["SENSNAME_CASE"] == sens2))
            ]

        # if no data left, or one of the selected SOURCE/ENSEMBLE is not present
        # in the dataframe after filtering, return empty dataframe
        if df.empty or any(x not in df[compare_on].values for x in [value1, value2]):
            return pd.DataFrame()

        df = df.loc[:, groups + responses].pivot_table(
            columns=compare_on,
            index=[x for x in groups if x not in [compare_on, "SENSNAME_CASE"]],
        )
        responses = [x for x in responses if x in df]
        for col in responses:
            df[col, "diff"] = df[col][value2] - df[col][value1]
            df[col, "diff (%)"] = ((df[col][value2] / df[col][value1]) - 1) * 100
            df.loc[df[col]["diff"] == 0, (col, "diff (%)")] = 0
        df = df[responses].replace([np.inf, -np.inf], np.nan).reset_index()

        # remove rows where the selected response is nan
        # can happen for properties where the volume columns are 0
        df = df.loc[~((df[resp][value1].isna()) & (df[resp][value2].isna()))]
        if selections["Remove zeros"]:
            df = df.loc[~((df[resp]["diff"] == 0) & (df[resp][value1] == 0))]

        df["highlighted"] = self.compute_highlighted_col(df, resp, value1, selections)
        df.columns = df.columns.map(" ".join).str.strip(" ")

        # remove BO∕BG columns if they are nan and drop SOURCE/ENSMEBLE column
        dropcols = [
            x for x in df.columns[df.isna().all()] if x.split(" ")[0] in ["BO", "BG"]
        ] + adiitional_groups
        df = df[[x for x in df.columns if x not in dropcols]]

        if rename_diff_col:
            df = df.rename(
                columns={f"{resp} diff": "diff", f"{resp} diff (%)": "diff (%)"}
            )
        df = self.add_fluid_zone_column(df, filters_subset)
        return df.sort_values(by=[abssort_on], key=abs, ascending=False)

    def create_scatterfig(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        selections: dict,
        groupby: list,
        diff_mode: Optional[str] = None,
    ) -> go.Figure:

        highlight_colors = {"yes": "#FF1243", "no": "#80B7BC"}
        colorby = (
            selections["Color by"]
            if selections["Color by"] == "highlighted"
            else groupby[0]
        )
        df[colorby] = df[colorby].astype(str)

        fig = (
            create_figure(
                plot_type="scatter",
                data_frame=df,
                x=x,
                y=y,
                color_discrete_sequence=px.colors.qualitative.Dark2,
                color_discrete_map=highlight_colors
                if colorby == "highlighted"
                else None,
                color=colorby,
                hover_data=groupby,
            )
            .update_traces(marker_size=10)
            .update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20})
        )
        if len(df) == 1:
            fig.update_xaxes(range=[df[x].mean() * 0.95, df[x].mean() * 1.05])
        if diff_mode is not None:
            fig.update_yaxes(range=self.find_diff_plot_range(df, diff_mode, selections))
            if diff_mode == "diff (%)" and y == diff_mode:
                fig.add_hline(y=selections["Accept value"], line_dash="dot").add_hline(
                    y=-selections["Accept value"], line_dash="dot"
                )
        return fig

    @staticmethod
    def find_diff_plot_range(
        df: pd.DataFrame, diff_mode: str, selections: dict
    ) -> list:
        """
        Find plot range for diff axis. If axis focus is selected
        the range will center around the non-acepted data points.
        An 10% extension is added to the axis
        """
        if selections["Axis focus"] and "yes" in df["highlighted"].values:
            df = df[df["highlighted"] == "yes"]

        low = min(df[diff_mode].min(), -selections["Accept value"])
        high = max(df[diff_mode].max(), selections["Accept value"])
        extend = (high - low) * 0.1
        return [low - extend, high + extend]

    @staticmethod
    def create_barfig(
        df: pd.DataFrame, groupby: list, diff_mode: str, colorcol: str
    ) -> Union[None, go.Figure]:
        if df.empty:
            return None
        return (
            create_figure(
                plot_type="bar",
                data_frame=df,
                x=df[groupby].astype(str).agg(" ".join, axis=1)
                if groupby
                else ["Total"],
                y=diff_mode,
                color_continuous_scale="teal_r",
                color=df[colorcol],
                hover_data={col: True for col in groupby},
                opacity=1,
            )
            .update_layout(
                margin={"l": 20, "r": 20, "t": 5, "b": 5},
                bargap=0.15,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            .update_xaxes(title_text=None, tickangle=45, ticks="outside")
            .update_yaxes(zeroline=True, zerolinecolor="black")
        )

    @staticmethod
    def add_fluid_zone_column(dframe: pd.DataFrame, filters: dict) -> pd.DataFrame:
        if "FLUID_ZONE" not in dframe and "FLUID_ZONE" in filters:
            dframe["FLUID_ZONE"] = (" + ").join(filters["FLUID_ZONE"])
        return dframe

    @staticmethod
    def compute_highlighted_col(
        df: pd.DataFrame, response: str, value1: str, selections: dict
    ) -> np.ndarray:
        highlight_mask = (df[response][value1] > selections["Ignore <"]) & (
            df[response]["diff (%)"].abs() > selections["Accept value"]
        )
        return np.where(highlight_mask, "yes", "no")
