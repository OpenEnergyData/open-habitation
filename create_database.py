import pandas as pd
import psycopg2 as pg
import sqlalchemy
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from pyproj import Transformer
import numpy as np
import dotenv
import os

dotenv.load_dotenv()

# host = os.getenv("POSTGRES_HOST")
# port = os.getenv("POSTGRES_PORT")
# username = os.getenv("POSTGRES_USER")
# password = os.getenv("POSTGRES_PASSWORD")
# database = username

# taylored for heroku deployment:
DATABASE_URL = os.environ['DATABASE_URL']


# ------------------------------------------------------------------------------------------------
# Try creating the database if it doesn't exist already <-- NOT REQUIRED FOR HEROKU

# new_database = "geo_admin"

# try:
#     # connection = pg.connect(database=database, user=username, password=password, host=host, port=port)
#     connection = pg.connect(DATABASE_URL, sslmode='require') # for heroku deployment
#     connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#     cursor = connection.cursor()
#     #cursor.execute("CREATE TABLE test (id bigserial, name varchar(10))")
#     cursor.execute("CREATE DATABASE %s" %new_database)
#     cursor.close()
#     connection.close()
#     print("Created database '%s'" %new_database)
# except pg.errors.DuplicateDatabase:
#     while True:
#         confirmation = input("Database '%s' already exists. Do you want to continue (y/n)?" %new_database)
#         if confirmation=="y" or confirmation=="Y":
#             break
#         elif confirmation=="n" or confirmation=="N":
#             print("Database set-up aborted.")
#             sys.exit()
#         else:
#             continue
#     pass



# ------------------------------------------------------------------------------------------------
# Adding all the tables from csv files

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL_SQLALCHEMY = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL_SQLALCHEMY = DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL_SQLALCHEMY)


filenames = {"ElectricityProductionPlant.csv":"electricity_production", "MainCategoryCatalogue.csv":"main_category", "OrientationCatalogue.csv":"orientation",\
                "PlantCategoryCatalogue.csv":"plant_category", "PlantDetail.csv":"plant_detail", "SubCategoryCatalogue.csv":"sub_category"}


for filename, table_name in filenames.items():
    try:
        df = pd.read_csv('./data/ch.bfe.elektrizitaetsproduktionsanlagen/%s' %filename, index_col=0)
        print(df.head(1))
        if filename=="ElectricityProductionPlant.csv":
            # create additional column CompleteAddress which combines street/nr/zipcode/municipality
            df["CompleteAddress"] = df["Address"] + ", " + df["PostCode"].astype(str) + " " + df["Municipality"]
            
            # transform from LV03 to wgs84
            transformer = Transformer.from_crs('EPSG:2056', 'EPSG:4326')
            df["lat"] = df.apply(lambda x: transformer.transform(x._x, x._y)[0], axis=1)
            df["lon"] = df.apply(lambda x: transformer.transform(x._x, x._y)[1], axis=1)
            df = df.replace(np.inf, np.nan)
            print("Added columns 'CompleteAddress', 'lat' and 'lon':")
            print(df.head(1))
        df.to_sql(table_name, engine, if_exists="fail")
        print("Written to table '%s'" %table_name)
    except ValueError as e:
        if str(e) == "Table '%s' already exists." %table_name:
            
            # always overwrite on heroku:
            print("writing to table...")
            df.to_sql(table_name, engine, if_exists="replace")

            # on own server, this might be the more appropriate approach:
            # while True:
            #     answer = input("Table '%s' already exists. Do wou want to overwrite it (o) or skip it (s)?" %table_name)
            #     if answer=="o" or answer=="O":
            #         print("writing to table...")
            #         df.to_sql(table_name, engine, if_exists="replace")
            #         break
            #     elif answer=="s" or answer=="S":
            #         break
            #     else:
            #         continue
            # pass
        else:
            raise e

