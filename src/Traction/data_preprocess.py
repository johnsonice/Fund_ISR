
# this file is used to extract staff appraisal and buff statement from raw xml files
# and convert all dicts to df for later use
# and create a paragraph level df for topic identification

# extract_StaffAppraisal_and_Buff function is way to complicated; need to be optimized at latter stage
# Need to be considered to either
# 1. rewrite the function in a more efficient and modular way for later use;


#%%
import pandas as pd
import os
import re
import string
import itertools
import bs4 as bs
import numpy as np
import json
import ast
from functools import reduce
from pathlib import Path
from bs4 import BeautifulSoup
from itertools import chain
from tqdm import tqdm
import config
## temporary fix for bs4 warning
from bs4 import XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
#%%

def get_folder_dict(raw_xml_dir):
    """ 
    # - get a filtered version of article iv xml files 
    # unite if analysis is a folder; each folder can contarins several xml files 
    """

    folder_dict = {}
    for root, dirs, files in os.walk(raw_xml_dir/'results_v2', topdown=False):
        for name in dirs:
            if 'spr_isr' not in name:
                folder_dict[name] = os.path.join(root, name)
    for root, dirs, files in os.walk(raw_xml_dir/'results_v5', topdown=False):
        for name in dirs:
            if 'spr_isr' not in name:
                folder_dict[name] = os.path.join(root, name)
    # print(len(folder_dict))
    # folder_dict['9781475514797']
    return folder_dict


