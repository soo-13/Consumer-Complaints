import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.pyplot as plt

from matplotlib.lines import Line2D

cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "analysis")


def save_plot(fig, filename, path=os.path.join(cPATH, 'temp'), tight=True):
    out_path = os.path.join(path, filename)
    if tight:
        fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)

def plot_quarterly_trend_zombie_data():
    gp1 = df[df['Zombie data'] == 1].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0)
    gp2 = df[df['Zombie data'] == 0].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0)
    gp3 = df.groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0)

    # reindex so all plots share the same x-axis
    gp1 = gp1.reindex(quarter_index, fill_value=0)
    gp2 = gp2.reindex(quarter_index, fill_value=0)
    gp3 = gp3.reindex(quarter_index, fill_value=0)

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    def plot_stacked(ax, grouped, title):
        grouped.plot(kind='bar', stacked=True, ax=ax, color={True: '#1f77b4', False: '#ff7f0e'}, width=0.8)
        ax.set_title(title)
        ax.set_ylabel("Complaint count")
        label_map = {True: "With narrative", False: "No narrative"}
        ax.legend([label_map.get(col, str(col)) for col in grouped.columns], loc='best')

        for label, q in CCPA_quarters.items(): # draw vertical lines at the time of policy event
            try:
                idx = grouped.index.astype(str).tolist().index(q)
                ax.axvline(x=idx - 0.5, color='grey', linestyle='--', linewidth=1)
                ax.text(idx, ax.get_ylim()[1]*0.5, label, color='grey', ha='center', rotation=90, fontsize=10)
            except ValueError:
                continue  # skip if the time of event is out of time range shown in the plot

    plot_stacked(axes[0], gp1, "Zombie Data Complaints")
    plot_stacked(axes[1], gp2, "Other Complaints")
    plot_stacked(axes[2], gp3, "All Complaints")

    axes[2].set_xlabel("Quarter")
    save_plot(fig, 'quarterly_trend_zombie_data.png')

def plot_quarterly_trend_zombie_data_CA():
    gp1z = df[(df['State'] == 'CA') & (df['Zombie data'] == 1)].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0) # California zombie data
    gp2z = df[(df['State'] != 'CA') & (df['Zombie data'] == 1)].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0) # other states zombie data
    gp1o = df[(df['State'] == 'CA') & (df['Zombie data'] == 0)].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0) # California other complaints
    gp2o = df[(df['State'] != 'CA') & (df['Zombie data'] == 0)].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0) # other states other complaints

    # reindex so all plots share the same x-axis and complaints on zombie data is stacked below other complaints
    gp1z = gp1z.reindex(quarter_index, fill_value=0)
    gp2z = gp2z.reindex(quarter_index, fill_value=0)

    def plot_stacked(ax, grouped, title):
        grouped.plot(kind='bar', stacked=True, ax=ax, color={1: '#1f77b4', 0: '#ff7f0e'}, width=0.8)
        ax.set_title(title)
        ax.set_ylabel("Complaint count")
        label_map = {True: "With narrative", 0: "No narrative"}
        ax.legend([label_map.get(col, str(col)) for col in grouped.columns], loc='best')

        for label, q in CCPA_quarters.items(): # draw vertical lines at the time of policy event
            try:
                idx = grouped.index.astype(str).tolist().index(q)
                ax.axvline(x=idx - 0.5, color='grey', linestyle='--', linewidth=1)
                ax.text(idx, ax.get_ylim()[1]*0.5, label, color='grey', ha='center', rotation=90, fontsize=10)
            except ValueError:
                continue  # skip if the time of event is out of time range shown in the plot

    fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    plot_stacked(axes[0], gp1z, "California")
    plot_stacked(axes[1], gp2z, "Other States")
    axes[1].set_xlabel("Quarter")
    save_plot(fig, 'quarterly_trend_zombie_data_CA.png')

    fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    plot_stacked(axes[0], gp1o, "California")
    plot_stacked(axes[1], gp2o, "Other States")
    axes[1].set_xlabel("Quarter")
    save_plot(fig, 'quarterly_trend_other_complaints_CA.png')

def plot_quarterly_trend_zombie_data_most_complaints_states(): # top 3 states with most complaints
    states = df['State'].value_counts().nlargest(3).index.tolist()

    ncomplaints = {}
    for state in states:
        ncomplaints[f'z{state}'] = df[(df['State'] == state) & (df['Zombie data'] == 1)].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0).reindex(quarter_index)
        ncomplaints[f'o{state}'] = df[(df['State'] == state) & (df['Zombie data'] == 0)].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0).reindex(quarter_index)

    def plot_stacked(ax, grouped, title):
        grouped.plot(kind='bar', stacked=True, ax=ax, color={1: '#1f77b4', 0: '#ff7f0e'}, width=0.8)
        ax.set_title(title)
        ax.set_ylabel("Complaint count")
        label_map = {True: "With narrative", 0: "No narrative"}
        ax.legend([label_map.get(col, str(col)) for col in grouped.columns], loc='best')

        for label, q in CCPA_quarters.items(): # draw vertical lines at the time of policy event
            try:
                idx = grouped.index.astype(str).tolist().index(q)
                ax.axvline(x=idx - 0.5, color='grey', linestyle='--', linewidth=1)
                ax.text(idx, ax.get_ylim()[1]*0.5, label, color='grey', ha='center', rotation=90, fontsize=10)
            except ValueError:
                continue  # skip if the time of event is out of time range shown in the plot

    fig, axes = plt.subplots(3, 1, figsize=(14, 18), sharex=True)
    for i in range(3):
        plot_stacked(axes[i], ncomplaints[f'z{states[i]}'], states[i])
    axes[2].set_xlabel("Quarter")
    save_plot(fig, 'quarterly_trend_zdata_most_complaints_states.png')

    fig, axes = plt.subplots(3, 1, figsize=(14, 18), sharex=True)
    for i in range(3):
        plot_stacked(axes[i], ncomplaints[f'o{states[i]}'], states[i])
    axes[2].set_xlabel("Quarter")
    save_plot(fig, 'quarterly_trend_others_most_complaints_states.png')

def plot_quarterly_companies_in_top_states(n):
    states = df['State'].value_counts().nlargest(n).index.tolist()
    companies = df['Company'].value_counts().nlargest(3).index.tolist()

    def plot_line(ax, grouped, state, title):
        grouped_prop = grouped.div(grouped.sum(axis=1), axis=0).fillna(0) * 100
        grouped_prop.index = grouped_prop.index.astype(str)
        grouped_prop.plot(ax=ax, marker='o')
        ax.set_title(title)
        ax.set_ylabel("Complaint share (%)")
        ax.set_xlabel("Quarter complaints were received")
        ax.legend(title="Company", bbox_to_anchor=(1.05, 1), loc='best')

        ax.set_xticks(range(len(grouped_prop.index))) 
        ax.set_xticklabels(grouped_prop.index, rotation=90, ha='right') 

        policy_date = df[df['State'] == state]['State privacy law'].dropna().unique() # plot policy line of state has implemented state privacy protection policy
        if len(policy_date) > 0:
            try:
                policy_quarter = pd.to_datetime(policy_date[0]).to_period("Q").strftime("%YQ%q")
                idx = grouped_prop.index.astype(str).tolist().index(str(policy_quarter))
                print(f"idx for {state}: {idx}")
                ax.axvline(x=idx, color='grey', linestyle='--', linewidth=1)
                ax.text(idx, ax.get_ylim()[1] * 0.5, f"{state} policy\nimplementation",
                        color='grey', ha='center', rotation=90, fontsize=10)
            except ValueError:
                pass

    df['Top company'] = df['Company'].where(df['Company'].isin(companies), other='Others')

    for state in states: 
        fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
        ztab = df[(df['State'] == state) & (df['Zombie data'] == 1)].groupby(['Quarter received', 'Top company'], observed=False).size().unstack(fill_value=0).reindex(quarter_index)
        otab = df[(df['State'] == state) & (df['Zombie data'] == 0)].groupby(['Quarter received', 'Top company'], observed=False).size().unstack(fill_value=0).reindex(quarter_index)

        plot_line(axes[0], ztab, state, f'zombie data complaints / {state}')
        plot_line(axes[1], otab, state, f'other complaints / {state}')
        axes[1].set_xlabel("Quarter")
        save_plot(fig, f'quarterly_trend_complaints_counts_{state}.png')

    df.drop(columns='Top company', inplace=True)

def _plot_complaint_trend(df, quarter_index, ax1, title_suffix="", policy_date=[]):
    obs = df.groupby(['Quarter received', 'Company type'], observed=False).size().unstack(fill_value=0).reindex(quarter_index).fillna(0)
    obs.index = obs.index.astype(str)
    left_df = obs[['bank', 'credit union', 'bank holding company', 'data broker']]
    right_df = obs[['major credit bureaus']]

    ax2 = ax1.twinx()  # secondary y-axis

    left_df.plot(ax=ax1, marker='o', legend=False)
    right_df.plot(ax=ax2, marker='x', linestyle='--', legend=False, color='tab:red')

    ax1.set_xticks(range(len(obs.index)))
    ax1.set_xticklabels(obs.index, rotation=90, ha='right')

    ax1.set_title(f"Complaints by Company Type - {title_suffix}")
    ax1.set_ylabel("Complaints Counts for Other Institutions")
    ax2.set_ylabel("Major Credit Bureaus Complaint Counts")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, title="Company Type", bbox_to_anchor=(1.05, 1), loc='upper left')

    if len(policy_date) > 0:
        try:
            policy_quarter = pd.to_datetime(policy_date[0]).to_period("Q").strftime("%YQ%q")
            idx = obs.index.astype(str).tolist().index(str(policy_quarter))
            ax1.axvline(x=idx, color='grey', linestyle='--', linewidth=1)
            ax1.text(idx, ax1.get_ylim()[1] * 0.5, "policy\nimplementation",
                    color='grey', ha='center', rotation=90, fontsize=10)
        except ValueError:
            pass

def plot_company_type(n):
    top_states = df['State'].value_counts().nlargest(n).index.tolist()

    # number of complaints for each company type (quarterly trend)
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_complaint_trend(df, quarter_index, ax, title_suffix="")
    save_plot(fig, 'companytype-quarterly.png')

    # number of complaints for each company type (quarterly trend) in top n states
    for state in top_states:
        policy_date = df[df['State'] == state]['State privacy law'].dropna().unique()
        fig, ax = plt.subplots(figsize=(12, 6))
        _plot_complaint_trend(df[df['State'] == state], quarter_index, ax, title_suffix=f"({state})", policy_date=policy_date)
        save_plot(fig, f'companytype-quarterly-{state}.png')

    # number of complaints for each company type (quarterly trend) - zombie data vs. others
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_complaint_trend(df[df['Zombie data'] == 1], quarter_index, ax, title_suffix="(zombie data related)")
    save_plot(fig, f"companytype-quarterly-zombie.png")
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_complaint_trend(df[df['Zombie data'] == 0], quarter_index, ax, title_suffix="(others)")
    save_plot(fig, f"companytype-quarterly-others.png")

    # number of complaints for each company type (quarterly trend) - with/without narratives
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_complaint_trend(df[df['With narrative'] == 1], quarter_index, ax, title_suffix="(with narrative)")
    save_plot(fig, f"companytype-quarterly-withnarrative.png")
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_complaint_trend(df[df['With narrative'] == 0], quarter_index, ax, title_suffix="(missing narrative)")
    save_plot(fig, f"companytype-quarterly-missingnarrative.png")

    # state-quarterly-companytype level (zombie vs. others) complaints count
    for state in top_states:
        zdf = df[(df['State'] == state) & (df['Zombie data'] == 1)]
        odf = df[(df['State'] == state) & (df['Zombie data'] == 0)]
        policy_date = df[df['State'] == state]['State privacy law'].dropna().unique()

        fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
        _plot_complaint_trend(zdf, quarter_index, axes[0], title_suffix=f"({state}-zombie)", policy_date=policy_date)
        _plot_complaint_trend(odf, quarter_index, axes[1], title_suffix=f"({state}-others)", policy_date=policy_date)
        save_plot(fig, f'companytype-quarterly-{state}-zombie.png')

    # state-quarterly-companytype level (zombie vs. others) complaints count
    for state in top_states:
        ndf = df[(df['State'] == state) & (df['With narrative'] == 1)]
        mdf = df[(df['State'] == state) & (df['With narrative'] == 0)]
        policy_date = df[df['State'] == state]['State privacy law'].dropna().unique()

        fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
        _plot_complaint_trend(ndf, quarter_index, axes[0], title_suffix=f"({state}-withnarrative)", policy_date=policy_date)
        _plot_complaint_trend(mdf, quarter_index, axes[1], title_suffix=f"({state}-missingnarrative)", policy_date=policy_date)
        save_plot(fig, f'companytype-quarterly-{state}-narrative.png')

def plot_complaints_and_response_per_size_company_quarter_level(company_type):
    subset = df[df['Company type']==company_type]

    grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'),reliefs=('Is relief', 'sum'), total_assets=('Log real total assets', 'mean')).reset_index())
    grouped['relief_rate'] = grouped['reliefs'] / grouped['complaints']
    grouped['log_complaints'] = np.log1p(grouped['complaints'])
    print(f"total assets for {company_type} ranges between {grouped['total_assets'].min()} and {grouped['total_assets'].max()}")
    print(f"{grouped['Company'].nunique()} unique companies included in the dataset")

    ### x: total assets, y1: complaint counts, y2: relief probability, color: company (to approximately observe company effect)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    sns.scatterplot(data=grouped, x='total_assets', y='log_complaints', hue='Company', palette='husl', legend=False, ax=axes[0], alpha=0.6)
    axes[0].set_ylabel('Log complaint counts per quarter-company')
    axes[0].set_title(f'{company_type} - Log Complaint Counts vs Log Total Assets')

    sns.scatterplot(data=grouped, x='total_assets', y='relief_rate', hue='Company', palette='husl', legend=False,ax=axes[1], alpha=0.6)
    axes[1].set_ylabel('Relief probability')
    axes[1].set_xlabel('Logarithm of total assets (in 2013 dollars)')
    axes[1].set_title(f'{company_type} - Relief Probability vs Log Total Assets')

    save_plot(fig, f'per_size_company_quarterly_level_{company_type}.png')

    ### left panels: zombie data related compalints, right panel: other complaints (same plot with previous one)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True)
    zombie_title = {0: 'Other Complaints', 1: 'Zombie Data Complaints'}
    for i in range(2):
        subset = df[(df['Company type'] == company_type) & (df['Zombie data'] == i)]

        grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'), reliefs=('Is relief', 'sum'), total_assets=('Log real total assets', 'mean')).reset_index())
        grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
        grouped['log_complaints'] = np.log1p(grouped['complaints'])

        sns.scatterplot(data=grouped, x='total_assets', y='log_complaints', hue='Company', palette='husl', alpha=0.6, ax=axes[0, i], legend=False)
        axes[0, i].set_title(f"{company_type} | {zombie_title[i]} | Log Complaints Counts")
        axes[0, i].set_ylabel('Log Complaints Counts (company-quarter level)')

        sns.scatterplot(data=grouped, x='total_assets', y='relief_rate', hue='Company', palette='husl', alpha=0.6, ax=axes[1, i], legend=False)
        axes[1, i].set_title(f"{company_type} | {zombie_title[i]}| Relief Probability")
        axes[1, i].set_ylabel('Relief probability (company-quarter level)')
        axes[1, i].set_xlabel('Log total assets (in 2013 dollars)')

        save_plot(fig, f'per_size_company_quarterly_level_zombie_{company_type}.png')

