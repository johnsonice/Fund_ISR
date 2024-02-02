### Process Ram Tables 

#%%
from docx import Document
import pandas as pd
import os,sys # ,getpass
sys.path.insert(0,'../libs')
from utils import get_all_files,load_json,parse_list_string
from utils_pdf import key_reg_match, Word_Table_Identifier
from util_prompts import format_ram_table
from oai_ast_utils import OpenAIAssistant_Base
import re, tqdm,time,json

key = load_json('/root/workspace/key/openai_key.json') 
os.environ['OPENAI_API_KEY'] = key['ISR']['API_KEY']
#%%
class Base_Formator(OpenAIAssistant_Base):
    def __init__(self):
        super().__init__()
        
    def delete_all_files(self,verbose=True):
        filter_criteria={} #USA_2022.pdf
        sampled_file_ids = self.FileManager.get_files_info_by(filter_criteria,return_fields=['id'],to_dict=True,to_single_list=True)
        self.FileManager.delete_files_by_ids(file_ids=sampled_file_ids)
        if verbose:
            print('files deleted {}'.format(sampled_file_ids))
        return sampled_file_ids
    
    def get_missing_files(self,file_names):
        """Check see if all need files are already uploaded"""
        server_file_info = self.FileManager.get_files_info_by(filter_criteria={'filename':file_names},return_fields=['filename'])
        missing_files = []
        for fn in file_names:
            if fn not in server_file_info:
                missing_files.append(fn)
        return missing_files
    
    def load_assistant_by_name(self,assistant_name,verbose=True):
        filter_criteria={'name':[assistant_name]}
        as_id = self.get_assistants_info_by(filter_criteria,return_fields=['id'])
        ## retrieve by id 
        assit = self.get_assistants_by_ids(as_id[0])
        if verbose:
            print(assit.name, assit.id )
        ## set the retrieved assistant as current active assistant 
        self._set_active_assistant(assit)
        
        return assit.id
    
    def run_a_task(self,loop_files,user_prompt,model_name='gpt-4-1106-preview'):
        results = {}
        for f_dict in tqdm.tqdm(loop_files):
            ## update assistant file with specific country file 
            fid,fname = f_dict.get('id'),f_dict.get('filename')
            ass_info_dict = {
                        'model':model_name,
                        'file_ids':[fid] 
                        }
            self.update_current_assistant(**ass_info_dict)
            
            user_input_dict = {"role":"user",
                            "content":user_prompt
                            }
            msg,status = self.quick_query(user_input_dict)
            results[fname]={'msg':msg,'status':status}
            time.sleep(2)
        
        return results

def _string_to_dict(input_str):
    # Split the string into sections
    sections = [s.strip() for s in input_str.split("||")]
    # Create a dictionary to store the results
    result_dict = {}
    # Process each section
    for section in sections:
        # Split each section into key and value
        if ":" in section:
            key, value = section.split(":", 1)
            result_dict[key.strip()] = value.strip()
    return result_dict

def msg2df(raw_msg):
    list_str = parse_list_string(raw_msg)
    list_dict = [_string_to_dict(m) for m in list_str]
    df = pd.DataFrame(list_dict)
    return df

#%%

if __name__ == "__main__":
    
    ###
    data_folder = '/root/workspace/data/DOCs'
    ram_folder = os.path.join(data_folder,'RAM')
    word_folder = os.path.join(ram_folder,'Word')
    pdf_folder = os.path.join(ram_folder,'PDF')
    out_path = os.path.join(ram_folder,'RAM_table_status.csv')
    ram_csv_out_folder = os.path.join(ram_folder,'CSV')
    #%%
    ##############
    # identify ram table normal or not 
    ##############
    file_paths = get_all_files(word_folder,end_with='.docx')
    file_names = [os.path.basename(f) for f in file_paths]
    R = Word_Table_Identifier()
    res = [[fp,R.identify_non_standard_tables(doc_path = fp, verbose=True)] for fp in file_paths]
    res_df = pd.DataFrame(res,columns=['file_path','standard_table'])
    print(res_df['standard_table'].value_counts(normalize=True) * 100)
    res_df.to_csv(out_path)     
    print('export status to {}'.format(out_path))

    #%%

    ##############
    # process standard ram table 
    ##############
    standard_files = res_df['file_path'][res_df['standard_table'] == True].tolist()
    for f in standard_files:
        raw_data = []
        R.load_doc(f)
        for t in R.tables:
            raw_data.extend(R.basic_table_extract(t))
        df = pd.DataFrame(raw_data)
        df = df.iloc[1:]
        f_id = os.path.basename(f).split('.')[0]
        df.to_csv(os.path.join(ram_csv_out_folder,'{}.csv'.format(f_id)))
    #%%
    
    ##############
    # process non standard ram table 
    ##############
    res_df = pd.read_csv(out_path)
    non_standard_files = res_df['file_path'][res_df['standard_table'] == False].tolist()
    non_standard_names = [os.path.basename(f).replace('.docx','.pdf') for f in non_standard_files]

    ## get files to upload 
    R =Base_Formator()
    up_files_names = R.get_missing_files(non_standard_names)
    fp = [os.path.join(pdf_folder,f) for f in up_files_names]
    fp = [f for f in fp if os.path.exists(f)]
    # upload files 
    if len(fp)>0:
        server_file_info = [R.FileManager.upload_file(f,purpose='assistants') for f in fp]
    #%%
    ## get all file ids that we need to go through 
    loop_files = R.FileManager.get_files_info_by(filter_criteria={'filename':non_standard_names},
                                                 return_fields=['id','filename'],to_dict=True)
    print(loop_files)
    #%%
    ## reload assistant ; sometime there are bugs if keep reusing the same assistant
    R.load_assistant_by_name('PDF_Table_Extractor')
    user_prompt = format_ram_table
    res_dict = R.run_a_task(loop_files,user_prompt,model_name='gpt-4-1106-preview')
    ## export to json
    with open(os.path.join(ram_folder,'raw_table_extraction_msg.json'), 'w') as file:
        json.dump(res_dict, file, indent=4)
    ## export to csv
    for k,v in res_dict.items():
        f_id = k.replace('.pdf','')
        df = msg2df(v['msg'])
        df.to_csv(os.path.join(ram_folder,'CSV','OAI_{}.csv'.format(f_id)))







# %%
