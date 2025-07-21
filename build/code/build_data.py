import glob
import itertools
import os
import re
import numpy as np
import pandas as pd
from datetime import date


cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "build")

def categorize_duration(days):
    if days < 1:
        return '< 1 day'
    elif days == 1:
        return '1 day'
    elif days == 2:
        return '2 days'
    elif days == 3:
        return '3 days'
    elif days == 4:
        return '4 days'
    elif days == 5:
        return '5 days'
    elif days == 6:
        return '6 days'
    elif days == 7:
        return '7 days'
    elif days <= 14:
        return 'within two weeks'
    elif days <= 30:
        return 'within a month'
    elif days <= 90:
        return 'within 90 days'
    elif days <= 180:
        return 'within 180 days'
    elif days <= 366:
        return 'within a year'
    else:
        return 'more than a year'

def group_duration(cat):
    mapping = {
        '< 1 day': '< 1 day',
        '1 day': 'within a week', '2 days': 'within a week',
        '3 days': 'within a week', '4 days': 'within a week',
        '5 days': 'within a week', '6 days': 'within a week',
        '7 days': 'within a week',
        'within two weeks': 'within a month',
        'within a month': 'within a month'
    }
    return mapping.get(cat, 'more than a month')

def state_privacy_law_implementation(state): # implementation date of CCPA is used for CA
    implementation_date = {'CA': '2020-01-01', 'VA': '2023-01-01', 'CO': '2023-07-01', 'CT': '2023-07-01', 'UT': '2023-12-31',
                           'TX': '2024-07-01', 'OR': '2024-07-01', 'FL': '2024-07-01', 'MT': '2024-10-01',
                           'DE': '2025-01-01', 'NH': '2025-01-01', 'IA': '2025-01-01', 'NE': '2025-01-01', 'NJ': '2025-01-15'
                           }
    return implementation_date.get(state, None)

def extract_date_parts(text):
    digits = ''.join(re.findall(r'\d+', text))
    if len(digits) == 8:     # MMDDYYYY
        month, day, year = digits[:2], digits[2:4], digits[4:]
    elif len(digits) == 7:   # MDDYYYY
        month, day, year = '0' + digits[:1], digits[1:3], digits[3:]
    elif len(digits) == 6:   # MMDDYY
        month, day, year = digits[:2], digits[2:4], '20' + digits[4:]
    elif len(digits) == 5:   # MDDYY
        month, day, year = '0' + digits[:1], digits[1:3], '20' + digits[3:]
    else:
        raise ValueError(f"Cannot parse date from digits: {digits} (text: {text})")
    return '-'.join([year, month, day]) # YYYY-MM-DD format

def read_cfpd_depository_institutions_list_excels(override=False):
    if not override and os.path.exists(os.path.join(cPATH, 'temp', 'cfpb_all_depository_institutions_combined.csv')):
        deduped_renamed = pd.read_csv(os.path.join(cPATH, 'temp', 'cfpb_all_depository_institutions_combined.csv'))
        return deduped_renamed 

    files = list(itertools.chain.from_iterable(glob.glob(os.path.join(cPATH, 'input', 'CFPD', 'depository_institutions', ext)) for ext in ('*.xlsx', '*.xls')))
    dfs = []
    valid_dates = {(3, 31), (6, 30), (9, 30), (12, 31)}
    for file in files:
        filename = os.path.basename(file)
        ext = filename.split('.')[-1]

        if filename == '201209_CFPB_depository-institutions-list.xls':
            header_depo, header_aff, date_idx, engine = 2, 1, 1, 'xlrd' # header rows, row index with date information, engine to use when reading excel file
        elif filename == '201409_cfpb_depository-institutions-list.xls':
            header_depo, header_aff, date_idx, engine = 1, 2, 0, 'xlrd'
        elif ext == '.xls':
            header_depo, header_aff, date_idx, engine = 1, 1, 0, 'xlrd'
        else:
            header_depo, header_aff, date_idx, engine = 1, 1, 0, None
        
        if filename == 'bcfp_depository-institutions_20180331.xlsx':
            prefix = 'Bureau'
        elif filename in ['bcfp_depository-insitutions-list_2018-09.xlsx', 'bcfp_depository-institutions_list_2018-06.xlsx']:
            prefix = 'BCFP'
        else:
            prefix = 'CFPB'

        df_raw = pd.read_excel(file, sheet_name=f'{prefix} Depository Institutions', header=None, engine=engine)
        df_depo = pd.read_excel(file, sheet_name=f'{prefix} Depository Institutions', header=header_depo, engine=engine)
        df_aff = pd.read_excel(file, sheet_name=f'{prefix} Depository Affilliates', header=header_aff, engine=engine)
        df_depo.columns = df_depo.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        df_aff.columns = df_aff.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        
        df_depo['Regulation'] = 'Depository'
        df_aff['Regulation'] = 'Affiliates'

        if 'ID' not in df_depo.columns:
            df_depo['ID'] = -1 # filler ID to indicate that RSSD ID information is not available
            df_aff['ID'] = -1 # filler ID to indicate that RSSD ID information is not available

        df_depo = df_depo[['ID', 'Institution', 'City', 'State', 'Regulation']]
        df_aff = df_aff[['ID', 'Institution', 'City', 'State', 'Regulation']]
        df = pd.concat([df_depo, df_aff], ignore_index=True)

        # getting date information
        date = extract_date_parts(df_raw.iloc[date_idx, 0])
        df['Reporting date'] = date
        df['Institution'] = df['Institution'].str.upper().str.strip() 
        dfs.append(df)


    combined = pd.concat(dfs, ignore_index=True)
    combined_renamed = combined.rename(columns={'Institution': 'Company', 'City': 'City company', 'State': 'State company'})
    print(f"before filtering out: {len(combined_renamed)}")

    # filter out empty rows & comment rows
    all_na = (combined_renamed['ID'].isna() & combined_renamed['Company'].isna() & combined_renamed['City company'].isna() & combined_renamed['State company'].isna())
    comment_row = (combined_renamed['ID'].isna() & combined_renamed['City company'].isna() & combined_renamed['State company'].isna() & combined_renamed['Company'].astype(str).str.strip().str.startswith('**'))
    rows_to_remove = all_na | comment_row
    combined_renamed = combined_renamed[~rows_to_remove]
    print(f"after filtering out: {len(combined_renamed)}")

    # remove duplicates
    final_cfpb = combined_renamed.drop_duplicates()
    print(f"after removing duplicates: {len(final_cfpb)}")

    # fill rssd id if there is a matching ('Company', 'City company', 'State company') pair
    def get_real_id(ser):
        rssd_values = ser.unique()
        if len(rssd_values) == 2:
            rssd_values = rssd_values.astype(int).tolist()
            rssd_values.remove(-1)     
        return rssd_values[0]
    #import pdb; pdb.set_trace()
    id_check = final_cfpb.groupby(['Company', 'City company', 'State company']).agg(**{'#ID_RSSD': ('ID', get_real_id)}).reset_index()    
    final_cfpb = final_cfpb.merge(id_check, on=['Company', 'City company', 'State company'], how='left')
    final_cfpb.drop('ID', axis=1, inplace=True)
    final_cfpb.to_csv(os.path.join(cPATH, 'temp', 'cfpb_all_depository_institutions_combined.csv'))
    return final_cfpb

