import sensortools.tools.spatial as spatial_tools
from sensortools.decorators import InputError
from shapely.geometry import Point
from math import isclose
from pyproj import Proj
import pytest


def test_convertaoitolocation():
    aoi_wkt = 'POLYGON ((15 -5, 15 0, 10 0, 10 -5, 15 -5))'
    y, x = spatial_tools.convertAOItoLocation(aoi_wkt)
    assert x == 12.5
    assert y == -2.5


def test_convertaoitolocation_input_err():
    with pytest.raises(InputError):
        aoi = (15, -5, 15, 0, 10, 0, 10, -5, 15, -5)
        spatial_tools.convertAOItoLocation(aoi)


def test_aoiArea_4326():
    aoi_wkt = 'POLYGON ((-104.9513504743272 22.60684943190418, -104.951024727671 23.51018701498204, ' \
              '-105 23.51019471509047, -105 22.60685680348743, -104.9513504743272 22.60684943190418))'
    truth_area = 500
    print(spatial_tools.aoiArea(aoi_wkt))
    assert isclose(spatial_tools.aoiArea(aoi_wkt), truth_area)


def test_getUTMProj_north():
    madrid = 'POINT (-3.7038 40.4168)'
    truth_proj = Proj(proj='utm', zone=30, ellps='WGS84', hemisphere='north')
    assert spatial_tools.getUTMProj(madrid).srs == truth_proj.srs


def test_getUTMProj_south():
    maputo = 'POINT (32.5732 -25.9692)'
    truth_proj = Proj(proj='utm', zone=36, ellps='WGS84', hemisphere='south')
    assert spatial_tools.getUTMProj(maputo).srs == truth_proj.srs


def test_getUTMProj_input_err():
    with pytest.raises(InputError):
        aoi = (15, -5, 15, 0, 10, 0, 10, -5, 15, -5)
        spatial_tools.getUTMProj(aoi)


def test_getLLUTMProj_north():
    madrid = [40.4168, -3.7038]
    truth_proj = Proj(proj='utm', zone=30, ellps='WGS84', hemisphere='north')
    assert spatial_tools.getLLUTMProj(*madrid).srs == truth_proj.srs


def test_getLLUTMProj_south():
    maputo = [-25.9692, 32.5732]
    truth_proj = Proj(proj='utm', zone=36, ellps='WGS84', hemisphere='south')
    assert spatial_tools.getLLUTMProj(*maputo).srs == truth_proj.srs


def test_getLLUTMProj_inputtype_err():
    with pytest.raises(InputError):
        aoi = Point(-3.7038, 40.4168).coords.xy
        spatial_tools.getLLUTMProj(*aoi)


def test_getLLUTMProj_lat_bound_err():
    with pytest.raises(InputError):
        aoi = [309483, -180]
        spatial_tools.getLLUTMProj(*aoi)


def test_getLLUTMProj_lon_bound_err():
    with pytest.raises(InputError):
        aoi = ['42', '500392']
        spatial_tools.getLLUTMProj(*aoi)
