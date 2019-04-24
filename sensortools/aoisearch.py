import sensortools.tools.spatial as spatial_tools
from functools import partial
from shapely.geos import TopologicalError
from shapely.ops import transform
import shapely.geometry
import shapely.wkt
from .exceptions import *
import pandas as pd
import numpy as np
import requests
import shapely
import pyproj
import json


def _fpaoiintersect(fp_wkt, aoi):
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


def formatSearchResults(search_results, aoi):
    """
    Format the results into a pandas df. To be used in plotting functions
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
        i.append(_fpaoiintersect(re['properties']['footprintWkt'], aoi))
        k.append(spatial_tools.aoiArea(re['properties']['footprintWkt']))

    df = pd.DataFrame({
        'image_identifier': ids,
        'catalog_id': cat,
        'Sensor': s,
        'Pan Resolution': pr,
        'MS Resolution': mr,
        'Date': pd.to_datetime(t),
        'Cloud Cover': c,
        'Off Nadir Angle': n,
        'Sun Elevation': e,
        'Target Azimuth': ta,
        'Footprint WKT': f,
        'Footprint Area (km2)': k,
        'Footprint AOI Inter Percent': i},
        index=pd.to_datetime(t))
    df.sort_values(['Date'], inplace=True)
    # for some reason, search results spit back geoms that do not intersect
    # the aoi... so must remove 0's
    df = df[df['Footprint AOI Inter Percent'] != 0]

    df['x'] = range(len(df))

    return df


def aoiFootprintIntersection(df, aoi):
    """
    Given an AOI and search results, determine percent of the AOI that is
    covered by all footprints
    ----------
    FORMERLY aoiFootprintCalculations
    returned pct (% overlap) as first argument and `inter_json` as the second argument
    Note: pct (% overlap) can still be calculated using the aoiFootprintPctCoverage function
    """
    # # projection info
    to_p = spatial_tools.getUTMProj(aoi)
    from_p = pyproj.Proj(init='epsg:4326')

    # project the AOI
    aoi_shp_prj = spatial_tools.utm_reproject_vector(aoi)

    # union all the footprint shapes
    shps = []
    for i, row in df.iterrows():
        shps.append(shapely.wkt.loads(row['Footprint WKT']))
    footprints = shapely.ops.cascaded_union(shps)

    # project the footprint union
    footprints_prj = spatial_tools.utm_reproject_vector(footprints.wkt)

    # perform intersection
    inter_shp_prj = aoi_shp_prj.intersection(footprints_prj)

    # project back to wgs84/wkt for mapping
    project_reverse = partial(pyproj.transform, to_p, from_p)
    inter_shp = transform(project_reverse, inter_shp_prj)
    inter_json = shapely.geometry.mapping(inter_shp)

    return inter_json


def aoiFootprintPctCoverage(df, aoi):
    """
    Return the percent area covered from aoi footprint calculation
    """
    # union all the footprint shapes and project to utm
    shps = []
    for i, row in df.iterrows():
        shps.append(shapely.wkt.loads(row['Footprint WKT']))
    footprints = shapely.ops.cascaded_union(shps)

    # Take the intersection of the aoi and the footprints and calculate %
    pct = _fpaoiintersect(footprints.wkt, aoi)

    return pct


def aoiCloudCover(df, aoi):
    """
    For each footprint in the search results, calculate a percent cloud
    cover for the AOI (instead of entire strip)
    """
    try:
        with open('duc-api.txt', 'r') as a:
            api_key = a.readlines()[0].rstrip()
    except IOError:
        raise MissingDUCAPIkeyError('Could not find DUC API key in ./duc-api.txt')
    except IndexError:
        raise DUCAPIkeyFormattingError('Could not find text in ./duc-api.txt')

    # projection info
    to_p = spatial_tools.getUTMProj(aoi)
    from_p = pyproj.Proj(init='epsg:4326')
    project = partial(pyproj.transform, from_p, to_p)

    # project the AOI, calc area
    aoi_shp_prj = spatial_tools.utm_reproject_vector(aoi)

    # add column to search df
    df['AOI Cloud Cover'] = 0
    df['Cloud WKT'] = ''

    # search the results, do not submit catids with 0 cloud cover
    catids = df[df['Cloud Cover'] > 0].catalog_id.values

    # split catids into groups of 50 so API doesn't choke
    cat_arr = np.array_split(catids, np.ceil(len(catids) / 50.))

    # iterate over groups of 50
    for cats in cat_arr:
        # send request to DUC database
        url = "https://api.discover.digitalglobe.com/v1/services/cloud_cover/MapServer/0/query"
        headers = {
            'x-api-key': "{api_key}".format(api_key=api_key),
            'content-type': "application/x-www-form-urlencoded"
        }
        data = {
            'outFields': '*',
            'where': "image_identifier IN ({cat})".format(cat="'" + "','".join(cats) + "'"),
            'outSR': '4326',
            'f': 'geojson'
        }
        response = requests.request("POST", url, headers=headers, data=data)
        clouds = json.loads(response.text)

        try:
            # iterate over the clouds and perform cloud cover percent
            for feature in clouds['features']:
                # get catalog id
                c = feature['properties']['image_identifier']

                # get the footprint shape
                fp = shapely.wkt.loads(df.loc[df['catalog_id'] == c, 'Footprint WKT'].values[0])
                fp_prj = transform(project, fp)

                # intersect the AOI with the footprint
                # using this as intersection with clouds
                aoi_fp_inter = aoi_shp_prj.intersection(fp_prj)
                aoi_fp_inter_km2 = aoi_fp_inter.area / 1000000.

                # extract the clouds and conver to shape
                cloud = shapely.geometry.shape(feature['geometry'])
                cloud_prj = transform(project, cloud)

                # perform intersection and calculate area
                try:
                    inter_shp_prj = aoi_fp_inter.intersection(cloud_prj)
                except TopologicalError:
                    cloud_prj = cloud_prj.buffer(0.0)
                    inter_shp_prj = aoi_fp_inter.intersection(cloud_prj)

                inter_km2 = inter_shp_prj.area / 1000000.

                pct = inter_km2 / aoi_fp_inter_km2 * 100.

                # update the dataframe
                df.loc[df['catalog_id'] == c, 'AOI Cloud Cover'] = pct
                df.loc[df['catalog_id'] == c, 'Cloud WKT'] = cloud.wkt
        except KeyError:
            # no clouds, move on...
            print('Warning, No Clouds Found...')

    return df
