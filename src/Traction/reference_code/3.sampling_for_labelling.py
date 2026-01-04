'''
Randomly sample documents for labelling. Process labelling results. Generate training / testing sets for fine-tuning.
Input: df_paragraphs_type_topics.csv
Output: to_label_all.xlsx, labelled_monetary.xlsx, labelled_fiscal.xlsx; training.xlsx, testing.xlsx
'''
from util import *

directory = r'../../data/'

# read data
df_paragraphs = pd.read_csv(directory+'output/df_paragraphs_type_topics.csv')
df_meta = pd.read_excel(directory+'aiv/IMF_Main_MetaData_20240710_toRan_filtered.xlsx')


# 1. generate files to label
sample_l = set(df_paragraphs['Print ISBN'])

topic_l = ['Monetary', 'Fiscal', 'External', 'Financial', 'Real']
result_l = []
for t in topic_l:
    for idx in sample_l:
        temp = {'Print ISBN': idx, 'sector': t}
        for ty in ['staff', 'buff']:
            temp[ty] = '\n'.join(df_paragraphs[
                                     (df_paragraphs[t + '_dummy'] == True) & (
                                                 df_paragraphs[
                                                     'Print ISBN'] == idx) & (
                                                 df_paragraphs['type'] == ty)][
                                     'text'])
        result_l.append(temp)

df_documents = pd.DataFrame(result_l)

country_dict = df_meta.set_index('Print ISBN')['Title'].to_dict()
year_dict = df_meta.set_index('Print ISBN')['Year from title'].to_dict()
df_documents['country'] = df_documents['Print ISBN'].apply(
    lambda x: country_dict[int(x)] if int(x) in country_dict else np.nan)
df_documents['year'] = df_documents['Print ISBN'].apply(
    lambda x: year_dict[int(x)] if int(x) in year_dict else np.nan)

df_documents['staff_len'] = df_documents['staff'].apply(
    lambda x: x.count(' ') + x.count('\n'))
df_documents['buff_len'] = df_documents['buff'].apply(
    lambda x: x.count(' ') + x.count('\n'))
df_documents['length'] = df_documents['staff_len'] + df_documents['buff_len']

df_documents.to_excel(directory + 'labeling/to_label_full_p2.xlsx', index=False)

# # combine the two parts (p2 as updates)
df_documents = pd.read_excel(directory+'to_label_full_p1.xlsx')
temp = df_documents[df_documents['sector'].apply(lambda x: x in ['Monetary', 'Fiscal'])][(df_documents['staff']!='')&(df_documents['buff']!='')&(df_documents['country']==df_documents['country'])].groupby('Print ISBN').count()['sector']
sample_fin_l = list(temp[temp==2].index)
df_documents_p1 = df_documents[df_documents['Print ISBN'].apply(lambda x: x in sample_fin_l)]
df_documents_p1[df_documents_p1['sector'].apply(lambda x: x in ['Monetary', 'Fiscal'])].to_excel(directory+'labeling/to_label_p1.xlsx', index=False)

df_documents = pd.read_excel(directory+'to_label_full_p2.xlsx')
temp = df_documents[df_documents['sector'].apply(lambda x: x in ['Monetary', 'Fiscal'])][(df_documents['staff']!='')&(df_documents['buff']!='')&(df_documents['country']==df_documents['country'])].groupby('Print ISBN').count()['sector']
sample_fin_l += list(temp[temp==2].index)
df_documents_p2 = df_documents[df_documents['Print ISBN'].apply(lambda x: x in sample_fin_l)]
df_documents_p2[df_documents_p2['sector'].apply(lambda x: x in ['Monetary', 'Fiscal'])].to_excel(directory+'labeling/to_label_p2.xlsx', index=False)

df_sample_fin = pd.concat([df_documents_p1[df_documents_p1['sector'].apply(lambda x: x in ['Monetary', 'Fiscal'])], df_documents_p2[df_documents_p2['sector'].apply(lambda x: x in ['Monetary', 'Fiscal'])]], ignore_index=True)
df_sample_fin.sort_values(by=['length'])
df_sample_fin = df_sample_fin.drop(['staff_len','buff_len', 'length'], axis=1)
df_sample_fin = df_sample_fin.sample(300)
df_sample_fin.to_excel(directory+'labeling/to_label_all.xlsx', index=False)


# # final sampling - split among colleagues
df_sample_fin = df_sample_fin[['Print ISBN', 'country', 'year', 'sector', 'staff', 'buff']]
df_sample_fin = df_sample_fin.reset_index().drop('index', axis=1)
df_sample_fin = df_sample_fin.reset_index()

# part 1: julia, laurent, xiaorui
doc_idx_l = list(set(df_sample_fin['Print ISBN']))
random.shuffle(doc_idx_l)
p1 = doc_idx_l[:100]
p2 = doc_idx_l[100:200]
p3 = doc_idx_l[200:]
df_sample_fin[df_sample_fin['Print ISBN'].apply(lambda x: x in p1)].to_excel(directory+'labeling/to_label_julia.xlsx', index=False)
df_sample_fin[df_sample_fin['Print ISBN'].apply(lambda x: x in p2)].to_excel(directory+'labeling/to_label_laurent.xlsx', index=False)
df_sample_fin[df_sample_fin['Print ISBN'].apply(lambda x: x in p3)].to_excel(directory+'labeling/to_label_xiaorui.xlsx', index=False)

# part 2: sergio, ghislain, ivailo
random.shuffle(doc_idx_l)
p1 = doc_idx_l[:100]
p2 = doc_idx_l[100:200]
p3 = doc_idx_l[200:]
df_sample_fin[df_sample_fin['Print ISBN'].apply(lambda x: x in p1)].to_excel(directory+'labeling/to_label_sergio.xlsx', index=False)
df_sample_fin[df_sample_fin['Print ISBN'].apply(lambda x: x in p2)].to_excel(directory+'labeling/to_label_ghislain.xlsx', index=False)
df_sample_fin[df_sample_fin['Print ISBN'].apply(lambda x: x in p3)].to_excel(directory+'labeling/to_label_ivailo.xlsx', index=False)

# # smaller sample to look at
# temp = df_documents[(df_documents['staff']!='')&(df_documents['buff']!='')&(df_documents['country']==df_documents['country'])].groupby('Print ISBN').count()['sector']
# sample_fin_l = temp[temp==5].index[:5]
# df_documents_sample = df_documents[df_documents['Print ISBN'].apply(lambda x: x in sample_fin_l)]
# df_documents_sample.to_excel(directory+'labeling/examples.xlsx', index=False)

# df_paragraphs_sample = df_paragraphs[df_paragraphs['Print ISBN'].apply(lambda x: x in sample_fin_l)]
# df_paragraphs_sample.to_excel(directory+'labeling/examples_para.xlsx', index=False)

# # adjust staff appraisal and buff
# df_sample_fin = pd.read_excel(directory+'labeling/to_label_all_old.xlsx')
# df_paragraphs = df_paragraphs[~df_paragraphs['to_drop']]

# for i,row in df_sample_fin.iterrows():
#     for ty in ['staff', 'buff']:
#         df_sample_fin.loc[i, ty] = '\n'.join(df_paragraphs[(df_paragraphs[row['sector']+'_dummy']==True)&(df_paragraphs['Print ISBN']==row['Print ISBN'])&(df_paragraphs['type']==ty)]['text'])

# for ty in ['staff', 'buff']:
#     for i,row in df_sample_fin[(df_sample_fin[ty]=='')].iterrows():
#         temp = df_paragraphs[(df_paragraphs['Print ISBN']==row['Print ISBN'])&(df_paragraphs['type']==ty)]
#         max_val = temp[row['sector']].max()
#         if max_val > 0:
#             df_sample_fin.loc[i, ty] = '\n'.join(temp[temp[row['sector']]==max_val]['text'])
#         else:
#             df_sample_fin.loc[i, ty] = '\n'.join(temp[temp['text'].apply(lambda x: row['sector'].lower() in x)]['text'])

# df_sample_fin.to_excel(directory+'labeling/to_label_all.xlsx', index=False)


# staff_l = ['julia', 'laurent', 'xiaorui', 'sergio', 'ghislain', 'ivailo']
# for s in staff_l:
#     df_sample_fin_s = pd.read_excel(directory+'labeling/to_label_%s.xlsx'%s)
#     df_sample_fin_s.drop(['staff', 'buff'], axis=1).merge(df_sample_fin, how='left').to_excel(directory+'labeling/to_label_%s_new.xlsx'%s, index=False)


