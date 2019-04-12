# Sensortools

Python package containing functions for the Sales Engineer data allotment Notebook.

This package is set up as one class `Sensortools` with many methods attached.  

The methods included in this library by loose application area are:
* Converting GB to km^2 and vice versa
    * `gb_to_km2`
    * `km2_to_gb`
* Mapping Functions
    * `mapGB`
    * `mapAOI`
* GBDX result helpers & visualizations
    * `formatSearchResults`
    * `searchScatterPlot`
    * `searchBarPlot`
    * `searchVarPlot`
    * `searchSensorComparePlot`
    * `sarchDistPlot`
* AOI-related manipulations
    * `createAOI`
    * `createAOIfromGeoJSON`
    * `readSHP`
    * `aoiFootprintPctCoverage`
    * `mapSearchFootprintsAOI`
    * `aoiArea`
* Cloud coverage
    * `aoiCloudCover`
    * `mapClouds`
* Earthwatch
    * `EarthWatchLookup`
* Pricing tables
    * `setGBDXPricingTable`
    * `setIPPPricingTable`
    * `addCustomTier`
    * `deleteTier`
    * `editGBDXTier`
    * `editIPPTier`
    * `pricing`
    * `setSensorResolution`
    
The usage of any but not all of these functions is shown in scripts in the examples folder.
