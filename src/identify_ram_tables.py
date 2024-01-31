import os,sys # ,getpass
sys.path.insert(0,'../libs')
import PyPDF2
import pandas as pd 
from tqdm import tqdm
import re
from utils_pdf import get_target_pagenum,key_reg_match
from utils import get_all_files

def matching_function(content: str): 
    """
    Finds the starting point of the risk assessment matrix table in the given content.
    The function searches for the presence of 'risk assessment matrix', 'likelihood', 
    and any of 'high', 'medium', or 'low' in the content.

    Args:
    content (str): The text content to search in.

    Returns:
    The result of the regex match if found, otherwise None.
    """
    pattern = re.compile(r'(?=.*risk assessment matrix)(?=.*likelihood)(?=.*(high|medium|low))',re.I)
    res = key_reg_match(content,reg_text = pattern,mode='rgx')
    if res:
        return res
    return None

def get_table_end(filename: str, start_page_num: int, check_page_n: int = 1): 
    """
    Finds the ending page number of the risk assessment matrix table in a PDF file.

    Args:
    filename (str): The path to the PDF file to be searched.
    start_page_num (int): The starting page number from where to begin the search.
    check_page_n (int, optional): The number of pages to check after the starting page. Defaults to 1.

    Returns:
    int: The page number where the table ends, or None if the table does not end in the checked pages.
    """
    pdfFileObj = open(filename,'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    all_res = []
    for pageNum in range(start_page_num+1,start_page_num+check_page_n+1):
            pageObj = pdfReader.pages[pageNum]
            content = pageObj.extract_text().lower().replace('\n','').replace('  ',' ')
            #pattern = re.compile(r'likelihood|policy response',re.I)
            pattern = re.compile(r'(?=.*likelihood)(?=.*risk)',re.I)
            res = key_reg_match(content,reg_text = pattern,mode='rgx')
            if res:
                all_res.append(pageNum)
            else:
                if len(all_res)>0:
                    return all_res[-1]


if __name__ == "__main__":
    
    PDF_folder = '/root/workspace/data/DOCs/pdf_temp'
    res_folder = '/root/workspace/data/ISR_Results'
    all_pdfs = get_all_files(PDF_folder,end_with='.pdf')
    file_names = [os.path.basename(f) for f in all_pdfs]

    ###########################
    ## identify all page number of tables 
    ###########################
    results = []
    for file_path in tqdm(all_pdfs):
        pgn = get_target_pagenum(file_path,match_func=matching_function,return_mode='first')
        end_pgn = get_table_end(file_path,pgn,check_page_n=2)
        if not end_pgn:
            end_pgn = pgn
        results.append((file_path,pgn,end_pgn))
    
    assert len(results) == len(all_pdfs)
    
    ## check ram table numbers 
    pn_df = pd.DataFrame(results)
    pn_df.to_csv(os.path.join(res_folder,'RAM_Tables','ram_table_pn.csv'),index=False)
    print(pn_df[pn_df[1]<20]) ## ram table should at the end, so page number should be relatively large ; otherwise it is a problem 

    ###########################
    ## export ram tables both by country and aggregated 
    ###########################
    pdfWriter = PyPDF2.PdfWriter()
    for filename,start_pgn,end_pgn in results:
        #print(filename,start_pgn,end_pgn)
        file_id = os.path.basename(filename).split('.')[0]
        if start_pgn and end_pgn:
            with open(filename,'rb') as pdfFileObj:
                pdfReader = PyPDF2.PdfReader(pdfFileObj)
                with PyPDF2.PdfWriter() as tempPdfWriter:
                    for extract_pagenum in range(start_pgn,end_pgn+1):
                        pageObj = pdfReader.pages[extract_pagenum]
                        tempPdfWriter.add_page(pageObj)  ## write to country specific file 
                        pdfWriter.add_page(pageObj)      ## write to an aggregated file 
                    ## write to country specific file 
                    temp_out_name = os.path.join(res_folder,'RAM_Tables','by_country',file_id+'.pdf')
                    with  open(temp_out_name, 'wb') as pdfOutput:
                        tempPdfWriter.write(pdfOutput)
    ## write to an aggregated file                     
    out_name = os.path.join(res_folder,'RAM_Tables','RAM_tables_large_v2.pdf')
    with open(out_name, 'wb') as pdfOutput:
        pdfWriter.write(pdfOutput)

    print('Finished, results in {}'.format(os.path.join(res_folder,'RAM_Tables')))