# # adjust fiscal paragraphs to make it more concise
# df_sample = pd.read_excel(directory+'labeling/to_label_all.xlsx')
# df_sample = df_sample[df_sample['sector']=='Fiscal']

# for i,row in df_sample.iterrows():
#     rv = []
#     p_l = row['staff'].split('\n')
#     for p in p_l:
#         chat_completion = client.chat.completions.create(
#                     messages=[
#                         {   "role": "system",
#                             "content": '''You are an experience macroeconomist from IMF. Given a paragraph from IMF staff report on a country, decide whether it contains staff assessment on debt sustainability, or staff advice on fiscal policy stance, fiscal revenue, fiscal expenditure, and government debt or financing. Return "No" if there is no such information, and "Yes" otherwise.''',},
#                         {   "role": "user",
#                             "content":  p}
#                     ],
#                     model="gpt-4o",
#                     temperature=0
#                 )
#         if chat_completion.choices[0].message.content.lower().strip() == 'yes':
#             rv.append(p)
#         elif chat_completion.choices[0].message.content.lower().strip() != 'no':
#             print('%d|%s' % (i,p))
#     df_sample.loc[i, 'staff_new'] = '\n'.join(rv)
# df_sample.loc[df_sample[df_sample['staff_new']==''].index, 'staff_new'] = df_sample.loc[df_sample[df_sample['staff_new']==''].index, 'staff']

# for i,row in df_sample.iterrows():
#     rv = []
#     p_l = [p for p in row['buff'].split('\n') if p.strip()!='']
#     for p in p_l:
#         chat_completion = client.chat.completions.create(
#             messages=[
#                 {   "role": "system",
#                     "content": '''You are an experience macroeconomist from IMF. Given a paragraph from the statement by a country's authority in response to an IMF staff report, decide whether it contains the authority's fiscal policy stance, or the authority's agreement/disagreement with IMF staff assessment or advice on debt sustainability, fiscal revenue, fiscal expenditure, or government financing. Return "No" if there is no such information, and "Yes" otherwise.''',},
#                 {   "role": "user",
#                     "content":  p}
#             ],
#             model="gpt-4o",
#             temperature=0
#         )
#         if chat_completion.choices[0].message.content.lower().strip() == 'yes':
#             rv.append(p)
#         elif chat_completion.choices[0].message.content.lower().strip() != 'no':
#             print('%d|%s' % (i,p))
#     df_sample.loc[i, 'buff_new'] = '\n'.join(rv)

# df_sample.to_excel(directory+'labeling/to_label_all_fiscal.xlsx')


# 2. processing labelling results
# 2.1. cross-check with GPT
df_sample = pd.read_excel(directory + 'labeling/to_label_all.xlsx')
df_sample = df_sample[df_sample['sector'] == 'Monetary']

for i, row in df_sample.iterrows():
    if i >= 0:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role": "system",
                 "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts written by IMF staff and a country's authority, complete the following three tasks: (1) classify their current (or near-past) monetary policy stances (staff_current/authority_current) into restrictive, neutral, accommodative, unclear, or irrelevant, respectively; (2) classify the direction of change in their near-future monetary policy stances (staff_future/authority_future) into tightening, tightening tendency, staying the same, loosening tendency, loosening, unclear, or irrelevant, respectively; (3) if the texts imply that authority agree/disagree with IMF staff on monetary policy issues not related to policy stance, assign mostly agree / mostly disagree / disagreement exists to agreement_other; if there are mixed and balanced opinions, assign neutral; if there are no such information, assign unrelated. Return a JSON dict without additional texts: \"staff_current\", \"staff_future\", \"authority_current\", \"authority_future\", \"agreement_other\".''', },
                {"role": "user",
                 "content": '''Part1 - IMF staff:/n%s/n/nPart2 - Authority:/n%s''' % (
                 row['staff'], row['buff'])}
            ]
        )
        temp = json.loads(
            response.choices[0].message.content.replace('```json\n{',
                                                        '{').replace('}\n```',
                                                                     '}'))
        df_sample.loc[i, 'staff_current'] = temp['staff_current']
        df_sample.loc[i, 'staff_future'] = temp['staff_future']
        df_sample.loc[i, 'buff_current'] = temp['authority_current']
        df_sample.loc[i, 'buff_future'] = temp['authority_future']
        df_sample.loc[i, 'agreement_other'] = temp['agreement_other']

df_sample.reset_index().to_csv(directory + 'labeling/df_sample_gpt.csv',
                               index=False)

# 2.2. cross-check among staff
df_gpt = pd.read_csv(directory+'labeling/df_sample_gpt.csv')
df_gpt = df_gpt.rename(columns={c:c+'_gpt' for c in ['staff_current', 'staff_future', 'buff_current', 'buff_future',
       'agreement_other']}).drop(['Print ISBN', 'sector', 'staff', 'buff', 'country', 'year'], axis=1)

directory1 = directory+r'labeling\monetary&fiscal\to_label\monetary/'
staff_l = ['julia', 'laurent', 'xiaorui', 'sergio', 'ghislain', 'ivailo']
key_columns = ['staff_stance_current', 'staff_stance_future', 'buff_stance_current',
       'buff_stance_future', 'agreement_other']

for staff in staff_l:
    df1 = pd.read_excel(directory1+'to_label_%s.xlsx' % staff)
    df2 = pd.DataFrame()
    for s in staff_l:
        if s != staff:
            dfa = pd.read_excel(directory1+'to_label_%s.xlsx'%s)
            dfa['name'] = s
            df2 = pd.concat([df2, dfa], ignore_index=True)
    df2 = df2.drop(['Print ISBN', 'country', 'year', 'sector', 'staff', 'buff', 'notes ']+[c for c in df2.columns if 'certainty' in c], axis=1)
    df2 = df2.rename(columns={c:c+'_alt' for c in df2.columns if c != 'index'})
    df1 = df1.merge(df2, on='index', how='left')

    for col in key_columns:
        df1[col+'_diff_main'] = df1.apply(lambda x: x[col+'_alt']==x[col+'_alt'] and x[col]!=x[col+'_alt'] and (x[col] not in ['unclear', 'irrelevant', 'unrelated'] or x[col+'_alt'] not in ['unclear', 'irrelevant', 'unrelated']), axis=1)
        df1[col+'_diff'] = df1.apply(lambda x: x[col+'_alt']==x[col+'_alt'] and x[col]!=x[col+'_alt'], axis=1)
    df1 = df1[['index', 'Print ISBN', 'country', 'year', 'sector', 'staff', 'buff', 'name_alt']+list(itertools.chain.from_iterable([[col, col+'_alt', col+'_diff_main'] for col in key_columns]))]
    df1 = df1.merge(df_gpt, how='left')

    df1.to_excel(directory+'labeling/by_staff/labels_to_check_%s.xlsx'%staff, index=False)


# 2.3. process the revised datasets - monetary
df_sample = pd.read_excel(directory + 'labeling/to_label_all.xlsx')
df_sample = df_sample[df_sample['sector'] == 'Monetary']

directory1 = directory + r'labeling\monetary&fiscal\to_label\monetary_crosscheck/'
staff_l = ['julia', 'laurent', 'xiaorui', 'sergio', 'ghislain', 'ivailo']
key_columns = ['staff_stance_current', 'staff_stance_future',
               'buff_stance_current',
               'buff_stance_future', 'agreement_other']
df_all = pd.DataFrame()
for staff in staff_l:
    df1 = pd.read_excel(directory1 + 'labels_to_check_%s.xlsx' % staff)
    df1['name'] = staff
    df_all = pd.concat([df_all, df1], ignore_index=True)
df_all = df_all[
    ['index', 'Print ISBN', 'country', 'year', 'sector', 'staff', 'buff',
     'name'] + key_columns]

for i, row in df_sample.iterrows():
    df_temp = df_all[df_all['Print ISBN'] == row['Print ISBN']]
    for col in key_columns + ['name']:
        df_sample.loc[i, col + '_0'] = df_temp.iloc[0][col]
        df_sample.loc[i, col + '_1'] = df_temp.iloc[1][col]

# reconcile differences
for col in key_columns:
    df_sample[col] = df_sample.apply(
        lambda x: x[col + '_0'] if x[col + '_0'] == x[col + '_1'] else np.nan,
        axis=1)
for col in key_columns:
    df_sample[col + '_0'] = df_sample[col + '_0'].fillna('')
    df_sample[col + '_1'] = df_sample[col + '_1'].fillna('')
    df_sample[col + '_options'] = df_sample.apply(
        lambda x: sorted([x[col + '_0'], x[col + '_1']]), axis=1)
    df_sample[col + '_options_orig'] = df_sample.apply(
        lambda x: [x[col + '_0'], x[col + '_1']], axis=1)
    df_sample['names'] = df_sample.apply(
        lambda x: sorted([x['name_0'], x['name_1']]), axis=1)

