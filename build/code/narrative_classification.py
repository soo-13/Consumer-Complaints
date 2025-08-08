import os
import re
import random
import torch
import numpy as np
import pandas as pd

from itertools import combinations
from tqdm import tqdm
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, set_seed, AutoModelForCausalLM
from sklearn.model_selection import train_test_split

import torch
print(torch.cuda.is_available())  
print(torch.cuda.current_device()) 
print(torch.cuda.get_device_name(0)) 

#cPATH = os.path.join("/Users", "yeonsoo","Dropbox (MIT)", "Projects", "consumer_complaints", "build")
cPATH = os.path.join("/home", "yeonsoo", "consumer_complaints", "build") # ORCD path
pPATH = os.path.join("/pool001/", "yeonsoo", "consumer_complaints", "build")

seed = 1234
torch.manual_seed(seed)
np.random.seed(seed)
random.seed(seed)
set_seed(seed)  


def load_data(compact=False, override=False):
    if compact:
        if not os.path.exists(os.path.join(cPATH, 'temp', 'complaints_narratives_compact.csv')) or override:
            df_ext = pd.read_csv(os.path.join(cPATH, 'temp', 'complaints_narratives.csv'))
            print(df_ext.columns)
            ncss_cols = ['Date received', 'ZIP code', 'Product', 'Issue', 'Sub-issue', 'Consumer complaint narrative', 'Complaint ID', 'Year received', 'Zombie data', 'Date sent to company', 'Company response to consumer', 'Consumer disputed?', 'Quarter received', 'CCPA phase at receipt', 'CCPA phase at sent', 'Is relief', 'Duration sending', 'Company type', 'State privacy law', 'zip', 'MedIncome', 'Population', 'fips', 'RealMedIncome', 'EDUCpop', 'EDUC<9', 'EDUC9-12', 'EDUChsg', 'EDUCcll', 'EDUCassc', 'EDUCbch', 'EDUCgrad']
            df = df_ext[ncss_cols]
            df.to_csv(os.path.join(cPATH, 'temp', 'complaints_narratives_compact.csv'), index=False)
            print("compact version of narrative data saved as complaints_narratives_compact.csv")
        else:
            df = pd.read_csv(os.path.join(cPATH, 'temp', 'complaints_narratives_compact.csv'), low_memory=False)
    else:
       df = pd.read_csv(os.path.join(cPATH, 'temp', 'complaints_narratives.csv'), low_memory=False)
    return df

def deleted_but_reappears(narr):
    keywords = [
        r"\b(reappear(ed)?|reappearing)\b",
        r"\b(show(ed)? up again|came back|returned)\b",
        r"\b(reinsert(ed)?|re-insert(ed)?|put\s+back|add(ed)?\s+again|place(d)?\s+back)\b",
        r"\b(put\s+\w+\s+back|add(ed)?\s+\w+\s+again|placed\s+\w+\s+back)\b",
        r"\b(resuscitated)\b",
        r"\b(reappearance|reinsertion)\b",
        r"\b(re-report(ed)?|re-reporting|re\s+report(ed)?|re\s+reporting)\b",
        r"\b(previous(ly)? deleted)\b"
        ]
        # previously in dispute Now resolved, continues to add and remove,  repeated updates 
        # returned: too much false positive
    return int(any(re.search(kw, narr.strip().lower()) for kw in keywords))

def wrong_info_never_deleted(narr):
    keywords = [
        r"\b(not\s+removed|never\s+removed|not\s+deleted|never\s+deleted|not\s+corrected|never\s+corrected)\b",
        r"\b(not\s+fixed|never\s+fixed|not\s+resolved|never\s+resolved|not\s+changed|never\s+changed)\b",
        r"\b(error\s+still\s+exists|error\s+remains|error\s+not\s+corrected)\b",
        r"\b(incorrect|inaccurate|wrong|false|erroneous)\b.*\b(still|remains|persist(s|ed)?)\b",
        r"\b(dispute|complaint|request)\b.*\b(ignored|dismissed|denied|not\s+addressed|not\s+resolved)\b",
        r"\b(no\s+action\s+taken|no\s+correction|no\s+change)\b",
        r"\b(still\s+report(ed)?|still\s+listed|still\s+show(s|ed)?)\b",
        r"\b(previously\s+disputed|formerly\s+dsiputed|previous\s+dispute|former\s+dispute)\b"
        ]
    return int(any(re.search(kw, narr.strip().lower()) for kw in keywords))

def right_but_oudated_info_never_deleted(narr):
    keywords = [
        r"\b(outdated|old|expired)\b",
        r"\b(year(s)?\s+old)\b"
        r"\b(past\s+(due|retention|reporting|deletion)\s+(date|period|deadline|time))\b",
        r"\b(should\s+be\s+removed|required\s+to\s+delete|obligated\s+to\s+remove|mandated\s+to\s+delete)\b",
        r"\b(violation\s+of\s+retention\s+policy|reporting\s+period\s+expired)\b",
        r"\b(too\s+old\s+to\s+report|beyond\s+allowed\s+timeframe)\b",
        r"\b(credit\s+reporting\s+rules|federal\s+regulations|compliance\s+issues)\b.*\b(outdated)\b",
        r"\b(should\s+have\s+been\s+deleted|failed\s+to\s+remove\s+after\s+period)\b",
        r"\b(should\s+no\s+longer+\sappear)"
        ]
    return int(any(re.search(kw, narr.strip().lower()) for kw in keywords))

def identify_theft(narr):
    keywords = [
        r"\b(identity\s+theft|identity\s+fraud|stolen\s+identity|identity\s+stolen)\b",
        r"\b(fraudulent\s+account|unauthorized\s+account|unauthorized\s+activity)\b",
        r"\b(fraud|scam|fraudulent)\b"
    ]
    return int(any(re.search(kw, narr.strip().lower()) for kw in keywords))

