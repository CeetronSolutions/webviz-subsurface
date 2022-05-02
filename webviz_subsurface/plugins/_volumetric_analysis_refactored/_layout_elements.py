# pylint: disable = too-few-public-methods
class ElementIds:
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

            class Filters:
                ID = "inplace_distributions_filters"

            class Settings:
                ID = "inplace_distributions_settings"

    class Tables:
        ID = "tables"
        TABLE = "table"
        DIV = "div"
        SETTING = "table_controls"

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
