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
            ID = "inplace_distributions_plots_per_zone_region"

        class ConvergencePlot:
            ID = "inplace_distributions_convergence_plot"

        class Settings:
            class PlotControls:
                ID = "inplace_distributions_plot_controls"

            class Filters:
                ID = "inplace_distributions_filters"

            class Settings:
                ID = "inplace_distributions_settings"

    class TornadoPlots:
        class Custom:
            ID = "tornado_plots_custom"

        class BulkVsStoiipGiip:
            ID = "tornado_plots_bulk"