# stance variables
for col in key_columns:
    df_sample[col] = df_sample.apply(
        lambda x: x[col] if x[col] == x[col] else 'unclear' if x[
                                                                   col + '_options'] == [
                                                                   'irrelevant',
                                                                   'unclear'] else 'tightening tendency' if
        x[col + '_options'] == ['tightening',
                                'tightening tendency'] else 'loosening tendency' if
        x[col + '_options'] == ['loosening', 'loosening tendency'] else np.nan,
        axis=1)
for col in ['staff_stance_current', 'buff_stance_current']:
    df_sample[col] = df_sample.apply(
        lambda x: x[col] if x[col] == x[col] else 'unclear' if x[
                                                                   col + '_options'] == [
                                                                   'neutral',
                                                                   'unclear'] else 'irrelevant' if
        x[col + '_options'] == ['irrelevant', 'neutral'] else np.nan, axis=1)
for col in ['staff_stance_future', 'buff_stance_future']:
    df_sample[col] = df_sample.apply(
        lambda x: x[col] if x[col] == x[col] else 'neutral' if x[
                                                                   col + '_options'] == [
                                                                   'neutral',
                                                                   'unclear'] else 'neutral' if
        x[col + '_options'] == ['irrelevant', 'neutral'] else np.nan, axis=1)

# agreement variables
# agreement_other
df_sample['agreement_other_0'] = df_sample['agreement_other_0'].apply(
    lambda x: 'mostly agree' if x == 'neutral' else x)
df_sample['agreement_other_1'] = df_sample['agreement_other_1'].apply(
    lambda x: 'mostly agree' if x == 'neutral' else x)
col = 'agreement_other'
df_sample[col] = df_sample.apply(
    lambda x: x[col + '_0'] if x[col + '_0'] == x[col + '_1'] else np.nan,
    axis=1)
df_sample[col + '_0'] = df_sample[col + '_0'].fillna('')
df_sample[col + '_1'] = df_sample[col + '_1'].fillna('')
df_sample[col + '_options'] = df_sample.apply(
    lambda x: sorted([x[col + '_0'], x[col + '_1']]), axis=1)
df_sample[col + '_options_orig'] = df_sample.apply(
    lambda x: [x[col + '_0'], x[col + '_1']], axis=1)
df_sample[col] = df_sample.apply(
    lambda x: x[col] if x[col] == x[col] else 'unrelated' if x[
                                                                 col + '_options'] == [
                                                                 'mostly agree',
                                                                 'unrelated'] else np.nan,
    axis=1)

# save
idx_l = df_sample[~((~df_sample['buff_stance_current'].isna()) & (
    ~df_sample['buff_stance_future'].isna()) & (
                        ~df_sample['staff_stance_current'].isna()) & (
                        ~df_sample['staff_stance_future'].isna()) & (
                        ~df_sample['agreement_other'].isna()))].index
idx_l1 = df_sample[(~((~df_sample['buff_stance_current'].isna()) & (
    ~df_sample['buff_stance_future'].isna()) & (
                          ~df_sample['staff_stance_current'].isna()) & (
                          ~df_sample['staff_stance_future'].isna()) & (
                          ~df_sample['agreement_other'].isna()))) & (
                       df_sample['names'].apply(lambda x: 'xiaorui' in x or (
                                   'julia' not in x and 'ghislain' in x)))].index
idx_l2 = [i for i in idx_l if i not in idx_l1]
df_sample = df_sample[
    ['Print ISBN', 'sector', 'staff', 'buff', 'country', 'year',
     'staff_stance_current',
     'staff_stance_future', 'buff_stance_current', 'buff_stance_future',
     'agreement_other', 'staff_stance_current_options_orig',
     'staff_stance_future_options_orig', 'buff_stance_current_options_orig',
     'buff_stance_future_options_orig', 'agreement_other_options_orig'
     ]].rename(columns={c: c.replace('_orig', '') for c in
                        ['staff_stance_current_options_orig',
                         'staff_stance_future_options_orig',
                         'buff_stance_current_options_orig',
                         'buff_stance_future_options_orig',
                         'agreement_other_options_orig'
                         ]})
df_sample.loc[idx_l1].to_excel(
    directory + 'labeling/crosscheck_julia.xlsx')
df_sample.loc[idx_l2].to_excel(
    directory + 'labeling/crosscheck_xiaorui.xlsx')

# after second-round labelling
df_labelled1 = pd.read_excel(
    directory + r'labeling\monetary&fiscal\to_label\monetary_crosscheck\second_round/crosscheck_julia.xlsx')
df_labelled2 = pd.read_excel(
    directory + r'labeling\monetary&fiscal\to_label\monetary_crosscheck\second_round/crosscheck_xiaorui.xlsx')

for i, row in df_labelled1.iterrows():
    row = df_labelled1.loc[i]
    idx = df_sample[df_sample['Print ISBN'] == row['Print ISBN']].index[0]
    for col in key_columns:
        df_sample.loc[idx, col] = row[col]

for i, row in df_labelled2.iterrows():
    row = df_labelled2.loc[i]
    idx = df_sample[df_sample['Print ISBN'] == row['Print ISBN']].index[0]
    for col in key_columns:
        if not (col == 'agreement_other' and row[
            'agreement_other_options'] == "['mostly agree', 'unrelated']"):
            df_sample.loc[idx, col] = row[col]

# save
# df_sample = df_sample[
#     df_sample['Print ISBN'].apply(lambda x: x not in to_drop_l)]
df_sample = df_sample[
    ['Print ISBN', 'sector', 'staff', 'buff', 'country', 'year',
     'staff_stance_current', 'staff_stance_future', 'buff_stance_current',
     'buff_stance_future',
     'agreement_other']]
for col in key_columns:
    df_sample[col] = df_sample[col].apply(
        lambda x: x.strip().replace('accomodative', 'accommodative').replace(
            'reestrictive', 'restrictive'))
df_sample.loc[
    df_sample[df_sample['Print ISBN'] == 9781484334850].index, 'year'] = 2017
df_sample.loc[df_sample[df_sample[
                            'Print ISBN'] == 9781484388600].index, 'buff_stance_future'] = 'tightening tendency'
df_sample.loc[df_sample[df_sample[
                            'Print ISBN'] == 9781484317259].index, 'staff_stance_future'] = 'tightening tendency'
df_sample.loc[df_sample[df_sample[
                            'Print ISBN'] == 9781484384749].index, 'staff_stance_future'] = 'neutral'
df_sample.loc[df_sample[df_sample[
                            'Print ISBN'] == 9781475579789].index, 'buff_stance_future'] = 'neutral'
df_sample.loc[df_sample[df_sample[
                            'Print ISBN'] == 9781498311946].index, 'buff_stance_future'] = 'neutral'
df_sample.reset_index().to_excel(directory + 'output/labelled_monetary.xlsx',
                                 index=False)

# remove no separate legal tender, currency board, or currency union countries
country_dict_aiv = {'South Sudan': 'Republic of South Sudan',
                    'The Republic of Moldova': 'Republic of Moldova'}
country_dict = {'Egypt': 'Arab Republic of Egypt',
                'Congo, Democratic Republic of the': 'Democratic Republic of the Congo',
                'North Macedonia, Republic of': 'Former Yugoslav Republic of Macedonia',
                'Iran, Islamic Republic of': 'Islamic Republic of Iran',
                'Mauritania': 'Islamic Republic of Mauritania',
                'China': 'People’s Republic of China',
                'Hong Kong SAR': 'People’s Republic of China—Hong Kong Special Administrative Region',
                'Armenia': 'Republic of Armenia',
                'Azerbaijan': 'Republic of Azerbaijan',
                'Belarus': 'Republic of Belarus',
                'Croatia': 'Republic of Croatia',
                'Fiji': 'Republic of Fiji',
                'Korea': 'Republic of Korea',
                'Madagascar': 'Republic of Madagascar',
                'Moldova': 'Republic of Moldova',
                'Mozambique': 'Republic of Mozambique',
                'Poland': 'Republic of Poland',
                'Serbia': 'Republic of Serbia',
                'South Sudan': 'Republic of South Sudan',
                'Timor-Leste': 'Republic of Timor-Leste',
                'Uzbekistan': 'Republic of Uzbekistan',
                'Bahamas, The': 'The Bahamas',
                'Ethiopia': 'The Federal Democratic Republic of Ethiopia',
                'Gambia, The': 'The Gambia',
                'Türkiye': 'Turkey',
                'Tanzania': 'United Republic of Tanzania'}
