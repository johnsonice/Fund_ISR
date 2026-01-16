'''
Merge textual data and non-textual data.
Input: df_aiv.csv
Output: df_aiv_funda.csv
'''
from util import *

directory = r'../../data/'

# read data
df = pd.read_csv(directory+'output/df_aiv.csv').rename(columns={'Year from title': 'year'})
df = df[(~df['Full Title'].isna())]
df = df[df['year']!=2024]

# df.loc[df[df['Print ISBN']==9781484334850].index, 'year'] = 2017
# df.loc[df[df['Print ISBN']==9781475564082].index, 'year'] = 2016
# df.loc[df[df['Print ISBN']==9781484334980].index, 'year'] = 2017
# df.loc[df[df['Print ISBN']==9781616356767].index, 'year'] = 2021
# df['country'] = df['Title'].apply(lambda x: x.replace('—', '-') if ':' not in x else x.split(':')[0].replace('—', '-').replace('’', "'"))

df['bm_date'] = pd.to_datetime(df['bm_date']).dt.to_period('M')
df['bm_year'] = df['bm_date'].apply(lambda x: x.year)
df['bm_ref_date'] = df.apply(lambda x: str(int(x['bm_year']))+'-07', axis=1)
df['ref_date'] = df.apply(lambda x: str(int(x['year']))+'-07', axis=1)
df['year_l'] = df['year'] - 1
df['year_f'] = df.apply(lambda x: x['year']+1 if str(x['bm_date'])>x['ref_date'] else x['year'], axis=1)

print(df['year'].value_counts())


# 1. merge part of funda
df_funda = pd.read_csv(directory+'macro/fundamentals.csv')

country_dict = {'Republic of Moldova':'Moldova',
 'Republic of Tajikistan':'Tajikistan',
 'Republic of Slovenia':'Slovenia',
 'Republic of Congo':'Congo, Republic of',
 'Guinea- Bissau':'Guinea-Bissau',
 'Kingdom of the Netherlands - Netherlands':'Netherlands',
 'Turkey':'Türkiye',
 'Republic of Türkiye':'Türkiye',
 'Republic of Belarus':'Belarus',
 'Islamic Republic of Afghanistan':'Afghanistan',
 'Kingdom of the Netherlands-Aruba':'Aruba',
 'Kingdom of Lesotho':'Lesotho',
 'Republic of Mozambique':'Mozambique',
 'Kingdom of the Netherlands-the Netherlands':'Netherlands',
 'Republic of Kosovo':'Kosovo',
 'The Kingdom of the Netherlands-Netherlands':'Netherlands',
 'Republic of Korea':'Korea',
 'Kingdom of Eswatini':'Eswatini',
 'United Republic of Tanzania':'Tanzania',
 'Republic of Estonia':'Estonia',
 'Principality of Andorra':'Andorra',
 'Republic of Equatorial Guinea':'Equatorial Guinea',
 'Republic of Nauru':'Nauru',
 'Lao People’s Democratic Republic':'Lao P.D.R.',
 'Republic of Timor-Leste':'Timor-Leste',
 'Kingdom of the Netherlands - Aruba':'Aruba',
 "Cote d'Ivoire":"Côte d'Ivoire",
 'Republic of Madagascar':'Madagascar',
 "People's Republic of China":'China',
 'Russian Federation':'Russia',
 'Republic of Fiji':'Fiji',
 'Democratic Republic of Timor-Leste':'Timor-Leste',
 'Union of the Comoros':'Comoros',
 'Islamic Republic of Mauritania':'Mauritania',
 'Republic of Uzbekistan':'Uzbekistan',
 'The Federal Democratic Republic of Ethiopia':'Ethiopia',
 'Democratic Republic of São Tomé and Príncipe':'São Tomé and Príncipe',
 'Montenegro':'Montenegro, Rep. of',
 'Islamic Republic of Iran':'Iran',
 'Republic of Lithuania':'Lithuania',
 'The Gambia':'Gambia, The',
 'Kingdom of the Netherlands-Netherlands':'Netherlands',
 'Former Yugoslav Republic of Macedonia':'North Macedonia',
 'People’s Republic of China':'China',
 'Republic of North Macedonia':'North Macedonia',
 'Democratic Republic of the Congo':'Congo',
 'The Republic of Moldova':'Moldova',
 'Republic of Poland':'Poland',
 'Republic of Kazakhstan':'Kazakhstan',
 'Republic of the Marshall Islands':'Marshall Islands',
 'Republic of San Marino':'San Marino',
 'Federated States of Micronesia':'Micronesia',
 "The People's Republic of China":'China',
 'The Bahamas':'Bahamas, The',
 'Republic of Latvia':'Latvia',
 'Republic of Armenia':'Armenia',
 "Lao People's Democratic Republic":'Lao P.D.R.',
 'Arab Republic of Egypt':'Egypt',
 'Republic of Croatia':'Croatia',
 'Democratic Republic of São Tomé and Princípe':'São Tomé and Príncipe',
 'Republic of South Sudan':'South Sudan',
 'Kingdom of the Netherlands–the Netherlands':'Netherlands',
 'Republic of Palau':'Palau',
 'Union of Comoros':'Comoros',
 'Côte d’Ivoire':"Côte d'Ivoire",
 'Republic of Serbia':'Serbia',
 'Republic of Azerbaijan':'Azerbaijan',
 'Kingdom of the Netherlands':'Netherlands',
 'Kingdom of Swaziland': 'Eswatini',
 'Euro Area Policies': 'Euro Area',
 "People's Republic of China-Macao Special Administrative Region": 'Macao SAR',
 "People's Republic of China-Hong Kong Special Administrative Region": 'Hong Kong SAR',
 'People’s Republic of China-Macao Special Administrative Region': 'Macao SAR',
 'People’s Republic of China-Hong Kong Special Administrative Region': 'Hong Kong SAR',
 'Kingdom of the Netherlands-Curaçao and Sint Maarten': 'Kingdom of the Netherlands-Curacao and Sint Maarten'}
