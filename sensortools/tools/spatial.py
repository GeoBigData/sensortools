from sensortools.decorators import ingest_wkt, ingest_latlon
import shapely
import shapely.wkt
import pyproj
import utm


@ingest_wkt
def convertAOItoLocation(aoi):
    """
    Convert a WKT Polygon to a Folium Point Location
    """

    shp = shapely.wkt.loads(aoi)
    coords = shp.centroid.coords.xy
    x, y = coords[0][-1], coords[1][-1]

    # returning as lat lon as that is required by folium
    return [y, x]


@ingest_wkt
def getUTMProj(aoi):
    """
    Determine the UTM Projection for an AOI
    """
    # get the centroid of the shape
    loc = convertAOItoLocation(aoi)
    # find the UTM info
    utm_def = utm.from_latlon(loc[0], loc[1])
    zone = utm_def[-2]
    # convert UTM zone info to something pyproj can understand
    if loc[0] < 0:
        hem = 'south'
    else:
        hem = 'north'
    to_p = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', hemisphere=hem)

    return to_p


@ingest_latlon
def getLLUTMProj(latitude, longitude):
    """
    Determine the UTM Projection for a LatLong
    """
    # find the UTM info
    utm_def = utm.from_latlon(latitude, longitude)
    zone = utm_def[-2]
    # convert UTM zone info to something pyproj can understand
    if latitude < 0:
        hem = 'south'
    else:
        hem = 'north'
    to_p = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', hemisphere=hem)

    return to_p
