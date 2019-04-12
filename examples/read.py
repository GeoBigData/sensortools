from sensortools import sensortools
import os

st = sensortools()

data_dir = os.path.abspath(os.path.join('./data'))
japan_path = os.path.join(data_dir, 'japan_urban.shp')

st.readSHP(japan_path)