df['country'] = df['country'].apply(lambda x: country_dict[x] if x in country_dict else x)
df['country_lower'] = df['country'].apply(lambda x: x.lower())

df_funda = df_funda[(df_funda['year'].apply(lambda x: x>=2014))&(df_funda['Country'].apply(lambda x: x in (set(df['country']))))]
df_funda = df_funda[~df_funda.duplicated(subset=['Country','year'])]

df = df.merge(df_funda.rename(columns={'Country':'country'}), on=['country', 'year'], how='outer')

key_funda_cols = ['bank_debt', 'official_debt_USD', 'total_debt_service',
       'ext_debt_gross', 'govt_debt_net', 'PPP_GDP', 'inflation', 'potential_GDP',
        'real_GDP', 'unemployment', 'CA_Balance']
df_funda['year_f'] = df_funda['year']
df = df.merge(df_funda[['Country', 'year_f']+key_funda_cols].rename(columns={c: 'f_'+c for c in key_funda_cols}), left_on=['country','year_f'], right_on=['Country', 'year_f'], how='left')
df_funda['bm_year'] = df_funda['year']
df = df.merge(df_funda[['Country', 'bm_year']+key_funda_cols].rename(columns={c: 'f_'+c+'_bm' for c in key_funda_cols}), left_on=['country','bm_year'], right_on=['Country', 'bm_year'], how='left')

df['monetary_sample'] = df.apply(lambda x: x['Category'] not in ['Currency board', 'No separate legal tender'] and x['Currencyunion']!=1 and x['Print ISBN']==x['Print ISBN'], axis=1)
# len(df[(df['monetary_sample']==True)]), len(df[(df['staff_verified']==True)&(df['monetary_sample']==True)])

# IMF related variables (in program, TA, FSAP)
program_l = set(df[df['InProgram']==1]['country'])
df['InProgram_ever'] = df['country'].apply(lambda x: x in program_l)
df['InProgram_after'] = df.apply(lambda x: x['InProgram']==0 and x['country'] in set(df[(df['InProgram']==1)&(df['year']<x['year'])]['country']), axis=1)

df['ta'] = (df['text_staff']+df['text_sa']).apply(lambda x: x==x and 'technical assistance' in x.lower())
program_l = set(df[df['ta']==1]['country'])
df['ta_ever'] = df['country'].apply(lambda x: x in program_l)
df['ta_after'] = df.apply(lambda x: x['ta']==0 and x['country'] in set(df[(df['ta']==1)&(df['year']<x['year'])]['country']), axis=1)

