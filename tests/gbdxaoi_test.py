import sensortools.tools.spatial as spatial_tools
import sensortools.gbdxaoi
# from pandas.util.testing import assert_frame_equal
from shapely.geometry import box
from math import isclose
import pandas as pd
import numpy as np


def test_fpaoiintersect():
    aoi = box(-5, -8, 5, 8)
    fprint = box(-5, -8, 0, 0)
    truth_pct = 19.915495233
    assert isclose(sensortools.gbdxaoi._fpaoiintersect(fprint.wkt, aoi.wkt), truth_pct)


def test_formatSearchResults_image_identifier(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    print(df_results)
    assert 'image_identifier' in df_results.columns
    assert df_results['image_identifier'].iloc[0] == "622eb7e2-dbe1-4d83-803c-4fdbbf23c754"


def test_formatSearchResults_catid(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'catalog_id' in df_results.columns
    assert df_results['catalog_id'].iloc[0] == "10400100373C4200"


def test_formatSearchResults_sensor(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Sensor' in df_results.columns
    assert df_results['Sensor'].iloc[0] == "WORLDVIEW03_VNIR"


def test_formatSearchResults_panresolution(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Pan Resolution' in df_results.columns
    assert df_results['Pan Resolution'].iloc[0] is None


def test_formatSearchResults_multiresolution(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'MS Resolution' in df_results.columns
    assert df_results['MS Resolution'].iloc[0] is None


def test_formatSearchResults_cloudcover(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Cloud Cover' in df_results.columns
    assert df_results['Cloud Cover'].iloc[0] == 23


def test_formatSearchResults_date(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Date' in df_results.columns
    assert df_results['Date'].iloc[0].tz_localize(None) == pd.to_datetime('2018-01-15 21:24:49.255')


def test_formatSearchResults_offnadir(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Off Nadir Angle' in df_results.columns
    assert df_results['Off Nadir Angle'].iloc[0] == 29.0


def test_formatSearchResults_sunelev(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Sun Elevation' in df_results.columns
    assert df_results['Sun Elevation'].iloc[0] == 43.8


def test_formatSearchResults_targetazimuth(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    assert 'Target Azimuth' in df_results.columns
    assert df_results['Target Azimuth'].iloc[0] is None


def test_formatSearchResults_footprintwkt(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    truth_wkt = "MULTIPOLYGON(((-157.93145697 21.4678678, -157.76562929 21.48603316, -157.76558305 21.35829358, " \
                "-157.93316103 21.33899499, -157.93145697 21.4678678)))"
    assert 'Footprint WKT' in df_results.columns
    assert df_results['Footprint WKT'].iloc[0] == truth_wkt


def test_formatSearchResults_footprintarea(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    truth_area = spatial_tools.aoiArea(df_results['Footprint WKT'].iloc[0])
    assert 'Footprint Area (km2)' in df_results.columns
    assert isclose(df_results['Footprint Area (km2)'].iloc[0], truth_area)


def test_formatSearchResults_footprintaoiintersectarea(gbdxsearch_results):
    aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)
    truth_pct = sensortools.gbdxaoi._fpaoiintersect(df_results['Footprint WKT'].iloc[0], aoi)
    assert 'Footprint AOI Inter Percent' in df_results.columns
    assert isclose(df_results['Footprint AOI Inter Percent'].iloc[0], truth_pct)


def test_aoifootprintintersection(gbdxsearch_resultsdf, search_intersection_geom):
    aoi = box(-158.360, 21.15, -157.800, 22.000)
    assert sensortools.gbdxaoi.aoiFootprintIntersection(gbdxsearch_resultsdf, aoi.wkt) == search_intersection_geom


def test_aoifootprintpctcoverage_100(gbdxsearch_resultsdf):
    aoi = box(-158.220, 21.27, -157.800, 21.73)
    assert sensortools.gbdxaoi.aoiFootprintPctCoverage(gbdxsearch_resultsdf, aoi.wkt) == 100.


def test_aoifootprintpctcoverage_partialcoverage(gbdxsearch_resultsdf):
    aoi = box(-158.360, 21.15, -157.800, 22.000)
    assert isclose(sensortools.gbdxaoi.aoiFootprintPctCoverage(gbdxsearch_resultsdf, aoi.wkt), 72.33696128)

# How to test aoicloudcover?
