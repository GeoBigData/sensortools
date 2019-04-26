import sensortools.gbdxaoi
# from pandas.util.testing import assert_frame_equal
from shapely.geometry import box
from math import isclose


def test_fpaoiintersect():
    aoi = box(-5, -8, 5, 8)
    fprint = box(-5, -8, 0, 0)
    truth_pct = 19.915495233
    assert isclose(sensortools.gbdxaoi._fpaoiintersect(fprint.wkt, aoi.wkt), truth_pct)


# def test_formatSearchResults(gbdxsearch_results):
#     pass
#     aoi = box(-157.9, 21.3, -157.8, 21.4).wkt
#     df_results = sensortools.gbdxaoi.formatSearchResults(gbdxsearch_results, aoi)


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