def test_keyword_matching():
    test_cases = [
        "Nothing happened. Should not return anything",
        "The error was fixed but reappeared again.",
        "They removed the account but then it was added again.",
        "It came back after being resolved.",
        "they re reported the error",
        "it was previously deleted",
        "they placed it back again",
        "I am a victim of identity theft"
        ]

    for t in test_cases:
        print(deleted_but_reappears(t))

def rule_based_matching(savepath=os.path.join(cPATH, 'temp', 'narrative_classified.csv'), override=False):
    if not os.path.exists(savepath) or override:
        df = load_data(compact=True, override=False)
        print("raw data loaded! Start classification")

        df["Reappear"] = df["Consumer complaint narrative"].apply(deleted_but_reappears)
        df["Outdated"] = df["Consumer complaint narrative"].apply(right_but_oudated_info_never_deleted)
        df["NoResolution"] = df["Consumer complaint narrative"].apply(wrong_info_never_deleted)
        df["IdentityTheft"] = df["Consumer complaint narrative"].apply(identify_theft)
        df.to_csv(os.path.join(cPATH, 'temp', 'narrative_classified.csv'), index=False)
    else:
        df = pd.read_csv(savepath)
    return df

def stats_and_validation(df, savepath):
    print(f"{df['Reappear'].sum()}/{len(df)} ({df['Reappear'].sum()/len(df)*100:2f}%) complaints with narratives are related to deleted info reappearing")
    print(f"{df['Outdated'].sum()}/{len(df)} ({df['Outdated'].sum()/len(df)*100:2f}%) complaints with narratives are related to outdated info never deleted")
    print(f"{df['NoResolution'].sum()}/{len(df)} ({df['NoResolution'].sum()/len(df)*100:2f}%) complaints with narratives are related to wrong info never deleted")
    print(f"{df['IdentityTheft'].sum()}/{len(df)} ({df['IdentityTheft'].sum()/len(df)*100:2f}%) complaints with narratives are related to identity theft")

    # count how many complaints fall into intersections
    categories = ["Reappear", "Outdated", "NoResolution", "IdentityTheft"]
    for cat in categories:
        print(f"{cat}: {df[cat].sum()}")
    for r in range(2, len(categories)+1):
        for comb in combinations(categories, r):
            intersect_count = df[list(comb)].all(axis=1).sum()
            print(f"{' & '.join(comb)}: {intersect_count}")

    cond1 = (df['Issue'] == 'Incorrect information on your report') & (df['Sub-issue'] == 'Old information reappears or never goes away')
    cond2 = (df['Issue'] == 'Incorrect information on credit report') & (df['Sub-issue'] == 'Reinserted previously deleted info')
    cond3 = (df['Issue'] == "Problem with a company's investigation into an existing problem") & (df['Sub-issue']=='Their investigation did not fix an error on your report')
    cond4 = (df['Issue'] == "Problem with a credit reporting company's investigation into an existing problem") & (df['Sub-issue']=='Their investigation did not fix an error on your report')
    cond5 = (df['Issue'] == "Problem with a company's investigation into an existing issue") & (df['Sub-issue']=='Their investigation did not fix an error on your report')
    df.loc[cond1 | cond2 | cond3 | cond4 | cond5, 'RTBF'] = 1 # issues/sub-issues that can potentially be related to the right to be forgotten

    df['Condition'] = 'None of the above'
    df.loc[cond1, 'Condition'] = 'Old information reappears or never goes away'
    df.loc[cond2, 'Condition'] = 'Reinserted previously deleted info'
    df.loc[cond3 | cond4 | cond5, 'Condition'] = 'Their investigation did not fix an error on your report'

    gp_issue = df.groupby('Issue').agg(total=('Reappear', 'size'), Reappear=('Reappear', 'sum'), Outdated=('Outdated', 'sum'), 
                            NoResolution=('NoResolution', 'sum'), IdentityTheft=('IdentityTheft', 'sum')).reset_index()
    gp_issue.to_csv(os.path.join(savepath, 'stats_groupby_issue.csv'), index=False)

    gr_cond = df.groupby('Condition').agg(total=('Reappear', 'size'), Reappear=('Reappear', 'sum'), Outdated=('Outdated', 'sum'), 
                            NoResolution=('NoResolution', 'sum'), IdentityTheft=('IdentityTheft', 'sum')).reset_index()
    gr_cond.to_csv(os.path.join(savepath, 'stats_groupby_condition.csv'), index=False)


    df[df['Reappear']==1].to_csv(os.path.join(savepath, 'deleted_but_reappear.csv'), index=False)
    df[df['Outdated']==1].to_csv(os.path.join(savepath, 'outdated_never_deleted.csv'), index=False)
    df[df['NoResolution']==1].to_csv(os.path.join(savepath, 'wrong_info_never_deleted.csv'), index=False)
    df[df['IdentityTheft']==1].to_csv(os.path.join(savepath, 'identity_theft.csv'), index=False)

    df[(df['Reappear']==0) & (df['Outdated']==0) & (df['NoResolution']==0) & (df['RTBF']==1)].to_csv(os.path.join(savepath, 'RTBF_not_classified.csv'), index=False)

    df[(df['Reappear']==1) & (df['RTBF']==1)].to_csv(os.path.join(savepath, 'RTBF_deleted_but_reappear.csv'), index=False)
    df[(df['Outdated']==1) & (df['RTBF']==1)].to_csv(os.path.join(savepath, 'RTBF_outdated_never_deleted.csv'), index=False)
    df[(df['NoResolution']==1) & (df['RTBF']==1)].to_csv(os.path.join(savepath, 'RTBF_wrong_info_never_deleted.csv'), index=False)
    df[(df['IdentityTheft']==1) & (df['RTBF']==1)].to_csv(os.path.join(savepath, 'RTBF_identity_theft.csv'), index=False)

