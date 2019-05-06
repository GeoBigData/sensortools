import sensortools.tools.spatial as spatial_tools
import sensortools.gbdxaoi
# from pandas.util.testing import assert_frame_equal
from shapely.geometry import box
import shapely.wkt
from math import isclose
import pandas as pd
import pytest


@pytest.fixture
def aoi_wkt():
    return box(-158.1, 21.15, -157.800, 21.50).wkt


def test_fpaoiintersect():
    aoi = box(-5, -8, 5, 8)
    fprint = box(-5, -8, 0, 0)
    truth_pct = 19.915495233
    assert isclose(sensortools.gbdxaoi._intersectpct(fprint.wkt, aoi.wkt), truth_pct)


def test_formatSearchResults_image_identifier(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'image_identifier' in df_results.columns
    assert df_results['image_identifier'].iloc[0] == "622eb7e2-dbe1-4d83-803c-4fdbbf23c754"


def test_formatSearchResults_catid(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'catalog_id' in df_results.columns
    assert df_results['catalog_id'].iloc[0] == "10400100373C4200"


def test_formatSearchResults_sensor(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'Sensor' in df_results.columns
    assert df_results['sensor'].iloc[0] == "WORLDVIEW03_VNIR"


def test_formatSearchResults_panresolution(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'pan_resolution' in df_results.columns
    assert df_results['pan_resolution'].iloc[0] is None


def test_formatSearchResults_multiresolution(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'ms_resolution' in df_results.columns
    assert df_results['ms_resolution'].iloc[0] is None


def test_formatSearchResults_cloudcover(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'cloud_cover' in df_results.columns
    assert df_results['cloud_cover'].iloc[0] == 23


def test_formatSearchResults_date(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'timestamp' in df_results.columns
    assert df_results['timestamp'].iloc[0].tz_localize(None) == pd.to_timestamptime('2018-01-15 21:24:49.255')


def test_formatSearchResults_offnadir(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'off_nadir_angle' in df_results.columns
    assert df_results['off_nadir_angle'].iloc[0] == 29.0


def test_formatSearchResults_sunelev(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'sun_elevation' in df_results.columns
    assert df_results['sun_elevation'].iloc[0] == 43.8


def test_formatSearchResults_targetazimuth(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert 'target_azimuth' in df_results.columns
    assert df_results['target_azimuth'].iloc[0] is None


def test_formatSearchResults_footprintwkt(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    truth_wkt = "MULTIPOLYGON(((-157.93145697 21.4678678, -157.76562929 21.48603316, -157.76558305 21.35829358, " \
                "-157.93316103 21.33899499, -157.93145697 21.4678678)))"
    assert 'footprint_geometry' in df_results.columns
    assert df_results['footprint_geometry'].iloc[0] == shapely.wkt.loads(truth_wkt)


def test_formatSearchResults_footprintarea(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    truth_area = spatial_tools.aoiArea(df_results['footprint_geometry'].iloc[0].wkt)
    assert 'footprint_area(km2)' in df_results.columns
    assert isclose(df_results['footprint_area(km2)'].iloc[0], truth_area)


def test_formatSearchResults_footprintaoiintersectarea(gbdxsearch_results, aoi_wkt):
    df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    truth_pct = sensortools.gbdxaoi._intersectpct(df_results['footprint_geometry'].iloc[0].wkt, aoi_wkt)
    assert 'footprint_aoi_intersect_percent' in df_results.columns
    assert isclose(df_results['footprint_aoi_intersect_percent'].iloc[0], truth_pct)


def test_aoifootprintintersection(gbdxsearch_results, search_intersection_geom, aoi_wkt):
    gbdxsearch_resultsdf = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    intersection_shp = sensortools.gbdxaoi.aoiFootprintIntersection(gbdxsearch_resultsdf, aoi_wkt)
    assert search_intersection_geom.contains(intersection_shp.exterior)


def test_aoifootprintpctcoverage_100(gbdxsearch_results):
    aoi = box(-158.000, 21.325, -157.800, 21.440)
    gbdxsearch_resultsdf = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi.wkt)
    assert sensortools.gbdxaoi.aoiFootprintPctCoverage(gbdxsearch_resultsdf, aoi.wkt) == 100.


def test_aoifootprintpctcoverage_partialcoverage(aoi_wkt, gbdxsearch_results):
    gbdxsearch_resultsdf = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi_wkt)
    assert isclose(sensortools.gbdxaoi.aoiFootprintPctCoverage(gbdxsearch_resultsdf, aoi_wkt), 42.5164538)

# How to test aoicloudcover?
