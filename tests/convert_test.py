import sensortools.convert
from pandas.util.testing import assert_frame_equal
import pandas as pd
import pytest


@pytest.fixture
def gb100_to_km2_truth(path_gb100_to_km2):
    return pd.read_csv(path_gb100_to_km2).sort_values(by=['Sensor']).reset_index(drop=True)


@pytest.fixture
def km100_to_gb_truth(path_km100_to_gb):
    return pd.read_csv(path_km100_to_gb).sort_values(by=['Sensor']).reset_index(drop=True)


# Not tested: bit_depth parameter
def test_gb_to_km2(gb100_to_km2_truth):
    test_df_output = sensortools.convert.gb_to_km2(100).sort_values(by=['Sensor']).reset_index(drop=True)
    assert_frame_equal(gb100_to_km2_truth, test_df_output, check_dtype=False)


def test_km2_to_gb(km100_to_gb_truth):
    test_df_output = sensortools.convert.km2_to_gb(100).sort_values(by=['Sensor']).reset_index(drop=True)
    assert_frame_equal(km100_to_gb_truth, test_df_output, check_dtype=False)