def extract_StaffAppraisal_and_Buff(folder_dict):
    """
    this function is used to extract staff appraisal and buff statement from xml files
    return a dictionary of staff appraisal and buff statement
    
    this fucntion is way to complicated; need to be optimized at latter stage 
    """
    staff_dict = {}
    staff_content_dict = {}
    text_sa_dict = {}
    para_sa_dict = {}
    buff_dict = {}
    buff_content_dict = {}
    para_bu_dict = {}
    # Additional content extracted in one pass
    para_sr_dict = {}
    para_av_dict = {}
    av_uncertain_dict = {}

    for folder in tqdm(folder_dict, desc="Extracting staff appraisal and buff statement"):
        if folder not in staff_dict:
            for root, dirs, files in os.walk(folder_dict[folder]):
                for i in range(len(files)):
                    if 'A00' in sorted(files)[i] and folder not in staff_dict:
                        #temp = _safe_read(os.path.join(root, sorted(files)[i]), encoding='utf-8')
                        temp = open(os.path.join(root, sorted(files)[i]), 'r', encoding='utf-8').read()
                        soup = bs.BeautifulSoup(temp, 'lxml')
                        sec_l = soup.find_all('sec')
                        sec = [sec for sec in sec_l if 'staff appraisal' in sec.find('title').text.lower() or 'staff apraisal' in sec.find('title').text.lower()]
                        if len(sec)>0:
                            sec = sec[0] # get first section under "staff appraisal" or "staff apraisal"
                            for s in sec.select('fig'):
                                s.extract()
                            for s in sec.select('table-wrap'):
                                s.extract()
                            end = str([l for l in sec.find_all('p') if len(l.text.strip())>0 and l.text.strip()[0].isdigit()][-1])
                            sec = bs.BeautifulSoup(str(sec)[:str(sec).find(end)+len(end)], 'lxml')
                            staff_dict[folder] = os.path.join(root, sorted(files)[i])
                            staff_content_dict[folder] = temp
                            text_sa_dict[folder] = str(sec)
                            para_sa_dict[folder] = [l.text for l in sec.find_all('p')]+[p for p in list(itertools.chain.from_iterable([l.text.split('\n') for l in sec.find_all('list')])) if p.strip()!='']
                                
                            # Also extract Staff Report paragraphs (non staff appraisal) and Authorities' Views in the same pass
                            try:
                                # remove non-narrative elements
                                soup = bs.BeautifulSoup(temp, 'lxml')
                                for s in soup.select('fig'):
                                    s.extract()
                                for s in soup.select('table-wrap'):
                                    s.extract()
                                for s in soup.select('boxed-text'):
                                    s.extract()

                                sec_l_all = soup.find_all('sec')
                                try:
                                    start_idx = [idx for idx in range(len(sec_l_all)) if sec_l_all[idx].find('title').text.lower()=='contents'][0] + 1
                                except Exception:
                                    start_idx = 0
                                end_idx = [idx for idx in range(len(sec_l_all)) if ('staff appraisal' in sec_l_all[idx].find('title').text.lower()) or ('staff apraisal' in sec_l_all[idx].find('title').text.lower())][0]
                                sec_l_range = sec_l_all[start_idx:end_idx]

                                text_sections = []
                                for sec_node in sec_l_range:
                                    if len(sec_node.find_all('sec'))==0 and sec_node not in text_sections:
                                        text_sections.append(sec_node)
                                    else:
                                        text_sections += [s for s in sec_node.find_all('sec') if s not in text_sections]
                                        for s in sec_node.find_all('sec'):
                                            s.extract()
                                        if sec_node.text.strip() != '' and sec_node not in text_sections:
                                            text_sections.append(sec_node)

                                # Rule detection
                                if len([sec_node for sec_node in text_sections if sec_node.find('title') is not None and 'authorit' in sec_node.find('title').text.lower()]) > 0:
                                    rule_type = 0
                                elif len([p for sec_node in text_sections for p in sec_node.find_all('p') if p.find('bold') is not None and p.find('bold').text.lower().startswith('authorit') and p.text.lower().replace('’','').replace("'",'').strip() not in ["authorities views", "authorities view"]]) > 0:
                                    rule_type = 1
                                elif len([p for sec_node in text_sections for p in sec_node.find_all('p') if p.find('bold') is not None and p.text.lower().replace('’','').replace("'",'').strip() in ["authorities views", "authorities view"]]) > 0:
                                    rule_type = 3
                                else:
                                    rule_type = 2

                                staff_l = []
                                authority_l = []
                                if rule_type == 0:
                                    for sec_node in text_sections:
                                        if sec_node.find('title') is not None and 'authorit' in sec_node.find('title').text.lower():
                                            authority_l += sec_node.find_all('p')
                                        else:
                                            staff_l += sec_node.find_all('p')
                                elif rule_type == 1:
                                    for sec_node in text_sections:
                                        p_l = sec_node.find_all('p')
                                        if len(p_l) > 0:
                                            for p in p_l:
                                                if p.find('bold') is not None and p.find('bold').text.lower().startswith('authorit'):
                                                    authority_l.append(p)
                                                else:
                                                    staff_l.append(p)
                                elif rule_type == 3:
                                    for sec_node in text_sections:
                                        p_l = sec_node.find_all('p')
                                        if len(p_l) > 0:
                                            for idx_p in range(len(p_l)):
                                                p = p_l[idx_p]
                                                if p.find('bold') is not None and p.text.lower().replace('’','').replace("'",'').strip() in ["authorities views", "authorities view"]:
                                                    if idx_p + 1 < len(p_l):
                                                        authority_l.append(p_l[idx_p+1])
                                                elif p not in authority_l:
                                                    staff_l.append(p)
                                else:
                                    for sec_node in text_sections:
                                        p_l = sec_node.find_all('p')
                                        if len(p_l) > 0:
                                            staff_l += p_l[:-1]
                                            if p_l[-1].find('bold') is not None and 'authorit' in p_l[-1].find('bold').text.lower():
                                                authority_l.append(p_l[-1])
                                            else:
                                                staff_l.append(p_l[-1])

                                para_sr_dict[folder] = [p.text for p in staff_l]
                                para_av_dict[folder] = [p.text for p in authority_l]
                                if rule_type == 2:
                                    av_uncertain_dict[folder] = True
                                else:
                                    av_uncertain_dict[folder] = False
                            except Exception:
                                # Fail safe: do not block extraction if additional content parsing fails
                                para_sr_dict[folder] = []
                                para_av_dict[folder] = []
                                av_uncertain_dict[folder] = True
                            
                # Extract buff statement
                for i in range(len(files)-1, 0, -1):
                    if i == len([f for f in files if 'A00' in f])-1 or i == len([f for f in files if 'A00' in f]) and folder not in buff_dict and not (folder in staff_dict and staff_dict[folder]==os.path.join(root, sorted(files)[i])):
                        #temp = _safe_read(os.path.join(root, sorted(files)[i]), encoding='utf-8')
                        temp = open(os.path.join(root, sorted(files)[i]), 'r', encoding='utf-8').read()
                        soup = bs.BeautifulSoup(temp, 'lxml')
                        for s in soup.select('abstract'):
                            s.extract()
                        if len([a for a in soup.find('body').find_all('article-title') if 'statement by' in a.text.lower() or 'statement on' in a.text.lower()])>0:
                            buff_dict[folder] = os.path.join(root, sorted(files)[i])
                            buff_content_dict[folder] = temp
                            para_bu_dict[folder] = [l.text for l in soup.find('body').find_all('p') if l.text.strip()!='']
                        elif len([p for p in soup.find_all('p') if p.text.lower().strip().startswith('statement by')])>0:
                            buff_dict[folder] = os.path.join(root, sorted(files)[i])
                            buff_content_dict[folder] = temp
                            para_bu_dict[folder] = [l.text for l in [p for p in soup.find_all('p') if p.text.lower().strip().startswith('statement by')][0].find_all_next('p') if l.text.strip()!='']
                            
    return (staff_dict, staff_content_dict, text_sa_dict, para_sa_dict,
            buff_dict, buff_content_dict, para_bu_dict,
            para_sr_dict, para_av_dict, av_uncertain_dict)

