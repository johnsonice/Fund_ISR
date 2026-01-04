'''
Perform topic modelling on paragraph-level data. Classify paragraph into staff/authorities' views. Aggregate paragraph-level analysis results to document level.
Input: df_paragraphs.csv
Output: df_paragraphs_type_topics.csv, df_documents.csv, df_documents_sector.csv, df_documents_funda.csv
'''
from util import *

directory = r'../../data/'

# read data
df_paragraphs = pd.read_csv(directory+'output/df_paragraphs.csv')
df_meta = pd.read_excel(directory+'aiv/IMF_Main_MetaData_20240710_toRan_filtered.xlsx')
df = pd.read_csv(directory+'output/df_aiv_funda.csv')

# 1. topic modelling by GPT
for i,row in df_paragraphs.iterrows():
    if i >= 0 and (row['topic_labels']!=row['topic_labels'] and row['gpt_error']!=row['gpt_error']):
        chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Your job is to assign topic labels to a given paragraph from IMF document.
You are given a list of topics with their definition and key indicators as below:
----------------
----------------
1. **Real Sector**:
   - **Definition**: The real sector encompasses the production and consumption of goods and services in an economy. It includes activities related to agriculture, manufacturing, services, and trade.
   - **Key Indicators**: GDP, industrial production, employment rates, and productivity.

2. **Fiscal Sector**:
   - **Definition**: The fiscal sector involves government revenue and expenditure. It includes taxation, government spending, budget deficits/surpluses, and public debt.
   - **Key Indicators**: Government budget balance, public debt-to-GDP ratio, tax revenue, and government expenditure.

3. **Monetary Sector**:
   - **Definition**: The monetary sector deals with the supply of money, interest rates, and the overall monetary policy managed by a country's central bank.
   - **Key Indicators**: Money supply (M1, M2, etc.), interest rates, inflation rates, and central bank policy rates.

4. **Financial Sector**:
   - **Definition**: The financial sector includes institutions and markets that facilitate the flow of funds between savers and borrowers. It encompasses banks, stock markets, bond markets, and other financial intermediaries.
   - **Key Indicators**: Stock market indices, bond yields, bank lending rates, and financial stability indicators.

5. **External Sector**:
   - **Definition**: The external sector covers a country's international economic transactions, including trade in goods and services, cross-border investment, and foreign exchange markets.
   - **Key Indicators**: Trade balance, current account balance, foreign direct investment (FDI), exchange rates, and international reserves.

6. **Other**:
   - **Definition**: Any other topics that do not fall into the above list, such as Inclusion, Governance, Technology, Climate Change, etc.
----------------
----------------

Given a paragraph from a report published by the International Monetary Fund, please carefully analyze the paragraph and classify the provided paragraph using ONLY the provided topics. If the paragraph does not fit into any of the provided topics, assign "Other".
Try your best to assign only one topic to the paragraph. You can use multiple categories only if you are very confident that multiple topics are all extensively discussed by the majority of the paragraph.
Please provide your reasoning for your classification first, and then provide the topic label and a confidence score from 0-100.

