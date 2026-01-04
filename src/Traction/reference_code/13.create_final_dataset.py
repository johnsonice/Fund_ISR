'''
Generate the data file for analysis.
Input: df_documents_funda.csv, df_documents_general.csv, df_documents_sector_labelled_mon_v2.csv, df_documents_sector_labelled_fis_v2.csv, df_documents_sector_fis_revisited_ts.csv
Output: df_fin.csv, df_fin_reg.csv, df_fin_core.csv
'''
from util import *

directory = r'../../data\output/'


# 1. read data
# load full sample - country-year panel
df = pd.read_csv(directory+'df_documents_funda.csv')
df = df[~df.duplicated(subset=['country','year'], keep=False)]

# zero shot classification
df_zs = pd.read_csv(directory+'gpt/df_documents_general.csv')
df = df.merge(df_zs[['Print ISBN', 'agreement_gpt', 'Monetary_gpt', 'Fiscal_gpt',
       'External_gpt', 'Financial_gpt', 'Real_gpt', 'other_areas_gpt',
       'agreement_gpt_Monetary', 'agreement_gpt_Fiscal',
       'agreement_gpt_External', 'agreement_gpt_Financial',
       'agreement_gpt_Real']], how='left')

# monetary fine-tuned results
df_mon = pd.read_csv(directory+'gpt/df_documents_sector_labelled_mon_v2.csv')
df = df.merge(df_mon[['Print ISBN', 'stance_current_gpt_ft_staff',
       'stance_future_gpt_ft_staff', 'stance_current_gpt_ft_buff',
       'stance_future_gpt_ft_buff', 'agreement_gpt_ft',
       'disagreement_areas_gpt_ft']].rename(columns={c:'mon_'+c for c in ['stance_current_gpt_ft_staff',
       'stance_future_gpt_ft_staff', 'stance_current_gpt_ft_buff',
       'stance_future_gpt_ft_buff', 'agreement_gpt_ft',
       'disagreement_areas_gpt_ft']}), how='left')

# fiscal fine-tuned results
df_fis = pd.read_csv(directory+'gpt/df_documents_sector_labelled_fis_v2.csv')
df_fis2 = pd.read_csv(directory+'gpt/df_documents_sector_fis_revisited_ts.csv')
for col in ['stance_near_term_gpt_ft_staff', 'stance_near_term_gpt_ft_buff',
       'stance_near_term_gpt_ft_staff_num', 'stance_near_term_gpt_ft_buff_num',
       'agreement_stance_near_term_gpt_ft_num',
       'agreement_stance_near_term_gpt_ft_cate1',
       'agreement_stance_near_term_gpt_ft_cate2']:
    df_fis[col] = df_fis2[col]
df = df.merge(df_fis[['Print ISBN', 'agreement_gpt_ft',
       'disagreement_areas_gpt_ft', 'stance_near_term_gpt_ft_staff', 'stance_near_term_gpt_ft_buff']].rename(columns={c:'fis_'+c for c in ['agreement_gpt_ft',
       'disagreement_areas_gpt_ft', 'stance_near_term_gpt_ft_staff', 'stance_near_term_gpt_ft_buff']}), how='left')

df = df[~df['Print ISBN'].isna()]


# 2. generate additional variables

df['year'] = df['year'].apply(lambda x: int(x) if x==x else np.nan)


sector = 'mon'

df[sector+'_'+'stance_future_gpt_ft_staff'] = df[sector+'_'+'stance_future_gpt_ft_staff'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'stance_future_gpt_ft_buff'] = df[sector+'_'+'stance_future_gpt_ft_buff'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'stance_current_gpt_ft_buff'] = df[sector+'_'+'stance_current_gpt_ft_buff'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'stance_current_gpt_ft_staff'] = df[sector+'_'+'stance_current_gpt_ft_staff'].fillna('irrelevant')
df[sector+'_'+'agreement_gpt_ft'] = df[sector+'_'+'agreement_gpt_ft'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'disagreement_areas_gpt_ft'] = df[sector+'_'+'disagreement_areas_gpt_ft'].apply(lambda x: x if x==x else [])

df[sector+'_'+'stance_current_gpt_ft_staff'] = df[sector+'_'+'stance_current_gpt_ft_staff'].apply(lambda x: 'restrictive' if x in ['moderately tight', 'tightening bias'] else 'neutral' if x in ['close to neutral'] else x)
df[sector+'_'+'stance_current_gpt_ft_buff'] = df[sector+'_'+'stance_current_gpt_ft_buff'].apply(lambda x: 'restrictive' if x in ['moderately tight', 'tightening bias'] else 'neutral' if x in ['close to neutral'] else x)

