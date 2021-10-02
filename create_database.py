import pandas as pd
import psycopg2 as pg
import sqlalchemy
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

host = "0.0.0.0"
port = "5434"
database="postgres"
username = "testuser"
password = "test123"


# ------------------------------------------------------------------------------------------------
# Try creating the database if it doesn't exist already

new_database = "geo_admin"

try:
    connection = pg.connect(database=database, user=username, password=password, host=host, port=port)
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    #cursor.execute("CREATE TABLE test (id bigserial, name varchar(10))")
    cursor.execute("CREATE DATABASE %s" %new_database)
    cursor.close()
    connection.close()
    print("Created database '%s'" %new_database)
except pg.errors.DuplicateDatabase:
    while True:
        confirmation = input("Database '%s' already exists. Do you want to continue (y/n)?" %new_database)
        if confirmation=="y" or confirmation=="Y":
            break
        elif confirmation=="n" or confirmation=="N":
            print("Database set-up aborted.")
            sys.exit()
        else:
            continue
    pass



# ------------------------------------------------------------------------------------------------
# Adding all the tables from csv files

engine = sqlalchemy.create_engine('postgresql+psycopg2://%s:%s@%s:%s/%s' %(username, password, host, port, new_database))

# df_test = pd.DataFrame({"col1":[1,2,3,4], "col2":[4,3,2,1]})
# df_test.to_sql("test_table", engine)

filenames = {"ElectricityProductionPlant.csv":"electricity_production", "MainCategoryCatalogue.csv":"main_category", "OrientationCatalogue.csv":"orientation",\
                "PlantCategoryCatalogue.csv":"plant_category", "PlantDetail.csv":"plant_detail", "SubCategoryCatalogue.csv":"sub_category"}


for filename, table_name in filenames.items():
    try:
        df = pd.read_csv('./data/ch.bfe.elektrizitaetsproduktionsanlagen/%s' %filename, index_col=0)
        print(df.head(1))
        if filename=="ElectricityProductionPlant.csv": # create additional column CompleteAddress which combines street/nr/zipcode/municipality
            df["CompleteAddress"] = df["Address"] + ", " + df["PostCode"].astype(str) + " " + df["Municipality"]
            print("Added column 'CompleteAddress':")
            print(df.head(1))
        df.to_sql(table_name, engine, if_exists="fail")
        print("Written to table '%s'" %table_name)
    except ValueError as e:
        if str(e) == "Table '%s' already exists." %table_name:
            while True:
                answer = input("Table '%s' already exists. Do wou want to overwrite it (o) or skip it (s)?" %table_name)
                if answer=="o" or answer=="O":
                    print("writing to table...")
                    df.to_sql(table_name, engine, if_exists="replace")
                    break
                elif answer=="s" or answer=="S":
                    break
                else:
                    continue
            pass
        else:
            raise e

