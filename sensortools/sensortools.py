import pandas as pd
import numpy as np
import folium

class sensortools(object):
    '''

    '''
    def __init__(self):
        self.sensors = _getSensorInfo()

    def _getSensorInfo(self):
        return pd.read_csv('../data/sensors.csv')

    def gb_to_km2(self, gb, bit_depth=32):
        """
        Function to convert GB of data into sensor aerial coverage (km2)

        Parameters
        ----------
        df : Pandas DataFrame
            DataFrame that includes Sensor name, resolution of the sensor, and band count of the sensor
        gb : int
            Desired GB to translate into aerial satellite sensor coverage in km2
        bit_depth :
            Depth of bit used for storage (defaults to 32)

        Returns
        -------
        df
            Returns input DataFrame with associated aerial coverage in km2 for each sensor
        """

        file_bytes = gb * 1073741824
        storage_bytes = bit_depth / 8.

        km2 = self.sensors.apply(lambda row: ((np.sqrt(file_bytes /
                             (row['Band Count'] * storage_bytes)) * row['Resolution (m)']) / 1000) ** 2, axis=1)

        return pd.concat([self.sensors, km2.rename('Area (km2)').astype(np.int)], axis=1)

    def km2_to_gb(self, km2, bit_depth=32):
        """
        Function that converts km2 into required GB per satellite

        Parameters
        ----------
        df : Pandas DataFrame
            DataFrame that includes Sensor name, resolution of the sensor, and band count of the sensor
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
        pixel_count =  (side_length / self.sensors['Resolution (m)']) ** 2
        sqkm = (pixel_count * self.sensors['Band Count'] * (bit_depth / 8.)) / 1073741824

        return pd.concat([self.sensors, sqkm.rename('GB')], axis=1)

    def plotSearch(self):
        pass

    def mapAOI(self, sensor_km2):
        m = folium.Map(location=[39.742043, -104.991531], zoom_start=8, tiles='Stamen Terrain')
        for i, row in sensor_km2.iterrows():
            folium.Circle(
                radius=np.sqrt(row['Area (km2)'] / np.pi) * 1000,
                location=[39.742043, -104.991531],
                popup=row['Sensor'],
                fill=False,
            ).add_to(m)
        return m