def convert_to_df(df_meta,
                  staff_dict, staff_content_dict,
                  text_sa_dict, para_sa_dict,
                  buff_dict, buff_content_dict, para_bu_dict,
                  para_sr_dict, para_av_dict, av_uncertain_dict):
    """
    this function is used to convert the dictionary to a dataframe
    return a dataframe
    """
    df = pd.DataFrame([
        staff_dict,
        staff_content_dict,
        buff_dict,
        buff_content_dict,
        text_sa_dict,
        para_sa_dict,
        para_bu_dict,
        para_sr_dict,
        para_av_dict,
        av_uncertain_dict
    ]).T
    df = df.reset_index()
    df = df[df['index'].apply(lambda x: not x.startswith('spr_'))]
    df = df.rename(columns={'index':'Print ISBN', 0:'filename_staff', 1: 'text_staff', 
                            2: 'filename_buff', 3: 'text_buff', 4: 'text_sa', 
                            5: 'paragraphs_sa', 6: 'paragraphs_bu',
                            7: 'paragraphs_sr', 8: 'paragraphs_av', 9: 'av_uncertain'})

    df['buff_verified'] = df['paragraphs_bu'].apply(lambda x: x==x and len(x)>0)
    df['staff_verified'] = df['paragraphs_sa'].apply(lambda x: x==x and len(x)>0)

    df_meta['Print ISBN'] = df_meta['Print ISBN'].apply(lambda x: str(x))
    df = df.merge(df_meta[['Print ISBN', 'Extract text after ":"', 'Full Title', 
                           'Subtitle', 'Title', 'Primary Country Code', 
                           'Year from title', 'Publication Date']], 
                            on='Print ISBN', how='left')
    for t in ['Extract text after ":"', 'Full Title', 'Subtitle']:
        df[t] = df[t].fillna('')
    df['title_all'] = df.apply(lambda x: ', '.join([x['Extract text after ":"'], x['Full Title'], x['Subtitle']]), axis=1)
    df.loc[df[df['title_all'].apply(lambda x: x==x and 'statement by' in x.lower())].index, 'has_buff'] = 1
    df.loc[df[(df['has_buff']!=1)&(df['buff_verified']==1)&(df['paragraphs_bu'].apply(lambda x: 'does not alter' in ' '.join(x).lower() or 'does not change' in ' '.join(x).lower() if x==x else False))].index, 'paragraphs_bu'] = np.nan
    df['buff_verified'] = df['paragraphs_bu'].apply(lambda x: x==x and len(x)>0)

    df.loc[df[df['Print ISBN']=='9781484334850'].index, 'Year from title'] = 2017
    df.loc[df[df['Print ISBN']=='9781475564082'].index, 'Year from title'] = 2016
    df.loc[df[df['Print ISBN']=='9781484334980'].index, 'Year from title'] = 2017
    df.loc[df[df['Print ISBN']=='9781616356767'].index, 'Year from title'] = 2021

    df.drop('title_all', axis=1, inplace=True)
    return df

