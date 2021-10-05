import requests
from pyproj import Transformer
import psycopg2 as pg

host = "0.0.0.0"
port = "5434"
database="geo_admin"
username = "testuser"
password = "test123"

connection = pg.connect(database=database, user=username, password=password, host=host, port=port)


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

    
def get_total_power(CompleteAddress):

    cursor = connection.cursor()
    cursor.execute("select \"TotalPower\" from electricity_production where \"CompleteAddress\"=%s", (CompleteAddress, ))
    result = cursor.fetchall()
    if len(result)==0:
        return None
    else:
        return result[0][0]

def get_plant_type(CompleteAddress):

    cursor = connection.cursor()
    cursor.execute("select * from sub_category where \"Catalogue_id\"=(select \"SubCategory\" from electricity_production where \"CompleteAddress\"=%s)", (CompleteAddress, ))
    result = cursor.fetchall()

    out_dict = {
        "de":None,
        "fr":None,
        "it":None,
        "en":None
    }

    if len(result)==0:
        return out_dict
    else:
        out_dict["de"] = result[0][1]
        out_dict["fr"] = result[0][2]
        out_dict["it"] = result[0][3]
        out_dict["en"] = result[0][4]
        return out_dict


def get_coordinates(CompleteAddress):

    cursor = connection.cursor()
    cursor.execute("select lat, lon from electricity_production where \"CompleteAddress\"=%s", (CompleteAddress, ))
    result = cursor.fetchall()
    print(result)
    print(result[0][0])
    lat = result[0][0]
    lon = result[0][1]

    return lat, lon


def get_production_info_string(searchText):
    url = "https://api3.geo.admin.ch/rest/services/api/MapServer/find?layer=ch.bfe.elektrizitaetsproduktionsanlagen&searchText=%s&searchField=address&contains=true" % (
        searchText)
    return requests.get(url)


def get_production_info(street, nr, zipcode, city):
    searchText = street + " " + str(nr) + ", " + str(zipcode) + " " + city
    return get_production_info_string(searchText)


def get_sub_category(response_json):
    return response_json["attributes"]["sub_category_en"]


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


def get_pv_gis_data(lat, lon, peakpower=1, loss=14, mountingplace="frees", angle=35, aspect=60):

    # loss: float between 0 and 100
    # mountingplace can be one of ["free", "building"] 
    # aspect must be between -180 and 180, where 0 is South, -90 is East and 90 is West

    # if no lat/lon in database, take lat/lon of Bern
    if lat==None:
        lat = 46.94809
    if lon==None:
        lon = 7.44744

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


def yearly_production(CompleteAddress):

    plant_type = get_plant_type(CompleteAddress)
    lat, lon = get_coordinates(CompleteAddress)

    if plant_type["en"] == "Photovoltaic":
        return get_pv_gis_data(lat, lon)
    else:
        return None

def calculate_rating(yearly_production=None):
    if yearly_production is None:
        return 'G'
    if yearly_production < 5000:
        return 'E'
    else:
        return 'A'


def calculate_results(searchText):
    output = {}
    output['address'] = searchText
    output['yearly_production'] = yearly_production(searchText)
    output['eco_rating'] = calculate_rating(output['yearly_production'])

    try:
        response = get_production_info_string(searchText)
        result_data = response.json()["results"]
        if len(result_data) == 0:
            # No address found
            return None
        output['category'] = get_sub_category(result_data[0])
        output['total_power'] = result_data[0]["attributes"]["total_power"]
    except:
        output['category'] = 'no data'
        output['total_power'] = -1

    return output


if __name__=="__main__":

    address = "Hallenbadweg 15, 8610 Uster"
    # address = "Schlossstrasse 15, 4147 Aesch BL"
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