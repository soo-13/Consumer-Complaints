import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns



cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "build")

def save_plot(fig, filename, tight=True):
    out_path = os.path.join(cPATH, 'output', filename)
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
    plt.savefig(os.path.join(cPATH, 'output', 'monthly_complaints_count.png'))
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
    plt.savefig(os.path.join(cPATH, 'output', 'yearly_trend_in_duration.png'))
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
    plt.savefig(os.path.join(cPATH, 'output', 'yearly_trend_in_response.png'))
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
    plt.savefig(os.path.join(cPATH, 'output', 'yearly_trend_in_response_with_without_narratives.png'))

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

def plot_quarterly_trend_zombie_data():
    gp1 = df[df['Zombie data'] == 1].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0)
    gp2 = df[df['Zombie data'] == 0].groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0)
    gp3 = df.groupby(['Quarter received', 'With narrative'], observed=False).size().unstack(fill_value=0)

    # reindex so all plots share the same x-axis
    common_index = sorted(df['Quarter received'].unique())
    gp1 = gp1.reindex(common_index, fill_value=0)
    gp2 = gp2.reindex(common_index, fill_value=0)
    gp3 = gp3.reindex(common_index, fill_value=0)

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
    common_index = sorted(df['Quarter received'].unique())
    gp1z = gp1z.reindex(common_index, fill_value=0)
    gp2z = gp2z.reindex(common_index, fill_value=0)

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


if __name__ == "__main__":
    # load dataset
    df = pd.read_csv(os.path.join(cPATH, 'output', 'complaints_processed.csv'))

    # set dtypes
    df['Date received'] = pd.to_datetime(df['Date received'])
    df['Date sent to company'] = pd.to_datetime(df['Date sent to company'])
    df['Consumer complaint narrative'] = df['Consumer complaint narrative'].astype('string')
    df['Month received'] = pd.to_datetime(df['Month received'])
    df['Quarter received'] = pd.PeriodIndex(df['Quarter received'], freq='Q')
    df['Year received'] = df['Year received'].astype('Int64') 
    df['Quarter sent'] = pd.PeriodIndex(df['Quarter sent'], freq='Q')
    df['Year sent'] = df['Year sent'].astype('Int64')

    # set orders of categorical variables with order 
    duration_order = ['< 1 day', '1 day', '2 days', '3 days', '4 days', '5 days', '6 days', '7 days', 'within two weeks', 
                      'within a month', 'within 90 days', 'within 180 days', 'within a year', 'more than a year']
    df['Duration categorized'] = pd.Categorical(df['Duration categorized'], categories=duration_order, ordered=True)
    group_order = ['< 1 day', 'within a week', 'within a month', 'more than a month']
    df['Duration grouped'] = pd.Categorical(df['Duration grouped'], categories=group_order, ordered=True)
    ccpa_order = ['Pre-CCPA', 'CCPA enacted, pre-implement', 'CCPA implemented, pre-CPRA', 'CPRA amended, pre-implementation', 'CPRA implemented']
    df['CCPA phase at receipt'] = pd.Categorical(df['CCPA phase at receipt'], categories=ccpa_order, ordered=False)
    df['CCPA phase at sent'] = pd.Categorical(df['CCPA phase at sent'], categories=ccpa_order, ordered=False)

    # split data into complaints with/without narratives for exploratory analysis
    subdf = df[df['With narrative']] # with narrative
    mssdf = df[~df['With narrative']] # missing narrative

    # CCPA and CPRA
    CCPA_timeline = {'CCPA enactment': '2018-06-28', 'CCPA implementation': '2020-01-01', 'CPRA amendment': '2020-11-03', 'CPRA implementation': '2023-01-01'}
    CCPA_quarters = {label: pd.to_datetime(date).to_period('Q').strftime('%YQ%q') for label, date in CCPA_timeline.items()}

    # plots
    visualize_duration_categorized()
    visualize_yearly_trend_in_duration()
    visualize_monthly_complaints_counts()
    visualize_yearly_trend_in_company_response()
    plot_quarterly_trend_zombie_data()
    plot_quarterly_trend_zombie_data_CA()

    plot_category_distribution([subdf, mssdf], 'Product', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'output', 'product_distribution.png'), top_n=10)
    plot_category_distribution([subdf, mssdf], 'Issue', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'output', 'issue_distribution.png'), top_n=10)
    plot_category_distribution([subdf, mssdf], 'Company response to consumer', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'output', 'company_response_distribution.png'))
    plot_category_distribution([subdf, mssdf], 'Timely response?', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'output', 'timely_response_distribution.png'))
    plot_category_distribution([subdf, mssdf], 'State', ["With Narratives", "Missing Narratives"], os.path.join(cPATH, 'output', 'state_distribution.png'), top_n=15)

    # examples of consumer complaints narratives related to zombie data
    for i in range(20):
        print(subdf[subdf['Zombie data']==1]['Consumer complaint narrative'].iloc[i])