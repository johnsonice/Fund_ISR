### LLM utils 

#%%
import tiktoken
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
import os, json, re
import openai
try:
    from openai import OpenAI
except:
    print('...currently using old version of openai')
import os
from utils import load_json,logging,exception_handler
import json
from huggingface_hub import hf_hub_download
from huggingface_hub import snapshot_download

def donload_hf_model(REPO_ID,save_location):
    # REPO_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
    # save_location = '/root/data/hf_cache/llama-3-8B-Instruct'
    hf_token = input("huggingface token:")
    snapshot_download(repo_id=REPO_ID,
                    local_dir=save_location,
                    token=hf_token)
    
    return save_location

# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

def get_oai_fees(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    if model_name.startswith("gpt-4o-mini"):
        model_name = "gpt-4o-mini"
    elif model_name.startswith("gpt-4o"):
        model_name = "gpt-4o"
    elif model_name.startswith("gpt-4"):
        model_name = "gpt-4"
    elif model_name.startswith("gpt-3.5-turbo"):
        model_name = "gpt-3.5-turbo"
    else:
        logging.info(f"Unknown model name {model_name}")
        #print(f"Unknown model name {model_name}")
    if model_name not in OAI_PRICE_DICT:
        return -1
    fee = (OAI_PRICE_DICT[model_name]["prompt"] * prompt_tokens + OAI_PRICE_DICT[model_name]["completion"] * completion_tokens) / 1000000
    # print (f"Model name used for billing: {model_name} \n{fee}")
    
    return fee

OAI_PRICE_DICT = {
    "gpt-4o-mini": {
        "prompt": 0.15,
        "completion": 0.6
    },
    "gpt-4o": {
        "prompt": 5,
        "completion": 15
    },
    "gpt-4": {
        "prompt": 5,
        "completion": 15
    },
    "gpt-3.5-turbo": {
        "prompt": 0.5,
        "completion": 1.5
    }
}


## define a base openai agent class 
class BSAgent():
    def __init__(self,
                 api_key=None, 
                 api_base_url='https://api.openai.com/v1',
                 model="gpt-4o", 
                 temperature=0):
        if not api_key:
            api_key = os.environ['OPENAI_API_KEY']
        self.client = OpenAI(api_key=api_key,
                             base_url=api_base_url)
        self.temperature = temperature
        if model:
            self.model = model
        self.message = []

    def _add_messages_history(self, response) -> None:

        self.message.append(response["choices"][0]["message"])

    def _get_api_response(self,model,conv_history,temperature,stream,json_mode,**kwargs):
        if json_mode:
            response = self.client.chat.completions.create(
                        model=model,
                        response_format={ "type": "json_object" },
                        messages=conv_history,
                        temperature=temperature,
                        stream=stream,
                        **kwargs
                    )
        else:  
            response = self.client.chat.completions.create(
                        model=model,
                        messages=conv_history,
                        temperature=temperature,
                        stream=stream,
                        **kwargs
                    )
        return response
    
    @exception_handler(error_msg='Failed with multiple retry',
                        error_return=None,
                        attempts=3,delay=5)
    def get_completion(self,
                       prompt_template, 
                       model=None,
                       temperature=None,
                       conv_history=None,
                       return_cost=False,
                       verbose=True,
                       stream=False,
                       json_mode=False,
                       **kwargs):
        if not model:
            model = self.model
        
        if not temperature:
            temperature = self.temperature
        
        new_message = []
        if prompt_template.get('System'):
            new_message.append({"role": "system", "content": prompt_template['System']})
        if prompt_template.get('Human'):
            new_message.append({"role": "user", "content": prompt_template['Human']})
        
        if conv_history is None:
            conv_history=[]
        conv_history.extend(new_message)
        
        if len(conv_history) == 0 :
            raise Exception('prompt template error, prompt must be a dict with with System message or Human message.')
  
        response = self._get_api_response(model,conv_history,temperature,stream,json_mode,**kwargs)
        # response = self.client.chat.completions.create(
        #             model=model,
        #             messages=conv_history,
        #             temperature=temperature,
        #             stream=stream
        #         )
        
        if not stream:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            this_time_price = get_oai_fees(model, prompt_tokens, completion_tokens)
            if verbose:
                logging.info(f"************|||----|||price: {this_time_price}|||----|||************")
        
        if return_cost:
            return response,this_time_price
        
        return response 
    
    def get_response_content(self,**kwargs):
        response = self.get_completion(**kwargs)
        res_msg = response.choices[0].message.content
        
        return res_msg
    
    @staticmethod
    def extract_json_string(text):
        """
        Extracts the string between ```json and ``` using regular expressions.
        Parameters:
        text (str): The text from which to extract the string.
        Returns:
        str: The extracted string, or an empty string if no match is found.
        """
        # Regular expression to extract text between ```json and ```
        match = re.search(r'```json\s+(.*?)\s+```', text, re.DOTALL)

        # Return the extracted text if a match is found, otherwise return an empty string
        return match.group(1) if match else ""
    
    def parse_load_json_str(self,js):
        res = json.loads(self.extract_json_string(js))
        return res
    

    

class BSAgent_legacy(BSAgent):
    def __init__(self, api_key=None, 
                 model="gpt-3.5-turbo-1106", 
                 temperature=0):

        if not api_key:
            api_key = os.environ['OPENAI_API_KEY']
        #self.client = OpenAI(api_key=api_key)
        self.temperature = temperature
        if model:
            self.model = model
        self.message = []
    
    def _get_api_response(self,model,conv_history,temperature,stream):
        response = openai.ChatCompletion.create(
                        model=model,
                        messages=conv_history,
                        temperature=temperature, # this is the degree of randomness of the model's output
                    )
        return response
        
    def get_response_content(self,**kwargs):
        response = self.get_completion(**kwargs)
        res_msg = response.choices[0].message["content"]
        return res_msg
    
    @staticmethod
    def parse_load_json_str(js):
        res = json.loads(js.replace("```json","").replace("```",""))
        return res
    
def parse_result(res, parser,verbose):
    try:
        return parser.parse(res).dict()
    except Exception as e:
        if verbose:
            print(f"Parser error: {e}")
        return None
    
def custom_llm_result_parsing(llm_res, llm_agent, json_parse=True,parser=None, output_fixing_pt_temp=None,verbose=False):
    """
    Parses the response from an LLM agent using a specified parser. If the parser fails,
    it attempts to parse the response as JSON, and if that fails, it uses an optional
    output fixing prompt template to reformat the response.

    Args:
        llm_res (str): The response string from the LLM agent to be parsed.
        llm_agent (object): The LLM agent object which has methods for parsing and getting responses.
        json_parse (bool, optional): Flag to indicate if a basic JSON parsing should be attempted if the parser fails. Defaults to True.
        parser (object, optional): A custom parser object with a parse method. Defaults to None.
        output_fixing_pt_temp (str, optional): A prompt template string for the LLM agent to fix the output format. Defaults to None.
        verbose (bool, optional): Flag to print detailed error messages and steps. Defaults to False.

    Returns:
        dict or None: The parsed response as a dictionary, or None if all parsing attempts fail.
    """

    if parser:
        res_dict = parse_result(llm_res, parser,verbose)
        if res_dict is None:
            if json_parse:
                try:
                    res_dict = llm_agent.parse_load_json_str(llm_res)
                    if verbose:
                        print('Use basic json parse to fix output ...')
                except Exception as e:
                    if verbose:
                        print(f"JSON parsing error: {e}")
                    res_dict = None
            if res_dict is None and output_fixing_pt_temp:
                try:
                    new_res = llm_agent.get_response_content(prompt_template=output_fixing_pt_temp, max_tokens=4096,temperature=0)
                    #print(res)
                    res_dict = custom_llm_result_parsing(new_res, llm_agent,json_parse,parser, False)
                    if verbose:
                        print('Use llm to fix output ...')
                except Exception as e:
                    if verbose:
                        print(f"Output fixing template error: {e}")
                    res_dict = None
        return res_dict
    else:
        return None

#%%
if __name__ == "__main__":
    print(tiktoken_len('a test sentence, macroeconomist'))
# %%