key_columns = ['staff_stance_current', 'staff_stance_future',
               'buff_stance_current',
               'buff_stance_future', 'agreement_other']

df_currency = pd.read_csv(directory + 'macro/areaer_currency.csv')
df_currency = df_currency[['Year', 'Country', 'Category']].rename(
    columns={c: c.lower() for c in ['Year', 'Country']})
df_currency['country'] = df_currency['country'].apply(
    lambda x: country_dict[x].strip() if x in country_dict else x.strip())
for year in range(2022, 2025):
    df_temp = df_currency[df_currency['year'] == 2021]
    df_temp['year'] = year
    df_currency = pd.concat([df_currency, df_temp], ignore_index=True)
df_currency = df_currency[~df_currency.duplicated(subset=['year', 'country'])]

df_cu = pd.read_csv(directory + 'macro/currency_union.csv')
df_cu = df_cu[['Year', 'Country', 'Currency union']].rename(
    columns={c: c.lower() for c in ['Year', 'Country']})
df_cu['country'] = df_cu['country'].apply(
    lambda x: country_dict[x].strip() if x in country_dict else x.strip())
for year in range(2022, 2025):
    df_temp = df_cu[df_cu['year'] == 2021]
    df_temp['year'] = year
    df_cu = pd.concat([df_cu, df_temp], ignore_index=True)
df_cu.loc[df_cu[(df_cu['country'] == 'Republic of Croatia') & (
    df_cu['year'].apply(lambda x: x >= 2023))].index, 'Currency union'] = 1
df_cu = df_cu[~df_cu.duplicated(subset=['year', 'country'])]

df_sample['country'] = df_sample['country'].apply(lambda x: country_dict_aiv[
    x].strip() if x in country_dict_aiv else x.strip())
df_sample = df_sample.merge(df_currency, on=['year', 'country'], how='left')
df_sample = df_sample.merge(df_cu, on=['year', 'country'], how='left')
df_sample.loc[df_sample[df_sample['country'].apply(
    lambda x: x in ['South Africa', 'Zimbabwe'])].index, 'Currency union'] = 0
df_sample['to_drop'] = (df_sample['Category'].apply(
    lambda x: x in ['Currency board', 'No separate legal tender'])) | (
                                   df_sample['Currency union'] == 1)
df_sample.loc[df_sample[df_sample['country'].apply(
    lambda x: x in ['The Bahamas', 'Denmark'])].index, 'to_drop'] = True

# further adjustments
df_sample['staff_stance_future'] = df_sample.apply(
    lambda x: 'neutral' if x['staff_stance_current'] not in ['unclear',
                                                             'irrelevant'] and
                           x['staff_stance_future'] in ['unclear',
                                                        'irrelevant'] else x[
        'staff_stance_future'], axis=1)
df_sample['buff_stance_future'] = df_sample.apply(
    lambda x: 'neutral' if x['buff_stance_current'] not in ['unclear',
                                                            'irrelevant'] and x[
                               'buff_stance_future'] in ['unclear',
                                                         'irrelevant'] else x[
        'buff_stance_future'], axis=1)
df_sample['staff_stance_current'] = df_sample.apply(
    lambda x: 'unclear' if x['staff_stance_current'] == 'irrelevant' and x[
        'staff_stance_future'] not in ['unclear', 'irrelevant'] else x[
        'staff_stance_current'], axis=1)
df_sample['buff_stance_current'] = df_sample.apply(
    lambda x: 'unclear' if x['buff_stance_current'] == 'irrelevant' and x[
        'buff_stance_future'] not in ['unclear', 'irrelevant'] else x[
        'buff_stance_current'], axis=1)
df_sample['staff_stance_future'] = df_sample['staff_stance_future'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral',
                                                    'no change'))  # .replace('unclear', 'irrelevant'))
df_sample['buff_stance_future'] = df_sample['buff_stance_future'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral',
                                                    'no change'))  # .replace('unclear', 'irrelevant'))
df_sample['agreement_other'] = df_sample['agreement_other'].apply(
    lambda x: x.replace('unrelated', 'irrelevant'))

df_sample.to_excel(directory + 'output/labelled_monetary_v2.xlsx', index=False)

# remove no separate legal tender, currency board, or currency union countries
country_dict_aiv = {'South Sudan': 'Republic of South Sudan',
                    'The Republic of Moldova': 'Republic of Moldova'}
country_dict = {'Egypt': 'Arab Republic of Egypt',
                'Congo, Democratic Republic of the': 'Democratic Republic of the Congo',
                'North Macedonia, Republic of': 'Former Yugoslav Republic of Macedonia',
                'Iran, Islamic Republic of': 'Islamic Republic of Iran',
                'Mauritania': 'Islamic Republic of Mauritania',
                'China': 'People’s Republic of China',
                'Hong Kong SAR': 'People’s Republic of China—Hong Kong Special Administrative Region',
                'Armenia': 'Republic of Armenia',
                'Azerbaijan': 'Republic of Azerbaijan',
                'Belarus': 'Republic of Belarus',
                'Croatia': 'Republic of Croatia',
                'Fiji': 'Republic of Fiji',
                'Korea': 'Republic of Korea',
                'Madagascar': 'Republic of Madagascar',
                'Moldova': 'Republic of Moldova',
                'Mozambique': 'Republic of Mozambique',
                'Poland': 'Republic of Poland',
                'Serbia': 'Republic of Serbia',
                'South Sudan': 'Republic of South Sudan',
                'Timor-Leste': 'Republic of Timor-Leste',
                'Uzbekistan': 'Republic of Uzbekistan',
                'Bahamas, The': 'The Bahamas',
                'Ethiopia': 'The Federal Democratic Republic of Ethiopia',
                'Gambia, The': 'The Gambia',
                'Türkiye': 'Turkey',
                'Tanzania': 'United Republic of Tanzania'}
key_columns = ['staff_stance_current', 'staff_stance_future',
               'buff_stance_current',
               'buff_stance_future', 'agreement_other']

df_currency = pd.read_csv(directory + 'macro/areaer_currency.csv')
df_currency = df_currency[['Year', 'Country', 'Category']].rename(
    columns={c: c.lower() for c in ['Year', 'Country']})
df_currency['country'] = df_currency['country'].apply(
    lambda x: country_dict[x].strip() if x in country_dict else x.strip())
for year in range(2022, 2025):
    df_temp = df_currency[df_currency['year'] == 2021]
    df_temp['year'] = year
    df_currency = pd.concat([df_currency, df_temp], ignore_index=True)
df_currency = df_currency[~df_currency.duplicated(subset=['year', 'country'])]

df_cu = pd.read_csv(directory + 'macro/currency_union.csv')
df_cu = df_cu[['Year', 'Country', 'Currency union']].rename(
    columns={c: c.lower() for c in ['Year', 'Country']})
df_cu['country'] = df_cu['country'].apply(
    lambda x: country_dict[x].strip() if x in country_dict else x.strip())
for year in range(2022, 2025):
    df_temp = df_cu[df_cu['year'] == 2021]
    df_temp['year'] = year
    df_cu = pd.concat([df_cu, df_temp], ignore_index=True)
df_cu.loc[df_cu[(df_cu['country'] == 'Republic of Croatia') & (
    df_cu['year'].apply(lambda x: x >= 2023))].index, 'Currency union'] = 1
df_cu = df_cu[~df_cu.duplicated(subset=['year', 'country'])]

df_sample['country'] = df_sample['country'].apply(lambda x: country_dict_aiv[
    x].strip() if x in country_dict_aiv else x.strip())
df_sample = df_sample.merge(df_currency, on=['year', 'country'], how='left')
df_sample = df_sample.merge(df_cu, on=['year', 'country'], how='left')
df_sample.loc[df_sample[df_sample['country'].apply(
    lambda x: x in ['South Africa', 'Zimbabwe'])].index, 'Currency union'] = 0
df_sample['to_drop'] = (df_sample['Category'].apply(
    lambda x: x in ['Currency board', 'No separate legal tender'])) | (
                                   df_sample['Currency union'] == 1)
df_sample.loc[df_sample[df_sample['country'].apply(
    lambda x: x in ['The Bahamas', 'Denmark'])].index, 'to_drop'] = True

