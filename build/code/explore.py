import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.pyplot as plt

from matplotlib.lines import Line2D



cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "build")

def save_plot(fig, filename, path='temp', tight=True):
    out_path = os.path.join(cPATH, path, filename)
    if tight:
        fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)

def visualize_duration_categorized(): # broken y-axis graph
    duration_counts = df.groupby('Duration categorized', observed=False).size().sort_index()
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(12, 6), gridspec_kw={'height_ratios': [1, 3]})
    plt.subplots_adjust(hspace=0.05)

    ax1.bar(duration_counts.index, duration_counts.values)
    ax1.set_ylim(duration_counts.max() * 0.7, duration_counts.max() * 1.2)

    ax2.bar(duration_counts.index, duration_counts.values)
    ax2.set_ylim(0, duration_counts[1:].max() * 1.2)  

    for ax in [ax1, ax2]:
        for i, v in enumerate(duration_counts.values):
            if ax == ax1 and v < duration_counts.max() * 0.7:
                continue  
            if ax == ax2 and v >= duration_counts.max() * 0.9:
                continue  
            ax.text(i, v +  0.5, str(v), ha='center', va='bottom', fontsize=9)

    ax2.set_xlabel('Time')
    ax1.set_ylabel('Count')
    ax2.set_ylabel('Count')
    fig.suptitle('Time Elapsed From Receiving the Complaint to Sending It to The Company')
    ax2.tick_params(axis='x', rotation=45)

    d = .001
    kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
    ax1.plot((-d, +d), (-d, +d), **kwargs)       
    ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs) 
    kwargs.update(transform=ax2.transAxes)
    ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)
    ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

    plt.subplots_adjust(hspace=0.02)
    save_plot(fig, 'duration_sending_count.png')

def visualize_monthly_complaints_counts():
    monthly_counts = df.groupby('Month received').size()
    monthly_counts.plot(kind='bar', figsize=(10,5))
    
    plt.xlabel('Month')
    plt.ylabel('Count')
    plt.title('Monthly Counts of Complains Received')

    xticks = monthly_counts.index
    tick_interval = 12  
    plt.xticks(
        ticks=range(0, len(xticks), tick_interval),
        labels=[xticks[i].strftime('%Y-%m') for i in range(0, len(xticks), tick_interval)],
        rotation=45
    )
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'monthly_complaints_count.png'))
    plt.clf()

    # comparsison of monthly counts of complaints with/without narratives
    mss_monthly_counts = df[~df['With narrative']].groupby('Month received').size()
    sub_monthly_counts = df[df['With narrative']].groupby('Month received').size()
    fig, axes = plt.subplots(1, 2, figsize=(15,5), sharey=True)

    plt.title('Monthly Counts of Complains Received With/Without Consumer Narratives')
    mss_monthly_counts.plot(kind='bar', ax=axes[0])
    xticks1 = mss_monthly_counts.index
    axes[0].set_title('Missing Narratives')
    axes[0].set_xlabel('Month')
    axes[0].set_ylabel('Count')
    axes[0].set_xticks(range(0, len(xticks1), tick_interval))
    axes[0].set_xticklabels([xticks1[i].strftime('%Y-%m') for i in range(0, len(xticks1), tick_interval)], rotation=45)

    sub_monthly_counts.plot(kind='bar', ax=axes[1])
    xticks2 = sub_monthly_counts.index
    axes[1].set_title('With Narrative')
    axes[1].set_xlabel('Month')
    axes[1].set_ylabel('Count')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].set_xticks(range(0, len(xticks2), tick_interval))
    axes[1].set_xticklabels([xticks2[i].strftime('%Y-%m') for i in range(0, len(xticks2), tick_interval)], rotation=45)

    save_plot(fig, 'monthly_complaints_count_with_without_narratives.png')

