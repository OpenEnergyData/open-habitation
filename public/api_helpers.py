import requests
from pyproj import Transformer
import psycopg2 as pg
import os
import dotenv

dotenv.load_dotenv()


local_database = os.getenv("LOCAL_DATABASE")

if local_database=="true":
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = "openhabitation"

    connection = pg.connect(database=database, user=username, password=password, host=host, port=port)
else:
    # database connection taylored for heroku deployment:
    DATABASE_URL = os.environ['DATABASE_URL']
    connection = pg.connect(DATABASE_URL, sslmode='require')


# def get_production_info(CompleteAddress):

#     cursor = connection.cursor()
#     result = cursor.fetchall()

#     xtf_id = result[0][0]
#     Address = result[0][1]
#     PostCode = result[0][2]
#     Municipality = result[0][3]
#     Canton = result[0][4]
#     BeginningOfOperation = result[0][5]
#     InitialPower = result[0][6]
#     TotalPower = result[0][7]
#     MainCategory = result[0][8]
#     SubCategory = result[0][9]
#     PlantCategory = result[0][10]
#     x = result[0][11]
#     y = result[0][12]
#     CompleteAddress = result[0][13]
#     lat = result[0][14]
#     lon = result[0][15]

# ---------------------------------------------
# FROM DATABASE



def get_house_info(address, angle=35, aspect=60):
    """
    Getting info for a house from the PostgreSQL databases

    Parameters
    ----------
    address : str
        address of the house to get the info for
    angle : str, int or None, optional
        angle of the PV panel (if any), by default 60
    aspect : str, int or None, optional
        aspect of the PV panel (if any), by default 35

    Returns
    -------
    dict
        dictionary containing the information about the house
    """

    response_dict = {}
    response_dict["address"] = address
    response_dict["coordinates"] = {}
    response_dict["summary"] = {}
    response_dict["installations"] = {}
    response_dict["installations"]["electricity_production"] = []
    response_dict["installations"]["space_heating"] = []
    response_dict["installations"]["domestic_hot_water"] = []

    # extract EGID
    cursor = connection.cursor()
    cursor.execute("select \"EGID\", lat, lon from gwr where \"CompleteAddress\"=%s", (address, ))
    result = cursor.fetchall()
    # print("EGID RESULT: ", result)
    if len(result)==0:
        return None
    else:
        egid = result[0][0]
        lat = result[0][1]
        lon = result[0][2]

    response_dict["coordinates"]["lat"] = lat
    response_dict["coordinates"]["lon"] = lon

    # search production plant info
    cursor.execute("select \"TotalPower\", \"PlantType\", \"MountingPlace\", \"BeginningOfOperation\" from electricity_production where \"EGID\"=%s", (egid, ))
    production = cursor.fetchall()
    for plant in production:
        mountingplace = plant[2]
        if mountingplace=="integrated":
            mountingplace_query="building"
        else:
            mountingplace_query="free"
        total_power = plant[0]
        estimated_annual_production = get_pv_gis_data(lat, lon, total_power, None, mountingplace_query, angle, aspect)
        plant_dict = {"plant_type":plant[1], "total_power":total_power, "mountingplace":mountingplace, "estimated_annual_production_kWh": estimated_annual_production, "beginning_of_operation":plant[3]}
        response_dict["installations"]["electricity_production"].append(plant_dict)

    # search space_heating info
    cursor.execute("select \"HeatingType\", \"ConstructionYear\" from heating_info where \"EGID\"=%s and \"InstallationType\"='SH'", (egid, ))
    space_heating = cursor.fetchall()
    # print("HEATING RESULT: ", space_heating)
    for heating in space_heating:
        space_heating_dict = {"heating_type":heating[0], "construction_year":heating[1]}
        response_dict["installations"]["space_heating"].append(space_heating_dict)

    # search hotwater info
    cursor.execute("select \"HeatingType\", \"ConstructionYear\" from heating_info where \"EGID\"=%s and \"InstallationType\"='DHW'", (egid, ))
    hot_water = cursor.fetchall()
    # print("HOTWATER RESULT: ", hot_water)
    for heating in hot_water:
        hot_water_dict = {"heating_type":heating[0], "construction_year":heating[1]}
        response_dict["installations"]["domestic_hot_water"].append(hot_water_dict)

    summary = get_summary(response_dict)

    response_dict["summary"] = summary

    return response_dict


def get_summary(response_dict):
    """
    Determining the summary of house info

    Parameters
    ----------
    response_dict : dict
        dictionary containing info about the production and heating/hot water of a house

    Returns
    -------
    dict
        dictionary containing the summary parameters
    """
    summary = {}

    # calculate total production power if any
    production_plants = response_dict["installations"]["electricity_production"]
    if len(production_plants) > 0:
        total_production_kWh = 0
        for plant in production_plants:
            try:
                total_production_kWh += plant["estimated_annual_production_kWh"]
            except KeyError:
                pass
        summary["estimated_annual_total_production_kWh"] = total_production_kWh
    else:
        summary["estimated_annual_total_production_kWh"] = None

    # classify space-heating
    space_heatings = response_dict["installations"]["space_heating"]
    space_heating_quality = classify_heating_quality(space_heatings)
    summary["space_heating"] = space_heating_quality

    # classify hot water
    domestic_hot_water = response_dict["installations"]["domestic_hot_water"]
    domestic_hot_water_quality = classify_heating_quality(domestic_hot_water)
    summary["domestic_hot_water"] = domestic_hot_water_quality

    return summary