Please respond in clean json format as follow:
reasoning: <explanation for topic label >,
topic_labels: [<topic label: confidence score>,...]''',},
                {   "role": "user",
                    "content":  row['text']}
            ],
            model="gpt-4o",
            temperature=0
        )
        try:
            result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
            df_paragraphs.loc[i,'topic_labels'] = result['topic_labels']
            df_paragraphs.loc[i,'reasoning'] = result['reasoning']
        except Exception:
            df_paragraphs.loc[i, 'gpt_error'] = chat_completion.choices[0].message.content


# 2. post-processing
for i, row in df_paragraphs[~df_paragraphs['gpt_error'].isna()].iterrows():
    try:
        result = json.loads(row['gpt_error'].replace('```json','').replace('```',''))
        df_paragraphs.at[i,'topic_labels'] = result['topic_labels']
        df_paragraphs.loc[i,'reasoning'] = result['reasoning']
    except Exception:
        print(row['text'])
df_paragraphs = df_paragraphs[~df_paragraphs['topic_labels'].isna()]

idx_l = df_paragraphs[df_paragraphs['topic_labels'].apply(lambda x: type(x)==str)].index
df_paragraphs.loc[idx_l, 'topic_labels'] = df_paragraphs.loc[idx_l, 'topic_labels'].apply(lambda x: ast.literal_eval(x))

df_paragraphs['topic_labels'] = df_paragraphs['topic_labels'].apply(lambda x: [x] if type(x)==dict else x)

idx_l = df_paragraphs[df_paragraphs['topic_labels'].apply(lambda x: type(x)==list and type(x[0])==list)].index
df_paragraphs.loc[idx_l, 'topic_labels'] = df_paragraphs.loc[idx_l, 'topic_labels'].apply(lambda x: x[0])
df_paragraphs.loc[idx_l, 'topic_labels'] = df_paragraphs.loc[idx_l, 'topic_labels'].apply(lambda x: {x[0]: x[1]})

idx_l = df_paragraphs[df_paragraphs['topic_labels'].apply(lambda x: type(x)==list and type(x[0])==str)].index
df_paragraphs.loc[idx_l, 'topic_labels'] = df_paragraphs.loc[idx_l, 'topic_labels'].apply(lambda x: {x[i].split(':')[0].strip():int(x[i].split(':')[1].strip()) for i in range(len(x))})

idx_l = df_paragraphs[df_paragraphs['topic_labels'].apply(lambda x: type(x)==list and type(x[0])==dict and list(x[0].keys())[0] in ['Monetary Sector', 'Fiscal Sector', 'External Sector', 'Financial Sector', 'Real Sector', 'Other'])].index
df_paragraphs.loc[idx_l, 'topic_labels'] = df_paragraphs.loc[idx_l, 'topic_labels'].apply(lambda x: reduce(lambda a, b: dict(a, **b), x))

idx_l = df_paragraphs[df_paragraphs['topic_labels'].apply(lambda x: type(x)==list and type(x[0])==dict and list(x[0].keys())[0] not in ['Monetary Sector', 'Fiscal Sector', 'External Sector', 'Financial Sector', 'Real Sector', 'Other'])].index
df_paragraphs.loc[idx_l, 'topic_labels'] = df_paragraphs.loc[idx_l, 'topic_labels'].apply(lambda x: {[v for v in list(x[i].values()) if type(v)==str][0]:[v for v in list(x[i].values()) if type(v)==int][0] for i in range(len(x))})

df_paragraphs['Monetary'] = df_paragraphs['topic_labels'].apply(lambda x: x['Monetary Sector'] if x==x and 'Monetary Sector' in x else 100 if x==x and 'topic_label' in x and x['topic_label']=='Monetary Sector' else 100 if x==x and 'topic label' in x and x['topic label']=='Monetary Sector' else 100 if x==x and 'topic' in x and x['topic']=='Monetary Sector' else 0)
df_paragraphs['Fiscal'] = df_paragraphs['topic_labels'].apply(lambda x: x['Fiscal Sector'] if x==x and 'Fiscal Sector' in x else 100 if x==x and 'topic_label' in x and x['topic_label']=='Fiscal Sector' else 100 if x==x and 'topic label' in x and x['topic label']=='Fiscal Sector' else 100 if x==x and 'topic' in x and x['topic']=='Fiscal Sector' else 0)
df_paragraphs['External'] = df_paragraphs['topic_labels'].apply(lambda x: x['External Sector'] if x==x and 'External Sector' in x else 100 if x==x and 'topic_label' in x and x['topic_label']=='External Sector' else 100 if x==x and 'topic label' in x and x['topic label']=='External Sector' else 100 if x==x and 'topic' in x and x['topic']=='External Sector' else 0)
df_paragraphs['Financial'] = df_paragraphs['topic_labels'].apply(lambda x: x['Financial Sector'] if x==x and 'Financial Sector' in x else 100 if x==x and 'topic_label' in x and x['topic_label']=='Financial Sector' else 100 if x==x and 'topic label' in x and x['topic label']=='Financial Sector' else 100 if x==x and 'topic' in x and x['topic']=='Financial Sector' else 0)
df_paragraphs['Real'] = df_paragraphs['topic_labels'].apply(lambda x: x['Real Sector'] if x==x and 'Real Sector' in x else 100 if x==x and 'topic_label' in x and x['topic_label']=='Real Sector' else 100 if x==x and 'topic label' in x and x['topic label']=='Real Sector' else 100 if x==x and 'topic' in x and x['topic']=='Real Sector' else 0)
df_paragraphs['Other'] = df_paragraphs['topic_labels'].apply(lambda x: x['Other'] if x==x and 'Other' in x else 100 if x==x and 'topic_label' in x and x['topic_label']=='Other' else 100 if x==x and 'topic label' in x and x['topic label']=='Other' else 100 if x==x and 'topic' in x and x['topic']=='Other' else 0)

df_paragraphs['max_topic'] = df_paragraphs.apply(lambda x: np.max([x['Monetary'], x['Fiscal'], x['External'], x['Financial'], x['Real'], x['Other']]), axis=1)
for topic in ['Monetary', 'Fiscal', 'External', 'Financial', 'Real', 'Other']:
    df_paragraphs['%s_dummy'%topic] = (df_paragraphs[topic]==df_paragraphs['max_topic'])&(df_paragraphs[topic]>=70)

df_paragraphs.to_excel(directory+'output/paragraphs_topic_sample.xlsx', index=False)


# 3. adjust staff appraisal part
df_paragraphs = pd.read_excel(directory+'output/paragraphs_topic_sample.xlsx')

# df['paragraphs_sa'] = df['paragraphs_sa'].apply(lambda x: ast.literal_eval(x))
staff_para_l = list(itertools.chain.from_iterable(df['paragraphs_sa']))
idx_l = df_paragraphs[df_paragraphs['type']=='staff'][~df_paragraphs[df_paragraphs['type']=='staff']['text'].apply(lambda x: x in staff_para_l)].index
df_paragraphs.loc[idx_l, 'to_drop_sa'] = True
df_paragraphs.loc[idx_l, 'to_drop'] = True

# df['paragraphs_bu'] = df['paragraphs_bu'].apply(lambda x: ast.literal_eval(x))
buff_para_l = list(itertools.chain.from_iterable(df['paragraphs_bu']))
idx_l = df_paragraphs[df_paragraphs['type']=='buff'][~df_paragraphs[df_paragraphs['type']=='buff']['text'].apply(lambda x: x in buff_para_l)].index
df_paragraphs.loc[idx_l, 'to_drop_bu'] = True
df_paragraphs.loc[idx_l, 'to_drop'] = True

df_paragraphs.to_excel(directory+'output/paragraphs_topic_sample.xlsx', index=False)


# 4. staff/authorities view classification
# read data
df_paragraphs = pd.read_csv(directory+'df_paragraphs_topics.csv')
df = df_paragraphs[(df_paragraphs['av_uncertain']==True)&(df_paragraphs['text'].apply(lambda x: 'authorit' in x.lower()))]
df['text'] = df['text'].apply(lambda x: x[re.search(r'[A-Za-z]', x).start():])
idx_l1 = df[df['text'].apply(lambda x: x.lower().startswith('authorities views') or x.lower().startswith('the authorities views') or x.lower().startswith('authorities view on') or x.lower().startswith('the authorities view on'))].index
df_paragraphs.loc[idx_l1, 'av_uncertain'] = False
df.drop(idx_l1, inplace=True)

# classification by GPT
for i, row in df_paragraphs[df_paragraphs['av_uncertain']==True].iterrows():
    if i >= 0:
        chat_completion = client.chat.completions.create(
                    messages=[
                        {   "role": "system",
                            "content": '''You are an experience macroeconomist from IMF. Given a paragraph from an IMF Article IV staff report, your task is to classify whether it mostly describes the views of the country's authorities or the views/recommendations of IMF staff. The paragraphs describing authorities' views usually contain sentences with "authorities" or "they" as the subject, and have verbs such as "agree", "disagree", "appreciate", "concur", "share", "emphasize", "note", "view", "consider", "intend" and "plan". In contrast, paragraphs that have "authorities" as the subject but describe the views/recommendations of IMF staff may contain the following words: 'need','encourage','advise','suggest','recommend','urge','propose','request','should', 'could', and 'must'. Paragraphs with no sentences having "authorities" as subject are also likely to be staff views. If a paragraph is just describing facts without expressing views, classify it as staff views.
        Example 1. Text: "The authorities were more optimistic on the growth outlook." Classification: authorities
        Example 2: Text: "The authorities’ initiatives to strengthen systemic risk monitoring are welcome." Classification: staff
        Example 3. Text: "Inflation has been below the target band, reflecting low food and oil prices, but is expected to rise to the middle of the band in 2017." Classification: staff
        Please respond one of the following classifications without returning additional texts: \"authorities\", \"staff\".''',},
                        {   "role": "user",
                            "content":  row['text']}
                    ],
                    model="gpt-4o-mini",
                    temperature=0
                )

        result = chat_completion.choices[0].message.content
        df_paragraphs.loc[i,'av_gpt'] = result

