from typing import Any, Dict, Optional

from dash import ALL, Input, Output, State, callback, callback_context, no_update
from dash.exceptions import PreventUpdate
from dash.development.base_component import Component
from webviz_config import WebvizPluginABC
import webviz_core_components as wcc
from webviz_subsurface._models import InplaceVolumesModel
from webviz_subsurface._utils.formatting import printable_int_list

from ._layout_elements import ElementIds
from .utils import update_relevant_components


def set_plugin_callbacks(
    plugin: WebvizPluginABC, volumes_model: InplaceVolumesModel
) -> None:
    @callback(
        Output(plugin.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        Input(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": ALL,
            },
            "value",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": ALL,
            },
            "id",
        ),
    )
    def _update_filters(
        filter_values: list,
        filter_ids: list,
    ) -> dict:
        ctx = callback_context.triggered[0]
        if ctx["prop_id"] == ".":
            raise PreventUpdate

        filters = {
            id_value["selector"]: values
            for id_value, values in zip(filter_ids, filter_values)
        }

        return filters

    @callback(
        Output(
            plugin.get_store_unique_id(ElementIds.Stores.INPLACE_DISTRIBUTIONS),
            "data",
        ),
        Input(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "value",
        ),
        Input(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.Settings.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "value",
        ),
        State(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "id",
        ),
        State(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.Settings.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "id",
        ),
    )
    def _update_inplace_distributions_selections(
        plot_controls_values: list,
        settings_values: list,
        plot_controls_ids: list,
        settings_ids: list,
    ) -> dict:
        ctx = callback_context.triggered[0]
        if ctx["prop_id"] == ".":
            raise PreventUpdate

        ids_values_dict = {
            id["selector"]: value
            for id, value in zip(
                plot_controls_ids + settings_ids,
                plot_controls_values + settings_values,
            )
        }

        return ids_values_dict

    @callback(
        Output(plugin.get_store_unique_id(ElementIds.Stores.TABLES), "data"),
        Input(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.view(ElementIds.Tables.ID)
                .settings_group(ElementIds.Tables.SETTING)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "value",
        ),
        State(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.view(ElementIds.Tables.ID)
                .settings_group(ElementIds.Tables.SETTING)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "id",
        ),
    )
    def _update_table_selections(
        values: list,
        ids: list,
    ) -> dict:
        ctx = callback_context.triggered[0]
        if ctx["prop_id"] == ".":
            raise PreventUpdate

        ids_values_dict = {
            id["selector"]: value
            for id, value in zip(
                ids,
                values,
            )
        }

        return ids_values_dict

    if volumes_model.sensrun:

        @callback(
            Output(plugin.get_store_unique_id(ElementIds.Stores.TORNADO_PLOTS), "data"),
            Input(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        ElementIds.TornadoPlots.Settings.TornadoControls.ID
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Input(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        ElementIds.TornadoPlots.Settings.Settings.ID
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            State(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        ElementIds.TornadoPlots.Settings.TornadoControls.ID
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "id",
            ),
            State(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        ElementIds.TornadoPlots.Settings.Settings.ID
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "id",
            ),
        )
        def _update_tornado_plots_selections(
            plot_controls_values: list,
            settings_values: list,
            plot_controls_ids: list,
            settings_ids: list,
        ) -> dict:
            ctx = callback_context.triggered[0]
            if ctx["prop_id"] == ".":
                raise PreventUpdate

            ids_values_dict = {
                id["selector"]: value
                for id, value in zip(
                    plot_controls_ids + settings_ids,
                    plot_controls_values + settings_values,
                )
            }

            return ids_values_dict

    if len(volumes_model.sources) > 1:

        @callback(
            Output(
                plugin.get_store_unique_id(ElementIds.Comparison.SourceComparison.ID),
                "data",
            ),
            Input(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.Settings.Controls.ID}",
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Input(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.Settings.Settings.ID}",
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            State(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.Settings.Controls.ID}",
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "id",
            ),
            State(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.Settings.Settings.ID}",
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": ALL,
                },
                "id",
            ),
        )
        def _update_source_comparison_selections(
            plot_controls_values: list,
            settings_values: list,
            plot_controls_ids: list,
            settings_ids: list,
        ) -> dict:
            ctx = callback_context.triggered[0]
            if ctx["prop_id"] == ".":
                raise PreventUpdate

            ids_values_dict = {
                id["selector"]: value
                for id, value in zip(
                    plot_controls_ids + settings_ids,
                    plot_controls_values + settings_values,
                )
            }

            return ids_values_dict

    if len(volumes_model.ensembles) > 1 or volumes_model.sensrun:
        if len(volumes_model.ensembles) > 1:

            @callback(
                Output(
                    plugin.get_store_unique_id(
                        ElementIds.Comparison.EnsembleComparison.ID
                    ),
                    "data",
                ),
                Input(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Controls.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "value",
                ),
                Input(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Settings.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "value",
                ),
                State(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Controls.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "id",
                ),
                State(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Settings.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "id",
                ),
            )
            def _update_ensemble_comparison_selections(
                plot_controls_values: list,
                settings_values: list,
                plot_controls_ids: list,
                settings_ids: list,
            ) -> dict:
                ctx = callback_context.triggered[0]
                if ctx["prop_id"] == ".":
                    raise PreventUpdate

                ids_values_dict = {
                    id["selector"]: value
                    for id, value in zip(
                        plot_controls_ids + settings_ids,
                        plot_controls_values + settings_values,
                    )
                }

                return ids_values_dict

        else:

            @callback(
                Output(
                    plugin.get_store_unique_id(
                        ElementIds.Comparison.SensitivityComparison.ID
                    ),
                    "data",
                ),
                Input(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Controls.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "value",
                ),
                Input(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Settings.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "value",
                ),
                State(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Controls.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "id",
                ),
                State(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Settings.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": ALL,
                    },
                    "id",
                ),
            )
            def _update_sensitivity_comparison_selections(
                plot_controls_values: list,
                settings_values: list,
                plot_controls_ids: list,
                settings_ids: list,
            ) -> dict:
                ctx = callback_context.triggered[0]
                if ctx["prop_id"] == ".":
                    raise PreventUpdate

                ids_values_dict = {
                    id["selector"]: value
                    for id, value in zip(
                        plot_controls_ids + settings_ids,
                        plot_controls_values + settings_values,
                    )
                }

                return ids_values_dict

    @callback(
        Output(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "disabled",
        ),
        Output(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "value",
        ),
        Output(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "options",
        ),
        Input(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": "Plot type",
            },
            "value",
        ),
        Input("webviz-content-manager", "activeViewId"),
        Input(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": "Color by",
            },
            "value",
        ),
        State(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "value",
        ),
        State(
            {
                "plugin_id": plugin.uuid(),
                "settings_id": plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string(),
                "selector": ALL,
            },
            "id",
        ),
        State(
            plugin.get_store_unique_id(ElementIds.Stores.INPLACE_DISTRIBUTIONS),
            "data",
        ),
    )
    # pylint: disable=too-many-locals
    def _plot_options(
        plot_type: str,
        active_view_id: str,
        selected_color_by: list,
        selector_values: list,
        selector_ids: list,
        previous_selection: Optional[dict],
    ) -> tuple:
        ctx = callback_context.triggered[0]
        custom_view_id = (
            plugin.view(ElementIds.InplaceDistributions.CustomPlotting.ID)
            .get_unique_id()
            .to_string()
        )
        per_zr_view_id = (
            plugin.view(ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID)
            .get_unique_id()
            .to_string()
        )
        convergence_view_id = (
            plugin.view(ElementIds.InplaceDistributions.ConvergencePlot.ID)
            .get_unique_id()
            .to_string()
        )
        if (
            active_view_id
            not in [
                custom_view_id,
                per_zr_view_id,
                convergence_view_id,
            ]
            or ("Color by" in ctx["prop_id"] and plot_type not in ["box", "bar"])
            or previous_selection is None
        ):
            raise PreventUpdate

        selections: Any = (
            previous_selection.get(active_view_id)
            if "page-selected" in ctx["prop_id"]
            and active_view_id in previous_selection
            else {
                id_value["selector"]: values
                for id_value, values in zip(selector_ids, selector_values)
            }
        )

        selectors_disable_in_pages: Dict[str, list] = {
            "Plot type": [per_zr_view_id, convergence_view_id],
            "Y Response": [per_zr_view_id, convergence_view_id],
            "X Response": [],
            "Color by": [convergence_view_id],
            "Subplots": [per_zr_view_id],
        }

        settings: Dict[str, dict] = {}
        for selector, disable_in_pages in selectors_disable_in_pages.items():
            disable = active_view_id in disable_in_pages or (
                selector == "Y Response"
                and selections["Plot type"] in ["distribution", "histogram"]
            )

            settings[selector] = {
                "disable": disable,
                "value": selections.get(selector),
            }

        # update dropdown options based on plot type
        if settings["Plot type"]["value"] == "scatter":
            y_elm = x_elm = (
                volumes_model.responses
                + volumes_model.selectors
                + volumes_model.parameters
            )
        elif settings["Plot type"]["value"] in ["box", "bar"]:
            y_elm = x_elm = volumes_model.responses + volumes_model.selectors
            if selections.get("Y Response") is None:
                settings["Y Response"]["value"] = selected_color_by
        else:
            y_elm = volumes_model.selectors
            x_elm = volumes_model.responses

        colorby_elm = (
            list(volumes_model.dataframe.columns) + volumes_model.parameters
            if settings["Plot type"]["value"] == "scatter"
            else [x for x in volumes_model.selectors if x != "REAL"]
        )
        settings["Y Response"]["options"] = [
            {"label": elm, "value": elm} for elm in y_elm
        ]
        settings["X Response"]["options"] = [
            {"label": elm, "value": elm} for elm in x_elm
        ]
        if (
            settings["X Response"]["value"] is not None
            and settings["X Response"]["value"] not in x_elm
        ):
            settings["X Response"]["value"] = x_elm[0]

        settings["Color by"]["options"] = [
            {"label": elm, "value": elm} for elm in colorby_elm
        ]

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
            for prop in ["disable", "value", "options"]
        )

    @callback(
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "undef",
            },
            "multi",
        ),
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "undef",
            },
            "value",
        ),
        Input("webviz-content-manager", "activeViewId"),
        Input(
            {"plugin_id": plugin.uuid(), "settings_id": ALL, "selector": ALL}, "value"
        ),
        State({"plugin_id": plugin.uuid(), "settings_id": ALL, "selector": ALL}, "id"),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "undef",
            },
            "options",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "undef",
            },
            "multi",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "undef",
            },
            "id",
        ),
    )
    # pylint: disable=too-many-locals
    def _update_filter_options(
        active_view_id: str,
        selectors: list,
        selector_ids: list,
        filter_options: list,
        filter_multi: list,
        filter_ids: list,
    ) -> tuple:

        distribution_view_ids = list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.InplaceDistributions.NAME),
            )
        )

        tornado_view_ids = list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.TornadoPlots.NAME),
            )
        )

        source_comparison_views = list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.SourceComparison.NAME),
            )
        )

        ensemble_comparison_views = list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.EnsembleComparison.NAME),
            )
        )

        sensitivity_comparison_views = list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.SensitivityComparison.NAME),
            )
        )

        active_settings_ids = []

        if active_view_id in distribution_view_ids:
            active_settings_ids.append(
                plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.PlotControls.ID
                )
                .get_unique_id()
                .to_string()
            )
            active_settings_ids.append(
                plugin.shared_settings_group(
                    ElementIds.InplaceDistributions.Settings.Settings.ID
                )
                .get_unique_id()
                .to_string()
            )
        elif (
            active_view_id
            == plugin.view(ElementIds.Tables.ID).get_unique_id().to_string()
        ):
            active_settings_ids.append(
                plugin.view(ElementIds.Tables.ID)
                .settings_group(ElementIds.Tables.SETTING)
                .get_unique_id()
                .to_string()
            )
        elif active_view_id in tornado_view_ids:
            active_settings_ids.append(
                plugin.shared_settings_group(
                    ElementIds.TornadoPlots.Settings.TornadoControls.ID
                )
                .get_unique_id()
                .to_string()
            )
            active_settings_ids.append(
                plugin.shared_settings_group(
                    ElementIds.TornadoPlots.Settings.Settings.ID
                )
                .get_unique_id()
                .to_string()
            )
        elif active_view_id in source_comparison_views:
            active_settings_ids.append(
                plugin.shared_settings_group(
                    f"{ElementIds.Comparison.SourceComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Controls.ID}"
                )
                .get_unique_id()
                .to_string()
            )
            active_settings_ids.append(
                plugin.shared_settings_group(
                    f"{ElementIds.Comparison.SourceComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Settings.ID}"
                )
                .get_unique_id()
                .to_string()
            )
        elif active_view_id in ensemble_comparison_views:
            active_settings_ids.append(
                plugin.shared_settings_group(
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Controls.ID}"
                )
                .get_unique_id()
                .to_string()
            )
            active_settings_ids.append(
                plugin.shared_settings_group(
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Settings.ID}"
                )
                .get_unique_id()
                .to_string()
            )
        elif active_view_id in sensitivity_comparison_views:
            active_settings_ids.append(
                plugin.shared_settings_group(
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Controls.ID}"
                )
                .get_unique_id()
                .to_string()
            )
            active_settings_ids.append(
                plugin.shared_settings_group(
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Settings.ID}"
                )
                .get_unique_id()
                .to_string()
            )

        page_selections = {
            id_value["selector"]: values
            for id_value, values in zip(selector_ids, selectors)
            if id_value["settings_id"] in active_settings_ids
        }
        page_filter_settings = {
            id_value["selector"]: {"options": options, "multi": multi}
            for id_value, options, multi in zip(
                filter_ids, filter_options, filter_multi
            )
        }

        selected_data = []

        if active_view_id in distribution_view_ids:
            selected_data = [
                page_selections[x]
                for x in ["Color by", "Subplots", "X Response", "Y Response"]
            ]
        if (
            active_view_id == plugin.unverified_view_uuid(ElementIds.Tables.ID)
            and page_selections["Group by"] is not None
        ):
            selected_data = page_selections["Group by"]
        if active_view_id in tornado_view_ids:
            selected_data = ["SENSNAME_CASE", page_selections["Subplots"]]
        if active_view_id in list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.EnsembleComparison.NAME),
            )
        ):
            selected_data = ["SENSNAME_CASE", "ENSEMBLE"]
        if active_view_id in list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.SourceComparison.NAME),
            )
        ):
            selected_data = ["SOURCE"]

        # set "SENSNAME_CASE" multi also if "SENSNAME" OR "SENSCASE" is selected
        if any(senscol in selected_data for senscol in ("SENSNAME", "SENSCASE")):
            selected_data.append("SENSNAME_CASE")

        output = {}
        for selector in ["SOURCE", "ENSEMBLE", "SENSNAME_CASE"]:
            if selector not in page_filter_settings:
                continue
            options = [x["value"] for x in page_filter_settings[selector]["options"]]
            multi = selector in selected_data
            selector_is_multi = page_filter_settings[selector]["multi"]
            if not multi and selector_is_multi:
                values = [
                    "rms_seed"
                    if selector == "SENSNAME_CASE" and "rms_seed" in options
                    else options[0]
                ]
            elif multi and not selector_is_multi:
                values = options
            else:
                multi = values = no_update
            output[selector] = {"multi": multi, "values": values}

        # filter tornado on correct fluid based on volume response chosen
        output["FLUID_ZONE"] = {}
        if active_view_id == plugin.unverified_view_uuid(
            ElementIds.TornadoPlots.BulkVsStoiipGiip.ID
        ):
            output["FLUID_ZONE"] = {
                "values": ["oil" if page_selections["Response"] == "STOIIP" else "gas"]
            }

        return (
            update_relevant_components(
                id_list=filter_ids,
                update_info=[
                    {
                        "new_value": values.get("multi", no_update),
                        "conditions": {"selector": selector},
                    }
                    for selector, values in output.items()
                ],
            ),
            update_relevant_components(
                id_list=filter_ids,
                update_info=[
                    {
                        "new_value": values.get("values", no_update),
                        "conditions": {"selector": selector},
                    }
                    for selector, values in output.items()
                ],
            ),
        )

    @callback(
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "wrapper": ALL,
                "type": "undef",
            },
            "style",
        ),
        Input("webviz-content-manager", "activeViewId"),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "wrapper": ALL,
                "type": "undef",
            },
            "id",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "undef",
            },
            "options",
        ),
    )
    def _hide_filters(active_view_id: str, filter_ids: list, elements: list) -> tuple:
        hide_selectors = ["SENSNAME", "SENSTYPE", "SENSCASE"]

        if active_view_id in list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.TornadoPlots.NAME),
            )
        ):
            hide_selectors += ["SENSNAME_CASE"]

        if active_view_id in list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.SourceComparison.NAME),
            )
        ):
            hide_selectors += ["SOURCE", "FLUID_ZONE"]

        if active_view_id in list(
            map(
                lambda x: x[1].get_unique_id().to_string(),
                plugin.views(ElementIds.Comparison.EnsembleComparison.NAME)
                + plugin.views(ElementIds.Comparison.SensitivityComparison.NAME),
            )
        ):
            hide_selectors += ["ENSEMBLE", "FLUID_ZONE", "SENSNAME_CASE"]

        return tuple(
            {"display": "none"}
            if (filter["wrapper"] in hide_selectors or len(options) <= 1)
            else {"display": ""}
            for filter, options in zip(filter_ids, elements)
        )

    @callback(
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "REAL",
            },
            "value",
        ),
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "element": "real_text",
            },
            "children",
        ),
        Input(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "component_type": ALL,
            },
            "value",
        ),
        State("webviz-content-manager", "activeViewId"),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "component_type": ALL,
            },
            "id",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "element": "real_text",
            },
            "id",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "REAL",
            },
            "id",
        ),
    )
    def _update_realization_filter_and_text(
        reals: list,
        active_view_id: str,
        reals_ids: list,
        real_string_id: str,
        real_filter_id: list,
    ) -> tuple:
        """Callback that updates the selected relization info and text"""
        if active_view_id == plugin.unverified_view_uuid(ElementIds.FipQC.ID):
            raise PreventUpdate

        real_list = [int(real) for real in reals[0]]

        if reals_ids[0]["component_type"] == "range":
            real_list = list(range(real_list[0], real_list[1] + 1))

        return (
            update_relevant_components(
                id_list=real_filter_id,
                update_info=[{"new_value": real_list, "conditions": {}}],
            ),
            update_relevant_components(
                id_list=[real_string_id],
                update_info=[
                    {
                        "new_value": printable_int_list(real_list),
                        "conditions": {},
                    }
                ],
            ),
        )

    @callback(
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "element": "real-slider-wrapper",
            },
            "children",
        ),
        Input(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "element": "real-selector-option",
            },
            "value",
        ),
        State(plugin.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        State("webviz-content-manager", "activeViewId"),
    )
    def _update_realization_selected_info(
        input_selector: str,
        filters: dict,
        active_view_id: str,
    ) -> Component:
        if active_view_id == plugin.unverified_view_uuid(ElementIds.FipQC.ID):
            raise PreventUpdate

        reals = plugin.volumes_model.realizations
        prev_selection = filters.get("REAL", []) if filters is not None else None
        selected_component = input_selector
        selected_reals = prev_selection if prev_selection is not None else reals

        component = (
            wcc.RangeSlider(
                id={
                    "id": plugin.shared_settings_group(
                        ElementIds.SharedSettings.Filters.ID
                    )
                    .get_unique_id()
                    .to_string(),
                    "component_type": selected_component,
                },
                value=[min(selected_reals), max(selected_reals)],
                min=min(reals),
                max=max(reals),
                marks={str(i): {"label": str(i)} for i in [min(reals), max(reals)]},
            )
            if selected_component == "range"
            else wcc.SelectWithLabel(
                id={
                    "id": plugin.shared_settings_group(
                        ElementIds.SharedSettings.Filters.ID
                    )
                    .get_unique_id()
                    .to_string(),
                    "component_type": selected_component,
                },
                options=[{"label": i, "value": i} for i in reals],
                value=selected_reals,
                size=min(20, len(reals)),
            )
        )
        return component

    @callback(
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "region",
            },
            "value",
        ),
        Output(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "wrapper": ALL,
                "type": "region",
            },
            "style",
        ),
        Input(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "element": "region-selector",
            },
            "value",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "selector": ALL,
                "type": "region",
            },
            "id",
        ),
        State(plugin.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "wrapper": ALL,
                "type": "region",
            },
            "id",
        ),
        State(
            {
                "id": plugin.shared_settings_group(ElementIds.SharedSettings.Filters.ID)
                .get_unique_id()
                .to_string(),
                "element": "region-selector",
            },
            "id",
        ),
        prevent_initial_call=True,
    )
    def update_region_filters(
        selected_reg_filter: list,
        reg_filter_ids: list,
        filters: dict,
        wrapper_ids: list,
        reg_select_ids: list,
    ) -> tuple:
        """
        Callback to update the visible region filter between FIPNUM or ZONE/REGION.
        When changing, the active selection will be used to set the new selection.
        Note this callback will only be used for cases where each FIPNUM belongs to
        a unique ZONE and REGION.
        """
        selected = [
            value for id_value, value in zip(reg_select_ids, selected_reg_filter)
        ]

        df = plugin.volumes_model.dataframe

        values = {}
        if selected[0] != "fipnum":
            values["FIPNUM"] = df["FIPNUM"].unique()
            for elm in ["REGION", "ZONE"]:
                values[elm] = df.loc[df["FIPNUM"].isin(filters["FIPNUM"])][elm].unique()

        else:
            values["REGION"] = df["REGION"].unique()
            values["ZONE"] = df["ZONE"].unique()
            mask = (df["REGION"].isin(filters["REGION"])) & (
                df["ZONE"].isin(filters["ZONE"])
            )
            values["FIPNUM"] = df.loc[mask]["FIPNUM"].unique()

        styles = {}
        styles["FIPNUM"] = {"display": "none" if selected[0] != "fipnum" else "block"}
        styles["REGION"] = {"display": "none" if selected[0] == "fipnum" else "block"}
        styles["ZONE"] = {"display": "none" if selected[0] == "fipnum" else "block"}

        return (
            update_relevant_components(
                id_list=reg_filter_ids,
                update_info=[
                    {
                        "new_value": value,
                        "conditions": {"selector": selector},
                    }
                    for selector, value in values.items()
                ],
            ),
            update_relevant_components(
                id_list=wrapper_ids,
                update_info=[
                    {
                        "new_value": style,
                        "conditions": {"wrapper": selector},
                    }
                    for selector, style in styles.items()
                ],
            ),
        )

    if len(plugin.volumes_model.sources) > 1:

        @callback(
            Output(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.Settings.Controls.ID}",
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": "Ignore <",
                },
                "value",
            ),
            Input(
                {
                    "plugin_id": plugin.uuid(),
                    "settings_id": plugin.shared_settings_group(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.Settings.Controls.ID}",
                    )
                    .get_unique_id()
                    .to_string(),
                    "selector": "Response",
                },
                "value",
            ),
        )
        def _reset_ignore_value_source_comparison(_response_change: str) -> float:
            """reset ignore value when new response is selected"""
            return 0

    if len(plugin.volumes_model.ensembles) > 1 or plugin.volumes_model.sensrun:
        if len(plugin.volumes_model.ensembles) > 1:

            @callback(
                Output(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Controls.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": "Ignore <",
                    },
                    "value",
                ),
                Input(
                    {
                        "plugin_id": plugin.uuid(),
                        "settings_id": plugin.shared_settings_group(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.Settings.Controls.ID}",
                        )
                        .get_unique_id()
                        .to_string(),
                        "selector": "Response",
                    },
                    "value",
                ),
            )
            def _reset_ignore_value_ens_comparison(_response_change: str) -> float:
                """reset ignore value when new response is selected"""
                return 0
