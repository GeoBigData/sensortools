# Sensortools

Python package containing functions for formatting and visualizing GBDX search results for an AOI.

This package is set up as four modules:

    1.  map
        Functions relating to displaying aois or search results on a folium map
    2. plot
        Functions that take a dataframe of search results and display them in some type of chart
    3. convert
        Functions that convert between km^2 and GB of imagery across multiple sensors
    4. gbdxaoi
        Functions for formatting search results and comparing search results to an aoi

The methods included in each of the modules are:
* map.py
    * `mapGB`
    * `mapAOI`
    * `mapSearchFootprintsAOI`
    * `mapClouds`
* plot.py
    * `searchScatterPlot`
    * `searchBarPlot`
    * `searchVarPlot`
    * `searchSensorComparePlot`
    * `sarchDistPlot`
* convert.py
    * `gb_to_km2`
    * `km2_to_gb`
* gbdxaoi.py
    * `formatSearchResults`
    * `aoiFootprintIntersection`
    * `aoiFootprintPctCoverage`
    * `aoiCloudCover`

The usage of many of these functions is shown in scripts in the examples folder.