df_paragraphs.loc[df_paragraphs[df_paragraphs['av_gpt']=='authorities'].index, 'type'] = 'buff_a'
df_paragraphs.loc[df_paragraphs[df_paragraphs['av_gpt']=='staff'].index, 'type'] = 'staff_a'

# save
df_paragraphs.to_csv(directory+'output/df_paragraphs_type.csv', index=False)


# 5. merge files with topic modelling and type classification results
df_paragraphs = pd.read_csv(directory+'output/df_paragraphs.csv')
# merge topics - part 1
df_paragraphs_topics = pd.read_excel(directory+'output/paragraphs_topic_sample.xlsx')
df_paragraphs = df_paragraphs.merge(df_paragraphs_topics.drop('to_drop', axis=1), on=['Print ISBN', 'text', 'type'], how='left').sort_values(by=['Print ISBN', 'type', 'text'])
df_paragraphs = df_paragraphs[~df_paragraphs['to_drop']]

df_paragraphs_topics['text'].apply(lambda x: x.count(' ')).sum(), df_paragraphs[df_paragraphs['Monetary_dummy'].isna()]['text'].apply(lambda x: x.count(' ')).sum(), len(df_paragraphs_topics), len(df_paragraphs[df_paragraphs['Monetary_dummy'].isna()])
df_paragraphs.to_csv(directory+'output/gpt/df_paragraphs_topics.csv')

