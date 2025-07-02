import glob
import itertools
import os
import numpy as np
import pandas as pd
from collections import defaultdict, deque


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

def read_cfpd_depository_institutions_list_excels(override=False):
    if not override and os.path.exists(os.path.join(cPATH, 'temp', 'cfpb_all_depository_institutions_combined.csv')):
        deduped_renamed = pd.read_csv(os.path.join(cPATH, 'temp', 'cfpb_all_depository_institutions_combined.csv'))
        return deduped_renamed 

    files = list(itertools.chain.from_iterable(glob.glob(os.path.join(cPATH, 'input', 'CFPD', 'depository_institutions', ext)) for ext in ('*.xlsx', '*.xls')))
    dfs = []
    no_id = []
    for file in files:
        filename = os.path.basename(file)
        ext = filename.split('.')[-1]
        if filename == '201209_CFPB_depository-institutions-list.xls':
            # df = pd.read_excel(file, header=2, engine='xlrd')
            df_all = pd.read_excel(file, sheet_name=None, header=2, engine='xlrd')
            df = pd.concat(df_all.values(), ignore_index=True)
            df.columns = df.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        elif ext == '.xls':
            # df = pd.read_excel(file, header=1, engine='xlrd')
            df_all = pd.read_excel(file, sheet_name=None, header=1, engine='xlrd')
            df = pd.concat(df_all.values(), ignore_index=True)
            df.columns = df.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        else:
            # df = pd.read_excel(file, header=1)
            df_all = pd.read_excel(file, sheet_name=None, header=1)
            df = pd.concat(df_all.values(), ignore_index=True)

        if 'ID' not in df.columns:
            df = df[['Institution', 'City', 'State']]
            df['source_file'] = os.path.basename(file) 
            no_id.append(df)
        else:
            df = df[['ID', 'Institution', 'City', 'State']]
            df['source_file'] = os.path.basename(file) 
            dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    deduped = combined.drop_duplicates(subset=['ID', 'Institution'])
    deduped_renamed = deduped.rename(columns={'ID': '#ID_RSSD', 'Institution': 'Company', 'City': 'City company', 'State': 'State company'})
    deduped_renamed.to_csv(os.path.join(cPATH, 'temp', 'cfpb_all_depository_institutions_combined.csv'), index=False)

    #check the institutions that does not include RSSD ID 
    no_id = pd.concat(no_id, ignore_index=True)
    no_id['Institution'] = no_id['Institution'].str.upper()
    deduped_sub = deduped[['Institution', 'City', 'State']].drop_duplicates()
    not_in_deduped_df = no_id.merge(deduped_sub, on=['Institution', 'City', 'State'], how='left', indicator=True)
    not_in_deduped_df = not_in_deduped_df[not_in_deduped_df['_merge'] == 'left_only']

    print(f"no_id institutions: {len(no_id)}")
    print(f"no_id institution not included in deduped: {len(not_in_deduped_df)}")
    print(not_in_deduped_df.head())
    return deduped_renamed

