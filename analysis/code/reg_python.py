import os
import pandas as pd
import statsmodels.formula.api as smf

from itertools import combinations, permutations
from linearmodels.panel import PanelOLS



cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "analysis")

def quarter_str_to_date(qstr):
    year = qstr[:4]
    month = (int(qstr[-1])-1)*3 + 1
    return pd.Timestamp(year=int(year), month=month, day=1)

def exclusion_criteria(df, study_num):
    print(f"Applying inclusion-exclusion criteria for study {study_num}")
    print("Starts with total number of complaints: ", len(df))
    tmp = df[df['Company type'] == 'major credit bureaus'].copy()
    print("Analysis restricted to complaints sent to major credit bureaus:  ", len(tmp))
    tmp['Consumer complaint narrative'] = tmp['Consumer complaint narrative'].str.strip()
    tmp = tmp[tmp['Consumer complaint narrative'].notna()].copy()
    print("Excluding complaints without narratives:  ", len(tmp))

    if study_num == 1:
        tmp = tmp[tmp['Dispute history'] != 'No valid answer'].copy()
        print("Excluding complaints of which LLM failed to classify dispute history:  ", len(tmp))
        tmp['Is CA'] = tmp['State'].apply(lambda x: 'CA' if x == 'CA' else 'Other')
        tmp['Persistent data'] = tmp['Dispute history'].isin(['Prior dispute unresolved', 'Prior dispute resolved but reappeared'])
        tmp['CCPA'] = tmp['Quarter sent'] > '2019-12-31'
        #tmp = tmp[tmp['Dispute history'] != 'Prior dispute resolved but reappeared'].copy()
        #print("temporarily exclude Reappear category with high error rate to see its effect")
        tmp = tmp[tmp['Quarter sent']<'2023-01-01'].copy() # limit the analysis to before 2023 when other states also implement similar state laws
    
    tmp['Quarter sent'] = tmp['Quarter sent'].apply(quarter_str_to_date)
    tmp['Quarter received'] = tmp['Quarter received'].apply(quarter_str_to_date)
    return tmp

def rename_index(idx_list, rename_dict):
    new_index = []
    for name in idx_list:
        if ':' in name: 
            parts = name.split(':')
            new_parts = [rename_dict.get(p, p) for p in parts]
            new_index.append(':'.join(new_parts))
        else:
            new_index.append(rename_dict.get(name, name))
    return new_index

def extract_results(name, res, rename_dict, time_fe=False, entity_fe=False, time_fe_name="Time", entity_fe_name="Entity"):
    if hasattr(res, "bse"):  # statsmodels
        df_res = pd.DataFrame({"coef": res.params, "se": res.bse, "pval": res.pvalues}).assign(model=name)
    else:  # PanelOLS
        df_res = pd.DataFrame({"coef": res.params, "se": res.std_errors, "pval": res.pvalues}).assign(model=name)

    df_res = df_res.assign(**{'model': name, f'{time_fe_name}FE': "Yes" if time_fe else "No", f'{entity_fe_name}FE': "Yes" if entity_fe else "No"})

    # drop variables that are excluded from final report
    df_res = df_res[~df_res.index.str.contains("Quarter_sent")]
    df_res = df_res[~df_res.index.str.contains("Year_sent")]
    df_res = df_res[df_res.index != "Intercept"]
    df_res = df_res[df_res.index != "C(CCPA, Treatment(reference=False))[False]"]

    # rename variables for better readability
    df_res.index = rename_index(df_res.index, rename_dict)
    return df_res
    