def visualize_yearly_trend_in_duration():
    pivot = (df.groupby(['Year received', 'Duration grouped'], observed=False).size().groupby(level=0, observed=False).apply(lambda x: x / x.sum() * 100).unstack(fill_value=0))
    pivot.index = pivot.index.get_level_values(0)

    pivot[pivot.columns].plot(kind='bar', stacked=True, color=sns.color_palette("Set2"), figsize=(10, 6))
    plt.ylabel("Percent")
    plt.title("Complaint Processing Duration by Year")
    plt.xticks(rotation=45)
    plt.legend(title="Duration")
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'yearly_trend_in_duration.png'))
    plt.clf()

    # comparison of yearly trend between complaint with/without narratives
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    legend_labels = None

    for ax, df_part, title in zip(axes, [mssdf, subdf], ["Missing Narratives", "With Narratives"]):
        pivot = (df_part.groupby(['Year received', 'Duration grouped'], observed=False).size().groupby(level=0, observed=False).apply(lambda x: x / x.sum() * 100).unstack(fill_value=0))
        pivot.index = pivot.index.get_level_values(0)
        
        bar_container = pivot[pivot.columns].plot(kind='bar', stacked=True, color=sns.color_palette("Set2"), ax=ax)
        ax.set_title(f"Complaint Duration Trend - {title}")
        ax.set_ylabel("Percent")
        ax.set_xlabel("Year")
        ax.tick_params(axis='x', rotation=45)

    if legend_labels is None:
        legend_labels = bar_container.get_legend_handles_labels()

    fig.legend(*legend_labels, title="Duration", loc='lower center', ncol=len(legend_labels[0]), bbox_to_anchor=(0.5, -0.05))
    save_plot(fig, 'yearly_trend_in_duration_with_without_narratives.png')

def visualize_yearly_trend_in_company_response():
    filtered_df = df[~df['Year sent'].isin([2011, 2012])] # filter out data in 2011 and 2012 since they contain period during which response categories were different
    pivot = (filtered_df.groupby(['Year sent', 'Company response to consumer'], observed=False).size().groupby(level=0, observed=False).apply(lambda x: x / x.sum() * 100).unstack(fill_value=0))
    pivot.index = pivot.index.get_level_values(0)

    nonzero_cols = pivot.loc[:, (pivot != 0).any(axis=0)]
    colors = sns.color_palette("Set2", n_colors=len(nonzero_cols.columns))
    nonzero_cols.plot(kind='bar', stacked=True, color=colors, figsize=(10, 6))

    plt.ylabel("Percent")
    plt.title("Proportion of Company Response to Complaint by Year")
    plt.xticks(rotation=45)
    plt.legend(title="Duration", loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'yearly_trend_in_response.png'))
    plt.clf()

    # comparison of yearly trend between complaint with/without narratives
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    filtered_mssdf = mssdf[~mssdf['Year sent'].isin([2011, 2012])]

    for ax, df_part, title in zip(axes, [filtered_mssdf, subdf], ["Missing Narratives", "With Narratives"]):
        pivot = (df_part.groupby(['Year sent', 'Company response to consumer'], observed=False).size().groupby(level=0, observed=False).apply(lambda x: x / x.sum() * 100).unstack(fill_value=0))
        pivot.index = pivot.index.get_level_values(0)
        pivot = pivot.reindex(columns=nonzero_cols.columns, fill_value=0)

        pivot.plot(kind='bar', stacked=True, color=colors, ax=ax)
        ax.set_title(f"Company Response Trend - {title}")
        ax.set_ylabel("Percent")
        ax.set_xlabel("Year")
        ax.legend_.remove()
        ax.tick_params(axis='x', rotation=45)

    fig.legend(nonzero_cols.columns, title="Duration", loc='lower right', bbox_to_anchor=(1.02, 0))
    plt.tight_layout(rect=[0, 0, 0.85, 1])  # legend 공간 확보
    plt.savefig(os.path.join(cPATH, 'temp', 'yearly_trend_in_response_with_without_narratives.png'))

