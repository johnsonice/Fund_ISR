from google import genai
from google.genai import types
import os,re,pathlib,httpx,sys
import pandas as pd
from io import StringIO
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InternalServerError
import json
from tqdm import tqdm
sys.path.insert(0, '../')
from prompts import extract_ram2csv,extract_ram2md
from dotenv import load_dotenv
load_dotenv(dotenv_path='../../.env')  # Load environment variables from .env file in parent directory
#from utils import load_json, logging, exception_handler
import logging 
import datetime 
now = datetime.datetime.now()
name = os.getlogin()
USER = name.upper()
file_path = f"log/{USER}/{datetime.date.today()}"
os.makedirs(file_path,exist_ok=True)
filename = f"{file_path}/Exp-{now.hour}:{now.minute}.log"
fmt = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    filename=filename,
    filemode="w",
    format=fmt
    )
#%%
def clean_markdown_fence(text):
    """
    Removes Markdown code fences like ```csv ... ``` and returns only the inner content.
    Handles cases with or without newlines, with or without language tags.
    """
    # Match fenced code block with or without language tag
    match = re.search(r"```(?:\w+)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def extract_csv_content(text):
    """
    Extracts CSV content from a Markdown fenced code block.
    Handles cases with or without newlines, with or without language tags.
    Args:
        text (str): The input text containing Markdown fenced code blocks.
    Returns:
        str: The extracted CSV content without the code fence.
    """
    # Match fenced code block with 'csv' language tag
    match = re.search(r"```csv(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def clean_RAM(ram):

    letter_pattern = r'[a-zA-Z]'
    keyword_pattern = r'(risk|assessment|matrix|ram)'
    # likelihood_impact_keywords = ['high', 'medium', 'low', 'moderate', 'severe']

    # Remove rows where 'Risk' column contain no letters
    cleaned_df = ram[
        ram['Risk'].str.contains(letter_pattern, na=False)
    ]

    # # Remove rows where 'Heading' does not contain RAM keywords if 'Heading' is not missing
    # cleaned_df = cleaned_df[
    #     cleaned_df['Heading'].isna() | 
    #     (cleaned_df['Heading'].str.count(keyword_pattern, flags=re.IGNORECASE) >=2)
    # ]

    # # Remove rows where 'Likelihood' or 'Impact' columns do not contain keywords from high, medium, low
    # cleaned_df = cleaned_df[
    #     cleaned_df['Likelihood'].str.contains('|'.join(likelihood_impact_keywords), case=False, na=False) |
    #     cleaned_df['Impact'].str.contains('|'.join(likelihood_impact_keywords), case=False, na=False)
    # ]

    # Keep only the specified columns
    cleaned_df = cleaned_df[['Heading', 'Risk Type','Risk', 'Time Horizon','Likelihood', 'Likelihood Full', 'Impact', 'Impact Full','Policy Response']]

    logging.info(f"Rows before cleaning: {len(ram)}")
    logging.info(f"Rows after cleaning: {len(cleaned_df)}")

    return cleaned_df

def log_retry_error(retry_state):
    """
    Callback function for tenacity's retry decorator to log retry attempts.
    Logs the file being processed, attempt number, and the exception that caused the retry.
    """
    # retry_state.args[1] is the 'filepath' argument from the 'extract_ram' method.
    filepath = retry_state.args[1]
    logging.warning(
        f"Error processing {filepath.name}, retrying (attempt {retry_state.attempt_number}). "
        f"Exception: {retry_state.outcome.exception()}"
    )

class RAM_Processor():
    """
    A class to process RAM data using Google GenAI.
    """
    def __init__(self, generation_config,api_key=None):
        self.generation_config = generation_config
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    @retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60), # Waits 2s, 4s, 8s ... up to 60s between retries
    retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable, InternalServerError)),
    reraise=True, # Reraise the last exception if all retries fail
    before_sleep=log_retry_error # This will log the error before each retry.
    )
    def extract_ram(self, filepath,PROMPT,model_name="gemini-2.5-pro-preview-05-06"):
        response = self.client.models.generate_content(
                model=model_name,
                config=generation_config,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type='application/pdf',
                    ),
                PROMPT])
        return response.text

