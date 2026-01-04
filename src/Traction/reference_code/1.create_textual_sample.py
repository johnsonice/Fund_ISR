'''
Read and preprocess textual data.
Input: AIV report files
Output: df_aiv.csv, df_paragraphs.csv
'''
from util import *

directory = r'../../data/'

# read meta data
df_meta = pd.read_excel(directory+'aiv/IMF_Main_MetaData_20240710_toRan_filtered.xlsx')
# df_meta = pd.read_excel(directory+'IMF_Main_MetaData_20240710_toRan_v2 1.xlsx')


# 1. create dataframe from folders
folder_dict = {}
for root, dirs, files in os.walk(directory + r'aiv_text/results_v2',
                                 topdown=False):
    for name in dirs:
        if 'spr_isr' not in name:
            folder_dict[name] = os.path.join(root, name)
for root, dirs, files in os.walk(directory + r'aiv_text/results_v5',
                                 topdown=False):
    for name in dirs:
        if 'spr_isr' not in name:
            folder_dict[name] = os.path.join(root, name)

staff_dict = {}
staff_content_dict = {}
text_sa_dict = {}
para_sa_dict = {}
buff_dict = {}
buff_content_dict = {}
para_bu_dict = {}
for folder in folder_dict:
    if folder not in staff_dict:
        for root, dirs, files in os.walk(folder_dict[folder]):
            for i in range(len(files)):
                if 'A00' in sorted(files)[i] and folder not in staff_dict:
                    with open(os.path.join(root, sorted(files)[i]), 'r',
                              encoding='utf-8') as f:
                        temp = f.read()
                    soup = bs.BeautifulSoup(temp)
                    sec_l = soup.find_all('sec')
                    sec = [sec for sec in sec_l if
                           'staff appraisal' in sec.find(
                               'title').text.lower() or 'staff apraisal' in sec.find(
                               'title').text.lower()]
                    if len(sec) > 0:
                        sec = sec[0]
                        for s in sec.select('fig'):
                            s.extract()
                        for s in sec.select('table-wrap'):
                            s.extract()
                        end = str([l for l in sec.find_all('p') if
                                   len(l.text.strip()) > 0 and l.text.strip()[
                                       0].isdigit()][-1])
                        sec = bs.BeautifulSoup(
                            str(sec)[:str(sec).find(end) + len(end)])
                        staff_dict[folder] = os.path.join(root,
                                                          sorted(files)[i])
                        staff_content_dict[folder] = temp
                        text_sa_dict[folder] = str(sec)
                        para_sa_dict[folder] = [l.text for l in
                                                sec.find_all('p')] + [p for p in
                                                                      list(
                                                                          itertools.chain.from_iterable(
                                                                              [
                                                                                  l.text.split(
                                                                                      '\n')
                                                                                  for
                                                                                  l
                                                                                  in
                                                                                  sec.find_all(
                                                                                      'list')]))
                                                                      if
                                                                      p.strip() != '']
            for i in range(len(files) - 1, 0, -1):
                if i == len([f for f in files if 'A00' in f]) - 1 or i == len(
                        [f for f in files if
                         'A00' in f]) and folder not in buff_dict and not (
                        folder in staff_dict and staff_dict[
                    folder] == os.path.join(root, sorted(files)[i])):
                    with open(os.path.join(root, sorted(files)[i]), 'r',
                              encoding='utf-8') as f:
                        temp = f.read()
                    soup = bs.BeautifulSoup(temp)
                    for s in soup.select('abstract'):
                        s.extract()
                    if len([a for a in
                            soup.find('body').find_all('article-title') if
                            'statement by' in a.text.lower() or 'statement on' in a.text.lower()]) > 0:
                        buff_dict[folder] = os.path.join(root, sorted(files)[i])
                        buff_content_dict[folder] = temp
                        para_bu_dict[folder] = [l.text for l in
                                                soup.find('body').find_all('p')
                                                if l.text.strip() != '']
                    elif len([p for p in soup.find_all('p') if
                              p.text.lower().strip().startswith(
                                      'statement by')]) > 0:
                        buff_dict[folder] = os.path.join(root, sorted(files)[i])
                        buff_content_dict[folder] = temp
                        para_bu_dict[folder] = [l.text for l in
                                                [p for p in soup.find_all('p')
                                                 if
                                                 p.text.lower().strip().startswith(
                                                     'statement by')][
                                                    0].find_all_next('p') if
                                                l.text.strip() != '']

df = pd.DataFrame(
    [staff_dict, staff_content_dict, buff_dict, buff_content_dict, text_sa_dict,
     para_sa_dict, para_bu_dict]).T
