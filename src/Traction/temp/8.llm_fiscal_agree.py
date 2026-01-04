'''
Experiment with GPT for fiscal policy agreement classification tasks - zero shot, few shot, fine-tuning.
Input: labelled_fiscal_v2.xlsx
Output: ../../data/llm_evaluation/fiscal/...
'''
#%%
import os,sys
sys.path.append('..')
import config
from util import *

directory = config.data_dir
#%%
# read training and testing sets
# prepare files for different tasks
df = pd.read_excel(directory / 'Finetuning_data/labelled_fiscal_v2.xlsx')
#df = pd.read_excel('/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/labelled_fiscal_v2.xlsx')
df_agree = df[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]
# 1. define prompt
prompt = '''You are an experienced macroeconomist from IMF. Given two pieces of texts expressing the views 
of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities 
agree or disagree with IMF staff on issues related to the country's fiscal policy. First, assign a value 
to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' 
agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' 
views. If the two pieces of texts discuss common aspect(s) of fiscal policy or if the authorities directly 
express agreement/disagreement to fiscal related issues in either text: (a) if the authorities disagree with 
IMF staff on any fiscal policy issues, assign "disagreement exists"; (b) if there is no disagreement by the 
authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with 
IMF staff on fiscal related issues, and either of the texts does not discuss fiscal policy or they discuss entirely 
different aspects of fiscal policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of 
disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "near-term policy 
direction", "fiscal revenue", "fiscal expenditure", "government debt & financing", "economic assessment", 
"fiscal framework", "medium-term fiscal stance", etc; if the authorities do not disagree with staff, 
leave the "disagreement_areas" field blank. Return a JSON dict without additional texts: "agreement", 
"disagreement_areas".'''

#%%
# 2. Zero-shot tests - short/long queries/chain-of-thought
# 2.1. version 1: simplest
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": prompt,},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt1'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt1'] = result['disagreement_areas']
    except Exception:
        df_agree.loc[i, 'error_gpt1'] = chat_completion.choices[0].message.content

df_agree['error_gpt1'] = df_agree['error_gpt1'].apply(lambda x: json.loads(x.replace('```json','').replace('```','').replace('\n',' ')) if x==x and x!='nan' else np.nan)
df_agree['agreement_gpt1'] = df_agree.apply(lambda x: x['error_gpt1']['agreement'] if x['agreement_gpt1']!=x['agreement_gpt1'] else x['agreement_gpt1'], axis=1)
df_agree['disagreement_areas_gpt1'] = df_agree.apply(lambda x: x['error_gpt1']['disagreement_areas'] if x['disagreement_areas_gpt1']!=x['disagreement_areas_gpt1'] or x['disagreement_areas_gpt1']=='n' else x['disagreement_areas_gpt1'], axis=1)
# for a in areas_l:
#     df_agree['da_'+a+'_gpt1'] = df_agree['disagreement_areas_gpt1'].apply(lambda x: x==x and a in x)
# query v1:
print(accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt1']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt1'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt1'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))
#%%
# 2.2. version 2: adding brief definitions
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's fiscal policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of fiscal policy or if the authorities directly express agreement/disagreement to fiscal related issues in either text: (a) if the authorities disagree with IMF staff on any fiscal policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on fiscal related issues, and either of the texts does not discuss fiscal policy or they discuss entirely different aspects of fiscal policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "near-term policy direction", "government revenue", "government expenditure", "government debt & financing", "economic fundamentals", "fiscal framework", "medium-term fiscal stance", etc; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank.\n\nDefinitions:\nnear-term policy direction: Planned or recommended near-term (next-year) direction of change in fiscal policy stance.\ngovernment revenue: The sources, levels, or methods of enhancing government income, including taxation policies, revenue from natural resources, or other forms of government income.\ngovernment expenditure: The amount, allocation, or priorities of government spending. Disagreements may arise from debates over the size of the public sector, investment in infrastructure, social welfare spending, or fiscal austerity measures.\ngovernment debt & financing: The level of government debt, its sustainability, and the methods of financing it (e.g., through issuing bonds, taking loans from international institutions, or printing money). Disagreements might also involve strategies for debt reduction or restructuring.\neconomic fundamentals: Assessments or interpretations of the underlying strength and stability of an economy, such as productivity, labor market health, inflation rates, and the balance of payments.\nfiscal framework: This refers to the structural aspects of how fiscal policy is formulated and implemented, including fiscal rules, budgetary processes, and institutional arrangements for fiscal governance.\nmedium-term fiscal stance: The fiscal policy orientation over the medium term (usually three to five years).\n\nReturn a JSON dict without additional texts: "agreement", "disagreement_areas".''',},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt2'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt2'] = result['disagreement_areas']
    except Exception:
        df_agree.loc[i, 'error_gpt2'] = chat_completion.choices[0].message.content