def format_latex(df, label="tab:table", caption="Insert caption here", remark = []):
    def stars(p):
        if p < 0.001:
            return "***"
        elif p < 0.01:
            return "**"
        elif p < 0.05:
            return "*"
        else:
            return ""

    df["coef_se"] = df.apply(lambda x: f"\\makecell{{{x['coef']:.3f}{stars(x['pval'])} \\\\ ({x['se']:.3f})}}", axis=1)
    table = df.pivot_table(index=df.index, columns="model", values="coef_se", aggfunc='first')
    table = table.fillna('-')


    fe_rows = {}
    fe_cols = [col for col in df.columns if 'FE' in col]
    models = table.columns
    if 'Yes' in fe_cols:
        for fe in fe_cols:
            fe_rows[fe] = [df[df['model'] == m][fe].iloc[0] for m in models]

    fe_table = pd.DataFrame(fe_rows, index=models).T
    final_table = pd.concat([table, fe_table])
    latex_table = final_table.to_latex(escape=False, column_format="l" + "c" * len(table.columns), multicolumn=True, label=label, caption=caption)

    # add remark
    if len(remark) > 0:
        remark_str = "\n".join(remark)
        latex_table = latex_table.replace(r"\end{tabule}", remark_str + "\end{table}")

    return latex_table