def plot_complaints_and_response_per_size_company_level():    
    ### company level, x: total assets, y1: complaint counts, y2: relief probability
    # total assets aggregated through taking average across quarters
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    palette = {'bank': 'blue', 'credit union': 'orange', 'bank holding company': 'green'}
    for company_type in ['bank', 'credit union', 'bank holding company']:
        subset = df[df['Company type']==company_type]
    
        grouped = subset.groupby(['Company']).agg(complaints=('Company', 'count'), reliefs=('Is relief', 'sum'), assets=('Log real total assets', 'mean')).reset_index()
        grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
        grouped['log_complaints'] = np.log1p(grouped['complaints'])

        sns.scatterplot(data=grouped, x='assets', y='log_complaints', hue=[company_type] * len(grouped), palette=[palette[company_type]], legend=True, ax=axes[0], alpha=0.6)
        sns.scatterplot(data=grouped, x='assets', y='relief_rate', hue=[company_type] * len(grouped), palette=[palette[company_type]], legend=True, ax=axes[1], alpha=0.6)

    axes[0].set_ylabel('Log complaint counts per company')
    axes[0].set_title('Log Complaint Counts vs Log Total Assets')

    axes[1].set_ylabel('Relief probability')
    axes[1].set_xlabel('Logarithm of Total Assets (in 2013 dollars)')
    axes[1].set_title(f'Relief Probability vs Log Total Assets')

    save_plot(fig, 'per_size_company_level.png')  

    fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True) 
    zombie_title = {0: 'Other Complaints', 1: 'Zombie Data Complaints'}
    for i in range(2):
        for company_type in ['bank', 'credit union', 'bank holding company']:
            subset = df[(df['Company type']==company_type) &  (df['Zombie data']==i)]

            grouped = subset.groupby(['Company']).agg(complaints=('Company', 'count'), reliefs=('Is relief', 'sum'), assets=('Log real total assets', 'mean')).reset_index()
            grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
            grouped['log_complaints'] = np.log1p(grouped['complaints'])

            sns.scatterplot(data=grouped, x='assets', y='log_complaints', hue=[company_type] * len(grouped), palette=[palette[company_type]], legend=True, ax=axes[0,i], alpha=0.6)
            sns.scatterplot(data=grouped, x='assets', y='relief_rate', hue=[company_type] * len(grouped), palette=[palette[company_type]], legend=True, ax=axes[1,i], alpha=0.6)
        
            axes[0, i].set_title(f"{zombie_title[i]} | Log Complaints Counts vs. Log Total Assets (in 2013 Dollars)")
            axes[1, i].set_title(f"{zombie_title[i]} | Relief Probability vs. Log Total Assets (in 2013 Dollars)")
            axes[0, i].set_ylabel('Log complaint counts(company-quarter level)')
            axes[1, i].set_ylabel('Relief probability (company-quarter level)')
        axes[1, 0].set_xlabel('Logarithm of Total Assets (in 2013 dollars)')
        axes[1, 1].set_xlabel('Logarithm of Total Assets (in 2013 dollars)')
    save_plot(fig, 'per_size_company_level_zombie.png')  

def plot_response_per_complaint_count_company_quarterly_level():
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    for i, company_type in enumerate(['bank', 'credit union', 'bank holding company']):
        subset = df[df['Company type']==company_type]

        grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'),reliefs=('Is relief', 'sum')).reset_index())
        grouped['relief_rate'] = grouped['reliefs'] / grouped['complaints']
        grouped['log_complaints'] = np.log1p(grouped['complaints'])

        ### x: complaint counts, y2: relief probability, color: company (to approximately observe company effect)
        sns.scatterplot(data=grouped, x='log_complaints', y='relief_rate', hue='Company', palette='husl', legend=False, ax=axes[i], alpha=0.6)

        axes[i].set_ylabel('Relief probability per quarter-company')
        axes[i].set_title(f'{company_type} - Log Complaint Counts vs Relief probability')

    axes[1].set_xlabel('Logarithm of Complaint Counts')
    save_plot(fig, 'relief_per_complaints_company_quarterly_level.png')

    ### left panels: other compalints, right panel: zombie related complaints (same plot with previous one)
    fig, axes = plt.subplots(2, 3, figsize=(20, 12), sharex=True)
    zombie_title = {0: 'Other Complaints', 1: 'Zombie Data Complaints'}
    for i in range(2):
        for j, company_type in enumerate(['bank', 'credit union', 'bank holding company']):
            subset = df[(df['Company type'] == company_type) & (df['Zombie data'] == i)]

            grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'), reliefs=('Is relief', 'sum')).reset_index())
            grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
            grouped['log_complaints'] = np.log1p(grouped['complaints'])

            sns.scatterplot(data=grouped, x='log_complaints', y='relief_rate', hue='Company', palette='husl', alpha=0.6, ax=axes[i, j], legend=False)
            axes[i, j].set_title(f"{company_type} | {zombie_title[i]} | Log Complaints Counts vs. Relief Probability")
            axes[i, j].set_ylabel('Relief probability (company-quarter level)')
            axes[1, j].set_xlabel('Log complaint counts')

        save_plot(fig, 'relief_per_complaints_company_quarterly_level_zombie.png')

def plot_response_per_complaint_count():
    fig, ax = plt.subplots(1, 1, figsize=(14, 8), sharex=True)

    subset = df[df['Company type'].isin(['bank', 'credit union', 'bank holding company', 'data broker', 'major credit bureaus'])]
    grouped = subset.groupby(['Company', 'Company type']).agg(complaints=('Company', 'count'), reliefs=('Is relief', 'sum')).reset_index()
    grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
    grouped['log_complaints'] = np.log1p(grouped['complaints'])

    sns.scatterplot(data=grouped, x='log_complaints', y='relief_rate', hue='Company type', palette='husl', legend=True, alpha=0.6)

    ax.set_ylabel('Relief probability per company')
    ax.set_title('Log Complaint Counts vs Relief probability')
    ax.set_xlabel('Logarithm of complaint counts')
    save_plot(fig, 'relief_per_complaints_company_level.png')  

    ### left panel: other complaints, right panel: zombie data complaints
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True) 
    zombie_title = {0: 'Other Complaints', 1: 'Zombie Data Complaints'}
    for i in range(2):
        subset = df[(df['Company type'].isin(['bank', 'credit union', 'bank holding company', 'data broker', 'major credit bureaus', 'scra'])) &  (df['Zombie data']==i)]

        grouped = subset.groupby(['Company', 'Company type']).agg(complaints=('Company', 'count'), reliefs=('Is relief', 'sum')).reset_index()
        grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
        grouped['log_complaints'] = np.log1p(grouped['complaints'])

        sns.scatterplot(data=grouped, x='log_complaints', y='relief_rate', hue='Company type', palette='colorblind', legend=True, ax=axes[i], alpha=0.6)

        axes[i].set_title(f"{zombie_title[i]} | Log Complaints Counts vs. Relief Probability")
        axes[i].set_ylabel('Relief probability (company-quarter level)')
    axes[1].set_xlabel('Log complaint counts(company-quarter level)')
    save_plot(fig, 'relief_per_complaints_company_level_zombie.png')  