df_agree['error_gpt2'] = df_agree['error_gpt2'].apply(lambda x: json.loads(x.replace('```json','').replace('```','').replace('\n',' ')) if x==x and x!='nan' else np.nan)
df_agree['agreement_gpt2'] = df_agree.apply(lambda x: x['error_gpt2']['agreement'] if x['agreement_gpt2']!=x['agreement_gpt2'] else x['agreement_gpt2'], axis=1)
df_agree['disagreement_areas_gpt2'] = df_agree.apply(lambda x: x['error_gpt2']['disagreement_areas'] if x['disagreement_areas_gpt2']!=x['disagreement_areas_gpt2'] or x['disagreement_areas_gpt2']=='n' else x['disagreement_areas_gpt2'], axis=1)


# query v2:
print(accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt2']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt2'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt2'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

#%%

# 2.3. version 3: chain-of-thought
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's fiscal policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of fiscal policy or if the authorities directly express agreement/disagreement to fiscal related issues in either text: (a) if the authorities disagree with IMF staff on any fiscal policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on fiscal related issues, and either of the texts does not discuss fiscal policy or they discuss entirely different aspects of fiscal policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "near-term policy direction", "fiscal revenue", "fiscal expenditure", "government debt & financing", "economic assessment", "fiscal framework", "medium-term fiscal stance", etc; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank. Provide reasoning before giving your answer. Return a JSON dict without additional texts: "reason", "agreement", "disagreement_areas".''',},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt3'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt3'] = result['disagreement_areas']
        df_agree.loc[i,'reason_gpt3'] = result['reason']
    except Exception:
        df_agree.loc[i, 'error_gpt3'] = chat_completion.choices[0].message.content

df_agree['error_gpt3'] = df_agree['error_gpt3'].apply(lambda x: json.loads(x.replace('```json','').replace('```','').replace('\n',' ')) if x==x and x != 'nan' else np.nan)
df_agree['agreement_gpt3'] = df_agree.apply(lambda x: x['error_gpt3']['agreement'] if x['agreement_gpt3']!=x['agreement_gpt3'] or x['agreement_gpt3'] in ['nan', 'n'] else x['agreement_gpt3'], axis=1)
df_agree['disagreement_areas_gpt3'] = df_agree.apply(lambda x: x['error_gpt3']['disagreement_areas'] if x['disagreement_areas_gpt3']!=x['disagreement_areas_gpt3'] or x['disagreement_areas_gpt3'] in ['n', 'nan'] else x['disagreement_areas_gpt3'], axis=1)
df_agree['reason_gpt3'] = df_agree.apply(lambda x: x['error_gpt3']['reason'] if x['reason_gpt3']!=x['reason_gpt3'] or x['reason_gpt3'] in ['n', 'nan'] else x['reason_gpt3'], axis=1)


