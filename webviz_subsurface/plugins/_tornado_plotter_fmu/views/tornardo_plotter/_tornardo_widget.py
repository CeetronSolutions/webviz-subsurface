import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from dash import (
    ClientsideFunction,
    Input,
    Output,
    State,
    callback,
    callback_context,
    clientside_callback,
)
from dash.exceptions import PreventUpdate
from webviz_config import WebvizSettings
from webviz_config.webviz_assets import WEBVIZ_ASSETS
from webviz_config.webviz_plugin_subclasses import ViewABC

import webviz_subsurface

from ..._plugin_ids import PlugInIDs
from ...view_elements._tornado_table import TornadoData, TornadoTable
from ...view_elements._tornardo_bar_chart import TornadoBarChart
from ...view_elements._tornardo_view_element import TornadoViewElement


class TornadoWidget(ViewABC):
    class IDs:
        # pylint: disable=too-few-public-methods
        TORNADO_WIDGET = "tornado-widget"
        LABEL = "label"
        RESET_BUTTON = "reset-button"

    def __init__(
        self,
        webviz_settings: WebvizSettings,
        realizations: pd.DataFrame,
        allow_click: bool = False,
    ) -> None:
        super().__init__("Tornado Widget")

        self.realizations = realizations
        self.sensnames = list(self.realizations["SENSNAME"].unique())
        if self.sensnames == [None]:
            raise KeyError(
                "No sensitivity information found in ensemble. "
                "Containers utilizing tornadoplot can only be used for ensembles with "
                "one by one design matrix setup "
                "(SENSNAME and SENSCASE must be present in parameter file)."
            )
        self.allow_click = allow_click
        self.plotly_theme = webviz_settings.theme.plotly_theme
        WEBVIZ_ASSETS.add(
            Path(webviz_subsurface.__file__).parent
            / "_assets"
            / "js"
            / "clientside_functions.js"
        )

        viewcolumn = self.add_column()
        first_row = viewcolumn.make_row()
        first_row.add_view_element(
            TornadoViewElement(), TornadoWidget.IDs.TORNADO_WIDGET
        )

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.LABEL),
                "disabled",
            ),  # skjønner ikke helt hva denne her gjør???
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.PLOT_OPTIONS),
                "value",  # denne er NoneType
            ),
        )
        def _disable_label(plot_options: List) -> bool:
            if plot_options is None:
                return False  # usikker på om denne skal bære ture eller false, den skal hvertfall være skult tror jeg
            else:
                return "Show realization points" in plot_options

        # denne bytter mellom tabell og graf: funker ikke
        @callback(
            Output(
                self.view_element(TornadoWidget.IDs.TORNADO_WIDGET)
                .component_unique_id(TornadoViewElement.IDs.BAR_WRAPPER)
                .to_string(),
                "style",
            ),
            Output(
                self.view_element(TornadoWidget.IDs.TORNADO_WIDGET)
                .component_unique_id(TornadoViewElement.IDs.TABLE_WRAPPER)
                .to_string(),
                "style",
            ),
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.PlotPicker.BARS_OR_TABLE),
                "value",
            ),
            # trengs egt disse?
            State(
                self.view_element(TornadoWidget.IDs.TORNADO_WIDGET)
                .component_unique_id(TornadoViewElement.IDs.BAR_WRAPPER)
                .to_string(),
                "style",
            ),
            State(
                self.view_element(TornadoWidget.IDs.TORNADO_WIDGET)
                .component_unique_id(TornadoViewElement.IDs.TABLE_WRAPPER)
                .to_string(),
                "style",
            ),
        )
        def _set_visualization(
            viz_type: str, graph_style: dict, table_style: dict
        ) -> Tuple[Dict[str, str], Dict[str, str]]:
            if viz_type == "bars":
                return ({"display": "inline"}, {"display": "none"})
            if viz_type == "table":
                return ({"display": "none"}, {"display": "inline"})

        clientside_callback(
            ClientsideFunction(
                namespace="clientside", function_name="get_client_height"
            ),
            Output(
                self.get_store_unique_id(
                    PlugInIDs.Stores.DataStores.CLIENT_HIGH_PIXELS
                ),
                "data",
            ),
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.PLOT_OPTIONS),
                "value",
            ),
        )

        @callback(
            # usikker på hva jeg skal gjøre med view elementsene her
            # for kun wrapperne som er larget som view element, men de har children
            # som er bars og table, som er egt de so er brukt her
            # men hvis jeg legger inn wrapperne og bars og table som view element
            # så blir de vel lagt inn dobbelt opp?
            Output(
                self.view_element(
                    TornadoWidget.IDs.TORNADO_WIDGET
                )  # tester med wrappers her
                .component_unique_id(TornadoViewElement.IDs.TORNADO_BAR)
                .to_string(),
                "figure",
            ),
            Output(
                self.view_element(TornadoWidget.IDs.TORNADO_WIDGET)
                .component_unique_id(TornadoViewElement.IDs.TORNADO_TABLE)
                .to_string(),
                "data",
            ),
            Output(
                self.view_element(TornadoWidget.IDs.TORNADO_WIDGET)
                .component_unique_id(TornadoViewElement.IDs.TORNADO_TABLE)
                .to_string(),
                "columns",
            ),
            Output(
                self.get_store_unique_id(PlugInIDs.Stores.DataStores.HIGH_LOW), "data"
            ),
            Input(
                self.get_store_unique_id(
                    PlugInIDs.Stores.ViewSetttings.REFERENCE
                ),  # må finne ut om det er data eller value på disse
                "value",
            ),
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.SCALE), "value"
            ),
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.PLOT_OPTIONS),
                "value",
            ),
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.LABEL), "value"
            ),
            Input(
                self.get_store_unique_id(
                    PlugInIDs.Stores.DataStores.TORNADO_DATA
                ),  # her var det opprinnelig "storage". litt usiker på hva d er
                "data",
            ),
            Input(
                self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.SENSITIVITIES),
                "value",
            ),
            State(
                self.get_store_unique_id(
                    PlugInIDs.Stores.DataStores.CLIENT_HIGH_PIXELS
                ),
                "data",
            ),
        )
        def _calc_tornado(
            reference: str,
            scale: str,
            plot_options: List,
            label_option: str,
            data: Union[str, bytes, bytearray],
            sens_filter: List[str],
            client_height: Optional[int],
        ) -> Tuple[dict, dict]:
            if not data:
                raise PreventUpdate
            plot_options = plot_options if plot_options else []
            data = json.loads(data)
            if not isinstance(data, dict):
                raise PreventUpdate
            values = pd.DataFrame(data["data"], columns=["REAL", "VALUE"])
            realizations = self.realizations.loc[
                self.realizations["ENSEMBLE"] == data["ENSEMBLE"]
            ]

            design_and_responses = pd.merge(values, realizations, on="REAL")
            if sens_filter is not None:
                if reference not in sens_filter:
                    sens_filter.append(reference)
                design_and_responses = design_and_responses.loc[
                    design_and_responses["SENSNAME"].isin(sens_filter)
                ]
            tornado_data = TornadoData(
                dframe=design_and_responses,
                response_name=data.get("response_name"),
                reference=reference,
                scale="Percentage" if scale == "Relative value (%)" else "Absolute",
                cutbyref="Remove sensitivites with no impact" in plot_options,
            )

            figure_height = (
                client_height * 0.59
                if "Fit all bars in figure" in plot_options
                and client_height is not None
                else max(100 * len(tornado_data.tornadotable["sensname"].unique()), 200)
            )
            tornado_figure = TornadoBarChart(
                tornado_data=tornado_data,
                plotly_theme=self.plotly_theme,
                figure_height=figure_height,
                label_options=label_option,
                number_format=data.get("number_format", ""),
                unit=data.get("unit", ""),
                spaced=data.get("spaced", True),
                locked_si_prefix=data.get("locked_si_prefix", None),
                use_true_base=scale == "True value",
                show_realization_points="Show realization points" in plot_options,
                color_by_sensitivity="Color bars by sensitivity" in plot_options,
            )
            tornado_table = TornadoTable(tornado_data=tornado_data)
            return (
                tornado_figure.figure,
                tornado_table.as_plotly_table,
                tornado_table.columns,
                tornado_data.low_high_realizations_list,
            )

        if self.allow_click:

            @callback(
                Output(
                    self.get_store_unique_id(PlugInIDs.Stores.DataStores.CLICK_DATA),
                    "data",
                ),
                Input(
                    self.view_element(
                        TornadoWidget.IDs.TORNADO_WIDGET
                    )  # tester med wrapper her og
                    .component_unique_id(TornadoViewElement.IDs.TORNADO_BAR)
                    .to_string(),
                    "clickData",
                ),  # vet ikke om dette view elementet har "clickData som en egenskap?"
                Input(
                    self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.RESET),
                    "n_clicks",
                ),  # dette er den kanppens om ikke vises på demoen
                State(
                    self.get_store_unique_id(PlugInIDs.Stores.DataStores.HIGH_LOW),
                    "data",
                ),
            )
            def _save_click_data(
                data: dict, nclicks: Optional[int], sens_reals: dict
            ) -> str:
                if (
                    callback_context.triggered is None
                    or sens_reals is None
                    or data is None
                ):
                    raise PreventUpdate
                ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
                if (
                    ctx
                    == self.get_store_unique_id(PlugInIDs.Stores.ViewSetttings.RESET)
                    and nclicks
                ):
                    return json.dumps(
                        {
                            "real_low": [],
                            "real_high": [],
                            "sens_name": None,
                        }
                    )
                sensname = data["points"][0]["y"]
                real_high = sens_reals[sensname]["real_high"]
                real_low = sens_reals[sensname]["real_low"]
                return json.dumps(
                    {
                        "real_low": real_low,
                        "real_high": real_high,
                        "sens_name": sensname,
                    }
                )