# after using GPT for classification
df_paragraphs = pd.read_csv(directory+'output/df_paragraphs.csv')
df_paragraphs = df_paragraphs[~df_paragraphs['to_drop']]
date_dict = df_meta.set_index('Print ISBN')['Publication Date'].to_dict()
df_paragraphs['year'] = df_paragraphs['Print ISBN'].apply(lambda x: year_dict[int(x)] if int(x) in year_dict else np.nan)
df_paragraphs = df_paragraphs[df_paragraphs['year']!=2024]

# update paragraph type
df_paragraphs_type = pd.read_csv(directory+'output/type/df_paragraphs_type.csv')
type_dict = df_paragraphs_type[~df_paragraphs_type['av_gpt'].isna()].set_index(['Print ISBN', 'text'])['type'].to_dict()
df_paragraphs['type'] = df_paragraphs.apply(lambda x: type_dict[(x['Print ISBN'], x['text'])] if (x['Print ISBN'], x['text']) in type_dict and x['av_uncertain']==True else x['type'], axis=1)
df_paragraphs = df_paragraphs.drop(df_paragraphs[(df_paragraphs.duplicated(subset=['Print ISBN', 'text'], keep=False))&(df_paragraphs['type'].apply(lambda x: '_a' in x))].index)

# update paragraph topics
df_p1 = pd.read_csv(directory+'output/topic/df_paragraphs_topics_updated_p1.csv')
df_p2 = pd.read_csv(directory+'output/topic/df_paragraphs_topics_updated_p2.csv')
topic_var_l = ['topic_labels', 'gpt_error',
       'reasoning', 'Monetary', 'Fiscal', 'External', 'Financial', 'Real',
       'Other', 'max_topic', 'Monetary_dummy', 'Fiscal_dummy',
       'External_dummy', 'Financial_dummy', 'Real_dummy', 'Other_dummy']
