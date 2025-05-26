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
    duration_order = ['< 1 day', '1 day', '2 days', '3 days', '4 days', '5 days', '6 days', '7 days', 'within two weeks',
                      'within a month', 'within 90 days', 'within 180 days', 'within a year', 'more than a year']
    df['Duration categorized'] = pd.Categorical(df['Duration categorized'], categories=duration_order, ordered=True)
    df['Duration grouped'] = df['Duration categorized'].apply(group_duration)
    group_order = ['< 1 day', 'within a week', 'within a month', 'more than a month']
    df['Duration grouped'] = pd.Categorical(df['Duration grouped'], categories=group_order, ordered=True)

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

    # save processed df
    df.to_csv(os.path.join(cPATH, 'output', 'complaints_processed.csv'))