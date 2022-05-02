from typing import Any, Callable, List, Optional, Tuple

import plotly.graph_objects as go
from webviz_config import WebvizConfigTheme

from webviz_subsurface._components.tornado._tornado_bar_chart import TornadoBarChart
from webviz_subsurface._components.tornado._tornado_data import TornadoData
from webviz_subsurface._components.tornado._tornado_table import TornadoTable

from ....utils.table_and_figure_utils import (
    create_table_columns,
)

def tornado_figure_and_table(
    tornado_data: TornadoData,
    response: str,
    selections: dict,
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
        + f"Fluid zone: {(' + ').join(selections['filters']['FLUID_ZONE'])}"
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
