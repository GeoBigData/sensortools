import sensortools.tools.spatial as spatial_tools
from shapely.ops import transform
import shapely.geometry
import shapely.wkt
import geopandas as gpd
import pandas as pd
import numpy as np
import requests
import shapely


def _intersectpct(fp_wkt, aoi):
    """
    Calculate the percent intersection of a footprint wkt and an AOI
    """
    # The projected aoi
    aoi_shp_prj = spatial_tools.utm_reproject_vector(aoi)

    # The projected footprint
    ft_shp_prj = spatial_tools.utm_reproject_vector(fp_wkt)

    # Intersect the two shapes
    inter_km2 = aoi_shp_prj.intersection(ft_shp_prj).area / 1000000.

    # Calculate area in km2
    pct = inter_km2 / spatial_tools.aoiArea(aoi) * 100.

    return pct


def formatSearchResults(search_results, aoi=None):
    """
    Format the results into a geopandas df. To be used in plotting functions
    but also useful outside of them.
    """
    ids, cat, s, pr, mr, t, c, n, e, f, i, k, ta = [], [], [], [], [], [], [], [], [], [], [], [], []
    for j, re in enumerate(search_results):
        ids.append(re['identifier'])
        cat.append(re['properties'].get('catalogID'))
        s.append(re['properties']['sensorPlatformName'])
        pr.append(re['properties'].get('panResolution'))
        mr.append(re['properties'].get('multiResolution'))
        ta.append(re['properties'].get('targetAzimuth'))
        t.append(re['properties']['timestamp'])
        # Catches for Landsat and RadarSat images missing these properties
        try:
            c.append(re['properties']['cloudCover'])
        except KeyError:
            c.append(0)
        try:
            n.append(re['properties']['offNadirAngle'])
        except KeyError:
            n.append(0)
        try:
            e.append(re['properties']['sunElevation'])
        except KeyError:
            e.append(0)
        f.append(re['properties']['footprintWkt'])
        if aoi:
            i.append(_intersectpct(re['properties']['footprintWkt'], aoi))
        k.append(spatial_tools.aoiArea(re['properties']['footprintWkt']))

    df = pd.DataFrame({
        'image_identifier': ids,
        'catalog_id': cat,
        'sensor': s,
        'pan_resolution': pr,
        'ms_resolution': mr,
        'timestamp': pd.to_datetime(t),
        'cloud_cover': c,
        'off_nadir_angle': n,
        'sun_elevation': e,
        'target_azimuth': ta,
        'footprint_geometry': list(map(shapely.wkt.loads, f)),
        'footprint_area(km2)': k,
        })
    if aoi:
        df = df.join(pd.DataFrame({'footprint_aoi_intersect_percent': i}))
        # for some reason, search results spit back geoms that do not intersect
        # the aoi... so must remove 0's
        df = df[df['footprint_aoi_intersect_percent'] != 0]
    # Reformat to geopandas df and set index as catalog_id
    df = gpd.GeoDataFrame(df, geometry='footprint_geometry')
    df = df.set_index('catalog_id')
    return df


def aoiFootprintIntersection(df, aoi, geom_column='footprint_geometry'):
    """
    Given an AOI and search results dataframe, return a shapely object of the intersection between the search results
    and the aoi.  Use the geometry column specified by `geom_column`
    :param df:
    :param aoi:
    :param geom_column: The string name of the column which should be used for the footprint shape geometry.  Shape
    geometries should be represented in the dataframe as shapely objects
    ----------
    FORMERLY aoiFootprintCalculations
    returned pct (% overlap) as first argument and `inter_json` as the second argument
    Note: pct (% overlap) can still be calculated using the aoiFootprintPctCoverage function
    """
    # union all the footprint shapes
    footprints = shapely.ops.cascaded_union([row[geom_column] for _, row in df.iterrows()])

    # perform intersection
    aoi = shapely.wkt.loads(aoi)
    intersection_shp = aoi.intersection(footprints)

    return intersection_shp


def aoiFootprintPctCoverage(df, aoi, geom_column='footprint_geometry'):
    """
    Return the percent area covered from aoi footprint calculation
    :param df:
    :param aoi:
    :param geom_column: The string name of the column which should be used for the footprint shape geometry.  Shape
    geometries should be represented in the dataframe as shapely objects
    """
    # union all the footprint shapes and project to utm
    footprints = shapely.ops.cascaded_union([row[geom_column] for _, row in df.iterrows()])

    # Take the intersection of the aoi and the footprints and calculate %
    pct = _intersectpct(footprints.wkt, aoi)

    # Print out a nice little print statement
    print('{cov_percent}% of the AOI is covered using {n_images} images'.format(
        n_images=df.shape[0],
        cov_percent=pct
    ))

    return pct


def catidCloudCover(catids, api_key, aoi=None):
    """
    For each catid in the catids list, query the DUC database to get the cloud cover polygon
    -------
    `get_clouds` from Jon's notebook
    """
    # Split catids into groups of 50 so API doesn't choke
    cat_arr = np.array_split(catids, np.ceil(len(catids) / 50.))

    # Send requests to DUC database in groups of 50
    url = "https://api.discover.digitalglobe.com/v1/services/cloud_cover/MapServer/0/query"
    headers = {
        'x-api-key': "{api_key}".format(api_key=api_key),
        'content-type': "application/x-www-form-urlencoded"
    }
    cloud_shapes = {}
    for cats in cat_arr:
        data = {
            'outFields': '*',
            'where': "image_identifier IN ({})".format(', '.join(["'{}'".format(catid) for catid in cats])),
            'outSR': '4326',
            'f': 'geojson'
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        for catid in catids:
            result = next(
                feature
                for feature in response.json()['features']
                if feature['properties']['image_identifier'] == catid
            )
            if result['geometry'] is None:
                cloud_shapes[catid] = None
            else:
                full_cloud_geom = shapely.geometry.shape(result['geometry'])
                if aoi:
                    aoi_geom = shapely.wkt.loads(aoi)
                    final_geom = full_cloud_geom.difference(aoi_geom)
                else:
                    final_geom = full_cloud_geom
                cloud_shapes[catid] = final_geom
    return cloud_shapes


def aoiCloudCover(df, api_key, aoi=None):
    """Automatically grab catids from a dataframe, get cloud shape from them, and append a new cloud column to df"""
    def add_cloud_footprint(row):
        cloud_polygons = []
        catid = row.name
        clouds = cloud_shapes[catid]
        if not clouds:
            pass
        elif clouds.geom_type == 'MultiPolygon':
            cloud_polygons += clouds.geoms
        else:
            cloud_polygons.append(clouds)
        row[cloud_name] = shapely.ops.cascaded_union(cloud_polygons)
        return row

    def add_cloud_free_footprint(row):
        row[cloud_free_name] = row['footprint_geometry'].difference(row[cloud_name])
        return row

    def add_aoi_coverage_pct(row):
        return 100*row['cloud_geom_aoi'].area / shapely.wkt.loads(aoi).area

    catids = list(df.index)
    if aoi:
        cloud_shapes = catidCloudCover(catids, api_key, aoi=aoi)
        cloud_name, cloud_free_name = 'cloud_geom_aoi', 'cloud_free_geom_aoi'
    else:
        cloud_shapes = catidCloudCover(catids, api_key)
        cloud_name, cloud_free_name = 'cloud_geom', 'cloud_free_geom'

    df = df.apply(add_cloud_footprint, axis=1)
    df = df.apply(add_cloud_free_footprint, axis=1)
    if aoi:
        df.apply(add_aoi_coverage_pct, axis=1)

    return df
