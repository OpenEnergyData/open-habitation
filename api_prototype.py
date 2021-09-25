import requests
from pyproj import Transformer


def get_production_info_string(searchText):
    url = "https://api3.geo.admin.ch/rest/services/api/MapServer/find?layer=ch.bfe.elektrizitaetsproduktionsanlagen&searchText=%s&searchField=address&contains=true" % (
        searchText)
    return requests.get(url)

def get_production_info(street, nr, zipcode, city):
    searchText = street + " " + str(nr) + ", " + str(zipcode) + " " + city
    return get_production_info_string(searchText)

def get_sub_category(response):
    return response.json()["results"][0]["attributes"]["sub_category_en"]


def get_total_power(response):
    return response.json()["results"][0]["attributes"]["total_power"]


def yearly_production_old(street, nr, zipcode, city):
    try:
        response = get_production_info(street, nr, zipcode, city)
    except Exception:
        print("API not available")
        return 0

    try:
        response_json = response.json()
    except Exception:
        print("Response could not be converted to json.")

    try:
        sub_category = get_sub_category(response)
    except KeyError:
        sub_category = "unknown"

    try:
        total_power = get_total_power(response)
        total_power = float(total_power[:-3])  # TODO: consider the unity
    except KeyError:
        total_power = 0

    if sub_category == "Photovoltaic":

        yearly_production = total_power * 1000
    elif sub_category == "Wind":
        yearly_production = total_power * 3600
    else:
        yearly_production = -1

    return yearly_production


def get_pv_gis_data(coordinate_x, coordinate_y):
    transformer = Transformer.from_crs('EPSG:21781', 'EPSG:4326')  # transformer from LV03 to wgs84
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


def yearly_production(street, nr=None, zipcode=None, city=None):
    try:
        if nr is None:
            response = get_production_info_string(street)
        else:
            response = get_production_info(street, nr, zipcode, city)
    except Exception:
        print("API not available")
        return 0

    try:
        sub_category = get_sub_category(response)
    except KeyError:
        sub_category = "unknown"

    if sub_category == "Photovoltaic":
        coordinate_x = response.json()['results'][0]['geometry']['x']
        coordinate_y = response.json()['results'][0]['geometry']['y']
        return get_pv_gis_data(coordinate_x, coordinate_y)
    else:
        return 0

def calculate_rating(yearly_production=None):
    if yearly_production is None:
        return 'G'
    if yearly_production < 5000:
        return 'E'
    else:
        return 'A'

def get_minergie(searchText):
    url = "https://api3.geo.admin.ch/rest/services/api/MapServer/find?layer=ch.bfe.minergiegebaeude&searchText=%s&searchField=address&contains=true" % (
        searchText)
    return requests.get(url)



searchText = 'Hauptstrasse 82, 4558 Hersiwil'

def calculate_results(searchText):
    output = {}
    output['address'] = searchText
    output['yearly_production'] = yearly_production(searchText)
    output['eco_rating'] = calculate_rating(output['yearly_production'])

    try:
        response = get_production_info_string(searchText)
        output['category'] = get_sub_category(response)
        output['total_power'] = response.json()["results"][0]["attributes"]["total_power"]
    except:
        output['category'] = 'no data'
        output['total_power'] = -1

    return output
