# pylint: disable = too-few-public-methods
class ElementIds:
    class Stores:
        FILTERS = "filters"
        INPLACE_DISTRIBUTIONS = "inplace_distributions"
        TABLES = "tables"
        TORNADO_PLOTS = "tornado_plots"

    class InplaceDistributions:
        NAME = "Inplace distributions"

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

    class Comparison:
        class SourceComparison:
            NAME = "Source comparison"
            ID = "source_comparison"

        class EnsembleComparison:
            NAME = "Ensemble comparison"
            ID = "ensemble_comparison"

        class SensitivityComparison:
            NAME = "Sensitivity comparison"
            ID = "sensitivity_comparison"

        class QCPlots:
            ID = "qc_plots"

            ROW = "row"

            PLOT_DIFF_VS_REAL = "diff_vs_real"
            PLOT_DIFF_VS_RESPONSE = "diff_vs_response"
            PLOT_CORRELATION = "correlation"
            HIGHLIGHTED_DATA = "highlighted_data"

        class DiffTableSelectedResponse:
            ID = "diff_table_selected_response"

            VIEW_TABLE = "view_table"

        class DiffTableMultipleResponses:
            ID = "diff_table_multiple_responses"

        GRAPH = "graph"
        TABLE = "table"
        HEADER = "header"
        SELECTION = "selection"
        FILTER = "filter"
        TABLE = "table"

        class Settings:
            class Controls:
                ID = "controls"

            class Settings:
                ID = "settings"

    class FipFile:
        NAME = "Fipfile QC"

        class QCPlots:
            ID = "fip_file_qc_plots"
            ZONE_REGION_HEATMAP = "zone_region_heatmap"
            ZONE_FIPNUM_HEATMAP = "zone_fipnum_heatmap"
            REGION_FIPNUM_HEATMAP = "region_fipnum_heatmap"


    class TornadoPlots:
        NAME = "Tornadoplots"

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
