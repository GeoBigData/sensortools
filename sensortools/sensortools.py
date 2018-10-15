import pandas as pd
import numpy as np
import folium

class sensortools(object):
    '''

    '''
    def __init__(self):
        # grab the sensor infomation
        self.sensor_info = self._sensorInfo()
        # format the sensor infomation into pandas df 
        self.sensors = self._formatSensorInfo()

    def _formatSensorInfo(self):
        df = pd.DataFrame(columns=['Sensor', 'Resolution (m)', 'Band Count'])
        for i, (image, key) in enumerate(self.sensor_info.items()):
            df.loc[i] = [image, key['resolution'], key['band_count']]

        return df

    def _sensorInfo(self):
        sensor_info = {
            'GE01_Pan' : {
                'resolution' : 0.41,
                'band_count' : 1
            },
            'GE01_MS' : {
                'resolution' : 1.64,
                'band_count' : 4
            },
            'WV01_Pan' : {
                'resolution' : 0.5,
                'band_count' : 1
            },
            'WV02_Pan' : {
                'resolution' : 0.46,
                'band_count' : 1
            },
            'WV02_MS' : {
                'resolution' : 1.85,
                'band_count' : 8
            },
            'WV03_Pan' : {
                'resolution' : 0.31,
                'band_count' : 1
            },
            'WV03_MS' : {
                'resolution' : 1.24,
                'band_count' : 8
            },
            'WV03_SWIR' : {
                'resolution' : 3.7,
                'band_count' : 8
            },
            'WV04_Pan' : {
                'resolution' : 0.31,
                'band_count' : 1
            },
            'WV04_MS' : {
                'resolution' : 1.24,
                'band_count' : 4}}

        return sensor_info

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
        '''
        Function to plot out the results of an image/AOI search
        '''

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