def plot_category_distribution(dfs, col, labels, savepath, top_n=0, suppress=False, wrap_width=30):
    tmpdf = pd.concat(dfs)
    if top_n: # filter top n categories in the whole dataset
        tmpdf = pd.concat(dfs)
        filled = tmpdf[col].fillna('Missing')
        counts = filled.value_counts()
        if filled.nunique() > top_n:
            top_cats = counts.nlargest(top_n).index
    else:
        top_cats = tmpdf[col].unique()

    def summarize(df, label, cats):
        filled = df[col].fillna('Missing')
        filled = filled.apply(lambda x: x if x in cats else 'Other')
        counts = filled.value_counts()
        counts = counts.reindex(cats, fill_value=0)
        percents = counts / len(df) * 100
        categories = counts.index
        return pd.DataFrame({'Category': categories, 'Count': counts.values, 'Percent': percents.values, 'Dataset': label})
    
    summary = [summarize(df, labels[i], top_cats) for i, df in enumerate(dfs)]

    fig, axes = plt.subplots(1, len(dfs), figsize=(7 * len(dfs), 6 + len(top_cats)*0.3), sharey=True)
    max_percent = max(pd.concat(summary)['Percent'])
    for i, ax in enumerate(axes):
        ax.set_xlabel("Percent")
        ax.set_ylabel("Category")
        sns.barplot(data=summary[i], y='Category', x='Percent', ax=ax, orient='h', color='skyblue', order=top_cats)
        if not suppress: 
            reordered = summary[i].set_index('Category').loc[top_cats].reset_index()
            for j, row in reordered.iterrows():
                ax.text(row['Percent'] + 0.5, j, f"{row['Percent']:.1f}%" ,va='top',fontsize=10)
        ax.set_xlim(0, max_percent * 1.2)
        ax.set_title(f"{labels[i]} - '{col}' distribution")

    if top_n:
        plt.suptitle(f"Distribution of '{col}' Across Datasets (Top {top_n} Categories)", fontsize=16)
    else:
        plt.suptitle(f"Distribution of '{col}' Across Datasets", fontsize=16)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if savepath[-4:] in ['.jpg', '.png', '.pdf']:
        plt.savefig(savepath)
    else:
        print("CHECK savepath ARGUMENT - SHOULD END WITH .jpg OR .png OR .pdf")
        plt.show()