# further adjustments
df_sample['staff_stance_future'] = df_sample.apply(
    lambda x: 'neutral' if x['staff_stance_current'] not in ['unclear',
                                                             'irrelevant'] and
                           x['staff_stance_future'] in ['unclear',
                                                        'irrelevant'] else x[
        'staff_stance_future'], axis=1)
df_sample['buff_stance_future'] = df_sample.apply(
    lambda x: 'neutral' if x['buff_stance_current'] not in ['unclear',
                                                            'irrelevant'] and x[
                               'buff_stance_future'] in ['unclear',
                                                         'irrelevant'] else x[
        'buff_stance_future'], axis=1)
df_sample['staff_stance_current'] = df_sample.apply(
    lambda x: 'unclear' if x['staff_stance_current'] == 'irrelevant' and x[
        'staff_stance_future'] not in ['unclear', 'irrelevant'] else x[
        'staff_stance_current'], axis=1)
df_sample['buff_stance_current'] = df_sample.apply(
    lambda x: 'unclear' if x['buff_stance_current'] == 'irrelevant' and x[
        'buff_stance_future'] not in ['unclear', 'irrelevant'] else x[
        'buff_stance_current'], axis=1)
df_sample['staff_stance_future'] = df_sample['staff_stance_future'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral',
                                                    'no change'))  # .replace('unclear', 'irrelevant'))
df_sample['buff_stance_future'] = df_sample['buff_stance_future'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral',
                                                    'no change'))  # .replace('unclear', 'irrelevant'))
df_sample['agreement_other'] = df_sample['agreement_other'].apply(
    lambda x: x.replace('unrelated', 'irrelevant'))

df_sample.to_excel(directory + 'output/labelled_monetary_v2.xlsx', index=False)

# remove no separate legal tender, currency board, or currency union countries
country_dict_aiv = {'South Sudan': 'Republic of South Sudan',
                    'The Republic of Moldova': 'Republic of Moldova'}
country_dict = {'Egypt': 'Arab Republic of Egypt',
                'Congo, Democratic Republic of the': 'Democratic Republic of the Congo',
                'North Macedonia, Republic of': 'Former Yugoslav Republic of Macedonia',
                'Iran, Islamic Republic of': 'Islamic Republic of Iran',
                'Mauritania': 'Islamic Republic of Mauritania',
                'China': 'People’s Republic of China',
                'Hong Kong SAR': 'People’s Republic of China—Hong Kong Special Administrative Region',
                'Armenia': 'Republic of Armenia',
                'Azerbaijan': 'Republic of Azerbaijan',
                'Belarus': 'Republic of Belarus',
                'Croatia': 'Republic of Croatia',
                'Fiji': 'Republic of Fiji',
                'Korea': 'Republic of Korea',
                'Madagascar': 'Republic of Madagascar',
                'Moldova': 'Republic of Moldova',
                'Mozambique': 'Republic of Mozambique',
                'Poland': 'Republic of Poland',
                'Serbia': 'Republic of Serbia',
                'South Sudan': 'Republic of South Sudan',
                'Timor-Leste': 'Republic of Timor-Leste',
                'Uzbekistan': 'Republic of Uzbekistan',
                'Bahamas, The': 'The Bahamas',
                'Ethiopia': 'The Federal Democratic Republic of Ethiopia',
                'Gambia, The': 'The Gambia',
                'Türkiye': 'Turkey',
                'Tanzania': 'United Republic of Tanzania'}
key_columns = ['staff_stance_current', 'staff_stance_future',
               'buff_stance_current',
               'buff_stance_future', 'agreement_other']

df_currency = pd.read_csv(directory + 'macro/areaer_currency.csv')
df_currency = df_currency[['Year', 'Country', 'Category']].rename(
    columns={c: c.lower() for c in ['Year', 'Country']})
df_currency['country'] = df_currency['country'].apply(
    lambda x: country_dict[x].strip() if x in country_dict else x.strip())
for year in range(2022, 2025):
    df_temp = df_currency[df_currency['year'] == 2021]
    df_temp['year'] = year
    df_currency = pd.concat([df_currency, df_temp], ignore_index=True)
df_currency = df_currency[~df_currency.duplicated(subset=['year', 'country'])]

df_cu = pd.read_csv(directory + 'macro/currency_union.csv')
df_cu = df_cu[['Year', 'Country', 'Currency union']].rename(
    columns={c: c.lower() for c in ['Year', 'Country']})
df_cu['country'] = df_cu['country'].apply(
    lambda x: country_dict[x].strip() if x in country_dict else x.strip())
for year in range(2022, 2025):
    df_temp = df_cu[df_cu['year'] == 2021]
    df_temp['year'] = year
    df_cu = pd.concat([df_cu, df_temp], ignore_index=True)
df_cu.loc[df_cu[(df_cu['country'] == 'Republic of Croatia') & (
    df_cu['year'].apply(lambda x: x >= 2023))].index, 'Currency union'] = 1
df_cu = df_cu[~df_cu.duplicated(subset=['year', 'country'])]

df_sample['country'] = df_sample['country'].apply(lambda x: country_dict_aiv[
    x].strip() if x in country_dict_aiv else x.strip())
df_sample = df_sample.merge(df_currency, on=['year', 'country'], how='left')
df_sample = df_sample.merge(df_cu, on=['year', 'country'], how='left')
df_sample.loc[df_sample[df_sample['country'].apply(
    lambda x: x in ['South Africa', 'Zimbabwe'])].index, 'Currency union'] = 0
df_sample['to_drop'] = (df_sample['Category'].apply(
    lambda x: x in ['Currency board', 'No separate legal tender'])) | (
                                   df_sample['Currency union'] == 1)
df_sample.loc[df_sample[df_sample['country'].apply(
    lambda x: x in ['The Bahamas', 'Denmark'])].index, 'to_drop'] = True

# further adjustments
df_sample['staff_stance_future'] = df_sample.apply(
    lambda x: 'neutral' if x['staff_stance_current'] not in ['unclear',
                                                             'irrelevant'] and
                           x['staff_stance_future'] in ['unclear',
                                                        'irrelevant'] else x[
        'staff_stance_future'], axis=1)
df_sample['buff_stance_future'] = df_sample.apply(
    lambda x: 'neutral' if x['buff_stance_current'] not in ['unclear',
                                                            'irrelevant'] and x[
                               'buff_stance_future'] in ['unclear',
                                                         'irrelevant'] else x[
        'buff_stance_future'], axis=1)
df_sample['staff_stance_current'] = df_sample.apply(
    lambda x: 'unclear' if x['staff_stance_current'] == 'irrelevant' and x[
        'staff_stance_future'] not in ['unclear', 'irrelevant'] else x[
        'staff_stance_current'], axis=1)
df_sample['buff_stance_current'] = df_sample.apply(
    lambda x: 'unclear' if x['buff_stance_current'] == 'irrelevant' and x[
        'buff_stance_future'] not in ['unclear', 'irrelevant'] else x[
        'buff_stance_current'], axis=1)
df_sample['staff_stance_future'] = df_sample['staff_stance_future'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral',
                                                    'no change'))  # .replace('unclear', 'irrelevant'))
df_sample['buff_stance_future'] = df_sample['buff_stance_future'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral',
                                                    'no change'))  # .replace('unclear', 'irrelevant'))
df_sample['agreement_other'] = df_sample['agreement_other'].apply(
    lambda x: x.replace('unrelated', 'irrelevant'))

df_sample.to_excel(directory + 'output/labelled_monetary_v2.xlsx', index=False)


# 2.4. process the revised datasets - fiscal
df_sample = pd.read_excel(
    directory + 'labeling/to_label/to_label_all_fiscal.xlsx')
df_sample['staff'] = df_sample['staff_new']
df_sample['buff'] = df_sample['buff_new']

directory1 = directory + r'labeling\monetary&fiscal\to_label\fiscal_new/'
staff_l = ['julia', 'xiaorui2', 'xiaorui', 'sergio', 'miro', 'ivailo']
key_columns = ['staff_stance_near_term', 'buff_stance_near_term',
               'agreement_revenue', 'agreement_expenditure',
               'agreement_debt&financing', 'agreement_fundamentals',
               'agreement_other']
df_all = pd.DataFrame()
for staff in staff_l:
    df1 = pd.read_excel(directory1 + 'to_label_fiscal_%s.xlsx' % staff)
    df1['name'] = staff
    df_all = pd.concat([df_all, df1], ignore_index=True)
df_all = df_all[
    ['index', 'Print ISBN', 'country', 'year', 'sector', 'staff', 'buff',
     'name'] + key_columns]