#%%
# Run the script
if __name__ == "__main__":

    Extract_type = 'csv'  # or 'md' for markdown extraction
    # define output folder 
    output_folder = pathlib.Path('/ephemeral/home/xiong/data/Fund/RAM_Table/RAM_Table_Examples_Outputs_v2')
    raw_output_folder = output_folder / 'raw'
    clean_output_folder = output_folder / 'clean'
    output_folder.mkdir(exist_ok=True, parents=True)
    raw_output_folder.mkdir(exist_ok=True, parents=True)
    clean_output_folder.mkdir(exist_ok=True, parents=True)
    
    # get file pathes,only ones that are not already processed:
    pdf_folder = pathlib.Path('/ephemeral/home/xiong/data/Fund/RAM_Table/RAM_Table_Examples_v2')
    pdf_files = [f for f in pdf_folder.glob("*.pdf") if f.is_file()]
    processed_files = {f.stem for f in clean_output_folder.glob("*")}
    pdf_files = [f for f in pdf_files if f.stem not in processed_files]

    logging.info(f"Found {len(pdf_files)} new files to process")
    # GenAI configuration
    generation_config = {
        "temperature": 0.01,
        "top_p": 0.9, 
        "top_k": 40,
        "max_output_tokens": 120000, # put it as 8k
        #"response_mime_type": "application/json",
        }
    
    # Initialize the RAM processor
    ram_processor = RAM_Processor(generation_config=generation_config,api_key=os.getenv("GEMINI_API_KEY"))

    # Define the prompt for extraction
    if Extract_type == 'md':
        RAM_PROMPT = extract_ram2md
    elif Extract_type == 'csv':
        RAM_PROMPT = extract_ram2csv
    
    # Initialize error tracking lists
    llm_errors = []  # Track files that failed during LLM processing
    cleaning_errors = []  # Track files that failed during cleaning step
    
    # Process each PDF file with tqdm
    for pdf_file in tqdm(pdf_files, desc="Processing PDF files"):
        try:
            logging.info(f"Processing: {pdf_file.name}")
            # Extract RAM data
            raw_result = ram_processor.extract_ram(pdf_file, RAM_PROMPT)
            output_file = raw_output_folder / f"{pdf_file.stem}.{Extract_type}" # save the raw result
            open(output_file, 'w', encoding='utf-8').write(raw_result)
            logging.info(f"Saved raw result to {output_file}")
        except Exception as e:
            logging.error(f"Error processing {pdf_file.name}: {str(e)}")
            llm_errors.append((pdf_file.name, str(e)))  # Track LLM processing errors
            continue  # Skip to next file if LLM processing fails
            
        ## clean the raw result:
        if Extract_type == 'csv':
            try:
                response_data = pd.read_csv(StringIO(extract_csv_content(raw_result)))
                clean_result = clean_RAM(response_data)
                clean_output_file = clean_output_folder / f"{pdf_file.stem}.csv"
                if clean_result.empty:
                    raise ValueError(f"No valid rows found in {pdf_file.name}")
                clean_result.to_csv(clean_output_file, index=False)
                logging.info(f"Saved clean result to {clean_output_file}")
            except Exception as e:
                logging.error(f"Error cleaning {pdf_file.name}: {str(e)}")
                cleaning_errors.append((pdf_file.name, str(e)))  # Track cleaning errors
    
    # Convert error lists to DataFrames and export to CSV
    if llm_errors:
        # Create DataFrame for LLM errors
        llm_df = pd.DataFrame(llm_errors, columns=['file_name', 'error_message'])
        llm_error_output =  output_folder / 'llm_processing_errors.csv'
        llm_df.to_csv(llm_error_output, index=False)
        logging.info(f"Saved LLM processing errors to {llm_error_output}")
            
    if cleaning_errors:
        # Create DataFrame for cleaning errors
        cleaning_df = pd.DataFrame(cleaning_errors, columns=['file_name', 'error_message'])
        cleaning_error_output = output_folder / 'cleaning_errors.csv'
        cleaning_df.to_csv(cleaning_error_output, index=False)
        logging.info(f"Saved cleaning errors to {cleaning_error_output}")
    
    # Print summary of errors
    total_llm_errors = len(llm_errors)
    total_cleaning_errors = len(cleaning_errors)
    
    print(f"Processing complete. Found {total_llm_errors} LLM processing errors and {total_cleaning_errors} cleaning errors.")
    