import pandas as pd
import sqlalchemy
import dotenv
import os


dotenv.load_dotenv()

local_database = os.getenv("LOCAL_DATABASE")

if local_database=="true":
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("DATABASE")

    DATABASE_URL_SQLALCHEMY = "postgresql://" + username +":" + password + "@" + host + ":" + port + "/" + database


else: # taylored for heroku deployment:
    DATABASE_URL = os.environ['DATABASE_URL']

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL_SQLALCHEMY = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL_SQLALCHEMY = DATABASE_URL



# engine = sqlalchemy.create_engine(DATABASE_URL_SQLALCHEMY, execution_options=dict(stream_results=True))
engine = sqlalchemy.create_engine(DATABASE_URL_SQLALCHEMY)


filenames = {"electricityProduction_TABLE.csv":"electricity_production", "gwr_TABLE.csv":"gwr", "heatingInfo_TABLE.csv":"heating_info"}


for filename, table_name in filenames.items():
    try:
        df = pd.read_csv(filename, index_col=0)
        print(df.head(1))
        print("Writing to table %s..." %table_name)
        df.to_sql(table_name, engine, if_exists="fail", chunksize=10000)

    except ValueError as e:
        if str(e) == "Table '%s' already exists." %table_name:

            if local_database=="true":
                # on own server/ local machine
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
                # always overwrite on heroku:
                print("writing to table...")
                df.to_sql(table_name, engine, if_exists="replace")

        else:
            raise e