df = df.reset_index()
df = df[df['index'].apply(lambda x: not x.startswith('spr_'))]
df = df.rename(
    columns={'index': 'Print ISBN', 0: 'filename_staff', 1: 'text_staff',
             2: 'filename_buff', 3: 'text_buff', 4: 'text_sa',
             5: 'paragraphs_sa', 6: 'paragraphs_bu'})

df['buff_verified'] = df['paragraphs_bu'].apply(lambda x: x == x and len(x) > 0)
df['staff_verified'] = df['paragraphs_sa'].apply(
    lambda x: x == x and len(x) > 0)

df_meta['Print ISBN'] = df_meta['Print ISBN'].apply(lambda x: str(x))
df = df.merge(df_meta[['Print ISBN', 'Extract text after ":"', 'Full Title',
                       'Subtitle', 'Title', 'Primary Country Code',
                       'Year from title', 'Publication Date']], on='Print ISBN',
              how='left')
for t in ['Extract text after ":"', 'Full Title', 'Subtitle']:
    df[t] = df[t].fillna('')
df['title_all'] = df.apply(lambda x: ', '.join(
    [x['Extract text after ":"'], x['Full Title'], x['Subtitle']]), axis=1)
df.loc[df[df['title_all'].apply(
    lambda x: x == x and 'statement by' in x.lower())].index, 'has_buff'] = 1
df.loc[df[(df['has_buff'] != 1) & (df['buff_verified'] == 1) & (
    df['paragraphs_bu'].apply(lambda x: 'does not alter' in ' '.join(
        x).lower() or 'does not change' in ' '.join(
        x).lower() if x == x else False))].index, 'paragraphs_bu'] = np.nan
df['buff_verified'] = df['paragraphs_bu'].apply(lambda x: x == x and len(x) > 0)

df.loc[df[df['Print ISBN'] == '9781484334850'].index, 'Year from title'] = 2017
df.loc[df[df['Print ISBN'] == '9781475564082'].index, 'Year from title'] = 2016
df.loc[df[df['Print ISBN'] == '9781484334980'].index, 'Year from title'] = 2017
df.loc[df[df['Print ISBN'] == '9781616356767'].index, 'Year from title'] = 2021

df.drop('title_all', axis=1, inplace=True)


# 2. get additional paragraphs from staff reports
for j, row in df.iterrows():
    if j >= 0 and row['text_staff'] == row['text_staff']:
        text_l = []
        staff_l = []
        authority_l = []

        soup = bs.BeautifulSoup(row['text_staff'])
        for s in soup.select('fig'):
            s.extract()
        for s in soup.select('table-wrap'):
            s.extract()
        for s in soup.select('boxed-text'):
            s.extract()

        # # key issues
        # key_issues = [s for s in soup.find_all('sec', {'sec-type':'contents'}) if 'key issues' in s.find('title').text.lower()][0].find_all('p')
        # staff_l += key_issues[:[i for i in range(len(key_issues)) if key_issues[i].text.strip().lower().startswith('approved by')][0]]

        # other paragraphs
        sec_l = soup.find_all('sec')
        try:
            start = [i for i in range(len(sec_l)) if
                     sec_l[i].find('title').text.lower() == 'contents'][0] + 1
        except Exception:
            start = 0
        end = [i for i in range(len(sec_l)) if
               'staff appraisal' in sec_l[i].find(
                   'title').text.lower() or 'staff apraisal' in sec_l[i].find(
                   'title').text.lower()][0]
        sec_l = sec_l[start:end]
        for sec in sec_l:
            if len(sec.find_all('sec')) == 0 and sec not in text_l:
                text_l.append(sec)
            else:
                text_l += [s for s in sec.find_all('sec') if s not in text_l]
                for s in sec.find_all('sec'):
                    s.extract()
                if sec.text.strip() != '' and sec not in text_l:
                    text_l.append(sec)

        if len([sec for sec in text_l if
                sec.find('title') != None and 'authorit' in sec.find(
                        'title').text.lower()]) > 0:
            rule_type = 0
        elif len([p for p in sec.find_all('p') for sec in text_l if
                  p.find('bold') != None and p.find(
                          'bold').text.lower().startswith(
                          'authorit') and p.text.lower().replace('’',
                                                                 '').replace(
                          "'", '').strip() not in ["authorities views",
                                                   "authorities view"]]) > 0:
            rule_type = 1
        elif len([p for p in sec.find_all('p') for sec in text_l if
                  p.find('bold') != None and p.text.lower().replace('’',
                                                                    '').replace(
                          "'", '').strip() in ["authorities views",
                                               "authorities view"]]) > 0:
            rule_type = 3
        else:
            rule_type = 2

        # Rule: eg. botswana 2021 (806); peru 2021 (820); Uzbekistan 2021 (801)
        if rule_type == 0:
            for sec in text_l:
                if sec.find('title') != None and 'authorit' in sec.find(
                        'title').text.lower():
                    authority_l += sec.find_all('p')
                else:
                    staff_l += sec.find_all('p')

        # Rule: eg. china 2015 (174)
        elif rule_type == 1:
            for sec in text_l:
                p_l = sec.find_all('p')
                if len(p_l) > 0:
                    for p in p_l:
                        if p.find('bold') != None and p.find(
                                'bold').text.lower().startswith('authorit'):
                            authority_l.append(p)
                        else:
                            staff_l.append(p)

        # Rule: eg. aruba 2017 (262)
        elif rule_type == 3:
            for sec in text_l:
                p_l = sec.find_all('p')
                if len(p_l) > 0:
                    for i in range(len(p_l)):
                        p = p_l[i]
                        if p.find('bold') != None and p.text.lower().replace(
                                '’', '').replace("'", '').strip() in [
                            "authorities views", "authorities view"]:
                            authority_l.append(p_l[i + 1])
                        elif p not in authority_l:
                            staff_l.append(p)

        # Rule: eg. Lithuania 2021 (843)
        else:
            for sec in text_l:
                p_l = sec.find_all('p')
                if len(p_l) > 0:
                    staff_l += p_l[:-1]
                    if p_l[-1].find('bold') != None and 'authorit' in p_l[
                        -1].find('bold').text.lower():
                        authority_l.append(p_l[-1])
                    else:
                        staff_l.append(p_l[-1])

        df.loc[j, 'paragraphs_sr'] = str([p.text for p in staff_l])
        df.loc[j, 'paragraphs_av'] = str([p.text for p in authority_l])
        if rule_type == 2:
            df.loc[j, 'av_uncertain'] = True

