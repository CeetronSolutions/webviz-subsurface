from typing import List, Dict, Union, Tuple, Callable
from pathlib import Path
import json

from dash import html, Dash
from webviz_config import WebvizPluginABC
import webviz_core_components as wcc
from webviz_subsurface_components import WellLogViewer as WellLogViewerComponent

from webviz_subsurface._models.well_set_model import WellSetModel
from webviz_subsurface._utils.webvizstore_functions import find_files, get_path
from .controllers import well_controller
from ._validate_log_templates import load_and_validate_log_templates


class WellLogViewer(WebvizPluginABC):
    """Uses [videx-welllog](https://github.com/equinor/videx-wellog) to visualize well logs
    from files stored in RMS well format.

?> Currently tracks for visualizing discrete logs are not included. This will
be added in later releases.

---

* **`wellfolder`:** Path to a folder with well files stored in RMS well format.
* **`wellsuffix`:** File suffix of well files
* **`logtemplates`:** List of yaml based log template configurations. \
    See the data section for description of the format.
* **`mdlog`:** Name of the md log. If not specified, MD will be calculated.
* **`well_tvdmin`:** Truncate well data values above this depth.
* **`well_tvdmax`:** Truncate well data values below this depth.
* **`well_downsample_interval`:** Sampling interval used for coarsening a well trajectory
* **`initial_settings`:** Configuration for initializing the plugin with various \
    properties set. All properties are optional.
    See the data section for available properties.

---

?> The format and documentation of the log template configuration will be improved \
in later releases. A small configuration sample is provided below.

```yaml
name: All logs # Name of the log template
scale:
  primary: MD # Which reference track to visualize as default (MD/TVD)
  allowSecondary: False # Set to True to show both MD and TVD reference tracks.
tracks: # The list of log tracks
  - title: Porosity # Optional title of log track
    plots: # List of which logs to include in the track
      - name: PHIT # Upper case name of log
        type: area # Type of visualiation (area, line, linestep, dot)
        color: green # Color of log
      - name: PHIT_ORIG
        type: line
  - plots:
      - name: ZONE
        type: area
  - plots:
      - name: FACIES
        type: area
  - plots:
      - name: VSH
        type: area
  - plots:
      - name: SW
        type: dot
styles: # List of styles that can be added to tracks
```


Format of the `initial_settings` argument:
```yaml
        initial_settings:
            well: str # Name of well
            logtemplate: str # Name of log template
```
"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        app: Dash,
        wellfolder: Path,
        logtemplates: List[Path],
        wellsuffix: str = ".w",
        mdlog: str = None,
        well_tvdmin: Union[int, float] = None,
        well_tvdmax: Union[int, float] = None,
        well_downsample_interval: int = None,
        initial_settings: Dict = None,
    ):

        super().__init__()
        self._wellfolder = wellfolder
        self._wellsuffix = wellsuffix
        self._logtemplatefiles = logtemplates
        self._wellfiles: List = json.load(
            find_files(folder=self._wellfolder, suffix=self._wellsuffix)
        )
        self._log_templates = load_and_validate_log_templates(
            [get_path(fn) for fn in self._logtemplatefiles]
        )
        self._well_set_model = WellSetModel(
            self._wellfiles,
            mdlog=mdlog,
            tvdmin=well_tvdmin,
            tvdmax=well_tvdmax,
            downsample_interval=well_downsample_interval,
        )
        self._initial_settings = initial_settings if initial_settings else {}
        self.set_callbacks(app)

    @property
    def layout(self) -> html.Div:
        return wcc.FlexBox(
            [
                wcc.Frame(
                    style={"height": "90vh", "flex": 1},
                    children=[
                        wcc.Dropdown(
                            label="Well",
                            id=self.uuid("well"),
                            options=[
                                {"label": name, "value": name}
                                for name in self._well_set_model.well_names
                            ],
                            value=self._initial_settings.get(
                                "well_name", self._well_set_model.well_names[0]
                            ),
                            clearable=False,
                        ),
                        wcc.Dropdown(
                            label="Log template",
                            id=self.uuid("template"),
                            options=[
                                {"label": name, "value": name}
                                for name in list(self._log_templates.keys())
                            ],
                            value=self._initial_settings.get(
                                "logtemplate", list(self._log_templates.keys())[0]
                            ),
                            clearable=False,
                        ),
                    ],
                ),
                wcc.Frame(
                    style={"flex": 6, "height": "90vh"},
                    children=[
                        WellLogViewerComponent(
                            id=self.uuid("well-log-viewer"),
                            template=self._log_templates[
                                list(self._log_templates.keys())[0]
                            ],
                        )
                    ],
                ),
            ]
        )

    def set_callbacks(self, app: Dash) -> None:
        well_controller(
            app=app,
            well_set_model=self._well_set_model,
            log_templates=self._log_templates,
            get_uuid=self.uuid,
        )

    def add_webvizstore(self) -> List[Tuple[Callable, list]]:
        store_functions = [
            (find_files, [{"folder": self._wellfolder, "suffix": self._wellsuffix}])
        ]
        store_functions.extend([(get_path, [{"path": fn}]) for fn in self._wellfiles])
        store_functions.extend(
            [(get_path, [{"path": fn}]) for fn in self._logtemplatefiles]
        )
        return store_functions
