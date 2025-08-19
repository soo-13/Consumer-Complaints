import itertools
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

from matplotlib.lines import Line2D


cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "analysis")

CCPA_timeline = {'CCPA enactment': '2018-06-28', 'CCPA implementation': '2020-01-01', 'CPRA amendment': '2020-11-03', 'CPRA implementation': '2023-01-01'}
CCPA_quarters = {label: pd.to_datetime(date).to_period('Q').strftime('%YQ%q') for label, date in CCPA_timeline.items()}


def save_plot(fig, filename, path=os.path.join(cPATH, 'temp'), tight=True):
    out_path = os.path.join(path, filename)
    if tight:
        fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)

def quarter_str_to_date(qstr):
    year = qstr[:4]
    month = (int(qstr[-1])-1)*3 + 1
    return pd.Timestamp(year=int(year), month=month, day=1)
    
def get_color_map(data, var, palette_type='colorblind'):
    palette = sns.color_palette(palette_type, n_colors=len(data[var].unique()))
    var_order = data[var].unique()
    color_map = dict(zip(var_order, palette))
    color_handles = [Line2D([0], [0], color=color_map[v], lw=2) for v in var_order]
    return color_map, color_handles, var_order

def draw_policy_line(ax, grouped, states, extended=False, qrt_col='Quarter sent'):
    for state in states:
        if state == 'CA' and extended:
            for label, q in CCPA_quarters.items(): # draw vertical lines at the time of policy event
                try:
                    q_date = pd.Period(q, freq='Q').to_timestamp()
                    if q_date in grouped[qrt_col].unique():
                        ax.axvline(x=q_date, color='grey', linestyle='--', linewidth=1)
                        ax.text(q_date + pd.Timedelta(days=50), ax.get_ylim()[1]*0.5, label, color='grey', ha='center', rotation=90, fontsize=10)
                except ValueError:
                    continue  # skip if the time of event is out of time range shown in the plot
        elif state in df['State'].unique():
            policy_date = df[df['State'] == state]['State privacy law'].dropna().unique() # plot policy line of state has implemented state privacy protection policy
            if len(policy_date) > 0:
                try:
                    policy_quarter = pd.to_datetime(policy_date[0])
                    if policy_quarter in grouped[qrt_col].unique():
                        ax.axvline(x=policy_quarter, color='grey', linestyle='--', linewidth=1)
                        ax.text(policy_quarter + pd.Timedelta(days=50), ax.get_ylim()[1] * 0.5, f"{state} policy\nimplementation", color='grey', ha='center', rotation=90, fontsize=10)
                except ValueError:
                    pass

def set_quarter_xticks(ax, tick_interval=1):
    def quarter_fmt(x, pos=None):
        date = mdates.num2date(x)
        quarter = (date.month - 1) // 3 + 1
        return f"{date.year}-Q{quarter}"
    
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10], interval=tick_interval))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(quarter_fmt))
    ax.tick_params(axis='x', rotation=90)

def exclusion_criteria(df, study_num):
    print(f"Applying inclusion-exclusion criteria for study {study_num}")
    print("Starts with total number of complaints: ", len(df))
    full = df[df['Company type'] == 'major credit bureaus'].copy()
    print("Analysis restricted to complaints sent to major credit bureaus:  ", len(tmp))

    # add variables 
    tmp['Experian'] = (tmp['Company']=='EXPERIAN INFORMATION SOLUTIONS INC.')
    tmp['Transunion'] = (tmp['Company']=='TRANSUNION INTERMEDIATE HOLDINGS, INC.')
    tmp['Equifax'] = (tmp['Company']=='EQUIFAX, INC.')
    tmp['Is CA'] = tmp['State'].apply(lambda x: 'CA' if x == 'CA' else 'Others')

    # change formats
    tmp['Quarter sent'] = tmp['Quarter sent'].apply(quarter_str_to_date)
    tmp['Quarter received'] = tmp['Quarter received'].apply(quarter_str_to_date)
    tmp['Consumer complaint narrative'] = tmp['Consumer complaint narrative'].str.strip()

    if study_num == 1:
        tmp = tmp[tmp['Consumer complaint narrative'].notna()].copy()
        print("Excluding complaints without narratives:  ", len(tmp))
        tmp = tmp[tmp['Dispute history'] != 'No valid answer'].copy()
        print("Excluding complaints of which LLM failed to classify dispute history:  ", len(tmp))
        tmp['Persistent data'] = tmp['Dispute history'].isin(['Prior dispute unresolved', 'Prior dispute resolved but reappeared'])
        tmp['CCPA'] = tmp['CCPA phase at sent'].isin([ "CCPA implemented, pre-CPRA", "CPRA amended, pre-implementation", "CPRA implemented"])
        #tmp = tmp[tmp['Dispute history'] != 'Prior dispute resolved but reappeared'].copy()
        #print("temporarily exclude Reappear category with high error rate to see its effect")
    return tmp