def quarterly_plot_assets_vs_relief():
    plt.style.use('default') 
    palette = sns.color_palette('tab20')
    df['Quarter sent'] = pd.PeriodIndex(df['Quarter sent'], freq='Q').to_timestamp()

    # Grouping for plots
    df_cq = df.groupby(['Quarter sent', 'Company', 'Company type']).agg(TotalAssets=('Log real total assets', 'mean'), ReliefRate=('Is relief', 'mean')).reset_index()
    df_q = df.groupby(['Quarter sent', 'Company type']).agg(TotalAssets=('Log real total assets', 'mean'), ReliefRate=('Is relief', 'mean')).reset_index()
    df_cq_z = df.groupby(['Quarter sent', 'Company', 'Zombie data', 'Company type']).agg(TotalAssets=('Log real total assets', 'mean'), ReliefRate=('Is relief', 'mean')).reset_index()
    df_q_z = df.groupby(['Quarter sent', 'Company type', 'Zombie data']).agg(TotalAssets=('Log real total assets', 'mean'), ReliefRate=('Is relief', 'mean')).reset_index()
    df_cq['ReliefRate'] = df_cq['ReliefRate'] + 0.1
    df_q['ReliefRate'] = df_q['ReliefRate'] + 0.1
    df_cq_z['ReliefRate'] = df_cq_z['ReliefRate'] + 0.1
    df_q_z['ReliefRate'] = df_q_z['ReliefRate'] + 0.1

    # P1 - Company-Quarter level plot, x: Quarter sent, y: Total assets, size: relief rate, color: company
    plt.figure(figsize=(10, 6))
    ax = sns.scatterplot(data=df_cq, x='Quarter sent', y='TotalAssets', size='ReliefRate', hue='Company', sizes=(20, 200), alpha=0.7, legend=False)
    plt.title('Company-Quarter: Log Real Total Assets vs Relief Rate (size)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'company_quartely_assets_relief_rate.png'))

    # P2 - Quarterly-Company level plot, x: Quarter sent, y: Total assets, size: relief rate, color: company type
    plt.figure(figsize=(10, 6))
    subset = df_cq[df_cq['Company type'].isin(['bank', 'credit union', 'bank holding company'])]
    ax = sns.scatterplot(data=subset, x='Quarter sent', y='TotalAssets', size='ReliefRate', hue='Company type', sizes=(20, 200), alpha=0.7, legend=False)
    plt.title('Company-Quarter: Log Real Total Assets vs Relief Rate (size)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'company_quartely_assets_relief_rate_company_type.png'))

    # P3 - Company-Quarter level, x: Total Assets, y1: Relief Rate, color: Quarter Sent
    fig, axes = plt.subplots(3, 1, figsize=(20, 14), sharex=True)
    for i, company_type in enumerate(['bank', 'credit union', 'bank holding company']):
        subset = df_cq[df_cq['Company type']==company_type]
        subset['QuarterNumeric'] = subset['Quarter sent'].map(lambda x: x.to_period('Q').ordinal)
        sns.scatterplot(data=subset, x='TotalAssets', y='ReliefRate', hue='QuarterNumeric', palette='Blues', legend=False, ax = axes[i], alpha=0.6)
        axes[i].set_ylabel('Relief probability')
        axes[i].set_xlabel('Logarithm of total assets (in 2013 dollars)')
        axes[i].set_title(f'{company_type} - Relief Probability vs Log Total Assets')
    save_plot(fig, f'per_size_quarterly_company_level')

    # P4 - Quarterly-Company type level plot, x: Quarter sent, y1: Total assets, y2: relief rate, color: company type
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    colors = {'bank': 'blue', 'credit union': 'orange', 'bank holding company': 'green'}
    for company_type in ['bank', 'credit union', 'bank holding company']:
        subset = df_q[df_q['Company type']==company_type]
        ax1.plot(subset['Quarter sent'], subset['TotalAssets'], color=colors[company_type], linestyle='--', label=f'{company_type} - Mean Log Total Assets')
        ax2.plot(subset['Quarter sent'], subset['ReliefRate'], color=colors[company_type], linestyle='-', marker='o', label=f'{company_type} - Mean Relief Rate')

    ax1.set_ylabel('Mean Log Total Assets', color='blue')
    ax2.set_ylabel('Mean Relief Rate', color='red')

    company_types = list(colors.keys())
    color_handles = [Line2D([0], [0], color=colors[ctype], lw=2) for ctype in company_types]

    style_handles = [Line2D([0], [0], color='black', lw=2, linestyle='--', label='Total Assets'),
                    Line2D([0], [0], color='black', lw=2, linestyle='-', marker='o', label='Relief Rate')]

    all_handles = color_handles + style_handles
    all_labels = company_types + ['Total Assets (--)', 'Relief Rate (-, o)']
    ax1.legend(all_handles, all_labels, title='Legend', loc='upper left')

    plt.title('Quarterly Trend by Company Type: Log Real Total Assets & Relief Rate')
    plt.xticks(rotation=90)
    save_plot(fig, 'quarterly_assets_relief_rate.png')

    # P5 - P1 zombie data complaints vs other complaints
    zombie_title = {0: 'other complaints', 1: 'zombie data complaints'}
    fig, axs = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

    for i in range(2):
        df_z = df_cq_z[df_cq_z['Zombie data'] == i]
        sns.scatterplot(data=df_z, x='Quarter sent', y='TotalAssets', size='ReliefRate', hue='Company', sizes=(20, 200), alpha=0.7, ax=axs[i], legend=False)
        axs[i].set_title(f'Company-Quarter ({zombie_title[i]})')
        axs[i].tick_params(axis='x', rotation=90)
    plt.suptitle('Company-Quarter Scatter: zombie data complaints vs. others', fontsize=16)
    save_plot(fig, 'company_quartely_assets_relief_rate_zombie.png')

    fig, axs = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

    # P6 - P2 zombie data complaints vs other complaints
    for i in range(2):
        df_z_q = df_cq_z[(df_cq_z['Zombie data'] == i) & (df_cq_z['Company type'].isin(['bank', 'credit union', 'bank holding company']))]
        sns.scatterplot(data=df_z_q, x='Quarter sent', y='TotalAssets', size='ReliefRate', hue= 'Company type', sizes=(20, 200), alpha=0.7,ax=axs[i])
        axs[i].set_title(f'Quarterly ({zombie_title[i]})')
        axs[i].tick_params(axis='x', rotation=90)

    plt.suptitle('Quarterly Scatter: zombie data complaints vs. others', fontsize=16)
    save_plot(fig, 'company_quartely_assets_relief_rate_company_type_zombie.png')

    # P7 - P3 zombie data complaints vs other complaints
    fig, axes = plt.subplots(3, 2, figsize=(20, 14), sharex=True)
    for i, company_type in enumerate(['bank', 'credit union', 'bank holding company']):
        for j in range (2):
            subset = df_cq_z[(df_cq_z['Company type']==company_type) & df_cq_z['Zombie data']==j]
            subset['QuarterNumeric'] = subset['Quarter sent'].map(lambda x: x.to_period('Q').ordinal)
            sns.scatterplot(data=subset, x='TotalAssets', y='ReliefRate', hue='QuarterNumeric', palette='Blues', legend=False, ax = axes[i, j], alpha=0.6)
            axes[i, j].set_ylabel('Relief probability')
            axes[i, j].set_xlabel('Logarithm of total assets (in 2013 dollars)')
            axes[i, j].set_title(f'{company_type}| {zombie_title[j]}| Relief Probability vs Log Total Assets')
    save_plot(fig, f'per_size_quarterly_company_level_zombie.png')

    # P8 - P4 zombie data complaints vs. other complaints
    fig, axes = plt.subplots(1, 2, figsize=(20, 8), sharey=True)
    ax2 = [axes[0].twinx(), axes[1].twinx()]

    for i in range(2):
        for company_type in ['bank', 'credit union', 'bank holding company']:
            subset = df_q_z[(df_q_z['Zombie data'] == i) & (df_q_z['Company type']==company_type)]
            axes[i].plot(subset['Quarter sent'], subset['TotalAssets'], color=colors[company_type], linestyle='--', label=f'{company_type} Log Total Assets')
            ax2[i].plot(subset['Quarter sent'], subset['ReliefRate'], color=colors[company_type], linestyle='-', marker='o', label=f'{company_type} Relief Rate')
    
        axes[i].set_ylabel('Mean Log Total Assets (in 2013 dollars)')
        ax2[i].set_ylabel('Mean Relief Rate')

        axes[i].set_xlabel('Quarter sent')
        axes[i].tick_params(axis='x', rotation=90)
        axes[i].set_title(f'Relief & Assets ({zombie_title[i]})')

    plt.suptitle('Quarterly Trends by Zombie Data Group')

    color_lines = [mlines.Line2D([], [], color=col, label=ctype) for ctype, col in colors.items()]

    style_lines = [mlines.Line2D([], [], color='black', linestyle='--', label='Total Assets'),
                mlines.Line2D([], [], color='black', linestyle='-', marker='o', label='Relief Rate')]

    legend1 = fig.legend(handles=color_lines, loc='upper center', ncol=3, title='Company Type')
    legend2 = fig.legend(handles=style_lines, loc='upper right', title='Line Type')

    plt.tight_layout(rect=[0, 0, 1, 0.9])
    save_plot(fig, f'quarterly_assets_relief_rate_zombie.png')

    # P9 - P8 in yearly level
    df_y_z = df.groupby(['Year sent', 'Company type', 'Zombie data']).agg(TotalAssets=('Log real total assets', 'mean'), ReliefRate=('Is relief', 'mean')).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(20, 8), sharey=True)
    ax2 = [axes[0].twinx(), axes[1].twinx()]

    for i in range(2):
        for company_type in ['bank', 'credit union', 'bank holding company']:
            subset = df_y_z[(df_y_z['Zombie data'] == i) & (df_y_z['Company type']==company_type)]
            axes[i].plot(subset['Year sent'], subset['TotalAssets'], color=colors[company_type], linestyle='--', label=f'{company_type} Log Total Assets')
            ax2[i].plot(subset['Year sent'], subset['ReliefRate'], color=colors[company_type], linestyle='-', marker='o', label=f'{company_type} Relief Rate')
    
        axes[i].set_ylabel('Mean Log Total Assets (in 2013 dollars)')
        ax2[i].set_ylabel('Mean Relief Rate')

        axes[i].set_xlabel('Year sent')
        axes[i].tick_params(axis='x', rotation=90)
        axes[i].set_title(f'Relief & Assets ({zombie_title[i]})')

    plt.suptitle('Yearly Trends by Zombie Data Group')

    color_lines = [mlines.Line2D([], [], color=col, label=ctype) for ctype, col in colors.items()]

    style_lines = [mlines.Line2D([], [], color='black', linestyle='--', label='Total Assets'),
                mlines.Line2D([], [], color='black', linestyle='-', marker='o', label='Relief Rate')]

    legend1 = fig.legend(handles=color_lines, loc='upper center', ncol=3, title='Company Type')
    legend2 = fig.legend(handles=style_lines, loc='upper right', title='Line Type')

    plt.tight_layout(rect=[0, 0, 1, 0.9])
    save_plot(fig, f'yearly_assets_relief_rate_zombie.png')

def time_trend_in_relief_per_asset_quantile():
    # quarterly trend in relief rate by total assets quantile 
    tmp_bank = df[df['Company type'].isin(['bank', 'bank holding company'])].copy()
    bank_assets = (tmp_bank.groupby(['Quarter sent', 'Company'])['Log total assets'].mean().reset_index())
    bank_assets['AssetsQuantile'] = bank_assets.groupby('Quarter sent')['Log total assets'].transform(lambda x: pd.qcut(x, 5, labels=False, duplicates='drop') + 1)
    tmp_bank = tmp_bank.merge(bank_assets[['Quarter sent', 'Company', 'AssetsQuantile']], on=['Quarter sent', 'Company'], how='left')
    print(pd.crosstab(bank_assets['Quarter sent'], bank_assets['AssetsQuantile']))

    tmp_cu = df[df['Company type']=='credit union'].copy()
    cu_assets = (tmp_cu.groupby(['Quarter sent', 'Company'])['Log total assets'].mean().reset_index())
    cu_assets['AssetsQuantile'] = cu_assets.groupby('Quarter sent')['Log total assets'].transform(lambda x: pd.qcut(x, 5, labels=False, duplicates='drop') + 1)
    tmp_cu = tmp_cu.merge(cu_assets[['Quarter sent', 'Company', 'AssetsQuantile']], on=['Quarter sent', 'Company'], how='left')
    print(pd.crosstab(cu_assets['Quarter sent'], cu_assets['AssetsQuantile']))
    
    tmp = pd.concat([tmp_bank, tmp_cu], axis=0)
    tmp['AssetsQuantile'] = tmp['AssetsQuantile'].astype('Int64')
    tmp['Quarter sent'] = pd.PeriodIndex(tmp['Quarter sent'], freq='Q').to_timestamp()
    counts = tmp.groupby(['Quarter sent', 'AssetsQuantile']).size().reset_index(name='ComplaintCount')
    counts['LogComplaintCount'] = np.log1p(counts['ComplaintCount'])
    relief = tmp.groupby(['Quarter sent', 'AssetsQuantile'])['Is relief'].mean().reset_index(name='ReliefRate')

    palette = sns.color_palette("viridis", 5)
    plt.figure(figsize=(14, 6))
    for quantile in sorted(relief['AssetsQuantile'].unique()):
        subset = relief[relief['AssetsQuantile'] == quantile]
        plt.plot(subset['Quarter sent'], subset['ReliefRate'], label=f'Q{quantile}', color=palette[quantile - 1])

    plt.title('Relief Rate Trend by Total Assets Quantile (5-Quantile)')
    plt.xlabel('Quarter Sent')
    plt.ylabel('Mean Relief Rate')
    plt.xticks(rotation=90)
    plt.legend(title='Total Assets Quantile', loc='upper right')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(os.path.join(cPATH, 'temp', 'time_trend_relief_per_asset_quantiles.png'))

    # heatmap complaint counts & relief rate
    pivot_count = counts.pivot(index='AssetsQuantile', columns='Quarter sent', values='LogComplaintCount')
    pivot_relief = relief.pivot(index='AssetsQuantile', columns='Quarter sent', values='ReliefRate')

    fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

    sns.heatmap(pivot_count, cmap='Oranges', annot=False, cbar_kws={'label': 'Number of Complaints'}, linewidths=0.5, linecolor='gray', ax=axes[0])
    axes[0].set_title('Complaint Count Heatmap by Quarter and Total Assets Quantile')
    axes[0].set_ylabel('Total Assets Quantile')
    axes[0].invert_yaxis()

    sns.heatmap(pivot_relief, cmap='YlGnBu', annot=False, cbar_kws={'label': 'Mean Relief Rate'}, linewidths=0.5, linecolor='gray', vmin=0, vmax=1, ax=axes[1])
    axes[1].set_title('Relief Rate Heatmap by Quarter and Total Assets Quantile')
    axes[1].set_xlabel('Quarter Sent')
    axes[1].set_ylabel('Total Assets Quantile')
    axes[1].invert_yaxis()

    period_labels = pd.PeriodIndex(pivot_relief.columns, freq='Q').strftime('%YQ%q')
    axes[1].set_xticks(range(len(period_labels)))
    axes[1].set_xticklabels(period_labels, rotation=90)
    save_plot(fig, 'time_heatmap_relief_per_asset_quantiles.png')

    # quarterly trend in relief rate by total assets quantile | zombie vs. other complaints
    grouped = tmp.groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')

    palette = sns.color_palette("viridis", 5)
    fig, axes = plt.subplots(1, 2, figsize=(18, 6), sharey=True)

    zombie_title = {0: 'Other Complaints', 1: 'Zombie Data Complaints'}

    for i in range(2):
        for quantile in sorted(grouped['AssetsQuantile'].unique()):
            subset = grouped[(grouped['Zombie data'] == i) & (grouped['AssetsQuantile'] == quantile)]
            axes[i].plot(subset['Quarter sent'], subset['ReliefRate'],label=f'Q{quantile}', color=palette[quantile - 1])
        axes[i].set_title(zombie_title[i])
        axes[i].set_xlabel('Quarter Sent')
        axes[i].tick_params(axis='x', rotation=90)
        axes[i].set_ylabel('Mean Relief Rate')
        axes[i].legend(title='Total Assets Quantile', loc='upper right')

    plt.suptitle('Relief Rate Trend by Total Assets Quantile (Zombie vs. Other)', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(os.path.join(cPATH, 'temp', 'time_trend_relief_per_asset_quantiles_zombie.png'))

    # heatmap of quarterly trend in relief rate by total assets quantile | zombie vs. other complaints
    counts = tmp.groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data']).size().reset_index(name='ComplaintCount')
    counts['LogComplaintCount'] = np.log1p(counts['ComplaintCount'])
    relief = tmp.groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')

    vmin = 0.01
    vmax = counts['LogComplaintCount'].max()
    fig, axes = plt.subplots(2, 2, figsize=(18, 12), sharey=True)
    
    for i in range(2):
        pivot_count = counts[counts['Zombie data'] == i].pivot(index='AssetsQuantile', columns='Quarter sent', values='LogComplaintCount')
        pivot_relief = relief[relief['Zombie data'] == i].pivot(index='AssetsQuantile', columns='Quarter sent', values='ReliefRate')

        sns.heatmap(pivot_count, cmap='Oranges', annot=False, cbar_kws={'label': 'Number of Complaints'}, linewidths=0.5, linecolor='gray', vmin=vmin, vmax=vmax, ax=axes[0, i])
        axes[0, i].set_title(f'Complaint Count Heatmap by Quarter and Total Assets Quantile | {zombie_title[i]}')
        axes[0, i].set_ylabel('Total Assets Quantile')
        axes[0, i].invert_yaxis()

        sns.heatmap(pivot_relief, cmap='YlGnBu', annot=False, cbar_kws={'label': 'Mean Relief Rate'}, linewidths=0.5, linecolor='gray', vmin=0, vmax=1, ax=axes[1, i])
        axes[1, i].set_title(f'Relief Rate Heatmap by Quarter and Total Assets Quantile | {zombie_title[i]}')
        axes[1, i].set_xlabel('Quarter Sent')
        axes[1, i].set_ylabel('Total Assets Quantile')
        axes[1, i].invert_yaxis()

        period_labels = pd.PeriodIndex(pivot_relief.columns, freq='Q').strftime('%YQ%q')
        axes[0, i].set_xticks(range(len(period_labels)))
        axes[0, i].set_xticklabels(period_labels, rotation=90)
        axes[1, i].set_xticks(range(len(period_labels)))
        axes[1, i].set_xticklabels(period_labels, rotation=90)
    save_plot(fig, 'time_heatmap_relief_per_asset_quantiles_zombie.png')

    # heatmap of quarterly trend in relief rate by total assets quantile | zombie vs. other complaints - each company type separately
    counts_bank = tmp[tmp['Company type'].isin(['bank', 'bank holding company'])].groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data']).size().reset_index(name='ComplaintCount')
    counts_cu = tmp[tmp['Company type']=='credit union'].groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data']).size().reset_index(name='ComplaintCount')
    relief_bank = tmp[tmp['Company type'].isin(['bank', 'bank holding company'])].groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')
    relief_cu = tmp[tmp['Company type']=='credit union'].groupby(['Quarter sent', 'AssetsQuantile', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')

    for counts, relief, title in [(counts_bank, relief_bank, 'bank & bank holding company'), (counts_cu, relief_cu, 'credit union')]:
        counts['LogComplaintCount'] = np.log1p(counts['ComplaintCount'])

        vmin = 0.01
        vmax = counts['LogComplaintCount'].max()
        fig, axes = plt.subplots(2, 2, figsize=(18, 12), sharey=True)
        
        for i in range(2):
            pivot_count = counts[counts['Zombie data'] == i].pivot(index='AssetsQuantile', columns='Quarter sent', values='LogComplaintCount')
            pivot_relief = relief[relief['Zombie data'] == i].pivot(index='AssetsQuantile', columns='Quarter sent', values='ReliefRate')

            sns.heatmap(pivot_count, cmap='Oranges', annot=False, cbar_kws={'label': 'Number of Complaints'}, linewidths=0.5, linecolor='gray', vmin=vmin, vmax=vmax, ax=axes[0, i])
            axes[0, i].set_title(f'Complaint Count Heatmap by Quarter and Total Assets Quantile - {title} | {zombie_title[i]}')
            axes[0, i].set_ylabel('Total Assets Quantile')
            axes[0, i].invert_yaxis()

            sns.heatmap(pivot_relief, cmap='YlGnBu', annot=False, cbar_kws={'label': 'Mean Relief Rate'}, linewidths=0.5, linecolor='gray', vmin=0, vmax=1, ax=axes[1, i])
            axes[1, i].set_title(f'Relief Rate Heatmap by Quarter and Total Assets Quantile - {title} | {zombie_title[i]}')
            axes[1, i].set_xlabel('Quarter Sent')
            axes[1, i].set_ylabel('Total Assets Quantile')
            axes[1, i].invert_yaxis()

            period_labels = pd.PeriodIndex(pivot_relief.columns, freq='Q').strftime('%YQ%q')
            axes[0, i].set_xticks(range(len(period_labels)))
            axes[0, i].set_xticklabels(period_labels, rotation=90)
            axes[1, i].set_xticks(range(len(period_labels)))
            axes[1, i].set_xticklabels(period_labels, rotation=90)
        save_plot(fig, f'time_heatmap_relief_per_asset_quantiles_zombie_{title}.png')

def get_color_map(data, var, palette_type='colorblind'):
    palette = sns.color_palette(palette_type, n_colors=len(data[var].unique()))
    var_order = data[var].unique()
    color_map = dict(zip(var_order, palette))
    color_handles = [Line2D([0], [0], color=color_map[v], lw=2) for v in var_order]
    return color_map, color_handles, var_order

def draw_policy_line(ax, grouped, states, extended=False):
    for state in states:
        if state == 'CA' and extended:
            for label, q in CCPA_quarters.items(): # draw vertical lines at the time of policy event
                try:
                    q_date = pd.Period(q, freq='Q').to_timestamp()
                    if q_date in grouped['Quarter sent'].unique():
                        ax.axvline(x=q_date - pd.Timedelta(days=60), color='grey', linestyle='--', linewidth=1)
                        ax.text(q_date, ax.get_ylim()[1]*0.5, label, color='grey', ha='center', rotation=90, fontsize=10)
                except ValueError:
                    continue  # skip if the time of event is out of time range shown in the plot
        elif state in df['State'].unique():
            policy_date = df[df['State'] == state]['State privacy law'].dropna().unique() # plot policy line of state has implemented state privacy protection policy
            if len(policy_date) > 0:
                try:
                    policy_quarter = pd.to_datetime(policy_date[0])
                    if policy_quarter in grouped['Quarter sent'].unique():
                        ax.axvline(x=policy_quarter + pd.Timedelta(days=60), color='grey', linestyle='--', linewidth=1)
                        ax.text(policy_quarter, ax.get_ylim()[1] * 0.5, f"{state} policy\nimplementation", color='grey', ha='center', rotation=90, fontsize=10)
                except ValueError:
                    pass

def get_nrow_ncol(n_panels):
    nrows = int(np.floor(np.sqrt(n_panels)))
    ncols = int(np.ceil(n_panels / nrows))
    return nrows, ncols

def get_asset_quantiles(data, bins=5, by_company_type=True):
    if by_company_type:
        tmp_bank = data[data['Company type'].isin(['bank', 'bank holding company'])].copy()
        bank_assets = (tmp_bank.groupby(['Quarter sent', 'Company'])['Log total assets'].mean().reset_index())
        bank_assets['AssetsQuantile'] = bank_assets.groupby('Quarter sent')['Log total assets'].transform(lambda x: pd.qcut(x, bins, labels=False, duplicates='drop') + 1)
        tmp_bank = tmp_bank.merge(bank_assets[['Quarter sent', 'Company', 'AssetsQuantile']], on=['Quarter sent', 'Company'], how='left')
        print(pd.crosstab(bank_assets['Quarter sent'], bank_assets['AssetsQuantile']))

        tmp_cu = data[data['Company type']=='credit union'].copy()
        cu_assets = (tmp_cu.groupby(['Quarter sent', 'Company'])['Log total assets'].mean().reset_index())
        cu_assets['AssetsQuantile'] = cu_assets.groupby('Quarter sent')['Log total assets'].transform(lambda x: pd.qcut(x, bins, labels=False, duplicates='drop') + 1)
        tmp_cu = tmp_cu.merge(cu_assets[['Quarter sent', 'Company', 'AssetsQuantile']], on=['Quarter sent', 'Company'], how='left')
        print(pd.crosstab(cu_assets['Quarter sent'], cu_assets['AssetsQuantile']))
        
        tmp = pd.concat([tmp_bank, tmp_cu], axis=0)
        tmp['AssetsQuantile'] = tmp['AssetsQuantile'].astype('Int64')
    else:
        tmp = data.copy()
        assets = (tmp.groupby(['Quarter sent', 'Company'])['Log total assets'].mean().reset_index())
        assets['AssetsQuantile'] = assets.groupby('Quarter sent')['Log total assets'].transform(lambda x: pd.qcut(x, bins, labels=False, duplicates='drop') + 1)
        tmp = tmp.merge(assets[['Quarter sent', 'Company', 'AssetsQuantile']], on=['Quarter sent', 'Company'], how='left')
        print(pd.crosstab(assets['Quarter sent'], assets['AssetsQuantile']))

    return tmp

def set_quarter_xticks(ax, tick_interval=1):
    def quarter_fmt(x, pos=None):
        date = mdates.num2date(x)
        quarter = (date.month - 1) // 3 + 1
        return f"{date.year}-Q{quarter}"
    
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10], interval=tick_interval))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(quarter_fmt))
    ax.tick_params(axis='x', rotation=90)

