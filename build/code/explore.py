import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns



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

def explore_total_assets():
    for company_type in ['bank', 'credit union']:
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

def plot_complaints_and_response_per_size_company_quarter_level(company_type):
    subset = df[df['Company type']==company_type]
    subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

    grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'),reliefs=('is_relief', 'sum'), total_assets=('Log real total assets', 'mean')).reset_index())
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
        subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

        grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'), reliefs=('is_relief', 'sum'), total_assets=('Log real total assets', 'mean')).reset_index())
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

    palette = {'bank': 'blue', 'credit union': 'orange'}
    for company_type in ['bank', 'credit union']:
        subset = df[df['Company type']==company_type]
        subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])
        grouped = subset.groupby(['Company']).agg(complaints=('Company', 'count'), reliefs=('is_relief', 'sum'), assets=('Log real total assets', 'mean')).reset_index()
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
        for company_type in ['bank', 'credit union']:
            subset = df[(df['Company type']==company_type) &  (df['Zombie data']==i)]
            subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

            grouped = subset.groupby(['Company']).agg(complaints=('Company', 'count'), reliefs=('is_relief', 'sum'), assets=('Log real total assets', 'mean')).reset_index()
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
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for i, company_type in enumerate(['bank', 'credit union']):
        subset = df[df['Company type']==company_type]
        subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

        grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'),reliefs=('is_relief', 'sum')).reset_index())
        grouped['relief_rate'] = grouped['reliefs'] / grouped['complaints']
        grouped['log_complaints'] = np.log1p(grouped['complaints'])

        ### x: complaint counts, y2: relief probability, color: company (to approximately observe company effect)
        sns.scatterplot(data=grouped, x='log_complaints', y='relief_rate', hue='Company', palette='husl', legend=False, ax=axes[i], alpha=0.6)

        axes[i].set_ylabel('Relief probability per quarter-company')
        axes[i].set_title(f'{company_type} - Log Complaint Counts vs Relief probability')

    axes[1].set_xlabel('Logarithm of Complaint Counts')
    save_plot(fig, 'relief_per_complaints_company_quarterly_level.png')

    ### left panels: other compalints, right panel: zombie related complaints (same plot with previous one)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True)
    zombie_title = {0: 'Other Complaints', 1: 'Zombie Data Complaints'}
    for i in range(2):
        for j, company_type in enumerate(['bank', 'credit union']):
            subset = df[(df['Company type'] == company_type) & (df['Zombie data'] == i)]
            subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

            grouped = (subset.groupby(['Company', 'Quarter sent']).agg(complaints=('Company', 'count'), reliefs=('is_relief', 'sum')).reset_index())
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
    subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])
    grouped = subset.groupby(['Company', 'Company type']).agg(complaints=('Company', 'count'), reliefs=('is_relief', 'sum')).reset_index()
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
        subset['is_relief'] = subset['Company response to consumer'].isin(['Closed with non-monetary relief','Closed with monetary relief'])

        grouped = subset.groupby(['Company', 'Company type']).agg(complaints=('Company', 'count'), reliefs=('is_relief', 'sum')).reset_index()
        grouped['relief_rate'] = grouped['reliefs']/grouped['complaints']
        grouped['log_complaints'] = np.log1p(grouped['complaints'])

        sns.scatterplot(data=grouped, x='log_complaints', y='relief_rate', hue='Company type', palette='colorblind', legend=True, ax=axes[i], alpha=0.6)

        axes[i].set_title(f"{zombie_title[i]} | Log Complaints Counts vs. Relief Probability")
        axes[i].set_ylabel('Relief probability (company-quarter level)')
    axes[1].set_xlabel('Log complaint counts(company-quarter level)')
    save_plot(fig, 'relief_per_complaints_company_level_zombie.png')  
    
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
    plot_quarterly_trend_zombie_data()
    plot_quarterly_trend_zombie_data_CA()
    plot_quarterly_trend_zombie_data_most_complaints_states()

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

    plot_quarterly_companies_in_top_states(5)
    plot_company_type(5)
    '''
    explore_total_assets()
    plot_real_assets('bank')
    plot_real_assets('credit union')

    plot_complaints_and_response_per_size_company_quarter_level('bank')
    plot_complaints_and_response_per_size_company_quarter_level('credit union')
    plot_complaints_and_response_per_size_company_level()
    plot_response_per_complaint_count_company_quarterly_level()
    plot_response_per_complaint_count()
    print("exploratory analysis finished")
    