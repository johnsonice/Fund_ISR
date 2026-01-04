'''
Experiment with GPT for fiscal policy stance classification tasks - zero shot, few shot, fine-tuning.
Input: labelled_fiscal_v2.xlsx
Output: ../../data/llm_evaluation/fiscal/...
'''
from util import *

directory = r'../../data/'

# read training and testing sets
# prepare files for different tasks
df = pd.read_excel(directory+'labeling/monetary&fiscal/labelled/labelled_fiscal_v2.xlsx')

df_stance = pd.DataFrame()
for tp in ['staff', 'buff']:
    df_temp = df[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_near_term'%tp]]
    df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
    df_temp['type'] = tp
    df_stance = pd.concat([df_stance, df_temp], ignore_index=True)


# 1. define prompt
type_dict1 = {'staff': 'IMF staff', 'buff': 'a country\'s authorities'}
type_dict2 = {'staff': 'IMF staff\'s', 'buff': 'country\'s authorities\''}
verb_dict = {'staff': 'recommended', 'buff': 'planned'}
explanation_dict = {'staff': 'Note that the near-term policy direction recommended by staff is different in concept from staff\'s projected near-term policy direction of the authorities.',
                    'buff': 'Note that the near-term policy direction planned by the authorities are different in concept from IMF staff\'s recommended or projected near-term policy direction.'}

prompt = '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, classify the %s %s near-term (next year) direction of change in fiscal policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s If the text indicates a leaning towards a tightening/loosening fiscal policy but without a full commitment, assign "tightening bias"/"loosening bias". If the text discusses fiscal policy but the direction of change is not clear, assign "unclear"; if it does not discuss fiscal policy, assign "irrelevant". Return your answer without additional texts.'''  # %(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},


# 2. Zero-shot tests - short/long queries/chain-of-thought
# 2.1. version 1: simplest
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = chat_completion.choices[0].message.content.replace('```json',
                                                                    '').replace(
            '```', '')
        df_stance.loc[i, 'stance_near_term_gpt1'] = result
    except Exception:
        df_stance.loc[i, 'error_gpt1'] = chat_completion.choices[
            0].message.content
df_stance['stance_near_term_gpt1'] = df_stance['stance_near_term_gpt1'].apply(lambda x: x.lower())

# query v1:
md = 'gpt1'
print('raw:', accuracy_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md]), f1_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', ''))), f1_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), average='weighted'))


# 2.2. version 2: adding brief definitions
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, classify the %s %s near-term (next year) direction of change in fiscal policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s\n\nDefinitions:\nTightening: Suggests a plan to reduce fiscal deficits or move towards a surplus. This can be achieved through higher taxation or non-tax revenues, reduced government spending, or a combination of both.\nTightening Bias: Indicates a leaning towards a tightening fiscal policy but without a full commitment.\nNo Change: Indicates a plan to maintain the current fiscal policy stance without significant changes to overall fiscal balance.\nLoosening Bias: Suggests a leaning towards adopting a loosening fiscal policy, though not explicitly planning to do so.\nLoosening: Suggests a clear move towards higher fiscal deficits or reduced surplus, involving increased government spending, revenue cuts, or a combination of both, aimed at stimulating the economy.\nUnclear: The text discusses fiscal policy but the direction of change is not clear.\nIrrelevant: The text does not discuss fiscal policy.\n\nReturn your answer without additional texts.''' %(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = chat_completion.choices[0].message.content.replace('```json',
                                                                    '').replace(
            '```', '')
        df_stance.loc[i, 'stance_near_term_gpt2'] = result
    except Exception:
        df_stance.loc[i, 'error_gpt2'] = chat_completion.choices[
            0].message.content
df_stance['stance_near_term_gpt2'] = df_stance['stance_near_term_gpt2'].apply(lambda x: x.lower())

# query v2:
md = 'gpt2'
print('raw:', accuracy_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md]), f1_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', ''))), f1_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), average='weighted'))


# 2.3. version 3: chain-of-thought
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, classify the %s %s near-term (next year) direction of change in fiscal policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s\n\nDefinitions:\nTightening: Suggests a plan to reduce fiscal deficits or move towards a surplus. This can be achieved through higher taxation or non-tax revenues, reduced government spending, or a combination of both.\nTightening Bias: Indicates a leaning towards a tightening fiscal policy but without a full commitment.\nNo Change: Indicates a plan to maintain the current fiscal policy stance without significant changes to overall fiscal balance.\nLoosening Bias: Suggests a leaning towards adopting a loosening fiscal policy, though not explicitly planning to do so.\nLoosening: Suggests a clear move towards higher fiscal deficits or reduced surplus, involving increased government spending, revenue cuts, or a combination of both, aimed at stimulating the economy.\nUnclear: The text discusses fiscal policy but the direction of change is not clear.\nIrrelevant: The text does not discuss fiscal policy.\n\nProvide reasoning before your classification. Return your answer in a JSON dict without additional texts: \"reason\", \"stance_near_term\".'''%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(
            chat_completion.choices[0].message.content.replace('```json',
                                                               '').replace(
                '```', ''))
        df_stance.loc[i, 'stance_near_term_gpt3'] = result[
            'stance_near_term']
        df_stance.loc[i, 'reason_gpt3'] = result['reason']
    except Exception:
        df_stance.loc[i, 'error_gpt3'] = chat_completion.choices[
            0].message.content
