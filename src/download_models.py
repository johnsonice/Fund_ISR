### download open source modesl 
#%%
import os
import sys
sys.path.insert(0, '../libs')#%%

from dotenv import load_dotenv
env_path = '../.env'
load_dotenv(dotenv_path=env_path)
hf_key = os.getenv("huggingface_token")
if not hf_key:
    raise ValueError("huggingface_token not found in environment variables. Please check your .env file.")

from utils import donload_hf_model
#%%
hf_cache_folder = '/ephemeral/home/xiong/data/hf_cache'
## download models
donload_hf_model('meta-llama/Llama-3.1-8B-Instruct', 
                 os.path.join(hf_cache_folder,'llama-3.1-8B-Instruct'),
                 hf_token=os.getenv('huggingface_token'))
# donload_hf_model('Qwen/Qwen2.5-7B-Instruct', os.path.join(hf_cache_folder,'Qwen2.5-7B-Instruct'),hf_token=os.getenv('huggingface_token'))
# #donload_hf_model('deepseek-ai/DeepSeek-V2-Lite-Chat', os.path.join(hf_cache_folder,'DeepSeek-V2-Lite-Chat'),hf_token=os.getenv('huggingface_token'))
# donload_hf_model('Qwen/Qwen2.5-14B-Instruct', os.path.join(hf_cache_folder,'Qwen2.5-14B-Instruct')  ,hf_token=os.getenv('huggingface_token'))
# donload_hf_model('microsoft/phi-4', os.path.join(hf_cache_folder,'phi-4'),hf_token=os.getenv('huggingface_token'))