if __name__ == "__main__":
    ### load dataset
    df = pd.read_csv(os.path.join(cPATH, 'input', 'complaints_processed.csv'), low_memory=False)

    ########################### STUDY Preliminary CCPA effect ############################
    ### DV: relief rate, unit of observation: state X quarterly level, treatment: CCPA ###
    ######################################################################################
    '''
    df_val = exclusion_criteria(df, study_num=1)
    df_val.columns = df_val.columns.str.strip()             
    df_val.columns = df_val.columns.str.replace(' ', '_') 

    df_grouped = df_val.groupby(['State', 'Quarter_sent', 'Is_CA', 'CCPA'], as_index=False).agg(relief_rate=('Is_relief', 'mean'))
    df_grouped['Is_CA'] = pd.Categorical(df_grouped['Is_CA'], categories=['CA', 'Other'], ordered=False)

    model1 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other'))", data=df_grouped).fit(cov_type='HC1')
    model2 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other'))", data=df_grouped).fit(cov_type='HC1')
    model3 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) + C(Quarter_sent)", data=df_grouped).fit(cov_type='HC1')
    
    df_panel = df_grouped.set_index(['State', 'Quarter_sent'])
    model4 = PanelOLS.from_formula("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) + EntityEffects", data=df_panel, drop_absorbed=True).fit(cov_type='clustered', cluster_entity=True)
    model5 = PanelOLS.from_formula("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) + EntityEffects + TimeEffects", data=df_panel, drop_absorbed=True).fit(cov_type='clustered', cluster_entity=True)

    rename_dict = {
        "C(CCPA, Treatment(reference=False))[T.True]": "CCPA",
        "C(CCPA, Treatment(reference=False))[True]": "CCPA",
        "C(Is_CA, Treatment(reference='Other'))[T.CA]": "CA",
        }

    df1 = extract_results("model1", model1, rename_dict, time_fe_name='Quarter',  entity_fe_name='State')
    df2 = extract_results("model2", model2, rename_dict, time_fe_name='Quarter',  entity_fe_name='State')
    df3 = extract_results("model3", model3, rename_dict, time_fe=True, time_fe_name='Quarter',  entity_fe_name='State')
    df4 = extract_results("model4", model4, rename_dict, entity_fe=True, time_fe_name='Quarter',  entity_fe_name='State')
    df5 = extract_results("model5", model5, rename_dict, time_fe=True, entity_fe=True, time_fe_name='Quarter',  entity_fe_name='State')

    results_df = pd.concat([df1, df2, df3, df4, df5])
    latex_table = format_latex(results_df)
    print(latex_table)
    '''

    ################################### STUDY 1: CCPA X Persistent data ####################################
    ### DV: relief rate, unit of observation: state X quarterly level, treatment: CCPA X Persistent data ###
    ########################################################################################################
    
    df_val = exclusion_criteria(df, study_num=1)
    df_val.columns = df_val.columns.str.strip()             
    df_val.columns = df_val.columns.str.replace(' ', '_') 

    df_grouped = df_val.groupby(['State', 'Quarter_sent', 'Is_CA', 'CCPA', 'Persistent_data', 'Year_sent'], as_index=False).agg(relief_rate=('Is_relief', 'mean'))
    df_grouped['Is_CA'] = pd.Categorical(df_grouped['Is_CA'], categories=['CA', 'Other'], ordered=False)

    model1 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other')) + C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')
    model2 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) + C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')
    model3 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other')) * C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')
    model4 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Persistent_data, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other'))", data=df_grouped).fit(cov_type='HC1')
    model5 = smf.ols("relief_rate ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) * C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')

    '''
    model4 = smf.ols(
        formula="relief_rate ~  C(Persistent_data, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other')) + C(Quarter_sent) "
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other'))"
                " + C(CCPA, Treatment(reference=False)):C(Persistent_data, Treatment(reference=False))"
                " + C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))",
        data=df_panel,
        ).fit(cov_type='HC1') 
   
    
    df_panel = df_grouped.set_index(['State', 'Quarter_sent'])
    model5 = PanelOLS.from_formula(
        formula="relief_rate ~  C(Persistent_data, Treatment(reference=False)) + C(CCPA, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other'))"
                " + C(CCPA, Treatment(reference=False)):C(Persistent_data, Treatment(reference=False))"
                " + C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + EntityEffects",
        data=df_grouped, 
        drop_absorbed=True
        ).fit(cov_type='clustered', cluster_entity=True)

    model6 = PanelOLS.from_formula(
        formula="relief_rate ~  C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other'))"
                " + C(CCPA, Treatment(reference=False)):C(Persistent_data, Treatment(reference=False))"
                " + C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + EntityEffects + TimeEffects",
        data=df_grouped, 
        drop_absorbed=True
        ).fit(cov_type='clustered', cluster_entity=True)
    '''
    rename_dict = {
        "C(CCPA, Treatment(reference=False))[T.True]": "CCPA",
        "C(CCPA, Treatment(reference=False))[True]": "CCPA",
        "C(Is_CA, Treatment(reference='Other'))[T.CA]": "CA",
        "C(Is_CA, Treatment(reference='Other'))[CA]": "CA",
        "C(Persistent_data, Treatment(reference=False))[T.True]": "PersistentData",
        "C(Persistent_data, Treatment(reference=False))[True]": "PersistentData"
        }


    df1 = extract_results("model1", model1, rename_dict)
    df2 = extract_results("model2", model2, rename_dict)
    df3 = extract_results("model3", model3, rename_dict)
    df4 = extract_results("model4", model4, rename_dict)
    df5 = extract_results("model5", model5, rename_dict)
    results_df = pd.concat([df1, df2, df3, df4, df5])

    remark = [r"\begin{tablenotes}", r"\scriptsize", r"\item \textit{Notes}: Robust standard errors in parentheses. $^{*}p<0.05$, $^{**}p<0.01$, $^{***}p<0.001$.", r"\end{tablenotes}"]
    latex_table = format_latex(results_df, label='tab:t1', caption="The CCPA effect on relief rate for first-time and persistent data complaint", remark=remark)
    print(latex_table)

    ########################################### STUDY 1: CCPA X Persistent data ###########################################
    ### DV: #complaints per population, unit of observation: state X quarterly level, treatment: CCPA X Persistent data ###
    #######################################################################################################################
    df_val = exclusion_criteria(df, study_num=1)
    df_val = df_val[df_val['Population_state'].notna()].copy()
    df_val['CCPA'] = (df_val['Quarter received'] > pd.Timestamp('2019-12-31')).astype(int)
    df_val.columns = df_val.columns.str.strip()             
    df_val.columns = df_val.columns.str.replace(' ', '_') 

    df_grouped = df_val.groupby(['State', 'Quarter_received', 'Is_CA', 'CCPA'], as_index=False).agg(count=('Is relief', 'size'), pop=('Population_state', 'first')) # unit of observation
    df_grouped['Is_CA'] = pd.Categorical(df_grouped['Is_CA'], categories=['CA', 'Other'], ordered=False)
    df_grouped['count_per_pop'] = df_grouped['count']/df_grouped['pop']

    model1 = smf.ols("count_per_pop ~ C(CCPA, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other')) + C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')
    model2 = smf.ols("count_per_pop ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) + C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')
    model3 = smf.ols("count_per_pop ~ C(CCPA, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other')) * C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')
    model4 = smf.ols("count_per_pop ~ C(CCPA, Treatment(reference=False)) * C(Persistent_data, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other'))", data=df_grouped).fit(cov_type='HC1')
    model5 = smf.ols("count_per_pop ~ C(CCPA, Treatment(reference=False)) * C(Is_CA, Treatment(reference='Other')) * C(Persistent_data, Treatment(reference=False))", data=df_grouped).fit(cov_type='HC1')

    '''
    model4 = smf.ols(
        formula="relief_rate ~  C(Persistent_data, Treatment(reference=False)) + C(Is_CA, Treatment(reference='Other')) + C(Quarter_sent) "
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other'))"
                " + C(CCPA, Treatment(reference=False)):C(Persistent_data, Treatment(reference=False))"
                " + C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))",
        data=df_panel,
        ).fit(cov_type='HC1') 
   
    
    df_panel = df_grouped.set_index(['State', 'Quarter_sent'])
    model5 = PanelOLS.from_formula(
        formula="relief_rate ~  C(Persistent_data, Treatment(reference=False)) + C(CCPA, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other'))"
                " + C(CCPA, Treatment(reference=False)):C(Persistent_data, Treatment(reference=False))"
                " + C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + EntityEffects",
        data=df_grouped, 
        drop_absorbed=True
        ).fit(cov_type='clustered', cluster_entity=True)

    model6 = PanelOLS.from_formula(
        formula="relief_rate ~  C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + C(CCPA, Treatment(reference=False)):C(Is_CA, Treatment(reference='Other'))"
                " + C(CCPA, Treatment(reference=False)):C(Persistent_data, Treatment(reference=False))"
                " + C(Is_CA, Treatment(reference='Other')):C(Persistent_data, Treatment(reference=False))"
                " + EntityEffects + TimeEffects",
        data=df_grouped, 
        drop_absorbed=True
        ).fit(cov_type='clustered', cluster_entity=True)
    '''
    rename_dict = {
        "C(CCPA, Treatment(reference=False))[T.True]": "CCPA",
        "C(CCPA, Treatment(reference=False))[True]": "CCPA",
        "C(Is_CA, Treatment(reference='Other'))[T.CA]": "CA",
        "C(Is_CA, Treatment(reference='Other'))[CA]": "CA",
        "C(Persistent_data, Treatment(reference=False))[T.True]": "PersistentData",
        "C(Persistent_data, Treatment(reference=False))[True]": "PersistentData"
        }


    df1 = extract_results("model1", model1, rename_dict)
    df2 = extract_results("model2", model2, rename_dict)
    df3 = extract_results("model3", model3, rename_dict)
    df4 = extract_results("model4", model4, rename_dict)
    df5 = extract_results("model5", model5, rename_dict)
    results_df = pd.concat([df1, df2, df3, df4, df5])

    remark = [r"\begin{tablenotes}", r"\scriptsize", r"\item \textit{Notes}: Robust standard errors in parentheses. $^{*}p<0.05$, $^{**}p<0.01$, $^{***}p<0.001$.", r"\end{tablenotes}"]
    latex_table = format_latex(results_df, label='tab:t1', caption="The CCPA effect on relief rate for first-time and persistent data complaint", remark=remark)
    print(latex_table)