def time_trend_in_relief_rate(): 
    # (1) line plot of quarterly trend in relief rate: quarterly-zombie level 
    relief = df.groupby(['Quarter sent', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')
    count = df.groupby(['Quarter sent', 'Zombie data']).size().reset_index(name='ComplaintCount')

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharex=True)
    sns.lineplot(data=relief, x='Quarter sent', y='ReliefRate', style='Zombie data', dashes={0: '', 1: (2, 2)}, ax=axes[0])
    axes[0].set_title('Relief Rate Trend')
    axes[0].set_ylabel('Relief Rate')
    axes[0].set_xlabel('Quarter Sent')
    set_quarter_xticks(axes[0])

    sns.lineplot(data=count, x='Quarter sent', y='ComplaintCount', style='Zombie data', dashes={0: '', 1: (2, 2)}, ax=axes[1])
    axes[1].set_title('Complaint Volume Trend')
    axes[1].set_ylabel('Complaint Count (Log Scale)')
    axes[1].set_xlabel('Quarter Sent')
    axes[1].set_yscale('log')
    set_quarter_xticks(axes[1])

    style_handles = [Line2D([0], [0], color='black', linestyle='-', lw=2, label='Other Complaints'),
                    Line2D([0], [0], color='black', linestyle='--', lw=2, label='Zombie Data Complaints')]
    axes[1].legend(handles=style_handles, title='Complaint Type', loc='upper left', bbox_to_anchor=(1, 1))
    axes[0].legend([], [], frameon=False) 
    save_plot(fig, 'quarterly_trend_relief_rate.png')

    # (2) line plot of quarterly trend in relief rate: quarterly-zombie-company type level - to observe company type-level heterogeneity 
    relief = df.groupby(['Quarter sent', 'Zombie data', 'Company type'])['Is relief'].mean().reset_index(name='ReliefRate')
    tmp = df[df['Company type']!='others'].copy()
    tmp.loc[tmp['Company type'].isin(['bank', 'bank holding company']), 'Company type'] = 'bank / bank holding company'

    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    for i, company in enumerate(tmp['Company type'].unique()):
        col, row = divmod(i, 2)
        ax = axes[row][col]
        relief = tmp[tmp['Company type'] == company].groupby(['Quarter sent', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')
        sns.lineplot(data=relief, x='Quarter sent', y='ReliefRate', style='Zombie data',dashes={0: '', 1: (2, 2)}, ax=ax)
        ax.set_title(company)
        ax.set_xlabel('Quarter Sent')
        ax.set_ylabel('Relief Rate')
        set_quarter_xticks(ax)

    style_handles = [Line2D([0], [0], color='black', linestyle='-', lw=2, label='Other Complaints'),
                    Line2D([0], [0], color='black', linestyle='--', lw=2, label='Zombie Data Complaints')]
    ax.legend(handles=style_handles, title='Complaint Type', loc='upper left', bbox_to_anchor=(1, 1))
    save_plot(fig, 'quarterly_trend_relief_rate_company_type.png')

    # (3) line plot of quarterly trend in relief rate: CA vs other states (Zombie vs Non-Zombie)
    plt.figure(figsize=(12, 7))
    tmp = df.copy()
    tmp['Is CA'] = (tmp['State']=='CA') # indicator of CA state (vs. others)

    relief = tmp.groupby(['Quarter sent', 'Zombie data', 'Is CA'])['Is relief'].mean().reset_index(name='ReliefRate')
    color_map, color_handles, color_labels = get_color_map(relief, 'Is CA')
    ax = sns.lineplot(data=relief, x='Quarter sent', y='ReliefRate', hue='Is CA', style='Zombie data', palette=color_map, dashes={0: '', 1: (2, 2)}) 
    draw_policy_line(ax, relief, ['CA'])

    set_quarter_xticks(ax)
    color_labels = ['CA' if v else 'Other States' for v in color_labels] # change names for color legend for better interpretability
    style_handles = [Line2D([0], [0], color='black', linestyle='-', lw=2, label='Other Complaints'),
                    Line2D([0], [0], color='black', linestyle='--', lw=2, label='Zombie Data Complaints')]

    legend1 = ax.legend(handles=color_handles, labels=color_labels, title='States', loc='upper left')
    ax.add_artist(legend1)
    legend2 = ax.legend(handles=style_handles, title='Complaint Type', loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'quarterly_trend_relief_rate_CA.png'))

    # heterogeneous company type
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    tmp.loc[tmp['Company type'].isin(['bank', 'bank holding company']), 'Company type'] = 'bank / bank holding company'
    tmp = tmp[tmp['Company type']!='others'].copy()

    color_map, color_handles, color_labels = get_color_map(relief, 'Is CA')
    color_labels = ['CA' if v else 'Other States' for v in color_labels] 

    for i, company in enumerate(tmp['Company type'].unique()):
        col, row = divmod(i, 2)
        ax = axes[row][col]
        relief = tmp[tmp['Company type'] == company].groupby(['Quarter sent', 'Zombie data', 'Is CA'])['Is relief'].mean().reset_index(name='ReliefRate')
        sns.lineplot(data=relief, x='Quarter sent', y='ReliefRate', hue='Is CA', style='Zombie data', palette=color_map, dashes={0: '', 1: (2, 2)}, ax=ax)
        draw_policy_line(ax, relief, ['CA'])
        ax.set_title(company)
        ax.set_xlabel('Quarter Sent')
        ax.set_ylabel('Relief Rate')
        set_quarter_xticks(ax)

    style_handles = [Line2D([0], [0], color='black', linestyle='-', lw=2, label='Other Complaints'),
                    Line2D([0], [0], color='black', linestyle='--', lw=2, label='Zombie Data Complaints')]

    legend1 = axes[0][2].legend(handles=color_handles, labels=color_labels, title='States', loc='upper left')
    axes[0][2].add_artist(legend1)
    legend2 = axes[0][2].legend(handles=style_handles, title='Complaint Type', loc='upper left', bbox_to_anchor=(1, 1))
    save_plot(fig,'quarterly_trend_relief_rate_CA_company_type.png')

    # (4) line plot of quarterly trend in relief rate (Zombie vs Non-Zombie) in top 5 complaint counts states
    top_states = df['State'].value_counts().head(6).index.tolist()
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))

    for i, state in enumerate(top_states):
        col, row = divmod(i, 2)
        ax = axes[row][col]
        relief = df[df['State'] == state].groupby(['Quarter sent', 'Zombie data'])['Is relief'].mean().reset_index(name='ReliefRate')
        sns.lineplot(data=relief, x='Quarter sent', y='ReliefRate', style='Zombie data', dashes={0: '', 1: (2, 2)}, ax=ax)
        ax.set_title(f'State: {state}')
        ax.set_xlabel('Quarter Sent')
        ax.set_ylabel('Relief Rate')
        set_quarter_xticks(ax)
        draw_policy_line(ax, relief, [state])

    style_handles = [Line2D([0], [0], color='black', linestyle='-', lw=2, label='Other Complaints'),
                    Line2D([0], [0], color='black', linestyle='--', lw=2, label='Zombie Data Complaints')]
    legend2 = ax.legend(handles=style_handles, title='Complaint Type', loc='upper left', bbox_to_anchor=(1, 1))
    save_plot(fig, 'quarterly_trend_relief_rate_top_states.png')

def plot_DV_per_size(DV_agg, data, titles, savepath): # DV_agg should be a list of tuple consisting of (DV var, aggregation method) - e,g,.[('Company', 'count'), ('Is relief', 'sum')]
    ### Company - quarter level scatter plot with x: size of financial institutes
    print(f"scatter plot of DV - size for {len(DV_agg)} DVs: {DV_agg}")
    agg_dict = {}
    agg_dict = {f"{dv}_{method}": (dv, method) for dv, method in DV_agg}
    agg_dict.update({'total_assets': ('Real total assets', 'mean')})
    title = '_'.join([dv_agg[0] for dv_agg in DV_agg]).replace(' ', '_')

    for company_type in data['Company type'].unique():
        subset = data[data['Company type']==company_type]
        grouped = subset.groupby(['Company', 'Quarter sent']).agg(**agg_dict).reset_index()

        ## x: total assets, y: DVs, color: company (to approximately observe company effect)
        fig, axes = plt.subplots(len(DV_agg), 1, figsize=(10, 2 + 4*len(DV_agg)), sharex=True)
        axes = np.atleast_1d(axes)

        for i, (dv, method) in enumerate(DV_agg):
            sns.scatterplot(data=grouped, x='total_assets', y=f'{dv}_{method}', hue='Company', palette='colorblind', legend=False, ax=axes[i], alpha=0.6)
            axes[i].set_ylabel(f'{titles[i]} per quarter-company')
            axes[i].set_title(f'{company_type} - {titles[i]} vs Log Total Assets')
            axes[i].set_xscale('log')
            #axes[i].set_yscale('symlog', linthresh=1e-4)

        axes[len(DV_agg)-1].set_xlabel('Logarithm of total assets (in 2013 dollars)')
        save_plot(fig, f'{title}_per_size_company_quarterly_level_{company_type}.png', savepath)

    ### Company level scatter plot 
    fig, axes = plt.subplots(len(DV_agg), 1, figsize=(10, 2 + 4*len(DV_agg)), sharex=True)
    axes = np.atleast_1d(axes)
    color_map, color_handles, var_sorted = get_color_map(data, 'Company type', palette_type='colorblind')

    for company_type in data['Company type'].unique():
        subset = data[data['Company type']==company_type]
        grouped = subset.groupby(['Company', 'Company type']).agg(**agg_dict).reset_index()
        for i, (dv, method) in enumerate(DV_agg):
            sns.scatterplot(data=grouped, x='total_assets', y=f'{dv}_{method}', hue='Company type', palette=color_map, legend=True, ax=axes[i], alpha=0.6)
            axes[i].set_ylabel(f'{titles[i]}')
            axes[i].set_title(f'{titles[i]} vs Log Mean Total Assets (in 2013 Dollars)')
            axes[i].set_xscale('log')
            #axes[i].set_yscale('symlog', linthresh=1e-4)
    save_plot(fig, f'{title}_per_size_company_level.png', savepath) 

