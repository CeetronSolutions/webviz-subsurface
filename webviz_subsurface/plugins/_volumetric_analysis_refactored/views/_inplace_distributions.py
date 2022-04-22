from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
from dash.development.base_component import Component

from dash import html

class StockOilTankPlot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def layout(self) -> Component:
        return html.Div(
            children=[
                html.Div(
                    id=self.register_component_uuid("custom-plotting"),
                    style={"display": "block"},
                ),
                html.Div(
                    id=self.register_component_uuid("plots-per-zone"),
                    style={"display": "none"},
                ),
                html.Div(
                    id=self.register_component_uuid("convergence-plot"),
                    style={"display": "none"},
                ),
            ]
        )

    def _set_callbacks(self) -> None:
        return None

class InplaceDistributions(ViewABC):
    def __init__(self) -> None:
        super().__init__("Inplace distributions")

        self.add_view_element(StockOilTankPlot(), "StockOilTankPlot")