for i, row in df_sample.iterrows():
    df_temp = df_all[df_all['Print ISBN'] == row['Print ISBN']]
    for col in key_columns + ['name']:
        df_sample.loc[i, col + '_0'] = df_temp.iloc[0][col]
        df_sample.loc[i, col + '_1'] = df_temp.iloc[1][col]

# reconcile differences
for col in key_columns:
    df_sample[col] = df_sample.apply(
        lambda x: x[col + '_0'] if x[col + '_0'] == x[col + '_1'] else np.nan,
        axis=1)
for col in key_columns:
    df_sample[col + '_0'] = df_sample[col + '_0'].fillna('')
    df_sample[col + '_1'] = df_sample[col + '_1'].fillna('')
    df_sample[col + '_options'] = df_sample.apply(
        lambda x: sorted([x[col + '_0'], x[col + '_1']]), axis=1)
    df_sample[col + '_options_orig'] = df_sample.apply(
        lambda x: [x[col + '_0'], x[col + '_1']], axis=1)
    df_sample['names'] = df_sample.apply(
        lambda x: sorted([x['name_0'], x['name_1']]), axis=1)
df_sample = df_sample = df_sample[
    (df_sample['staff_stance_near_term_0'] != '') & (
                df_sample['staff_stance_near_term_1'] != '')]

# stance variables
for col in key_columns:
    df_sample[col] = df_sample.apply(
        lambda x: x[col] if x[col] == x[col] else 'unclear' if x[
                                                                   col + '_options'] == [
                                                                   'irrelevant',
                                                                   'unclear'] else 'tightening tendency' if
        x[col + '_options'] == ['tightening',
                                'tightening tendency'] else 'loosening tendency' if
        x[col + '_options'] == ['loosening', 'loosening tendency'] else np.nan,
        axis=1)
for col in ['staff_stance_near_term', 'buff_stance_near_term']:
    df_sample[col] = df_sample.apply(
        lambda x: x[col] if x[col] == x[col] else 'neutral' if x[
                                                                   col + '_options'] == [
                                                                   'neutral',
                                                                   'unclear'] else 'neutral' if
        x[col + '_options'] == ['irrelevant', 'neutral'] else np.nan, axis=1)

# agreement variables
key_vars_agreement = ['agreement_revenue', 'agreement_expenditure',
                      'agreement_debt&financing', 'agreement_fundamentals',
                      'agreement_other']
for col in key_vars_agreement:
    for i in range(2):
        df_sample[col + '_%d' % i] = df_sample[col + '_%d' % i].apply(
            lambda x: 'mostly agree' if x == 'neutral' else x)
        df_sample[col] = df_sample.apply(
            lambda x: x[col + '_0'] if x[col + '_0'] == x[
                col + '_1'] else np.nan, axis=1)
        df_sample[col + '_0'] = df_sample[col + '_0'].fillna('')
        df_sample[col + '_1'] = df_sample[col + '_1'].fillna('')
        df_sample[col + '_options'] = df_sample.apply(
            lambda x: sorted([x[col + '_0'], x[col + '_1']]), axis=1)
        df_sample[col + '_options_orig'] = df_sample.apply(
            lambda x: [x[col + '_0'], x[col + '_1']], axis=1)
        df_sample[col] = df_sample.apply(
            lambda x: x[col] if x[col] == x[col] else 'mostly agree' if x[
                                                                            col + '_options'] == [
                                                                            'mostly agree',
                                                                            'unrelated'] else np.nan,
            axis=1)

# save
idx_l = df_sample[~((~df_sample['buff_stance_near_term'].isna()) & (
    ~df_sample['staff_stance_near_term'].isna()) & (
                        ~df_sample['agreement_revenue'].isna()) & (
                        ~df_sample['agreement_expenditure'].isna()) & (
                        ~df_sample['agreement_debt&financing'].isna()) & (
                        ~df_sample['agreement_fundamentals'].isna()) & (
                        ~df_sample['agreement_other'].isna()))].index
# idx_l1 = df_sample[(~((~df_sample['buff_stance_current'].isna())&(~df_sample['buff_stance_future'].isna())&(~df_sample['staff_stance_current'].isna())&(~df_sample['staff_stance_future'].isna())&(~df_sample['agreement_other'].isna())))&(df_sample['names'].apply(lambda x: 'xiaorui' in x or ('julia' not in x and 'ghislain' in x)))].index
# idx_l2 = [i for i in idx_l if i not in idx_l1]
df_sample = df_sample[
    ['Print ISBN', 'sector', 'staff', 'buff', 'country', 'year',
     'staff_stance_near_term', 'buff_stance_near_term', 'agreement_revenue',
     'agreement_expenditure', 'agreement_debt&financing',
     'agreement_fundamentals', 'agreement_other',
     'staff_stance_near_term_options_orig',
     'buff_stance_near_term_options_orig',
     'agreement_revenue_options_orig',
     'agreement_expenditure_options_orig',
     'agreement_debt&financing_options_orig',
     'agreement_fundamentals_options_orig',
     'agreement_other_options_orig'
     ]].rename(columns={c: c.replace('_orig', '') for c in
                        ['staff_stance_near_term_options_orig',
                         'buff_stance_near_term_options_orig',
                         'agreement_revenue_options_orig',
                         'agreement_expenditure_options_orig',
                         'agreement_debt&financing_options_orig',
                         'agreement_fundamentals_options_orig',
                         'agreement_other_options_orig'
                         ]})
# # df_sample.loc[idx_l].to_excel(directory+'labeling/crosscheck_fiscal_julia.xlsx')
# # df_sample.loc[idx_l2].to_excel(directory+'labeling/crosscheck_xiaorui.xlsx')
# idx_l0 = list(pd.read_excel(directory+'labeling/to_label/fiscal/crosscheck_fiscal_julia.xlsx')['Unnamed: 0'])
# idx_l1 = list(pd.read_excel(directory+'labeling/to_label/fiscal/crosscheck_fiscal_laurent.xlsx')['Unnamed: 0'])
# df_sample.loc[[i for i in idx_l if i not in idx_l0+idx_l1]].to_excel(directory+'labeling/to_label/fiscal/crosscheck_fiscal_xiaorui.xlsx')


# after second-round labelling - fiscal
directory1 = directory + r'labeling\monetary&fiscal\to_label\fiscal_crosscheck/'
key_columns = ['staff_stance_near_term', 'buff_stance_near_term',
               'agreement_revenue', 'agreement_expenditure',
               'agreement_debt&financing', 'agreement_fundamentals',
               'agreement_other', 'disagreement_areas']
df_labelled1 = pd.read_excel(directory1 + 'crosscheck_fiscal_julia.xlsx')
df_labelled2 = pd.read_excel(directory1 + 'crosscheck_fiscal_xiaorui.xlsx')
df_labelled3 = pd.read_excel(directory1 + 'crosscheck_fiscal_laurent.xlsx')

for i, row in df_labelled1.iterrows():
    row = df_labelled1.loc[i]
    idx = df_sample[df_sample['Print ISBN'] == row['Print ISBN']].index[0]
    for col in key_columns:
        if row[col] == row[col] and row[col] != 'nan':
            df_sample.loc[idx, col] = row[col]

for i, row in df_labelled2.iterrows():
    row = df_labelled2.loc[i]
    idx = df_sample[df_sample['Print ISBN'] == row['Print ISBN']].index[0]
    for col in key_columns:
        if row[col] == row[col] and row[col] != 'nan':
            df_sample.loc[idx, col] = row[col]

for i, row in df_labelled3.iterrows():
    row = df_labelled3.loc[i]
    idx = df_sample[df_sample['Print ISBN'] == row['Print ISBN']].index[0]
    for col in key_columns:
        if row[col] == row[col] and row[col] != 'nan':
            df_sample.loc[idx, col] = row[col]

df_sample['buff_stance_near_term'] = df_sample['buff_stance_near_term'].apply(
    lambda x: 'irrelevant' if x == 'unrelated' else x)
df_sample['agreement_revenue'] = df_sample['agreement_revenue'].apply(
    lambda x: 'irrelevant' if x in ['unrelated', 'Unrelated'] else x)
df_sample['agreement_expenditure'] = df_sample['agreement_expenditure'].apply(
    lambda x: 'irrelevant' if x in ['unrelated',
                                    'Unrelated'] else 'mostly agree' if x == 'unclear' else x)
df_sample['agreement_debt&financing'] = df_sample[
    'agreement_debt&financing'].apply(
    lambda x: 'irrelevant' if x in ['unrelated', 'Unrelated'] else x)
df_sample['agreement_fundamentals'] = df_sample['agreement_fundamentals'].apply(
    lambda x: 'irrelevant' if x in ['unrelated', 'Unrelated'] else x)