def explore_bhc_assets():
    #bhc = df[df['Company type']=='bank holding company']
    bhc_assets = pd.read_csv(os.path.join(cPATH, 'temp', 'bhc_assets.csv'))
    grouped = bhc_assets.groupby(['Quarter sent', '#ID_RSSD']).agg(TotalAssets=('Total assets', 'mean'), BankAssets=('BankAssets', 'mean'), Consolidated=('Consolidated', 'mean')).reset_index()
    grouped['AssetsRatio'] = grouped['BankAssets'] / grouped['TotalAssets']

    complaint_level = {'Total Count': len(bhc_assets), 
                        'Total Assets Only': len(bhc_assets[(bhc_assets['Total assets'].notna()) & (bhc_assets['BankAssets'].isna())]),
                        '(Total Assets Only - Consolidated)': len(bhc_assets[(bhc_assets['Total assets'].notna()) & (bhc_assets['BankAssets'].isna()) & (bhc_assets['Consolidated']==1)]),
                        '(Total Assets Only - Parent Only)': len(bhc_assets[(bhc_assets['Total assets'].notna()) & (bhc_assets['BankAssets'].isna()) & (bhc_assets['Consolidated']==0)]),
                        'Sum Bank Assets Only': len(bhc_assets[(bhc_assets['Total assets'].isna()) & (bhc_assets['BankAssets'].notna())]), 
                        'No Assets info': len(bhc_assets[(bhc_assets['Total assets'].isna()) & (bhc_assets['BankAssets'].isna())]),
                        'Both Assets info': len(bhc_assets[(bhc_assets['Total assets'].notna()) & (bhc_assets['BankAssets'].notna())]),
                        '(Both Assets info - Consolidated)': len(bhc_assets[(bhc_assets['Total assets'].notna()) & (bhc_assets['BankAssets'].notna()) & (bhc_assets['Consolidated']==1)]),
                        '(Both Assets info - Parent Only)': len(bhc_assets[(bhc_assets['Total assets'].notna()) & (bhc_assets['BankAssets'].notna()) & (bhc_assets['Consolidated']==0)])}

    bhc_quarter_level = {'Total Count': len(grouped), 'Total Assets Only': len(grouped[(grouped['TotalAssets'].notna()) & (grouped['BankAssets'].isna())]),
                        '(Total Assets Only - Consolidated)': len(grouped[(grouped['TotalAssets'].notna()) & (grouped['BankAssets'].isna()) & (grouped['Consolidated']==1)]),
                        '(Total Assets Only - Parent Only)': len(grouped[(grouped['TotalAssets'].notna()) & (grouped['BankAssets'].isna()) & (grouped['Consolidated']==0)]),
                        'Sum Bank Assets Only': len(grouped[(grouped['TotalAssets'].isna()) & (grouped['BankAssets'].notna())]), 
                        'No Assets info': len(grouped[(grouped['TotalAssets'].isna()) & (grouped['BankAssets'].isna())]),
                        'Both Assets info': len(grouped[(grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna())]),
                         '(Both Assets info - Consolidated)': len(grouped[(grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna()) & (grouped['Consolidated']==1)]),
                        '(Both Assets info - Parent Only)': len(grouped[(grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna()) & (grouped['Consolidated']==0)])}

    print(f"{len(bhc_assets)} complaints filed to bhc were filed to {len(grouped)} unique bhc-quarter pairs for {grouped['#ID_RSSD'].nunique()} bhcs")
    df_summary = pd.DataFrame([complaint_level, bhc_quarter_level], index=['Complaint Level', 'Company-Quarter Level'])
    print(df_summary.transpose())

    # scatter plot to compare total assets vs. bank assets
    plt.figure(figsize=(8, 6))
    grouped['Consolidated'] = grouped['Consolidated'].map({0: 'Parent-only', 1: 'Consolidated'})
    sns.scatterplot(x='TotalAssets', y='BankAssets', data=grouped, hue='Consolidated', alpha=0.6)

    min_val = min(grouped['TotalAssets'].min(), grouped['BankAssets'].min())
    max_val = max(grouped['TotalAssets'].max(), grouped['BankAssets'].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='x = y')

    plt.xscale('log')
    plt.yscale('log')

    plt.xlabel('Total Assets (log scale)', fontsize=12)
    plt.ylabel('Sum of Bank Subsidiary Assets (log scale)', fontsize=12)
    plt.title('Log-Log Plot: Total vs. Bank Subsidiary Assets (BHC-Quarterly level)', fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'bhc_total_vs_bank_assets.png'))

    plt.figure(figsize=(8, 6))

    # compare means of TotalAssets depending on missingness of BankAssets & report type of TotalAssets (consolidated vs. parent-only)
    grouped['Consolidated'] = grouped['Consolidated'].map({'Parent-only':0, 'Consolidated':1})
    conditions_total = [
        (grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna()) & (grouped['Consolidated'] == 1),
        (grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna()) & (grouped['Consolidated'] == 0),
        (grouped['TotalAssets'].notna()) & (grouped['BankAssets'].isna())  & (grouped['Consolidated'] == 1),
        (grouped['TotalAssets'].notna()) & (grouped['BankAssets'].isna())  & (grouped['Consolidated'] == 0)
    ]
    labels_total = ['Consolidated + BankAssets', 'Parent Only + BankAssets', 
                    'Consolidated + No BankAssets', 'Parent Only + No BankAssets']
    grouped['total_group'] = np.select(conditions_total, labels_total, default="Missing")

    plt.figure(figsize=(10, 6))
    sns.barplot(data=grouped[grouped['total_group'] != 'Missing'], x='total_group', y='TotalAssets')
    plt.yscale('log') 
    plt.title('Total Assets Distribution by Group')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'total_assets_dist_missing_bank_assets.png'))

    # compare means of BankAssets depending on missingness of TotalAssets & report type of TotalAssets (consolidated vs. parent-only)
    conditions_bank = [
    (grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna()) & (grouped['Consolidated'] == 1),
    (grouped['TotalAssets'].notna()) & (grouped['BankAssets'].notna()) & (grouped['Consolidated'] == 0),
    (grouped['TotalAssets'].isna())  & (grouped['BankAssets'].notna())
    ]
    labels_bank = ['Consolidated', '(2) Parent Only', '(3) No TotalAssets']
    grouped['bank_group'] = np.select(conditions_bank, labels_bank, default="Missing")

    plt.figure(figsize=(10, 6))
    sns.barplot(data=grouped[grouped['bank_group'] != 'Missing'], x='bank_group', y='BankAssets')
    plt.yscale('log') 
    plt.title('Bank Assets Distribution by Group')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(cPATH, 'temp', 'bank_assets_dist_missing_total_assets.png'))

