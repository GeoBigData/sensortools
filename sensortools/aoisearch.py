import sensortools.tools.spatial as spatial_tools
from functools import partial
from shapely.ops import transform
import shapely
import pyproj


def aoifootprintcalculations(df, aoi):
    """
    Given an AOI and search results, determine percent of the AOI that is
    covered by all footprints
    """
    # projection info
    to_p = spatial_tools.getUTMProj(aoi)
    from_p = pyproj.Proj(init='epsg:4326')
    project = partial(pyproj.transform, from_p, to_p)

    # project the AOI, calc area
    aoi_shp = shapely.wkt.loads(aoi)
    aoi_shp_prj = transform(project, aoi_shp)
    aoi_km2 = aoi_shp_prj.area / 1000000.

    # union all the footprint shapes
    shps = []
    for i, row in df.iterrows():
        shps.append(shapely.wkt.loads(row['Footprint WKT']))
    footprints = shapely.ops.cascaded_union(shps)

    # project the footprint union
    footprints_prj = transform(project, footprints)

    # perform intersection and calculate area
    inter_shp_prj = aoi_shp_prj.intersection(footprints_prj)
    inter_km2 = inter_shp_prj.area / 1000000.
    pct = inter_km2 / aoi_km2 * 100.

    # project back to wgs84/wkt for mapping
    project_reverse = partial(pyproj.transform, to_p, from_p)
    inter_shp = transform(project_reverse, inter_shp_prj)
    inter_json = shapely.geometry.mapping(inter_shp)

    return [pct, inter_json]