for var in topic_var_l:
    df_p1.loc[45000:,var] = df_p2.loc[45000:,var]
df_paragraphs = df_paragraphs.merge(df_p1[~df_p1.duplicated(subset=['Print ISBN', 'text'])][['Print ISBN', 'text']+topic_var_l], on=['Print ISBN', 'text'], how='left')


# 6. save
df_paragraphs.to_csv(directory+'output/df_paragraphs_type_topics.csv')


# 7. aggregate paragraph-level results into document-level
df_paragraphs = pd.read_csv(directory+'output/df_paragraphs_type_topics.csv')
# generate document sample - general
sample_l = set(df_paragraphs['Print ISBN'])
result_l = []
for idx in sample_l:
    temp = {'Print ISBN': idx}
    for ty in ['staff', 'buff']:
        temp[ty] = '\n'.join(df_paragraphs[(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty+'_a')]['text']) + '\n' + '\n'.join(df_paragraphs[(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty)]['text'])
    result_l.append(temp)
df_documents = pd.DataFrame(result_l)

country_dict = df_meta.set_index('Print ISBN')['Title'].to_dict()
year_dict = df_meta.set_index('Print ISBN')['Year from title'].to_dict()
date_dict = df_meta.set_index('Print ISBN')['Publication Date'].to_dict()
df_documents['country'] = df_documents['Print ISBN'].apply(lambda x: country_dict[int(x)] if int(x) in country_dict else np.nan)
df_documents['year'] = df_documents['Print ISBN'].apply(lambda x: year_dict[int(x)] if int(x) in year_dict else np.nan)
df_documents['publication_date'] = df_documents['Print ISBN'].apply(lambda x: date_dict[int(x)] if int(x) in year_dict else np.nan)

df_documents.loc[df_documents[df_documents['Print ISBN']==9781484334850].index, 'year'] = 2017
df_documents.loc[df_documents[df_documents['Print ISBN']==9781475564082].index, 'year'] = 2016
df_documents.loc[df_documents[df_documents['Print ISBN']==9781484334980].index, 'year'] = 2017
df_documents.loc[df_documents[df_documents['Print ISBN']==9781616356767].index, 'year'] = 2021

df_documents['country'] = df_documents['country'].apply(lambda x: x.replace('—', '-') if ':' not in x else x.split(':')[0].strip().replace('—', '-').replace('’', "'"))

# save
df_documents.reset_index().to_csv(directory+'output/df_documents.csv', index=False)

# add fundamentals to the file
df = pd.read_csv(directory+'output/df_aiv_funda.csv')
df_documents = pd.read_csv(directory+'output/df_documents.csv')
df_documents = df_documents.drop(['year', 'country'], axis=1).merge(df, how='right')
df_documents.to_csv(directory+'output/df_documents_funda.csv', index=False)


# 8. separate document texts by sector
# df = pd.read_csv(directory+'output/df_aiv_funda.csv')
topic_l = ['Monetary', 'Fiscal', 'External', 'Financial', 'Real']
sample_l = set(df_paragraphs['Print ISBN'])
result_l = []

