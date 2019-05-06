from datetime import datetime, timedelta
import shapely.wkt
import json

from gbdxtools import Interface

###############
# Establish Search Criteria and Query GBDX
###############

# The earliest allowable acquisition date
start_date = datetime.strftime(datetime.now() - timedelta(days=365), '%Y-%m-%dT00:00:00.000Z')

# The latest allowable acquisition date
end_date = None

# The maximum allowable cloud cover in %. Use 100 for no filter.
max_cloud_cover = 10

# Define AOI for Boulder
aoi_path = '/Users/rachelwegener/repos/sensortools/examples/boulder_wkt.txt'

with open(aoi_path, 'r') as f:
    aoi_wkt = f.read()

aoi_geom = shapely.wkt.loads(aoi_wkt)

# Query Catalog
gbdx = Interface()

catalog_results = gbdx.catalog.search(
    searchAreaWkt=aoi_wkt,
    startDate=start_date,
    endDate=end_date,
    types=['DigitalGlobeAcquisition'],
    filters=['cloudCover < {}'.format(max_cloud_cover)]
)

print('Found {} catalog results.'.format(len(catalog_results)))

results_path = '/Users/rachelwegener/data/tmp/results.json'
with open(results_path, 'w') as f:
    f.write(json.dumps(catalog_results))
