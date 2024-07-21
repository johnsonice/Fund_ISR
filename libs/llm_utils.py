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

#%%
if __name__ == "__main__":
    print(tiktoken_len('a test sentence, macroeconomist'))
# %%