df['fsap'] = (df['text_staff']+df['text_sa']).apply(lambda x: x==x and ('financial sector assessment program' in x.lower() or 'fsap' in x.lower()))
program_l = set(df[df['fsap']==1]['country'])
df['fsap_ever'] = df['country'].apply(lambda x: x in program_l)
df['fsap_after'] = df.apply(lambda x: x['fsap']==0 and x['country'] in set(df[(df['fsap']==1)&(df['year']<x['year'])]['country']), axis=1)


# 2. merge with CPA
df_cpa = pd.read_excel(directory+'macro/cpa.xlsx')
country_dict1 = {'Euro area': 'Euro Area',
 'Andorra, Principality of':'Andorra',
 'Congo, Democratic Republic of the': 'Congo'}
df_cpa['Country'] = df_cpa['Country'].apply(lambda x: country_dict1[x] if x in country_dict1 else x)

for i, row in df[(~df['Print ISBN'].isna())&(df['year']>=2018)].iterrows():
    if str(row['bm_date']) > row['ref_date']:
        temp_date = 'Fall' + ' ' + str(int(row['year']))
    else:
        temp_date = 'Spring' + ' ' + str(int(row['year']))
    if len(df_cpa[(df_cpa['Country']==row['country'])])>0:
        df.loc[i, 'mp_future_buff'] = df_cpa[(df_cpa['Country']==row['country'])&(df_cpa['Indicator']=='CPA_PA_010')][temp_date].iloc[0]
        df.loc[i, 'mp_future_staff'] = df_cpa[(df_cpa['Country']==row['country'])&(df_cpa['Indicator']=='CPA_PA_020')][temp_date].iloc[0]
        df.loc[i, 'fp_future_staff'] = df_cpa[(df_cpa['Country']==row['country'])&(df_cpa['Indicator']=='CPA_PA_050')][temp_date].iloc[0]
    if str(row['bm_date']) > row['bm_ref_date']:
        temp_date = 'Fall' + ' ' + str(int(row['bm_year']))
    else:
        temp_date = 'Spring' + ' ' + str(int(row['bm_year']))
    if len(df_cpa[(df_cpa['Country']==row['country'])])>0:
        df.loc[i, 'mp_future_buff_bm'] = df_cpa[(df_cpa['Country']==row['country'])&(df_cpa['Indicator']=='CPA_PA_010')][temp_date].iloc[0]
        df.loc[i, 'mp_future_staff_bm'] = df_cpa[(df_cpa['Country']==row['country'])&(df_cpa['Indicator']=='CPA_PA_020')][temp_date].iloc[0]
        df.loc[i, 'fp_future_staff_bm'] = df_cpa[(df_cpa['Country']==row['country'])&(df_cpa['Indicator']=='CPA_PA_050')][temp_date].iloc[0]


# 3. global series

# capb
df_capb = pd.read_csv(directory+'macro/capb.csv')
df = df.merge(df_capb[df_capb['COUNTRY.Name']=='Emerging Market and Middle-Income Economies'][['TIME_PERIOD', 'OBS_VALUE']].rename(columns={'TIME_PERIOD':'year', 'OBS_VALUE':'capb_emde'}), how='left')
df = df.merge(df_capb[df_capb['COUNTRY.Name']=='Advanced Economies'][['TIME_PERIOD', 'OBS_VALUE']].rename(columns={'TIME_PERIOD':'year', 'OBS_VALUE':'capb_ae'}), how='left')

# [c for c in set(df_capb['COUNTRY.Name']) if c not in set(df['country'])]
country_dict1 = {'Netherlands, The': 'Netherlands',
 'Russian Federation': 'Russia',
 'Euro Area (EA)': 'Euro Area'}
df_capb['country'] = df_capb['COUNTRY.Name'].apply(lambda x: country_dict1[x] if x in country_dict1 else x)

df = df.merge(df_capb[['TIME_PERIOD', 'country', 'OBS_VALUE']].rename(columns={'TIME_PERIOD':'year', 'OBS_VALUE':'capb'}), how='left')
df_capb['year_f'] = df_capb['TIME_PERIOD']
df = df.merge(df_capb[['country', 'year_f', 'OBS_VALUE']].rename(columns={'OBS_VALUE': 'f_capb'}), how='left')
df_capb['bm_year'] = df_capb['TIME_PERIOD']
df = df.merge(df_capb[['country', 'bm_year', 'OBS_VALUE']].rename(columns={'OBS_VALUE': 'f_capb_bm'}), how='left')

