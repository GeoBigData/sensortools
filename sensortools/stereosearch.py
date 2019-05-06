import geopandas as gpd
from datetime import timedelta
import numpy as np
import math


def _ground_to_sat_vector(taz, ona):
    """
    Get a normalized vector from the ground to the satellite.

    :param taz: Target azimuth of the image
    :param ona: Off-nadir angle of the image
    """

    # Get the reverse target azimuth (from ground to satellite)
    rev_taz = (taz + 180.) % 360

    return np.array([
        math.cos((90 - rev_taz) * (math.pi / 180)) * math.cos((90 - ona) * (math.pi / 180)),
        math.sin((90 - rev_taz) * (math.pi / 180)) * math.cos((90 - ona) * (math.pi / 180)),
        math.sin((90 - ona) * (math.pi / 180))
    ])


def _get_stereo_angles(taz1, ona1, taz2, ona2):
    """
    Computes the stereo angles based on the Target Azimuth and Off-Nadir Angle for each image.

    :param taz1: Target Azimuth for first image
    :param ona1: Off-nadir angle for first image
    :param taz2: Target Azimuth for second image
    :param ona2: Off-nadir angle for second image
    """

    # Compute the normalized vector from ground to satellite
    q1 = _ground_to_sat_vector(taz1, ona1)
    q2 = _ground_to_sat_vector(taz2, ona2)

    # Compute normalized sum of both vectors
    q1_q2_sum = (q1 + q2) / np.linalg.norm(q1 + q2)

    # Compute the normal to both vectors using the cross product
    q1_q2_cross = np.cross(q1, q2) / np.linalg.norm(np.cross(q1, q2))

    # Compute the normal to this cross-product and the normalized z vector using the cross product
    z_vector = np.array([0, 0, 1])
    z_cross = np.cross(
        q1_q2_cross,
        np.cross(
            z_vector,
            q1_q2_cross
        )
    )
    # Normalize it
    z_cross = z_cross / np.linalg.norm(z_cross)

    return {
        'convergence': math.acos(np.dot(q1, q2)) * (180 / math.pi),
        'asymmetry': math.acos(np.dot(q1_q2_sum, z_cross)) * (180 / math.pi),
        'roll': math.asin(abs(np.dot(q1_q2_cross, z_vector))) * (180 / math.pi),
        'bisector_elevation': math.asin(np.dot(q1_q2_sum, z_vector)) * (180 / math.pi)
    }