for t in topic_l:
    for idx in sample_l:
        temp = {'Print ISBN': idx, 'sector': t}
        for ty in ['staff', 'buff']:
            if t in ['Monetary', 'External']:
                temp[ty] = '\n'.join(df_paragraphs[(df_paragraphs[t]>=50)&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty+'_a')]['text']) + '\n' + '\n'.join(df_paragraphs[(df_paragraphs[t]>=50)&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty)]['text'])
            else:
                temp[ty] = '\n'.join(df_paragraphs[(df_paragraphs[t]>=70)&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty+'_a')]['text']) + '\n' + '\n'.join(df_paragraphs[(df_paragraphs[t]>=70)&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty)]['text'])
            if temp[ty]=='\n' and (t != 'Monetary' or df[df['Print ISBN']==idx]['monetary_sample'].iloc[0]==True): # and (ty=='staff' or df[df['Print ISBN']==idx]['buff_verified'].iloc[0]==True):
                temp[ty] = '\n'.join(df_paragraphs[(df_paragraphs[t]>0)&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty+'_a')]['text']) + '\n' + '\n'.join(df_paragraphs[(df_paragraphs[t]>0)&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty)]['text'])
            if temp[ty]=='\n' and (t != 'Monetary' or df[df['Print ISBN']==idx]['monetary_sample'].iloc[0]==True): # and (ty=='staff' or df[df['Print ISBN']==idx]['buff_verified'].iloc[0]==True):
                if t in ['Monetary', 'Fiscal', 'Financial']:
                    temp[ty] = '\n'.join(df_paragraphs[(df_paragraphs['text'].apply(lambda x: t.lower() in x.lower()))&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty+'_a')]['text']) + '\n' +'\n'.join(df_paragraphs[(df_paragraphs['text'].apply(lambda x: t.lower() in x.lower()))&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty)]['text'])
                elif t == 'External':
                    temp[ty] = '\n'.join(df_paragraphs[(df_paragraphs['text'].apply(lambda x: t.lower() in x.lower() or 'current account' in x.lower() or 'exchange rate' in x.lower() or 'capital flow' in x.lower() or 'foreign reserve' in x.lower()))&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty+'_a')]['text']) + '\n' + '\n'.join(df_paragraphs[(df_paragraphs['text'].apply(lambda x: t.lower() in x.lower() or 'current account' in x.lower() or 'exchange rate' in x.lower() or 'capital flow' in x.lower() or 'foreign reserve' in x.lower()))&(df_paragraphs['Print ISBN']==idx)&(df_paragraphs['type']==ty)]['text'])
        result_l.append(temp)

df_documents = pd.DataFrame(result_l)

country_dict = df.set_index('Print ISBN')['country'].to_dict()
year_dict = df.set_index('Print ISBN')['year'].to_dict()
df_documents['country'] = df_documents['Print ISBN'].apply(lambda x: country_dict[int(x)] if int(x) in country_dict else np.nan)
df_documents['year'] = df_documents['Print ISBN'].apply(lambda x: year_dict[int(x)] if int(x) in year_dict else np.nan)
df_documents['publication_date'] = df_documents['Print ISBN'].apply(lambda x: date_dict[int(x)] if int(x) in year_dict else np.nan)

# df_documents['staff_len'] = df_documents['staff'].apply(lambda x: x.count(' ')+x.count('\n'))
# df_documents['buff_len'] = df_documents['buff'].apply(lambda x: x.count(' ')+x.count('\n'))
# df_documents['length'] = df_documents['staff_len'] + df_documents['buff_len']
df_documents = df_documents.merge(df[~df['Print ISBN'].isna()], on=['Print ISBN', 'country', 'year'], how='left')
df_documents['staff'] = df_documents['staff'].apply(lambda x: '' if x=='\n' else x)
df_documents['buff'] = df_documents['buff'].apply(lambda x: '' if x=='\n' else x)

# save
df_documents.to_csv(directory+'df_documents_sector.csv', index=False)