# query v3:
print(accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt3']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt3'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt3'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

#%%
# 3. Few-shot
# version 4: adding a few examples
example_l = [
    '''Example 1:\nCountry: Philippines; Year: 2018\n\nPart1 - IMF staff:\n35. To balance growth and stability objectives, the authorities should adopt a neutral fiscal stance over 2018–2019. This implies an overall deficit of 2.4 percent in 2018 and 2.5 percent of GDP in 2019 (compared to staff’s current baseline of 2.8 and 3.2 percent), which would support pro-growth infrastructure investment without overburdening monetary policy, while containing inflationary pressures. Raising tax revenues and reallocating spending from nonpriority programs can support the continued expansion of public investment and social spending.\n\nPart2 - Authority:\nAuthorities are keeping their expansionary fiscal policy, as originally programmed. While they have carefully considered the staff policy recommendation to keep a neutral fiscal stance to balance growth and stability, Authorities continue to see the imperative for stronger investment in infrastructure. ... Part of staff argument for a neutral fiscal stance was to “limit overheating risks” and avoid “overburdening monetary policy” While Authorities are cognizant of elevated risks, they continue to see few signs of possible overheating in the economy.\n\nAnswer: {"agreement": "disagreement exists", "disagreement_areas": "['economic fundamentals', 'near-term policy direction']"}.'''.replace('\n\n','\n'),
    '''Example 2:\nCountry: India; Year: 2017\n\nPart1 - IMF staff:\n55. The authorities should press ahead with their longer-term objective of substantially reducing fiscal deficits and the public debt burden. With continued delays in reaching medium-term deficit targets, India’s public debt ratio is likely to remain high and fiscal policy space remains limited. ...\n\nPart2 - Authority:\n5. We want to emphasize the commitment of our authorities on medium-term fiscal consolidation. A conducive environment for improvement in state public finances has been created through suitable incentives/costs for states to renew fiscal efforts towards consolidation. ... As regards debt, India’s public debt is sustainable both because of the authorities’ commitments for fiscal consolidation and the projected interest versus growth trajectory going forward.\n\nAnswer: {"agreement": "disagreement exists", "disagreement_areas": "['government debt & financing']"}.'''.replace('\n\n','\n'),
    '''Example 3:\nCountry: Denmark; Year: 2019\n\nPart1 - IMF staff:\n47. Denmark’s public finances are sound with substantial fiscal space in the medium term. The fiscal stance should remain neutral, while letting automatic stabilizers operate fully in case of shocks to aggregate demand. In the event of a severe downturn, additional temporary loosening should be considered, while remaining anchored to the medium-term objective. Efficiency-improving reforms that cover both revenues and expenditures could be implemented in a fiscally-neutral way or designed to provide stimulus if loosening is warranted.\n\nPart2 - Authority:\nFor more than two decades, Danish fiscal policy has been conducted within a forward-looking medium-term fiscal framework. The associated plans contain operational targets for the medium-term structural fiscal balance and play an important role in ensuring long-term fiscal sustainability. The most recent update of the 2025-plan aims at structural fiscal balance in 2025.\n\nAnswer: {"agreement": "mostly agree", "disagreement_areas": "[]"}.'''.replace('\n\n','\n'),
]

for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's fiscal policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of fiscal policy or if the authorities directly express agreement/disagreement to fiscal related issues in either text: (a) if the authorities disagree with IMF staff on any fiscal policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on fiscal related issues, and either of the texts does not discuss fiscal policy or they discuss entirely different aspects of fiscal policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "near-term policy direction", "fiscal revenue", "fiscal expenditure", "government debt & financing", "economic assessment", "fiscal framework", "medium-term fiscal stance", etc; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank.\n\n%s\n\nReturn a JSON dict without additional texts: \"agreement\", \"disagreement_areas\".'''%('\n\n'.join(example_l)),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt4'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt4'] = result['disagreement_areas']
    except Exception:
        df_agree.loc[i, 'error_gpt4'] = chat_completion.choices[0].message.content


