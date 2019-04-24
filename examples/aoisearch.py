import sensortools.aoisearch
from shapely.geometry import box
import json
import os

# Load in the gbdx search result json
data_dir = os.path.abspath(os.path.join('./data'))
gbdxsearch = os.path.join(data_dir, 'gbdxsearch_results.json')

with open(gbdxsearch, 'r') as f:
    results = json.load(f)

# Define AOI
aoi = box(-157.9, 21.3, -157.8, 21.4).wkt

# Using `formatSearchResults` -- converting the json of search results to a pandas dataframe
results_df = sensortools.aoisearch.formatSearchResults(results, aoi)

# Getting the overlap geometry -- `aoiFootprintIntersection`
intersection_shape = sensortools.aoisearch.aoiFootprintIntersection(results_df, aoi)

# Calculate overlap percentage -- `aoiFootprintPctCoverage`
intersect_pct = sensortools.aoisearch.aoiFootprintPctCoverage(results_df, aoi)
