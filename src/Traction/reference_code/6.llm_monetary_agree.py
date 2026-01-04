'''
Experiment with GPT for monetary policy agreement classification tasks - zero shot, few shot, fine-tuning.
Input: labelled_monetary_v6.xlsx
Output: ../../data/llm_evaluation/monetary/...
'''
from util import *

directory = r'../../data/'

# read training and testing sets
# prepare files for different tasks
df = pd.read_excel(directory+'labeling/monetary&fiscal/labelled/labelled_monetary_v6.xlsx')

df_agree = df[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]


# 0. refine the agreement variables using GPT
# no predefined values for disagreement + chain of thought
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts written by IMF staff and a country's authority, determine whether the country's authority agree or disagree with IMF staff on issues related to the country's monetary policy and assign a value to the "agreement" field": if either of the texts does not discuss monetary policy or if they discuss entirely different aspects of monetary policy, assign "irrelevant"; if the two texts discuss common aspect(s) of monetary policy, assign "disagreement exists" if the authority disagrees with IMF staff on any monetary policy issues, and "mostly agree" if no disagreement exists. If disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; if the authority mostly agree, leave the "disagreement_areas" field blank. Provide reasoning for your answer. Return a JSON dict without additional texts: \"agreement\", \"disagreement_areas\", \"reason\".''',},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
        ],
            model='gpt-4o-2024-08-06',
            temperature=0
        )
    try:
        result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```','').replace('\n',' '))
        df_agree.loc[i,'agreement_gpt0'] = result['agreement']
        df_agree.loc[i,'disagreement_areas_gpt0'] = result['disagreement_areas']
        df_agree.loc[i,'reason_gpt0'] = result['reason']
    except Exception:
        df_agree.loc[i, 'error_gpt0'] = chat_completion.choices[0].message.content
df_agree['error_gpt0'] = df_agree['error_gpt0'].apply(lambda x: json.loads(x.replace('```json','').replace('```','').replace('\n',' ')) if x==x else np.nan)
df_agree['agreement_gpt0'] = df_agree.apply(lambda x: x['error_gpt0']['agreement'] if x['agreement_gpt0']!=x['agreement_gpt0'] else x['agreement_gpt0'], axis=1)
df_agree['disagreement_areas_gpt0'] = df_agree.apply(lambda x: x['error_gpt0']['disagreement_areas'] if x['disagreement_areas_gpt0']!=x['disagreement_areas_gpt0'] else x['disagreement_areas_gpt0'], axis=1)
df_agree['reason_gpt0'] = df_agree.apply(lambda x: x['error_gpt0']['reason'] if x['reason_gpt0']!=x['reason_gpt0'] else x['reason_gpt0'], axis=1)

accuracy_score(df_agree['agreement_general'], df_agree['agreement_gpt0']), f1_score(df_agree['agreement_general'], df_agree['agreement_gpt0'], average='weighted'), confusion_matrix(df_agree['agreement_general'], df_agree['agreement_gpt0'], labels=['disagreement exists', 'mostly agree', 'irrelevant'])

# df_agree.loc[df_agree[df_agree['Print ISBN']==9798400258442].index, 'agreement_general'] = 'disagreement exists'
# df_agree.at[df_agree[df_agree['Print ISBN']==9798400258442].index[0], 'disagreement_areas'] = ['Future Policy Direction']
# df.loc[df[df['Print ISBN']==9798400258442].index, 'agreement_general'] = 'disagreement exists'
# df.at[df[df['Print ISBN']==9798400258442].index[0], 'disagreement_areas'] = ['Future Policy Direction']
# df.loc[df[df['Print ISBN']==9798400258442].index, 'buff_stance_future'] = 'loosening bias'

# df_agree.loc[df_agree[df_agree['Print ISBN']==9781484301814].index, 'agreement_general'] = 'disagreement exists'
# df_agree.at[df_agree[df_agree['Print ISBN']==9781484301814].index[0], 'disagreement_areas'] = ['Future Policy Direction']
# df.loc[df[df['Print ISBN']==9781484301814].index, 'agreement_general'] = 'disagreement exists'
# df.at[df[df['Print ISBN']==9781484301814].index[0], 'disagreement_areas'] = ['Future Policy Direction']
# df.loc[df[df['Print ISBN']==9781484301814].index, 'staff_stance_future'] = 'loosening'

# df_agree.loc[df_agree[df_agree['Print ISBN']==9781475551327].index, 'agreement_general'] = 'disagreement exists'
# df_agree.at[df_agree[df_agree['Print ISBN']==9781475551327].index[0], 'disagreement_areas'] = ['Monetary Policy Operations']
# df.loc[df[df['Print ISBN']==9781475551327].index, 'agreement_general'] = 'disagreement exists'
# df.at[df[df['Print ISBN']==9781475551327].index[0], 'disagreement_areas'] = ['Monetary Policy Operations']

# df_agree.loc[df_agree[df_agree['Print ISBN']==9781484317327].index, 'agreement_general'] = 'disagreement exists'
# df_agree.at[df_agree[df_agree['Print ISBN']==9781484317327].index[0], 'disagreement_areas'] = ['Exchange Rate Policy']
# df.loc[df[df['Print ISBN']==9781484317327].index, 'agreement_general'] = 'disagreement exists'
# df.at[df[df['Print ISBN']==9781484317327].index[0], 'disagreement_areas'] = ['Exchange Rate Policy']

# df_agree.loc[df_agree[df_agree['Print ISBN']==9798400243127].index, 'agreement_general'] = 'disagreement exists'
# df_agree.at[df_agree[df_agree['Print ISBN']==9798400243127].index[0], 'disagreement_areas'] = ['Exchange Rate Policy']
# df.loc[df[df['Print ISBN']==9798400243127].index, 'agreement_general'] = 'disagreement exists'
# df.at[df[df['Print ISBN']==9798400243127].index[0], 'disagreement_areas'] = ['Exchange Rate Policy']

# df['disagreement_areas'] = df['disagreement_areas'].apply(lambda x: '; '.join(x) if type(x)==list else x)
# df['disagreement_areas'] = df['disagreement_areas'].apply(lambda x: '; '.join(x) if type(x)==list else x)
# df_agree['disagreement_areas'] = df_agree['disagreement_areas'].apply(lambda x: '; '.join(x) if type(x)==list else x)
# df_agree['disagreement_areas'] = df_agree['disagreement_areas'].apply(lambda x: '; '.join(x) if type(x)==list else x)

# # revise the labelled dataset
# df_final_orig = pd.read_excel(directory+'labeling/monetary&fiscal/labelled/labelled_monetary_v3.xlsx')
# df_final = pd.concat([df,df], ignore_index=True)
# key_columns = ['staff_stance_current', 'staff_stance_future', 'buff_stance_current',
#        'buff_stance_future', 'agreement_other', 'disagreement_areas']
# df_final.loc[df_final[df_final['Print ISBN']==9798400258442].index, 'buff_stance_future'] = 'loosening bias'
# for i, row in df_final_orig.iterrows():
#     try:
#         df_temp = df_final[df_final['Print ISBN']==row['Print ISBN']].iloc[0]
#         for col in key_columns:
#             if row[col]!=df_temp[col]:
#                 print(col)
#                 df_final_orig.loc[i, col] = df_temp[col]
#     except Exception:
#         pass
# df_final_orig['disagreement_areas'] = df_final_orig['disagreement_areas'].apply(lambda x: x.replace('Future Policy Stance', 'Future Policy Direction') if x==x else x)
# df_final_orig['agreement_stance_current'] = df_final_orig.apply(lambda x: 'irrelevant' if x['staff_stance_current'] in ['unclear', 'irrelevant'] or x['buff_stance_current'] in ['unclear', 'irrelevant'] else 'mostly agree' if x['staff_stance_current']==x['buff_stance_current'] else 'disagreement exists', axis=1)
# df_final_orig['agreement_stance_future'] = df_final_orig.apply(lambda x: 'irrelevant' if x['staff_stance_future'] in ['unclear', 'irrelevant'] or x['buff_stance_future'] in ['unclear', 'irrelevant'] else 'mostly agree' if x['staff_stance_future']==x['buff_stance_future'] else 'disagreement exists', axis=1)
# df_final_orig.loc[df_final_orig[(df_final_orig['agreement_stance_future']!='disagreement exists')&(df_final_orig['agreement_stance_current']!='disagreement exists')&(df_final_orig['agreement_other']!='disagreement exists')&(df_final_orig['agreement_general']=='disagreement exists')].index, 'agreement_other']='disagreement exists'
# df_final_orig.to_excel(directory+'labeling/monetary&fiscal/labelled/labelled_monetary_v3.xlsx', index=False)


# 1. define prompt
prompt = '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's monetary policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of monetary policy or if the authorities directly express agreement/disagreement to monetary related issues in either text: (a) if the authorities disagree with IMF staff on any monetary policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on monetary related issues, and either of the texts does not discuss monetary policy or they discuss entirely different aspects of monetary policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "current policy stance", "future policy direction", "monetary policy framework", "monetary policy operations", "central bank communication", "institutions", "economic assessment", etc; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank. Return a JSON dict without additional texts: "agreement", "disagreement_areas".'''


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


# 2.2. version 2: adding brief definitions
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's monetary policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of monetary policy or if the authorities directly express agreement/disagreement to monetary related issues in either text: (a) if the authorities disagree with IMF staff on any monetary policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on monetary related issues, and either of the texts does not discuss monetary policy or they discuss entirely different aspects of monetary policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank. Example areas include:\nCurrent Policy Stance: The current or recent monetary policy stance to influencing the economy through interest rates, money supply, etc.\nFuture Policy Direction: Planned or recommended direction of change in monetary policy stance.\nMonetary Policy Framework: The overall strategy and guidelines governing monetary policy decisions.\nMonetary Policy Operations: The specific actions taken to implement monetary policy, such as open market operations.\nCentral Bank Communication: How the central bank communicates its policy intentions and decisions to the public.\nInstitutions: The structure and role of institutions involved in monetary policy formulation and execution, including the independence of the central bank.\nPolicy Assessment: Evaluation of the effectiveness and outcomes of current or recent monetary policy.\nEconomic Assessment: The analysis of current economic conditions and forecasts that inform monetary policy.\nReturn a JSON dict without additional texts: "agreement", "disagreement_areas".''',},
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


# 2.3. version 3: chain-of-thought
for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's monetary policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of monetary policy or if the authorities directly express agreement/disagreement to monetary related issues in either text: (a) if the authorities disagree with IMF staff on any monetary policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on monetary related issues, and either of the texts does not discuss monetary policy or they discuss entirely different aspects of monetary policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "current policy stance", "future policy direction", "monetary policy framework", "monetary policy operations", "central bank communication", "institutions", "economic assessment", etc; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank. Provide reasoning before giving your answer. Return a JSON dict without additional texts: "reason", "agreement", "disagreement_areas".''',},
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


# 3. Few-shot
# version 4: adding a few examples
example_l = [
    '''Example 1:\nCountry: Mauritius; Year: 2015\n\nPart1 - IMF staff:\n44. The monetary policy stance is broadly appropriate given the low-inflation environment. Further excess liquidity absorption should proceed at a measured pace in order to avoid any sharp increases in market interest rates.\n\nPart2 - Authority:\nThe monetary policy pursued by Bank of Mauritius will remain cautiously accommodative to subdue inflation. In the same vein, efforts to gradually reduce excess domestic liquidity will be enhanced to improve the monetary policy transmission mechanism and without harming the overall money market conditions. The authorities welcome the analysis stating that the real effective exchange rate is broadly in line with fundamentals. Efforts to continue preserving this progress will be pursued with a careful monitoring of continued large inflows from the global business corporate (GBC) sector.\n\nAnswer: {"agreement": "mostly agree", "disagreement_areas": ""}.'''.replace('\n\n','\n'),
    '''Example 2:\nCountry: Guyana; Year: 2017\n\nPart1 - IMF staff:\n51. The accommodative monetary policy is appropriate, but should gradually move towards a neutral stance in 2017. Pass-through from the exchange rate and from the VAT reform to inflation should be closely monitored.\n\nPart2 - Authority:\n11. Monetary policy remained broadly accommodative in 2016. The BoG maintained the bank rate at 5 percent and ensured that liquidity levels in the banking system were conducive to facilitate lending to the private sector. According to BoG data, domestic interest rates fell during 2016 and in the first quarter of 2017. The authorities note staff’s recommendation to gradually tighten monetary policy in 2017. However, with benign price pressures and moderate growth, the BoG will continue to closely monitor domestic and international conditions before adjusting its policy stance.\n\nAnswer: {"agreement": "disagreement exists", "disagreement_areas": "Future Policy Stance"}.'''.replace('\n\n','\n'),
    '''Example 3:\nCountry: Libya; Year: 2023\n\nPart1 - IMF staff:\n53. To maintain public confidence in the nominal anchor, the central bank should continue in its efforts to reunify and avoid frequent changes to the currency peg. The reunification of the central bank is a crucial step towards achieving financial stability and fostering private sector development. Keeping the peg unchanged would allow the central bank to protect foreign exchange reserves and maintain macroeconomic stability amid political and security risks. In 2022, Libya’s external position was broadly in line with the fundamentals and desirable policy settings.\n\nPart2 - Authority:\nMonetary developments are largely driven by large swings in net claims on government as the government resorts to (interest free) monetary financing to meet budget shortfalls. Monetary management is further complicated by the parallel government’s borrowings from CBL-Al Bayda and printing bank notes on which the CBL-Tripoli has no control. The CBL has no instruments to control the monetary aggregates. Since the 2013 prohibition on interest, commercial banks have been setting their own internal rates in lending to the private sector. The CBL intends to develop Islamic finance products and has requested Fund TA.\n\nAnswer: {"agreement": "irrelevant", "disagreement_areas": ""}.'''.replace('\n\n','\n'),
]

for i, row in df_agree.iterrows():
    chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts expressing the views of IMF staff and a country's authorities, respectively, your task is to determine whether the authorities agree or disagree with IMF staff on issues related to the country's monetary policy. First, assign a value to the "agreement" field": "mostly agree"/"disagreement exists"/"irrelevant". Note that the authorities' agreement with IMF staff's views is different in concept from IMF staff's agreement with the authorities' views. If the two pieces of texts discuss common aspect(s) of monetary policy or if the authorities directly express agreement/disagreement to monetary related issues in either text: (a) if the authorities disagree with IMF staff on any monetary policy issues, assign "disagreement exists"; (b) if there is no disagreement by the authorities, assign "mostly agree"; (c) if the authorities do not directly express agreement/disagreement with IMF staff on monetary related issues, and either of the texts does not discuss monetary policy or they discuss entirely different aspects of monetary policy, assign "irrelevant".  Second, if disagreement exists, summarize the area(s) of disagreement in short phrase(s) and list them in the "disagreement_areas" field; for example, "current policy stance", "future policy direction", "monetary policy framework", "monetary policy operations", "central bank communication", "institutions", "economic assessment", etc; if the authorities do not disagree with staff, leave the "disagreement_areas" field blank.\n\n%s\n\nReturn a JSON dict without additional texts: \"agreement\", \"disagreement_areas\".'''%('\n\n'.join(example_l)),},
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

# save
df_agree.to_excel(directory+'llm_evaluation/monetary/df_train_agree_gpt.xlsx', index=False)


# 5. fine-tuning

# 5.1. read training and testing files
idx = 0
df_train = pd.read_excel(directory+'finetuning/cv/monetary/training_%d.xlsx'%idx)
df_test = pd.read_excel(directory+'finetuning/cv/monetary/testing_%d.xlsx'%idx)

df_train_agree = df_train[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]
df_test_agree = df_test[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]

df_train_agree['disagreement_areas'] = df_train_agree['disagreement_areas'].apply(lambda x: x.replace('Future Policy Stance', 'Future Policy Direction') if x==x else x)
df_test_agree['disagreement_areas'] = df_test_agree['disagreement_areas'].apply(lambda x: x.replace('Future Policy Stance', 'Future Policy Direction') if x==x else x)


# 5.2. generate prompts and answers for the training set
df_train_agree['answer'] = df_train_agree.fillna('').apply(lambda x:( "{'agreement': '%s', 'disagreement_areas': %s}" % (x['agreement_general'], str(x['disagreement_areas'].replace('Future Policy Stance', 'Future Policy Direction').split('; ')))).replace("['']", "[]"), axis=1)
df_train_agree['messages'] = df_train_agree.apply(lambda row: [
                {   "role": "system",
                    "content": prompt,},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])},
                {   "role": "assistant",
                    "content":  row['answer']}
            ], axis=1)

df_train_agree[['messages']].to_json(directory+'cv/training_mon_agree_%d.jsonl'%idx, orient='records', lines=True)
# df_train_agree[['messages']].to_json(directory+'training_mon_agree.jsonl', orient='records', lines=True)

# check fine-tuning dataset
check_finetuning_dataset(directory+'finetuning/monetary/cv/training_mon_agree_%d.jsonl'%idx)


# 5.3. create fine-tuning job
file = client.files.create(
    file=open(directory+'cv/training_mon_agree_%d.jsonl'%idx, "rb"),
    # file=open(directory+'training_mon.jsonl', "rb"),
    purpose="fine-tune"
)
print(file.id)

client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18"
    # model="gpt-4o-2024-08-06"
)

# List up to 10 events from a fine-tuning job
client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-ldrGeNI4ZSOCL8SBq9wBdvUB", limit=3)

# List the recent fine-tuning jobs
client.fine_tuning.jobs.list(limit=2)


# 5.4. Apply the fine-tuned model to testing set
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vZfLqyV'  # testing set
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vw0lgWO'  # idx=0
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vwjDDsr'  # idx=1
# model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vxD1H3x'  # idx=2
model_id = 'ft:gpt-4o-mini-2024-07-18:personal::9vxl1w0y'  # idx=3

for i,row in df_test_agree.iterrows():
    chat_completion = client.chat.completions.create(
        messages=[
                {   "role": "system",
                    "content": prompt,},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])},
        ],
        model=model_id,
        temperature=0
    )

    try:
        result = json.loads(chat_completion.choices[0].message.content.replace("'", '"').replace('```json','').replace('```','').replace('\n',' '))
        df_test_agree.loc[i,'agreement_gpt_ft4'] = result['agreement']
        df_test_agree.loc[i,'disagreement_areas_gpt_ft4'] = result['disagreement_areas']
#         df_test_agree.loc[i,'reason_gpt_ft2'] = result['reason']
    except Exception:
        df_test_agree.loc[i, 'error_gpt_ft4'] = chat_completion.choices[0].message.content

df_test_agree['error_gpt_ft4'] = df_test_agree['error_gpt_ft4'].apply(lambda x: json.loads(x.replace("'", '"').replace('s" ', "s' ").replace('"s ', "'s ").replace('```json','').replace('```','').replace('\n',' ')) if x==x and x not in ['nan', 'n'] else np.nan)
df_test_agree['agreement_gpt_ft4'] = df_test_agree.apply(lambda x: x['error_gpt_ft4']['agreement'] if x['agreement_gpt_ft4']!=x['agreement_gpt_ft4'] or x['agreement_gpt_ft4'] in ['nan', 'n'] else x['agreement_gpt_ft4'], axis=1)
df_test_agree['disagreement_areas_gpt_ft4'] = df_test_agree.apply(lambda x: x['error_gpt_ft4']['disagreement_areas'] if x['disagreement_areas_gpt_ft4']!=x['disagreement_areas_gpt_ft4'] or x['disagreement_areas_gpt_ft4'] in ['nan', 'n'] else x['disagreement_areas_gpt_ft4'], axis=1)
# df_test_agree['reason_gpt_ft2'] = df_test_agree.apply(lambda x: x['error_gpt_ft2']['reason'] if x['reason_gpt_ft2']!=x['reason_gpt_ft2'] else x['reason_gpt_ft2'], axis=1)

# ft v1:
print(accuracy_score(df_test_agree['agreement_general'], df_test_agree['agreement_gpt_ft4']), f1_score(df_test_agree['agreement_general'], df_test_agree['agreement_gpt_ft4'], average='weighted'), confusion_matrix(df_test_agree['agreement_general'], df_test_agree['agreement_gpt_ft4'], labels=['disagreement exists', 'mostly agree', 'irrelevant']))

# save results
df_test_agree.drop('error_gpt_ft4', axis=1).to_excel(directory+'llm_evaluation/monetary/df_test_agree_mon_%d.xlsx'%idx, index=False)


# 5.5. final training
df_sample = pd.read_excel(directory+'labeling/monetary&fiscal/labelled/labelled_monetary_v6.xlsx')
df_agree = df_sample[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']]
df_agree['disagreement_areas'] = df_agree['disagreement_areas'].apply(lambda x: x.lower() if x==x else x)

df_agree['answer'] = df_agree.fillna('').apply(lambda x:( "{'agreement': '%s', 'disagreement_areas': %s}" % (x['agreement_general'], str(x['disagreement_areas'].replace('Future Policy Stance', 'Future Policy Direction').split('; ')))).replace("['']", "[]"), axis=1)
df_agree['messages'] = df_agree.apply(lambda row: [
                {   "role": "system",
                    "content": prompt,},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authority:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])},
                {   "role": "assistant",
                    "content":  row['answer']}
            ], axis=1)

df_agree[['messages']].to_json(directory+'finetuning/monetary/all_mon_agree.jsonl', orient='records', lines=True)

check_finetuning_dataset(directory+'finetuning/monetary/all_mon_agree.jsonl')

# create finetuning job
file = client.files.create(
    file=open(directory+'all_mon_agree.jsonl', "rb"),
    purpose="fine-tune"
)
print(file.id)

client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18"
)

# List up to 10 events from a fine-tuning job
client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-bgpztdSB8IEOX0Db6GFjW63s", limit=5)

client.fine_tuning.jobs.list(limit=2)

# save model id
model_id = 'ft:gpt-4o-mini-2024-07-18:personal::A4qCO7QC'  # agreement