# fed funds rate
df_ffr = pd.read_csv(directory+'macro/FEDFUNDS.csv')
df_ffr['DATE'] = pd.to_datetime(df_ffr['DATE'])
df_ffr['year'] = df_ffr['DATE'].apply(lambda x: x.year)
df_ffr_yr = df_ffr.groupby('year')[['FEDFUNDS']].mean()
df_ffr_yr['FEDFUNDS_std'] = df_ffr.groupby('year')['FEDFUNDS'].std()
df_ffr_yr = df_ffr_yr.reset_index()
df = df.merge(df_ffr_yr, how='left')

df_ffr_yr['year_f'] = df_ffr_yr['year']
df = df.merge(df_ffr_yr[['year_f', 'FEDFUNDS']].rename(columns={'FEDFUNDS': 'f_FEDFUNDS'}), how='left')
df_ffr_yr['bm_year'] = df_ffr_yr['year']
df = df.merge(df_ffr_yr[['bm_year', 'FEDFUNDS']].rename(columns={'FEDFUNDS': 'f_FEDFUNDS_bm'}), how='left')

# vix
df_vix = pd.read_csv(directory+'macro/VIXCLS.csv')
df_vix['VIXCLS'] = df_vix['VIXCLS'].apply(lambda x: float(x) if x!='.' else np.nan)
df_vix['DATE'] = pd.to_datetime(df_vix['DATE'])
df_vix['year'] = df_vix['DATE'].apply(lambda x: x.year)
df_vix_yr = df_vix.groupby('year')[['VIXCLS']].mean()
df_vix_yr = df_vix_yr.reset_index()
df = df.merge(df_vix_yr, how='left')

df_vix_yr['year_f'] = df_vix_yr['year']
df = df.merge(df_vix_yr[['year_f', 'VIXCLS']].rename(columns={'VIXCLS': 'f_VIXCLS'}), how='left')
df_vix_yr['bm_year'] = df_vix_yr['year']
df = df.merge(df_vix_yr[['bm_year', 'VIXCLS']].rename(columns={'VIXCLS': 'f_VIXCLS_bm'}), how='left')

# EPU
df_epu = pd.read_csv(directory+'macro/All_Country_Data(EPU).csv')
df_epu_yr = df_epu.groupby('Year').mean().drop('Month', axis=1).reset_index().rename(columns={'Year': 'year', 'UK': 'United Kingdom',
 'US': 'United States', 'Mainland China': 'China'})
df = df.merge(df_epu_yr[['year', 'GEPU_current', 'GEPU_ppp']], how='left')

# [c for c in df_epu_yr.columns if c not in set(df['country'])]
for c in df_epu_yr.columns:
    if c in set(df['country']):
        df_temp = df_epu_yr[['year', c]]
        for i, row in df_temp.iterrows():
            if len(df[(df['country']==c)&(df['year']==row['year'])]) > 0:
                df.loc[df[(df['country']==c)&(df['year']==row['year'])].index, 'EPU'] = row[c]

# MPU
df_mpu = pd.read_excel(directory+'macro/HRS_MPU_monthly.xlsx')
df_mpu['year'] = df_mpu['Month'].apply(lambda x: int(x.split('m')[0]))
df_mpu_yr = df_mpu.groupby('year')[['US MPU']].mean().reset_index()
df = df.merge(df_mpu_yr, how='left')

# brics
brics_l = ['Brazil', 'Russia', 'India', 'China', 'South Africa']
bricsp_l = ['Brazil', 'Russia', 'India', 'China', 'South Africa', 'Iran', 'Egypt', 'Ethiopia', 'United Arab Emirates']
df['brics_dummy'] = df['country'].apply(lambda x: x in brics_l)
df['bricsplus_dummy'] = df['country'].apply(lambda x: x in bricsp_l)

# us-china tension
df_uct = pd.read_csv(directory+'macro/UCT.csv')
df_uct['year'] = df_uct['date'].apply(lambda x: int(x.split('m')[0]))
df_uct_yr = df_uct.groupby('year')[['UCT']].mean().reset_index()
df = df.merge(df_uct_yr, how='left')