def generate_sample_dataset_with_label(df, savepath):
    # generate sample dataset with label to test the performance of language models - the labels are ADJUSTED MANUALLY AFTERWARD to ensure the label accuracy
    candidate_labels = ["Disputed info reappears after deletion", "Incorrect info never deleted", "Outdated info never removed", "Not related to right to be forgotten"]
    df.loc[(df['Condition']=='Reinserted previously deleted info'), 'Answer (Machine-generated)'] = "Disputed info reappears after deletion"
    df.loc[(df['Condition']=='Old information reappears or never goes away'), 'Answer (Machine-generated)'] = "Outdated info never removed"
    df.loc[(df['Condition']=='Their investigation did not fix an error on your report'), 'Answer (Machine-generated)'] = "Incorrect info never deleted"
    df.loc[(df['Condition']=='None of the above'), 'Answer (Machine-generated)'] = "Not related to right to be forgotten"

    new_df = []
    for label in candidate_labels:
        sample = df[df['Answer (Machine-generated)'] == label].sample(n=50, random_state=42)
        new_df.append(sample)
    new_df = pd.concat(new_df).reset_index(drop=True)
    new_df = new_df[['Issue', 'Sub-issue', 'Consumer complaint narrative', 'Complaint ID', 'Answer (Machine-generated)']]
    new_df.to_csv(savepath, index=False)

def mutually_exclusive_collectively_exhaustive_label(savepath, seed=1234):
    '''
    classify complaints into mutually exclusive and collectively exhaustive categories as follows: 
    - complaints about removing information that should be deleted
        - information does not belongs to me
            - (0) result of identity theft
            - (1) it removed it after a dispute but came back
            - (2) it never got deleted despite multiple disputes
            - (3) first time dispute
        - (4) information belongs to me but should be deleted because it is outdated
    - (5) complaints that are not about removing information that should be removed
    '''
    df = load_data(compact=True)
    mcb = df[df['Company type']=='major credit bureaus'].copy()

    cond0 = mcb['Sub-issue']=='Debt was result of identity theft'
    cond1 = (mcb['Issue'] == 'Incorrect information on credit report') & (mcb['Sub-issue'] == 'Reinserted previously deleted info')
    cond2_1 = (mcb['Issue'] == "Problem with a company's investigation into an existing problem") & (mcb['Sub-issue']=='Their investigation did not fix an error on your report')
    cond2_2 = (mcb['Issue'] == "Problem with a credit reporting company's investigation into an existing problem") & (mcb['Sub-issue']=='Their investigation did not fix an error on your report')
    cond2_3 = (mcb['Issue'] == "Problem with a company's investigation into an existing issue") & (mcb['Sub-issue']=='Their investigation did not fix an error on your report')
    cond3 = (mcb['Issue']=='Incorrect information on your report') & (mcb['Sub-issue'] != 'Old information reappears or never goes away')
    cond4 = (mcb['Issue'] == 'Incorrect information on your report') & (mcb['Sub-issue'] == 'Old information reappears or never goes away')

    mcb['temp label'] = 'Others'
    mcb.loc[cond0, 'temp label'] = 'Identity theft'
    mcb.loc[cond1, 'temp label'] = 'Reappear after deletion'
    mcb.loc[cond2_1 |cond2_2 | cond2_3, 'temp label'] = 'Not my info persists'
    mcb.loc[cond3, 'temp label'] = 'Not my info'
    mcb.loc[cond4, 'temp label'] = 'My info that should be removed'
    mcb['Answer'] = mcb['temp label']

    sample = []
    candidate_labels = ['Identity theft', 'Reappear after deletion', 'Not my info persists', 'Not my info', 'My info that should be removed', 'Others']
    for label in candidate_labels:
        tmp = mcb[mcb['temp label'] == label].sample(n=30, random_state=seed)
        sample.append(tmp)
    sample = pd.concat(sample).reset_index(drop=True)
    sample = sample[['Issue', 'Sub-issue', 'Consumer complaint narrative', 'Complaint ID', 'temp label', 'Answer']]
    sample.to_csv(savepath, index=False)

def transformer_zero_shot_sample(df, model, candidate_labels, savepath, multi_label=False, batch_size=8, threshold=0.5):
    classifier = pipeline("zero-shot-classification", model=model, framework='pt', device=0)
    print("Model loaded!")

    results = []
    print(f"Starting classification for {len(df)//batch_size} batches (batch_size: {batch_size}, datapoints: {len(df)})")
    
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size].copy()
        sequences = batch['Consumer complaint narrative'].tolist()

        res = classifier(sequences, candidate_labels=candidate_labels, multi_label=multi_label)

        if multi_label:
            for label in candidate_labels:
                batch[label] = [dict(zip(r['labels'], r['scores'])).get(label, 0) for r in res]
    
            batch_pred = []
            batch_score = []
            for r in res:
                label_score_dict = dict(zip(r['labels'], r['scores']))
                max_label = max(label_score_dict, key=label_score_dict.get)
                max_score = label_score_dict[max_label]
                batch_score.append(max_score)
                if all(score < threshold for score in label_score_dict.values()):
                    batch_pred.append('Others')
                else:
                    batch_pred.append(max_label)
            batch['predicted_label'] = batch_pred
            batch['score'] = batch_score
            results.append(batch)
            
        else:
            batch['predicted_label'] = [r['labels'][0] for r in res]
            batch['score'] = [r['scores'][0] for r in res]
            results.append(batch)

        if i%10==0:
            print(f"{i}-th datapoint classified")


    results = pd.concat(results).reset_index(drop=True)
    results.to_csv(savepath, index=False)
    print(f"Classification complete!")

def save_ml_model(savepath, model_name="valhalla/distilbart-mnli-12-3"):
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    os.makedirs(os.path.join(savepath, model_name), exist_ok=True)
    model.save_pretrained(os.path.join(savepath, model_name))
    tokenizer.save_pretrained(os.path.join(savepath, model_name))