df_stance['stance_near_term_gpt3'] = df_stance['stance_near_term_gpt3'].apply(lambda x: x.lower())


# query v3:
md = 'gpt3'
print('raw:', accuracy_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md]), f1_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', ''))), f1_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), average='weighted'))


# 3. Few-shot
# version 4: adding a few examples
example_dict = {'staff': 'Example 1: Country: Tunisia; Year: 2015; Text: \"The modest fiscal loosening in 2015 appropriately responds to weaker economic activity. Going forward, fiscal consolidation is needed to reduce external imbalances, restore private sector confidence, and ensure debt sustainability.\" Answer: \"tightening\".\nExample 2: Country: Denmark; Year: 2019; Text: \"The fiscal stance should remain neutral, while letting automatic stabilizers operate fully in case of shocks to aggregate demand.\" Answer: \"no change\".\nExample 3: Country: Denmark; Year: 2017; Text: \"Thus, provided that strong new labor market reforms are agreed to raise labor supply, it would be appropriate to slow the pace of consolidation somewhat to facilitate cuts in the high tax burden.\" Answer: \"loosening bias\".',
               'buff': 'Example 1: Country: Tunisia; Year: 2015; Text: \"The authorities are firmly committed to take additional measures to attain their fiscal objectives in 2015, including through reduction of non-essential non-wage expenditure. They are committed to fiscal adjustment from 2016 onwards.\" Answer: \"tightening\".\nExample 2: Country: China; Year: 2019; Text: \"We concur with staff’s suggestion that there is no need for a further large-scale fiscal stimulus at this moment since the effects of trade tensions have already been factored into this year’s budget.\" Answer: \"no change\".\nExample 3: Country: Singapore; Year: 2019; Text: \"While fiscal policy is focused on medium- to long-term restructuring, the authorities stand ready to provide fiscal stimulus should economic conditions take a significant turn for the worse.\" Answer: \"loosening bias\".'}


for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system",
             "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, classify the %s %s near-term (next year) direction of change in fiscal policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s\n\nDefinitions:\nTightening: Suggests a plan to reduce fiscal deficits or move towards a surplus. This can be achieved through higher taxation or non-tax revenues, reduced government spending, or a combination of both.\nTightening Bias: Indicates a leaning towards a tightening fiscal policy but without a full commitment.\nNo Change: Indicates a plan to maintain the current fiscal policy stance without significant changes to overall fiscal balance.\nLoosening Bias: Suggests a leaning towards adopting a loosening fiscal policy, though not explicitly planning to do so.\nLoosening: Suggests a clear move towards higher fiscal deficits or reduced surplus, involving increased government spending, revenue cuts, or a combination of both, aimed at stimulating the economy.\nUnclear: The text discusses fiscal policy but the direction of change is not clear.\nIrrelevant: The text does not discuss fiscal policy.\n\n%s\n\nReturn your answer without additional texts.''' % (
             type_dict1[row['type']], type_dict2[row['type']],
             verb_dict[row['type']], explanation_dict[row['type']],
             example_dict[row['type']])},
    {"role": "user",
     "content": '''Country: %s; Year: %s\nText:\n%s''' % (
     row['country'], row['year'], row['text'])}
    ],
    model = 'gpt-4o-2024-08-06',
    temperature = 0
)
    try:
        result = chat_completion.choices[0].message.content.replace('```json',
                                                                    '').replace(
            '```', '')
        df_stance.loc[i, 'stance_near_term_gpt4'] = result
    except Exception:
        df_stance.loc[i, 'error_gpt4'] = chat_completion.choices[
            0].message.content
