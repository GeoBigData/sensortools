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
import requests
import warnings
warnings.filterwarnings("ignore")

class sensortools(object):
    '''

    '''
    def __init__(self):
        # grab the sensor infomation
        self._sensor_info = self._sensorInfo()
        # format the sensor infomation into pandas df
        self.sensors = self._formatSensorInfo()

    def _formatSensorInfo(self):
        """
        Formats sensor info into a pandas dataframe
        """
        df = pd.DataFrame(columns=['Sensor', 'Resolution (m)', 'Band Count'])
        for i, (image, key) in enumerate(self._sensor_info.items()):
            df.loc[i] = [image, key['resolution'], key['band_count']]

        return df

    def createAOI(self, latitude, longitude, area_km2, shape='circle'):
        """
        Create a WKT AOI from a lat, lon, area
        """
        # create the point goem
        pt = shapely.geometry.Point(longitude, latitude)

        # create the UTM projection
        to_p = self._getLLUTMProj(latitude, longitude)
        from_p = pyproj.Proj(init='epsg:4326')
        project = partial(pyproj.transform, from_p, to_p)
        project_reverse = partial(pyproj.transform, to_p, from_p)

        # transform the point to UTM and buffer
        pt_prj = transform(project, pt)

        if shape=='circle':
            # calculate desired buffer size
            radius = np.sqrt(area_km2 / np.pi) * 1000
            pt_buffer = pt_prj.buffer(area)
            pt_buffer_wgs = transform(project_reverse, pt_buffer)
        elif shape=='square':
            pass

        return pt_buffer_wgs.wkt

    def setSensorResolution(self, sensor, resolution):
        """
        Method to change the resolution of the sensor
        """
        self.sensors.loc[self.sensors['Sensor']==sensor, 'Resolution (m)'] = resolution

    def _sensorInfo(self):
        # TODO: make these names match the names used by catalog search
        # going to deviate some however given Pan/MS designations
        sensor_info = {
            'GE01_Pan' : {
                'resolution' : 0.41,
                'band_count' : 1,
                'plot_color' : '#fee6ce'
            },
            'GE01_MS' : {
                'resolution' : 1.64,
                'band_count' : 4,
                'plot_color' : '#fdae6b'
            },
            'WV01_Pan' : {
                'resolution' : 0.5,
                'band_count' : 1,
                'plot_color' : '#756bb1'
            },
            'WV02_Pan' : {
                'resolution' : 0.46,
                'band_count' : 1,
                'plot_color' : '#deebf7'
            },
            'WV02_MS' : {
                'resolution' : 1.85,
                'band_count' : 8,
                'plot_color' : '#9ecae1'
            },
            'WV03_Pan' : {
                'resolution' : 0.31,
                'band_count' : 1,
                'plot_color' : '#bae4b3'
            },
            'WV03_MS' : {
                'resolution' : 1.24,
                'band_count' : 8,
                'plot_color' : '#74c476'
            },
            'WV03_SWIR' : {
                'resolution' : 3.7,
                'band_count' : 8,
                'plot_color' : '#edf8e9'
            },
            'WV04_Pan' : {
                'resolution' : 0.31,
                'band_count' : 1,
                'plot_color' : '#fee6ce'
            },
            'WV04_MS' : {
                'resolution' : 1.24,
                'band_count' : 4,
                'plot_color' : '#fdae6b'}
            }

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

    def _fpaoiinter(self, fp_wkt, aoi):
        """
        Calculate the individual footprint coverage of the AOI
        """
        # get the projection for area calculations
        to_p = self._getUTMProj(aoi)
        from_p = pyproj.Proj(init='epsg:4326')
        project = partial(pyproj.transform, from_p, to_p)

        # The projected aoi
        aoi_shp = shapely.wkt.loads(aoi)
        aoi_shp_prj = transform(project, aoi_shp)

        # The projected footprint
        ft_shp = shapely.wkt.loads(fp_wkt)
        ft_shp_prj = transform(project, ft_shp)

        # Intersect the two shapes
        inter_km2 = aoi_shp_prj.intersection(ft_shp_prj).area / 1000000.

        # Calculate area in km2
        pct = inter_km2 / self.aoiArea(aoi) * 100.

        return pct

    def _aoiFootprintCalculations(self, df, aoi):
        """
        Given an AOI and search results, determine percent of the AOI that is
        covered by all footprints
        """
        # projection info
        to_p = self._getUTMProj(aoi)
        from_p = pyproj.Proj(init='epsg:4326')
        project = partial(pyproj.transform, from_p, to_p)

        # project the AOI, calc area
        aoi_shp = shapely.wkt.loads(aoi)
        aoi_shp_prj = transform(project, aoi_shp)
        aoi_km2 = aoi_shp_prj.area / 1000000.

        # union all the footprint shapes
        shps = []
        for i, row in df.iterrows():
            shps.append(shapely.wkt.loads(row['Footprint WKT']))
        footprints = shapely.ops.cascaded_union(shps)

        # project the footprint union
        footprints_prj = transform(project, footprints)

        # perform intersection and calculate area
        inter_shp_prj = aoi_shp_prj.intersection(footprints_prj)
        inter_km2 = inter_shp_prj.area / 1000000.
        pct = inter_km2 / aoi_km2 * 100.

        # project back to wgs84/wkt for mapping
        project_reverse = partial(pyproj.transform, to_p, from_p)
        inter_shp = transform(project_reverse, inter_shp_prj)
        inter_json = shapely.geometry.mapping(inter_shp)

        return [pct, inter_json]

    def aoiCloudCover(self, df, aoi):
        """
        For each footprint in the search results, calculate a percent cloud
        cover for the AOI (instead of entire strip)
        """
        try:
            with open('duc-api.txt', 'r') as a:
                api_key = a.readlines()[0].rstrip()
        except:
            print('Could not find DUC API key in ./duc-api.txt')
        # search the results, do not submit catids with 0 cloud cover
        catids = df[df['Cloud Cover'] > 0].catalog_id.values

        # send request to DUC database
        url = "https://api.discover.digitalglobe.com/v1/services/cloud_cover/MapServer/0/query"
        headers = {
            'x-api-key': "{api_key}".format(api_key=api_key),
            'content-type': "application/x-www-form-urlencoded"
        }
        data = {
            'outFields': '*',
            'where':"image_identifier IN ({cat})".format(cat="'" + "','".join(catids) + "'"),
            'outSR':'4326',
            'f':'geojson'
        }
        response = requests.request("POST", url, headers=headers, data=data)
        clouds = json.loads(response.text)

        # projection info
        to_p = self._getUTMProj(aoi)
        from_p = pyproj.Proj(init='epsg:4326')
        project = partial(pyproj.transform, from_p, to_p)

        # project the AOI, calc area
        aoi_shp = shapely.wkt.loads(aoi)
        aoi_shp_prj = transform(project, aoi_shp)
        aoi_km2 = aoi_shp_prj.area / 1000000.

        # add column to search df
        df['AOI Cloud Cover'] = 0

        # iterate over the clouds and perform cloud cover percent
        for feature in clouds['features']:
            # get catalog id
            c = feature['properties']['image_identifier']

            # get the footprint shape
            fp = shapely.wkt.loads(df.loc[df['catalog_id']==c,
                    'Footprint WKT'].values[0])
            fp_prj = transform(project, fp)

            # intersect the AOI with the footprint
            # using this as intersection with clouds
            aoi_fp_inter = aoi_shp_prj.intersection(fp_prj)
            aoi_fp_inter_km2 = aoi_fp_inter.area / 1000000.

            # extract the clouds and conver to shape
            cloud = shapely.geometry.shape(feature['geometry'])
            cloud_prj = transform(project, cloud)

            # perform intersection and calculate area
            try:
                inter_shp_prj = aoi_fp_inter.intersection(cloud_prj)
            except:
                cloud_prj = cloud_prj.buffer(0.0)
                inter_shp_prj = aoi_fp_inter.intersection(cloud_prj)

            inter_km2 = inter_shp_prj.area / 1000000.
            pct = inter_km2 / aoi_fp_inter_km2 * 100.

            # update the dataframe
            df.loc[df['catalog_id']==c, 'AOI Cloud Cover'] = pct

        return df

    def aoiFootprintPctCoverage(self, df, aoi):
        """
        Return the percent area covered from aoi footprint calculation
        """
        return self._aoiFootprintCalculations(df, aoi)[0]

    def formatSearchResults(self, search_results, aoi):
        """
        Format the results into a pandas df. To be used in plotting functions
        but also useful outside of them.
        """
        cat, s, t, c, n, e, f, i = [], [], [], [], [], [], [], []
        for j, re in enumerate(search_results):
            cat.append(re['identifier'])
            s.append(re['properties']['sensorPlatformName'])
            t.append(re['properties']['timestamp'])
            c.append(re['properties']['cloudCover'])
            n.append(re['properties']['offNadirAngle'])
            e.append(re['properties']['sunElevation'])
            f.append(re['properties']['footprintWkt'])
            i.append(self._fpaoiinter(re['properties']['footprintWkt'], aoi))

        df = pd.DataFrame({
            'catalog_id': cat,
            'Sensor': s,
            'Date': pd.to_datetime(t),
            'Cloud Cover': c,
            'Off Nadir Angle': n,
            'Sun Elevation': e,
            'Footprint WKT': f,
            'Footprint AOI Inter Percent': i},
            index=pd.to_datetime(t))
        df.sort_values(['Date'], inplace=True)
        df['x'] = range(len(df))

        return df

    def searchVarPlot(self, df, var1=None, var2=None, sensor=None):
        """
        Create a Jointplot of two variables. Optionally, subset by sensor
        """
        if sensor:
            df = df[df.Sensor==sensor]
        g = sns.jointplot(df[var1], df[var2], kind='kde')
        try:
            # seems to fail on GBDX Notebooks
            g.ax_joint.legend_.remove()
        except:
            pass

        return None

    def searchSensorComparePlot(self, df, var1=None, var2=None):
        """
        Compare multiple sensors and variables
        """
        g = sns.FacetGrid(df, col="Sensor")
        g.map(sns.kdeplot, var1, var2)

        return None

    def searchBarPlot(self, df):
        """
        Bar Plot of the count of sensor images in search
        """
        f, ax = plt.subplots(figsize=(15,6))
        sns.countplot(x='Sensor', data=df)
        ax.set_ylabel('Image Count')

        return None

    def searchScatterPlot(self, df):
        '''
        Function to plot out the results of an image/AOI search
        '''

        f, ax = plt.subplots(figsize=(12,6))
        sns.despine(bottom=True, left=True)

        sns.stripplot(x="Date", y="Sensor", hue="Sensor",
                      data=df, dodge=True, jitter=True,
                      alpha=.25, zorder=1, size=10)

        years = mdates.YearLocator()   # every year
        months = mdates.MonthLocator()  # every month
        yearsFmt = mdates.DateFormatter('%Y')
        monthsFmt = mdates.DateFormatter('%m')

        # TODO: check len of date range and adjust labels accordingly
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        ax.xaxis.set_minor_locator(months)

        s = df.groupby(['Sensor']).count()

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

    def _fpStyleFunction(self, feature):
        """
        Style Function for Footprints
        """
        return {
            'fillOpacity': 0.0,
            'weight': 1,
            'fillColor': 'red',
            'color': 'red',
            'opacity': 0.5
        }

    def _fpUnionStyleFunction(self, feature):
        """
        Style Function for Unioned Footprints
        """
        return {
            'fillOpacity': 0.75,
            'weight': 1,
            'fillColor': 'green',
            'color': 'green',
            'opacity': 0.5
        }

    def mapSearchFootprintsAOI(self, df, aoi):
        """
        Map the footprints of the results in relation to the AOI
        """
        # TODO: this needs better symbology

        shp = shapely.wkt.loads(aoi)
        geojson = shapely.geometry.mapping(shp)
        loc = self._convertAOItoLocation(aoi)
        m = folium.Map(location=loc, zoom_start=8, tiles='Stamen Terrain')
        folium.GeoJson(
            geojson,
            name='geojson'
        ).add_to(m)
        for i, row in df.iterrows():
            shp = shapely.wkt.loads(row['Footprint WKT'])
            geojson = shapely.geometry.mapping(shp)
            folium.GeoJson(
                geojson,
                style_function=self._fpStyleFunction,
                name=str(i)
            ).add_to(m)

        # add the union footprints to map
        fp_json = self._aoiFootprintCalculations(df, aoi)[1]
        folium.GeoJson(
            fp_json,
            style_function=self._fpUnionStyleFunction,

        ).add_to(m)
        return m

    def _getUTMProj(self, aoi):
        """
        Determine the UTM Proj for an AOI
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
        to_p = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', hemisphere=hem)

        return to_p

    def _getLLUTMProj(self, latitude, longitude):
        """
        Determine the UTM Proj for a LatLong
        """
        # find the UTM info
        utm_def = utm.from_latlon(latitude, longitude)
        zone = utm_def[-2]
        # convert UTM zone info to something pyproj can understand
        if latitude < 0:
            hem = 'south'
        else:
            hem = 'north'
        to_p = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', hemisphere=hem)

        return to_p

    def aoiArea(self, aoi):
        """
        Get the UTM projection string for an AOI centroid
        """
        shp = shapely.wkt.loads(aoi)
        to_p = self._getUTMProj(aoi)
        from_p = pyproj.Proj(init='epsg:4326')

        project = partial(pyproj.transform, from_p, to_p)
        shp_utm = transform(project, shp)
        # calculate area of projected units in km2
        km2 = shp_utm.area / 1000000.

        return km2


    sensor_colors = {
        'GE01_Pan' : {
            'plot_color' : '#fd8d3c'
        },
        'GE01_MS' : {
            'plot_color' : '#fdbe85'
        },
        'GE01_Pansharpened' : {
            'plot_color' : '#e6550d'
        },
        'WV01_Pan' : {
            'plot_color' : '#969696'
        },
        'WV02_Pan' : {
            'plot_color' : '#3182bd'
        },
        'WV02_MS' : {
            'plot_color' : '#6baed6'
        },
        'WV02_Pansharpened' : {
            'plot_color' : '#006d2c'
        },
        'WV03_Pan' : {
            'plot_color' : '#31a354'
        },
        'WV03_MS' : {
            'plot_color' : '#74c476'
        },
        'WV03_Pansharpened' : {
            'plot_color' : '#238b45'
        },
        'WV03_SWIR' : {
            'plot_color' : '#bae4b3'
        },
        'WV04_Pan' : {
            'plot_color' : '#756bb1'
        },
        'WV04_MS' : {
            'plot_color' : '#9e9ac8'
        },
        'WV04_Pansharpened' : {
            'plot_color' : '#54278f'
        }}


    def mapGB(self, gb=None, aoi=[39.742043, -104.991531]):
        """
        Function to map GB to sensor areas given bands and resolution
        User can input a point lon, lat or the Polygon AOI from which
        a centroid  will be calculated
        """
        # convert GB to df
        df = self.gb_to_km2(gb)

        df = df.sort_values(by=['Area (km2)'], ascending=False)

        # if user passes in Polygon AOI, convert to Folium location
        if isinstance(aoi, str):
            aoi = self._convertAOItoLocation(aoi)

        # TODO: add legend
        # TODO: could add some logic to control zoom level
        # TODO: add more info to popup, such as area
        # TODO: add pansharpened area calculation and plot on map
        m = folium.Map(location=aoi, zoom_start=8, tiles='Stamen Terrain')
        for i, row in df.iterrows():
            folium.Circle(
                radius=np.sqrt(row['Area (km2)'] / np.pi) * 1000,
                location=aoi,
                tooltip=row['Sensor'],
                color=self.sensor_colors[row['Sensor']]['plot_color'],
                fill=False,
            ).add_to(m)
        return m