# 4. external
df_neer = pd.read_excel(directory + 'macro/NEER_REER_IMF.xlsx')
# [c for c in set(df_neer['Country']) if c not in set(df['country'])]
country_dict1 = {'Iran, Islamic Rep. of': 'Iran',
                 'Congo, Dem. Rep. of the': 'Congo',
                 'Central African Rep.': 'Central African Republic',
                 'North Macedonia, Republic of': 'North Macedonia',
                 'Dominican Rep.': 'Dominican Republic',
                 'Fiji, Rep. of': 'Fiji',
                 'Czech Rep.': 'Czech Republic',
                 'Croatia, Rep. of': 'Croatia',
                 'Moldova, Rep. of': 'Moldova',
                 'Equatorial Guinea, Rep. of': 'Guinea',
                 'Netherlands, The': 'Netherlands',
                 'Lesotho, Kingdom of': 'Lesotho',
                 'China, P.R.: Hong Kong': 'Hong Kong SAR',
                 'Russian Federation': 'Russia',
                 'Poland, Rep. of': 'Poland',
                 'Armenia, Rep. of': 'Armenia',
                 'China, P.R.: Mainland': 'China',
                 'Slovak Rep.': 'Slovak Republic'}
df_neer['country'] = df_neer['Country'].apply(
    lambda x: country_dict1[x] if x in country_dict1 else x)

for i, row in df.iterrows():
    if len(df_neer[df_neer['country'] == row['country']]) > 0 and row[
        'year'] < 2024:
        df.loc[i, 'neer'] = \
        df_neer[df_neer['country'] == row['country']][row['year']].iloc[0]
        df.loc[i, 'd_neer'] = \
        df_neer[df_neer['country'] == row['country']][row['year']].iloc[0] / \
        df_neer[df_neer['country'] == row['country']][row['year'] - 1].iloc[
            0] - 1

for i, row in df.iterrows():
    if len(df_neer[df_neer['country'] == row['country']]) > 0 and row[
        'year_f'] == row['year_f'] and row['year_f'] < 2024:
        df.loc[i, 'f_neer'] = \
        df_neer[df_neer['country'] == row['country']][row['year_f']].iloc[0]
        df.loc[i, 'f_d_neer'] = \
        df_neer[df_neer['country'] == row['country']][row['year_f']].iloc[0] / \
        df_neer[df_neer['country'] == row['country']][row['year_f'] - 1].iloc[
            0] - 1
        df.loc[i, 'f_neer_bm'] = \
        df_neer[df_neer['country'] == row['country']][row['bm_year']].iloc[0]
        df.loc[i, 'f_d_neer_bm'] = \
        df_neer[df_neer['country'] == row['country']][row['bm_year']].iloc[0] / \
        df_neer[df_neer['country'] == row['country']][row['bm_year'] - 1].iloc[
            0] - 1

# reserves
df_reserves = pd.read_csv(directory+'macro/reserves.csv')
df = df.merge(df_reserves[['CountryCode', 'year', 'official_reserves']], how='left')


# 5. election
df_election = pd.read_excel(directory+'macro/election.xlsx')
df_election['Last Election'] = pd.to_datetime(df_election['Last Election'].apply(lambda x: x if x != '-' else np.nan))
df_election['election_year2'] = df_election['Last Election'].apply(lambda x: x.year)
df_election['Cycle'] = df_election['Cycle'].apply(lambda x: int(x.replace(' Years','')) if x==x else np.nan)
df_election['election_year1'] = df_election['election_year2']-df_election['Cycle']
df_election['election_year0'] = df_election['election_year1']-df_election['Cycle']
df_election['election_year3'] = df_election['election_year2']+df_election['Cycle']

# [c for c in set(df['country']) if c not in set(df_election['Country'])]

country_dict1 = {
 'Laos': 'Lao P.D.R.',
 'Cape Verde': 'Cabo Verde',
 'Guinea Bissau': 'Guinea-Bissau',
 "Côte D'Ivoire": "Côte d'Ivoire",
 'Montenegro': 'Montenegro, Rep. of',
 'Democratic Republic of the Congo': 'Congo',
 'United States of America': 'United States',
 'Saint Lucia': 'St. Lucia',
 'Saint Vincent and the Grenadines': 'St. Vincent and the Grenadines',
 'Saint Kitts and Nevis': 'St. Kitts and Nevis',
 'Slovakia': 'Slovak Republic',
 'Gambia': 'Gambia, The',
 'Turkey':'Türkiye',
 'Bahamas':'Bahamas, The',
 'South Korea':  'Korea'}