def get_nic_data(override=False):
    nic_path, nic_raw_path = os.path.join(cPATH, 'temp', 'nic_combined.csv'), os.path.join(cPATH, 'temp', 'nic_combined_raw.csv')
    if not override and os.path.exists(nic_path) and os.path.exists(nic_raw_path):
        nic = pd.read_csv(os.path.join(cPATH, 'temp', 'nic_combined.csv'))
        nic_raw = pd.read_csv(os.path.join(cPATH, 'temp', 'nic_combined_raw.csv'))
        return nic, nic_raw


    nic_actv = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_ACTIVE.CSV'), low_memory=False) # NIC dataset to obtain institution types
    nic_clsd = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_CLOSED.CSV'), low_memory=False)
    nic_brnch = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_BRANCHES.CSV'), low_memory=False)
    nic_actv = nic_actv[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL', 'D_DT_START', 'D_DT_END', 'CITY', 'STATE_CD']]
    nic_clsd = nic_clsd[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL', 'D_DT_START', 'D_DT_END', 'CITY', 'STATE_CD']]
    # nic_brnch = nic_brnch[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL', 'D_DT_START', 'D_DT_END']]
    # nic = pd.concat([nic_actv, nic_clsd, nic_brnch])
    nic = pd.concat([nic_actv, nic_clsd])
    nic['NM_LGL'] = nic['NM_LGL'].str.upper().str.strip()

    # cross join to track rssd id changes over time
    quarters_df = pd.DataFrame({'quarter': pd.date_range(start='2010-01-01', end='2025-06-30', freq='QE')})
    quarters_df['key'] = 1
    nic['key'] = 1
    nic_cross = nic.merge(quarters_df, on='key', how='left')
    nic_cross.drop(columns='key', inplace=True)

    rssd_counts = nic[['NM_LGL', '#ID_RSSD']].drop_duplicates().groupby('NM_LGL').size().reset_index(name='rssd_count')
    nic_cross = nic_cross.merge(rssd_counts, on='NM_LGL', how='left')

    # if multiple RSSD ID exist for same name, get rssd id valid for each period
    # if only one RSSD ID exists for same name, get that rssd id for all periods
    nic_cross['D_DT_START'] = pd.to_datetime(nic_cross['D_DT_START']) 
    nic_cross['D_DT_END'] = pd.to_datetime(nic_cross['D_DT_END'], errors='coerce') # 12/13/9999, which indicates on-going relationships causes error -> fill with nan in that case
    nic_cross['D_DT_END'].fillna(pd.Timestamp('2262-04-11'), inplace=True)  # change nans into upper bound of datetime64[ns] (2262-04-11)
    
    nic_valid = nic_cross[
        ((nic_cross['rssd_count'] > 1) & (nic_cross['quarter'] >= nic_cross['D_DT_START']) & (nic_cross['quarter'] <= nic_cross['D_DT_END'])) |
        (nic_cross['rssd_count'] == 1)
    ].copy()

    # create company type variable based on CHTR_TYPE_CD and ENTITY_TYPE
    nic_valid['Company type'] = 'others'
    bank_ind = (nic_valid['CHTR_TYPE_CD'].isin([200, 300, 320, 340]) |nic_valid['ENTITY_TYPE'].isin(['SMB', 'DBR', 'NAT', 'NMB', 'ISB']))
    cu_ind =  (nic_valid['CHTR_TYPE_CD']==330) |nic_valid['ENTITY_TYPE'].isin(['FCU', 'SCU']) # credit union
    bhc_ind = (nic_valid['ENTITY_TYPE'].isin(['BHC', 'FBH', 'BHC', 'FHD', 'SLHC'])) # bank/saving/loan holding companies
    insur_ind = (nic_valid['CHTR_TYPE_CD']==550) # insurance broker or agent and/or insurance company
    sec_ind = (nic_valid['CHTR_TYPE_CD']==700) # Securities Broker and/or Dealer
    #nic.loc[sec_ind, 'Company type'] = 'security related'
    #nic.loc[insur_ind, 'Company type'] = 'insurance related'
    nic_valid.loc[bhc_ind, 'Company type'] = 'bank holding company'
    nic_valid.loc[cu_ind, 'Company type'] = 'credit union'
    nic_valid.loc[bank_ind, 'Company type'] = 'bank'

    # if the same name X qurter falls into two or more category, apply the follwing priority
    priority = {'bank': 1, 'credit union': 2, 'bank holding company':3, 'insurance related':4, 'security related': 5, 'others':6}
    nic_valid['type_priority'] = nic_valid['Company type'].map(priority)
    priority_combos = (nic_valid.groupby('NM_LGL')['type_priority'].apply(lambda x: tuple(sorted(x.unique()))).reset_index(name='priority_combo'))
    print(priority_combos['priority_combo'].value_counts().reset_index(name='count').rename(columns={'index': 'priority_combo'}))

    nic_dedup = nic_valid.sort_values('type_priority', ascending=True).drop_duplicates(subset=['NM_LGL', 'quarter'], keep='first')
    nic_dedup = nic_dedup.drop(['CHTR_TYPE_CD', 'ENTITY_TYPE', 'type_priority', 'D_DT_START', 'D_DT_END', 'CITY', 'STATE_CD'], axis=1)
    nic_dedup = nic_dedup.drop_duplicates()

    # name-quarter level to match with institution name impute missing quarters with the nearest quarter info
    complete = nic_cross[['NM_LGL', 'quarter']].copy().drop_duplicates()
    nic_complete = complete.merge(nic_dedup, on=['NM_LGL', 'quarter'], how='left')
    nic_complete.sort_values(['NM_LGL', 'quarter'], inplace=True)

    # rssd id-quarter level to match with rssd id 
    complete_id = nic_cross[['#ID_RSSD', 'quarter']].copy()
    nic_id_complete = complete_id.merge(nic_valid, on=['#ID_RSSD', 'quarter'], how='left')
    
    # impute missing quarters with the nearest quarter info
    nic_complete.update(nic_complete.groupby('NM_LGL').ffill())
    nic_complete.update(nic_complete.groupby('NM_LGL').bfill())
    nic_id_complete.update(nic_id_complete.groupby('#ID_RSSD').ffill())
    nic_id_complete.update(nic_id_complete.groupby('#ID_RSSD').bfill())

    nic_complete.to_csv(os.path.join(cPATH, 'temp', 'nic_combined.csv'), index=False)
    nic_id_complete.to_csv(os.path.join(cPATH, 'temp', 'nic_combined_raw.csv'), index=False)
    return nic_complete, nic_id_complete

def quarter_to_period_end(quarter_str):
    year = int(quarter_str[:4])
    q = int(quarter_str[-1])
    q_dict = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
    return f"{year}-{q_dict[q]}"

def get_ffiec_data(path, override=False):
    if not override and os.path.exists(os.path.join(cPATH, 'temp', 'ffiec_cdr_combined.csv')):
        ffiec_all = pd.read_csv(os.path.join(cPATH, 'temp', 'ffiec_cdr_combined.csv'))
        return ffiec_all 

    all_files = glob.glob(os.path.join(path, '*', '*.txt'))
    all_files = [f for f in all_files if os.path.basename(f) != 'Readme.txt'] # do not read Readme.txt 

    ffiec_all = []
    for file in all_files:
        try:
            ffiec = pd.read_csv(file, delimiter='\t', low_memory=False)
            ffiec = ffiec[['Reporting Period End Date', 'IDRSSD', 'Financial Institution Name', 'RCFD2170', 'RCON2170']]  # RCFD2170 = Total Assets (consolidated), RCON2170: total assets - if RCFD is missing, use RCON as total assets
            ffiec_all.append(ffiec.drop(0))
        except Exception as e:
            print(f"Error reading {file}: {e}") # the ffiec txt files are divided in columns - it is normal that some files do not contain RCFD2170 column and are excluded from ffiec_all

    ffiec_all = pd.concat(ffiec_all, ignore_index=True)

    # Total asset information is available in only one of the two columns, RCFD2170 or RCON2170 — use the non-missing value to construct the Total Assets variable.
    ffiec_all['Total assets'] = ffiec_all[['RCFD2170', 'RCON2170']].astype(float).sum(axis=1, skipna=True)
    ffiec_all.drop(['RCFD2170', 'RCON2170'], axis=1, inplace=True)

    # total assets in ffiec form 031, 041 (call reports) are reported in thousands - multiply by 1,000 to convert it into a dollar unit
    ffiec_all['Total assets'] = pd.to_numeric(ffiec_all['Total assets'], errors='coerce')
    ffiec_all['Total assets'] = ffiec_all['Total assets']*1000 
    ffiec_all.to_csv(os.path.join(cPATH, 'temp', 'ffiec_cdr_combined.csv'), index=False)
    return ffiec_all

def get_ncua_data(path, override=False):
    if not override and os.path.exists(os.path.join(cPATH, 'temp', 'ncua_combined.csv')):
        ncua_all = pd.read_csv(os.path.join(cPATH, 'temp', 'ncua_combined.csv'))
        return ncua_all 

    callrpt_dirs = glob.glob(os.path.join(path, '*'))
    ncua_all = []

    for callrpt_dir in callrpt_dirs:
        foicu_path = os.path.join(callrpt_dir, 'foicu.txt')
        fs220_path = os.path.join(callrpt_dir, 'fs220.txt')
        
        if os.path.exists(foicu_path) and os.path.exists(fs220_path):
            foicu = pd.read_csv(foicu_path, delimiter=',', low_memory=False)
            fs220 = pd.read_csv(fs220_path, delimiter=',', low_memory=False)

            fs220 = fs220[['CU_NUMBER', 'CYCLE_DATE', 'ACCT_010']] # ACCT_010: total assets
            if 'RSSD' in foicu.columns:
                merged = fs220.merge(foicu[['CU_NUMBER', 'RSSD', 'CU_NAME']], on='CU_NUMBER', how='left')
            else:
                merged = fs220.merge(foicu[['CU_NUMBER', 'CU_NAME']], on='CU_NUMBER', how='left')
                merged['RSSD'] = np.nan
            ncua_all.append(merged)
        else:
            print(f"either FOICU.txt or FS200.txt does not exist for {os.path.basename(callrpt_dir)}")

    ncua_all = pd.concat(ncua_all, ignore_index=True)
    ncua_all.rename(columns={'ACCT_010': 'Total assets'}, inplace=True)
    ncua_all['CYCLE_DATE'] = pd.to_datetime(ncua_all['CYCLE_DATE'])

    # fill missing RSSD ID by matching with (CU_NAME, CU_NUMBER) pair
    ncua_id = ncua_all[ncua_all['RSSD'].notna()].copy()
    for idx, row in ncua_all[ncua_all['RSSD'].isna()].iterrows():
        candidates = ncua_id[(ncua_id['CU_NAME'] == row['CU_NAME']) & (ncua_id['CU_NUMBER'] == row['CU_NUMBER'])]
        if not candidates.empty:
            candidates = candidates.copy()
            candidates['date_diff'] = (candidates['CYCLE_DATE'] - row['CYCLE_DATE']).abs()
            best_match = candidates.loc[candidates['date_diff'].idxmin()]
            ncua_all.at[idx, 'RSSD'] = best_match['RSSD']

    ncua_all['CYCLE_DATE'] = ncua_all['CYCLE_DATE'].astype(str)
    ncua_all.to_csv(os.path.join(cPATH, 'temp', 'ncua_combined.csv'), index=False)
    return ncua_all

def get_bhc_financial_data(path, override=False):
    if not override and os.path.exists(os.path.join(cPATH, 'temp', 'ffiec_bhcf_combined.csv')):
        bhcf_all = pd.read_csv(os.path.join(cPATH, 'temp', 'ffiec_bhcf_combined.csv'))
        return bhcf_all 

    all_files = glob.glob(os.path.join(path, '*.txt'))
    bhcf_all = []

    for file in all_files:
        try:
            bhcf = pd.read_csv(file, delimiter='^', low_memory=False, on_bad_lines='warn')
            bhcf = bhcf[['RSSD9001', 'RSSD9999', 'BHCK2170', 'BHCP2170', 'BHSP2170']]
            bhcf_all.append(bhcf)
        except:
            try:
                bhcf = pd.read_csv(file, delimiter='^', low_memory=False, encoding='cp1252', on_bad_lines='warn')
                bhcf = bhcf[['RSSD9001', 'RSSD9999', 'BHCK2170', 'BHCP2170', 'BHSP2170']]
                bhcf_all.append(bhcf)
            except Exception as e:
                print(f"Error reading {file}: {e}") # the ffiec txt files are divided in columns - it is normal that some files do not contain RCFD2170 column and are excluded from ffiec_all

    bhcf_all = pd.concat(bhcf_all, ignore_index=True)
    bhcf_all['Consolidated'] = bhcf_all['BHCK2170'].notna() # indicates whether consolidated total assets is reported
    bhcf_all.rename(columns={'RSSD9001': 'RSSD ID', 'RSSD9999': 'bhcf report date', 'BHCK2170': 'Total assets'}, inplace=True)
    bhcf_all['Parent only assets'] = bhcf_all[['BHCP2170', 'BHSP2170']].sum(axis=1, skipna=True)

    bhcf_all.loc[~bhcf_all['Consolidated'], 'Total assets'] = bhcf_all.loc[~bhcf_all['Consolidated'], 'Parent only assets'] # if consolicated total assets info do not exists, get parent only total assets
    bhcf_all['Total assets'] = bhcf_all['Total assets']*1000 # total assets of bhc are reported in 1,000 dollars
    bhcf_all['bhcf report date'] = pd.to_datetime(bhcf_all['bhcf report date'].astype(str),format='%Y%m%d').dt.strftime('%Y-%m-%d')
    bhcf_all.drop(['BHCP2170', 'BHSP2170'], axis=1, inplace=True)
    bhcf_all.to_csv(os.path.join(cPATH, 'temp', 'ffiec_bhcf_combined.csv'), index=False)
    return bhcf_all

def bank_total_assets_in_bhc(nic, ffiec_crp): # get sum of total assets for child banks in bhc (total assets of bhc held by banks)
    relationships = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_RELATIONSHIPS.CSV'))
    relationships = relationships[relationships['RELN_LVL'].isin([1, 2])] # include direct and indirect relationships
    relationships['D_DT_START'] = pd.to_datetime(relationships['D_DT_START']) # change dtypes for comparison later on
    relationships['D_DT_END'] = pd.to_datetime(relationships['D_DT_END'], errors='coerce') # 12/13/9999, which indicates on-going relationships causes error -> fill with nan in that case
    relationships['D_DT_END'].fillna(pd.Timestamp('2262-04-11'), inplace=True)  # change nans into upper bound of datetime64[ns] (2262-04-11)

    # cross-join relationships to get quarterly level relationships
    quarters = pd.date_range(start='2010-01-01', end='2025-06-30', freq='QE') # create all quarters of our interest
    relationships['key'] = 1
    quarters_df = pd.DataFrame({'quarter': quarters})
    quarters_df['key'] = 1
    rel_cross = relationships[['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'key', 'D_DT_START', 'D_DT_END']].merge(quarters_df, on='key', how='left')
    rel_cross.drop(columns='key', inplace=True)

    rel_valid = rel_cross[(rel_cross['quarter'] >= rel_cross['D_DT_START']) &(rel_cross['quarter'] <= rel_cross['D_DT_END'])].copy() # filter out invalid dates
    rel_vallid = rel_valid.drop_duplicates(['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'quarter'])
    rel_valid.drop(['D_DT_START', 'D_DT_END'], axis=1, inplace=True)

    # Merge with NIC dataset and FFIEC call reports to get Company type and Total assets
    nic.drop(['D_DT_START', 'D_DT_END'], axis=1, inplace=True)
    rel_valid['quarter'] = rel_valid['quarter'].astype(str)
    rel_valid = rel_valid.merge(nic[['#ID_RSSD', 'Company type', 'quarter']], left_on=['ID_RSSD_OFFSPRING', 'quarter'], right_on=['#ID_RSSD', 'quarter'], how='left') # get company type of offspring
    merged = rel_valid.merge(ffiec_crp, left_on=['ID_RSSD_OFFSPRING', 'quarter'], right_on=['IDRSSD', 'Reporting Period End Date'], how='left')
    print("parent-subsidiary relationships, quarterly level", merged.shape)

    # filter out non-banks & remove duplicates
    merged = merged[merged['Company type']=='bank']
    print("After filtering out non-banks", merged.shape)
    merged = merged.drop_duplicates(subset=['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'quarter'])
    print("After removing dupplicates:", merged.shape)

    # Aggregate total assets of banks under each BHC per quarter
    # BankNotnaCount: Number of subsidiaries with non-missing total assets
    # BankTotal: Sum of total assets across subsidiaries (returns NaN if all values are NaN)
    # BankCount: Total number of subsidiaries (including those with NaN total assets)
    grouped = merged.groupby(['#ID_RSSD_PARENT', 'Reporting Period End Date'])
    bhc_assets = grouped['Total assets'].agg(BankNotnaCount='count', BankAssets=lambda x: x.sum(min_count=1), BankCount='size').reset_index()
    bhc_assets['Reporting Period End Date'] = bhc_assets['Reporting Period End Date'].astype(str)
    return bhc_assets, merged

def get_lag_quarter(date): # input: date in str 'yyyy-mm-dd' format
    md_dict = {'03-31': '12-31', '06-30': '03-31', '09-30': '06-30', '12-31': '09-30'}
    year = date[:4]
    md = date[5:]
    lag_year = str(int(year)-1) if md == '03-31' else year  
    return f"{lag_year}-{md_dict[md]}"

def aggregate_regulation(x):
    uniq = x.unique()
    if len(uniq) == 1:
        return uniq[0]
    return '-'.join(sorted(uniq))

if __name__ == "__main__":
    # basic statistics of the whole dataset
    df = pd.read_csv(os.path.join(cPATH, "input", "CFPD", "complaints.csv"))
    print(f"shape of full data: {df.shape}")
    print(f"number of unique ids: {df['Complaint ID'].nunique()}")
    print(df.columns)

    # transform date variables 
    df['Date received'] = pd.to_datetime(df['Date received'])
    df['Date sent to company'] = pd.to_datetime(df['Date sent to company'])
    df['Consumer complaint narrative'] = df["Consumer complaint narrative"].astype('string')
    df['Month received'] = df['Date received'].dt.to_period('M').dt.to_timestamp()
    df['Quarter received'] = df['Date received'].dt.to_period('Q')
    df['Year received'] = df['Date received'].dt.year
    df['Quarter sent'] = df['Date sent to company'].dt.to_period('Q')
    df['Year sent'] = df['Date sent to company'].dt.year

    # remove complaints sent to companies in 2025 Q2 (as the data was downloaded in the middle of 2025 Q2)
    df = df[df['Quarter sent'] <= pd.Period('2025Q1')]
    print(f"number of observations after removing complaints sent to companies in 2025 Q2 : {len(df)}")

    # binary indicator of receiving monetary or non-monetary relief
    df['Is relief'] = df['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

    # quantifies the time duration between receiving complaints and sending them to companies
    df['Duration sending'] = (df['Date sent to company'] - df['Date received']).dt.days # duration between receiving the complaints to sending the complaints to the company (in days)
    df['Duration categorized'] = df['Duration sending'].apply(categorize_duration) 
    df['Duration grouped'] = df['Duration categorized'].apply(group_duration)

    # CCPA and CPRA
    CCPA_timeline = {'CCPA enactment': '2018-06-28', 'CCPA implementation': '2020-01-01', 'CPRA amendment': '2020-11-03', 'CPRA implementation': '2023-01-01'}
    ccpa_enact = pd.to_datetime(CCPA_timeline['CCPA enactment'])
    ccpa_impl = pd.to_datetime(CCPA_timeline['CCPA implementation'])
    cpra_amend = pd.to_datetime(CCPA_timeline['CPRA amendment'])
    cpra_impl = pd.to_datetime(CCPA_timeline['CPRA implementation'])
    df['CCPA phase at receipt'] = pd.cut(df['Date received'], 
                                         bins=[pd.Timestamp.min, ccpa_enact, ccpa_impl, cpra_amend, cpra_impl, pd.Timestamp.max], 
                                         right=False, 
                                         labels=['Pre-CCPA', 'CCPA enacted, pre-implement', 'CCPA implemented, pre-CPRA', 'CPRA amended, pre-implementation', 'CPRA implemented'])
    df['CCPA phase at sent'] = pd.cut(df['Date received'], 
                                         bins=[pd.Timestamp.min, ccpa_enact, ccpa_impl, cpra_amend, cpra_impl, pd.Timestamp.max], 
                                         right=False, 
                                         labels=['Pre-CCPA', 'CCPA enacted, pre-implement', 'CCPA implemented, pre-CPRA', 'CPRA amended, pre-implementation', 'CPRA implemented'])
    
    # implementation of all state privacy law 
    df['State privacy law'] = df['State'].apply(state_privacy_law_implementation)

    # identification of zombie data
    df['Zombie data'] = 0
    cond1 = (df['Issue'] == 'Incorrect information on your report') & (df['Sub-issue'] == 'Old information reappears or never goes away')
    cond2 = (df['Issue'] == 'Incorrect information on credit report') & (df['Sub-issue'] == 'Reinserted previously deleted info')
    df.loc[cond1 | cond2, 'Zombie data'] = 1
    print(f"{df['Zombie data'].sum()}/{len(df)} complaints are about zombie data")
    print(f"number of companies that zombie data-related compaints were filed to: {df[df['Zombie data']==1]['Company'].nunique()}")
    print(f"top 20 companies that zombie data complaints were filed to: \n {df[df['Zombie data'] == 1]['Company'].value_counts().head(20)}")

    # indicator of complaints with/without narratives 
    df["With narrative"] = df["Consumer complaint narrative"].notna()

    ### Getting RSSD ID & institution type
    nic, nic_raw = get_nic_data()
    if nic['quarter'].dtype == 'O' or nic['quarter'].dtype.name == 'string':
        nic['quarter'] = pd.to_datetime(nic['quarter']).dt.to_period('Q')
    else:
        nic['quarter'] = snic['quarter'].dt.to_period('Q')

    df = df.merge(nic, how='left', left_on=['Company', 'Quarter sent'], right_on=['NM_LGL', 'quarter'])
    print(f"df after merging with nic: {len(df)}")

    # major credit bureaus
    df['Company'] = df['Company'].str.upper().str.strip() 
    credit_bureaus = ['EXPERIAN INFORMATION SOLUTIONS INC.', 'TRANSUNION INTERMEDIATE HOLDINGS, INC.', 'EQUIFAX, INC.']
    cb_ind = df['Company'].isin(credit_bureaus)
    df.loc[cb_ind, 'Company type'] = 'major credit bureaus'

    # SCRA (specialized credit reporting agencies)
    scra_df = pd.read_csv(os.path.join(cPATH, 'input', 'CFPD', 'cfpb-consumer-reporting-companies_list_2025.csv'), encoding='cp1252')
    scra = scra_df['Company'].str.upper().tolist()
    scra_ind = df['Company'].isin(scra)
    df.loc[scra_ind, 'Company type'] = 'scra'
    
    # data broker
    db = pd.read_excel(os.path.join(cPATH, 'input', 'Data_Broker_Full_Registry_2025.xlsx'))
    db['Name'] = db['Name'].str.upper().str.strip() 
    db_names = db['Name'].unique().tolist()
    db_ind = df['Company'].isin(db_names)
    df.loc[db_ind, 'Company type'] = 'data broker'

    df['Company type'] = df['Company type'].fillna('others')
    print(df['Company type'].unique())
    print(df.groupby('Company type').count())
    print(f"df size after financial institution classification: {len(df)}")
    
    ### financial institutions size (total assets in dollars)
    ## get asset information for banks from ffiec call reports (031/041/051)
    ffiec_path = os.path.join(cPATH, 'input', 'FFIEC', 'CDR Call Reports')
    ffiec = get_ffiec_data(ffiec_path)
    df['Quarter sent end date'] = df['Quarter sent'].astype(str).apply(quarter_to_period_end) # calcuate end date of quarter when the complain was sent to the company for match purpose

    df = df.merge(ffiec, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['IDRSSD', 'Reporting Period End Date']) # match with RSSD ID
    df.rename(columns={'Total assets': 'Total assets bank'}, inplace=True)

    ffiec_dup = ffiec.drop_duplicates(['Financial Institution Name', 'Reporting Period End Date'], keep=False)
    df.drop(['IDRSSD', 'Reporting Period End Date', 'Financial Institution Name'], axis=1, inplace=True)
    df = df.merge(ffiec_dup, how='left', left_on=['Company', 'Quarter sent end date'], right_on=['Financial Institution Name', 'Reporting Period End Date']) # match with name
    
    # combine information gathered from matching with rssd id and name
    df['Total assets bank'] = df['Total assets bank'].combine_first(df['Total assets']) 
    df['#ID_RSSD'] = df['#ID_RSSD'].combine_first(df['IDRSSD'])
    df.loc[df['Total assets bank'].notna(), 'Company type'] = 'bank' # all the institution that file ffiec call reports 031/041/051 are banks
    print(f"total assets identified for {df['Total assets bank'].notna().sum()} out of {len(df[df['Company type']=='bank'])} complaints filed to banks")
    df.drop(['IDRSSD', 'Reporting Period End Date', 'Financial Institution Name', 'Total assets'], axis=1, inplace=True)

    ## get asset information for credit unions
    ncua_path = os.path.join(cPATH, 'input', 'NCUA')
    ncua = get_ncua_data(ncua_path)
    ncua_id = ncua[ncua['RSSD'].notna()]

    df = df.merge(ncua_id, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'],right_on=['RSSD', 'CYCLE_DATE']) # first match with IDRSSD
    df.rename(columns={'Total assets': 'Total assets cu'}, inplace=True)
    df.drop(['RSSD', 'CYCLE_DATE', 'CU_NAME', 'CU_NUMBER'], axis=1, inplace=True)

    ncua_dup = ncua.drop_duplicates(['CU_NAME', 'CYCLE_DATE'], keep=False)
    df = df.merge(ncua_dup, how='left', left_on=['Company', 'Quarter sent end date'], right_on=['CU_NAME', 'CYCLE_DATE']) # match with name

    # combine the matched information 
    df['Total assets cu'] = df['Total assets cu'].combine_first(df['Total assets'])
    df['#ID_RSSD'] = df['#ID_RSSD'].combine_first(df['RSSD'])
    df.loc[df['Total assets cu'].notna(), 'Company type'] = 'credit union' # all the institution that file NCUA call reports are credit union
    print(f"total assets identified for {df['Total assets cu'].notna().sum()} out of {len(df[df['Company type']=='credit union'])} complaints filed to credit union")
    df.drop(['RSSD', 'CYCLE_DATE', 'CU_NAME', 'CU_NUMBER', 'Total assets'], axis=1, inplace=True)

    ## get asset information for bank holding companies
    bhcf_path = os.path.join(cPATH, 'input', 'FFIEC', 'Holding Company Financial Data')
    bhcf = get_bhc_financial_data(bhcf_path) # get total assets of bhc
    bhc_bank, bhc_offsprings = bank_total_assets_in_bhc(nic_raw, ffiec) # get sum of total assets held by banks under bhc

    df = df.merge(bhcf, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['RSSD ID', 'bhcf report date']) # match with rssd id 
    df = df.merge(bhc_bank, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['#ID_RSSD_PARENT', 'Reporting Period End Date'])
    df.rename(columns={'Total assets': 'Total assets bhc'}, inplace=True)
    df.loc[df['Total assets bhc'].notna(), 'Company type'] = 'bank holding company' # all the institution that file NCUA call reports are credit union
    print(len(df), "after matching with rssd id")

    print(f"bhc total assets identified for {df['Total assets bhc'].notna().sum()} out of {len(df[df['Company type']=='bank holding company'])} complaints filed to bank holding companies")
    print(f"bhc total assets ranges between: {df['Total assets bhc'].min()} to {df['Total assets bhc'].max()}")
    print(f"bhc total assets held by banks identified for {df['BankAssets'].notna().sum()} out of {len(df[df['Company type']=='bank holding company'])} complaints filed to bank holding companies")
    print(f"bhc total assets held by banks ranges between: {df['BankAssets'].min()} to {df['BankAssets'].max()}")

    df[df['Company type']=='Bank holding company'].to_csv(os.path.join(cPATH,  'temp', 'bhc_assets.csv')) # save to compare bhc total assets vs. bhc total assets held by banks

    # adjust total assets based on exploratory analysis of BankAssets and TotalAssets
    # we use BankAssets as our default measure of total assets for bhcs since it better reflects each institution's capability regarding its banking system
    # when AssetsRatio < 0.3, bank subsidiaries are not properly matched, resulting in big discrepancy between Total assets & BankAssets -> better use Total assets
    df['AssetsRatio'] = df['BankAssets'] / df['Total assets bhc']    
    df.rename(columns={'Total assets bhc' : 'BhcAssets', 'BankAssets': 'Total assets bhc'}, inplace=True)
    use_bhc_assets = df[(df['AssetsRatio']<0.3)&(df['Total assets bhc'].notna())&(df['BhcAssets'].notna())] 
    df.loc[use_bhc_assets.index, 'Total assets bhc'] = df.loc[use_bhc_assets.index, 'BhcAssets']
    df['BankCount'] = df['BankCount'].fillna(-1)

    df.drop(['quarter', 'RSSD ID', 'bhcf report date', 'Consolidated', '#ID_RSSD_PARENT', 'Reporting Period End Date', 'BankNotnaCount', 'BhcAssets'], axis=1, inplace=True)
    print(f"final bhc total assets identified for {df['Total assets bhc'].notna().sum()} out of {len(df[df['Company type']=='Bank holding company'])} complaints filed to bank holding companies")
    print(f"final bhc total assets ranges between: {df['Total assets bhc'].min()} to {df['Total assets bhc'].max()}")

    # combine all total assets info
    df['Total assets'] = df['Total assets bank'].fillna(df['Total assets cu']).fillna(df['Total assets bhc'])
    df.drop(columns=['Total assets bank', 'Total assets cu', 'Total assets bhc'], axis=1, inplace=True)
    print("financial institution classification updated: ", df.groupby('Company type').count())

    ## Use the Consumer Price Index (CPI) to adjust total assets to real values in 2013 dollars.
    cpi_df = pd.read_csv(os.path.join(cPATH, 'input', 'CPIAUCSL.csv'))
    cpi_df['observation_month'] = cpi_df['observation_date'].str[:-3] # convert to month to make matching easier
    cpi_dict = cpi_df.set_index('observation_month')['CPIAUCSL'].to_dict() # convert to dictionary to make matching easier

    cpi_2013 = cpi_df[cpi_df['observation_date'].str.startswith('2013')] # average CPI in 2013
    mean_cpi_2013 = cpi_2013['CPIAUCSL'].mean()

    df['Total assets'] = pd.to_numeric(df['Total assets'], errors='coerce')
    df['Real total assets'] = df['Total assets']*mean_cpi_2013/df['Quarter sent end date'].apply(lambda x: cpi_dict[x[:-3]])
    df['Log total assets'] = np.log(df['Total assets'])
    df['Log real total assets'] = np.log(df['Real total assets'])

    ## Lagged total assets variable
    df['LagQuarter'] = df['Quarter sent end date'].apply(get_lag_quarter)
    lag_df = df[['#ID_RSSD', 'Quarter sent end date', 'Total assets']].drop_duplicates()
    lag_df = lag_df.rename(columns={'Quarter sent end date': 'LagQuarter', 'Total assets': 'Lagged total assets'})
    df = df.merge(lag_df, how='left', on=['#ID_RSSD', 'LagQuarter'])

    ### CFPB regulation
    cfpb = read_cfpd_depository_institutions_list_excels(override=True)
    cfpb_noid = cfpb[cfpb['#ID_RSSD']==-1].copy().drop('#ID_RSSD', axis=1)
    cfpb_id = cfpb[cfpb['#ID_RSSD']!=-1].copy()

    # get regulation information in bhc level
    bhc_offsprings['quarter'] = bhc_offsprings['quarter'].astype(str)
    bhc_offsprings = bhc_offsprings[['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'quarter']].merge(cfpb_id, how='left', left_on=['ID_RSSD_OFFSPRING', 'quarter'], right_on=['#ID_RSSD', 'Reporting date'])
    bhc_with_reg = bhc_offsprings[bhc_offsprings['Regulation'].notna()]
    bhc_no_reg = bhc_offsprings[bhc_offsprings['Regulation'].isna()][['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'quarter']]

    nic_raw['quarter'] = nic_raw['quarter'].astype(str)
    bhc_no_reg = bhc_no_reg.merge(nic_raw[['#ID_RSSD', 'quarter', 'NM_LGL']], how='left', left_on=['ID_RSSD_OFFSPRING', 'quarter'], right_on=['#ID_RSSD', 'quarter'])
    bhc_no_reg = bhc_no_reg.merge(cfpb_noid, how='left', left_on=['NM_LGL', 'quarter'], right_on=['Company', 'Reporting date'])
    bhc_reg = pd.concat([bhc_with_reg, bhc_no_reg], ignore_index=True)[['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'quarter', 'Regulation']]
    bhc_reg['Regulation'] = bhc_reg['Regulation'].fillna('NoRegulation')

    bhc_reg_agg = bhc_reg.groupby(['#ID_RSSD_PARENT', 'quarter']).agg({'Regulation': aggregate_regulation}).reset_index()
    df = df.merge(bhc_reg_agg, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['#ID_RSSD_PARENT', 'quarter'])
    df = df.rename(columns={'Regulation': 'Regulation_bhc'})
    print(f"regulation under CFPD identified for {len(df[df['Regulation_bhc'].notna()])} complaints filed to bank holding company")
    df = df.merge(cfpb_id[['#ID_RSSD', 'Reporting date', 'Regulation']], how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['#ID_RSSD', 'Reporting date'])
    df_with_reg = df[df['Regulation'].notna()].copy()
    df_no_reg = df[df['Regulation'].isna()].drop(['Regulation', 'Reporting date'], axis=1)
    print(f"regulation under CFPD identified for {len(df_with_reg)} complaints (matching with ID RSSD)")
    df_no_reg = df_no_reg.merge(cfpb_noid[['Company', 'Reporting date', 'Regulation']], how='left', left_on=['Company', 'Quarter sent end date'], right_on=['Company', 'Reporting date'])
    print(f"regulation under CFPD identified for {len(df_no_reg[df_no_reg['Regulation'].notna()])} complaints (additional matching with name)")
    df = pd.concat([df_with_reg, df_no_reg], ignore_index=True)

    df['Regulation'] = df['Regulation'].combine_first(df['Regulation_bhc'])
    df['Regulation'] = df['Regulation'].fillna('NoRegulation')
    print("complaint level statistics for regulation:")
    print(df.groupby('Regulation')['Regulation'].count())
    print("company-quarter level statistics for regulation:")
    print(df.drop_duplicates(subset=['Company', 'Quarter sent', 'Regulation']).groupby('Regulation').size().reset_index(name='n_company_quarters'))

    ### save data with narratives to observe complaint narratives
    narr = df[df['With narrative']==1] # complaints with narrative
    znarr = df[(df['With narrative']==1) & (df['Zombie data'] == 1)] # complaints on zombie data with narrative
    narr.to_csv(os.path.join(cPATH, 'temp', 'complaints_narratives.csv'))
    znarr.to_csv(os.path.join(cPATH, 'temp', 'zombie_complaints_narratives.csv'))

    ### delete irrelevant columns & save processed df
    df.drop(['NM_LGL', 'quarter', 'Quarter sent end date', 'Reporting date', 'LagQuarter', 'Regulation_bhc', '#ID_RSSD_PARENT'], axis=1, inplace=True)
    df.to_csv(os.path.join(cPATH, 'output', 'complaints_processed.csv'))