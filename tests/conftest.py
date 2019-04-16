import pytest
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