df_stance['stance_near_term_gpt4'] = df_stance['stance_near_term_gpt4'].apply(lambda x: x.lower().strip('.'))


# query v4:
md = 'gpt4'
print('raw:', accuracy_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md]), f1_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))


# 4. other models
# version 5: gpt-4o-mini
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, classify the %s %s near-term (next year) direction of change in fiscal policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s\n\nDefinitions:\nTightening: Suggests a plan to reduce fiscal deficits or move towards a surplus. This can be achieved through higher taxation or non-tax revenues, reduced government spending, or a combination of both.\nTightening Bias: Indicates a leaning towards a tightening fiscal policy but without a full commitment.\nNo Change: Indicates a plan to maintain the current fiscal policy stance without significant changes to overall fiscal balance.\nLoosening Bias: Suggests a leaning towards adopting a loosening fiscal policy, though not explicitly planning to do so.\nLoosening: Suggests a clear move towards higher fiscal deficits or reduced surplus, involving increased government spending, revenue cuts, or a combination of both, aimed at stimulating the economy.\nUnclear: The text discusses fiscal policy but the direction of change is not clear.\nIrrelevant: The text does not discuss fiscal policy.\n\nReturn your answer without additional texts.''' %(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-mini-2024-07-18',
            temperature=0
        )
    try:
        result = chat_completion.choices[0].message.content.replace('```json',
                                                                    '').replace(
            '```', '')
        df_stance.loc[i, 'stance_near_term_gpt5'] = result
    except Exception:
        df_stance.loc[i, 'error_gpt5'] = chat_completion.choices[
            0].message.content
df_stance['stance_near_term_gpt5'] = df_stance['stance_near_term_gpt5'].apply(lambda x: x.lower())

# query v5:
md = 'gpt5'
print('raw:', accuracy_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md]), f1_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))


# version 6: gpt-3.5-turbo
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, classify the %s %s near-term (next year) direction of change in fiscal policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s\n\nDefinitions:\nTightening: Suggests a plan to reduce fiscal deficits or move towards a surplus. This can be achieved through higher taxation or non-tax revenues, reduced government spending, or a combination of both.\nTightening Bias: Indicates a leaning towards a tightening fiscal policy but without a full commitment.\nNo Change: Indicates a plan to maintain the current fiscal policy stance without significant changes to overall fiscal balance.\nLoosening Bias: Suggests a leaning towards adopting a loosening fiscal policy, though not explicitly planning to do so.\nLoosening: Suggests a clear move towards higher fiscal deficits or reduced surplus, involving increased government spending, revenue cuts, or a combination of both, aimed at stimulating the economy.\nUnclear: The text discusses fiscal policy but the direction of change is not clear.\nIrrelevant: The text does not discuss fiscal policy.\n\nReturn your answer without additional texts.''' %(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-3.5-turbo',
            temperature=0
        )
    try:
        result = chat_completion.choices[0].message.content.replace('```json',
                                                                    '').replace(
            '```', '')
        df_stance.loc[i, 'stance_near_term_gpt6'] = result
    except Exception:
        df_stance.loc[i, 'error_gpt6'] = chat_completion.choices[
            0].message.content
df_stance['stance_near_term_gpt6'] = df_stance['stance_near_term_gpt6'].apply(lambda x: x.lower().strip('.'))

# query v6:
md = 'gpt6'
print('raw:', accuracy_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md]), f1_score(df_stance['stance_near_term'], df_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))

# save
df_stance.to_excel(directory+'llm_evaluation/fiscal/df_train_stance_gpt.xlsx', index=False)


# 5. fine-tuning

# 5.1. read training and testing files
idx = 0
df_train = pd.read_excel(directory+'finetuning/fiscal/cv/training_%d.xlsx'%idx)
df_test = pd.read_excel(directory+'finetuning/fiscal/cv/testing_%d.xlsx'%idx)