def evaluate_ml_prediction(candidate_label, org_label, meaning, savepath):
    df = pd.read_csv(savepath)
    df = df.dropna(how='all') 

    ans_map = dict(zip(org_label, meaning))

    pred_map = dict(zip(candidate_label[:4], meaning))
    if len(candidate_label) > 4:
        for label in candidate_label[4:]:
            pred_map[label] = "Others"

    df['Answer'] = df['Answer'].astype(str).str.strip().map(ans_map)
    df['predicted_label'] = df['predicted_label'].fillna('').str.strip().str.split('\n').str[0].apply(lambda x: x[4:] if x not in candidate_label and len(x) >= 4 else x)
    df['predicted_label'] = df['predicted_label'].map(pred_map)

    print(f"Evaluating classification performance: {savepath}")

    correct = (df['Answer'] == df['predicted_label']).sum()
    total = len(df)
    print(f"{correct}/{total} ({correct/total*100:.2f}%) classified accurately")

    print("\nMisclassification Breakdown (Answer vs. Predicted):")
    print(pd.crosstab(df['Answer'], df['predicted_label'], rownames=['True Label'], colnames=['Predicted Label'], dropna=False))

def evaluate_ml_prediction_multilabel(candidate_label, org_label, meaning, savepath):
    df = pd.read_csv(savepath)
    df = df.dropna(how='all') 

    ans_map = dict(zip(org_label, meaning))
    pred_map = dict(zip(candidate_label + ["Others"], meaning))

    df['Answer'] = df['Answer'].map(ans_map)
    df['predicted_label'] = df['predicted_label'].map(pred_map)

    print(f"Evaluating classification performance: {savepath}")

    correct = (df['Answer'] == df['predicted_label']).sum()
    total = len(df)
    print(f"{correct}/{total} ({correct/total*100:.2f}%) classified accurately")

    print("\nMisclassification Breakdown based on max prediction score (Answer vs. Predicted):")
    print(pd.crosstab(df['Answer'], df['predicted_label'], rownames=['True Label'], colnames=['Predicted Label'], dropna=False))

    for i, label in enumerate(candidate_label):
        df[f'{label}_true'] = (df['Answer'] == meaning[i])
        df[f'{label}_pred'] = (df[label] > 0.5)
        print(f"\nMisclassification Breakdown based on binary classification of label: {label}")
        print(pd.crosstab(df[f'{label}_true'], df[f'{label}_pred'], rownames=['True Value'], colnames=['Prediction'], dropna=False))
        tn = df[(df[f'{label}_true'])&(~df[f'{label}_pred'])]
        fp = df[(~df[f'{label}_true'])&(df[f'{label}_pred'])]

def generate_prompts(df, general_prompt, candidate_label=[], len_example=0, include_issue=False, suffix="", seed=1234):
    print(f"Generating Prompt with {len_example} examples")
    random.seed(seed)
    org_label = ["Disputed info reappears after deletion", "Incorrect info never deleted", "Outdated info never removed", "Not related to right to be forgotten"]
    label_map = dict(zip(org_label, candidate_label))

    if include_issue:
        df['Issue'] = df['Issue'].fillna("")
        df['Sub-issue'] = df['Sub-issue'].fillna("")
        df['Consumer complaint narrative'] = ('Complaint narrative: ' + df['Consumer complaint narrative'] + '\nIssue: ' + df['Issue'] + '\nSub-issue: ' + df['Sub-issue'])

    if len_example > 0:
        exampledf = df[df['Sample type']=='Train'].dropna(how='all')
        examples = exampledf['Consumer complaint narrative'].tolist()
        example_labels = exampledf['Answer'].dropna()
        questionsdf = df[df['Sample type']=='Test'].dropna(how='all')

        if len(candidate_label) > 0:
            example_labels = example_labels.map(label_map).tolist()
        else:
            example_labels = example_labels.tolist()
    else:
        questionsdf = df.dropna(how='all')

    questions = questionsdf['Consumer complaint narrative'].tolist()
    complaintID = questionsdf['Complaint ID'].tolist()
    if not 'Answer' in questionsdf.columns:
        questionsdf['Answer'] = ""
    answers = questionsdf['Answer']
    answers = answers.tolist()
    
    prompts = []
    for question in questions:
        prompt_parts = [general_prompt.strip(), ""]

        if len_example > 0:
            sample_idx = random.sample(range(len(examples)), len_example)
            for j, idx in enumerate(sample_idx):
                prompt_parts.append(f"Example {j}: {examples[idx].strip()}")
                prompt_parts.append(f"Answer {j}: {example_labels[idx].strip()}")

        prompt_parts.append(f"Question: {question.strip()}")
        prompt_parts.append(f"Answer:")
        if len(suffix)>0:
            prompt_parts.append(suffix)
        
        prompt = "\n".join(prompt_parts)
        prompts.append(prompt)
    print("Prompt generation complete!")
    
    return pd.DataFrame({'Consumer complaint narrative': questions, 'Answer': answers, 'Prompts': prompts, 'Complaint ID': complaintID})