def get_nic_data(override=False):
    if override or not os.path.exists(os.path.join(cPATH, 'temp', 'nic_combined.csv')):
        nic_actv = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_ACTIVE.CSV'), low_memory=False) # NIC dataset to obtain institution types
        nic_clsd = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_CLOSED.CSV'), low_memory=False)
        nic_brnch = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_BRANCHES.CSV'), low_memory=False)
        nic_actv = nic_actv[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL', 'D_DT_START', 'D_DT_END']]
        nic_clsd = nic_clsd[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL', 'D_DT_START', 'D_DT_END']]
        nic_brnch = nic_brnch[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL', 'D_DT_START', 'D_DT_END']]
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
        nic_valid.to_csv(os.path.join(cPATH, 'temp', 'nic_raw.csv'), index=False)
    else:
        nic_valid = pd.read_csv(os.path.join(cPATH, 'temp', 'nic_combined.csv'))

    nic_dedup = nic_valid.sort_values('type_priority', ascending=True).drop_duplicates(subset=['NM_LGL', 'quarter'], keep='first')
    nic_dedup = nic_dedup.drop(['CHTR_TYPE_CD', 'ENTITY_TYPE', 'type_priority', 'D_DT_START', 'D_DT_END'], axis=1)
    nic_dedup = nic_dedup.drop_duplicates()

    # impute missing quarters with the nearest quarter info
    complete = nic_cross[['NM_LGL', 'quarter']].copy()
    nic_complete = complete.merge(nic_dedup, on=['NM_LGL', 'quarter'], how='left')
    nic_complete.sort_values(['NM_LGL', 'quarter'], inplace=True)
    nic_complete.update(nic_complete.groupby('NM_LGL').ffill())
    nic_complete.update(nic_complete.groupby('NM_LGL').bfill())

    return nic_complete, nic_valid

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
    ncua_all['CYCLE_DATE'] = pd.to_datetime(ncua_all['CYCLE_DATE']).astype(str)
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

    rel_valid = rel_cross[(rel_cross['quarter'] >= rel_cross['D_DT_START']) &(rel_cross['quarter'] <= rel_cross['D_DT_END'])] # filter out invalid dates
    rel_valid.drop(['D_DT_START', 'D_DT_END'], axis=1, inplace=True)

    # Merge with NIC dataset and FFIEC call reports to get Company type and Total assets
    nic.drop(['D_DT_START', 'D_DT_END'], axis=1, inplace=True)
    ffiec_crp['Reporting Period End Date'] = pd.to_datetime(ffiec_crp['Reporting Period End Date'])
    rel_valid = rel_valid.merge(nic[['#ID_RSSD', 'Company type', 'quarter']], left_on=['ID_RSSD_OFFSPRING', 'quarter'], right_on=['#ID_RSSD', 'quarter'], how='left') # get company type of offspring
    merged = rel_valid.merge(ffiec_crp, left_on=['ID_RSSD_OFFSPRING', 'quarter'], right_on=['IDRSSD', 'Reporting Period End Date'], how='left')
    print("parent-subsidiary relationships, quarterly level", merged.shape)

    # filter out non-banks & remove duplicates 
    is_bank = (merged['Company type']=='bank')
    merged = merged[is_bank]
    print("After filtering out non-banks", merged.shape)
    merged = merged.drop_duplicates(subset=['#ID_RSSD_PARENT', 'ID_RSSD_OFFSPRING', 'Reporting Period End Date'])
    print("After removing dupplicates:", merged.shape)

    # Aggregate total assets of banks under each BHC per quarter
    # BankCount: Number of subsidiaries with non-missing total assets
    # BankTotal: Sum of total assets across subsidiaries (returns NaN if all values are NaN)
    # BankCountNanIncluded: Total number of subsidiaries (including those with NaN total assets)
    grouped = merged.groupby(['#ID_RSSD_PARENT', 'Reporting Period End Date'])
    bhc_assets = grouped['Total assets'].agg(BankCount='count', BankAssets=lambda x: x.sum(min_count=1)).reset_index()
    return bhc_assets

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
    nic['quarter'] = nic['quarter'].dt.to_period('Q')
    df = df.merge(nic, how='left', left_on=['Company', 'Quarter sent'], right_on=['NM_LGL', 'quarter'])

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

    for company_type in df['Company type'].unique():
        print(f"RSSD ID identified for {len(df[(df['Company type']==company_type)&df['#ID_RSSD'].notna()])} out of {len(df[df['Company type']==company_type])} complaints filed to {company_type}")
    
    ### financial institutions size (total assets in dollars)
    ## get asset information for banks
    ffiec_path = os.path.join(cPATH, 'input', 'FFIEC', 'CDR Call Reports')
    ffiec = get_ffiec_data(ffiec_path)
    df['Quarter sent end date'] = df['Quarter sent'].astype(str).apply(quarter_to_period_end) # calcuate end date of quarter when the complain was sent to the company for match purpose

    # all institutes in ffiec dataset are classified as banks
    bank = df[df['Company type']=='bank']
    bank = bank.merge(ffiec, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'],right_on=['IDRSSD', 'Reporting Period End Date']) # all banks have #ID_RSSD, so match with RSSD ID
    bank.drop(['NM_LGL', 'quarter', 'Reporting Period End Date', 'IDRSSD', 'Financial Institution Name'], axis=1, inplace=True)
    print(f"total assets identified for {bank['Total assets'].notna().sum()} out of {len(bank)} complaints filed to banks")

    ## get asset information for credit unions
    ncua_path = os.path.join(cPATH, 'input', 'NCUA')
    ncua = get_ncua_data(ncua_path)

    cu = df[df['Company type']=='credit union']
    cu = cu.merge(ncua, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'],right_on=['RSSD', 'CYCLE_DATE']) # all credit unions have #ID_RSSD, so match with RSSD ID
    cu.drop(['CU_NUMBER', 'quarter', 'CYCLE_DATE', 'RSSD', 'CU_NAME'], axis=1, inplace=True)
    print(f"total assets of identified for {cu['Total assets'].notna().sum()} out of {len(cu)} complaints filed to credit unions")

    ## get asset information for bank holding companies
    bhcf_path = os.path.join(cPATH, 'input', 'FFIEC', 'Holding Company Financial Data')
    bhcf = get_bhc_financial_data(bhcf_path) # get total assets of bhc
    bhc_bank = bank_total_assets_in_bhc(nic_raw, ffiec) # get sum of total assets held by banks under bhc

    bhc_bank['Reporting Period End Date'] = bhc_bank['Reporting Period End Date'].astype(str)
    bhc = df[df['Company type']=='bank holding company']
    bhc = bhc.merge(bhcf, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['RSSD ID', 'bhcf report date']) # all bhcs have #ID_RSSD, so match with RSSD ID
    bhc = bhc.merge(bhc_bank, how='left', left_on=['#ID_RSSD', 'Quarter sent end date'], right_on=['#ID_RSSD_PARENT', 'Reporting Period End Date'])

    print(f"bhc total assets identified for {bhc['Total assets'].notna().sum()} out of {len(bhc)} complaints filed to bank holding companies")
    print(f"bhc total assets ranges between: {bhc['Total assets'].min()} to {bhc['Total assets'].max()}")
    print(f"bhc total assets held by banks identified for {bhc['BankAssets'].notna().sum()} out of {len(bhc)} complaints filed to bank holding companies")
    print(f"bhc total assets held by banks ranges between: {bhc['BankAssets'].min()} to {bhc['BankAssets'].max()}")

    bhc.to_csv(os.path.join(cPATH,  'temp', 'bhc_assets.csv')) # save to compare bhc total assets vs. bhc total assets held by banks
    bhc.drop(['quarter', 'RSSD ID', 'bhcf report date', 'Consolidated', '#ID_RSSD_PARENT', 'Reporting Period End Date', 'BankCount', 'BankAssets'], axis=1, inplace=True)

    others = df[~df['Company type'].isin(['bank', 'credit union', 'bank holding company'])]
    others.loc[:,'Total assets'] = np.nan
    df = pd.concat([bank, cu, bhc, others], ignore_index=True)

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

    ### save data with narratives to observe complaint narratives
    narr = df[df['With narrative']==1] # complaints with narrative
    znarr = df[(df['With narrative']==1) & (df['Zombie data'] == 1)] # complaints on zombie data with narrative
    narr.to_csv(os.path.join(cPATH, 'temp', 'complaints_narratives.csv'))
    znarr.to_csv(os.path.join(cPATH, 'temp', 'zombie_complaints_narratives.csv'))

    ### delete irrelevant columns
    df.drop(['NM_LGL', 'quarter', 'Quarter sent end date'], axis=1)

    ### save processed df
    df.to_csv(os.path.join(cPATH, 'output', 'complaints_processed.csv'))