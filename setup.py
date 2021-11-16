from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

TESTS_REQUIRE = [
    "bandit",
    "black>=21.4b0",
    "dash[testing]",
    "flaky",
    "isort",
    "mypy",
    "pylint",
    "pytest-xdist",
    "selenium>=3.141",
    "types-dataclasses>=0.1.5; python_version<'3.7'",
    "types-pkg-resources",
    "types-pyyaml",
]

# pylint: disable=line-too-long
setup(
    name="webviz-subsurface",
    description="Webviz config plugins for subsurface data",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/equinor/webviz-subsurface",
    author="R&T Equinor",
    packages=find_packages(exclude=["tests"]),
    package_data={
        "webviz_subsurface": [
            "_abbreviations/abbreviation_data/*.json",
            "_assets/css/*.css",
            "_assets/js/*.js",
            "ert_jobs/config_jobs/*",
        ]
    },
    entry_points={
        "webviz_config_plugins": [
            "BhpQc = webviz_subsurface.plugins:BhpQc",
            "DiskUsage = webviz_subsurface.plugins:DiskUsage",
            "GroupTree = webviz_subsurface.plugins:GroupTree",
            "HistoryMatch = webviz_subsurface.plugins:HistoryMatch",
            "HorizonUncertaintyViewer = webviz_subsurface.plugins:HorizonUncertaintyViewer",
            "InplaceVolumes = webviz_subsurface.plugins:InplaceVolumes",
            "InplaceVolumesOneByOne = webviz_subsurface.plugins:InplaceVolumesOneByOne",
            "LinePlotterFMU = webviz_subsurface.plugins:LinePlotterFMU",
            "MorrisPlot = webviz_subsurface.plugins:MorrisPlot",
            "ParameterAnalysis = webviz_subsurface.plugins:ParameterAnalysis",
            "ParameterCorrelation = webviz_subsurface.plugins:ParameterCorrelation",
            "ParameterDistribution = webviz_subsurface.plugins:ParameterDistribution",
            "ParameterParallelCoordinates = webviz_subsurface.plugins:ParameterParallelCoordinates",
            "ParameterResponseCorrelation = webviz_subsurface.plugins:ParameterResponseCorrelation",
            "PropertyStatistics = webviz_subsurface.plugins:PropertyStatistics",
            "PvtPlot = webviz_subsurface.plugins:PvtPlot",
            "RelativePermeability = webviz_subsurface.plugins:RelativePermeability",
            "ReservoirSimulationTimeSeries = webviz_subsurface.plugins:ReservoirSimulationTimeSeries",
            "ReservoirSimulationTimeSeriesOneByOne = webviz_subsurface.plugins:ReservoirSimulationTimeSeriesOneByOne",
            "ReservoirSimulationTimeSeriesRegional = webviz_subsurface.plugins:ReservoirSimulationTimeSeriesRegional",
            "RftPlotter = webviz_subsurface.plugins:RftPlotter",
            "RunningTimeAnalysisFMU = webviz_subsurface.plugins:RunningTimeAnalysisFMU",
            "SegyViewer = webviz_subsurface.plugins:SegyViewer",
            "SeismicMisfit = webviz_subsurface.plugins:SeismicMisfit",
            "StructuralUncertainty = webviz_subsurface.plugins:StructuralUncertainty",
            "SubsurfaceMap = webviz_subsurface.plugins:SubsurfaceMap",
            "SurfaceViewerFMU = webviz_subsurface.plugins:SurfaceViewerFMU",
            "SurfaceWithGridCrossSection = webviz_subsurface.plugins:SurfaceWithGridCrossSection",
            "SurfaceWithSeismicCrossSection = webviz_subsurface.plugins:SurfaceWithSeismicCrossSection",
            "TornadoPlotterFMU = webviz_subsurface.plugins:TornadoPlotterFMU",
            "VolumetricAnalysis = webviz_subsurface.plugins:VolumetricAnalysis",
            "WellCrossSection = webviz_subsurface.plugins:WellCrossSection",
            "WellCrossSectionFMU = webviz_subsurface.plugins:WellCrossSectionFMU",
            "AssistedHistoryMatchingAnalysis = webviz_subsurface.plugins:AssistedHistoryMatchingAnalysis",
            "WellCompletions = webviz_subsurface.plugins:WellCompletions",
            "WellLogViewer = webviz_subsurface.plugins:WellLogViewer",
        ],
        "console_scripts": ["smry2arrow_batch=webviz_subsurface.smry2arrow_batch:main"],
    },
    install_requires=[
        "dash>=2.0.0",
        "dash_bootstrap_components>=0.10.3",
        "dash-daq>=0.5.0",
        "dataclasses>=0.8; python_version<'3.7'",
        "defusedxml>=0.6.0",
        "ecl2df>=0.15.0; sys_platform=='linux'",
        "fmu-ensemble>=1.2.3",
        "fmu-tools>=1.8",
        "jsonschema>=3.2.0",
        "opm>=2020.10.1; sys_platform=='linux'",
        "pandas>=1.1.5",
        "pillow>=6.1",
        "pyarrow>=5.0.0",
        "pyscal>=0.7.5",
        "scipy>=1.2",
        "statsmodels>=0.12.1",  # indirect dependency through https://plotly.com/python/linear-fits/
        "webviz-config>=0.3.1",
        "webviz-core-components>=0.5.1",
        "webviz-subsurface-components>=0.4.7",
        "xtgeo>=2.14",
    ],
    extras_require={"tests": TESTS_REQUIRE},
    setup_requires=["setuptools_scm~=3.2"],
    python_requires="~=3.6",
    use_scm_version=True,
    zip_safe=False,
    project_urls={
        "Documentation": "https://equinor.github.io/webviz-subsurface",
        "Download": "https://pypi.org/project/webviz-subsurface/",
        "Source": "https://github.com/equinor/webviz-subsurface",
        "Tracker": "https://github.com/equinor/webviz-subsurface/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Environment :: Web Environment",
        "Framework :: Dash",
        "Framework :: Flask",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