def find_stereo_pairs(
        df,
        aoi,
        days_tolerance,
        max_convergence,
        min_convergence,
        max_asymmetry,
        max_roll,
        min_bie_conv_diff,
        resolution_tolerance=0.1,
        track_type='in-track'
):
    """
    Find matching stereo pairs based on the criteria given in the arguments.
    :param df: A GeoDataFrame based on the outputs of sensortools.formatSearchResults
    :param aoi: A shapely geometry object of the aoi over which to look for stereo pairs
    :param resolution_tolerance: The amount (in meters) that the resolution of two images can vary
    :param days_tolerance: The allowable difference (in days) between the collections within a stereo pair
    :param max_convergence: The maximum allowable convergence angle between the images (in degrees). Defaults to 60.
    :param min_convergence: The minimum allowable convergence angle between the images (in degrees). Defaults to 15.
    :param max_asymmetry: The maximum allowable asymmetry angle between the images (in degrees). Defaults to 30.
    :param max_roll: The maximum allowable roll angle between the images (in degrees). Defaults to 15.
    :param min_bie_conv_diff: The maximum allowable difference between the bisector elevation and convergence angle
    (in degrees). Defaults 15.
    :param track_type: Whether to restrict to in-track, cross-track, or both.
    """
    # Convert the days_tolerance into a datetime.timedelta interval
    date_tolerance = timedelta(days=days_tolerance)

    def should_keep(row):
        """
        Determines whether a row should be kept based on whether the images:
        * meet criteria for stereo angles
        * have similar resolutions
        * are within a certain date range of each other
        """
        similar_resolutions = abs(row['panResolution_left'] - row['panResolution_right']) < resolution_tolerance
        similar_dates = abs(row['timestamp_left'] - row['timestamp_right']) < date_tolerance
        if not (similar_resolutions and similar_dates):
            return False

        convergence_check = min_convergence < row['convergence'] < max_convergence
        asymmetry_check = row['asymmetry'] < max_asymmetry
        roll_check = row['roll'] < max_roll
        bie_conv_diff_check = (row['bisector_elevation'] - row['convergence']) > min_bie_conv_diff
        if not (convergence_check and asymmetry_check and roll_check and bie_conv_diff_check):
            return False

        return True

    def add_stereo_angles(row):
        """Adds the stereo angles to the given row."""
        new_row = row.copy()

        stereo_angles = _get_stereo_angles(
            row['targetAzimuth_left'],
            row['offNadirAngle_left'],
            row['targetAzimuth_right'],
            row['offNadirAngle_right']
        )
        new_row['convergence'] = stereo_angles['convergence']
        new_row['asymmetry'] = stereo_angles['asymmetry']
        new_row['roll'] = stereo_angles['roll']
        new_row['bisector_elevation'] = stereo_angles['bisector_elevation']

        return new_row

    # Compute the cross-join
    cross_join = gpd.sjoin(df, df, how='inner', op='intersects')
    cross_join = cross_join[cross_join['catalogID_left'] != cross_join['catalogID_right']]

    # Filter based on the criteria above
    cross_join = cross_join.apply(add_stereo_angles, axis=1)

    filtered = cross_join.copy(deep=True)
    filtered['keep'] = filtered.apply(should_keep, axis=1)
    filtered = filtered[filtered.keep is True]
    filtered.drop('keep', 1, inplace=True)

    # Remove any identical pairs
    filtered['ordered_pair'] = filtered.apply(
        lambda row: ':'.join(sorted([row['catalogID_left'], row['catalogID_right']])), axis=1)
    filtered.drop_duplicates(subset=['ordered_pair'], inplace=True)
    filtered.drop('ordered_pair', 1, inplace=True)

    # Filter based on the track type
    def is_in_track(row):
        same_sensor = row['catalogID_left'][:3] == row['catalogID_right'][:3]
        same_day = (abs(row['timestamp_left'] - row['timestamp_right']).total_seconds() // 3600) < 24

        return same_sensor and same_day

    filtered['in_track'] = filtered.apply(is_in_track, axis=1)

    if track_type == 'in-track':
        filtered = filtered[filtered.in_track.astype(bool)]
    elif track_type == 'cross-track':
        filtered = filtered[~filtered.in_track.astype(bool)]
    elif track_type == 'both':
        pass
    else:
        raise ValueError("track_type must be one of 'in-track', 'cross-track', or 'both'.")

    # Find the intersection of the two images
    filtered['stereoGeom'] = filtered.apply(
        lambda row: row['footprintGeom_left'].intersection(row['footprintGeom_right']).buffer(0).simplify(0.000001),
        axis=1
    )

    # Check that the stereoGeom intersects the AOI
    def intersects_aoi(row):
        return row['stereoGeom'].intersects(aoi)

    filtered['intersectsAoi'] = filtered.apply(intersects_aoi, axis=1)
    filtered = filtered[filtered['intersectsAoi'] is True]

    # Format the final DataFrame
    final_pairs = filtered[[
        'catalogID_left',
        'timestamp_left',
        'catalogID_right',
        'timestamp_right',
        'stereoGeom',
        'convergence',
        'asymmetry',
        'roll',
        'bisector_elevation',
        'in_track'
    ]]
    final_pairs = final_pairs.rename(
        index=str,
        columns={
            'catalogID_left': 'catalogID_1',
            'timestamp_left': 'timestamp_1',
            'catalogID_right': 'catalogID_2',
            'timestamp_right': 'timestamp_2'
        }
    )
    final_pairs.set_index(['catalogID_1', 'catalogID_2'], inplace=True)

    return final_pairs