def explore_total_assets():
    for company_type in ['bank', 'credit union', 'bank holding company']:
        subset = df[df['Company type']==company_type]
        print(f"total assets of identified for {subset['Total assets'].notna().sum()} out of {len(subset)} complaints filed to {company_type}")
        grouped = subset.groupby(['Quarter sent', 'Company']).agg(complaints=('Company', 'count'), assets=('Total assets', 'mean')).reset_index()
        company_grouped = grouped.groupby(['Company']).agg(complaints=('complaints', 'sum')).reset_index()
        print(f"{len(subset)} complaints filed to {company_type} were filed to {len(grouped)} unique {company_type}-quarter pairs for {len(company_grouped)} {company_type}")
        print(f"out of {len(grouped)} {company_type}-quarter pairs, total assets info exists for {grouped['assets'].notna().sum()} company-quarter pairs")

        company_nan_info = grouped.groupby('Company')['assets'].agg(total_quarters='size', non_nan_quarters='count').reset_index()
        all_nan_companies = company_nan_info[company_nan_info['non_nan_quarters'] == 0]
        print(f"Number of companies with all quarters having missing total assets: {len(all_nan_companies)}")
        all_present_companies = company_nan_info[company_nan_info['non_nan_quarters'] == company_nan_info['total_quarters']]
        print(f"Number of companies with total assets present for ALL quarters: {len(all_present_companies)}")

        ### histogram of the number of quarters in which the complaints were sent to each company
        quarters_per_company = grouped.groupby('Company').size()
        counts = quarters_per_company.value_counts().sort_index()
        plt.figure(figsize=(10, 6))
        plt.bar(counts.index, counts.values, edgecolor='black')
        plt.title('Distribution of number of quarters included in the dataset per company')
        plt.xlabel('Number of quarters')
        plt.ylabel('Number of companies')
        plt.savefig(os.path.join(cPATH, 'temp', f'dist_quarters_per_company_{company_type}.png'))

        ### histogram of the proportion of quarters with total assets information per company
        company_nan_info['non_nan_ratio'] = company_nan_info['non_nan_quarters'] / company_nan_info['total_quarters']
        plt.figure(figsize=(10, 6))
        plt.hist(company_nan_info['non_nan_ratio'], bins=20, edgecolor='black')
        plt.title('Histogram of ratio of quarters with total assets info')
        plt.xlabel('Ratio of quarters with non-missing total assets')
        plt.ylabel('Number of companies')
        plt.savefig(os.path.join(cPATH, 'temp', f'hist_ratio_quarters_with_assets_per_company_{company_type}.png'))

        # histogram of distribution of total assets
        plt.figure(figsize=(10, 6))
        plt.hist(np.log10(grouped['assets']), bins=20, edgecolor='black')
        plt.title('Distribution of total assets (company-quarterly level)')
        plt.xlabel('Total assets')
        plt.ylabel('Density')
        plt.savefig(os.path.join(cPATH, 'temp', f'dist_total_assets_{company_type}.png'))
    
    # histogram of distribution of total assets - bank & bhc combined
    grouped = df[df['Company type'].isin(['bank', 'bank holding company'])].groupby(['Quarter sent', 'Company']).agg(complaints=('Company', 'count'), assets=('Total assets', 'mean')).reset_index()
    bank = df[df['Company type']=='bank'].groupby(['Quarter sent', 'Company']).agg(complaints=('Company', 'count'), assets=('Total assets', 'mean')).reset_index()
    bhc = df[df['Company type']=='bank holding company'].groupby(['Quarter sent', 'Company']).agg(complaints=('Company', 'count'), assets=('Total assets', 'mean')).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    axes[0].hist(np.log10(grouped['assets']), bins=20, color='skyblue', alpha=0.6, label='bank')
    axes[0].set_ylabel('Density')
    axes[0].set_xlabel('Total assets (log scale)')
    axes[0].set_title('Distribution of total assets - bank & bhc combined')
    axes[0].legend()

    axes[1].hist(np.log10(bhc['assets']), bins=20, color='salmon', alpha=0.6, label='bank holding company')
    axes[1].hist(np.log10(bank['assets']), bins=20, color='skyblue', alpha=0.6, label='bank')
    axes[1].set_ylabel('Density')
    axes[1].set_xlabel('Total assets (log scale)')
    axes[1].set_title('Distribution of total assets - bank & bhc separately')
    axes[1].legend()
    save_plot(fig, 'dist_total_assets_bank_bhc_combined.png')

