'''
Experiment with GPT for monetary policy stance classification tasks - zero shot, few shot, fine-tuning.
Input: labelled_monetary_v6.xlsx
Output: ../../data/llm_evaluation/monetary/...
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
df = pd.read_excel(directory / 'Finetuning_data/labelled_monetary_v6.xlsx')

df_stance = pd.DataFrame()
for tp in ['staff', 'buff']:
    df_temp = df[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_current'%tp, '%s_stance_future'%tp]]
    df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
    df_temp['type'] = tp
    df_stance = pd.concat([df_stance, df_temp], ignore_index=True)


# 1. define prompt
type_dict1 = {'staff': 'IMF staff', 'buff': 'a country\'s authorities'}
type_dict2 = {'staff': 'IMF staff\'s', 'buff': 'country\'s authorities\''}
verb_dict = {'staff': 'recommended', 'buff': 'planned'}
explanation_dict = {'staff': 'Note that the near-term policy direction recommended by staff is different in concept from staff\'s projected near-term policy direction of the authorities.',
                    'buff': 'Note that the near-term policy direction planned by the authorities are different in concept from IMF staff\'s recommended or projected near-term policy direction.'}

prompt = '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, complete the following two tasks. First, classify the country\'s recent or current monetary policy stance as described in the text into "restrictive"/"neutral"/"accommodative"/"unclear"/"irrelevant"; if it discusses monetary policy but the specific stance is not clear, assign "unclear"; if it does not discuss monetary policy, assign "irrelevant". Second, classify the %s %s near-term (next year) direction of change in monetary policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s If the text indicates a leaning towards a tightening/loosening monetary policy but without a full commitment, assign "tightening bias"/"loosening bias". If the text discusses monetary policy stance but the direction of change is not clear, assign "no change". If it does not discuss monetary policy stance but discusses monetary policy, assign "unclear". If it does not discuss monetary policy, assign "irrelevant". Return a JSON dict without additional texts: \"stance_current\", \"stance_future\".'''  #%(type_dict1[ty],  type_dict2[ty],  verb_dict[ty], explanation_dict[ty])
#%%
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
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
        df_stance.loc[i,'stance_current_gpt1'] = result['stance_current']
        df_stance.loc[i,'stance_future_gpt1'] = result['stance_future']
    except Exception:
        df_stance.loc[i, 'error_gpt1'] = chat_completion.choices[0].message.content

# query v1:
print('raw:', accuracy_score(df_stance['stance_current'], df_stance['stance_current_gpt1']), 
      accuracy_score(df_stance['stance_future'], df_stance['stance_future_gpt1']), 
      f1_score(df_stance['stance_current'], df_stance['stance_current_gpt1'], average='weighted'), 
      f1_score(df_stance['stance_future'], df_stance['stance_future_gpt1'], average='weighted'), 
      'merging unclear/irrelevant:', 
      accuracy_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), 
                     df_stance['stance_current_gpt1'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), 
      accuracy_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), 
                     df_stance['stance_future_gpt1'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), 
      f1_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), 
               df_stance['stance_current_gpt1'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), 
      f1_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), 
               df_stance['stance_future_gpt1'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))
#%%
# 2.2. version 2: adding brief definitions
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, complete the following two tasks. First, classify the country\'s recent or current monetary policy stance as described in the text into "restrictive"/"neutral"/"accommodative"/"unclear"/"irrelevant". Definitions:\nRestrictive: The policy aims to reduce inflation and prevent the economy from overheating. This is typically achieved through higher interest rates or other measures that reduce the money supply.\nNeutral: The policy neither aims to reduce inflation nor stimulate the economy. It is intended to maintain the current economic conditions without significant changes.\nAccommodative: The policy aims to stimulate the economy, usually to combat unemployment or to encourage growth. This often involves lower interest rates or measures to increase the money supply.\nUnclear: The text discusses monetary policy but the specific stance is not clear.\nIrrelevant: The text does not discuss monetary policy.\n\nSecond, classify the %s %s near-term (next year) direction of change in monetary policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s Definitions:\nTightening: Suggests a plan to make the policy more restrictive, typically to combat inflation or overheating in the economy.\nTightening Bias: Indicates a leaning towards tightening, though not explicitly planning to do so.\nNo Change: Indicates a plan to maintain the current policy stance, or an unclear policy direction if the text discusses monetary policy stance.\nLoosening Bias: Suggests a leaning towards loosening, though not explicitly planning to do so.\nLoosening: Suggests a plan to make the policy more accommodative, typically to stimulate economic growth or combat unemployment.\nUnclear: The text discusses monetary policy but does not discuss monetary policy stance.\nIrrelevant: The text does not discuss monetary policy.\n\nReturn a JSON dict without additional texts: \"stance_current\", \"stance_future\".'''%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
        df_stance.loc[i,'stance_current_gpt2'] = result['stance_current']
        df_stance.loc[i,'stance_future_gpt2'] = result['stance_future']
    except Exception:
        df_stance.loc[i, 'error_gpt2'] = chat_completion.choices[0].message.content