stance_dict = {'tightening': 5, 'tightening bias': 4, 'no change': 3, 'loosening bias': 2, 'loosening': 1}
df[sector+'_'+'stance_future_gpt_ft_staff_num'] = df[sector+'_'+'stance_future_gpt_ft_staff'].apply(lambda x: stance_dict[x] if x in stance_dict else np.nan)
df[sector+'_'+'stance_future_gpt_ft_buff_num'] = df[sector+'_'+'stance_future_gpt_ft_buff'].apply(lambda x: stance_dict[x] if x in stance_dict else np.nan)
df[sector+'_'+'agreement_stance_future_gpt_ft_num'] = df[sector+'_'+'stance_future_gpt_ft_staff_num']-df[sector+'_'+'stance_future_gpt_ft_buff_num']
df[sector+'_'+'agreement_stance_future_gpt_ft_cate1'] = df[sector+'_'+'agreement_stance_future_gpt_ft_num'].apply(lambda x: 'major difference' if x >= 3 or x <= -3 else 'some difference' if x in [2, -2] else 'minor difference' if x in [1, -1] else 'no difference' if x==0 else 'irrelevant')
df[sector+'_'+'agreement_stance_future_gpt_ft_cate2'] = df[sector+'_'+'agreement_stance_future_gpt_ft_num'].apply(lambda x: 'significantly tighter' if x >= 3 else 'tighter' if x==2 else 'moderately tighter' if x==1 else 'same' if x==0 else 'moderately looser' if x==-1 else 'looser' if x==-2 else 'significantly looser' if x<=-3 else 'irrelevant')

stance_current_dict = {'accommodative': 0, 'neutral': 1, 'restrictive': 2}
df[sector+'_'+'stance_current_gpt_ft_staff_num'] = df[sector+'_'+'stance_current_gpt_ft_staff'].apply(lambda x: stance_current_dict[x] if x in stance_current_dict else np.nan)
df[sector+'_'+'stance_current_gpt_ft_buff_num'] = df[sector+'_'+'stance_current_gpt_ft_buff'].apply(lambda x: stance_current_dict[x] if x in stance_current_dict else np.nan)
df[sector+'_'+'agreement_stance_current_gpt_ft_num'] = df[sector+'_'+'stance_current_gpt_ft_staff_num']-df[sector+'_'+'stance_current_gpt_ft_buff_num']
df[sector+'_'+'agreement_stance_current_gpt_ft_cate2'] = df[sector+'_'+'agreement_stance_current_gpt_ft_num'].apply(lambda x: 'same' if x==0 else 'more accommodative' if x<0 else 'more restrictive' if x>0 else 'irrelevant')