def doc_to_paragraphs(df_doc):
    """
    this function is used to convert the dataframe to a paragraph dataframe
    return a paragraph dataframe
    """
    df_doc = df_doc[(df_doc['Full Title']!='')&(~df_doc['Full Title'].isna())]
    df_doc = df_doc.reset_index()
    
    # mapping of source columns to 'type' labels
    col_map = {
        'paragraphs_bu': 'buff',
        'paragraphs_sa': 'staff',
        'paragraphs_av': 'buff_a',
        'paragraphs_sr': 'staff_a',
    }
    for col in col_map.keys():
        df_doc[col] = df_doc[col].apply(lambda x: ast.literal_eval(x) if x==x and x!='nan' else [])
        
    # --- build the paragraph DataFrame, exapnd  ---
    paragraph_frames = []
    for col, typ in col_map.items():
        temp = (
            df_doc[['Print ISBN', col, 'av_uncertain']]
            .explode(col, ignore_index=True)
            .rename(columns={col: 'text'})
        )
        temp['type'] = typ
        paragraph_frames.append(temp)

    # combine all types
    df_paragraphs = pd.concat(paragraph_frames, ignore_index=True)
    # --- drop NaN or short paragraphs ---
    df_paragraphs = df_paragraphs.dropna(subset=['text'])
    df_paragraphs['to_drop'] = df_paragraphs['text'].str.len().le(100)
    # if you want to actually remove them:
    # df_paragraphs = df_paragraphs.loc[~df_paragraphs['to_drop']]
    # --- deduplicate ---
    df_paragraphs = df_paragraphs.drop_duplicates(subset=['Print ISBN', 'text', 'type'])
    # --- fix av_uncertain for non-_a types ---
    df_paragraphs.loc[df_paragraphs['type'].isin(['staff', 'buff']), 'av_uncertain'] = False
    df_paragraphs['av_uncertain'] = df_paragraphs['av_uncertain'].fillna(False)
    
    return df_paragraphs
    #%%
if __name__ == "__main__":
    ## set path 
    # raw_xml_dir = config.raw_xml_dir
    raw_xml_dir = Path('/data/home/xiong/data/Fund/CSR/Tractions/ArticleIV_xml_updated')
    # data_dir = config.data_dir
    data_dir = Path('/data/home/xiong/data/Fund/CSR/Tractions/')
    folder_dict = get_folder_dict(raw_xml_dir)
    output_dir = data_dir / 'output'
    meta_df = pd.read_excel(data_dir / 'text_collection' / 'IMF_Main_MetaData_20240710_toRan_filtered.xlsx')
    #%%
    ## extract staff appraisal and buff statement from raw xml files 
    (staff_dict, staff_content_dict, 
     text_sa_dict, para_sa_dict, 
     buff_dict, buff_content_dict, 
     para_bu_dict,para_sr_dict, 
     para_av_dict, av_uncertain_dict) = extract_StaffAppraisal_and_Buff(folder_dict)
    #%%
    ## convert all dicts to df for later use
    df = convert_to_df(meta_df, 
                       staff_dict, staff_content_dict, 
                       text_sa_dict, para_sa_dict, 
                       buff_dict, buff_content_dict, para_bu_dict,
                       para_sr_dict, para_av_dict, av_uncertain_dict)
    print('staff_verified:', len(df[df['staff_verified']]), 
          'total:', len(df), 
          'buff_verified:', len(df[df['buff_verified']]), 
          'has_buff:', len(df[df['has_buff']==1]))
    
    df.to_csv(output_dir / 'df_aiv.csv', index=False)
    print('export doc level df to :{}'.format(output_dir / 'df_aiv.csv'))
    #%%
    ## load data back to work; and create a paragraph level df for topic identification
    df_doc = pd.read_csv(output_dir / 'df_aiv.csv')
    df_paragraphs = doc_to_paragraphs(df_doc)
    df_paragraphs.to_csv(output_dir / 'df_paragraphs.csv', index=False)
    print('export paragraph level df to :{}'.format(output_dir / 'df_paragraphs.csv'))