# query v2:
print('raw:', accuracy_score(df_stance['stance_current'], df_stance['stance_current_gpt2']), accuracy_score(df_stance['stance_future'], df_stance['stance_future_gpt2']), f1_score(df_stance['stance_current'], df_stance['stance_current_gpt2'], average='weighted'), f1_score(df_stance['stance_future'], df_stance['stance_future_gpt2'], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt2'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), accuracy_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt2'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt2'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), f1_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt2'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))

#%%
# 2.3. version 3: chain-of-thought
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, complete the following two tasks. First, classify the country\'s recent or current monetary policy stance as described in the text into "restrictive"/"neutral"/"accommodative"/"unclear"/"irrelevant"; if it discusses monetary policy but the specific stance is not clear, assign "unclear"; if it does not discuss monetary policy, assign "irrelevant". Second, classify the %s %s near-term (next year) direction of change in monetary policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s If the text indicates a leaning towards a tightening/loosening monetary policy but without a full commitment, assign "tightening bias"/"loosening bias". If the text discusses monetary policy stance but the direction of change is not clear, assign "no change". If it does not discuss monetary policy stance but discusses monetary policy, assign "unclear". If it does not discuss monetary policy, assign "irrelevant". Provide reasoning before making your classifications. Return a JSON dict without additional texts: \"stance_current\", \"stance_future\", \"reason\".'''%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
        df_stance.loc[i,'stance_current_gpt3'] = result['stance_current']
        df_stance.loc[i,'stance_future_gpt3'] = result['stance_future']
        df_stance.loc[i,'reason_gpt3'] = result['reason']
    except Exception:
        df_stance.loc[i, 'error_gpt3'] = chat_completion.choices[0].message.content


# query v3:
print('raw:', accuracy_score(df_stance['stance_current'], df_stance['stance_current_gpt3']), accuracy_score(df_stance['stance_future'], df_stance['stance_future_gpt3']), f1_score(df_stance['stance_current'], df_stance['stance_current_gpt3'], average='weighted'), f1_score(df_stance['stance_future'], df_stance['stance_future_gpt3'], average='weighted'), 'merging unclear/irrelevant:', \
accuracy_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt3'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), accuracy_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt3'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt3'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), f1_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt3'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))
#%%