def classify_heating_quality(heatings: list):
    """Classifies heating type into "renewable" or "non-renewable"

    Parameters
    ----------
    heatings : list
        list containing dicts of heating installation info

    Returns
    -------
    str
        "renewable" or "non-renewable"
    """
    heating_types = []
    for heating in heatings:
        try:
            heating_types.append(heating["heating_type"])
        except KeyError:
            pass

    if len(heatings) > 1:
        if "wood (a)" in heating_types:
            heating_types = list(filter(("wood (a)").__ne__, heating_types)) # remove occurrences of "wood (a)"

    heating_qualities = []

    for heating_type in heating_types:
        heating_qualities.append(classify_heating_type(heating_type))

    if "unknown" in heating_qualities:
        return "unknown"
    elif "renewable" in heating_qualities and "non-renewable" in heating_qualities:
        return "unknown"
    elif "renewable" in heating_qualities:
        return "renewable"
    elif "non-renewable" in heating_qualities:
        return "non-renewable"
    else:
        return "unknown"



def classify_heating_type(heating_type: str):
    """
    Classifies the heating type in "renewable", "non-renewable" or unknown

    Parameters
    ----------
    heating_type : str
        heating type
    Returns
    -------
    str
        quality of heating type, one of ["renewable", "non-renewable", "unknown"]
    """

    if heating_type in ["wood (a)", "wood (b)", "wood (c)", "district_heating", "geothermal", "heatpump (air)", "heatpump (water)", "heatpump (geothermal)", "solar"]:
        return "renewable"
    elif heating_type in ["gas", "oil", "biogas", "electricity (resistive)", "heavy oil", "coal"]:
        return "non-renewable"
    else:
        return "unknown"


# ---------------------------------------------
# FROM EXTERNAL API

def get_pv_gis_data(lat, lon, peakpower, loss, mountingplace, angle, aspect):

    # loss: float between 0 and 100
    # mountingplace can be one of ["free", "building"]
    # aspect must be between -180 and 180, where 0 is South, -90 is East and 90 is West

    # if no lat/lon in database, take lat/lon of Bern
    if lat==None:
        lat = 46.94809
    if lon==None:
        lon = 7.44744
    if peakpower==None:
        peakpower=1
    if loss==None:
        loss=14
    if mountingplace==None:
        mountingplace="free"
    if angle==None:
        angle=35
    if aspect==None:
        aspect=60

    url = 'https://re.jrc.ec.europa.eu/api/PVcalc?' + \
          'lat=' + str(lat) + \
          '&lon=' + str(lon) + \
          '&peakpower=' + str(peakpower) + \
          '&loss=' + str(loss) + \
          '&mountingplace=' + mountingplace + \
          '&angle=' + str(angle) + \
          '&aspect=' + str(aspect) + \
          '&outputformat=json'

    try:
        return (requests.get(url).json()['outputs']['totals']['fixed']['E_y'])
    except Exception:
        return None


def calculate_rating(yearly_production=None):
    if yearly_production is None:
        return 'G'
    if yearly_production < 5000:
        return 'E'
    else:
        return 'A'








# ----------------------------------------------------------------------------------
# OLD STUFF

# def get_production_info_string(searchText):
#     url = "https://api3.geo.admin.ch/rest/services/api/MapServer/find?layer=ch.bfe.elektrizitaetsproduktionsanlagen&searchText=%s&searchField=address&contains=true" % (
#         searchText)
#     return requests.get(url)


# def get_production_info(street, nr, zipcode, city):
#     searchText = street + " " + str(nr) + ", " + str(zipcode) + " " + city
#     return get_production_info_string(searchText)


# def get_sub_category(response_json):
#     return response_json["attributes"]["sub_category_en"]


def get_pv_gis_data_old(coordinate_x, coordinate_y):
    # transformer from LV03 to wgs84
    transformer = Transformer.from_crs('EPSG:21781', 'EPSG:4326')
    coordinate_wgs84 = transformer.transform(coordinate_x, coordinate_y)
    lat = coordinate_wgs84[0]
    lon = coordinate_wgs84[1]
    peakpower = 1
    loss = 14
    mountingplace = 'free'
    angle = 35
    aspect = 60

    url = 'https://re.jrc.ec.europa.eu/api/PVcalc?' + \
          'lat=' + str(lat) + \
          '&lon=' + str(lon) + \
          '&peakpower=' + str(peakpower) + \
          '&loss=' + str(loss) + \
          '&mountingplace=' + mountingplace + \
          '&angle=' + str(angle) + \
          '&aspect=' + str(aspect) + \
          '&outputformat=json'

    return (requests.get(url).json()['outputs']['totals']['fixed']['E_y'])

def yearly_production_old(street, nr=None, zipcode=None, city=None):
    try:
        if nr is None:
            response = get_production_info_string(street)
        else:
            response = get_production_info(street, nr, zipcode, city)
    except Exception:
        print("API not available")
        return None

    result_data = response.json()["results"]
    if len(result_data) == 0:
        return None

    try:
        sub_category = get_sub_category(result_data[0])
    except KeyError:
        sub_category = "unknown"

    if response.json()['results'][0]['geometry'] is None:
        return None

    if sub_category == "Photovoltaic":
        coordinate_x = response.json()['results'][0]['geometry']['x']
        coordinate_y = response.json()['results'][0]['geometry']['y']
        return get_pv_gis_data(coordinate_x, coordinate_y)
    else:
        return None



if __name__=="__main__":

    address = "Hallenbadweg 15, 8610 Uster"
    # address = "Schlossstrasse 15, 4147 Aesch BL"
    row = get_electricity_production_row(address)
    print("ROW: ", row)
    total_power = get_total_power(address)
    print(type(total_power))
    print(total_power)
    plant_type = get_plant_type(address)
    print(type(plant_type))
    print(plant_type)
    print(get_coordinates(address))
    print("PV gis data:")

    lat, lon = get_coordinates(address)
    print("lat: ", lat, "lon: ", lon)
    print(get_pv_gis_data(lat, lon))