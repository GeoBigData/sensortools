from shapely.geometry import shape
import pytest
import json
import os


@pytest.fixture(scope='session')
def data_dir():
    """Absolute file path to the directory containing test datasets."""
    return os.path.abspath(os.path.join('data'))


@pytest.fixture(scope='session')
def path_gb100_to_km2(data_dir):
    return os.path.join(data_dir, '100gb_to_km2.csv')


@pytest.fixture(scope='session')
def path_km100_to_gb(data_dir):
    return os.path.join(data_dir, 'km100_to_gb.csv')


@pytest.fixture(scope='session')
def gbdxsearch_results(data_dir):
    path = os.path.join(data_dir, 'gbdxsearch_results.json')
    with open(path, 'r') as f:
        return json.load(f)


@pytest.fixture(scope='session')
def search_intersection_geom(data_dir):
    path = os.path.join(data_dir, 'search_intersection.geojson')
    with open(path, 'r') as f:
        geojson = json.load(f)
    raw_shp = shape(geojson['geometry'])
    buffered = raw_shp.buffer(0.001)
    inside = raw_shp.buffer(-0.001)
    donut_of_acceptability = buffered - inside
    return donut_of_acceptability