df_election['country'] = df_election['Country'].apply(lambda x: country_dict1[x] if x in country_dict1 else x)

for i, row in df.iterrows():
    if len(df_election[df_election['country']==row['country']])>0:
        df_temp = df_election[df_election['country']==row['country']].iloc[0]
        for j in range(0,4):
            if row['year']==df_temp['election_year%d'%j]:
                df.loc[i, 'election_years_left'] = 0
                break
            elif j==0 and row['year']<df_temp['election_year%d'%j]:
                df.loc[i, 'election_years_left'] = df_temp['election_year%d'%j]-row['year']
            elif j > 0 and row['year']>df_temp['election_year%d'%(j-1)] and row['year']<df_temp['election_year%d'%(j)]:
                df.loc[i, 'election_years_left'] = df_temp['election_year%d'%j]-row['year']


# political variables
df_political = pd.read_csv(directory+'macro/DPI2020.csv')
df_political = df_political[['countryname', 'year', 'execrlc', 'polariz', 'stabs', 'allhouse', 'system', 'yrcurnt']]

# [c for c in set(df['country']) if c not in set(df_political['country'])]
# [c for c in set(df_political['country']) if c not in set(df['country'])]
country_dict1 = {
 'Laos': 'Lao P.D.R.',
 'Trinidad-Tobago': 'Trinidad and Tobago',
 'eSwatini':'Eswatini',
 'S. Africa': 'South Africa',
 'Congo (DRC)': 'Congo',
 'UK': 'United Kingdom',
 'Eq. Guinea': 'Equatorial Guinea',
 'Solomon Is.': 'Solomon Islands',
 'Cent. Af. Rep.': 'Central African Republic',
 'PRC': 'China',
 'Comoro Is.':'Comoros',
 'Czech Rep.': 'Czech Republic',
 'Dom. Rep.': 'Dominican Republic',
 'Brunei': 'Brunei Darussalam',
 'C. Verde Is.': 'Cabo Verde',
 'Slovakia': 'Slovak Republic',
 'Swaziland': 'Eswatini',
 'Gambia': 'Gambia, The',
 "Cote d'Ivoire": "Côte d'Ivoire",
 'Bosnia-Herz': 'Bosnia and Herzegovina',
 'USA':'United States',
 'FRG/Germany':'Germany',
 'Bahamas': 'Bahamas, The',
 'Turkey':'Türkiye',
 'ROK': 'Korea',
 'UAE': 'United Arab Emirates',
 'P. N. Guinea':'Papua New Guinea'}
df_political['country'] = df_political['countryname'].apply(lambda x: country_dict1[x] if x in country_dict1 else x)
df = df.merge(df_political.drop('countryname', axis=1), how='left')
df = df[~df.duplicated(subset=['country', 'year'])]

# 6. others
# commodity price
df_comm = pd.read_csv(directory+'macro/PALLFNFINDEXQ.csv')
df_comm['DATE'] = pd.to_datetime(df_comm['DATE'])
df_comm['year'] = df_comm['DATE'].apply(lambda x: x.year)
df_comm_yr = df_comm.groupby('year')[['PALLFNFINDEXQ']].mean()
df_comm_yr['PALLFNFINDEXQ_std'] = df_comm.groupby('year')['PALLFNFINDEXQ'].std()
df_comm_yr = df_comm_yr.reset_index()
df = df.merge(df_comm_yr, how='left')

# TODO: risk measures from ve

# # BIS data
# df_bis = pd.read_csv(directory+'macro/macro_daily.csv')
# df_bis['date'] = pd.to_datetime(df_bis['date'])
# df_bis['year'] = df_bis['date'].apply(lambda x: x.year)
# df_bis = df_bis.sort_values(by='date')
# df_bis = df_bis[df_bis['date'].apply(lambda x: str(x)<='2024-03-13' and str(x)>='2014-01-01')]
# df_bis = df_bis[~df_bis.duplicated(subset=['country_name', 'year'])]
# df_bis[['country_name', 'year', 'Inflation target', 'Policy rates']].to_csv('cb_policy_rates.csv', index=False)

