from typing import Dict, List, Optional, Set

import pandas as pd
from plotly.subplots import make_subplots

from webviz_config._theme_class import WebvizConfigTheme
from webviz_subsurface._providers import Frequency

from .graph_figure_builder_base import GraphFigureBuilderBase

from ..types import FanchartOptions, StatisticsOptions

from ..utils.create_vector_traces_utils import (
    create_history_vector_trace,
    create_vector_fanchart_traces,
    create_vector_observation_traces,
    create_vector_realization_traces,
    create_vector_statistics_traces,
    render_hovertemplate,
)


class EnsembleSubplotBuilder(GraphFigureBuilderBase):
    """
    Figure builder for creating/building serializable Output property data
    for the callback. Where vector traces are added per ensemble, and subplots
    are categorized per ensemble among selected ensembles.

    Contains functions for adding titles, graph data and retreving the serialized
    data for callback Output property.

    `Input:`
    * selected_vectors: List[str] - list of selected vector names
    * selected_ensembles: List[str] - list of selected ensemble names
    * vector_colors: dict - Dictionary with vector name as key and graph color as value
    * sampling_frequency: Optional[Frequency] - Sampling frequency of data
    * vector_line_shapes: Dict[str,str] - Dictionary of vector names and line shapes
    * theme: Optional[WebvizConfigTheme] = None - Theme for plugin, given to graph figure
    * line_shape_fallback: str = "linear" - Lineshape fallback
    """

    def __init__(
        self,
        selected_vectors: List[str],
        selected_ensembles: List[str],
        vector_colors: dict,
        sampling_frequency: Optional[Frequency],
        vector_line_shapes: Dict[str, str],
        theme: Optional[WebvizConfigTheme] = None,
        line_shape_fallback: str = "linear",
    ) -> None:
        # Init for base class
        super().__init__()

        self._selected_vectors = selected_vectors
        self._selected_ensembles = selected_ensembles
        self._vector_colors = vector_colors
        self._sampling_frequency = sampling_frequency
        self._line_shape_fallback = line_shape_fallback
        self._vector_line_shapes = vector_line_shapes

        # Overwrite graph figure widget
        self._figure = make_subplots(
            rows=max(1, len(self._selected_ensembles)),
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[f'Ensemble: "{elm}"' for elm in self._selected_ensembles],
        )
        if theme:
            self._figure.update_layout(
                theme.create_themed_layout(self._figure.to_dict().get("layout", {}))
            )
        self._set_keep_uirevision()

        # Internal status added vector legens and history legend
        self._vector_legends_added: Set[str] = set()
        self._history_legend_added = False

    #############################################################################
    #
    # Public methods
    #
    #############################################################################

    def add_realizations_traces(
        self,
        vectors_df: pd.DataFrame,
        ensemble: str,
        add_legend: bool = True,
    ) -> None:
        # Dictionary with vector name as key and list of ensemble traces as value
        vector_traces_set: Dict[str, List[dict]] = {}

        # Get vectors - order not important
        vectors = set(vectors_df.columns) ^ set(["DATE", "REAL"])

        for vector in vectors:
            # Add legend if not already added
            show_legend = add_legend and vector not in self._vector_legends_added
            legendrank: Optional[int] = None

            # Update storage of added legends and set legendrank according to selection order
            if show_legend:
                self._vector_legends_added.add(vector)
                legendrank = self._selected_vectors.index(vector) + 1

            vector_df = vectors_df[["DATE", "REAL", vector]]
            color = self._vector_colors.get(vector, "black")
            line_shape = self._vector_line_shapes.get(vector, self._line_shape_fallback)
            vector_traces_set[vector] = create_vector_realization_traces(
                vector_df=vector_df,
                ensemble=ensemble,
                legend_group=vector,
                color=color,
                line_shape=line_shape,
                hovertemplate=render_hovertemplate(vector, self._sampling_frequency),
                show_legend=show_legend,
                legendrank=legendrank,
            )

        # Add traces to figure
        self._add_vector_traces_set_to_figure(vector_traces_set, ensemble)

    def add_statistics_traces(
        self,
        vectors_statistics_df: pd.DataFrame,
        ensemble: str,
        statistics_options: List[StatisticsOptions],
        add_legend: bool = True,
    ) -> None:
        # Dictionary with vector name as key and list of ensemble traces as value
        vector_traces_set: Dict[str, List[dict]] = {}

        # Get vectors - order not important
        vectors = set(vectors_statistics_df.columns.get_level_values(0)) ^ set(["DATE"])

        for vector in vectors:
            # Add legend if not already added
            show_legend = add_legend and vector not in self._vector_legends_added
            legendrank: Optional[int] = None

            # Update storage of added legends and set legendrank according to selection order
            if show_legend:
                self._vector_legends_added.add(vector)
                legendrank = self._selected_vectors.index(vector) + 1

            # Retrieve DATE and statistics columns for specific vector
            vector_statistics_df = pd.DataFrame(vectors_statistics_df["DATE"]).join(
                vectors_statistics_df[vector]
            )
            color = self._vector_colors.get(vector, "black")
            line_shape = self._vector_line_shapes.get(vector, self._line_shape_fallback)
            vector_traces_set[vector] = create_vector_statistics_traces(
                vector_statistics_df=vector_statistics_df,
                color=color,
                legend_group=vector,
                line_shape=line_shape,
                statistics_options=statistics_options,
                hovertemplate=render_hovertemplate(vector, self._sampling_frequency),
                show_legend=show_legend,
                legendrank=legendrank,
            )

        # Add traces to figure
        self._add_vector_traces_set_to_figure(vector_traces_set, ensemble)

    def add_fanchart_traces(
        self,
        vectors_statistics_df: pd.DataFrame,
        ensemble: str,
        fanchart_options: List[FanchartOptions],
        add_legend: bool = True,
    ) -> None:
        # Dictionary with vector name as key and list of ensemble traces as value
        vector_traces_set: Dict[str, List[dict]] = {}

        # Get vectors - order not important
        vectors = set(vectors_statistics_df.columns.get_level_values(0)) ^ set(["DATE"])

        for vector in vectors:
            # Add legend if not already added
            show_legend = add_legend and vector not in self._vector_legends_added
            legendrank: Optional[int] = None

            # Update storage of added legends and set legendrank according to selection order
            if show_legend:
                self._vector_legends_added.add(vector)
                legendrank = self._selected_vectors.index(vector) + 1

            # Retrieve DATE and statistics columns for specific vector
            vector_statistics_df = pd.DataFrame(vectors_statistics_df["DATE"]).join(
                vectors_statistics_df[vector]
            )
            color = self._vector_colors.get(vector, "black")
            line_shape = self._vector_line_shapes.get(vector, self._line_shape_fallback)
            vector_traces_set[vector] = create_vector_fanchart_traces(
                vector_statistics_df=vector_statistics_df,
                color=color,
                legend_group=vector,
                line_shape=line_shape,
                fanchart_options=fanchart_options,
                hovertemplate=render_hovertemplate(vector, self._sampling_frequency),
                show_legend=show_legend,
                legendrank=legendrank,
            )

        # Add traces to figure
        self._add_vector_traces_set_to_figure(vector_traces_set, ensemble)

    def add_history_traces(
        self,
        vectors_df: pd.DataFrame,
        ensemble: str,
        add_legend: bool = True,
    ) -> None:
        if "DATE" not in vectors_df.columns and "REAL" not in vectors_df.columns:
            raise ValueError('vectors_df is missing required columns ["DATE","REAL"]')

        if ensemble is None:
            raise ValueError(
                "Must provide ensemble argument of type str for this implementation!"
            )

        samples = vectors_df["DATE"].tolist()
        vector_trace_set: Dict[str, dict] = {}
        vectors = set(vectors_df.columns) ^ set(["DATE", "REAL"])

        for vector in vectors:
            # Set show legend on first history vector trace
            show_legend = add_legend and not self._history_legend_added

            # Update state
            if show_legend:
                self._history_legend_added = True

            line_shape = self._vector_line_shapes.get(vector, self._line_shape_fallback)
            vector_trace_set[vector] = create_history_vector_trace(
                samples,
                vectors_df[vector].values,
                line_shape=line_shape,
                vector_name=vector,
                show_legend=show_legend,
            )
        self._add_vector_trace_set_to_figure(vector_trace_set, ensemble)

    def add_vector_observations(
        self, vector_name: str, vector_observations: dict
    ) -> None:
        if vector_name not in self._selected_vectors:
            raise ValueError(f"Vector {vector_name} not among selected vectors!")

        vector_observations_traces_set = {
            vector_name: create_vector_observation_traces(
                vector_observations, vector_name
            )
        }
        for ensemble in self._selected_ensembles:
            self._add_vector_traces_set_to_figure(
                vector_observations_traces_set, ensemble
            )

    #############################################################################
    #
    # Private methods
    #
    #############################################################################

    def _set_keep_uirevision(
        self,
    ) -> None:
        # Keep uirevision (e.g. zoom) for unchanged data.
        self._figure.update_xaxes(uirevision="locked")  # Time axis state kept
        for i, owner in enumerate(self._selected_ensembles, start=1):
            self._figure.update_yaxes(row=i, col=1, uirevision=owner)

    def _add_vector_trace_set_to_figure(
        self, vector_trace_set: Dict[str, dict], ensemble: Optional[str] = None
    ) -> None:
        for trace in vector_trace_set.values():
            subplot_index = (
                self._selected_ensembles.index(ensemble) + 1
                if ensemble in self._selected_ensembles
                else None
            )
            if subplot_index is None:
                continue
            self._figure.add_trace(trace, row=subplot_index, col=1)

    def _add_vector_traces_set_to_figure(
        self, vector_traces_set: Dict[str, List[dict]], ensemble: Optional[str] = None
    ) -> None:
        for vector_traces in vector_traces_set.values():
            subplot_index = (
                self._selected_ensembles.index(ensemble) + 1
                if ensemble in self._selected_ensembles
                else None
            )
            if subplot_index is None:
                continue
            self._figure.add_traces(vector_traces, rows=subplot_index, cols=1)
