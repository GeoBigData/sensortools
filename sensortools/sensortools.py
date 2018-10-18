import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import shapely
import json
import utm
import pyproj
from functools import partial
from shapely.ops import transform

class sensortools(object):
    '''

    '''
    def __init__(self):
        # grab the sensor infomation
        self._sensor_info = self._sensorInfo()
        # format the sensor infomation into pandas df
        self.sensors = self._formatSensorInfo()
        # formatted seach results from catalog search
        self.search_df = None

    def _formatSensorInfo(self):
        """
        Formats sensor info into a pandas dataframe
        """
        df = pd.DataFrame(columns=['Sensor', 'Resolution (m)', 'Band Count'])
        for i, (image, key) in enumerate(self._sensor_info.items()):
            df.loc[i] = [image, key['resolution'], key['band_count']]

        return df

    def _sensorInfo(self):
        # TODO: make these names match the names used by catalog search
        # going to deviate some however given Pan/MS designations
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
            DataFrame that includes Sensor name, resolution of the sensor,
            and band count of the sensor
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

    def formatSearchResults(self, search_results):
        """
        Format the results into a pandas df. To be used in plotting functions
        but also useful outside of them.
        """

        s, t, c, n, e, f = [], [], [], [], [], []
        for i, re in enumerate(search_results):
            s.append(re['properties']['sensorPlatformName'])
            t.append(re['properties']['timestamp'])
            c.append(re['properties']['cloudCover'])
            n.append(re['properties']['offNadirAngle'])
            e.append(re['properties']['sunElevation'])
            f.append(re['properties']['footprintWkt'])
        df = pd.DataFrame({'Sensor': s,
            'Date': pd.to_datetime(t),
            'Cloud Cover': c,
            'Off Nadir Angle': n,
            'Sun Elevation': e,
            'Footprint WKT': f},
            index=pd.to_datetime(t))
        df.sort_values(['Date'], inplace=True)
        df['x'] = range(len(df))

        self.search_df = df

    def searchBarPlot(self):
        """
        Bar Plot of the count of sensor images in search
        """
        f, ax = plt.subplots(figsize=(15,6))
        sns.countplot(x='Sensor', data=self.search_df)
        ax.set_ylabel('Image Count')

        return None

    def searchScatterPlot(self):
        '''
        Function to plot out the results of an image/AOI search
        '''

        f, ax = plt.subplots(figsize=(12,6))
        sns.despine(bottom=True, left=True)

        sns.stripplot(x="Date", y="Sensor", hue="Sensor",
                      data=self.search_df, dodge=True, jitter=True,
                      alpha=.25, zorder=1, size=10)

        years = mdates.YearLocator()   # every year
        months = mdates.MonthLocator()  # every month
        yearsFmt = mdates.DateFormatter('%Y')
        monthsFmt = mdates.DateFormatter('%m')

        # TODO: check len of date range and adjust labels accordingly
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        ax.xaxis.set_minor_locator(months)

        s = self.search_df.groupby(['Sensor']).count()

        _= ax.set_yticklabels(s.index + ' Count: ' + s.x.map(str))
        _= ax.get_yaxis().set_visible(False)

        legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=len(s.index))
        for t in legend.get_texts():
            c = s[s.index==t.get_text()].x.values[0]
            label = t.get_text() + ' Count:' + str(c)
            t.set_text(label)

        return None

    def _convertAOItoLocation(self, aoi):
        """
        Convert a WKT Polygon to a Folium Point Location
        """

        shp = shapely.wkt.loads(aoi)
        coords = shp.centroid.coords.xy
        x, y = coords[0][-1], coords[1][-1]

        # returning as lat lon as that is required by folium
        return [y, x]

    def mapAOI(self, aoi):
        """
        Mapping function to show the area of a user defined AOI
        """
        # turn WKT AOI into something folium can read
        shp = shapely.wkt.loads(aoi)
        geojson = shapely.geometry.mapping(shp)
        # calculate centroid of AOI as starting location
        aoi = self._convertAOItoLocation(aoi)
        # create simple map
        m = folium.Map(location=aoi, zoom_start=8, tiles='Stamen Terrain')
        folium.GeoJson(
            geojson,
            name='geojson'
        ).add_to(m)

        return m

    def aoiArea(self, aoi):
        """
        Get the UTM projection string for an AOI centroid
        """
        # convert AOI to shape
        shp = shapely.wkt.loads(aoi)
        # get the centroid of the shape
        loc = self._convertAOItoLocation(aoi)
        # find the UTM info
        utm_def = utm.from_latlon(loc[0], loc[1])
        zone = utm_def[-2]
        # convert UTM zone info to something pyproj can understand
        if loc[0] < 0:
            hem = 'south'
        else:
            hem = 'north'
        # transform the shape
        from_p = pyproj.Proj(init='epsg:4326')
        to_p = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', hemisphere=hem)
        project = partial(pyproj.transform, from_p, to_p)
        shp_utm = transform(project, shp)
        # calculate area of projected units in km2
        km2 = shp_utm.area / 1000000.

        return km2

    def mapGB(self, gb=None, aoi=[39.742043, -104.991531]):
        """
        Function to map GB to sensor areas given bands and resolution
        User can input a point lon, lat or the Polygon AOI from which
        a centroid  will be calculated
        """
        # convert GB to df
        df = self.gb_to_km2(gb)

        # if user passes in Polygon AOI, convert to Folium location
        if isinstance(aoi, str):
            aoi = self._convertAOItoLocation(aoi)

        # TODO: turn these into strip type features
        # TODO: make sensor features different colors
        # TODO: add legend
        # TODO: could add some logic to control zoom level
        m = folium.Map(location=aoi, zoom_start=8, tiles='Stamen Terrain')
        for i, row in df.iterrows():
            folium.Circle(
                radius=np.sqrt(row['Area (km2)'] / np.pi) * 1000,
                location=aoi,
                popup=row['Sensor'],
                fill=False,
            ).add_to(m)
        return m
