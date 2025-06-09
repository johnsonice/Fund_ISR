#%%
import os,sys # ,getpass
sys.path.insert(0,'../../libs')
import PyPDF2
import pandas as pd 
from tqdm import tqdm
import re,pathlib
from joblib import Parallel, delayed
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

def get_table_end(filename: str, start_page_num: int, check_page_n: int = 4,offset=None): 
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
    num_pages = len(pdfReader.pages)
    if offset:
        end_page_n = min(start_page_num + offset,num_pages-1)
        return end_page_n

    all_res = []
    for pageNum in range(start_page_num+1,min(start_page_num+check_page_n+1,num_pages)):
            pageObj = pdfReader.pages[pageNum]
            content = pageObj.extract_text().lower().replace('\n','').replace('  ',' ')
            # pattern = re.compile(r'(?=.*likelihood)(?=.*risk)',re.I)
            pattern = re.compile(r'likelihood|risk|policy|response|domestic|global|conjunctural|external|high|medium|low|moderate|severe', re.I)
            res = key_reg_match(content,reg_text = pattern,mode='rgx')
            if res:
                all_res.append(pageNum)
            else:
                if len(all_res)>0:
                    return all_res[-1] + offset
                
def process_pdf(file_path, match_func):
    """
    Processes a single PDF file to find the start and end page numbers of a table.

    Args:
    file_path (str): The path to the PDF file.
    match_func (function): The function to identify the start of the table.

    Returns:
    tuple: A tuple containing the file path, start page number, and end page number.
    """
    pgn = get_target_pagenum(file_path, match_func=match_func, return_mode='first')
    if pgn is None:
        return (file_path, None, None)
    end_pgn = get_table_end(file_path, pgn, check_page_n=4,offset=4)
    if not end_pgn:
        end_pgn = pgn
    return (file_path, pgn, end_pgn)

def filter_pdfs_by_year(pdf_paths: list, start_year: int = None, end_year: int = None) -> list:
    """
    Filter PDF paths based on year range extracted from filenames.
    Returns:
        list: Filtered list of PDF paths that fall within the year range
    """
    filtered_paths = []
    for path in pdf_paths:
        # Extract year from filename using regex
        # Assumes filename format contains year like: "123_2022_0.pdf"
        year_match = re.search(r'_(\d{4})_', os.path.basename(path))
        if year_match:
            year = int(year_match.group(1))
            # Apply year range filters if specified
            if start_year and year < start_year:
                continue
            if end_year and year > end_year:
                continue
            filtered_paths.append(path)
            
    return filtered_paths

def export_ram_table(result_tuple, res_folder):
    """
    Exports RAM table pages from a single PDF to a new file.

    Args:
        result_tuple (tuple): A tuple containing (filename, start_pgn, end_pgn).
        res_folder (pathlib.Path): The folder to save the exported PDF.

    Returns:
        str: The path to the created PDF file, or None if no table was found or an error occurred.
    """
    filename, start_pgn, end_pgn = result_tuple
    if start_pgn and end_pgn:
        file_id = os.path.basename(filename).split('.')[0]
        temp_out_name = os.path.join(res_folder, file_id + '.pdf')
        
        # Use a new PdfWriter for each file to ensure thread safety
        tempPdfWriter = PyPDF2.PdfWriter()
        
        with open(filename, 'rb') as pdfFileObj:
            pdfReader = PyPDF2.PdfReader(pdfFileObj)
            for extract_pagenum in range(start_pgn, end_pgn + 1):
                pageObj = pdfReader.pages[extract_pagenum]
                tempPdfWriter.add_page(pageObj)
        
        with open(temp_out_name, 'wb') as pdfOutput:
            tempPdfWriter.write(pdfOutput)
            
        return temp_out_name
    return None
#%%

if __name__ == "__main__":
    
    # PDF_folder = '/root/workspace/data/DOCs/pdf_temp'
    # res_folder = '/root/workspace/data/ISR_Results'
    PDF_folder = pathlib.Path('/ephemeral/home/xiong/data/Fund/pdf_parse/Fund_Document/input/All_AIV_2008-2025_PDF')
    res_folder = pathlib.Path('/ephemeral/home/xiong/data/Fund/RAM_Table/RAM_Table_Examples_v2')
    res_folder.mkdir(exist_ok=True,parents=True)
    pn_csv_path = os.path.join(res_folder,'..','ram_table_pn_v2.csv')
    agg_pdf_out_path = os.path.join(res_folder,'..','RAM_tables_agg_v2.pdf')
    
    all_pdfs = get_all_files(PDF_folder,end_with='.pdf')
    all_pdfs = filter_pdfs_by_year(all_pdfs,start_year=2022,end_year=2025)
    file_names = [os.path.basename(f) for f in all_pdfs]
    
    n_workers = -4
#%%
    ###########################
    ## identify all page number of tables 
    ###########################
    print(f"Processing {len(all_pdfs)} files with {n_workers} workers")
    results = Parallel(n_jobs=n_workers,verbose=10)(delayed(process_pdf)(file_path, matching_function) for file_path in all_pdfs)
    assert len(results) == len(all_pdfs)
    
    ## check ram table numbers 
    pn_df = pd.DataFrame(results)
    pn_df.to_csv(pn_csv_path,index=False)
    # Calculate summary statistics for RAM table identification
    total_files = len(pn_df)
    files_with_tables = pn_df[1].notna().sum()
    files_without_tables = pn_df[1].isna().sum()
    
    print("\nRAM Table Identification Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Files with RAM tables: {files_with_tables} ({files_with_tables/total_files*100:.1f}%)")
    print(f"Files without RAM tables: {files_without_tables} ({files_without_tables/total_files*100:.1f}%)")
    # Check for potential issues (tables found in first 20 pages)
    early_tables = pn_df[pn_df[1] < 20]
    if not early_tables.empty:
        print(f"\nWarning: Found {len(early_tables)} potential false positives (tables in first 20 pages)")
    #%%
    ###########################
    ## export ram tables both by country and aggregated 
    ###########################
    # Filter out results where no table was found
    valid_results = [r for r in results if r[1] is not None]

    print(f"\nExporting {len(valid_results)} RAM tables to individual files...")
    # Use joblib to export country-specific PDFs in parallel
    exported_files = Parallel(n_jobs=n_workers,verbose=10)(
        delayed(export_ram_table)(result, res_folder) for result in valid_results
    )
    # Filter out None values in case of errors
    exported_files = [f for f in exported_files if f is not None]
    print(f"Aggregating {len(exported_files)} tables into a single PDF...")
    # Aggregate all exported tables into a single PDF
    pdfWriter = PyPDF2.PdfWriter()
    for temp_pdf_path in exported_files:
        pdfWriter.append(temp_pdf_path)

    ## write to an aggregated file                     
    with open(agg_pdf_out_path, 'wb') as pdfOutput:
        pdfWriter.write(pdfOutput)

    print('Finished, results in {}'.format(os.path.join(res_folder,'..')))

# %%

