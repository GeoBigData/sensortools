import sensortools.gbdxaoi
import shapely.wkt
import json

# Define AOI for Boulder
aoi_path = '/Users/rachelwegener/repos/sensortools/examples/boulder_wkt.txt'

with open(aoi_path, 'r') as f:
    aoi_wkt = f.read()

aoi_geom = shapely.wkt.loads(aoi_wkt)

# Open search results
results_path = '/Users/rachelwegener/data/tmp/results.json'
with open(results_path, 'r') as f:
    catalog_results = json.load(f)

##########
# Format the search results into a dataframe
##########
results_df = sensortools.gbdxaoi.formatSearchResults(catalog_results, aoi_wkt)

##########
# Cloud Cover df
##########
# Just get clouds shapes by catid
catids = list(results_df.index)
api_key = 'pP2aV9nVyt2BzJd4IUcfy8GXslhtWV4K3k9ILWxz'
cloud_shapes = sensortools.gbdxaoi.catidCloudCover(catids, api_key)
cloud_shapes_aoi = sensortools.gbdxaoi.catidCloudCover(catids, api_key, aoi=aoi_wkt)

# Get all cloud information for the aoi
results_clouds_aoi = sensortools.gbdxaoi.aoiCloudCover(results_df, api_key, aoi=aoi_wkt)
coverage_pct = sensortools.gbdxaoi.aoiFootprintPctCoverage(results_clouds_aoi, aoi_wkt)

# Or to just get general cloud information
results_full_clouds = sensortools.gbdxaoi.aoiCloudCover(results_df, api_key)

##########
# Assign catid to vector
##########