# query v4:
print(accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt4']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt4'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt4'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

#%%
# 4. other models
# version 5: gpt-4o-mini
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": prompt,},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-4o-mini-2024-07-18',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt5'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt5'] = result['disagreement_areas']
    except Exception:
        df_agree.loc[i, 'error_gpt5'] = chat_completion.choices[0].message.content
df_agree['error_gpt5'] = df_agree['error_gpt5'].apply(lambda x: json.loads(x.replace('```json','').replace('```','').replace('\n',' ')) if x==x and x != 'nan' else np.nan)
df_agree['agreement_gpt5'] = df_agree.apply(lambda x: x['error_gpt5']['agreement'] if x['agreement_gpt5']!=x['agreement_gpt5'] or x['agreement_gpt5'] in ['nan', 'n'] else x['agreement_gpt5'], axis=1)
df_agree['disagreement_areas_gpt5'] = df_agree.apply(lambda x: x['error_gpt5']['disagreement_areas'] if x['disagreement_areas_gpt5']!=x['disagreement_areas_gpt5'] or x['disagreement_areas_gpt5'] in ['n', 'nan'] else x['disagreement_areas_gpt5'], axis=1)


# query v5:
print(accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt5']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt5'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt5'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

#%%
# version 6: gpt-3.5-turbo
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": prompt,},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-3.5-turbo',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt6'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt6'] = result['disagreement_areas']
    except Exception:
        df_agree.loc[i, 'error_gpt6'] = chat_completion.choices[0].message.content
df_agree['error_gpt6'] = df_agree['error_gpt6'].apply(lambda x: json.loads(x.replace('```json','').replace('```','').replace('\n',' ')) if x==x and x!= 'nan' else np.nan)
df_agree['agreement_gpt6'] = df_agree.apply(lambda x: x['error_gpt6']['agreement'] if x['agreement_gpt6']!=x['agreement_gpt6'] else x['agreement_gpt6'], axis=1)
df_agree['disagreement_areas_gpt6'] = df_agree.apply(lambda x: x['error_gpt6']['disagreement_areas'] if x['disagreement_areas_gpt6']!=x['disagreement_areas_gpt6'] else x['disagreement_areas_gpt6'], axis=1)


# query v6:
print(accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt6']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt6'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt6'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

#%%
# save
output_dir = Path(config.data_dir / 'Finetuning_data/llm_evaluation/fiscal/df_agree_gpt_v1.xlsx')
output_dir.parent.mkdir(parents=True, exist_ok=True)
df_agree.to_excel(output_dir, index=False)
#%%

# # 5. fine-tuning

# # 5.1. read training and testing files
# idx = 0
# df_train = pd.read_excel(directory+'finetuning/cv/fiscal/training_%d.xlsx'%idx)
# df_test = pd.read_excel(directory+'finetuning/cv/fiscal/testing_%d.xlsx'%idx)

# df_train_agree = df_train[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]
# df_test_agree = df_test[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]


# # 5.2. generate prompts and answers for the training set
# df_train_agree['answer'] = df_train_agree.fillna('').apply(lambda x:( "{'agreement': '%s', 'disagreement_areas': %s}" % (x['agreement_general'], str(x['disagreement_areas'].split('; ')))).replace("['']", "[]"), axis=1)
# df_train_agree['messages'] = df_train_agree.apply(lambda row: [
#                 {   "role": "system",
#                     "content": prompt,},
#                 {   "role": "user",
#                     "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])},
#                 {   "role": "assistant",
#                     "content":  row['answer']}
#             ], axis=1)

# df_train_agree[['messages']].to_json(directory+'fiscal/cv/training_fis_agree_%d.jsonl'%idx, orient='records', lines=True)

# # check fine-tuning dataset
# check_finetuning_dataset(directory+'finetuning/fiscal/cv/training_fis_agree_%d.jsonl'%idx)


# # 5.3. create fine-tuning job
# file = client.files.create(
#     file=open(directory+'cv/training_fis_agree_%d.jsonl'%idx, "rb"),
#     # file=open(directory+'training_mon.jsonl', "rb"),
#     purpose="fine-tune"
# )
# print(file.id)

# client.fine_tuning.jobs.create(
#     training_file=file.id,
#     model="gpt-4o-mini-2024-07-18"
#     # model="gpt-4o-2024-08-06"
# )

# # List up to 10 events from a fine-tuning job
# client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-Ksr7B3KaUeylj0VTS1KXsRjh", limit=3)

# # List the recent fine-tuning jobs
# client.fine_tuning.jobs.list(limit=2)


# # 5.4. Apply the fine-tuned model to testing set
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A3BXVE87'  # idx=0
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A3C6Ns5r'  # idx=1
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A3CSrPTF'  # idx=2
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A3DBKQm9'  # idx=3
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A3DhNo9A'  # idx=4

# for i,row in df_test_agree.iterrows():
#     chat_completion = client.chat.completions.create(
#         messages=[
#                 {   "role": "system",
#                     "content": prompt,},
#                 {   "role": "user",
#                     "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])},
#         ],
#         model=model_id,
#     )

#     try:
#         result = json.loads(chat_completion.choices[0].message.content.replace("'", '"').replace('```json','').replace('```','').replace('\n',' '))
#         df_test_agree.loc[i,'agreement_gpt_ft'] = result['agreement']
#         df_test_agree.loc[i,'disagreement_areas_gpt_ft'] = result['disagreement_areas']
#     except Exception:
#         df_test_agree.loc[i, 'error_gpt_ft'] = chat_completion.choices[0].message.content

# df_test_agree['error_gpt_ft'] = df_test_agree['error_gpt_ft'].apply(lambda x: json.loads(x.replace("'", '"').replace('s" ', "s' ").replace('"s ', "'s ").replace('```json','').replace('```','').replace('\n',' ')) if x==x and x not in ['nan', 'n'] else np.nan)
# df_test_agree['agreement_gpt_ft'] = df_test_agree.apply(lambda x: x['error_gpt_ft']['agreement'] if x['agreement_gpt_ft']!=x['agreement_gpt_ft'] or x['agreement_gpt_ft'] in ['nan', 'n'] else x['agreement_gpt_ft'], axis=1)
# df_test_agree['disagreement_areas_gpt_ft'] = df_test_agree.apply(lambda x: x['error_gpt_ft']['disagreement_areas'] if x['disagreement_areas_gpt_ft']!=x['disagreement_areas_gpt_ft'] or x['disagreement_areas_gpt_ft'] in ['nan', 'n'] else x['disagreement_areas_gpt_ft'], axis=1)

# # ft v1:
# print(accuracy_score(df_test_agree['agreement_general'], df_test_agree['agreement_gpt_ft']), f1_score(df_test_agree['agreement_general'], df_test_agree['agreement_gpt_ft'], average='weighted'), confusion_matrix(df_test_agree['agreement_general'], df_test_agree['agreement_gpt_ft'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

# # save results
# df_test_agree.drop('error_gpt_ft', axis=1).to_excel(directory+'llm_evaluation/fiscal/df_test_agree_fis_%d.xlsx'%idx, index=False)


# # 5.5. final training
# df_sample = pd.read_excel(directory+'labeling/monetary&fiscal/labelled/labelled_fiscal_v2.xlsx')
# df_agree = df_sample[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]
# df_agree['disagreement_areas'] = df_agree['disagreement_areas'].apply(lambda x: x.replace('government revenue', 'fiscal revenue').replace('government expenditure', 'fiscal expenditure').replace('economic fundamentals', 'economic assessment') if x==x else x)

# df_agree['answer'] = df_agree.fillna('').apply(lambda x:( "{'agreement': '%s', 'disagreement_areas': %s}" % (x['agreement_general'], str(x['disagreement_areas'].split('; ')))).replace("['']", "[]"), axis=1)
# df_agree['messages'] = df_agree.apply(lambda row: [
#                 {   "role": "system",
#                     "content": prompt,},
#                 {   "role": "user",
#                     "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])},
#                 {   "role": "assistant",
#                     "content":  row['answer']}
#             ], axis=1)

# df_agree[['messages']].to_json(directory+'finetuning/fiscal/all_fis_agree.jsonl', orient='records', lines=True)

# check_finetuning_dataset(directory+'finetuning/fiscal/all_fis_agree.jsonl')

# # create finetuning job
# file = client.files.create(
#     file=open(directory+'all_fis_agree.jsonl', "rb"),
#     purpose="fine-tune"
# )
# print(file.id)

# client.fine_tuning.jobs.create(
#     training_file=file.id,
#     model="gpt-4o-mini-2024-07-18"
# )

# # List up to 10 events from a fine-tuning job
# client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-hQvbjuWL4Zq6mc7dPtVvfoDf", limit=5)

# client.fine_tuning.jobs.list(limit=2)

# # save model id
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4q8cvri'  # agreement