if __name__ == "__main__":
    ### load dataset
    #df = pd.read_csv(os.path.join(cPATH, 'input', 'complaints_processed.csv'), low_memory=False)
    df = pd.read_csv(os.path.join(cPATH, 'input', 'complaints_processed.csv'), low_memory=False)

    ######################################### STUDY 1 CCPA effect ##########################################
    ### DV: relief rate, unit of observation: state X quarterly level, treatment: CCPA X dispute history ###
    ########################################################################################################
    df_val = exclusion_criteria(df, study_num=1)
    savepath = os.path.join(cPATH, 'output', 'study1')
    if not os.path.exists(savepath):
        os.mkdir(savepath)

    ### Plot 1 - x: quarters, y: relief rate, line: CA vs. others 
    df_grouped = df_val.groupby(['State', 'Quarter sent', 'Is CA'], as_index=False).agg(relief_rate=('Is relief', 'mean')) # unit of observation
    df_grouped = df_grouped.groupby(['Is CA', 'Quarter sent'], as_index=False).agg(relief_rate=('relief_rate', 'mean'))

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='Quarter sent', y='relief_rate', style='Is CA', markers=True, alpha=0.6, ax=ax)

    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA'], extended=True)
    save_plot(fig, 'p1_relief_CCPAeffect.png', savepath)

    ### Plot 2 - x: quarters, y: relief rate, hue: persistent data, line: CA vs. others
    df_grouped = df_val.groupby(['State', 'Is CA', 'Quarter sent', 'Persistent data'], as_index=False).agg(relief_rate=('Is relief', 'mean'))
    df_grouped = df_grouped.groupby(['Is CA', 'Quarter sent', 'Persistent data'], as_index=False).agg(relief_rate=('relief_rate', 'mean'))

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='Quarter sent', y='relief_rate', hue='Persistent data', style='Is CA', markers=True, alpha=0.6, ax=ax)

    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA'], extended=True)
    save_plot(fig, 'p2_relief_CCPAeffect_persistentdata.png', savepath)

    ###### Let's look at other DV's as well
    ### Plot 3 - x: quarters received , y: proportion of complaints on persistent data, line: CA vs. others 
    df_grouped = df_val.groupby(['State', 'Quarter received', 'Is CA'], as_index=False).agg(pprop=('Persistent data', 'mean'))
    df_grouped = df_grouped.groupby(['Is CA', 'Quarter received'], as_index=False).agg(pprop=('pprop', 'mean'))

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='Quarter received', y='pprop', style='Is CA', markers=True, alpha=0.6, ax=ax)

    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA'], extended=True, qrt_col='Quarter received')
    save_plot(fig, 'p3_pprop_CCPAeffect.png', savepath)

    ### Plot 4 - x: quarters, y: relief rate, line: CA vs. FL 
    df_grouped = df_val[df_val['State'].isin(['CA', 'FL'])].groupby(['State', 'Quarter sent'], as_index=False).agg(relief_rate=('Is relief', 'mean')) # unit of observation

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='Quarter sent', y='relief_rate', hue='State', markers=True, alpha=0.6, ax=ax)

    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA', 'FL'])
    save_plot(fig, 'p4_relief_CCPAeffect_CAvsFL.png', savepath)

    ### Plot 5 - x: quarters, y: relief rate, hue: persistent data, line: CA vs. FL 
    df_grouped = df_val[df_val['State'].isin(['CA', 'FL'])].groupby(['State', 'Quarter sent', 'Persistent data'], as_index=False).agg(relief_rate=('Is relief', 'mean'))

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='Quarter sent', y='relief_rate', hue='State', style='Persistent data', markers=True, alpha=0.6, ax=ax)

    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA', 'FL'], extended=True)
    save_plot(fig, 'p5_relief_CCPAeffect_persistentdata_CAvsFL.png', savepath)

    ### Plot 6 - x: quarters received , y: proportion of complaints on persistent data, line: CA vs. FL 
    df_grouped = df_val[df_val['State'].isin(['CA', 'FL'])].groupby(['State', 'Quarter received'], as_index=False).agg(pprop=('Persistent data', 'mean'))

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='Quarter received', y='pprop', style='State', markers=True, alpha=0.6, ax=ax)

    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA', 'FL'], extended=True, qrt_col='Quarter received')
    save_plot(fig, 'p6_pprop_CCPAeffect_CAvsFL.png', savepath)

    ### Plot 7 - partialling out some controls to check parallel trend- x: quarters, y: relief rate, hue: CA vs. others
    # set unit of observation
    '''
    disaster = pd.read_csv(os.path.join('/Users', 'yeonsoo', 'Downloads', 'DisasterDeclarationsSummaries.csv'), low_memory=False)
    disaster = disaster[['declarationType', 'state', 'declarationDate', 'ihProgramDeclared', 'lastIAFilingDate', 'disasterNumber']]
    disaster['declarationDate'] = pd.to_datetime(disaster['declarationDate'])
    disaster['lastIAFilingDate'] = pd.to_datetime(disaster['lastIAFilingDate'])
    disaster = disaster[disaster['declarationDate'] > pd.Timestamp('2013-01-01', tz='UTC')]
    disaster['Period'] = disaster['lastIAFilingDate'] - disaster['declarationDate'] # median: 120 days
    disaster['declarationQuarter'] = pd.PeriodIndex(disaster['declarationDate'], freq='Q').astype(str)
    disaster['declarationQuarter'] = disaster['declarationQuarter'].apply(quarter_str_to_date)
    disaster['Quarter_list'] = disaster['declarationQuarter'].apply(lambda x: pd.period_range(start=pd.Period(x, freq='Q'), end=pd.Period(x, freq='Q')+1)) # assumes three months impact
    disaster_expanded = disaster.explode('Quarter_list')
    disaster_expanded['Quarter_list'] = disaster_expanded['Quarter_list'].astype(str).apply(quarter_str_to_date)
    disaster_expanded = disaster_expanded[['state', 'Quarter_list', 'ihProgramDeclared']].rename(columns={'Quarter_list':'declarationQuarter'})
    disaster_gp = disaster_expanded.groupby(['state', 'declarationQuarter']).agg(assistant=('ihProgramDeclared', 'max')).reset_index()
    disaster_gp['Disaster'] = 1

    df_val = df_val.merge(disaster_gp, how='left', left_on=['State', 'Quarter received'], right_on=['state', 'declarationQuarter'])
    df_val.drop(['state', 'declarationQuarter'], axis=1, inplace=True)
    df_val['assistant'] = df_val['assistant'].fillna(0)
    df_val['Disaster'] = df_val['Disaster'].fillna(0)
    '''

    df_val['Incorrect'] = (df_val['Issue'].isin(['Incorrect information on your report', "Incorrect information on credit report"]))
    df_val['Improper use'] = (df_val['Issue'].isin(['Improper use of your report', 'Improper use of my credit report']))
    df_val['Follow-up'] = (df_val['Issue'].isin(["Credit reporting company's investigation", "Problem with a credit reporting company's investigation into an existing problem", "Problem with a company's investigation into an existing problem"]))
    df_val['CreditAccess'] = (df_val['Issue'].isin(["Unable to get credit report/credit score", "Unable to get your credit report or credit score"]))
    df_val['IdentityTheft'] = (df_val['Issue'].isin(["Problem with fraud alerts or security freezes", "Credit monitoring or identity theft protection services", "Credit monitoring or identity protection"]))
    df_val['DebtCollection'] = (df_val['Issue'].isin(["Attempts to collect debt not owed", "Written notification about debt", "Cont'd attempts collect debt not owed"]))
    df_preshock = df_val[df_val['Quarter sent']<pd.Timestamp('2020-01-01')].copy() # use only pre-shock to check pre-trend
    
    df_grouped = (
        df_preshock
        .groupby(['State', 'Quarter sent', 'Is CA'], as_index=False)
        .agg(
            equifax=('Equifax', 'mean'),
            experian=('Experian', 'mean'),
            relief_rate=('Is relief', 'mean'),
            incorrect=('Incorrect', 'mean'),
            improper_use=('Improper use', 'mean'),
            follow_up=('Follow-up', 'mean'),
            credit_access=('CreditAccess', 'mean'),
            identity_theft=('IdentityTheft', 'mean'),
            debt_collection=('DebtCollection', 'mean'),
            count=('Is relief', 'size')
        )
        .reset_index()
    )

    '''
    df_grouped['automatic_reponse'] = (df_grouped['Quarter sent'] > pd.Timestamp('2020-03-01')).astype(int)
    df_grouped['CFPBreport'] = (df_grouped['Quarter sent'] >= pd.Timestamp('2022-01-01')).astype(int)
    df_grouped['CRCsupervision'] = ((df_grouped['Quarter sent']== pd.Timestamp('2015-10-01')) | (df_grouped['Quarter sent']== pd.Timestamp('2016-10-01')) | (df_grouped['Quarter sent']== pd.Timestamp('2017-01-01')) |
                                    (df_grouped['Quarter sent'].astype(str).str.startswith('2019')) | (df_grouped['Quarter sent']== pd.Timestamp('2021-07-01')) | (df_grouped['Quarter sent']== pd.Timestamp('2021-10-01')) |
                                    (df_grouped['Quarter sent']== pd.Timestamp('2023-04-01')) | (df_grouped['Quarter sent']== pd.Timestamp('2023-07-01')) | (df_grouped['Quarter sent']== pd.Timestamp('2023-10-01')) 
                                    ).astype(int)
    '''
    df_grouped['Equifax_breach'] = (df_grouped['Quarter sent'] == pd.Timestamp('2017-07-01'))*df_grouped['equifax']
    df_grouped['Equifax_settlement'] = ((df_grouped['Quarter sent'] >= pd.Timestamp('2019-07-01')) & (df_grouped['Quarter sent'] < pd.Timestamp('2020-07-01')))*df_grouped['equifax'] # 1 year time window

    # create interactions
    bureaus = ['equifax', 'experian']
    issues = ['incorrect', 'improper_use', 'follow_up']
    issues_ext = ['credit_access', 'identity_theft', 'debt_collection']

    interaction_cols = [f"{b}_{i}" for b, i in itertools.product(bureaus, issues)]
    #interaction_autoresp = [f"{b}_autoresp" for b in bureaus]
    for b, i in itertools.product(bureaus, issues):
        df_grouped[f"{b}_{i}"] = df_grouped[b] * df_grouped[i]
    #for b in bureaus:
    #    df_grouped[f"{b}_autoresp"] = df_grouped['automatic_reponse'] * df_grouped[b]

    # partialling out
    X = df_grouped[bureaus + issues + interaction_cols]
    X = sm.add_constant(X)
    model = sm.OLS(df_grouped['relief_rate'], X)
    results = model.fit()
    print(results.summary())
    df_grouped['residual'] = results.resid

    # aggregate and plot
    df_agg = df_grouped.groupby(['Is CA', 'Quarter sent']).agg(res_relief_rate=('residual', 'mean')).reset_index()

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_agg, x='Quarter sent', y='res_relief_rate', style='Is CA', markers=True, alpha=0.6, ax=ax)
    ax.set_ylabel("Residual after partialling out share of each credit bureaus and top issues from relief rate")
    set_quarter_xticks(ax)
    draw_policy_line(ax, df_agg, ['CA'], extended=True)
    save_plot(fig, 'p7_res_relief_CCPAeffect.png', savepath)

    # partialling out
    X = df_grouped[bureaus + issues]
    X = sm.add_constant(X)
    model = sm.WLS(df_grouped['relief_rate'], X, df_grouped['count'])
    results = model.fit()
    print(results.summary())
    df_grouped['residual'] = results.resid

    # aggregate and plot
    df_agg = df_grouped.groupby(['Is CA', 'Quarter sent']).agg(res_relief_rate=('residual', 'mean')).reset_index()

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_agg, x='Quarter sent', y='res_relief_rate', style='Is CA', markers=True, alpha=0.6, ax=ax)
    ax.set_ylabel("Residual after partialling out share of each credit bureaus and top issues from relief rate")
    set_quarter_xticks(ax)
    draw_policy_line(ax, df_agg, ['CA'], extended=True)
    save_plot(fig, 'p7_res_relief_CCPAeffect_weighted.png', savepath)


    import pdb; pdb.set_trace()
    '''
    # partialling out
    X = df_grouped[bureaus + issues + interaction_cols + ['Equifax_breach', 'automatic_reponse', 'CRCsupervision'] + interaction_autoresp]
    X = sm.add_constant(X)
    model = sm.OLS(df_grouped['relief_rate'], X)
    results = model.fit()
    print(results.summary())
    df_grouped['residual'] = results.resid

    # aggregate and plot
    df_agg = df_grouped.groupby(['Is CA', 'Quarter sent']).agg(res_relief_rate=('residual', 'mean')).reset_index()

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_agg, x='Quarter sent', y='res_relief_rate', style='Is CA', markers=True, alpha=0.6, ax=ax)
    ax.set_ylabel("Residual after partialling out factors from relief rate")
    set_quarter_xticks(ax)
    draw_policy_line(ax, df_agg, ['CA'], extended=True)
    save_plot(fig, 'p7_res_relief_CCPAeffec_breach_autoresp_supervision.png', savepath)

    # partialling out
    X = df_grouped[bureaus + issues + interaction_cols + ['Equifax_breach', 'automatic_reponse', 'CFPBreport'] + interaction_autoresp]
    X = sm.add_constant(X)
    model = sm.OLS(df_grouped['relief_rate'], X)
    results = model.fit()
    print(results.summary())
    df_grouped['residual'] = results.resid

    # aggregate and plot
    df_agg = df_grouped.groupby(['Is CA', 'Quarter sent']).agg(res_relief_rate=('residual', 'mean')).reset_index()

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_agg, x='Quarter sent', y='res_relief_rate', style='Is CA', markers=True, alpha=0.6, ax=ax)
    ax.set_ylabel("Residual after partialling out factors from relief rate")
    set_quarter_xticks(ax)
    draw_policy_line(ax, df_agg, ['CA'], extended=True)
    save_plot(fig, 'p7_res_relief_CCPAeffec_breach_autoresp_report.png', savepath)



    df_val['bi_year'] = np.where(df_val['Quarter sent'].dt.month <= 6, 1, 2)
    df_val['year_bi'] = df_val['Quarter sent'].dt.year.astype(str) + '-H' + df_val['bi_year'].astype(str)
    sorted_periods = sorted(df_val['year_bi'].unique()) 
    df_val['year_bi'] = pd.Categorical(df_val['year_bi'], categories=sorted_periods, ordered=True)

    fips_counts = df_val.groupby(['fips', 'year_bi'])['Is CA'].nunique().reset_index()
    fips_counts.rename(columns={'Is CA':'num_IsCA'}, inplace=True)

    mixed_fips = fips_counts[fips_counts['num_IsCA'] > 1][['fips', 'year_bi']]

    df_clean = df_val.merge(mixed_fips, on=['fips','year_bi'], how='left', indicator=True)
    df_clean = df_clean[df_clean['_merge']=='left_only'].drop(columns=['_merge'])
    
    df_grouped = df_clean.groupby(['fips', 'year_bi', 'Is CA']).agg(equifax=('Equifax', 'mean'), experian=('Experian', 'mean'), relief_rate=('Is relief', 'mean'), incorrect=('Incorrect', 'mean'), improper_use=('Improper use', 'mean'), follow_up=('Follow-up', 'mean')).reset_index()

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.lineplot(data=df_grouped, x='year_bi', y='relief_rate', style='Is CA', markers=True, alpha=0.6, ax=ax)
    ax.set_ylabel("Relief rate")
    set_quarter_xticks(ax)
    draw_policy_line(ax, df_grouped, ['CA'], extended=True)
    save_plot(fig, 'p8_relief_CCPAeffect_county_biyearly.png', savepath)


    ccpa_date = pd.to_datetime('2020-01-01')
    df_val['quarter_num'] = (df_val['Quarter sent'].dt.year - df_val['Quarter sent'].dt.year.min()) * 4 + (df_val['Quarter sent'].dt.quarter - 1)
    ccpa_quarter_num = (ccpa_date.year - df_val['Quarter sent'].dt.year.min()) * 4 + (ccpa_date.quarter - 1)
    df_grouped = df_val.groupby(['State', 'quarter_num'], as_index=False).agg(relief_rate=('Is relief', 'mean')) 

    sc = Synth(df_grouped, "relief_rate", "State", "quarter_num", 1990, "CA", n_optim=100, random_seed=1234)

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sc.plot(["original", "pointwise", "cumulative"], treated_label="CA", synth_label="Synthetic Other States", treatment_label="CCPA implementation")
    print(sc.original_data.weight_df)
    save_plot(fig, 'p7_SC_reliefrate.png', savepath)
    '''