# 3. Few-shot
# version 4: adding a few examples
example_dict = {'staff': 'Example 1: Country: Guyana; Year: 2017; Text: \"The accommodative monetary policy is appropriate, but should gradually move towards a neutral stance in 2017. Pass-through from the exchange rate and from the VAT reform to inflation should be closely monitored.\" Answer: {\"stance_current\": \"accommodative\", \"stance_future\": \"tightening\"}.\nExample 2: Country: Mauritius; Year: 2015; Text: \"The monetary policy stance is broadly appropriate given the low-inflation environment. Further excess liquidity absorption should proceed at a measured pace in order to avoid any sharp increases in market interest rates.\" Answer: {\"stance_current\": \"unclear\", \"stance_future\": \"no change\"}.\nExample 3: Country: Trinidad and Tobago; Year: 2017; Text: \"The current monetary policy is appropriate, and in any case, room for maneuver is limited. Modest interest rate easing could eventually support a recovery, but would be contingent on reestablishing policy credibility with a strong fiscal package, wide-ranging structural reforms, and restoring balance in the f/x market.\" Answer: {\"stance_current\": \"unclear\", \"stance_future\": \"loosening bias\"}.',
               'buff': 'Example 1: Country: Guyana; Year: 2019; Text: \"Monetary policy remained broadly accommodative in 2018. The Bank of Guyana (BoG) maintained a bank rate of 5 percent, whilst ensuring an adequate level of liquidity in the banking system to create an enabling environment for credit and economic growth.\" Answer: {\"stance_current\": \"accommodative\", \"stance_future\": \"no change\"}.\nExample 2: Country: Bangladesh; Year: 2018; Text: \"The monetary policy stance will remain prudent, and the authorities are vigilant against upside risks to inflation and ready for appropriate adjustments in both policy rates and reserve requirements.\" Answer: {\"stance_current\": \"unclear\", \"stance_future\": \"tightening bias\"}.\nExample 3: Country: Iran; Year: 2015; Text: \"Monetary policy is guided by the disinflation strategy which seeks to achieve single-digit inflation by end 2016/17. While prioritizing price stability over output growth, my authorities are of the view that some temporary relief to the economy is needed at present, given sluggish growth, better-than-expected inflation outturns, benign inflation outlook, and tight fiscal stance.\" Answer: {\"stance_current\": \"restrictive\", \"stance_future\": \"loosening\"}.'}

for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of %s, complete the following two tasks. First, classify the country\'s recent or current monetary policy stance as described in the text into "restrictive"/"neutral"/"accommodative"/"unclear"/"irrelevant"; if it discusses monetary policy but the specific stance is not clear, assign "unclear"; if it does not discuss monetary policy, assign "irrelevant". Second, classify the %s %s near-term (next year) direction of change in monetary policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". %s If the text indicates a leaning towards a tightening/loosening monetary policy but without a full commitment, assign "tightening bias"/"loosening bias". If the text discusses monetary policy stance but the direction of change is not clear, assign "no change". If it does not discuss monetary policy stance but discusses monetary policy, assign "unclear". If it does not discuss monetary policy, assign "irrelevant".\n%s\n\nReturn a JSON dict without additional texts: \"stance_current\", \"stance_future\".'''%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']], example_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
        df_stance.loc[i,'stance_current_gpt4'] = result['stance_current']
        df_stance.loc[i,'stance_future_gpt4'] = result['stance_future']
    except Exception:
        df_stance.loc[i, 'error_gpt4'] = chat_completion.choices[0].message.content


# query v4:
print('raw:', accuracy_score(df_stance['stance_current'], df_stance['stance_current_gpt4']), accuracy_score(df_stance['stance_future'], df_stance['stance_future_gpt4']), f1_score(df_stance['stance_current'], df_stance['stance_current_gpt4'], average='weighted'), f1_score(df_stance['stance_future'], df_stance['stance_future_gpt4'], average='weighted'), 'merging unclear/irrelevant:', accuracy_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt4'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), accuracy_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt4'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt4'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), f1_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt4'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))
#%%

# 4. other models
# version 5: gpt-4o-mini
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-4o-mini-2024-07-18',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
        df_stance.loc[i,'stance_current_gpt5'] = result['stance_current']
        df_stance.loc[i,'stance_future_gpt5'] = result['stance_future']
    except Exception:
        df_stance.loc[i, 'error_gpt5'] = chat_completion.choices[0].message.content


# query v5:
print('raw:', accuracy_score(df_stance['stance_current'], df_stance['stance_current_gpt5']), accuracy_score(df_stance['stance_future'], df_stance['stance_future_gpt5']), f1_score(df_stance['stance_current'], df_stance['stance_current_gpt5'], average='weighted'), f1_score(df_stance['stance_future'], df_stance['stance_future_gpt5'], average='weighted'), 'merging unclear/irrelevant:', accuracy_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt5'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), accuracy_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt5'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt5'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), f1_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt5'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))

#%%
# version 6: gpt-3.5-turbo
for i, row in df_stance.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
        ],
            model='gpt-3.5-turbo',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
        df_stance.loc[i,'stance_current_gpt6'] = result['stance_current']
        df_stance.loc[i,'stance_future_gpt6'] = result['stance_future']
    except Exception:
        df_stance.loc[i, 'error_gpt6'] = chat_completion.choices[0].message.content


