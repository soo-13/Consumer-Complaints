import os
import requests
import urllib.request
import zipfile
import pandas as pd
from urllib.parse import quote


cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "build")
baseurl = "https://www2.census.gov/programs-surveys/acs/summary_file/"
API_KEY = '68f0c084ed938bea6c3776671fd8017cfbffaa3d' 


def get_geo_path(year):
    if year > 2020:
        return f"{year}/table-based-SF/documentation/Geos{year}5YR.txt"
    else:
        #return f"{year}/documentation/geography/5_year_Mini_Geo.xlsx"
        return f"{year}/data/5_year_entire_sf/{year}_ACS_Geography_Files.zip"

def get_data_path(year):
    if year > 2020:
        return f"{year}/table-based-SF/data/5YRData/5YRData.zip"
    else:
        #return f"{year}/data/5_year_entire_sf/{year}_ACS_Geography_Files.zip"
        return f"{year}/data/5_year_entire_sf/{year}_ACS_Geography_Files.zip"

def download_ACS_dataset(download_dir=os.path.join(cPATH, 'input', 'ACS')):
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    print("Downloading ACS Dataset")

    for year in range(2013, 2024):
        print(f"Downloading ACS Dataset for year {year}")
        local_path = os.path.join(download_dir, str(year))
        if not os.path.exists(local_path):
            os.mkdir(local_path)

        geo_path = get_geo_path(year)
        data_path = get_data_path(year)
        geo_url = baseurl + geo_path
        data_url = baseurl + data_path

        try:
            print(f"Downloading {geo_url} ...")
            geo_local = os.path.join(local_path, os.path.basename(geo_url))
            if not os.path.exists(geo_local):
                urllib.request.urlretrieve(geo_url, geo_local)
        except Exception as e:
            print(f"Failed to download {geo_url}: {e}")

        try:
            print(f"Downloading {data_url} ...")
            data_local = os.path.join(local_path, os.path.basename(data_url))
            if not os.path.exists(data_local):
                urllib.request.urlretrieve(data_url, data_local)
        except Exception as e:
            print(f"Failed to download {data_url}: {e}")

        if os.path.basename(geo_local).endswith(".zip"):
            try:
                with zipfile.ZipFile(geo_local, 'r') as zip_ref:
                    print(f"Extracting {geo_local}")
                    zip_ref.extractall(os.path.join(local_path, "5YearGeoDataset"))
            except Exception as e:
                print(f"[ERROR] Failed to extract {geo_local}: {e}")

        try:
            with zipfile.ZipFile(data_local, 'r') as zip_ref:
                print(f"Extracting {data_local}")
                zip_ref.extractall(os.path.join(local_path, "5YearACSDataset"))
        except Exception as e:
            print(f"[ERROR] Failed to extract {data_local}: {e}")

    print("Finish Downloading ACS Dataset!")

def get_target_variables(year):
    '''
    # list of variables in year > 2020
    DP03_0062E: median household income
    DP02_0059E: educational attainment - population 25 years and over
    DP02_0060E:  educational attainment - population 25 years and over & less than 9th grade
    DP02_0061E:  educational attainment - population 25 years and over & 9th to 12th grade, no diploma
    DP02_0062E:  educational attainment - population 25 years and over & high school graduate (includes equivalency)
    DP02_0063E:  educational attainment - population 25 years and over & some college, no degree
    DP02_0064E:  educational attainment - population 25 years and over & associate's degree
    DP02_0065E:  educational attainment - population 25 years and over & bachelor's degree
    DP02_0066E:  educational attainment - population 25 years and over & graduate or professional degree
    DP02_0112E:  language spoken at home - population 5 years and over 
    DP02_0113E:  language spoken at home - population 5 years and over & english only
    DP02_0114E:  language spoken at home - population 5 years and over & language other than english
    DP02_0115E:  language spoken at home - population 5 years and over & language other than english, speak english less than "very well"
    '''
    variables = ['DP03_0062E'] 
    labels = ['MedIncome', 'EDUCpop', 'EDUC<9', 'EDUC9-12', 'EDUChsg', 'EDUCcll', 'EDUCassc', 'EDUCbch', 'EDUCgrad', 'LANGpop', 'LANGen', 'LANGother', 'LANGless']
    if year > 2020:
        variables.extend([f'DP02_00{num}E' for num in range(59, 67)])
        variables.extend([f'DP02_0{num}E' for num in range(112, 116)])
    elif year > 2018:
        variables.extend([f'DP02_00{num}E' for num in range(59, 67)])
        variables.extend([f'DP02_0{num}E' for num in range(111, 115)]) # change of variable names for "language spoken at home"
    else:
        variables.extend([f'DP02_00{num}E' for num in range(58, 66)]) # change of variable names for "educational attainment"
        variables.extend([f'DP02_0{num}E' for num in range(110, 114)]) # change of variable names for "language spoken at home"
    return variables, labels