df[sector+'_'+'agreement_stance_current_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'stance_current_gpt_ft_staff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_current_gpt_ft_staff']!=x[sector+'_'+'stance_current_gpt_ft_staff'] or x[sector+'_'+'stance_current_gpt_ft_buff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_current_gpt_ft_buff']!=x[sector+'_'+'stance_current_gpt_ft_buff'] else 'mostly agree' if x[sector+'_'+'stance_current_gpt_ft_staff']==x[sector+'_'+'stance_current_gpt_ft_buff'] else 'disagreement exists', axis=1)
# df[sector+'_'+'agreement_stance_future_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'stance_future_gpt_ft_staff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_future_gpt_ft_staff']!=x[sector+'_'+'stance_future_gpt_ft_staff'] or x[sector+'_'+'stance_future_gpt_ft_buff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_future_gpt_ft_buff']!=x[sector+'_'+'stance_future_gpt_ft_buff'] else 'mostly agree' if x[sector+'_'+'stance_future_gpt_ft_staff']==x[sector+'_'+'stance_future_gpt_ft_buff'] else 'disagreement exists', axis=1)
df[sector+'_'+'agreement_stance_future_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'stance_future_gpt_ft_staff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_future_gpt_ft_staff']!=x[sector+'_'+'stance_future_gpt_ft_staff'] or x[sector+'_'+'stance_future_gpt_ft_buff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_future_gpt_ft_buff']!=x[sector+'_'+'stance_future_gpt_ft_buff'] else 'mostly agree' if x[sector+'_'+'agreement_stance_future_gpt_ft_num'] in [-1, 0, 1] else 'disagreement exists', axis=1)

# df[sector+'_'+'agreement_general_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'agreement_stance_current_gpt_ft']=='irrelevant' and x[sector+'_'+'agreement_stance_future_gpt_ft']=='irrelevant' and x[sector+'_'+'agreement_gpt_ft']=='irrelevant' else 'disagreement exists' if x[sector+'_'+'agreement_stance_current_gpt_ft']=='disagreement exists' or x[sector+'_'+'agreement_stance_future_gpt_ft']=='disagreement exists' or x[sector+'_'+'agreement_gpt_ft']=='disagreement exists' else 'mostly agree', axis=1)
df[sector+'_'+'agreement_general_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'agreement_stance_current_gpt_ft']=='irrelevant' and x[sector+'_'+'agreement_stance_future_gpt_ft']=='irrelevant' and x[sector+'_'+'agreement_gpt_ft']=='irrelevant' else 'disagreement exists' if x[sector+'_'+'agreement_stance_current_gpt_ft']=='disagreement exists' or x[sector+'_'+'agreement_stance_future_gpt_ft_num']>1 or x[sector+'_'+'agreement_stance_future_gpt_ft_num']<-1 or (x[sector+'_'+'agreement_gpt_ft']=='disagreement exists' and x[sector+'_'+'disagreement_areas_gpt_ft']!='Future Policy Direction') else 'mostly agree', axis=1)


sector = 'fis'
df[sector+'_disagreement_areas_gpt_ft'] = df[sector+'_disagreement_areas_gpt_ft'].apply(lambda x: ast.literal_eval(x) if x==x and '[' in x else [x] if x==x else x)
df[sector+'_'+'stance_near_term_gpt_ft_staff'] = df[sector+'_'+'stance_near_term_gpt_ft_staff'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'stance_near_term_gpt_ft_buff'] = df[sector+'_'+'stance_near_term_gpt_ft_buff'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'agreement_gpt_ft'] = df[sector+'_'+'agreement_gpt_ft'].apply(lambda x: 'irrelevant' if x=='nan' else x)
df[sector+'_'+'disagreement_areas_gpt_ft'] = df[sector+'_'+'disagreement_areas_gpt_ft'].apply(lambda x: x if x==x else [])

stance_dict = {'tightening': 5, 'tightening bias': 4, 'no change': 3, 'loosening bias': 2, 'loosening': 1}
df[sector+'_'+'stance_near_term_gpt_ft_staff_num'] = df[sector+'_'+'stance_near_term_gpt_ft_staff'].apply(lambda x: stance_dict[x] if x in stance_dict else np.nan)
df[sector+'_'+'stance_near_term_gpt_ft_buff_num'] = df[sector+'_'+'stance_near_term_gpt_ft_buff'].apply(lambda x: stance_dict[x] if x in stance_dict else np.nan)
df[sector+'_'+'agreement_stance_near_term_gpt_ft_num'] = df[sector+'_'+'stance_near_term_gpt_ft_staff_num']-df[sector+'_'+'stance_near_term_gpt_ft_buff_num']
df[sector+'_'+'agreement_stance_near_term_gpt_ft_cate1'] = df[sector+'_'+'agreement_stance_near_term_gpt_ft_num'].apply(lambda x: 'major difference' if x >= 3 or x <= -3 else 'some difference' if x in [2, -2] else 'minor difference' if x in [1, -1] else 'no difference' if x==0 else 'irrelevant')
df[sector+'_'+'agreement_stance_near_term_gpt_ft_cate2'] = df[sector+'_'+'agreement_stance_near_term_gpt_ft_num'].apply(lambda x: 'significantly tighter' if x >= 3 else 'tighter' if x==2 else 'moderately tighter' if x==1 else 'same' if x==0 else 'moderately looser' if x==-1 else 'looser' if x==-2 else 'significantly looser' if x<=-3 else 'irrelevant')

# df[sector+'_'+'agreement_stance_near_term_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'stance_near_term_gpt_ft_staff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_near_term_gpt_ft_staff']!=x[sector+'_'+'stance_near_term_gpt_ft_staff'] or x[sector+'_'+'stance_near_term_gpt_ft_buff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_near_term_gpt_ft_buff']!=x[sector+'_'+'stance_near_term_gpt_ft_buff'] else 'mostly agree' if x[sector+'_'+'stance_near_term_gpt_ft_staff']==x[sector+'_'+'stance_near_term_gpt_ft_buff'] else 'disagreement exists', axis=1)
df[sector+'_'+'agreement_stance_near_term_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'stance_near_term_gpt_ft_staff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_near_term_gpt_ft_staff']!=x[sector+'_'+'stance_near_term_gpt_ft_staff'] or x[sector+'_'+'stance_near_term_gpt_ft_buff'] in ['', 'nan', 'n','unclear', 'irrelevant'] or x[sector+'_'+'stance_near_term_gpt_ft_buff']!=x[sector+'_'+'stance_near_term_gpt_ft_buff'] else 'mostly agree' if x[sector+'_'+'agreement_stance_near_term_gpt_ft_num'] in [-1, 0, 1] else 'disagreement exists', axis=1)

df[sector+'_'+'agreement_gpt_ft'] = df[sector+'_'+'agreement_gpt_ft'].apply(lambda x: 'mostly agree' if x in ['Micah mostly agree', 'appropriately agree', 'валлийский'] else x)

# df[sector+'_'+'agreement_general_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'agreement_stance_near_term_gpt_ft']=='irrelevant' and x[sector+'_'+'agreement_gpt_ft']=='irrelevant' else 'disagreement exists' if x[sector+'_'+'agreement_stance_near_term_gpt_ft']=='disagreement exists' or x[sector+'_'+'agreement_gpt_ft']=='disagreement exists' else 'mostly agree', axis=1)
df[sector+'_'+'agreement_general_gpt_ft'] = df.apply(lambda x: 'irrelevant' if x[sector+'_'+'agreement_stance_near_term_gpt_ft']=='irrelevant' and x[sector+'_'+'agreement_gpt_ft']=='irrelevant' else 'disagreement exists' if x[sector+'_'+'agreement_stance_near_term_gpt_ft_num'] not in [-1, 0, 1] or (x[sector+'_'+'agreement_gpt_ft']=='disagreement exists' and x[sector+'_'+'disagreement_areas_gpt_ft']!="['near-term policy direction']") else 'mostly agree', axis=1)

df[sector+'_'+'disagreement_areas_general_gpt_ft'] = df[sector+'_'+'disagreement_areas_gpt_ft']
df[sector+'_'+'disagreement_areas_general_gpt_ft'] = df.apply(lambda x: (x[sector+'_'+'disagreement_areas_general_gpt_ft']+['near-term policy direction']) if x[sector+'_'+'agreement_stance_near_term_gpt_ft']=='disagreement exists' and 'near-term policy direction' not in x[sector+'_'+'disagreement_areas_general_gpt_ft'] else x[sector+'_'+'disagreement_areas_general_gpt_ft'], axis=1)


# policy mix
df['mon_stance_future_gpt_ft_staff'] = df['mon_stance_future_gpt_ft_staff'].apply(lambda x: 'no change / unclear' if x in ['unclear', 'no change', 'gradual normalization'] else x)
df['fis_stance_near_term_gpt_ft_staff'] = df['fis_stance_near_term_gpt_ft_staff'].apply(lambda x: 'no change / unclear' if x in ['unclear', 'no change'] else x)

df['policy_mix_staff'] = df.apply(lambda x: np.nan if x['mon_stance_future_gpt_ft_staff']!=x['mon_stance_future_gpt_ft_staff'] or x['fis_stance_near_term_gpt_ft_staff']!=x['fis_stance_near_term_gpt_ft_staff'] else 'MtFt' if 'tightening' in x['mon_stance_future_gpt_ft_staff'] and 'tightening' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MtFn' if 'tightening' in x['mon_stance_future_gpt_ft_staff'] and 'no change / unclear' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MtFl' if 'tightening' in x['mon_stance_future_gpt_ft_staff'] and 'loosening' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MlFt' if 'loosening' in x['mon_stance_future_gpt_ft_staff'] and 'tightening' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MlFn' if 'loosening' in x['mon_stance_future_gpt_ft_staff'] and 'no change / unclear' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MlFl' if 'loosening' in x['mon_stance_future_gpt_ft_staff'] and 'loosening' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MnFt' if 'no change / unclear' in x['mon_stance_future_gpt_ft_staff'] and 'tightening' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MnFn' if 'no change / unclear' in x['mon_stance_future_gpt_ft_staff'] and 'no change / unclear' in x['fis_stance_near_term_gpt_ft_staff'] else
                                                'MnFl' if 'no change / unclear' in x['mon_stance_future_gpt_ft_staff'] and 'loosening' in x['fis_stance_near_term_gpt_ft_staff'] else np.nan
                                                , axis=1)

# df = df[(df['mon_stance_future_gpt_ft_buff']!='irrelevant')&(df['fis_stance_near_term_gpt_ft_buff']!='irrelevant')]
df['mon_stance_future_gpt_ft_buff'] = df['mon_stance_future_gpt_ft_buff'].apply(lambda x: 'no change / unclear' if x in ['unclear', 'no change', 'gradual normalization'] else x)
df['fis_stance_near_term_gpt_ft_buff'] = df['fis_stance_near_term_gpt_ft_buff'].apply(lambda x: 'no change / unclear' if x in ['unclear', 'no change'] else x)

df['policy_mix_buff'] = df.apply(lambda x: np.nan if x['mon_stance_future_gpt_ft_buff']!=x['mon_stance_future_gpt_ft_buff'] or x['fis_stance_near_term_gpt_ft_buff']!=x['fis_stance_near_term_gpt_ft_buff'] else 'MtFt' if 'tightening' in x['mon_stance_future_gpt_ft_buff'] and 'tightening' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MtFn' if 'tightening' in x['mon_stance_future_gpt_ft_buff'] and 'no change / unclear' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MtFl' if 'tightening' in x['mon_stance_future_gpt_ft_buff'] and 'loosening' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MlFt' if 'loosening' in x['mon_stance_future_gpt_ft_buff'] and 'tightening' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MlFn' if 'loosening' in x['mon_stance_future_gpt_ft_buff'] and 'no change / unclear' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MlFl' if 'loosening' in x['mon_stance_future_gpt_ft_buff'] and 'loosening' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MnFt' if 'no change / unclear' in x['mon_stance_future_gpt_ft_buff'] and 'tightening' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MnFn' if 'no change / unclear' in x['mon_stance_future_gpt_ft_buff'] and 'no change / unclear' in x['fis_stance_near_term_gpt_ft_buff'] else
                                                'MnFl' if 'no change / unclear' in x['mon_stance_future_gpt_ft_buff'] and 'loosening' in x['fis_stance_near_term_gpt_ft_buff'] else np.nan
                                                , axis=1)

key_cols = ['agreement_gpt',
 'agreement_gpt_Monetary',
 'agreement_gpt_Fiscal',
 'agreement_gpt_External',
 'agreement_gpt_Financial',
 'agreement_gpt_Real',
 'mon_agreement_gpt_ft', 'mon_agreement_stance_future_gpt_ft_num', 'mon_agreement_general_gpt_ft',
'fis_agreement_gpt_ft', 'fis_agreement_stance_near_term_gpt_ft_num', 'fis_agreement_general_gpt_ft']


idx_l = df[df['Print ISBN'].isna()].index
for col in key_cols:
    df.loc[idx_l, col] = np.nan
    df[col] = df[col].apply(lambda x: np.nan if x==99 else x)
    df[col] = df[col].apply(lambda x: np.nan if x=='irrelevant' else 0 if x=='disagreement exists' else 1 if x=='mostly agree' else x)

    print(df[col].value_counts())
    print('\n')

df['disagree_economic'] = df.apply(lambda x: 'economic assessment' in x['mon_disagreement_areas_gpt_ft'] or 'economic assessment' in x['fis_disagreement_areas_gpt_ft'], axis=1)
df['agreement_gpt_ft'] = (df['mon_agreement_general_gpt_ft'] + df['fis_agreement_general_gpt_ft'] == 2) | ((df['mon_agreement_general_gpt_ft'].isna()) & (df['fis_agreement_general_gpt_ft']==1)) | ((df['fis_agreement_general_gpt_ft'].isna()) & (df['mon_agreement_general_gpt_ft']==1))


# 3. save
df.to_csv(directory+'df_fin.csv', index=False)
df.drop(['staff',
 'buff', 'text_staff','text_buff',
 'text_sa',
 'paragraphs_sa',
 'paragraphs_bu','paragraphs_sr',
 'paragraphs_av'], axis=1).to_csv(directory+'df_fin_reg.csv', index=False)
df[['Print ISBN', 'country', 'Primary Country Code', 'year', 'publication_date', 'bm_date']+[c for c in df.columns if 'stance' in c.lower() or 'agree' in c.lower()]].to_csv(directory+'df_fin_reg_core.csv', index=False)