def time_heatmap_DV_per_asset_quantile(DV_agg, data, titles, savepath):
    agg_dict = {}
    agg_dict = {f"{dv}_{method}": (dv, method) for dv, method in DV_agg}
    agg_dict.update({'total_assets': ('Real total assets', 'mean')})
    title = '_'.join([dv_agg[0] for dv_agg in DV_agg]).replace(' ', '_')

    ### heatmap of DVs by total assets quantile 
    grouped = data.groupby(['AssetsQuantile', 'Quarter sent']).agg(**agg_dict).reset_index()

    palette = sns.color_palette("viridis", data['AssetsQuantile'].nunique())
    fig, axes = plt.subplots(len(DV_agg), 1, figsize=(10, 2 + 4*len(DV_agg)), sharex=True)
    axes = np.atleast_1d(axes)
    for i, (dv, method) in enumerate(DV_agg):
        pivot= grouped.pivot(index='AssetsQuantile', columns='Quarter sent', values=f'{dv}_{method}')
        sns.heatmap(pivot, cmap='YlGnBu', annot=False, cbar_kws={'label': titles[i]}, linewidths=0.5, linecolor='gray', ax=axes[i])
        axes[i].set_ylabel('Financial Institution Size Quantile')
        axes[i].set_title(f'{titles[i]} Heatmap by Quarter and Size Quantile')
        axes[i].invert_yaxis()

    period_labels = pd.PeriodIndex(pivot.columns, freq='Q').strftime('%YQ%q')
    axes[len(DV_agg)-1].set_xlabel('Quarter Sent')
    axes[len(DV_agg)-1].set_xticks(range(len(period_labels)))
    axes[len(DV_agg)-1].set_xticklabels(period_labels, rotation=90)
    save_plot(fig, f'time_heatmap_{title}_per_asset_quantiles.png', savepath)

    # heatmap of quarterly trend in relief rate by total assets quantile - each company type separately
    fig, axes = plt.subplots(len(DV_agg), data['Company type'].nunique(), figsize=(14 + 4*len(DV_agg), 2 + 4*data['Company type'].nunique()), sharex=True)
    axes = np.atleast_2d(axes)
    grouped = data.groupby(['AssetsQuantile', 'Quarter sent', 'Company type']).agg(**agg_dict).reset_index()

    for i, (dv, method) in enumerate(DV_agg):
        for j, company_type in enumerate(grouped['Company type'].unique()):
            pivot= grouped[grouped['Company type']==company_type].pivot(index='AssetsQuantile', columns='Quarter sent', values=f'{dv}_{method}')
            sns.heatmap(pivot, cmap='YlGnBu', annot=False, cbar_kws={'label': titles[i]}, linewidths=0.5, linecolor='gray', ax=axes[i][j])
            axes[i, j].set_ylabel('Financial Institution Size Quantile')
            axes[i, j].set_title(f'{titles[i]} Heatmap by Quarter and Size Quantile ({company_type})')
            axes[i, j].invert_yaxis()
            axes[i, j].set_xticks(range(len(period_labels)))
            axes[i, j].set_xticklabels(period_labels, rotation=90)

    # heatmap of quarterly trend in relief rate by total assets quantile for bank/bhc - each regulatory type separately
    fig, axes = plt.subplots(data['Regulation'].nunique(), len(DV_agg), figsize=(10 + 4*len(DV_agg), 6 + 4*data['Regulation'].nunique()), sharex=True)
    axes = np.atleast_1d(axes).flatten()
    grouped = data[data['Company type']=='bank_bhc'].groupby(['AssetsQuantile', 'Quarter sent', 'Regulation']).agg(**agg_dict).reset_index()

    for i, (dv, method) in enumerate(DV_agg):
        for j, reg in enumerate(grouped['Regulation'].unique()):
            ax = axes[i * grouped['Regulation'].nunique() + j]
            pivot= grouped[grouped['Regulation']==reg].pivot(index='AssetsQuantile', columns='Quarter sent', values=f'{dv}_{method}')
            sns.heatmap(pivot, cmap='YlGnBu', annot=False, cbar_kws={'label': titles[i]}, linewidths=0.5, linecolor='gray', ax=ax)
            ax.set_ylabel('Financial Institution Size Quantile')
            ax.set_title(f'{titles[i]} Heatmap by Quarter and Size Quantile ({reg})')
            ax.invert_yaxis()
            ax.set_xticks(range(len(period_labels)))
            ax.set_xticklabels(period_labels, rotation=90)

    save_plot(fig, f'time_heatmap_{title}_per_asset_quantiles_bank_regulation.png', savepath)

def time_trend_in_DV(DV_agg, data, titles, savepath): 
    if not pd.api.types.is_datetime64_any_dtype(data['Quarter sent']):
        data['Quarter sent'] = data['Quarter sent'].dt.to_timestamp()
    
    agg_dict = {}
    agg_dict = {f"{dv}_{method}": (dv, method) for dv, method in DV_agg}
    agg_dict.update({'total_assets': ('Real total assets', 'mean')})
    title = '_'.join([dv_agg[0] for dv_agg in DV_agg]).replace(' ', '_')

    # (1) line plot of time trend in DV: quarterly-company type level 
    grouped = data.groupby(['Quarter sent', 'Company type']).agg(**agg_dict).reset_index()
    nrows, ncols = get_nrow_ncol(len(DV_agg) * data['Company type'].nunique())
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 + 4*ncols, 2 + 4*nrows), sharex=True)
    axes = np.atleast_1d(axes).flatten()

    for i, (dv, method) in enumerate(DV_agg):
        for j, company_type in enumerate(grouped['Company type'].unique()):
            ax = axes[i * data['Company type'].nunique() + j]
            sns.lineplot(data=grouped[grouped['Company type']==company_type], x='Quarter sent', y=f'{dv}_{method}', ax=ax)
            ax.set_xlabel('Quarter Sent')
            ax.set_ylabel(titles[i])
            ax.set_title(f'{titles[i]} trend ({company_type})')
            set_quarter_xticks(ax)
            #ax.set_yscale('symlog', linthresh=1e-4)

    save_plot(fig, f'quarterly_trend_{title}_company_type.png', savepath)

    # (2) line plot of quarterly trend in DV: CA vs other states
    fig, axes = plt.subplots(len(DV_agg), 1, figsize=(10, 2 + 4*len(DV_agg)), sharex=True)
    axes = np.atleast_1d(axes)

    data['Is CA'] = (data['State']=='CA') # indicator of CA state (vs. others)
    grouped = data.groupby(['Quarter sent', 'Is CA']).agg(**agg_dict).reset_index()
    color_map, color_handles, color_labels = get_color_map(grouped, 'Is CA')

    for i, (dv, method) in enumerate(DV_agg):
        sns.lineplot(data=grouped, x='Quarter sent', y=f'{dv}_{method}', hue='Is CA', palette=color_map, ax=axes[i])
        draw_policy_line(axes[i], grouped, ['CA'])
        set_quarter_xticks(axes[i])
        axes[i].set_xlabel('Quarter Sent')
        axes[i].set_ylabel(titles[i])
        axes[i].set_title(f'{titles[i]} trend - CA vs. other states')
        #axes[i].set_yscale('symlog', linthresh=1e-4)

    color_labels = ['CA' if v else 'Other States' for v in color_labels] # change names for color legend for better interpretability
    axes[len(DV_agg)-1].legend(handles=color_handles, labels=color_labels, title='States', loc='upper left')
    save_plot(fig, f'quarterly_trend_{title}_CA.png', savepath)

    # heterogeneous company type
    grouped = data.groupby(['Quarter sent', 'Company type', 'Is CA']).agg(**agg_dict).reset_index()
    nrows, ncols = get_nrow_ncol(len(DV_agg) * data['Company type'].nunique())
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 + 4*ncols, 2 + 4*nrows), sharex=True)
    axes = np.atleast_1d(axes).flatten()

    for i, (dv, method) in enumerate(DV_agg):
        for j, company_type in enumerate(grouped['Company type'].unique()):
            ax = axes[i * data['Company type'].nunique() + j]
            sns.lineplot(data=grouped[grouped['Company type']==company_type], x='Quarter sent', y=f'{dv}_{method}', hue='Is CA', palette=color_map, ax=ax)
            draw_policy_line(ax, grouped, ['CA'])
            ax.set_xlabel('Quarter Sent')
            ax.set_ylabel(titles[i])
            ax.set_title(f'{titles[i]} trend - CA vs. other states | {company_type}')
            ax.legend(handles=color_handles, labels=color_labels, title='States', loc='upper left')
            set_quarter_xticks(ax)
            #ax.set_yscale('symlog', linthresh=1e-4)

    save_plot(fig, f'quarterly_trend_{title}_CA_company_type.png', savepath)

    # (4) line plot of quarterly trend in relief rate (Zombie vs Non-Zombie) in top 5 complaint counts states
    top_states = data['State'].value_counts().head(5).index.tolist()
    tmp = data[data['State'].isin(top_states)]
    grouped = tmp.groupby(['Quarter sent', 'State']).agg(**agg_dict).reset_index()
    color_map, color_handles, color_labels = get_color_map(grouped, 'State')

    fig, axes = plt.subplots(len(DV_agg), 1, figsize=(10, 2 + 4*len(DV_agg)), sharex=True)
    axes = np.atleast_1d(axes)

    for i, (dv, method) in enumerate(DV_agg):
        sns.lineplot(data=grouped, x='Quarter sent', y=f'{dv}_{method}', hue='State', palette=color_map, ax=axes[i])
        draw_policy_line(axes[i], grouped, top_states)
        axes[i].set_xlabel('Quarter Sent')
        axes[i].set_ylabel(titles[i])
        axes[i].set_title(f'{titles[i]} trend - top complaints states')
        set_quarter_xticks(axes[i])
        #axes[i].set_yscale('symlog', linthresh=1e-4)
    axes[len(DV_agg)-1].legend(handles=color_handles, labels=color_labels.tolist(), title='States', loc='upper left')
    save_plot(fig, f'quarterly_trend_{title}_top_states.png', savepath)

def plot_prop_zombie_per_complaint_counts(data, savepath):
    # scatter plot - x: total complaints y: proportion of zombie complaints
    grouped = data.groupby(['Company', 'Company type']).agg(count=('Zombie data', 'count'), zombie=('Zombie data', 'mean')).reset_index()
    grouped['count'] = np.log1p(grouped['count'])
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.scatterplot(data=grouped, x='count', y='zombie', hue='Company type', palette='colorblind', legend=True, ax=ax, alpha=0.6)
    ax.set_ylabel('Proportion of zombie complaints')
    ax.set_xlabel('Log complaint counts')
    #ax.set_xscale('log')
    ax.set_title(f'Proportion of zombie complaints by total complaint counts')
    save_plot(fig, f'proportion_zombie_per_total_complaint_counts.png', savepath)

    # scatter plot - x: total complaints y: number of zombie complaints
    grouped = data.groupby(['Company', 'Company type']).agg(count=('Zombie data', 'count'), zombie=('Zombie data', 'sum')).reset_index()
    grouped['count'] = np.log1p(grouped['count'])
    grouped['zombie'] = np.log1p(grouped['zombie'])
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.scatterplot(data=grouped, x='count', y='zombie', hue='Company type', palette='colorblind', legend=True, ax=ax, alpha=0.6)
    ax.set_ylabel('Log count of zombie complaints')
    ax.set_xlabel('Log complaint counts')
    #ax.set_yscale('symlog', linthresh=1e-3)
    #ax.set_xscale('symlog', linthresh=1e-3)
    ax.set_title('Proportion of zombie complaints by total complaint counts')
    save_plot(fig, 'zombie_count_per_total_complaint_counts.png', savepath)

    # bar plot - y: proportion of zombie complaints | company type (company-quarterly level)
    grouped = data.groupby(['Company', 'Quarter sent', 'Company type']).agg(zombie=('Zombie data', 'mean')).reset_index()
    type_avg = grouped.groupby('Company type')['zombie'].mean().reset_index()
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    sns.barplot(data=grouped, x='Company type', y='zombie', ax=ax)
    ax.set_ylabel('Proportion of zombie complaint')
    ax.set_xlabel('Company type')
    ax.set_title('Average zombie complaint rate per company type (company-quarter level)')
    save_plot(fig, 'proportion_zombie_company_type_barplot.png', savepath)

def summarize_from_column(df, column, label):
    counts = df[column]
    total_n = len(counts)
    
    summary = {
        'Label': label,
        'Mean': counts.mean(),
        'Median': counts.median(),
        '1st Quartile (Q1)': counts.quantile(0.25),
        '3rd Quartile (Q3)': counts.quantile(0.75),
        'Count == 0': (counts == 0).sum(),
        'Pct == 0': (counts == 0).mean(),
        'Count == 1': (counts == 1).sum(),
        'Pct == 1': (counts == 1).mean(),
        'Count < 5': (counts < 5).sum(),
        'Pct < 5': (counts < 5).mean(),
        'Count < 10': (counts < 10).sum(),
        'Pct < 10': (counts < 10).mean(),
        'N': total_n
    }
    
    return pd.DataFrame([summary])