df_bis = pd.read_csv(directory+'macro/cb_policy_rates.csv')
df_bis['country_name'] = df_bis['country_name'].apply(lambda x: 'congo, republic of' if x=='congo' else x)
country_dict1 = { 'macao': 'macao sar',
 'montenegro': 'montenegro, rep. of',
 'bahamas': 'bahamas, the',
 'turkey': 'türkiye',
 'cape verde': 'cabo verde',
 'trinidad & tobago': 'trinidad and tobago',
 'curaçao & sint maarten': 'kingdom of the netherlands-curacao and sint maarten',
 'myanmar (burma)': 'myanmar',
 'hong kong': 'hong kong sar',
 'saint lucia': 'st. lucia',
 'saint kitts & nevis': 'st. kitts and nevis',
 'brunei':'brunei darussalam',
 'congo (democratic republic)': 'congo',
 'slovakia': 'slovak republic',
 'micronesia (fed. states of)': 'micronesia',
 'bosnia & herzegovina': 'bosnia and herzegovina',
 'antigua & barbuda': 'antigua and barbuda',
 'gambia': 'gambia, the',
 'sao tome & principe': 'são tomé and príncipe',
 'south korea': 'korea',
 'saint vincent & the grenadines': 'st. vincent and the grenadines'}
df_bis['country_lower'] = df_bis['country_name'].apply(lambda x: country_dict1[x] if x in country_dict1 else x)
df_bis.drop('country_name', axis=1, inplace=True)

df = df.merge(df_bis, how='left')

df_bis['year_f'] = df_bis['year']
df = df.merge(df_bis[['Inflation target', 'Policy rates', 'country_lower', 'year_f']].rename(columns={c:'f_'+c for c in ['Policy rates', 'Inflation target']}), how='left')
df_bis['bm_year'] = df_bis['year']
df = df.merge(df_bis[['Inflation target', 'Policy rates', 'country_lower', 'bm_year']].rename(columns={c:'f_'+c+'_bm' for c in ['Policy rates', 'Inflation target']}), how='left')

# pb
df_pb = pd.read_csv(directory + 'macro/pb.csv')
country_dict1 = {"China, People's Republic of": 'China',
                 'Saint Kitts and Nevis': 'St. Kitts and Nevis',
                 'Congo, Dem. Rep. of the': 'Congo',
                 'Russian Federation': 'Russia',
                 'Saint Vincent and the Grenadines': 'St. Vincent and the Grenadines',
                 'Türkiye, Republic of': 'Türkiye',
                 'North Macedonia ': 'North Macedonia',
                 'Congo, Republic of ': 'Congo, Republic of',
                 'Micronesia, Fed. States of': 'Micronesia',
                 'Saint Lucia': 'St. Lucia',
                 'Korea, Republic of': 'Korea'}
# [c for c in set(df_pb['Government primary balance, percent of GDP (% of GDP)']) if c not in set(df['country'])]
# [c for c in set(df['country']) if c not in set(df_pb['Government primary balance, percent of GDP (% of GDP)'])]

df_pb['country'] = df_pb[
    'Government primary balance, percent of GDP (% of GDP)'].apply(
    lambda x: country_dict1[x] if x in country_dict1 else x)
for i, row in df.iterrows():
    if len(df_pb[df_pb['country'] == row['country']]) > 0 and row[
        'year'] < 2023:
        df.loc[i, 'pb'] = \
        df_pb[df_pb['country'] == row['country']][str(int(row['year']))].iloc[0]

for i, row in df.iterrows():
    if len(df_pb[df_pb['country'] == row['country']]) > 0 and row['year_f'] == \
            row['year_f'] and row['year_f'] < 2023:
        df.loc[i, 'f_pb'] = \
        df_pb[df_pb['country'] == row['country']][str(int(row['year_f']))].iloc[
            0]
        df.loc[i, 'f_pb_bm'] = df_pb[df_pb['country'] == row['country']][
            str(int(row['bm_year']))].iloc[0]

# 7. SAVE
df.to_csv(directory+'output/df_aiv_funda.csv', index=False)

# # add fundamentals to the documents file
# df = pd.read_csv(directory+'output/df_aiv_funda.csv')
df_documents = pd.read_csv(directory+'output/df_documents.csv')
df_documents = df_documents.drop(['year', 'country'], axis=1).merge(df, how='right')
df_documents.to_csv(directory+'output/df_documents_funda.csv', index=False)