# # check missing data
# df_meta[df_meta['Print ISBN'].apply(lambda x: str(x) not in folder_dict)]#.to_excel(directory+'output/aiv_missing_v2.xlsx', index=False)


# 3. get board meeting dates
folder_dict = {}
for root, dirs, files in os.walk(directory+'aiv_text/', topdown=False):
    for name in dirs:
        if 'spr_isr' not in name:
            folder_dict[name] = os.path.join(root, name)

for i, row in df[~df['Full Title'].isna()].iterrows():
    if i >= 0:
        soup = bs.BeautifulSoup(row['text_staff'])
        try:
            sec = [s for s in soup.find_all('sec') if len([p for p in s.find_all('title') if p.text.lower().startswith('key issues')])>0 or len([p for p in s.find_all('title') if p.text.lower().startswith('executive summary')])>0 or '<bold>Context</bold>' in str(s) or len([p for p in s.find_all('p') if p.text.lower().startswith('staff report')])>0 or len([p for p in s.find_all('p') if ':' in p.text and p.text.split(':')[1].lower().strip().startswith('staff report')])>0 or len([p for p in s.find_all('p') if '-' in p.text and p.text.split('-')[1].lower().replace('romania ', '').strip().startswith('staff report')])>0][0]
            for p in sec.find_all('p'):
                try:
                    df.loc[i, 'bm_date'] = pd.to_datetime(p.text.replace('201 ', '201').replace('202 ', '202'))
                    break
                except Exception:
                    pass
        except Exception:
            try:
                sec = soup.find('book-front')
                time_l = []
                for p in sec.find_all('p'):
                    try:
                        time_l.append(pd.to_datetime(p.text.replace('201 ', '201').replace('202 ', '202')))
                        if len(time_l) == 2:
                            df.loc[i, 'bm_date'] = time_l[-1]
                            break
                    except Exception:
                        pass
            except Exception:
                for root, dirs, files in os.walk(folder_dict[str(row['Print ISBN'])]):
                    for f in files:
                        if 'A000' in f:
                            with open(os.path.join(folder_dict[str(row['Print ISBN'])], f), 'r', encoding='utf-8') as f:
                                temp = f.read()
                                soup = bs.BeautifulSoup(temp)
                                try:
                                    sec = [s for s in soup.find_all('sec') if len([p for p in s.find_all('title') if p.text.lower().startswith('key issues')])>0 or len([p for p in s.find_all('title') if p.text.lower().startswith('executive summary')])>0 or '<bold>Context</bold>' in str(s) or len([p for p in s.find_all('p') if p.text.lower().startswith('staff report')])>0 or len([p for p in s.find_all('p') if ':' in p.text and p.text.split(':')[1].lower().strip().startswith('staff report')])>0 or len([p for p in s.find_all('p') if '-' in p.text and p.text.split('-')[1].lower().replace('romania ', '').strip().startswith('staff report')])>0][0]
                                    for p in sec.find_all('p'):
                                        try:
                                            df.loc[i, 'bm_date'] = pd.to_datetime(p.text.replace('201 ', '201').replace('202 ', '202'))
                                            break
                                        except Exception:
                                            pass
                                except Exception:
                                    try:
                                        sec = soup.find('book-front')
                                        time_l = []
                                        for p in sec.find_all('p'):
                                            try:
                                                time_l.append(pd.to_datetime(p.text.replace('201 ', '201').replace('202 ', '202')))
                                                if len(time_l) == 2:
                                                    df.loc[i, 'bm_date'] = time_l[-1]
                                                    break
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
    if row['bm_date']!=row['bm_date']:
        df.loc[i,'bm_date'] = pd.to_datetime(row['Publication Date'])


