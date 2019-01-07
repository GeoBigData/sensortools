import pandas as pd
import numpy as np
import folium
import fiona
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
        # pricing table
        self.gbdx_pricing_table = None
        # IPP pricing table
        self.ipp_pricing_table = None
        # Compute costs
        self.compute_fee=0.65
        self.imagery_fee=4.5
        self.compute_cost=0.4
        self.imagery_cost=0.1

    def setGBDXPricingTable(self, df):
        self.gbdx_pricing_table = df

    def setIPPPricingTable(self, df):
        self.ipp_pricing_table = df

    def addCustomTier(self, subscription, tier, cost, gb, compute, sales, mac, rev_share, claw_back):

        self.gbdx_pricing_table = self.gbdx_pricing_table.append( \
            pd.DataFrame({
                    'Subscription': [subscription],
                    'Tier': [tier],
                    'Cost': [cost],
                    'GB': [gb],
                    'Compute': [compute],
                    'Partner Sales': [sales],
                    'MAC': [mac],
                    'Revenue Share': [rev_share],
                    'Claw Back': [claw_back]
            })).reset_index().drop(columns=['index'])

    def deleteTier(self, subscription, tier):
        """
        Remove pricing tier given both Subscription and Tier designation
        """
        g = self.gbdx_pricing_table
        g = g.drop(index=g[(g['Subscription']==subscription) & (g['Tier']==tier)].index)
        self.gbdx_pricing_table = g

    def editGBDXTier(self, subscription, tier, variable, value):
        """
        Edit a GBDX Subcription Variable
        """
        g = self.gbdx_pricing_table
        idx = g[(g['Subscription']==subscription) & (g['Tier']==tier)].index
        g.loc[idx, variable] = value
        self.gbdx_pricing_table = g

    def editIPPTier(self, sensor, variable, value):
        """
        Edit a IPP Subcription Variable
        """
        g = self.ipp_pricing_table
        idx = g[g.Sensor==sensor].index
        g.loc[idx, variable] = value
        self.ipp_pricing_table = g

    def pricing(self, sensor=None, gb_tier=None):
        """

        """
        dfs = []

        if gb_tier:
            g = self.gbdx_pricing_table[self.gbdx_pricing_table['GB']==gb_tier]
        else:
            g = self.gbdx_pricing_table

        for i, row in g.iterrows():
            df = self._gbdx_detailed_pricing(row['Subscription'], row['Tier'],
                row['Cost'], row['GB'], row['Compute'], row['Partner Sales'],
                row['MAC'], row['Revenue Share'], row['Claw Back'], sensor)
            dfs.append(df)

        gbdx_price = pd.concat(dfs, axis=0)

        ipp = self._ipp_detailed_pricing(gbdx_price)

        df = pd.concat([gbdx_price, ipp])

        return df

    def _ipp_detailed_pricing(self, df):
        """
        IPP Pricing is performed as a comparison to GBDX Pricing
        """
        df = pd.DataFrame(df.groupby(['Sensor', 'Resolution (m)', 'Band Count', 'Area (km2)', 'GB']).size()).reset_index()
        df = df[df.columns[0:-1]]
        df = df.merge(self.ipp_pricing_table, on='Sensor')

        # if sales * rev share <= MAC
        idx = df['Partner Sales'] * df['Revenue Share'] <= df['MAC']

        df.loc[idx, 'Partner Payment $'] = df.loc[idx, 'Area (km2)'] * \
            df.loc[idx, 'Cost $/km2'] * df.loc[idx, 'Discount Rate'] + df.loc[idx, 'MAC']

        df.loc[~idx, 'Partner Payment $'] = df.loc[~idx, 'Area (km2)'] * \
        df.loc[~idx, 'Cost $/km2'] * df.loc[~idx, 'Discount Rate'] + df['MAC'] + \
        ((df.loc[~idx, 'Partner Sales'] * df.loc[~idx, 'Revenue Share']) - \
        df.loc[~idx, 'MAC']) - (df.loc[~idx, 'Claw Back'] * (df.loc[~idx, 'Area (km2)'] * \
        df.loc[~idx, 'Cost $/km2'] * df.loc[~idx, 'Discount Rate']))

        # IPP Partner Retained Revenue
        df['Partner Revenue $'] = df['Partner Sales'] - df['Partner Payment $']

        # IPP DG Profit
        df['Profit $'] = (df['Partner Payment $']).astype(np.int)

        # IPP $/GB
        df['Partner $/GB'] = (df['Partner Payment $'] / df['GB']).astype(np.int)

        # IPP $/km2
        df['Partner $/km2'] = (df['Partner Payment $'] / df['Area (km2)']).astype(np.int)

        df['Subscription'] = 'IPP'
        df['Tier'] = 'N/A'
        df['Compute'] = 0
        df['Internal Costs $'] = 0
        df['Subscription Cost $'] = 0

        df = df.drop(columns=['Cost $/km2', 'Discount Rate'])

        return df

    def _gbdx_detailed_pricing(self, subscription, tier, cost, gb, compute, sales,
            mac, rev_share, claw_back, sensor):
        """
        Detailed Tier Pricing. Used primarily to determine $/km2 to be used in
        self.pricing method.
        """
        if gb:
            df = self.gb_to_km2(gb=gb)
            df['GB'] = gb
        elif km2:
            df = self.km2_to_gb(km2=km2)
            df['Area (km2)'] = km2
        if sensor:
            df = df[df.Sensor.isin(sensor)]

        df['Subscription'] = subscription
        df['Tier'] = tier
        df['Compute'] = compute
        df['Subscription Cost $'] = cost
        df['Partner Sales'] = sales
        df['Revenue Share'] = rev_share
        df['MAC'] = mac
        df['Claw Back'] = claw_back

        # DG Costs (Year 1)
        df['Internal Costs $'] = ((df['Compute'] * self.compute_cost) + (df['GB'] * self.imagery_cost)).astype(np.int)

        # GBDX Partner Payment to DG
        if sales * rev_share <= mac:
            df['Partner Payment $'] = df['Subscription Cost $'] + mac
        else:
            df['Partner Payment $'] = df['Subscription Cost $'] + mac + \
                ((sales * rev_share) - mac) - \
                (claw_back * df['Subscription Cost $'])

        # GBDX Partner Retained Revenue
        df['Partner Revenue $'] = df['Partner Payment $'] - df['Partner Payment $']

        # GBDX DG Profit
        df['Profit $'] = (df['Partner Payment $'] - df['Internal Costs $']).astype(np.int)

        # GBDX Partner $/GB
        df['Partner $/GB'] = (df['Partner Payment $'] / df['GB']).astype(np.int)

        # GBDX Partner $/km2
        df['Partner $/km2'] = (df['Partner Payment $'] / df['Area (km2)']).astype(np.float)

        return df

    def earthWatchLookup(self, df):
        """
        Given a dataframe with catalog_ids, do a search on WFS for
        EarthWatch IDs
        """

        try:
            with open('ew-connectid.txt', 'r') as a:
                key = a.readlines()[0].rstrip()
        except:
            print('Could not find Connect ID in ./ew-connectid.txt')

        url = """https://securewatch.digitalglobe.com/catalogservice/wfsaccess?SERVICE=
        WFS&VERSION=1.1.0&REQUEST=GetFeature&CONNECTID={key}&TYPENAME=
        DigitalGlobe:FinishedFeature&CQL_FILTER=legacyId=%27{f}%27&propertyName=featureId
        """

        # add placeholder in dataframe
        df['EarthWatchID'] = None

        # iterate the dataframe rows, performing single lookups
        for i, row in df.iterrows():
            resp = requests.get(url.format(key=key, f=row['catalog_id'])).text

            # featureID
            fid = response.text.split('DigitalGlobe:featureId')[1][1:][:-2]

            df.loc[df.catalog_id==row.catalog_id, 'EarthWatchID'] = fid

        return df

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
            pt_buffer = pt_prj.buffer(radius)
            pt_buffer_wgs = transform(project_reverse, pt_buffer)
        elif shape=='square':
            pass

        return pt_buffer_wgs.wkt

    def createAOIFromGeoJSON(self, geojson, epsg):
        """
        Create a simplified WKT AOI from a GeoJSON File
        """
        pass

    def readSHP(self, shapefile):
        """
        Read Shapefile and Store in Dataframe with each polygon stored as
        WKT. MUST BE ESPG 4326!
        """
        gid, wkt = [], []
        shape = fiona.open(shapefile)
        for feature in shape:
            gid.append(feature['id'])
            wkt.append(shapely.geometry.shape(feature['geometry']).wkt)

        return pd.DataFrame({'gid': gid, 'WKT': wkt})

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
                'plot_color' : '#fd8d3c'
            },
            'GE01_MS' : {
                'resolution' : 1.64,
                'band_count' : 4,
                'plot_color' : '#fdbe85'
            },
            'WV01_Pan' : {
                'resolution' : 0.5,
                'band_count' : 1,
                'plot_color' : '#969696'
            },
            'WV02_Pan' : {
                'resolution' : 0.46,
                'band_count' : 1,
                'plot_color' : '#3182bd'
            },
            'WV02_MS' : {
                'resolution' : 1.85,
                'band_count' : 8,
                'plot_color' : '#6baed6'
            },
            'WV02_PanSharp': {
                'resolution': 0.46,
                'band_count': 8,
                'plot_color': '#6baed6'
            },
            'WV03_Pan' : {
                'resolution' : 0.31,
                'band_count' : 1,
                'plot_color' : '#006d2c'
            },
            'WV03_MS' : {
                'resolution' : 1.24,
                'band_count' : 8,
                'plot_color' : '#31a354'
            },
            'WV03_SWIR' : {
                'resolution' : 3.7,
                'band_count' : 8,
                'plot_color' : '#74c476'
            },
            'WV03_PanSharp' : {
                'resolution' : 0.31,
                'band_count' : 8,
                'plot_color' : '#bae4b3'
            },
            'WV04_Pan' : {
                'resolution' : 0.31,
                'band_count' : 1,
                'plot_color' : '#756bb1'
            },
            'WV04_MS' : {
                'resolution' : 1.24,
                'band_count' : 4,
                'plot_color' : '#9e9ac8'}
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

        file_bytes = gb * 1e+9
        storage_bytes = bit_depth / 8.

        km2 = self.sensors.apply(lambda row: ((np.sqrt(file_bytes /
                             (row['Band Count'] * storage_bytes)) * row['Resolution (m)']) / 1000) ** 2, axis=1)

        df = pd.concat([self.sensors, km2.rename('Area (km2)').astype(np.int)], axis=1)

        # Using a ratio of km2/GB for WV2/WV3 Pansharp
        df.loc[df.Sensor=='WV03_PanSharp', 'Area (km2)'] = gb * 16.017
        df.loc[df.Sensor=='WV02_PanSharp', 'Area (km2)'] = gb * 35.394

        return df

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
        sqkm = (pixel_count * self.sensors['Band Count'] * (bit_depth / 8.)) / 1e+9

        df = pd.concat([self.sensors, sqkm.rename('GB')], axis=1)

        df.loc[df.Sensor=='WV03_PanSharp', 'GB'] = df.loc[df.Sensor=='WV03_Pan'].GB.values + df.loc[df.Sensor=='WV03_MS'].GB.values
        df.loc[df.Sensor=='WV02_PanSharp', 'GB'] = df.loc[df.Sensor=='WV02_Pan'].GB.values + df.loc[df.Sensor=='WV02_MS'].GB.values

        return df

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
        df['Cloud WKT'] = ''

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
            df.loc[df['catalog_id']==c, 'Cloud WKT'] = cloud.wkt

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
        cat, s, t, c, n, e, f, i, k = [], [], [], [], [], [], [], [], []
        for j, re in enumerate(search_results):
            cat.append(re['identifier'])
            s.append(re['properties']['sensorPlatformName'])
            t.append(re['properties']['timestamp'])
            # Catches for Landsat and RadarSat images missing these properties
            try:
                c.append(re['properties']['cloudCover'])
            except:
                c.append(0)
            try:
                n.append(re['properties']['offNadirAngle'])
            except:
                n.append(0)
            try:
                e.append(re['properties']['sunElevation'])
            except:
                e.append(0)
            f.append(re['properties']['footprintWkt'])
            i.append(self._fpaoiinter(re['properties']['footprintWkt'], aoi))
            k.append(self.aoiArea(re['properties']['footprintWkt']))

        df = pd.DataFrame({
            'catalog_id': cat,
            'Sensor': s,
            'Date': pd.to_datetime(t),
            'Cloud Cover': c,
            'Off Nadir Angle': n,
            'Sun Elevation': e,
            'Footprint WKT': f,
            'Footprint Area (km2)': k,
            'Footprint AOI Inter Percent': i},
            index=pd.to_datetime(t))
        df.sort_values(['Date'], inplace=True)
        df['x'] = range(len(df))

        return df

    def searchDistPlot(self, df, var, sensor=None):
        """
        Create a Distribution plot of one variable. Optionally, subset by sensor
        """
        if sensor:
            df = df.loc[df.Sensor==sensor]
        sns.distplot(df[var])

        return None

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

        sns.stripplot(x="Date", y="Sensor",
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
            name='geojson
        ).add_to(m)

        return m

    def _fpStyleFunction(self, feature):
        """
        Style Function for Footprints
        """
        return {
            fillOpacity': 0.0,
            'weight': 1,
            'fillColor': 'red',
            'color': 'red',
            'opacity': 0.5
        }

    def _CloudStyleFunction(self, feature):
        """
        Style Function for Footprints
        """
        return {
            'fillOpacity': 0.5,
            'weight': 1,
            'fillColor': 'blue',
            'color': 'blue',
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

    def mapClouds(self, df, aoi):
        """
        Given formatted search results with cloud cover WKT, map against AOI
        Caution: should limit how many results are mapped
        """

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

        for i, row in df.iterrows():
            shp = shapely.wkt.loads(row['Cloud WKT'])
            geojson = shapely.geometry.mapping(shp)
            folium.GeoJson(
                geojson,
                style_function=self._CloudStyleFunction,
                name=str(i)
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
                color=self._sensorInfo()[row['Sensor']]['plot_color'],
                fill=False,
            ).add_to(m)
        return m