def plot_real_assets(company_type):
    ### plot quarterly trend of real assets for each company 
    subset = df[df['Company type']==company_type]
    grouped = (subset.groupby(['Company', 'Quarter sent']).agg(real_assets=('Log real total assets', 'mean')).reset_index())
    
    plt.figure(figsize=(14, 8))
    for company, group in grouped.groupby('Company'):
        plt.plot(group['Quarter sent'].dt.to_timestamp(), group['real_assets'], label=company, alpha=0.7)

    plt.title(f'Quarterly Log Real Total Assets per Company - {company_type}')
    plt.xlabel('Quarter')
    plt.ylabel('Logarithm of Real Total Assets (2013 USD)')
    plt.xticks(rotation=90)
    plt.savefig(os.path.join(cPATH, 'temp', f'quarterly_real_assets_{company_type}.png'))

    company_means = subset.groupby('Company')['Log real total assets'].mean().reset_index(name='mean_log_assets').sort_values('mean_log_assets', ascending=False)
    print(f"Company order by mean log real assets ({company_type}):")
    print(company_means)

def check_regulation_criterion():
    ### exclusion criteria
    com_quart = df.drop_duplicates(['Company', 'Quarter sent'])
    print("Preparing the dataset for regulation analysis")
    print(f"All data - complaints level: {len(df)}, company-quarter level: {len(com_quart)}")

    # include bank, bank holding company, credit union 
    df_val = df[df['Company type'].isin(['bank', 'bank holding company', 'credit union'])].copy()
    com_quart_val = com_quart[com_quart['Company type'].isin(['bank', 'bank holding company', 'credit union'])].copy()
    print(f"After including only complaints from bank/bhc, credit union-  complaints level: {len(df_val)}, company-quarter level: {len(com_quart_val)}")

    # drop observations before 2012Q2
    df_val = df_val[df_val['Quarter sent'] >= pd.Period('2012Q2')].copy()
    com_quart_val = com_quart_val[com_quart_val['Quarter sent'] >= pd.Period('2012Q2')].copy()
    print(f"After excluding complaints before 2012 Q2 -  complaints level: {len(df_val)}, company-quarter level: {len(com_quart_val)}")

    # drop bhcs with more than one bank within RELV_LVL 2
    df_val = df_val[df_val['BankCount']<2]
    com_quart_val = com_quart_val[com_quart_val['BankCount']<2]
    print(f"After excluding bhcs with more than two banks -  complaints level: {len(df_val)}, company-quarter level: {len(com_quart_val)}")

    # drop observations without total assets information
    df_val = df_val[df_val['Total assets'].notna()]
    com_quart_val = com_quart_val[com_quart_val['Total assets'].notna()]
    print(f"After excluding institutions without total assets information -  complaints level: {len(df_val)}, company-quarter level: {len(com_quart_val)}")
    print(f"Final data size - complaints level: {len(df_val)}, company-quarter level: {len(com_quart_val)}")

    df_val['AssetBin'] = df_val['Total assets'].apply(lambda x: '>10B' if x >= 10e9 else '<10B')
    com_quart_val['AssetBin'] = com_quart_val['Total assets'].apply(lambda x: '>10B' if x >= 10e9 else '<10B')
    
    print("final data statistics in complaints level: ")
    print(pd.crosstab(df_val['AssetBin'], df_val['Regulation'], margins=True))
    print("final data statistics in company-quarter level: ")
    print(pd.crosstab(com_quart_val['AssetBin'], com_quart_val['Regulation'], margins=True))


