from typing import List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
from webviz_config import WebvizConfigTheme
import webviz_core_components as wcc
from dash.development.base_component import Component
from dash import html, no_update

from webviz_subsurface._components.tornado._tornado_bar_chart import TornadoBarChart
from webviz_subsurface._components.tornado._tornado_data import TornadoData
from webviz_subsurface._components.tornado._tornado_table import TornadoTable
from webviz_subsurface._figures import create_figure
from webviz_subsurface._models import InplaceVolumesModel

from ....utils.table_and_figure_utils import create_table_columns, create_figure_matrix


def update_relevant_components(id_list: list, update_info: List[dict]) -> list:
    output_id_list = [no_update] * len(id_list)
    for elm in update_info:
        for idx, x in enumerate(id_list):
            if all(x[key] == value for key, value in elm["conditions"].items()):
                output_id_list[idx] = elm["new_value"]
                break
    return output_id_list


def tornado_figure_and_table(
    tornado_data: TornadoData,
    response: str,
    selections: dict,
    filters: dict,
    theme: WebvizConfigTheme,
    sensitivity_colors: dict,
    font_size: float,
    use_si_format: bool,
    group: Optional[str] = None,
) -> Tuple[go.Figure, List[dict], List[dict]]:

    figure = TornadoBarChart(
        tornado_data=tornado_data,
        plotly_theme=theme.plotly_theme,
        label_options=selections["labeloptions"],
        number_format="#.3g",
        locked_si_prefix=None if use_si_format else "",
        use_true_base=selections["Scale"] == "True",
        show_realization_points=bool(selections["real_scatter"]),
        show_reference=selections["torn_ref"],
        color_by_sensitivity=selections["color_by_sens"],
        sensitivity_color_map=sensitivity_colors,
    ).figure

    figure.update_xaxes(side="bottom", title=None).update_layout(
        title_text=f"Tornadoplot for {response} <br>"
        + f"Fluid zone: {(' + ').join(filters['FLUID_ZONE'])}"
        if group is None
        else f"{response} {group}",
        title_font_size=font_size,
        margin={"t": 70},
    )

    table_data, columns = create_tornado_table(
        tornado_data,
        subplots=selections["Subplots"],
        group=group,
        use_si_format=use_si_format,
    )
    return figure, table_data, columns


def create_tornado_table(
    tornado_data: TornadoData,
    subplots: str,
    group: Optional[str],
    use_si_format: bool,
) -> Tuple[List[dict], List[dict]]:

    tornado_table = TornadoTable(
        tornado_data=tornado_data,
        use_si_format=use_si_format,
        precision=4 if use_si_format else 3,
    )
    table_data = tornado_table.as_plotly_table
    for data in table_data:
        data["Reference"] = tornado_data.reference_average
        if group is not None:
            data[subplots] = group

    columns = create_table_columns(columns=[subplots]) if subplots is not None else []
    columns.extend(tornado_table.columns)
    columns.extend(
        create_table_columns(
            columns=["Reference"],
            use_si_format=["Reference"] if use_si_format else [],
        )
    )
    return table_data, columns


def create_realplot(df: pd.DataFrame, sensitivity_colors: dict) -> go.Figure:
    senscasecolors = {
        senscase: sensitivity_colors[sensname]
        for senscase, sensname in zip(df["sensname_case"], df["sensname"])
    }

    return (
        create_figure(
            plot_type="bar",
            data_frame=df,
            x="REAL",
            y="VALUE",
            color="sensname_case",
            color_discrete_map=senscasecolors,
            barmode="overlay",
            custom_data=["casetype"],
            yaxis={"range": [df["VALUE"].min() * 0.7, df["VALUE"].max() * 1.1]},
            opacity=0.85,
        )
        .update_layout(legend={"orientation": "h", "yanchor": "bottom", "y": 1.02})
        .update_layout(legend_title_text="")
        .for_each_trace(
            lambda t: (
                t.update(marker_line_color="black")
                if t["customdata"][0][0] == "high"
                else t.update(marker_line_color="white", marker_line_width=2)
            )
            if t["customdata"][0][0] != "mc"
            else None
        )
    )


def sens_colors(volumes_model: InplaceVolumesModel) -> dict:
    colors = [
        "#FF1243",
        "#243746",
        "#007079",
        "#80B7BC",
        "#919BA2",
        "#BE8091",
        "#B2D4D7",
        "#FF597B",
        "#BDC3C7",
        "#D8B2BD",
        "#FFE7D6",
        "#D5EAF4",
        "#FF88A1",
    ]
    sensitivities = volumes_model.dataframe["SENSNAME"].unique()
    return dict(zip(sensitivities, colors * 10))


def tornado_plots_layout(
    view_id: str, figures: list, bottom_display: Optional[Component]
) -> wcc.WebvizPluginLayoutColumn:
    matrix = create_figure_matrix(figures)
    max_height = 45 if bottom_display != None else 86

    return wcc.WebvizPluginLayoutColumn(
        children=[
            wcc.WebvizPluginLayoutRow(
                children=[
                    wcc.WebvizViewElement(
                        id=f"{view_id}-{row_index}-{col_index}",
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={
                                "height": f"{max_height/len(matrix)}vh",
                                "min-height": "350px",
                            },
                            figure=fig,
                        ),
                    )
                    for col_index, fig in enumerate(row)
                    if fig is not None
                ]
            )
            for row_index, row in enumerate(matrix)
        ]
        + [
            wcc.WebvizViewElement(
                id=f"{view_id}-tables",
                children=[bottom_display],
                hidden=bottom_display is None,
            )
        ]
    )


def tornado_error_layout(message: str) -> wcc.Frame:
    return html.Div(message, style={"margin-top": "40px"})
