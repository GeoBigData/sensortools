from shapely.geometry import box
import fiona
from sensortools import sensortools
from gbdxtools import Interface
import os

st = sensortools()
gbdx = Interface()

# Load in AOI
data_dir = os.path.abspath(os.path.join('./data'))
japan_path = os.path.join(data_dir, 'japan_urban.shp')
with fiona.open(japan_path) as src:
    crs = src.crs
    aoi = box(*src.bounds).wkt

# Search parameters
start_date = '2017-01-20T00:00:00.000Z'
end_date = '2017-12-01T00:00:00.000Z'
filters = None
types = ['DigitalGlobeAcquisition']


results = gbdx.catalog.search(searchAreaWkt=aoi, startDate=start_date, endDate=end_date, types=types)
df = st.formatSearchResults(results, aoi)

df2 = df.iloc[[0, 9, 16, 17, 18]]

df_clouds = st.aoiCloudCover(df2, aoi)

