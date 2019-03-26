import shapely
import pyproj
import utm


def convertAOItoLocation(aoi):
    """
    Convert a WKT Polygon to a Folium Point Location
    """

    shp = shapely.wkt.loads(aoi)
    coords = shp.centroid.coords.xy
    x, y = coords[0][-1], coords[1][-1]

    # returning as lat lon as that is required by folium
    return [y, x]


def getUTMProj(aoi):
    """
    Determine the UTM Proj for an AOI
    """
    # convert AOI to shape
    shp = shapely.wkt.loads(aoi)
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


def getLLUTMProj(latitude, longitude):
    """
    Determine the UTM Proj for a LatLong
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