df_sample['agreement_other'] = df_sample['agreement_other'].apply(
    lambda x: 'irrelevant' if x in ['unrelated', 'Unrelated'] else x)
df_sample['buff_stance_near_term'] = df_sample['buff_stance_near_term'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral', 'no change'))
df_sample['staff_stance_near_term'] = df_sample['staff_stance_near_term'].apply(
    lambda x: x.replace('tendency', 'bias').replace('neutral', 'no change'))
df_sample['disagreement_areas'] = df_sample['disagreement_areas'].apply(
    lambda x: '' if x == 'nan' else x)
for i, row in df_sample.iterrows():
    for col in ['agreement_revenue', 'agreement_expenditure',
                'agreement_debt&financing', 'agreement_fundamentals']:
        if row[col] in ['disagreement exists', 'mostly disagree']:
            df_sample.loc[i, 'disagreement_areas'] = (
                        row['disagreement_areas'] + '; ' + col.replace(
                    'agreement_', '').replace('fundamentals',
                                              'economic fundamentals').replace(
                    'revenue', 'government revenue').replace('expenditure',
                                                             'government expenditure').replace(
                    'debt&financing', 'government debt & financing')).strip(
                '; ')

# save
df_sample = df_sample[
    ['Print ISBN', 'sector', 'staff', 'buff', 'country', 'year',
     'staff_stance_near_term', 'buff_stance_near_term', 'agreement_revenue',
     'agreement_expenditure', 'agreement_debt&financing',
     'agreement_fundamentals', 'agreement_other', 'disagreement_areas']]

df_sample['agreement_stance_future'] = df_sample.apply(
    lambda x: 'irrelevant' if x['staff_stance_near_term'] in ['unclear',
                                                              'irrelevant'] or
                              x['buff_stance_near_term'] in ['unclear',
                                                             'irrelevant'] else 'mostly agree' if
    x['staff_stance_near_term'] == x[
        'buff_stance_near_term'] else 'disagreement exists', axis=1)
df_sample['disagreement_areas'] = df_sample.apply(
    lambda x: (x['disagreement_areas'] + '; near-term policy direction').strip(
        '; ') if x['agreement_stance_future'] == 'disagreement exists' else x[
        'disagreement_areas'], axis=1)
df_sample['agreement_general'] = df_sample.apply(
    lambda x: 'irrelevant' if x['agreement_stance_future'] == 'irrelevant' and
                              x[
                                  'agreement_other'] == 'irrelevant' else 'disagreement exists' if
    x['disagreement_areas'] != '' else 'mostly agree', axis=1)

df_sample.reset_index().to_excel(directory + 'output/labelled_fiscal.xlsx',
                                 index=False)


# 3. generate training / testing sets for llms
# 3.1. fiscal
df_sample = pd.read_excel(directory+'labeling/labelled/labelled_fiscal_v1.xlsx')

# five-fold cross validation
shuffled = df_sample.sample(frac=1)
result = np.array_split(shuffled, 5)

# check the distribution of train and test sets
key_columns = ['staff_stance_near_term', 'buff_stance_near_term', 'agreement_revenue', 'agreement_expenditure',
               'agreement_debt&financing', 'agreement_fundamentals', 'agreement_other', 'agreement_general']
for i in range(5):
    df_test1 = result[i]
    df_train1 = pd.concat([result[j] for j in range(5) if j != i])
    same_l = []
    for col in key_columns:
        try:
            same_l.append(set(df_train1[col].value_counts(normalize=True).index == df_test1[col].value_counts(normalize=True).index)=={True})
        except Exception:
            same_l.append(False)
    print(same_l)

for i in range(5):
    df_test1 = result[i]
    df_train1 = pd.concat([result[j] for j in range(5) if j != i])
    for col in key_columns:
        print(df_train1[col].value_counts(normalize=True))
        print(df_test1[col].value_counts(normalize=True))
        print('\n')

# save
for i in range(5):
    df_test1 = result[i]
    df_train1 = pd.concat([result[j] for j in range(5) if j != i])
    df_test1.to_excel(directory+'finetuning/fiscal/cv/testing_%d.xlsx'%i, index=False)
    df_train1.to_excel(directory+'finetuning/fiscal/cv/training_%d.xlsx'%i, index=False)


# 3.2. monetary
# agreement_general
df_sample = pd.read_excel(directory+'labeling/labelled_monetary_v3.xlsx')
df_sample = df_sample[~df_sample['to_drop']]
df_sample['agreement_stance_current'] = df_sample.apply(lambda x: 'irrelevant' if x['staff_stance_current'] in ['unclear', 'irrelevant'] or x['buff_stance_current'] in ['unclear', 'irrelevant'] else 'mostly agree' if x['staff_stance_current']==x['buff_stance_current'] else 'disagreement exists', axis=1)
df_sample['agreement_stance_future'] = df_sample.apply(lambda x: 'irrelevant' if x['staff_stance_future'] in ['unclear', 'irrelevant'] or x['buff_stance_future'] in ['unclear', 'irrelevant'] else 'mostly agree' if x['staff_stance_future']==x['buff_stance_future'] else 'disagreement exists', axis=1)
df_sample['disagreement_areas'] = df_sample['disagreement_areas'].fillna('')
df_sample['disagreement_areas'] = df_sample.apply(lambda x: (x['disagreement_areas']+'; Current Policy Stance').strip('; ') if x['agreement_stance_current']=='disagreement exists' else x['disagreement_areas'], axis=1)
df_sample['disagreement_areas'] = df_sample.apply(lambda x: (x['disagreement_areas']+'; Future Policy Stance').strip('; ') if x['agreement_stance_future']=='disagreement exists' else x['disagreement_areas'], axis=1)
df_sample['agreement_general'] = df_sample.apply(lambda x: 'irrelevant' if x['agreement_stance_current']=='irrelevant' and x['agreement_stance_future']=='irrelevant' and x['agreement_other']=='irrelevant' else 'disagreement exists' if x['agreement_stance_current']=='disagreement exists' or x['agreement_stance_future']=='disagreement exists' or x['agreement_other']=='disagreement exists' else 'mostly agree', axis=1)
df_sample.to_excel(directory+'labeling/labelled_monetary_final.xlsx', index=False)

# train-test split
test_l = list(df_sample.sample(int(np.round(len(df_sample)*0.2))).index)
train_l = [i for i in df_sample.index if i not in test_l]
df_train = df_sample.loc[train_l]
df_test = df_sample.loc[test_l]
print(len(train_l), len(test_l))

key_columns = ['staff_stance_current', 'staff_stance_future', 'buff_stance_current',
       'buff_stance_future', 'agreement_other', 'agreement_stance_current',
       'agreement_stance_future', 'agreement_general']
same_l = []
for col in key_columns:
    try:
        same_l.append(set(df_train[col].value_counts(normalize=True).index == df_test[col].value_counts(normalize=True).index)=={True})
    except Exception:
        same_l.append(False)
print(same_l)

# check the distribution of train and test sets
for col in key_columns:
    print(df_train[col].value_counts(normalize=True))
    print(df_test[col].value_counts(normalize=True))
    print('\n')

# update values
for var in key_columns:
    df_train = df_train.drop(var, axis=1).merge(df_sample[['Print ISBN', var]])
    df_test = df_test.drop(var, axis=1).merge(df_sample[['Print ISBN', var]])

df_train.to_excel(directory+'finetuning/monetary/training2.xlsx', index=False)
df_test.to_excel(directory+'finetuning/monetary/testing2.xlsx', index=False)

# five-fold cross validation
df_train = pd.read_excel(directory+'finetuning/monetary/training2.xlsx')
df_test = pd.read_excel(directory+'finetuning/monetary/testing2.xlsx')
df_sample = pd.concat([df_train, df_test], ignore_index=True)
len(df_train), len(df_test)

shuffled = df_train.sample(frac=1)
result = np.array_split(shuffled, 4)

# check the distribution of train and test sets
key_columns = ['staff_stance_current', 'staff_stance_future', 'buff_stance_current',
       'buff_stance_future', 'agreement_other', 'agreement_stance_current',
       'agreement_stance_future', 'agreement_general']
for i in range(4):
    df_test1 = result[i]
    df_train1 = pd.concat([result[j] for j in range(4) if j != i]+[df_test])
    same_l = []
    for col in key_columns:
        try:
            same_l.append(set(df_train1[col].value_counts(normalize=True).index == df_test1[col].value_counts(normalize=True).index)=={True})
        except Exception:
            same_l.append(False)
    print(same_l)

for i in range(4):
    df_test1 = result[i]
    df_train1 = pd.concat([result[j] for j in range(4) if j != i]+[df_test])
    for col in key_columns:
        print(df_train1[col].value_counts(normalize=True))
        print(df_test1[col].value_counts(normalize=True))
        print('\n')

# save
for i in range(4):
    df_test1 = result[i]
    df_train1 = pd.concat([result[j] for j in range(4) if j != i]+[df_test])
    for var in key_columns:
        df_train = df_train.drop(var, axis=1).merge(
            df_sample[['Print ISBN', var]])
        df_test = df_test.drop(var, axis=1).merge(
            df_sample[['Print ISBN', var]])
    df_test1.to_excel(directory+'finetuning/monetary/cv/testing_%d.xlsx'%i, index=False)
    df_train1.to_excel(directory+'finetuning/monetary/cv/training_%d.xlsx'%i, index=False)


# 4. estimate fine-tuning costs
# monetary classification
df_sample = pd.read_excel(directory+'labeling/to_label_all.xlsx')
df_sample = df_sample[df_sample['sector']=='Monetary']
testing_l = list(df_sample.sample(90)['Print ISBN'])
df_sample.loc[df_sample[df_sample['Print ISBN'].apply(lambda x: x in testing_l)].index,'testing'] = 1

# df_sample['answer'] = "{'staff_current': 'neutral', 'staff_future': 'neutral', 'authority_current': 'neutral', 'authority_future': 'neutral', 'agreement_other': 'agree'}"
df_sample['messages'] = df_sample.apply(lambda x: [
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts written by IMF staff and a country's authority, classify their current (or near-past) and near-future monetary policy stances (staff/authority_current/future) into restrictive, moderately restrictive, neutral, moderately accommodative, and accommodative, respectively. If the texts imply that authority agree/disagree with IMF staff on monetary policy issues not related to stance, assign agree/disagree to agreement_other; if there are mixed and balanced opinions, assign neutral; if there are no such information, assign irrelevant. Return a JSON dict without additional texts: \"staff_current\", \"staff_future\", \"authority_current\", \"authority_future\", \"agreement_other\".''',},
                {   "role": "user",
                    "content":  '''Part1 - IMF staff:/n%s/n/nPart2 - Authority:/n%s''' % (x['staff'], x['buff'])},
                {   "role": "assistant",
                    "content":  x['answer']}
            ], axis=1)

