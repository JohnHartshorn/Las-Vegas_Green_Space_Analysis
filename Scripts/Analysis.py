#Workflow

#set up necessary packages
!pip install geopandas
!pip install bokeh


from bokeh.io import output_file, show,output_notebook
from bokeh.models import ColumnDataSource,ColorBar,HoverTool
from bokeh.transform import linear_cmap
from bokeh.plotting import figure
from bokeh.palettes import Greens9




import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import shape
%matplotlib inline

output_notebook()

#Read in data

parks = gpd.read_file("pk_ccparks.shp")
zipcodes= gpd.read_file("tl_2023_32003_faces.shp")

#Reproject coordinate reference systems to ensure accurate analysis

proj_parks = parks.to_crs("EPSG:26911")
proj_zipcodes = zipcodes.to_crs("EPSG:26911")

#create nearest distance formula for zipcode

nearest = gpd.sjoin_nearest(proj_zipcodes, proj_parks, distance_col= 'nearest_distance_m')

#This builds a new data set with the zipcode information as well as the calculated nearest park in meters


##Convert geometries from geopandas to bokeh format

def gpd_bokeh(df):
    nan = float('nan')
    lons = []
    lats = []
    for i,shape in enumerate(df.geometry.values):
        if shape.geom_type == 'MultiPolygon':
            gx = []
            gy = []
            ng = len(shape.geoms) - 1
            for j,member in enumerate(shape.geoms):
                xy = np.array(list(member.exterior.coords))
                xs = xy[:,0].tolist()
                ys = xy[:,1].tolist()
                gx.extend(xs)
                gy.extend(ys)
                if j < ng:
                    gx.append(nan)
                    gy.append(nan)
            lons.append(gx)
            lats.append(gy)

        else:
            xy = np.array(list(shape.exterior.coords))
            xs = xy[:,0].tolist()
            ys = xy[:,1].tolist()
            lons.append(xs)
            lats.append(ys)

    return lons,lats


#ColumnDataSource contains geometry and attributes
#Use the nearest dataset

lons, lats = gpd_bokeh(nearest)
source = ColumnDataSource(data=dict(
    	x=lons,
    	y=lats,
        zipcode_id = nearest['ZCTA5CE20'],
        nearest_park = nearest['nearest_distance_m'],
        park_name = nearest['PKNAME']))


##create a color mapping function to convert numeric data into colors for your map.


color_mapper = linear_cmap(field_name='nearest_park', palette=Greens9,
                           low=min(nearest['nearest_distance_m']),
                           high=20000)
TOOLS = "pan,wheel_zoom,reset,hover,save"


#create the Bokeh map canvas

map = figure(frame_width=700, frame_height=600,title="Park Proximity Map, Las Vegas Nevada", tools=TOOLS,
             x_range=(xmin, xmax), y_range=(ymin, ymax))
map.patches('x', 'y', source=source, line_color="white", line_width=0.1, color=color_mapper)

map.select_one(HoverTool).tooltips = [
    ('Park Name', '@park_name'),
    ('Distance to Park(M)', '@nearest_park'),
     ('zip_code', '@zipcode_id')
]

color_bar = ColorBar(color_mapper=color_mapper['transform'], width=16, location=(0,0))
map.add_layout(color_bar, 'right')


show(map)
