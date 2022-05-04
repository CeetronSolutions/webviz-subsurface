# pylint: disable = too-few-public-methods
class ElementIds:
    class Stores:
        FILTERS = "filters"
        INPLACE_DISTRIBUTIONS = "inplace_distributions"
        TABLES = "tables"
        TORNADO_PLOTS = "tornado_plots"
        COMPARISON = "comparison"

    class InplaceDistributions:
        class CustomPlotting:
            ID = "custom_plots"

            class Plot:
                ID = "plot"
                GRAPH = "graph"

            class ResponseTable:
                ID = "statistics_response_table"
                TABLE = "table"

            class PropertyTable:
                ID = "statistics_property_table"
                TABLE = "table"

        class PlotsPerZoneRegion:
            ID = "plots_per_zone_region"

            GRAPH = "graph"

            class ZonePlot:
                BAR_PLOT = "zone_bar_plot"
                PIE_PLOT = "zone_pie_plot"

            class RegionPlot:
                BAR_PLOT = "zone_bar_plot"
                PIE_PLOT = "zone_pie_plot"

            class FaciesPlot:
                BAR_PLOT = "zone_bar_plot"
                PIE_PLOT = "zone_pie_plot"

            class FipNumPlot:
                BAR_PLOT = "zone_bar_plot"
                PIE_PLOT = "zone_pie_plot"

            class SetPlot:
                BAR_PLOT = "zone_bar_plot"
                PIE_PLOT = "zone_pie_plot"

        class ConvergencePlot:
            ID = "convergence_plot"

            class Plot:
                ID = "plot"
                GRAPH = "graph"

        class Settings:
            class PlotControls:
                ID = "inplace_distributions_plot_controls"

            class Settings:
                ID = "inplace_distributions_settings"

    class Tables:
        ID = "tables"
        TABLE = "table"
        DIV = "div"
        SETTING = "table_controls"

    class EnsembleComparison:
        ID = "ensemble_comparison"

        class Settings:
            ID = "settings"

    class SensitivityComparison:
        ID = "sensitivity_comparison"

        class Settings:
            ID = "settings"

    class Comparison:
        class SourceComparison:
            ID = "source_comparison"

        class EnsembleComparison:
            ID = "ensemble_comparison"

        class SensitivityComparison:
            ID = "sensitivity_comparison"

        class QCPlots:
            ID = "qc_plots"

            PLOT_DIFF_VS_RESPONSE = "diff_vs_response"
            PLOT_CORRELATION = "correlation"
            HIGHLIGHTED_DATA = "highlighted_data"

        class DiffTableSelectedResponse:
            ID = "diff_table_selected_response"

        class DiffTableMultipleResponses:
            ID = "diff_table_multiple_responses"

        GRAPH = "graph"

        class Settings:
            class Controls:
                ID = "controls"

            class Settings:
                ID = "settings"

    class FipQC:
        ID = "fipqc"

    class TornadoPlots:
        class Custom:
            ID = "tornado_plots_custom"

            class Plots:
                ID = "plot"
                GRAPHS = "graphs"

            class Tables:
                ID = "statistics_response_table"
                TABLES = "tables"

        class BulkVsStoiipGiip:
            ID = "tornado_plots_bulk"

        class Settings:
            class TornadoControls:
                ID = "tornado_controls"

            class Settings:
                ID = "tornado_settings"

    class SharedSettings:
        class Filters:
            ID = "inplace_distributions_filters"
