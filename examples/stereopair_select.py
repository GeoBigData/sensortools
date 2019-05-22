from datetime import datetime, timedelta
import sensortools.gbdxaoi
import sensortools.stereosearch
import shapely.wkt
import json


# The earliest allowable acquisition date
start_date = datetime.strftime(datetime.now() - timedelta(days=365), '%Y-%m-%dT00:00:00.000Z')

# The latest allowable acquisition date
end_date = None

# The maximum allowable cloud cover in %. Use 100 for no filter.
max_cloud_cover = 10

# The maximum allowable difference in acquisition date (in days) between the two images
days_tolerance = 30

# The maximum allowable convergence angle (in degrees). 60 is the recommended value, but you can set
# this lower to limit results further. 20 seems to be ideal for machine learning, 40 for human-in-the-loop.
max_convergence = 60

# The minimum allowable convergence angle (in degrees). 20 is the recommended value, but you could go down
# to 15 to get more results.
min_convergence = 20

# The maximum allowable asymmetry angle (in degrees).
max_asymmetry = 30

# The maximum allowable roll angle (in degrees).
max_roll = 15

# The minimum allowable difference between the bisector elevation and the convergence angle.
min_bie_conv_diff = 15

# Restrict the results to either in-track stereo or cross-track stereo (or both)
track_type = 'both'  # Must be one of 'in-track', 'cross-track', 'both'

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
# Get the stereo pairs
##########
stereo_pairs = sensortools.stereosearch.find_stereo_pairs(
    results_df,
    aoi_geom,
    days_tolerance=days_tolerance,
    max_convergence=max_convergence,
    min_convergence=min_convergence,
    max_asymmetry=max_asymmetry,
    max_roll=max_roll,
    min_bie_conv_diff=min_bie_conv_diff,
    track_type=track_type
)

##########
# Cloud Cover df
##########
all_catids = set([
    catid
    for catid_pair in stereo_pairs.index.tolist()
    for catid in catid_pair
])

api_key = 'pP2aV9nVyt2BzJd4IUcfy8GXslhtWV4K3k9ILWxz'
clouds_shapes = sensortools.gbdxaoi.catidCloudCover(list(all_catids), api_key)

clouds_df = sensortools.gbdxaoi.aoiCloudCover(stereo_pairs, clouds_shapes, api_key)

##########
# Assign catids to AOI
##########