# 4. additional adjustment and analysis
# country and year
df.loc[df[df['Print ISBN']==9781484334850].index, 'year'] = 2017
df.loc[df[df['Print ISBN']==9781475564082].index, 'year'] = 2016
df.loc[df[df['Print ISBN']==9781484334980].index, 'year'] = 2017
df.loc[df[df['Print ISBN']==9781616356767].index, 'year'] = 2021
df['country'] = df['Title'].apply(lambda x: x.replace('—', '-') if x==x and ':' not in x else x.split(':')[0].replace('—', '-').replace('’', "'") if x==x else x)

# textual complexity
df.loc[df[~df['Full Title'].isna()].index, 'complexity'] = df[~df['Full Title'].isna()]['paragraphs_sr'].apply(lambda x: textual_complexity('\n'.join(x)))
for col in ['Flesch Reading Ease', 'Flesch-Kincaid Grade Level', 'Gunning Fog Index', 'Coleman-Liau Index', 'SMOG Index', 'Automated Readability Index', 'Lexical Diversity (Type-Token Ratio)', 'Average Sentence Length', 'Number of Words']:
    df[col] = df['complexity'].apply(lambda x: x[col] if x==x else np.nan)

# IMF's assessment of past policies
for i, row in df.iterrows():
    if i >= 0 and row['Full Title']==row['Full Title'] and len(row['paragraphs_sa'])>0:
        chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given a piece of text written by IMF staff concerning a particular country in a given year, evaluate IMF staff's assessment of how appropriate the country's authorities' last-year policy decisions are based on the text only. First, assign a numerical value to the extent of the appropriateness of the authorities' past policy as assessed by IMF staff, ranging from -5 to 5, where -5 stands for completely inappropriate and 5 stands for completely appropriate. Second, for monetary/fiscal policy, assign a value from -5 to 5 to the extent of the appropriateness of the authorities' past monetary/fiscal policy as assessed by IMF staff, respectively. If there is no relevant information, assign a value of 99. Please respond in a clean json dictionary: \"appropriateness\", \"appropriateness_monetary\", \"appropriateness_fiscal\".''',},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\nText: \n%s''' % (row['country'], row['year'], '\n'.join(row['paragraphs_sa']))}
            ],
            model="gpt-4o-2024-08-06",
            temperature=0
        )
        try:
            result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
            df.loc[i, 'appropriateness'] = result['appropriateness']
            for sector in ['monetary', 'fiscal']:
                df.loc[i, 'appropriateness_'+sector] = result['appropriateness_'+sector]
        except Exception:
            df.loc[i, 'error_gpt'] = chat_completion.choices[0].message.content.replace('```json','').replace('```','')


# 5. output document-level dataset
df = df.loc[:,~df.columns.duplicated()]
df.to_csv(directory+'output/df_aiv.csv', index=False)


# 6. break down into paragraphs
# # sampling
# sample_l = []
# df_sample = df[df['Print ISBN'].apply(lambda x: x not in sample_l)][(df['buff_verified'])&(df['staff_verified'])]
# df_sample = df_sample.reset_index()
#
# texts = list(itertools.chain.from_iterable(df_sample['paragraphs_bu']))
# len_l = list(df_sample['paragraphs_bu'].apply(lambda x: len(x)))
# idx_l = list(itertools.chain.from_iterable([[df_sample.loc[i]['Print ISBN']]*len_l[i] for i in df_sample.index]))
# df_paragraphs = pd.DataFrame([[i] for i in idx_l], columns=['Print ISBN'])
# df_paragraphs['text'] = texts
# df_paragraphs['type'] = 'buff'
#
# texts = list(itertools.chain.from_iterable(df_sample['paragraphs_sa']))
# len_l = list(df_sample['paragraphs_sa'].apply(lambda x: len(x)))
# idx_l = list(itertools.chain.from_iterable([[df_sample.loc[i]['Print ISBN']]*len_l[i] for i in df_sample.index]))
# df_paragraphs1 = pd.DataFrame([[i] for i in idx_l], columns=['Print ISBN'])
# df_paragraphs1['text'] = texts
# df_paragraphs1['type'] = 'staff'
#
# df_paragraphs = pd.concat([df_paragraphs1, df_paragraphs], ignore_index=True)
# df_paragraphs['to_drop'] = df_paragraphs['text'].apply(lambda x: True if x!=x else len(x)<=100)
# df_paragraphs = df_paragraphs[~df_paragraphs['to_drop']]
#
# df_paragraphs = df_paragraphs[~df_paragraphs.duplicated(subset=['Print ISBN', 'text', 'type'])]

# full sample
df = pd.read_csv(directory+'output/df_aiv.csv')

df = df[(df['Full Title']!='')&(~df['Full Title'].isna())]
df = df.reset_index()
for col in ['paragraphs_sa', 'paragraphs_bu', 'paragraphs_sr', 'paragraphs_av']:
    df[col] = df[col].apply(lambda x: ast.literal_eval(x) if x==x and x!='nan' else [])

texts = list(itertools.chain.from_iterable(df['paragraphs_bu']))
len_l = list(df['paragraphs_bu'].apply(lambda x: len(x)))
idx_l = list(itertools.chain.from_iterable([[df.loc[i]['Print ISBN']]*len_l[i] for i in df.index]))
df_paragraphs = pd.DataFrame([[i] for i in idx_l], columns=['Print ISBN'])
df_paragraphs['text'] = texts
df_paragraphs['type'] = 'buff'

texts = list(itertools.chain.from_iterable(df['paragraphs_sa']))
len_l = list(df['paragraphs_sa'].apply(lambda x: len(x)))
idx_l = list(itertools.chain.from_iterable([[df.loc[i]['Print ISBN']]*len_l[i] for i in df.index]))
df_paragraphs1 = pd.DataFrame([[i] for i in idx_l], columns=['Print ISBN'])
df_paragraphs1['text'] = texts
df_paragraphs1['type'] = 'staff'
df_paragraphs = pd.concat([df_paragraphs1, df_paragraphs], ignore_index=True)

texts = list(itertools.chain.from_iterable(df['paragraphs_av']))
len_l = list(df['paragraphs_av'].apply(lambda x: len(x)))
idx_l = list(itertools.chain.from_iterable([[df.loc[i]['Print ISBN']]*len_l[i] for i in df.index]))
df_paragraphs1 = pd.DataFrame([[i] for i in idx_l], columns=['Print ISBN'])
df_paragraphs1['text'] = texts
df_paragraphs1['type'] = 'buff_a'
df_paragraphs = pd.concat([df_paragraphs1, df_paragraphs], ignore_index=True)

texts = list(itertools.chain.from_iterable(df['paragraphs_sr']))
len_l = list(df['paragraphs_sr'].apply(lambda x: len(x)))
idx_l = list(itertools.chain.from_iterable([[df.loc[i]['Print ISBN']]*len_l[i] for i in df.index]))
df_paragraphs1 = pd.DataFrame([[i] for i in idx_l], columns=['Print ISBN'])
df_paragraphs1['text'] = texts
df_paragraphs1['type'] = 'staff_a'
df_paragraphs = pd.concat([df_paragraphs1, df_paragraphs], ignore_index=True)

df_paragraphs = df_paragraphs[~df_paragraphs.duplicated()]
df_paragraphs['to_drop'] = df_paragraphs['text'].apply(lambda x: True if x!=x else len(x)<=100)
# df_paragraphs = df_paragraphs[~df_paragraphs['to_drop']]

df_paragraphs = df_paragraphs.merge(df[['Print ISBN', 'av_uncertain']], how='left')
df_paragraphs.loc[df_paragraphs[df_paragraphs['type'].apply(lambda x: x in ['staff', 'buff'])].index, 'av_uncertain'] = False
df_paragraphs['av_uncertain'] = df_paragraphs['av_uncertain'].fillna(False)


# 7. output paragraph-level dataset
df_paragraphs.to_csv(directory+'output/df_paragraphs.csv', index=False)