df_train_stance = pd.DataFrame()
for tp in ['staff', 'buff']:
    df_temp = df_train[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_near_term'%tp,]]
    df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
    df_temp['type'] = tp
    df_train_stance = pd.concat([df_train_stance, df_temp], ignore_index=True)

df_test_stance = pd.DataFrame()
for tp in ['staff', 'buff']:
    df_temp = df_test[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_near_term'%tp,]]
    df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
    df_temp['type'] = tp
    df_test_stance = pd.concat([df_test_stance, df_temp], ignore_index=True)


# 5.2. generate prompts and answers for the training set
df_train_stance['answer'] = df_train_stance.apply(lambda x: x['stance_near_term'], axis=1)
df_train_stance['messages'] = df_train_stance.apply(lambda row: [
                {   "role": "system",
                    "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])},
                {   "role": "assistant",
                    "content":  row['answer']}
            ], axis=1)

df_train_stance[['messages']].to_json(directory+'finetuning/fiscal/cv/training_fis_%d.jsonl'%idx, orient='records', lines=True)


# check fine-tuning dataset
check_finetuning_dataset(directory+'finetuning/fiscal/cv/training_fis_%d.jsonl'%idx)


# 5.3. create fine-tuning job
file = client.files.create(
    file=open(directory+'finetuning/fiscal/cv/training_fis_%d.jsonl'%idx, "rb"),
    purpose="fine-tune"
)
print(file.id)

client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18"
    # model="gpt-4o-2024-08-06"
)

# List up to 10 events from a fine-tuning job
client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-FQjmswzuQuBamJR5YtQ6kQ82", limit=3)

# List the recent fine-tuning jobs
client.fine_tuning.jobs.list(limit=2)


# 5.4. Apply the fine-tuned model to testing set
model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4TjP1Dd'  # idx = 0
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4Uckv4P'   # idx = 1
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4VGh39x'   # idx = 2
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4XBbmtz'   # idx = 3
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4Y0y06F'   # idx = 4

for i,row in df_test_stance.iterrows():
    chat_completion = client.chat.completions.create(
        messages=[
                {   "role": "system",
                    "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
        model=model_id,
        temperature=0
    )
    try:
        result = chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace("\'", "\"")
        df_test_stance.loc[i,'stance_near_term_gpt_ft'] = result.lower()
    except Exception:
        df_test_stance.loc[i, 'error_gpt_ft'] = chat_completion.choices[0].message.content

# ft v1:
md = 'gpt_ft'
print('raw:', accuracy_score(df_test_stance['stance_near_term'], df_test_stance['stance_near_term_%s'%md]), f1_score(df_test_stance['stance_near_term'], df_test_stance['stance_near_term_%s'%md], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_test_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_test_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', ''))), f1_score(df_test_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df_test_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), average='weighted'))

print(confusion_matrix(df_test_stance['stance_near_term'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_near_term_%s'%md].apply(lambda x: 'unclear' if x=='irrelevant' else x), labels=['tightening', 'tightening bias', 'no change', 'loosening bias', 'loosening', 'unclear']))

# save results
df_test_stance.to_excel(directory+'finetuning/fiscal/cv/df_test_stance_fis_%d_v1.xlsx'%idx, index=False)


# 5.5. final training
df_sample = pd.read_excel(directory+'labeling/monetary&fiscal/labelled/labelled_fiscal_v2.xlsx')

df_stance = pd.DataFrame()
for tp in ['staff', 'buff']:
    df_temp = df_sample[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_near_term'%tp]]
    df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
    df_temp['type'] = tp
    df_stance = pd.concat([df_stance, df_temp], ignore_index=True)


df_stance['answer'] = df_stance.apply(lambda x: x['stance_near_term'], axis=1)
df_stance['messages'] = df_stance.apply(lambda row: [
                {   "role": "system",
                    "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])},
                {   "role": "assistant",
                    "content":  row['answer']}
            ], axis=1)

df_stance[['messages']].to_json(directory+'finetuning/fiscal/all_fis.jsonl', orient='records', lines=True)

check_finetuning_dataset(directory+'finetuning/fiscal/all_fis.jsonl')

# create finetuning job
file = client.files.create(
    file=open(directory+'all_fis.jsonl', "rb"),
    purpose="fine-tune"
)
print(file.id)

client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18"
)

# List up to 10 events from a fine-tuning job
client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-ltV05AoY1USB8ucxxryXbKt2", limit=5)

client.fine_tuning.jobs.list(limit=2)

# save model id
model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4ZD00Na'  # stance