if __name__ == "__main__":
    ### load dataset
    df = pd.read_csv(os.path.join(cPATH, 'output', 'complaints_processed.csv'), low_memory=False)

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

    ### regulation variable
    df['Regulation'] = df['Regulation'].fillna('NA')

    ### split data into complaints with/without narratives for exploratory analysis
    subdf = df[df['With narrative']] # with narrative
    mssdf = df[~df['With narrative']] # missing narrative

    ### CCPA and CPRA
    CCPA_timeline = {'CCPA enactment': '2018-06-28', 'CCPA implementation': '2020-01-01', 'CPRA amendment': '2020-11-03', 'CPRA implementation': '2023-01-01'}
    CCPA_quarters = {label: pd.to_datetime(date).to_period('Q').strftime('%YQ%q') for label, date in CCPA_timeline.items()}

    ### state-quarterly level plots
    quarter_index = sorted(df['Quarter received'].unique())
    '''
    visualize_duration_categorized()
    visualize_yearly_trend_in_duration()
    visualize_monthly_complaints_counts()
    visualize_yearly_trend_in_company_response()
    
    plot_category_distribution([subdf, mssdf], 'Product', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'temp', 'product_distribution.png'), top_n=10)
    plot_category_distribution([subdf, mssdf], 'Issue', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'temp', 'issue_distribution.png'), top_n=10)
    plot_category_distribution([subdf, mssdf], 'Company response to consumer', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'temp', 'company_response_distribution.png'))
    plot_category_distribution([subdf, mssdf], 'Timely response?', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'temp', 'timely_response_distribution.png'))
    plot_category_distribution([subdf, mssdf], 'State', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'temp', 'state_distribution.png'), top_n=15)

    # examples of consumer complaints narratives related to zombie data
    for i in range(20):
        print(subdf[subdf['Zombie data']==1]['Consumer complaint narrative'].iloc[i])

    ### state-financial bureau level analysis 
    state_index = df['State'].value_counts().index.tolist()
    company_index = df['Company'].value_counts().index.tolist()
    ztab = df[df['Zombie data']==1].groupby(['State', 'Company'], observed=False).size().unstack(fill_value=0).reindex(index=state_index, columns=company_index).fillna(0) # zombie data complaints by state-financial bureau level 
    otab = df[df['Zombie data']==0].groupby(['State', 'Company'], observed=False).size().unstack(fill_value=0).reindex(index=state_index, columns=company_index).fillna(0) # other complaints by state-financial bureau level 
    zrow_sums = ztab.sum(axis=1)
    orow_sums = otab.sum(axis=1)
    zero_zobs_states = zrow_sums[zrow_sums == 0].index  # no zombie data complaints observed in these states
    zero_oobs_states = orow_sums[orow_sums == 0].index  # no other complaints observed in these states
    ztab_prop = (ztab.div(zrow_sums, axis=0)*100).fillna(0).round(0).astype(object) # proportion of complaints filed to each financial bureau for each state
    otab_prop = (otab.div(orow_sums, axis=0)*100).fillna(0).round(0).astype(object)
    for state in zero_zobs_states:
        ztab_prop.loc[state] = ""
        ztab_prop.loc[state, ztab_prop.columns[0]] = "zero complaints in this state"
    for state in zero_oobs_states:
        otab_prop.loc[state] = ""
        otab_prop.loc[state, otab_prop.columns[0]] = "zero complaints in this state"

    with pd.ExcelWriter(os.path.join(cPATH, 'temp', 'state_company.xlsx')) as writer:
        ztab.to_excel(writer, sheet_name='zombie counts')
        otab.to_excel(writer, sheet_name='others counts')
        ztab_prop.to_excel(writer, sheet_name='zombie proportion')
        otab_prop.to_excel(writer, sheet_name='others proportion')

    # size of financial institutes
    explore_bhc_assets()
    explore_total_assets()
    for company_type in ['bank', 'credit union', 'bank holding company']:
        plot_real_assets(company_type)
    '''
    # CFPB regulation
    check_regulation_criterion()
    print("exporation of variables finished")
    