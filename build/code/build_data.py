import glob
import itertools
import os
import pandas as pd

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

def read_cfpd_depository_institutions_list_excels():
    files = list(itertools.chain.from_iterable(glob.glob(os.path.join(cPATH, 'input', 'CFPD', 'depository_institutions', ext)) for ext in ('*.xlsx', '*.xls')))

    dfs = []
    no_id = []
    for file in files:
        filename = os.path.basename(file)
        ext = filename.split('.')[-1]
        if filename == '201209_CFPB_depository-institutions-list.xls':
            df = pd.read_excel(file, header=2, engine='xlrd')
            df.columns = df.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        elif ext == '.xls':
            df = pd.read_excel(file, header=1, engine='xlrd')
            df.columns = df.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
        else:
            df = pd.read_excel(file, header=1)

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

def get_nic_data():
    nic_actv = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_ACTIVE.CSV')) # NIC dataset to obtain institution types
    nic_clsd = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_CLOSED.CSV'))
    nic_brnch = pd.read_csv(os.path.join(cPATH, 'input', 'NIC', 'CSV_ATTRIBUTES_BRANCHES.CSV'))
    nic_actv = nic_actv[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL']]
    nic_clsd = nic_clsd[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL']]
    nic_brnch = nic_brnch[['#ID_RSSD', 'CHTR_TYPE_CD', 'ENTITY_TYPE', 'NM_LGL']]
    nic = pd.concat([nic_actv, nic_clsd, nic_brnch])
    nic['NM_LGL'] = nic['NM_LGL'].str.upper().str.strip()

    # create company type variable based on CHTR_TYPE_CD and ENTITY_TYPE
    nic['Company type'] = 'others'
    bank_ind = (nic['CHTR_TYPE_CD'].isin([200, 300, 320, 340]) |nic['ENTITY_TYPE'].isin(['SMB', 'DBR', 'NAT', 'NMB', 'ISB']))
    cu_ind =  (nic['CHTR_TYPE_CD']==330) |nic['ENTITY_TYPE'].isin(['FCU', 'SCU']) # credit union
    bhc_ind = (nic['ENTITY_TYPE'].isin(['BHC', 'FBH', 'BHC', 'FHD', 'SLHC'])) # bank/saving/loan holding companies
    insur_ind = (nic['CHTR_TYPE_CD']==550) # insurance broker or agent and/or insurance company
    sec_ind = (nic['CHTR_TYPE_CD']==700) # Securities Broker and/or Dealer
    nic.loc[sec_ind, 'Company type'] = 'security related'
    nic.loc[insur_ind, 'Company type'] = 'insurance related'
    nic.loc[bhc_ind, 'Company type'] = 'bank holding company'
    nic.loc[cu_ind, 'Company type'] = 'credit union'
    nic.loc[bank_ind, 'Company type'] = 'bank'

    # if the same name falls into two or more category, apply the follwing priority
    priority = {'bank': 1, 'credit union': 2, 'bank holding company':3, 'insurance related':4, 'security related': 5, 'others':6}
    nic['type_priority'] = nic['Company type'].map(priority)
    priority_combos = (nic.groupby('NM_LGL')['type_priority'].apply(lambda x: tuple(sorted(x.unique()))).reset_index(name='priority_combo'))
    print(priority_combos['priority_combo'].value_counts().reset_index(name='count').rename(columns={'index': 'priority_combo'})) # number of 
    nic_dedup = nic.sort_values('type_priority', ascending=True).drop_duplicates(subset='NM_LGL', keep='first')

    
    nic_dedup = nic_dedup.drop(['CHTR_TYPE_CD', 'ENTITY_TYPE', 'type_priority'], axis=1)
    nic_dedup = nic_dedup.drop_duplicates()
    return nic_dedup, nic
    
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

    ### institution type
    inst = read_cfpd_depository_institutions_list_excels() # match the RSSD ID info provided by CFPD to NIC dataset
    inst = inst[['#ID_RSSD', 'Company']]
    inst = inst.drop_duplicates('Company')
    inst['CFPD_depository'] = 1 # indicator of whether the company is included in the depository institutions affiliated with CFPD
    nic, nic_raw = get_nic_data()

    # get RSSD ID from depository institutions info
    df['Company'] = df['Company'].str.upper().str.strip() 
    df = df.merge(inst, how='left', on='Company')
    df['CFPD_depository'] = df['CFPD_depository'].fillna(0).astype(int)
    print(f"{df['#ID_RSSD'].isna().sum()} rows with missing #ID_RSSD :")
    print(df[['Company', '#ID_RSSD']].head())

    #import pdb; pdb.set_trace()
    # get company type by merging with nic using RSSD ID
    df = df.merge(nic_raw, how='left', on='#ID_RSSD')

    # in case ID RSSD is not provided, try matching with legal name
    df_with_id = df[df['#ID_RSSD'].notna()]
    df_no_id = df[df['#ID_RSSD'].isna()].drop(columns=['#ID_RSSD', 'Company type'], errors='ignore')
    
    df = df.drop('#ID_RSSD', axis=1)
    nic.drop('#ID_RSSD', axis=1)
    nic = nic.drop_duplicates()
    nic.rename(columns={'NM_LGL': 'Company'}, inplace=True)

    df_no_id = df_no_id.merge(nic, how='left', on='Company')
    df = pd.concat([df_with_id, df_no_id], ignore_index=True)

    # major credit bureaus
    credit_bureaus = ['EXPERIAN INFORMATION SOLUTIONS INC.', 'TRANSUNION INTERMEDIATE HOLDINGS, INC.', 'EQUIFAX, INC.']
    cb_ind = df['Company'].isin(credit_bureaus)
    df.loc[cb_ind, 'Company type'] = 'major credit bureaus'
    df['Company type'] = df['Company type'].fillna('others')

    # data broker
    db = pd.read_excel(os.path.join(cPATH, 'input', 'Data_Broker_Full_Registry_2025.xlsx'))
    db['Name'] = db['Name'].str.upper().str.strip() 
    db_names = db['Name'].unique().tolist()
    db_ind = df['Company'].isin(db_names)
    df.loc[db_ind, 'Company type'] = 'data broker'
    print(df['Company type'].unique())
    print(df.groupby('Company type').count())

    # save data with narratives to observe complaint narratives
    narr = df[df['With narrative']==1] # complaints with narrative
    znarr = df[(df['With narrative']==1) & (df['Zombie data'] == 1)] # complaints on zombie data with narrative
    narr.to_csv(os.path.join(cPATH, 'temp', 'complaints_narratives.csv'))
    znarr.to_csv(os.path.join(cPATH, 'temp', 'zombie_complaints_narratives.csv'))


    # save processed df
    df.to_csv(os.path.join(cPATH, 'output', 'complaints_processed.csv'))