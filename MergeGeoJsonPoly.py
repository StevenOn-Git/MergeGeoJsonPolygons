import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from AllThingsClick import GetClickObject, environmentUsr, environmentPwd, prodObjectCheck, UpdateClickObject
import json

"""
    Description: Grab Working Area GeoJSON objects from Click, merge polygons together, and retrieve the merged
                 geoJSON to update the working area in click.
                 
    Version:
        -Original Release - Steve On 20240618
        -Changed manual polygon association to for loop - Steve On 20240619
"""


def prod_check(environment):
    """ helper method to utilize a specific URL based on selected user environment"""
    return True if environment.upper() == "PROD" else False


def get_click_url(environment):
    """ helper method to pull the click url"""
    return prodObjectCheck(prod_check(environment))


def get_work_area_polygon(environment, api_filter):
    """ retrieves the working area from click and returns the polygon object"""
    results = GetClickObject("Geometry_SO", api_filter, get_click_url(environment),
                             environmentUsr(environment), environmentPwd(environment))

    # get json string
    geojson_str = results[0]['GeometryGeoJson_SO']

    # convert to json object
    geojson_obj = json.loads(geojson_str)

    # polygon
    return Polygon(geojson_obj['geometry']['coordinates'][0])


def update_click_geometry_so(environment, key, geo_json_string):
    """ updates the working area in click by key and geoJson string"""
    payload = {
        "@objectType": "Geometry_SO",
        "Key": key,
        "GeometryGeoJson_SO": geo_json_string
    }
    UpdateClickObject(payload, get_click_url(environment), environmentUsr(environment), environmentPwd(environment))


# VARIABLES
ENV = "DEV"
zip_code_list = ['95832', '95758', '95757', '95690']
WORKING_AREA_NAME = "MS AREA 8"
GEOMETRY_SO_KEY = 552427520

# MAIN
polygons = []
for zip_code in zip_code_list:
    # get working area polygons from click and append to polygons
    polygons.append(gpd.GeoSeries([get_work_area_polygon(ENV, "$filter=(contains(Name_SO,'" + zip_code + "'))")])[0])

# merge polygons together
boundary = gpd.GeoSeries(unary_union(polygons))

# convert merged polygon to json
merged_json = json.loads(boundary.to_json())
del merged_json['features'][0]['id']
merged_json['features'][0]['properties']['Name'] = WORKING_AREA_NAME

# convert json to json string
new_geometry_geojson = merged_json['features'][0]
new_geometry_geojson_str = json.dumps(new_geometry_geojson)

# Update the new polygon in Click
update_click_geometry_so(ENV, GEOMETRY_SO_KEY, new_geometry_geojson_str)
