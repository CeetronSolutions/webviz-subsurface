from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from dash import Dash, html
from webviz_config import WebvizPluginABC

from webviz_subsurface._providers import (
    EnsembleSurfaceProviderFactory,
    EnsembleSurfaceProvider,
)
from webviz_subsurface._providers.ensemble_surface_provider.surface_server import (
    SurfaceServer,
)
from .callbacks import plugin_callbacks
from .layout import main_layout


class MapViewerSUMO(WebvizPluginABC):
    """Surface visualizer for FMU ensembles using SUMO."""

    # pylint: disable=too-many-arguments
    def __init__(self, app: Dash, field_name: str, ensembles: Dict[str, List[str]]):

        print("MapViewerSUMO INIT")

        super().__init__()

        surface_provider_factory = EnsembleSurfaceProviderFactory.instance()

        self._ensemble_surface_providers: Dict[str, EnsembleSurfaceProvider] = {}

        case_names = ensembles.keys()
        for case_name in case_names:
            iteration_ids = ensembles[case_name]
            for iteration_id in iteration_ids:
                provider = surface_provider_factory.create_from_sumo_on_demand(
                    field_name=field_name,
                    case_name=case_name,
                    iteration_id=iteration_id,
                )

                ensemble_name = f"CASE:{case_name}  ITER:{iteration_id}"
                self._ensemble_surface_providers[ensemble_name] = provider

        self._surface_server = SurfaceServer.instance(app)

        self.set_callbacks()

        # @app.server.before_request
        # def _my_before_request():
        #     print("Before")

    @property
    def layout(self) -> html.Div:

        print("MapViewerSUMO layout")

        reals = []
        for provider in self._ensemble_surface_providers.values():
            reals.extend([x for x in provider.realizations() if x not in reals])
        return main_layout(
            get_uuid=self.uuid,
            well_names=[],
            realizations=reals,
        )

    def set_callbacks(self) -> None:

        plugin_callbacks(
            get_uuid=self.uuid,
            ensemble_surface_providers=self._ensemble_surface_providers,
            surface_server=self._surface_server,
            ensemble_fault_polygons_providers={},
            fault_polygon_attribute=None,
            fault_polygons_server=None,
            map_surface_names_to_fault_polygons={},
            well_picks_provider=None,
        )
