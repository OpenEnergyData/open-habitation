import requests
import json


#def get_electricity_production_info(street, nr, zipcode, city):
def get_electricity_production_info(street, nr=None, zipcode=None, city=None):
    
    search_input = [street]

    if nr != None:
        search_input.append(str(nr))
    if zipcode != None:
        search_input.append(str(zipcode))
    if city != None:
        search_input.append(city)

    searchText = " ".join(search_input)
    print(searchText)
    url = "https://api3.geo.admin.ch/rest/services/api/MapServer/find?layer=ch.bfe.elektrizitaetsproduktionsanlagen&searchText=%s&searchField=address&contains=true" % (searchText)

    return requests.get(url)



test = get_electricity_production_info("Dorfstrasse 17,", zipcode=6332, city="Hagendorn")

print(json.dumps(test.json()))

#Rebenweid 27, 6332 Hagendorn
  	#6300 	 	
# def get_production_info_string(searchText):
#     url = "https://api3.geo.admin.ch/rest/services/api/MapServer/find?layer=ch.bfe.elektrizitaetsproduktionsanlagen&searchText=%s&searchField=address&contains=true" % (
#         searchText)
#     return requests.get(url)


# def get_production_info(street, nr, zipcode, city):
#     searchText = street + " " + str(nr) + ", " + str(zipcode) + " " + city
#     return get_production_info_string(searchText)


# def get_sub_category(response_json):
#     return response_json["attributes"]["sub_category_en"]


# def get_pv_gis_data(coordinate_x, coordinate_y):
#     # transformer from LV03 to wgs84
#     transformer = Transformer.from_crs('EPSG:21781', 'EPSG:4326')
#     coordinate_wgs84 = transformer.transform(coordinate_x, coordinate_y)
#     lat = coordinate_wgs84[0]
#     lon = coordinate_wgs84[1]
#     peakpower = 1
#     loss = 14
#     mountingplace = 'free'
#     angle = 35
#     aspect = 60

#     url = 'https://re.jrc.ec.europa.eu/api/PVcalc?' + \
#           'lat=' + str(lat) + \
#           '&lon=' + str(lon) + \
#           '&peakpower=' + str(peakpower) + \
#           '&loss=' + str(loss) + \
#           '&mountingplace=' + mountingplace + \
#           '&angle=' + str(angle) + \
#           '&aspect=' + str(aspect) + \
#           '&outputformat=json'

#     return (requests.get(url).json()['outputs']['totals']['fixed']['E_y'])


# def yearly_production(street, nr=None, zipcode=None, city=None):
#     try:
#         if nr is None:
#             response = get_production_info_string(street)
#         else:
#             response = get_production_info(street, nr, zipcode, city)
#     except Exception:
#         print("API not available")
#         return None

#     result_data = response.json()["results"]
#     if len(result_data) == 0:
#         return None

#     try:
#         sub_category = get_sub_category(result_data[0])
#     except KeyError:
#         sub_category = "unknown"

#     if response.json()['results'][0]['geometry'] is None:
#         return None

#     if sub_category == "Photovoltaic":
#         coordinate_x = response.json()['results'][0]['geometry']['x']
#         coordinate_y = response.json()['results'][0]['geometry']['y']
#         return get_pv_gis_data(coordinate_x, coordinate_y)
#     else:
#         return None