# query v6:
print('raw:', accuracy_score(df_stance['stance_current'], df_stance['stance_current_gpt6']), accuracy_score(df_stance['stance_future'], df_stance['stance_future_gpt6']), f1_score(df_stance['stance_current'], df_stance['stance_current_gpt6'], average='weighted'), f1_score(df_stance['stance_future'], df_stance['stance_future_gpt6'], average='weighted'), 'merging unclear/irrelevant:', accuracy_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt6'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), accuracy_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt6'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_current_gpt6'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), f1_score(df_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_stance['stance_future_gpt6'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))
#%%
# save
output_dir = Path(config.data_dir / 'Finetuning_data/llm_evaluation/monetary/df_stance_gpt_v2.xlsx')
output_dir.parent.mkdir(parents=True, exist_ok=True)
df_stance.to_excel(output_dir, index=False)

#%%
# 5. fine-tuning

# # 5.1. read training and testing files
# idx = 0
# df_train = pd.read_excel(directory / 'Finetuning_data/monetary/cv/training_%d.xlsx'%idx)
# df_test = pd.read_excel(directory / 'Finetuning_data/monetary/cv/testing_%d.xlsx'%idx)

# df_train_stance = pd.DataFrame()
# for tp in ['staff', 'buff']:
#     df_temp = df_train[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_current'%tp, '%s_stance_future'%tp]]
#     df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
#     df_temp['type'] = tp
#     df_train_stance = pd.concat([df_train_stance, df_temp], ignore_index=True)

# df_test_stance = pd.DataFrame()
# for tp in ['staff', 'buff']:
#     df_temp = df_test[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_current'%tp, '%s_stance_future'%tp]]
#     df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
#     df_temp['type'] = tp
#     df_test_stance = pd.concat([df_test_stance, df_temp], ignore_index=True)


# # 5.2. generate prompts and answers for the training set
# df_train_stance['answer'] = df_train_stance.apply(lambda x: "{'stance_current': '%s', 'stance_future': '%s'}" % (x['stance_current'], x['stance_future']), axis=1)
# df_train_stance['messages'] = df_train_stance.apply(lambda row: [
#                 {   "role": "system",
#                     "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
#                 {   "role": "user",
#                     "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])},
#                 {   "role": "assistant",
#                     "content":  row['answer']}
#             ], axis=1)

# df_train_stance[['messages']].to_json(directory / 'Finetuning_data/monetary/cv/training_mon_%d.jsonl'%idx, orient='records', lines=True)

# # check fine-tuning dataset
# check_finetuning_dataset(directory / 'Finetuning_data/monetary/cv/training_mon_%d.jsonl'%idx)


# # 5.3. create fine-tuning job
# file = client.files.create(
#     file=open(directory / 'Finetuning_data/monetary/cv/training_mon_%d.jsonl'%idx, "rb"),
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
# client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-JWA4derIBXyrqSKNbGqfnm5x", limit=3)

# # List the recent fine-tuning jobs
# client.fine_tuning.jobs.list(limit=2)


# # 5.4. Apply the fine-tuned model to testing set
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vPXXeG8'  # testing set
# # model_id = "ft:gpt-4o-mini-2024-07-18:personal::9vwKslca"  # idx = 0
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vwzGOOy'  # idx = 1
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vxnZ5mZ'  # idx = 2
# # model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vyT9aYE'  # idx = 3

# # model_id = 'ft:gpt-4o-2024-08-06:personal::A1SBk6Si'  # testing set
# # model_id = 'ft:gpt-4o-2024-08-06:personal::A1U18ml3'   # idx = 0
# # model_id = 'ft:gpt-4o-2024-08-06:personal::A1XyKzof'   # idx = 1
# # model_id = 'ft:gpt-4o-2024-08-06:personal::A3ERK599'  # idx = 2
# model_id = 'ft:gpt-4o-2024-08-06:personal::A3FKdjBr'  # idx = 3

# for i,row in df_test_stance.iterrows():
#     chat_completion = client.chat.completions.create(
#         messages=[
#                 {   "role": "system",
#                     "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
#                 {   "role": "user",
#                     "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])}
#         ],
#         model=model_id,
#         temperature=0
#     )
#     try:
#         result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace("\'", "\""))
#         df_test_stance.loc[i,'stance_current_gpt_ft'] = result['stance_current']
#         df_test_stance.loc[i,'stance_future_gpt_ft'] = result['stance_future']
#     except Exception:
#         df_test_stance.loc[i, 'error_gpt_ft'] = chat_completion.choices[0].message.content

# # df_test_stance['error_gpt_ft'] = df_test_stance['error_gpt_ft'].apply(lambda x: json.loads(x.replace("\'", "\"")))
# # df_test_stance['stance_current_gpt_ft'] = df_test_stance['error_gpt_ft'].apply(lambda x: x['stance_current'])
# # df_test_stance['stance_future_gpt_ft'] = df_test_stance['error_gpt_ft'].apply(lambda x: x['stance_future'])

# # ft v1:
# print('raw:', accuracy_score(df_test_stance['stance_current'], df_test_stance['stance_current_gpt_ft']), accuracy_score(df_test_stance['stance_future'], df_test_stance['stance_future_gpt_ft']), f1_score(df_test_stance['stance_current'], df_test_stance['stance_current_gpt_ft'], average='weighted'), f1_score(df_test_stance['stance_future'], df_test_stance['stance_future_gpt_ft'], average='weighted'), 'merging unclear/irrelevant:', accuracy_score(df_test_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_current_gpt_ft'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), accuracy_score(df_test_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_future_gpt_ft'].apply(lambda x: 'unclear' if x=='irrelevant' else x)), f1_score(df_test_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_current_gpt_ft'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'), f1_score(df_test_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_future_gpt_ft'].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted'))

# print(confusion_matrix(df_test_stance['stance_current'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_current_gpt_ft'].apply(lambda x: 'unclear' if x=='irrelevant' else x), labels=['accommodative', 'neutral', 'restrictive', 'unclear']))

# print(confusion_matrix(df_test_stance['stance_future'].apply(lambda x: 'unclear' if x=='irrelevant' else x), df_test_stance['stance_future_gpt_ft'].apply(lambda x: 'unclear' if x=='irrelevant' else x), labels=['tightening', 'tightening bias', 'no change', 'loosening bias', 'loosening', 'unclear']))

# # save results
# df_test_stance.to_excel(directory / 'Finetuning_data/llm_evaluation/monetary/df_test_stance_mon_%d.xlsx'%idx, index=False)


# # 5.5. final training
# df_sample = pd.read_excel(directory / 'Finetuning_data/labelled_monetary_v6.xlsx')

# df_stance = pd.DataFrame()
# for tp in ['staff', 'buff']:
#     df_temp = df_sample[['index', 'Print ISBN', 'country', 'year', tp, '%s_stance_current'%tp, '%s_stance_future'%tp]]
#     df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp+'_', '') for c in df_temp.columns})
#     df_temp['type'] = tp
#     df_stance = pd.concat([df_stance, df_temp], ignore_index=True)

# df_stance['answer'] = df_stance.apply(lambda x: "{'stance_current': '%s', 'stance_future': '%s'}" % (x['stance_current'], x['stance_future']), axis=1)
# df_stance['messages'] = df_stance.apply(lambda row: [
#                 {   "role": "system",
#                     "content": prompt%(type_dict1[row['type']],  type_dict2[row['type']],  verb_dict[row['type']], explanation_dict[row['type']]),},
#                 {   "role": "user",
#                     "content":  '''Country: %s; Year: %s\nText:\n%s''' % (row['country'], row['year'], row['text'])},
#                 {   "role": "assistant",
#                     "content":  row['answer']}
#             ], axis=1)

# df_stance[['messages']].to_json(directory / 'Finetuning_data/monetary/all_mon.jsonl', orient='records', lines=True)

# check_finetuning_dataset(directory / 'Finetuning_data/monetary/all_mon.jsonl')

# # create finetuning job
# file = client.files.create(
#     file=open(directory / 'Finetuning_data/monetary/all_mon.jsonl', "rb"),
#     purpose="fine-tune"
# )
# print(file.id)

# client.fine_tuning.jobs.create(
#     training_file=file.id,
#     model="gpt-4o-mini-2024-07-18"
# )

# # List up to 10 events from a fine-tuning job
# client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-9pUpJdb54chA35VY5krQujDs", limit=5)

# client.fine_tuning.jobs.list(limit=2)

# # save model id
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4qneai9'  # stance