def load_llama_model(do_sample=False):
    model_id = "meta-llama/Llama-3.1-8B"
    generator = pipeline("text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, device_map="auto", do_sample=do_sample)
    print("Model loaded!")
    return generator

def llama_predict(promptsdf, generator, savepath, batch_size=64, max_length=50):
    prompts = promptsdf['Prompts']
    print(f"Starting generating answers for {len(prompts)} questions ({len(prompts)//batch_size} batches)")

    results = []
    for i in tqdm(range(0, len(prompts), batch_size)):
        batch_prompts = prompts[i:i + batch_size].tolist()
        #inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True).to(model.device)
        #print(f"Tokenization complete for the {i//batch_size+1}-th batch")
        
        #with torch.no_grad():
        #    outputs = model.generate(**inputs, max_new_tokens=max_length, do_sample=False, eos_token_id=tokenizer.eos_token_id)
        try:
            outputs = generator(batch_prompts, max_new_tokens=max_length, do_sample=False)
        except Exception as e:
            print(f"Error at batch {i//batch_size+1}: {e}")
            results.extend(["[ERROR]"] * len(batch_prompts))
            continue

        for j, out in enumerate(outputs):
            generated_text = out[0]["generated_text"]
            prompt_text = batch_prompts[j]
            generated_only = generated_text[len(prompt_text):].strip()  # remove prompt part
            results.append(generated_only)
            #full_decoded = tokenizer.decode(output_ids, skip_special_tokens=True)
            #prompt_text = batch_prompts[j]
            #generated_only = full_decoded[len(prompt_text):].strip()  # remove prompt part
            #results.append(generated_only)

        if (i//batch_size)%10==0:
            print(f"{i//batch_size+1}-th datapoint classified")

    promptsdf['predicted_label'] = results
    promptsdf.to_csv(savepath, index=False)
    print(f"Classification complete!")

def train_test_split_for_fsl(df, sample, test_size= 0.8, seed=1234):
    sample = sample.merge(df[['Complaint ID', 'Company type']], how='left', on='Complaint ID')
    sample_mcb = sample[sample['Company type']=='major credit bureaus']
    print(f"{len(sample_mcb)} samples are complaints filed to credit bureaus")
    print(sample_mcb['Answer'].value_counts())

    train, test = train_test_split(sample_mcb, test_size=test_size, stratify=sample_mcb['Answer'],random_state=seed)
    train['Sample type'] = 'Train'
    test['Sample type'] = 'Test'

    print(f"\nTrain set size: {len(train)}")
    print(train['Answer'].value_counts())
    print(f"\nTest set size: {len(test)}")
    print(test['Answer'].value_counts())

    return pd.concat([train, test]).sort_index()

def get_last_chunk_idx(checkpoint):
    if not os.path.exists(checkpoint):
        return -1
    with open(checkpoint, "r") as f:
        return int(f.read().strip())

def save_last_chunk_idx(idx, checkpoint):
    with open(checkpoint, "w") as f:
        f.write(str(idx))

def classify_all_with_llama(general_prompt, candidate_label, tmppath, savepath, chunk_size=100):
    df = load_data(compact=True)
    mcb = df[df['Company type'] == 'major credit bureaus']
    df = mcb[['Complaint ID', 'Issue', 'Sub-issue', 'Consumer complaint narrative']].copy()
    promptsdf = generate_prompts(df, general_prompt, candidate_label=candidate_label)
    total = len(df)
    total_chunks = (total + chunk_size - 1) // chunk_size

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    checkpoint = os.path.join(tmppath, "checkpoint.txt")
    start_chunk = get_last_chunk_idx(checkpoint) + 1

    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B", torch_dtype=torch.bfloat16, device_map="auto")

    for i in range(start_chunk, total_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total)
        df_chunk = promptsdf.iloc[start:end].copy()

        print(f"[PROCESS] Chunk {i} → rows {start}–{end}")
        max_length = df_chunk["Consumer complaint narrative"].str.len().max()
        print(f"max length: {max_length}")

        if max_length < 4000:
            batch_size = 12
        elif max_length < 7000:
            batch_size = 8
        elif max_length < 15000:
            batch_size = 5
        else:
            batch_size = 3

        outpath = os.path.join(tmppath, f"classified_chunk_{i:05}.csv")
        #llama_predict(promptsdf, generator, outpath, max_length=20)
        results = llama_predict_manual(df_chunk['Prompts'].tolist(), tokenizer, model, batch_size=batch_size, max_length=20)
        df_chunk['predicted_label'] = results
        df_chunk.to_csv(outpath, index=False)
        print(f"[DONE] Saved to {outpath}")
        save_last_chunk_idx(i, checkpoint)

    merge_classified_results(mcb, tmppath, savepath, "classified_chunk_")

def merge_classified_results(df, segpath, savepath, prefix):
    files = sorted([f for f in os.listdir(segpath) if f.endswith('.csv') and f.startswith(prefix)])

    dfs = [pd.read_csv(os.path.join(segpath, f)) for f in files]
    combined = pd.concat(dfs, ignore_index=True)
    merged = df.merge(combined[['Complaint ID', 'predicted_label', 'Prompts']], how='left', on='Complaint ID')

    print(f"[MERGE DONE] Final shape: {merged.shape}")
    merged.to_csv(savepath, index=False)

def llama_predict_manual(prompts, tokenizer, model, batch_size=16, max_length=50):
    print(f"Starting generating answers for {len(prompts)} questions ({len(prompts)//batch_size} batches)")
    #inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(model.device)

    results = []
    for i in tqdm(range(0, len(prompts), batch_size)):
        batch_prompts = prompts[i:i + batch_size]
        inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True).to(model.device)

        with torch.no_grad():
            outputs = model.generate(input_ids=inputs.input_ids, attention_mask=inputs.attention_mask, max_new_tokens=max_length, pad_token_id=tokenizer.eos_token_id, do_sample=False)

        decoded_outputs = tokenizer.batch_decode(outputs.cpu(), skip_special_tokens=True)

        for prompt_text, generated in zip(batch_prompts, decoded_outputs):
            generated_only = generated[len(prompt_text):].strip()
            results.append(generated_only)

    torch.cuda.empty_cache()
    return results

if __name__ == "__main__":
    '''
    ### rule based matching
    savepath = os.path.join(cPATH, 'temp', 'narrative_classification')
    if not os.path.exists(savepath):
        os.mkdir(savepath)

    df = rule_based_matching()
    stats_and_validation(df, savepath)

    ### transfomer zero-shot
    savepath = os.path.join(cPATH, 'temp', 'narrative_classification', 'MLapproach')
    if not os.path.exists(savepath):
        os.mkdir(savepath)

    #generate_sample_dataset_with_label(df, os.path.join(savepath, 'sample.csv'))
    #mutually_exclusive_collectively_exhaustive_label(os.path.join(savepath, 'sample_label6.csv'))
    sample = pd.read_csv(os.path.join(savepath, 'sample.csv'))
    sample = sample.dropna(how='all') 

    org_label = ["Disputed info reappears after deletion", "Incorrect info never deleted", "Outdated info never removed", "Not related to right to be forgotten"]
    meaning = ["Reappears", "Incorrect info persists", "Outdated info persists", "Others"]

    candidate_labels = ["Disputed info reappears after deletion", "Incorrect info never deleted", "Outdated info never removed", "Not related to right to be forgotten"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnli.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnli.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bart.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bart.csv'))

    candidate_labels = ["Deleted info reappears", "Incorrect info persists after dispute", "Right but outdated info persists after dispute", "One time complaint"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlil2.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlil2.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartl2.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartl2.csv'))

    candidate_labels = ["This complaint is about deleted info reinserted", 
                        "This complaint is about incorrect info remaining after dispute", 
                        "This complaint is about outdated info remaining after dispute", 
                        "This complaint is a one time complaint (not about persisting or reappearing info)"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlil3.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlil3.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartl3.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartl3.csv'))

    candidate_labels = ["This complaint is about deleted info reinserted", 
                        "This complaint is about incorrect info persisting after dispute", 
                        "This complaint is about outdated info persisting after dispute", 
                        "This complaint is a first claim of this customer"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlil4.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlil4.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartl4.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartl4.csv'))

    candidate_labels = ["This complaint is about deleted info reinserted", 
                        "This complaint is about incorrect info not removed after dispute", 
                        "This complaint is about obsolete old info not removed after dispute", 
                        "This complaint is an initial request to remove or investigate an inquiry"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlil5.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlil5.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartl5.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartl5.csv'))

    candidate_labels = ["This complaint is about deleted info reinserted", 
                        "This complaint is about incorrect info persits after dispute", 
                        "This complaint is about obsolete old info persists after dispute", 
                        "This complaint is not about removing or updating info", 
                        "This complaint is a one-time dispute, not ongoing"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlil6.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlil6.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartl6.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartl6.csv'))

    candidate_labels = ["This complaint is about deleted info reinserted", 
                        "This complaint is about incorrect info persits after dispute", 
                        "This complaint is about obsolete info persists after dispute or change of delinquency date", 
                        "This complaint is not about removing or updating info", 
                        "This complaint is an initial request to remove or investigate an inquiry"]
    transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlil7.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlil7.csv'))
    transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartl7.csv'))
    evaluate_ml_prediction(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartl7.csv'))

    candidate_labels = ["This complaint is about deleted info reinserted", 
                        "This complaint is about incorrect info persits after dispute", 
                        "This complaint is about obsolete info persists after dispute or change of delinquency date"]
    #transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_labels, os.path.join(savepath, 'sample_pred_mnlilML1.csv'), multi_label=True)
    evaluate_ml_prediction_multilabel(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_mnlilML1.csv'))
    #transformer_zero_shot_sample(sample, "facebook/bart-large-mnli", candidate_labels, os.path.join(savepath, 'sample_pred_bartlML1.csv'), multi_label=True)
    evaluate_ml_prediction_multilabel(candidate_labels, org_label, meaning, os.path.join(savepath, 'sample_pred_bartlML1.csv'))
    '''

    ### LLAMA zero shot
    #generator = load_llama_model()
    #print(generator.model.device)

    '''
    candidate_label = ["Disputed info reappears after deletion", "Incorrect info not removed after dispute", "Right but obsolete info not deleted after dispute or change of deliquency date to keep old info", "None of the above"]
    general_prompt = (
            f"Your task is to classify a consumer complaint submitted to a financial institution into one of the following categories:\n"
            f"(A) {candidate_label[0]}\n"
            f"(B) {candidate_label[1]}\n"
            f"(C) {candidate_label[2]}\n"
            f"(D) {candidate_label[3]}\n\n"
            "Pay special attention to whether the issue had occurred before and either persisted without resolution or resurfaced after seeming to be resolved.\n"
            "You will be given some examples, followed by a question.\n"
            "Classify the question based on the above categories.\n"
            f"**Important: Output only the exact category name (e.g., '{candidate_label[1]}', '{candidate_label[2]}', etc.) without any extra text or explanation.**"
        )

    promptsdf = generate_prompts(sample, general_prompt, candidate_label=candidate_label)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_zero1.csv'), batch_size=32, max_length=50)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_zero1.csv'))

    promptsdf = generate_prompts(sample, general_prompt, candidate_label=candidate_label, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_zero2.csv'), batch_size=32, max_length=50)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_zero2.csv'))

    ### LLAMA few shot
    split_file = os.path.join(savepath, "sample_split.csv")
    if os.path.exists(split_file):
        sample_split = pd.read_csv(split_file)
    else:
        df = load_data(compact=True, override=False)
        sample_split = train_test_split_for_fsl(df, sample)
        sample_split.to_csv(split_file, index=False)

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=5, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few1.csv'), batch_size=32, max_length=50)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few1.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=5, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few2.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few2.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few3.csv'), batch_size=32, max_length=50)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few3.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few4.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few4.csv'))

    general_prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
            "You are an expert in classifying consumer complaints filed to major credit bureaus to identify problems that persistently bother consumers. "
            "You should focus on whether the issue had occured before and either persisted without resolution or resurfaced after seeming to be resolved.\n"
            f"Your task is to classify a consumer complaint submitted to a financial institution into one of the following categories:\n"
            f"(A) {candidate_label[0]}\n"
            f"(B) {candidate_label[1]}\n"
            f"(C) {candidate_label[2]}\n"
            f"(D) {candidate_label[3]}\n\n"
            f"You MUST return only the exact category name (e.g., '{candidate_label[1]}', '{candidate_label[2]}', etc.). "
            "You SHOULD NOT include any extra text or explanation.\n"
            "You will be given some examples, followed by a question.\n"
            "Classify the question based on the above categories.\n" 
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"    
        )
    
    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few5.csv'), batch_size=64, max_length=50)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few5.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few6.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few6.csv'))

    general_prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
            "You are an expert in classifying consumer complaints filed to major credit bureaus to identify problems that persistently bother consumers. "
            "You should focus on whether the issue had occured before and either persisted without resolution or resurfaced after seeming to be resolved.\n"
            f"Your task is to classify a consumer complaint submitted to a financial institution into one of the following categories:\n"
            f"(A) {candidate_label[0]}\n"
            f"(B) {candidate_label[1]}\n"
            f"(C) {candidate_label[2]}\n"
            f"(D) {candidate_label[3]}\n\n"
            f"You MUST return only the exact category name (e.g., '{candidate_label[1]}', '{candidate_label[2]}', etc.). "
            "You SHOULD NOT include any extra text or explanation.\n"
            "You will be given some examples, followed by a question.\n"
            "Classify the question based on the above categories.\n"     
        )
    suffix = "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=False, suffix=suffix)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few7.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few7.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=True, suffix=suffix)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few8.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few8.csv'))

    candidate_label = ["Disputed info reappears after deletion", "Incorrect info not removed after dispute", "Right but obsolete info not delete", "None of the above"]
    general_prompt = (
            f"Your task is to classify a consumer complaint submitted to major credit bureaus into one of the following categories:\n"
            f"(A) {candidate_label[0]}\n"
            f"(B) {candidate_label[1]}\n"
            f"(C) {candidate_label[2]}\n"
            f"(D) {candidate_label[3]}\n\n"
            f"A complaint belongs to '{candidate_label[0]}' category if the consumer had previously disputed incorrect information, the credit bureau DELETED it, but later the same information REAPPEARED on the credit report. "
            "This applies only when the item was DELETED after a prior dispute and RE-ADDED again without any notice.\n"
            f"A complaint belongs to '{candidate_label[1]}' category if the consumer previously disputed incorrect information but the bureau NEVER removed it. The incorrect item REMAINS on the report despite a prior complaint. "
            f"Unlike '{candidate_label[0]}' category, the information was NEVER DELETED at any point. If it was deleted and came back, refer to category '{candidate_label[0]}'.\n"
            f"A complaint belongs to '{candidate_label[2]}' category if it concerns information that is technically correct but should no longer appear on the credit report due to age or legal expiration. "
            "This includes attempts to manipulate the delinquency date in order to keep the information longer than permitted by law.\n"
            f"A complaint belongs to '{candidate_label[3]}' category if it does NOT involve a PERSISTENT or REOCCURING problem. "
            "This includes cases where the issue is UNRELATED to REMOVING information or where the complaint is the consumer’s FIRST report on removing incorrect information, with NO prior dispute or resolution attempt. "
            "This category covers complaints that are NEITHER about information that was NEVER REMOVED nor about information that was seemingly removed but later REAPPEARED.\n\n"
            f"You MUST return only the exact category name (e.g., '{candidate_label[1]}', '{candidate_label[2]}', etc.). "
            "You SHOULD NOT include any extra text or explanation.\n"
            "You will be given some examples, followed by a question.\n"
            "Classify the question based on the above categories.\n"
            )

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few9.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few9.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few10.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few10.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=5, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few11.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few11.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=5, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few12.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few12.csv'))

    candidate_label = ["Disputed info reappears after deletion", "Incorrect info not removed after dispute", "Right but obsolete info persists", "None of the above"]

    general_prompt = (
        f"Your task is to classify a consumer complaint submitted to major credit bureaus into one of the following categories:\n"
        f"(A) {candidate_label[0]}\n"
        f"(B) {candidate_label[1]}\n"
        f"(C) {candidate_label[2]}\n"
        f"(D) {candidate_label[3]}\n\n"

        f"**{candidate_label[0]}**:\n"
        f"The consumer previously DISPUTED incorrect information, and the credit bureau DELETED it. However, the SAME item later REAPPEARED on the credit report. "
        f"This category applies only if the previously deleted information was re-inserted without notice. "
        f"If the bureau claimed they would remove the information but never actually did so, it should NOT be classified here — refer instead to category '{candidate_label[1]}'. "
        f"This category also includes repeated reappearances of the same disputed item despite prior deletion attempts. "
        f"If the previous removal was clearly due to a technical glitch, the complaint should be classified under '{candidate_label[3]}'.\n\n"

        f"**{candidate_label[1]}**:\n"
        f"The consumer previously disputed incorrect information, but the bureau NEVER removed it. "
        f"The item remains on the report despite the previous dispute — either because the bureau ignored the request or deemed the information valid after investigation. "
        f"The key difference from category '{candidate_label[0]}' is that the information was NEVER removed at any point. "
        f"If it was deleted and later returned, classify under '{candidate_label[0]}'.\n\n"

        f"**{candidate_label[2]}**:\n"
        f"The complaint concerns information that is factually accurate but should no longer appear due to age or legal expiration. "
        f"This includes cases involving outdated information in credit report that should have been removed or efforts to manipulate the delinquency date to extend the reporting period.\n\n"

        f"**{candidate_label[3]}**:\n"
        f"The complaint does NOT involve persistence or recurrence of information that should have been deleted. "
        f"This includes:\n"
        f"– Complaints unrelated to removing information\n"
        f"– First-time disputes to remove incorrect information where no prior resolution was attempted\n"
        f"– Issues that are clearly unrelated to recurring or unresolved items on the credit report\n\n"

        f"You MUST choose ONE category that best fits the complaint. Return only the exact category name (e.g., '{candidate_label[1]}', '{candidate_label[2]}', etc.)."
        f"Do NOT include any additional text or explanation.\n\n"
        f"You will now be shown a few examples, followed by a new complaint to classify.\n"
    )

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=5, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few13.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few13.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=5, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few14.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few14.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=False)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few15.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few15.csv'))

    promptsdf = generate_prompts(sample_split.copy(), general_prompt, candidate_label=candidate_label, len_example=10, include_issue=True)
    llama_predict(promptsdf, generator, os.path.join(savepath, 'LLAMA_few16.csv'), batch_size=64, max_length=25)
    evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'LLAMA_few16.csv'))
    '''
    ###### classification of complaints on removing information vs. others
    # transfomer zero-shot
    savepath = os.path.join(cPATH, 'temp', 'narrative_classification', 'two_step_approach')
    if not os.path.exists(savepath):
        os.mkdir(savepath)
    
    if os.path.exists(os.path.join(savepath, 'sample_step1.csv')):
        sample = pd.read_csv(os.path.join(savepath, 'sample_step1.csv'))
    else:
        df = load_data(compact=True)
        mcb = df[df['Company type'] == 'major credit bureaus']
        sample = mcb.sample(n=100, random_state=42)
        sample[['Complaint ID', 'Issue', 'Sub-issue', 'Consumer complaint narrative']].to_csv(os.path.join(savepath, 'sample_step1.csv'), index=False)

    candidate_label = ["Request to remove or correct inaccurate information", "Not a request to remove or correct information"]
    org_label = ["True", "False"]
    meaning = ["Removing Info", "Others"]
    #transformer_zero_shot_sample(sample, "valhalla/distilbart-mnli-12-3", candidate_label, os.path.join(savepath, 'step1_pred_mnli.csv'), batch_size=100)
    #evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'step1_pred_mnli.csv'))

    general_prompt = (
            f"Your task is to classify a consumer complaint submitted to the CFPB based on whether it involves a request to remove or correct inaccurate information.\n\n"
            f"Classify the complaint as '{candidate_label[0]}' if it:\n"
            f"- Requests deletion of information, OR\n"
            f"- Implies a desire to have information removed (e.g., by pointing out inaccuracies), OR\n"
            f"- Requests an update or correction to existing information on the credit report.\n\n"
            f"Classify the complaint as '{candidate_label[1]}' if it:\n"
            f"- Does NOT request removal or correction of inaccurate information.\n\n"
            f"Any complaint that does not fit the '{candidate_label[0]}' criteria should be classified as '{candidate_label[1]}'.\n\n"
            f"You MUST output only the exact category name — no extra text or explanation.\n\n"
            f"Example 1: I have accounts in my file that I do not recognize: XXXX/XX/XX, account XXXXX\n"
            f"Answer: {candidate_label[0]}\n\n"
            f"Example 2: XXXX has not responded to me in 90 days. Please help.\n"
            f"Answer: {candidate_label[1]}\n"
        )

    #promptsdf = generate_prompts(sample.copy(), general_prompt, candidate_label=candidate_label)
    #llama_predict(promptsdf, generator, os.path.join(savepath, 'step1_LLAMA.csv'), batch_size=100, max_length=50)
    #evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'step1_LLAMA.csv'))

    general_prompt = (
            f"Your task is to classify a consumer complaint submitted to the CFPB based on whether it involves a request to remove or correct inaccurate information.\n\n"
            f"Classify the complaint as '{candidate_label[0]}' if it:\n"
            f"- Contains a direct request from the complainant to delete information, OR\n"
            f"- Directly requests an update or correction to existing information on the credit report, OR\n"
            f"- Strongly implies a desire to have information removed (e.g., by pointing out inaccuracies) .\n\n"
            f"Only a direct request by the complainant to delete or correct existing information should be included in '{candidate_label[0]}'.\n\n"
            f"Classify the complaint as '{candidate_label[1]}' if it:\n"
            f"- Focuses on matters other than requesting removal or correction of inaccurate information, OR\n"
            f"- Is a request for a third party to intervene or prompt another company to act, OR\n"
            f"- Does not contain enough information to decide whether it fits the '{candidate_label[0]}' criteria.\n\n"
            f"Any complaint that does not fit the '{candidate_label[0]}' criteria should be classified as '{candidate_label[1]}'.\n\n"
            f"You MUST output only the exact category name — no extra text or explanation.\n\n"
            f"Example 1: I have accounts in my file that I do not recognize: XXXX/XX/XX, account XXXXX\n"
            f"Answer: {candidate_label[0]}\n\n"
            f"Example 2: XXXX has not responded to me in 90 days. Please help.\n"
            f"Answer: {candidate_label[1]}\n"
        )

    #promptsdf = generate_prompts(sample.copy(), general_prompt, candidate_label=candidate_label)
    #llama_predict(promptsdf, generator, os.path.join(savepath, 'step1_LLAMA2.csv'), batch_size=100, max_length=20)
    #evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'step1_LLAMA2.csv'))


    general_prompt = (
            f"Your task is to classify a consumer complaint submitted to the CFPB based on whether it involves a request to remove or correct inaccurate information.\n\n"
            f"Classify the complaint as '{candidate_label[0]}' if it:\n"
            f"- Requests deletion of information, OR\n"
            f"- Directly requests an update or correction to existing information on the credit report, OR\n"
            f"- Implies a desire to have information removed (e.g., by pointing out inaccuracies).\n\n"
            f"Only a direct request by the complainant to delete or correct existing information should be included in '{candidate_label[0]}'.\n\n"
            f"Classify the complaint as '{candidate_label[1]}' if it:\n"
            f"- Focuses on matters other than requesting removal or correction of inaccurate information, OR\n"
            f"- Is a request for a third party to intervene or prompt another company to act, OR\n"
            f"- Does not contain enough information to decide whether it fits the '{candidate_label[0]}' criteria.\n\n"
            f"Any complaint that does not fit the '{candidate_label[0]}' criteria should be classified as '{candidate_label[1]}'.\n\n"
            f"You MUST output only the exact category name — no extra text or explanation.\n\n"
            f"Example 1: I have accounts in my file that I do not recognize: XXXX/XX/XX, account XXXXX\n"
            f"Answer: {candidate_label[0]}\n\n"
            f"Example 2: XXXX has not responded to me in 90 days. Please help.\n"
            f"Answer: {candidate_label[1]}\n\n"
            f"Example 3: Please verify the XXXX on XXXX/XX/XX. \n"
            f"Answer: {candidate_label[1]}\n\n"
        )

    #promptsdf = generate_prompts(sample.copy(), general_prompt, candidate_label=candidate_label)
    #llama_predict(promptsdf, generator, os.path.join(savepath, 'step1_LLAMA3.csv'), batch_size=100, max_length=20)
    #evaluate_ml_prediction(candidate_label, org_label, meaning, os.path.join(savepath, 'step1_LLAMA3.csv'))

    classify_all_with_llama(general_prompt, candidate_label, os.path.join(pPATH, 'step1_classification_LLAMA'), os.path.join(savepath, 'step1_res.csv'))
