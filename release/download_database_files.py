import pandas as pd

download_paths = {
    "electricityProduction_TABLE.csv": "https://drive.switch.ch/index.php/s/gvQQyntaRACA02C/download",
    "gwr_TABLE.csv": "https://drive.switch.ch/index.php/s/BrJLquqI3aKYlJe/download",
    "heatingInfo_TABLE.csv": "https://drive.switch.ch/index.php/s/KbDql9Acv9SxFYr/download"
}

for key, url in download_paths.items():
    print("Downloading '%s'..." %key)
    df = pd.read_csv(url, index_col=0)
    print("Saving '%s'..." %key)
    # print(df.head())
    df.to_csv("./data/" + key)