def regulation_effect_analysis():
    # keep observations according to the inclusion-exclusion criteria
    tmp = df[(df['Company type'].isin(['bank', 'bank holding company', 'credit union']))
            &(df['Quarter sent'] >= pd.Period('2012Q2'))
            &(df['BankCount']<2)
            &(df['Total assets'].notna())].copy()

    # (1) histogram of total counts and zombie counts in company-quarterly level
    total = tmp.groupby(['Quarter sent', 'Company']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'), regulation=('Regulation', 'first'),  zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Quarter sent', 'Company']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Quarter sent', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    sns.histplot(data=data, x='zcount', ax=axes[0], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(True, False))
    sns.histplot(data=data, x='count', ax=axes[1], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(True, False))
    axes[1].set_xlabel('Complaint counts')
    axes[0].set_ylabel('number of company-quarters')
    axes[0].set_title('Distribution zombie complaint counts (company-quarterly level)')
    axes[1].set_title('Distribution all complaint counts (company-quarterly level)')
    save_plot(fig, 'dist_complaint_count_company_quarterly_level.png')

    print("information on distribution of zombie complaint counts (company-quarterly level)")
    summary_z = summarize_from_column(data, 'zcount', 'Zombie Complaints')
    summary_t = summarize_from_column(data, 'count', 'All Complaints')

    summary_df = pd.concat([summary_z, summary_t], ignore_index=True)
    summary_df = summary_df.round(3)
    for col in ['Pct == 0', 'Pct == 1', 'Pct < 5', 'Pct < 10']:
        summary_df[col] = summary_df[col].map(lambda x: f"{x:.1%}")

    print(summary_df.to_string(index=False))

    #(2) x: total assets, y1: proportion of zombie complaints, y2: zombie complaints count, y3: total complaints count, hue: regulation (company-quarterly level)
    #import pdb; pdb.set_trace()
    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    sns.scatterplot(data=data, x='assets', y='zprop', hue='regulation', palette='colorblind', legend=True, ax=axes[0], alpha=0.7)
    sns.scatterplot(data=data, x='assets', y='zcount', hue='regulation', palette='colorblind', legend=True, ax=axes[1], alpha=0.7)
    sns.scatterplot(data=data, x='assets', y='count', hue='regulation', palette='colorblind', legend=True, ax=axes[2], alpha=0.7)
    axes[2].set_xlabel('Total assets')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by total assets (company-quarterly level)')
    axes[1].set_title('Number of zombie complaint by total assets (company-quarterly level)')
    axes[1].set_title('Number of all complaint by total assets (company-quarterly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_xscale('log')
        axes[i].set_ylim(ymin=0)
        axes[i].axvline(x=10_000_000_000, color='gray', linestyle='--', label='10B line')
        axes[i].legend()

    save_plot(fig, 'complaint_count_total_assets_company_quarterly_level.png')

    #(3) histogram of complaint counts (company-yearly level)
    total = tmp.groupby(['Year sent', 'Company']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'), regulation=('Regulation', lambda x: x.mode().iloc[0]), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year sent', 'Company']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year sent', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    sns.histplot(data=data, x='zcount', ax=axes[0], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(True, False))
    sns.histplot(data=data, x='count', ax=axes[1], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(True, False))
    axes[1].set_xlabel('Complaint counts')
    axes[0].set_ylabel('number of company-quarters')
    axes[0].set_title('Distribution zombie complaint counts (company-yearly level)')
    axes[1].set_title('Distribution all complaint counts (company-yearly level)')
    save_plot(fig, 'dist_complaint_count_company_yearly_level.png')

    print("information on distribution of zombie complaint counts (company-yearly level)")
    summary_z = summarize_from_column(data, 'zcount', 'Zombie Complaints')
    summary_t = summarize_from_column(data, 'count', 'All Complaints')

    summary_df = pd.concat([summary_z, summary_t], ignore_index=True)
    summary_df = summary_df.round(3)
    for col in ['Pct == 0', 'Pct == 1', 'Pct < 5', 'Pct < 10']:
        summary_df[col] = summary_df[col].map(lambda x: f"{x:.1%}")

    print(summary_df.to_string(index=False))

    #(4) x: total assets, y1: proportion of zombie complaints, y2: zombie complaints count, y3: total complaints count, hue: regulation (company-yearly level)
    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    sns.scatterplot(data=data, x='assets', y='zprop', hue='regulation', palette='colorblind', legend=True, ax=axes[0], alpha=0.6)
    sns.scatterplot(data=data, x='assets', y='zcount', hue='regulation', palette='colorblind', legend=True, ax=axes[1], alpha=0.6)
    sns.scatterplot(data=data, x='assets', y='count', hue='regulation', palette='colorblind', legend=True, ax=axes[2], alpha=0.6)
    axes[2].set_xlabel('Total assets')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by total assets (company-yearly level)')
    axes[1].set_title('Number of zombie complaint by total assets (company-yearly level)')
    axes[2].set_title('Number of all complaint by total assets (company-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_xscale('log')
        axes[i].set_ylim(ymin=0)
        axes[i].axvline(x=10_000_000_000, color='gray', linestyle='--', label='10B line')
        axes[i].legend()

    save_plot(fig, 'complaint_count_total_assets_company_yearly_level.png')

    #(5) plot (4) separating regulation type Depository and NoRegulation
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    for i, reg in enumerate(['NoRegulation', 'Depository']):
        sns.scatterplot(data=data[data['regulation']==reg], x='assets', y='zprop', legend=True, ax=axes[0,i], alpha=0.6)
        sns.scatterplot(data=data[data['regulation']==reg], x='assets', y='zcount', legend=True, ax=axes[1,i], alpha=0.6)
        sns.scatterplot(data=data[data['regulation']==reg], x='assets', y='count', legend=True, ax=axes[2,i], alpha=0.6)
        
        axes[2,i].set_xlabel('Total assets')
        axes[0,i].set_ylabel('Proportion of zombie complaints')
        axes[1,i].set_ylabel('Zombie complaint count')
        axes[2,i].set_ylabel('Total complaint count')

        axes[0,i].set_title(f'{reg}|Proportion of of zombie complaints by total assets')
        axes[1,i].set_title(f'{reg} | Number of zombie complaint by total assets')
        axes[2,i].set_title(f'{reg} | Number of all complaint by total assets')

        axes[1, i].set_yscale('symlog')
        axes[2, i].set_yscale('symlog')

        for j in range(3):
            axes[j,i].set_xscale('log')
            axes[j,i].set_ylim(ymin=0)

    save_plot(fig, 'complaint_count_total_assets_company_yearly_level_regulation.png')

    #(6) x: total assets, y1: proportion of zombie complaints, y2: zombie complaints count, y3: total complaints count, hue: regulation (company level)
    for year in [2020, 2021, 2022, 2023, 2024]:
        total = tmp[tmp['Year sent']==year].groupby(['Company']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'), regulation=('Regulation', lambda x: x.mode().iloc[0]), zprop=('Zombie data', 'mean')).reset_index()
        zombie = tmp[(tmp['Year sent']==year)&(tmp['Zombie data'] == 1)].groupby(['Company']).agg(zcount=('Total assets', 'size')).reset_index()
        data = pd.merge(total, zombie, on=['Company'], how='left')
        data['zcount'] = data['zcount'].fillna(0).astype(int)

        fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
        sns.scatterplot(data=data, x='assets', y='zprop', hue='regulation', palette='colorblind', legend=True, ax=axes[0], alpha=0.6)
        sns.scatterplot(data=data, x='assets', y='zcount', hue='regulation', palette='colorblind', legend=True, ax=axes[1], alpha=0.6)
        sns.scatterplot(data=data, x='assets', y='count', hue='regulation', palette='colorblind', legend=True, ax=axes[2], alpha=0.6)
        axes[2].set_xlabel('Total assets')

        axes[0].set_ylabel('Proportion of zombie complaints')
        axes[1].set_ylabel('Zombie complaint count')
        axes[2].set_ylabel('Total complaint count')

        axes[0].set_title(f'Proportion of of zombie complaints by total assets (Year {year})')
        axes[1].set_title(f'Number of zombie complaint by total assets (Year {year})')
        axes[2].set_title(f'Number of all complaint by total assets (Year {year})')

        axes[1].set_yscale('symlog')
        axes[2].set_yscale('symlog')

        for i in range(3):
            axes[i].set_xscale('log')
            axes[i].set_ylim(ymin=0)
            axes[i].axvline(x=10_000_000_000, color='gray', linestyle='--', label='10B line')
            axes[i].legend()
        save_plot(fig, f'complaint_count_total_assets_year{year}.png')

    # (7) distrubution of total assets - focusing around 10B
    total = tmp.groupby(['Year sent', 'Company']).agg(assets=('Total assets', 'mean')).reset_index()
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    sns.histplot(data=total, x='assets', binrange=(5_000_000_000, 15_000_000_000), ax=ax, element='bars')
    ax.set_xlabel('Total assets')
    ax.set_ylabel('number of company-quarters')
    ax.set_title('Distribution of total assets (company-yearly level)')
    save_plot(fig, 'dist_total_assets_company_yearly_level.png')

    # (8) scatter plot - focusing around 10B
    total = tmp.groupby(['Year sent', 'Company']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'), regulation=('Regulation', lambda x: x.mode().iloc[0]), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year sent', 'Company']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year sent', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)
    data = data[(data['assets']>5000000000)&(data['assets']<15000000000)] 

    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    sns.scatterplot(data=data, x='assets', y='zprop', hue='regulation', palette='colorblind', legend=True, ax=axes[0], alpha=0.6)
    sns.scatterplot(data=data, x='assets', y='zcount', hue='regulation', palette='colorblind', legend=True, ax=axes[1], alpha=0.6)
    sns.scatterplot(data=data, x='assets', y='count', hue='regulation', palette='colorblind', legend=True, ax=axes[2], alpha=0.6)
    axes[2].set_xlabel('Total assets')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by total assets (company-yearly level)')
    axes[1].set_title('Number of zombie complaint by total assets (company-yearly level)')
    axes[2].set_title('Number of all complaint by total assets (company-yearly level)')

    for i in range(3):
        axes[i].axvline(x=10_000_000_000, color='gray', linestyle='--', label='10B line')
        axes[i].legend()

    save_plot(fig, 'complaint_count_total_assets_around_cutoff.png')

def CFPB_depository_analysis():
    tmp = df[(df['Company type'].isin(['bank', 'bank holding company', 'credit union']))
            &(df['Quarter sent'] >= pd.Period('2012Q2'))
            &(df['BankCount']<2)
            &(df['Total assets'].notna())
            & (df['Regulation']=='Depository')].copy()
    tmp['Is CA'] = (tmp['State']=='CA')

    # (1) histogram of total counts and zombie counts in company-quarterly level
    total = tmp.groupby(['Quarter sent', 'Company']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'),  zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Quarter sent', 'Company']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Quarter sent', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    sns.histplot(data=data, x='zcount', ax=axes[0], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(False, False))
    sns.histplot(data=data, x='count', ax=axes[1], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(True, False))
    axes[1].set_xlabel('Complaint counts')
    axes[0].set_ylabel('number of company-quarters')
    axes[0].set_title('Distribution zombie complaint counts (company-quarterly level)')
    axes[1].set_title('Distribution all complaint counts (company-quarterly level)')
    save_plot(fig, 'depo_dist_complaint_count_company_quarterly_level.png')

    print("information on distribution of zombie complaint counts (company-quarterly level)")
    summary_z = summarize_from_column(data, 'zcount', 'Zombie Complaints')
    summary_t = summarize_from_column(data, 'count', 'All Complaints')

    summary_df = pd.concat([summary_z, summary_t], ignore_index=True)
    summary_df = summary_df.round(3)
    for col in ['Pct == 0', 'Pct == 1', 'Pct < 5', 'Pct < 10']:
        summary_df[col] = summary_df[col].map(lambda x: f"{x:.1%}")

    print(summary_df.to_string(index=False))

    # (2) histogram of total counts and zombie counts in company-yearly level
    total = tmp.groupby(['Year sent', 'Company']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year sent', 'Company']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year sent', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    sns.histplot(data=data, x='zcount', ax=axes[0], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(False, False))
    sns.histplot(data=data, x='count', ax=axes[1], discrete=True, element='bars', color='skyblue', alpha=1, log_scale=(True, False))
    axes[1].set_xlabel('Complaint counts')
    axes[0].set_ylabel('number of company-quarters')
    axes[0].set_title('Distribution zombie complaint counts (company-yearly level)')
    axes[1].set_title('Distribution all complaint counts (company-yearly level)')
    save_plot(fig, 'depo_dist_complaint_count_company_yearly_level.png')

    print("information on distribution of zombie complaint counts (company-yearly level)")
    summary_z = summarize_from_column(data, 'zcount', 'Zombie Complaints')
    summary_t = summarize_from_column(data, 'count', 'All Complaints')

    summary_df = pd.concat([summary_z, summary_t], ignore_index=True)
    summary_df = summary_df.round(3)
    for col in ['Pct == 0', 'Pct == 1', 'Pct < 5', 'Pct < 10']:
        summary_df[col] = summary_df[col].map(lambda x: f"{x:.1%}")

    print(summary_df.to_string(index=False))

    # (3) x: Quarter sent, y: zprop, zcount, count
    total = tmp.groupby(['Quarter sent', 'State']).agg(count=('Total assets', 'size'), zprop=('Zombie data', 'mean'), isca=('Is CA', 'first')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Quarter sent', 'State']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Quarter sent', 'State'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)
    data = data.groupby(['Quarter sent', 'isca']).agg(count=('count', 'mean'), zprop=('zprop', 'mean'), zcount=('zcount', 'mean')).reset_index()
    data['zcount'] = data['zcount'].fillna(0).astype(int)
    if not pd.api.types.is_datetime64_any_dtype(data['Quarter sent']):
        data['Quarter sent'] = data['Quarter sent'].dt.to_timestamp()

    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    sns.lineplot(data=data, x='Quarter sent', y='zprop', style='isca', legend=True, ax=axes[0], alpha=0.7)
    sns.lineplot(data=data, x='Quarter sent', y='zcount', style='isca', legend=True, ax=axes[1], alpha=0.7)
    sns.lineplot(data=data, x='Quarter sent', y='count', style='isca', legend=True, ax=axes[2], alpha=0.7)
    axes[2].set_xlabel('Quarter sent')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by total assets (quarterly level)')
    axes[1].set_title('Number of zombie complaint by total assets (quarterly level)')
    axes[1].set_title('Number of all complaint by total assets (quarterly level)')

    for i in range(3):
        draw_policy_line(axes[i], data, ['CA'], extended=True)
        set_quarter_xticks(axes[i])

    save_plot(fig, 'depo_quarterly_trend_zprop_complaint_counts.png')

    # (4) x: Quarter sent, y: zprop, zcount, count - top states
    top_states = df['State'].value_counts().nlargest(5).index.tolist()
    total = tmp.groupby(['Quarter sent', 'State']).agg(count=('Total assets', 'size'), zprop=('Zombie data', 'mean'), isca=('Is CA', 'first')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Quarter sent', 'State']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Quarter sent', 'State'], how='left')
    data = data[data['State'].isin(top_states)]
    data['zcount'] = data['zcount'].fillna(0).astype(int)
    data = data.groupby(['Quarter sent', 'isca']).agg(count=('count', 'mean'), zprop=('zprop', 'mean'), zcount=('zcount', 'mean')).reset_index()
    data['zcount'] = data['zcount'].fillna(0).astype(int)
    if not pd.api.types.is_datetime64_any_dtype(data['Quarter sent']):
        data['Quarter sent'] = data['Quarter sent'].dt.to_timestamp()

    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    sns.lineplot(data=data, x='Quarter sent', y='zprop', style='isca', legend=True, ax=axes[0], alpha=0.7)
    sns.lineplot(data=data, x='Quarter sent', y='zcount', style='isca', legend=True, ax=axes[1], alpha=0.7)
    sns.lineplot(data=data, x='Quarter sent', y='count', style='isca', legend=True, ax=axes[2], alpha=0.7)
    axes[2].set_xlabel('Quarter sent')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by total assets (quarterly level)')
    axes[1].set_title('Number of zombie complaint by total assets (quarterly level)')
    axes[1].set_title('Number of all complaint by total assets (quarterly level)')

    for i in range(3):
        draw_policy_line(axes[i], data, ['CA'], extended=True)
        set_quarter_xticks(axes[i])

    save_plot(fig, 'depo_quarterly_trend_zprop_complaint_counts_top5_states.png')

    # (5) heatmap - x: Quarter sent, y: asset quantile
    tmp = get_asset_quantiles(tmp, bins=5, by_company_type=False)

    total = tmp.groupby(['Quarter sent', 'AssetsQuantile']).agg(count=('Total assets', 'size'), assets=('Total assets', 'mean'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Quarter sent', 'AssetsQuantile']).agg(zcount=('Total assets', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Quarter sent', 'AssetsQuantile'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)
    if not pd.api.types.is_datetime64_any_dtype(data['Quarter sent']):
        data['Quarter sent'] = data['Quarter sent'].dt.to_timestamp()

    palette = sns.color_palette("viridis", data['AssetsQuantile'].nunique())
    titles = ['Proportion of Zombie Complaints', 'Zombie Complaints Count', 'All Complaints Count']
    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    for i, val in enumerate(['zprop', 'zcount', 'count']):
        pivot= data.pivot(index='AssetsQuantile', columns='Quarter sent', values=val)
        sns.heatmap(pivot, cmap='YlGnBu', annot=False, cbar_kws={'label': titles[i]}, linewidths=0.5, linecolor='gray', ax=axes[i])
        axes[i].set_ylabel('Financial Institution Size Quantile')
        axes[i].set_title(f'{titles[i]} Heatmap by Quarter and Size Quantile')
        axes[i].invert_yaxis()

    period_labels = pd.PeriodIndex(pivot.columns, freq='Q').strftime('%YQ%q')
    axes[2].set_xlabel('Quarter Sent')
    axes[2].set_xticks(range(len(period_labels)))
    axes[2].set_xticklabels(period_labels, rotation=90)
    save_plot(fig, 'depo_time_heatmap_per_asset_quantiles.png')
    import pdb; pdb.set_trace()
    print(1)

def regulation_effect_in_binary_zombie_counts(savepath):
    tmp = df[(df['Company type'].isin(['bank', 'bank holding company', 'credit union']))
            &(df['Quarter sent'] >= pd.Period('2012Q2'))
            &(df['BankCount']<2)
            &(df['Total assets'].notna())].copy()

    #(1) x: total assets, y1: DV_agg, hue: regulation (company-yearly level)
    data = tmp.groupby(['Quarter sent', 'Company']).agg(assets=('Total assets', 'mean'),  zbin=('Zombie data', 'any'), regulation=('Regulation', 'first')).reset_index()

    fig, ax = plt.subplots(1, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='assets', y='zbin', hue='regulation', palette='colorblind', legend=True, ax=ax, alpha=0.6)
    ax.set_xlabel('Total assets')
    ax.set_ylabel('Binary indicator of receiving zombie complaints')
    ax.set_title('Binary indicator of receiving zombie complaints by total assets (company-yearly level)')
    ax.set_xscale('log')
    ax.axvline(x=10_000_000_000, color='gray', linestyle='--', label='10B line')
    ax.legend()
    save_plot(fig, 'zbin_total_assets_company_yearly_level.png', savepath)

    #(2) heatmap - proportion of companies with atleast one zombie data in asset quantile X year sent level
    tmp = get_asset_quantiles(tmp, bins=10, by_company_type=False)
    data = tmp.groupby(['Quarter sent', 'Company']).agg(assets=('Total assets', 'mean'),  zbin=('Zombie data', 'any'), AssetsQuantile=('AssetsQuantile', 'mean')).reset_index()
    heatmap_data = data.groupby(['Quarter sent', 'AssetsQuantile']).agg(zrate=('zbin', 'mean')).reset_index()
    pivot = heatmap_data.pivot(index='Quarter sent', columns='AssetsQuantile', values='zrate')

    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap='YlGnBu', cbar_kws={'label': 'Proportion of companies that received zombie data complaints'})
    plt.title("Proportions of company-quarters with any zombie data by asset quantile and quarter")
    plt.xlabel("Asset Quantile")
    plt.ylabel("Quarter Sent")
    save_plot(fig, 'zbin_rate_heatmap_company_quarterly_level.png', savepath)


    #(3) x: total assets, y1: proportion of zombie complaints, y2: zombie complaints count, y3: total complaints count, hue: regulation (company level)
    for year in [2020, 2021, 2022, 2023, 2024]:
        data = tmp[tmp['Year sent']==year].groupby(['Company']).agg(assets=('Total assets', 'mean'),  zbin=('Zombie data', 'any'), regulation=('Regulation', lambda x: x.mode().iloc[0])).reset_index()

        fig, ax = plt.subplots(1, 1, figsize=(10, 10), sharex=True)
        sns.scatterplot(data=data, x='assets', y='zbin', hue='regulation', palette='colorblind', legend=True, ax=ax, alpha=0.6)
        ax.set_xlabel('Total assets')
        ax.set_ylabel('Binary indicator of receiving zombie complaints')
        ax.set_title(f'Binary indicator of receiving zombie complaints by total assets (Year {year})')
        ax.set_xscale('log')
        ax.axvline(x=10_000_000_000, color='gray', linestyle='--', label='10B line')
        ax.legend()
        save_plot(fig, f'zbin_total_assets_company_yearly_level_year{year}.png', savepath)

    #(4) lineplot - proportion of companies with atleast one zombie data in asset quantile X year sent level
    bins = np.linspace(tmp['Log total assets'].min(), tmp['Log total assets'].max(), 20)
    tmp['asset_bin'] = pd.cut(tmp['Log total assets'], bins)
    data = tmp.groupby(['Quarter sent', 'Company']).agg(asset_bin=('asset_bin', 'first'),  zbin=('Zombie data', 'any')).reset_index()
    zrate_by_bin = data.groupby('asset_bin').agg(zrate=('zbin', 'mean')).reset_index()
    zrate_by_bin['asset_bin_center'] = zrate_by_bin['asset_bin'].apply(lambda x: np.exp((x.left + x.right) / 2))
    zrate_by_bin = zrate_by_bin.sort_values('asset_bin_center')

    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    sns.lineplot(data=zrate_by_bin, x='asset_bin_center', y='zrate', errorbar='ci')
    plt.axvline(1e10, color='gray', linestyle='--', label='10B cutoff') 
    plt.xscale('log')
    plt.xlabel("Total Assets (log scale)")
    plt.ylabel("Proportion of companies-quarters that received atleast one zombie data complaints")
    plt.title("Rate of Receiving Zombie Data Complaints by Asset Size")
    plt.legend()
    save_plot(fig, 'zbin_rate_lineplot_company_quarterly_level.png', savepath)

def get_col_quantiles(data, gpcols, bincols, subcol, qcol='', bins=5): 
    '''
    gpcols (list of str): Columns to group by
    bincols (list of str): Columns to define groups for quantile computation
    subcol (str): Column to compute quantiles on
    qcol (str): Optional name for the new quantile column; auto-generated if blank
    '''
    if qcol == '':
        qcol = subcol + '_Quantile'

    for col in bincols:
        if col not in gpcols:
            gpcols.append(col)

    tmp = data.copy()
    gp = tmp.groupby(gpcols)[subcol].mean().reset_index()
    gp[qcol] = gp.groupby(bincols)[subcol].transform(lambda x: pd.qcut(x, bins, labels=False, duplicates='drop') + 1)
    tmp = tmp.merge(gp[gpcols + [qcol]], on=gpcols, how='left')
    if len(bincols)==1:
        print(pd.crosstab(gp[bincols[0]], gp[qcol]))
    import pdb; pdb.set_trace()
    return tmp

def explore_income_effect_zctalvl(savepath):
    # exclusion inclusion criteria
    print(f"Exclusion criteria: starting with {len(df)} complaints")
    tmp = df[df['ZIP code'].notna()].copy()
    print(f"drop complaints without zipcode: {len(tmp)} complaints left")
    tmp = tmp[tmp['zip'].notna()].copy()
    print(f"drop complaints that cannot be matched with ACS dataset with zipcode: {len(tmp)} complaints left")
    tmp = tmp[tmp['MedIncome']>0].copy()
    print(f"drop complaints from zip code where median income information is unavailable: {len(tmp)} complaints left")
    tmp = tmp[tmp['Company type']=='major credit bureaus'].copy()
    print(f"only keep complaints sent to major credit bureus: {len(tmp)} complaints left")
    print(f"finish constructing dataset on complaints with socio-demographic vars sent to major credit bureaus {len(tmp)}")
    print(f"{tmp['Zombie data'].sum()} complaints are about zombie data")
    #import pdb; pdb.set_trace()
    #(1) x: median income, y: zprop, zcount, count (year-zip level)
    total = tmp.groupby(['Year received', 'ZIP code']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'ZIP code']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'ZIP code'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
    sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
    sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (zip code-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (zip code-yearly level)')
    axes[1].set_title('Number of all complaint by median household income (zip code-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, 'zprop_zip_yearly_level.png', savepath)

    #(2) x: median income, y: zprop, zcount, count, hue: company (year-zip level) - heterogeneity between companies
    total = tmp.groupby(['Year received', 'ZIP code', 'Company']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'ZIP code', 'Company']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'ZIP code', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', hue='Company', palette='colorblind', legend=True, ax=axes[0], alpha=0.7)
    sns.scatterplot(data=data, x='income', y='zcount', hue='Company', palette='colorblind', legend=True, ax=axes[1], alpha=0.7)
    sns.scatterplot(data=data, x='income', y='count', hue='Company', palette='colorblind', legend=True, ax=axes[2], alpha=0.7)
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (zip code-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (zip code-yearly level)')
    axes[1].set_title('Number of all complaint by median household income (zip code-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, 'zprop_zip_yearly_level_company.png', savepath)


    #(3) plot each year separately - x: median income, y: zprop, zcount, count (year-zip level)
    for year in [2020, 2021, 2022, 2023, 2024]:
        total = tmp[tmp['Year received']==year].groupby(['ZIP code']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
        zombie = tmp[(tmp['Zombie data'] == 1)&(tmp['Year received']==year)].groupby(['ZIP code']).agg(zcount=('Zombie data', 'size')).reset_index()
        data = pd.merge(total, zombie, on=['ZIP code'], how='left')
        data['zcount'] = data['zcount'].fillna(0).astype(int)

        fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
        sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
        sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
        sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
        axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

        axes[0].set_ylabel('Proportion of zombie complaints')
        axes[1].set_ylabel('Zombie complaint count')
        axes[2].set_ylabel('Total complaint count')

        axes[0].set_title('Proportion of of zombie complaints by median household income (zip code-yearly level)')
        axes[1].set_title('Number of zombie complaint by median household income (zip code-yearly level)')
        axes[1].set_title('Number of all complaint by median household income (zip code-yearly level)')

        axes[1].set_yscale('symlog')
        axes[2].set_yscale('symlog')

        for i in range(3):
            axes[i].set_ylim(ymin=0)
        save_plot(fig, f'zprop_zip_yearly_level_year{year}.png', savepath)

    #(4) temporary - zip3 level x: median income, y: zprop, zcount, count (year-zip3 level)
    tmp['ZIP3'] = tmp['ZIP code'].astype(str).str[:3]
    total = tmp.groupby(['Year received', 'ZIP3']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'ZIP3']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'ZIP3'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
    sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
    sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (zip3 code-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (zip3 code-yearly level)')
    axes[1].set_title('Number of all complaint by median household income (zip3 code-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, 'zprop_zip3_yearly_level.png', savepath)

    #(5) temporary - zip3 level x: median income, y: zprop, zcount, count (year-zip3 level)
    for year in [2020, 2021, 2022, 2023, 2024]:
        total = tmp[tmp['Year received']==year].groupby(['ZIP3']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
        zombie = tmp[(tmp['Zombie data'] == 1)&(tmp['Year received']==year)].groupby(['ZIP3']).agg(zcount=('Zombie data', 'size')).reset_index()
        data = pd.merge(total, zombie, on=['ZIP3'], how='left')
        data['zcount'] = data['zcount'].fillna(0).astype(int)

        fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
        sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
        sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
        sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
        axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

        axes[0].set_ylabel('Proportion of zombie complaints')
        axes[1].set_ylabel('Zombie complaint count')
        axes[2].set_ylabel('Total complaint count')

        axes[0].set_title(f'Proportion of of zombie complaints by median household income (zip3 code level, year {year})')
        axes[1].set_title(f'Number of zombie complaint by median household income (zip3 code level, year {year})')
        axes[1].set_title(f'Number of all complaint by median household income (zip3 codelevel, year {year})')

        axes[1].set_yscale('symlog')
        axes[2].set_yscale('symlog')

        for i in range(3):
            axes[i].set_ylim(ymin=0)
        save_plot(fig, f'zprop_zip3_yearly_level_year{year}.png', savepath)

def explore_income_effect_countylvl(savepath):
    # exclusion inclusion criteria
    print(f"Exclusion criteria: starting with {len(df)} complaints")
    tmp = df[df['ZIP code'].notna()].copy()
    print(f"drop complaints without zipcode or three digits zipcodes: {len(tmp)} complaints left")
    tmp = tmp[~tmp['ZIP code'].str.endswith('XX')].copy()
    print(f"drop complaints with three digits zipcode: {len(tmp)} complaints left")
    tmp = tmp[tmp['zip'].notna()].copy()
    print(f"drop complaints that cannot be matched with ACS dataset with zipcode: {len(tmp)} complaints left")
    tmp = tmp[tmp['MedIncome']>0].copy()
    print(f"drop complaints from zip code where median income information is unavailable: {len(tmp)} complaints left")
    tmp = tmp[tmp['Company type']=='major credit bureaus'].copy()
    print(f"only keep complaints sent to major credit bureus: {len(tmp)} complaints left")
    print(f"finish constructing dataset on complaints with socio-demographic vars sent to major credit bureaus {len(tmp)}")
    print(f"{tmp['Zombie data'].sum()} complaints are about zombie data")
    county_zip = df.groupby(['Year received','fips'])['ZIP code'].nunique().reset_index(name='nuniq')
    print(f"on average, a county includes {county_zip['nuniq'].mean():.2f} zip codes")

    # histogram of median income
    total = tmp.groupby(['Year received', 'fips']).agg(income=('RealMedIncome', 'mean')).reset_index()
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    sns.histplot(data=total, x='income', ax=ax, element='bars', color='skyblue', alpha=1)
    ax.set_xlabel('Median Income')
    ax.set_ylabel('number of county-years')
    save_plot(fig, 'dist_medincome_county_yearly_level.png', savepath)
    
    #(1) x: median income, y: zprop, zcount, count (year-county level)
    total = tmp.groupby(['Year received', 'fips']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'fips']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'fips'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
    sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
    sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (county-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (county-yearly level)')
    axes[2].set_title('Number of all complaint by median household income (county-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, 'zprop_county_yearly_level.png', savepath)

    #(2) x: median income, y: zprop, zcount, count, hue: company (year-zip level) - heterogeneity between companies
    total = tmp.groupby(['Year received', 'fips', 'Company']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'fips', 'Company']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'fips', 'Company'], how='left')
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', hue='Company', palette='colorblind', legend=True, ax=axes[0], alpha=0.7)
    sns.scatterplot(data=data, x='income', y='zcount', hue='Company', palette='colorblind', legend=True, ax=axes[1], alpha=0.7)
    sns.scatterplot(data=data, x='income', y='count', hue='Company', palette='colorblind', legend=True, ax=axes[2], alpha=0.7)
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (county-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (county-yearly level)')
    axes[2].set_title('Number of all complaint by median household income (county-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, 'zprop_county_yearly_level_company.png', savepath)

    #(3) plot each year separately - x: median income, y: zprop, zcount, count (year-zip level)
    for year in range(2013,2025):
        total = tmp[tmp['Year received']==year].groupby(['fips']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
        zombie = tmp[(tmp['Zombie data'] == 1)&(tmp['Year received']==year)].groupby(['fips']).agg(zcount=('Zombie data', 'size')).reset_index()
        data = pd.merge(total, zombie, on=['fips'], how='left')
        data['zcount'] = data['zcount'].fillna(0).astype(int)

        fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
        sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
        sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
        sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
        axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

        axes[0].set_ylabel('Proportion of zombie complaints')
        axes[1].set_ylabel('Zombie complaint count')
        axes[2].set_ylabel('Total complaint count')

        axes[0].set_title('Proportion of of zombie complaints by median household income (county-yearly level)')
        axes[1].set_title('Number of zombie complaint by median household income (county-yearly level)')
        axes[2].set_title('Number of all complaint by median household income (county-yearly level)')

        axes[1].set_yscale('symlog')
        axes[2].set_yscale('symlog')

        for i in range(3):
            axes[i].set_ylim(ymin=0)
        save_plot(fig, f'zprop_county_yearly_level_year{year}.png', savepath)

    #(4) heatmap - proportion of zombie data median income quantile (county level) X year sent level
    #tmp = get_col_quantiles(tmp, ['fips'], ['Year received'], 'MedIncome', qcol='', bins=5)
    tmp['MedIncome_Quantile'] = pd.qcut(tmp['RealMedIncome'], q=5, labels=False)
    data = tmp.groupby(['Year received', 'MedIncome_Quantile']).agg(income=('MedIncome', 'mean'),  zprop=('Zombie data', 'mean')).reset_index()
    pivot= data.pivot(index='MedIncome_Quantile', columns='Year received', values='zprop')

    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap='YlGnBu', cbar_kws={'label': 'Proportion zombie data complaints'})
    ax.invert_yaxis()
    plt.title("Proportions of zombie data complaints by county-level median income quantile and year")
    plt.ylabel("Median Income Quantile (upper = richer)")
    plt.xlabel("Year received")
    save_plot(fig, 'zprop_heatmap_county_yearly_level.png', savepath)
    tmp.drop('MedIncome_Quantile', axis=1, inplace=True)

def explore_income_effect_countylvl_with_cutoff(cutoff, savepath, bins=5): # only include counties with yearly complaint counts > cutoff
    # exclusion inclusion criteria
    tmp = df[df['ZIP code'].notna()].copy()
    tmp = tmp[~tmp['ZIP code'].str.endswith('XX')].copy()
    tmp = tmp[tmp['zip'].notna()].copy()
    tmp = tmp[tmp['MedIncome']>0].copy()
    tmp = tmp[tmp['Company type']=='major credit bureaus'].copy()
    county_zip = df.groupby(['Year received','fips'])['ZIP code'].nunique().reset_index(name='nuniq')

    ### only include counties with yearly complaint counts > cutoff
    # histogram of median income 
    total = tmp.groupby(['Year received', 'fips']).agg(income=('RealMedIncome', 'mean'), count=('RealMedIncome', 'size')).reset_index()
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    sns.histplot(data=total[total['count']>cutoff], x='income', ax=ax, element='bars', color='skyblue', alpha=1)
    ax.set_xlabel('Median Income')
    ax.set_ylabel('number of county-years')
    save_plot(fig, f'dist_medincome_county_yearly_level_cutoff{cutoff}.png', savepath)
    

    #(1) x: median income, y: zprop, zcount, count (year-county level)
    total = tmp.groupby(['Year received', 'fips']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'fips']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'fips'], how='left')
    data = data[data['count']>cutoff]
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
    sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
    sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (county-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (county-yearly level)')
    axes[2].set_title('Number of all complaint by median household income (county-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, f'zprop_county_yearly_level_cutoff{cutoff}.png', savepath)

    #(2) x: median income, y: zprop, zcount, count, hue: company (year-zip level) - heterogeneity between companies
    total = tmp.groupby(['Year received', 'fips', 'Company']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'fips', 'Company']).agg(zcount=('Zombie data', 'size')).reset_index()
    data = pd.merge(total, zombie, on=['Year received', 'fips', 'Company'], how='left')
    data = data[data['count']>cutoff]
    data['zcount'] = data['zcount'].fillna(0).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sns.scatterplot(data=data, x='income', y='zprop', hue='Company', palette='colorblind', legend=True, ax=axes[0], alpha=0.7)
    sns.scatterplot(data=data, x='income', y='zcount', hue='Company', palette='colorblind', legend=True, ax=axes[1], alpha=0.7)
    sns.scatterplot(data=data, x='income', y='count', hue='Company', palette='colorblind', legend=True, ax=axes[2], alpha=0.7)
    axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

    axes[0].set_ylabel('Proportion of zombie complaints')
    axes[1].set_ylabel('Zombie complaint count')
    axes[2].set_ylabel('Total complaint count')

    axes[0].set_title('Proportion of of zombie complaints by median household income (county-yearly level)')
    axes[1].set_title('Number of zombie complaint by median household income (county-yearly level)')
    axes[2].set_title('Number of all complaint by median household income (county-yearly level)')

    axes[1].set_yscale('symlog')
    axes[2].set_yscale('symlog')

    for i in range(3):
        axes[i].set_ylim(ymin=0)

    save_plot(fig, f'zprop_county_yearly_level_company_cutoff{cutoff}.png', savepath)

    #(3) plot each year separately - x: median income, y: zprop, zcount, count (year-zip level)
    for year in range(2013,2025):
        total = tmp[tmp['Year received']==year].groupby(['fips']).agg(income=('RealMedIncome', 'mean'),  count=('Zombie data', 'size'), zprop=('Zombie data', 'mean')).reset_index()
        zombie = tmp[(tmp['Zombie data'] == 1)&(tmp['Year received']==year)].groupby(['fips']).agg(zcount=('Zombie data', 'size')).reset_index()
        data = pd.merge(total, zombie, on=['fips'], how='left')
        data = data[data['count']>cutoff]
        data['zcount'] = data['zcount'].fillna(0).astype(int)

        fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
        sns.scatterplot(data=data, x='income', y='zprop', legend=True, ax=axes[0])
        sns.scatterplot(data=data, x='income', y='zcount', legend=True, ax=axes[1])
        sns.scatterplot(data=data, x='income', y='count', legend=True, ax=axes[2])
        axes[2].set_xlabel('Median Household Income (in 2013 inflation adjusted dollars)')

        axes[0].set_ylabel('Proportion of zombie complaints')
        axes[1].set_ylabel('Zombie complaint count')
        axes[2].set_ylabel('Total complaint count')

        axes[0].set_title('Proportion of of zombie complaints by median household income (county-yearly level)')
        axes[1].set_title('Number of zombie complaint by median household income (county-yearly level)')
        axes[2].set_title('Number of all complaint by median household income (county-yearly level)')

        axes[1].set_yscale('symlog')
        axes[2].set_yscale('symlog')

        for i in range(3):
            axes[i].set_ylim(ymin=0)
        save_plot(fig, f'zprop_county_yearly_level_year{year}_cutoff{cutoff}.png', savepath)

    #(4) heatmap - proportion of zombie data median income quantile (county level) X year sent level
    total = tmp.groupby(['Year received', 'fips']).agg(count=('Zombie data', 'size'), income=('RealMedIncome', 'mean')).reset_index()
    zombie = tmp[tmp['Zombie data'] == 1].groupby(['Year received', 'fips']).agg(zcount=('Zombie data', 'size')).reset_index()
    merged = pd.merge(total, zombie, on=['Year received', 'fips'], how='left')
    merged['zcount'] = merged['zcount'].fillna(0).astype(int)
    merged = merged[merged['count']>cutoff]

    #merged = get_col_quantiles(merged, ['fips'], ['Year received'], 'income', qcol='', bins=bins)
    merged['income_Quantile'] = pd.qcut(merged['income'], q=bins, labels=False)
    data = merged.groupby(['Year received', 'income_Quantile']).agg(totcount=('count', 'sum'), totzcount=('zcount', 'sum')).reset_index()
    data['zprop'] = data['totzcount']/data['totcount']
    pivot= data.pivot(index='income_Quantile', columns='Year received', values='zprop')

    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap='YlGnBu', cbar_kws={'label': 'Proportion zombie data complaints'})
    ax.invert_yaxis()
    plt.title("Proportions of zombie data complaints by county-level median income quantile and year")
    plt.ylabel("Median Income Quantile (upper = richer)")
    plt.xlabel("Year received")
    if bins==5:
        save_plot(fig, f'zprop_heatmap_county_yearly_level_cutoff{cutoff}.png', savepath)
    else:
        save_plot(fig, f'zprop_heatmap_county_yearly_level_cutoff{cutoff}_{bins}bins.png', savepath)

    

if __name__ == "__main__":
    ### load dataset
    df = pd.read_csv(os.path.join(cPATH, 'input', 'complaints_processed.csv'), low_memory=False)

    ### set dtypes
    df['Date received'] = pd.to_datetime(df['Date received'])
    df['Date sent to company'] = pd.to_datetime(df['Date sent to company'])
    df['Consumer complaint narrative'] = df['Consumer complaint narrative'].astype('string')
    df['Month received'] = pd.to_datetime(df['Month received'])
    df['Quarter received'] = pd.PeriodIndex(df['Quarter received'], freq='Q')
    df['Year received'] = df['Year received'].astype('Int64') 
    df['Quarter sent'] = pd.PeriodIndex(df['Quarter sent'], freq='Q')
    df['Year sent'] = df['Year sent'].astype('Int64')
    df['State privacy law'] = pd.to_datetime(df['State privacy law'])

    ### set orders of categorical variables with order 
    duration_order = ['< 1 day', '1 day', '2 days', '3 days', '4 days', '5 days', '6 days', '7 days', 'within two weeks', 
                      'within a month', 'within 90 days', 'within 180 days', 'within a year', 'more than a year']
    df['Duration categorized'] = pd.Categorical(df['Duration categorized'], categories=duration_order, ordered=True)
    group_order = ['< 1 day', 'within a week', 'within a month', 'more than a month']
    df['Duration grouped'] = pd.Categorical(df['Duration grouped'], categories=group_order, ordered=True)
    ccpa_order = ['Pre-CCPA', 'CCPA enacted, pre-implement', 'CCPA implemented, pre-CPRA', 'CPRA amended, pre-implementation', 'CPRA implemented']
    df['CCPA phase at receipt'] = pd.Categorical(df['CCPA phase at receipt'], categories=ccpa_order, ordered=False)
    df['CCPA phase at sent'] = pd.Categorical(df['CCPA phase at sent'], categories=ccpa_order, ordered=False)

    ### split data into complaints with/without narratives for exploratory analysis
    subdf = df[df['With narrative']] # with narrative
    mssdf = df[~df['With narrative']] # missing narrative

    ### CCPA and CPRA
    CCPA_timeline = {'CCPA enactment': '2018-06-28', 'CCPA implementation': '2020-01-01', 'CPRA amendment': '2020-11-03', 'CPRA implementation': '2023-01-01'}
    CCPA_quarters = {label: pd.to_datetime(date).to_period('Q').strftime('%YQ%q') for label, date in CCPA_timeline.items()}
    '''
    ### state-quarterly level zombie data plots
    quarter_index = sorted(df['Quarter received'].unique())
    plot_quarterly_trend_zombie_data()
    plot_quarterly_trend_zombie_data_CA()
    plot_quarterly_trend_zombie_data_most_complaints_states()

    ### state-financial bureau level analysis 
    plot_quarterly_companies_in_top_states(5)
    plot_company_type(5)

    ### DV: relief rate
    plot_complaints_and_response_per_size_company_level()
    plot_response_per_complaint_count_company_quarterly_level()
    plot_response_per_complaint_count()
    quarterly_plot_assets_vs_relief()
    time_trend_in_relief_per_asset_quantile()
    time_trend_in_relief_rate()

    ### DV: proportion of zombie data related complaints among all compliants
    savepath = os.path.join(cPATH, 'temp', 'DV_prop_zombie_complaints')
    if not os.path.exists(savepath):
        os.mkdir(savepath)

    tmp = df[df['Company type'].isin(['bank', 'bank holding company', 'credit union'])].copy()
    tmp = get_asset_quantiles(tmp)
    tmp.loc[tmp['Company type'].isin(['bank', 'bank holding company']), 'Company type'] = 'bank_bhc'

    plot_DV_per_size([('Zombie data', 'mean')], tmp, ['Proportion of zombie data complaints'], savepath)
    time_heatmap_DV_per_asset_quantile([('Zombie data', 'mean')], tmp, ['Proportion of zombie data complaints'], savepath)

    tmp = df[df['Company type']!='others'].copy()
    tmp.loc[tmp['Company type'].isin(['bank', 'bank holding company']), 'Company type'] = 'bank_bhc'
    time_trend_in_DV([('Zombie data', 'mean')], tmp, ['Proportion of zombie data complaints'], savepath)
    plot_prop_zombie_per_complaint_counts(tmp, savepath)

    # explores CFPB regulation effect 
    regulation_effect_analysis()
    CFPB_depository_analysis()

    ### DV: receiving zombie complaints
    savepath = os.path.join(cPATH, 'temp', 'DV_bin_zombie_complaints')
    if not os.path.exists(savepath):
        os.mkdir(savepath)

    tmp = df[(df['Company type'].isin(['bank', 'bank holding company', 'credit union']))
            &(df['Quarter sent'] >= pd.Period('2012Q2'))
            &(df['BankCount']<2)
            &(df['Total assets'].notna())].copy()

    plot_DV_per_size([('Zombie data', 'any')], tmp, ['Receiving any zombie data complaints'], savepath)
    regulation_effect_in_binary_zombie_counts(savepath)

    savepath = os.path.join(cPATH, 'temp', 'MedianIncome')
    if not os.path.exists(savepath):
        os.mkdir(savepath)
    explore_income_effect_zctalvl(savepath)
    '''
    savepath = os.path.join(cPATH, 'temp', 'MedianIncome_countylvl')
    if not os.path.exists(savepath):
        os.mkdir(savepath)
    explore_income_effect_countylvl(savepath)
    explore_income_effect_countylvl_with_cutoff(500, savepath)
    explore_income_effect_countylvl_with_cutoff(100, savepath)
    explore_income_effect_countylvl_with_cutoff(30, savepath)
    explore_income_effect_countylvl_with_cutoff(10, savepath)
    explore_income_effect_countylvl_with_cutoff(100, savepath, bins=10)
    explore_income_effect_countylvl_with_cutoff(100, savepath, bins=20)
    explore_income_effect_countylvl_with_cutoff(100, savepath, bins=4)



    
    