df_sample[['messages']].to_json(directory+'finetuning/all_mon.jsonl', orient='records', lines=True)
df_sample[df_sample['testing']!=1][['messages']].to_json(directory+'finetuning/training_mon.jsonl', orient='records', lines=True)

# fiscal classification
df_sample = pd.read_excel(directory+'labeling/to_label_all.xlsx')
df_sample = df_sample[df_sample['sector']=='Fiscal']
df_sample.loc[df_sample[df_sample['Print ISBN'].apply(lambda x: x in testing_l)].index,'testing'] = 1

df_sample['answer'] = "{'staff_current': 'neutral', 'staff_future': 'neutral', 'authority_current': 'neutral', 'authority_future': 'neutral', 'agreement_other': 'agree'}"
df_sample['messages'] = df_sample.apply(lambda x: [
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. 
                    Given two pieces of texts written by IMF staff and a country's authority, classify their current (or near-past) and near-future fiscal policy stances (staff/authority_current/future) into contractionary, moderately contractionary, neutral, moderately expansionary, and expansionary, respectively. If the texts imply that authority agree/disagree with IMF staff on fiscal policy issues not related to stance, assign agree/disagree to agreement_other; if there are mixed and balanced opinions, assign neutral; if there are no such information, assign irrelevant. Return a JSON dict without additional texts: \"staff_current\", \"staff_future\", \"authority_current\", \"authority_future\", \"agreement_other\".''',},
                {   "role": "user",
                    "content":  '''Part1 - IMF staff:/n%s/n/nPart2 - Authority:/n%s''' % (x['staff'], x['buff'])},
                {   "role": "assistant",
                    "content":  x['answer']}
            ], axis=1)

df_sample[['messages']].to_json(directory+'finetuning/all_fis.jsonl', orient='records', lines=True)
df_sample[df_sample['testing']!=1][['messages']].to_json(directory+'finetuning/training_fis.jsonl', orient='records', lines=True)

# Load the dataset
with open(directory+'finetuning/training_mon.jsonl', 'r', encoding='utf-8') as f:
    dataset = [json.loads(line) for line in f]

# Initial dataset stats
print("Num examples:", len(dataset))
print("First example:")
for message in dataset[0]["messages"]:
    print(message)

# Format error checks
format_errors = defaultdict(int)

for ex in dataset:
    if not isinstance(ex, dict):
        format_errors["data_type"] += 1
        continue

    messages = ex.get("messages", None)
    if not messages:
        format_errors["missing_messages_list"] += 1
        continue

    for message in messages:
        if "role" not in message or "content" not in message:
            format_errors["message_missing_key"] += 1

        if any(k not in ("role", "content", "name", "function_call", "weight")
               for k in message):
            format_errors["message_unrecognized_key"] += 1

        if message.get("role", None) not in (
        "system", "user", "assistant", "function"):
            format_errors["unrecognized_role"] += 1

        content = message.get("content", None)
        function_call = message.get("function_call", None)

        if (not content and not function_call) or not isinstance(content, str):
            format_errors["missing_content"] += 1

    if not any(
            message.get("role", None) == "assistant" for message in messages):
        format_errors["example_missing_assistant_message"] += 1

if format_errors:
    print("Found errors:")
    for k, v in format_errors.items():
        print(f"{k}: {v}")
else:
    print("No errors found")


encoding = tiktoken.get_encoding("cl100k_base")

# not exact!
# simplified from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def num_tokens_from_messages(messages, tokens_per_message=3, tokens_per_name=1):
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens

def num_assistant_tokens_from_messages(messages):
    num_tokens = 0
    for message in messages:
        if message["role"] == "assistant":
            num_tokens += len(encoding.encode(message["content"]))
    return num_tokens

def print_distribution(values, name):
    print(f"\n#### Distribution of {name}:")
    print(f"min / max: {min(values)}, {max(values)}")
    print(f"mean / median: {np.mean(values)}, {np.median(values)}")
    print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")

# Warnings and tokens counts
n_missing_system = 0
n_missing_user = 0
n_messages = []
convo_lens = []
assistant_message_lens = []

for ex in dataset:
    messages = ex["messages"]
    if not any(message["role"] == "system" for message in messages):
        n_missing_system += 1
    if not any(message["role"] == "user" for message in messages):
        n_missing_user += 1
    n_messages.append(len(messages))
    convo_lens.append(num_tokens_from_messages(messages))
    assistant_message_lens.append(num_assistant_tokens_from_messages(messages))

print("Num examples missing system message:", n_missing_system)
print("Num examples missing user message:", n_missing_user)
print_distribution(n_messages, "num_messages_per_example")
print_distribution(convo_lens, "num_total_tokens_per_example")
print_distribution(assistant_message_lens, "num_assistant_tokens_per_example")
n_too_long = sum(l > 16385 for l in convo_lens)
print(f"\n{n_too_long} examples may be over the 16,385 token limit, they will be truncated during fine-tuning")


# Pricing and default n_epochs estimate
MAX_TOKENS_PER_EXAMPLE = 16385

TARGET_EPOCHS = 3
MIN_TARGET_EXAMPLES = 100
MAX_TARGET_EXAMPLES = 25000
MIN_DEFAULT_EPOCHS = 1
MAX_DEFAULT_EPOCHS = 25

n_epochs = TARGET_EPOCHS
n_train_examples = len(dataset)
if n_train_examples * TARGET_EPOCHS < MIN_TARGET_EXAMPLES:
    n_epochs = min(MAX_DEFAULT_EPOCHS, MIN_TARGET_EXAMPLES // n_train_examples)
elif n_train_examples * TARGET_EPOCHS > MAX_TARGET_EXAMPLES:
    n_epochs = max(MIN_DEFAULT_EPOCHS, MAX_TARGET_EXAMPLES // n_train_examples)

n_billing_tokens_in_dataset = sum(min(MAX_TOKENS_PER_EXAMPLE, length) for length in convo_lens)
print(f"Dataset has ~{n_billing_tokens_in_dataset} tokens that will be charged for during training")
print(f"By default, you'll train for {n_epochs} epochs on this dataset")
print(f"By default, you'll be charged for ~{n_epochs * n_billing_tokens_in_dataset} tokens")