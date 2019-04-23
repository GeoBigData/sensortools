import sensortools.tools.spatial as spatial_tools
import sensortools.aoisearch
import sensortools.convert
import shapely.geometry
import shapely.wkt
import numpy as np
import folium


def _sensor_info():
    return {
            'GE01_Pan': {
                'resolution': 0.41,
                'band_count': 1,
                'plot_color': '#fd8d3c'
            },
            'GE01_MS': {
                'resolution': 1.64,
                'band_count': 4,
                'plot_color': '#fdbe85'
            },
            'GE01_PanSharp': {
                'resolution': 0.41,
                'band_count': 4,
                'plot_color': '#fdbe85'
            },
            'WV01_Pan': {
                'resolution': 0.5,
                'band_count': 1,
                'plot_color': '#969696'
            },
            'WV02_Pan': {
                'resolution': 0.46,
                'band_count': 1,
                'plot_color': '#3182bd'
            },
            'WV02_MS': {
                'resolution': 1.85,
                'band_count': 8,
                'plot_color': '#6baed6'
            },
            'WV02_PanSharp': {
                'resolution': 0.46,
                'band_count': 8,
                'plot_color': '#6baed6'
            },
            'WV03_Pan': {
                'resolution': 0.31,
                'band_count': 1,
                'plot_color': '#006d2c'
            },
            'WV03_MS': {
                'resolution': 1.24,
                'band_count': 8,
                'plot_color': '#31a354'
            },
            'WV03_SWIR': {
                'resolution': 3.7,
                'band_count': 8,
                'plot_color': '#74c476'
            },
            'WV03_PanSharp': {
                'resolution': 0.31,
                'band_count': 8,
                'plot_color': '#bae4b3'
            },
            'WV04_Pan': {
                'resolution': 0.31,
                'band_count': 1,
                'plot_color': '#756bb1'
            },
            'WV04_MS': {
                'resolution': 1.24,
                'band_count': 4,
                'plot_color': '#9e9ac8'
            },
            'WV04_PanSharp': {
                'resolution': 0.31,
                'band_count': 4,
                'plot_color': '#9e9ac8'}
            }


def _fpStyleFunction():
    """
    Style Function for Footprints
    """
    return {
        'fillOpacity': 0.0,
        'weight': 1,
        'fillColor': 'red',
        'color': 'red',
        'opacity': 0.5
    }


def _fpUnionStyleFunction():
    """
    Style Function for Unioned Footprints
    """
    return {
        'fillOpacity': 0.75,
        'weight': 1,
        'fillColor': 'green',
        'color': 'green',
        'opacity': 0.5
    }


def _CloudStyleFunction():
    """
    Style Function for Footprints
    """
    return {
        'fillOpacity': 0.5,
        'weight': 1,
        'fillColor': 'blue',
        'color': 'blue',
        'opacity': 0.5
    }


def mapGB(gb=None, aoi=(39.742043, -104.991531)):
    """
    Function to map GB to sensor areas given bands and resolution
    User can input a point lon, lat or the Polygon AOI from which
    a centroid  will be calculated
    Example
    -------
    from sensortools import map
    map.mapGB(100)
    """
    # convert GB to df
    df = sensortools.convert.gb_to_km2(gb)

    df = df.sort_values(by=['Area (km2)'], ascending=False)

    # if user passes in Polygon AOI, convert to Folium location
    if isinstance(aoi, str):
        aoi = spatial_tools.convertAOItoLocation(aoi)

    # TODO: add legend
    # TODO: could add some logic to control zoom level
    # TODO: add more info to popup, such as area
    # TODO: add pansharpened area calculation and plot on map
    m = folium.Map(location=aoi, zoom_start=8, tiles='Stamen Terrain')
    for i, row in df.iterrows():
        folium.Circle(
            radius=np.sqrt(row['Area (km2)'] / np.pi) * 1000,
            location=aoi,
            tooltip=row['Sensor'],
            color=_sensor_info()[row['Sensor']]['plot_color'],
            fill=False,
        ).add_to(m)

    return m


def mapAOI(aoi):
    """
    Mapping function to show the area of a user defined AOI
    """
    # turn WKT AOI into something folium can read
    shp = shapely.wkt.loads(aoi)
    geojson = shapely.geometry.mapping(shp)
    # calculate centroid of AOI as starting location
    aoi = spatial_tools.convertAOItoLocation(aoi)
    # create simple map
    m = folium.Map(location=aoi, zoom_start=8, tiles='Stamen Terrain')
    folium.GeoJson(
        geojson,
        name='geojson'
    ).add_to(m)

    return m


def mapSearchFootprintsAOI(df, aoi):
    """
    Map the footprints of the results in relation to the AOI
    """

    shp = shapely.wkt.loads(aoi)
    geojson = shapely.geometry.mapping(shp)
    loc = spatial_tools.convertAOItoLocation(aoi)
    m = folium.Map(location=loc, zoom_start=8, tiles='Stamen Terrain')
    folium.GeoJson(
        geojson,
        name='geojson'
    ).add_to(m)
    for i, row in df.iterrows():
        shp = shapely.wkt.loads(row['Footprint WKT'])
        geojson = shapely.geometry.mapping(shp)
        folium.GeoJson(
            geojson,
            style_function=_fpStyleFunction,
            name=str(i)
        ).add_to(m)

    # add the union footprints to map
    fp_json = sensortools.aoisearch.aoifootprintcalculations(df, aoi)[1]
    folium.GeoJson(
        fp_json,
        style_function=_fpUnionStyleFunction,
    ).add_to(m)

    return m


def mapClouds(df, aoi):
    """
    Given formatted search results with cloud cover WKT, map against AOI
    Caution: should limit how many results are mapped
    """

    shp = shapely.wkt.loads(aoi)
    geojson = shapely.geometry.mapping(shp)
    loc = spatial_tools.convertAOItoLocation(aoi)
    m = folium.Map(location=loc, zoom_start=8, tiles='Stamen Terrain')
    folium.GeoJson(
        geojson,
        name='geojson'
    ).add_to(m)

    for i, row in df.iterrows():
        shp = shapely.wkt.loads(row['Footprint WKT'])
        geojson = shapely.geometry.mapping(shp)
        folium.GeoJson(
            geojson,
            style_function=_fpStyleFunction,
            name=str(i)
        ).add_to(m)

    for i, row in df.iterrows():
        shp = shapely.wkt.loads(row['Cloud WKT'])
        geojson = shapely.geometry.mapping(shp)
        folium.GeoJson(
            geojson,
            style_function=_CloudStyleFunction,
            name=str(i)
        ).add_to(m)

    return m
