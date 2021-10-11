import urllib.request
import zipfile
    
url = "https://data.geo.admin.ch/ch.bfe.elektrizitaetsproduktionsanlagen/csv/2056/ch.bfe.elektrizitaetsproduktionsanlagen.zip"
filehandle, _ = urllib.request.urlretrieve(url)
zip_file_object = zipfile.ZipFile(filehandle, 'r')

for filename in zip_file_object.namelist():
    zip_file_object.extract(filename, path="./data/ch.bfe.elektrizitaetsproduktionsanlagen")
    print("Extracted: ", filename)