def get_ACS_dataset_with_url(download_dir):
    if not os.path.exists(download_dir):
            os.mkdir(download_dir)
    print("Downloading ACS Dataset with URL")

    for year in range(2013, 2024):
        print(f"Downloading ACS Dataset for year {year}")
        savepath = os.path.join(download_dir, f'ACS5YR_{year}.csv')
        if not os.path.exists(savepath):
            variables, labels = get_target_variables(year)
            var_str = ",".join(['NAME'] + variables)

            # geography: zip code tabulation area (ZCTA)
            url = f'https://api.census.gov/data/{year}/acs/acs5/profile?get={var_str}&for=zip%20code%20tabulation%20area:*&key={API_KEY}'

            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                df = pd.DataFrame(data[1:], columns=data[0])
                df.rename(columns=dict(zip(variables, labels)), inplace=True)
                df.to_csv(savepath, index=False)
            except Exception as e:
                print(f"[ERROR] Failed for {year}: {e}")

def merging_ACS_dataset(savedir):
    if not os.path.exists(os.path.join(savedir, "ACS5YR_combined.csv")):
        dfs = []
        for year in range(2013, 2024):
            df = pd.read_csv(os.path.join(savedir, f"ACS5YR_{year}zip.csv"))
            df['Year'] = year
            dfs.append(df)

        dfs = pd.concat(dfs, ignore_index=True)
        dfs.to_csv(os.path.join(savedir, "ACS5YR_combined.csv"))

def get_zcta520_zcta510_match(savedir):
    print("Downloading relationship file: zcta520-zcta510")
    url = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta510_zcta520_natl.txt"
    filename = "tab20_zcta510_zcta520_natl.csv"
    filepath = os.path.join(savedir, filename)

    if not os.path.exists(filepath):
        urllib.request.urlretrieve(url, filepath)
        print("Download complete")
    else:
        print("Using existing file")

def get_zip_zcta_crosswalk(savedir):
    if not os.path.exists(savedir):
        os.mkdir(savedir)

    base_url = "https://raw.githubusercontent.com/chris-prener/uds-mapper/main/data/uds_crosswalk_"

    for year in range(2013, 2023): 
        url = f"{base_url}{year}.csv"
        filename = f"zcta{str(year)[2:]}_crosswalk.csv"
        filepath = os.path.join(savedir, filename)

        if not os.path.exists(filepath):    
            print(f"Downloading zcta crosswalk for {year} from {url}")
            try:
                urllib.request.urlretrieve(url, filepath)
            except Exception as e:
                print(f"Failed to download for year {year}: {e}")
        else:
            print(f"Using existing file for {year}")

    print("Download complete!")

def mapping_zip_with_zcta(ACSdir, crosswalkdir):
    for year in range(2013, 2024):
        acs = pd.read_csv(os.path.join(ACSdir, f'ACS5YR_{str(year)}.csv'))
        if year == 2023:
            crosswalk = pd.read_csv(os.path.join(crosswalkdir, 'zcta22_crosswalk.csv'))
        else: 
            crosswalk = pd.read_csv(os.path.join(crosswalkdir, f'zcta{str(year)[2:]}_crosswalk.csv'))

        crosswalk.columns = crosswalk.columns.map(str.strip)
        if year == 2015:
            crosswalk = crosswalk.rename(columns={'zcta_use': 'zcta'})

        tmp = crosswalk.groupby('zip').size()
        mzcta1zip = tmp[tmp>1].index.tolist()
        if len(mzcta1zip) > 0:
            print(f"exists {len(mzcta1zip)} mapping from one zip to multiple zcta in year {year} (zip nunique: {len(tmp)})")

        if crosswalk['zcta'].dtype == 'object':
            crosswalk['zcta'] = pd.to_numeric(crosswalk['zcta'], errors='coerce').astype('Int64')

        acs_new = acs.merge(crosswalk[['zip', 'zcta']], how='left', left_on='zip code tabulation area', right_on='zcta')
        acs_new.to_csv(os.path.join(ACSdir, f'ACS5YR_{str(year)}zip.csv'), index=False)

    
if __name__ == "__main__":
    ACSpath = os.path.join(cPATH, 'temp', 'ACSdataset')
    crosswalkpath = os.path.join(cPATH, 'temp', 'crosswalk')
    get_ACS_dataset_with_url(ACSpath)
    get_zip_zcta_crosswalk(crosswalkpath)
    mapping_zip_with_zcta(ACSpath, crosswalkpath)
    merging_ACS_dataset(ACSpath)

