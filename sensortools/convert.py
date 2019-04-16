import pandas as pd
import numpy as np


def _sensor_info():
    return {
            'GE01_Pan': {
                'resolution': 0.41,
                'band_count': 1,
            },
            'GE01_MS': {
                'resolution': 1.64,
                'band_count': 4,
            },
            'GE01_PanSharp': {
                'resolution': 0.41,
                'band_count': 4,
            },
            'WV01_Pan': {
                'resolution': 0.5,
                'band_count': 1,
            },
            'WV02_Pan': {
                'resolution': 0.46,
                'band_count': 1,
            },
            'WV02_MS': {
                'resolution': 1.85,
                'band_count': 8,
            },
            'WV02_PanSharp': {
                'resolution': 0.46,
                'band_count': 8,
            },
            'WV03_Pan': {
                'resolution': 0.31,
                'band_count': 1,
            },
            'WV03_MS': {
                'resolution': 1.24,
                'band_count': 8,
            },
            'WV03_SWIR': {
                'resolution': 3.7,
                'band_count': 8,
            },
            'WV03_PanSharp': {
                'resolution': 0.31,
                'band_count': 8,
            },
            'WV04_Pan': {
                'resolution': 0.31,
                'band_count': 1,
            },
            'WV04_MS': {
                'resolution': 1.24,
                'band_count': 4,
            },
            'WV04_PanSharp': {
                'resolution': 0.31,
                'band_count': 4,
            }
        }


def _formatsensorinfo():
    """
    Formats sensor info into a pandas dataframe
    """
    df = pd.DataFrame(columns=['Sensor', 'Resolution (m)', 'Band Count'])
    for i, (image, key) in enumerate(_sensor_info().items()):
        df.loc[i] = [image, key['resolution'], key['band_count']]

    return df


def gb_to_km2(gb, bit_depth=32):
    """
    Function to convert GB of data into sensor aerial coverage (km2)

    Parameters
    ----------
    gb : int
        Desired GB to translate into aerial satellite sensor coverage in km2
    bit_depth :
        Depth of bit used for storage (defaults to 32)

    Returns
    -------
    df
        Returns input DataFrame with associated aerial coverage in km2 for each sensor
    """

    file_bytes = gb * 1e+9
    storage_bytes = bit_depth / 8.
    sensors = _formatsensorinfo()

    km2 = sensors.apply(lambda row: ((np.sqrt(file_bytes /
                                                   (row['Band Count'] * storage_bytes)) * row[
                                               'Resolution (m)']) / 1000) ** 2, axis=1)

    df = pd.concat([sensors, km2.rename('Area (km2)').astype(np.int)], axis=1)

    # Using a ratio of km2/GB for WV2/WV3 Pansharp
    df.loc[df.Sensor == 'WV03_PanSharp', 'Area (km2)'] = gb * 16.017
    df.loc[df.Sensor == 'WV02_PanSharp', 'Area (km2)'] = gb * 35.394
    df.loc[df.Sensor == 'WV04_PanSharp', 'Area (km2)'] = gb * 19.22
    df.loc[df.Sensor == 'GE01_PanSharp', 'Area (km2)'] = gb * 33.62

    return df


def km2_to_gb(km2, bit_depth=32):
        """
        Function that converts km2 into required GB per satellite

        Parameters
        ----------
        km2 : int
            Desired km2 to translate into GB of data
        bit_depth :
            Depth of bit used for storage (defaults to 32)

        Returns
        -------
        df
            Returns input DataFrame with associated GB for input aerial coverage
        """
        side_length = np.sqrt(km2) * 1000
        sensors = _formatsensorinfo()
        pixel_count = (side_length / sensors['Resolution (m)']) ** 2
        sqkm = (pixel_count * sensors['Band Count'] * (bit_depth / 8.)) / 1e+9

        df = pd.concat([sensors, sqkm.rename('GB')], axis=1)

        df.loc[df.Sensor == 'WV03_PanSharp', 'GB'] = df.loc[df.Sensor == 'WV03_Pan'].GB.values + \
                                                     df.loc[df.Sensor == 'WV03_MS'].GB.values
        df.loc[df.Sensor == 'WV02_PanSharp', 'GB'] = df.loc[df.Sensor == 'WV02_Pan'].GB.values + \
                                                     df.loc[df.Sensor == 'WV02_MS'].GB.values
        df.loc[df.Sensor == 'GE01_PanSharp', 'GB'] = df.loc[df.Sensor == 'GE01_Pan'].GB.values + \
                                                     df.loc[df.Sensor == 'GE01_MS'].GB.values
        df.loc[df.Sensor == 'WV04_PanSharp', 'GB'] = df.loc[df.Sensor == 'WV04_Pan'].GB.values + \
                                                     df.loc[df.Sensor == 'WV04_MS'].GB.values

        return df
