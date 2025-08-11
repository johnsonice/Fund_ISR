"""
Simple LLM Agent for OpenAI API interactions.
Provides basic API calls with retry logic and result parsing.
"""
#%%
import os
import json
import re
from typing import Dict, List, Optional, Union, Any
from openai import OpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import datetime
import math
import asyncio
from tqdm.asyncio import tqdm
now = datetime.datetime.now()
USER = os.environ.get("USER", "UNKNOWN").upper()
today = datetime.date.today()
file_path = f"log/{USER}/{today}"
os.makedirs(file_path, exist_ok=True)
filename = f"{file_path}/Exp-{now.hour:02d}:{now.minute:02d}.log"
fmt = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    filename=filename,
    filemode="w",
    format=fmt
)
logger = logging.getLogger(__name__)
from pydantic import BaseModel, Field
# Load API key from environment
from dotenv import load_dotenv
load_dotenv('../.env')

# Constants
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0


#%%
class LLMAgent:
    """Simple LLM agent for OpenAI API interactions."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE
    ):
        """
        Initialize the agent with OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, uses environment variable OPENAI_API_KEY
            base_url: Base URL for API endpoint. If None, uses OpenAI default
            model: Model identifier to use (default: gpt-4o-mini)
            temperature: Temperature parameter for generation (default: 0)
        """
        self.client = OpenAI(
            api_key=api_key or os.environ.get('OPENAI_API_KEY'),
            base_url=base_url
        )
        self.model = model
        self.temperature = temperature
    
    @staticmethod
    def _is_pydantic_model(obj) -> bool:
        """Check if an object is a Pydantic model class."""
        return (obj and hasattr(obj, '__bases__') and 
                any(base.__name__ == 'BaseModel' for base in obj.__mro__))

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def _make_api_call(self, messages: List[Dict[str, str]],**kwargs) -> Any:
        """Make a retry-enabled API call to OpenAI with Pydantic model support."""
        # get response_format from kwargs, use different parser for different response_format
        response_format = kwargs.get("response_format")
        # Determine temperature: use user-passed value if present, else self.temperature
        temperature = kwargs.pop("temperature", self.temperature)
        
        # Check if response_format is a Pydantic model
        if self._is_pydantic_model(response_format):
            return self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                temperature=temperature,
                **kwargs
            )
        else:
            # Use regular API for JSON objects and text responses
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                **kwargs
            )

    def get_response_content(self, messages: List[Dict[str, str]], safe_mode: bool = False, **kwargs) -> Union[str, Any]:
        """Get just the content from a completion response."""
        try:
            response = self._make_api_call(messages, **kwargs)
            response_format = kwargs.get("response_format")
            
            # Check if response_format is a Pydantic model (structured output)
            if self._is_pydantic_model(response_format):
                # Return parsed Pydantic model
                return response.choices[0].message.parsed
            else:
                # Return text content for regular responses and JSON objects
                return response.choices[0].message.content
        except Exception as e:
            if safe_mode:
                return "LLM_ERROR"
            else:
                raise Exception(f"LLM API call failed: {str(e)}")

    @staticmethod
    def parse_json(text: str) -> Dict:
        """Parse JSON from response, handling code"""       # Remove code block markers if present
        text = re.sub(r'```json\s*\n?', '', text)
        text = re.sub(r'\n?```', '', text)
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Text: {text}")
            raise

    def test_connection(self, test_message: str = "Hello, can you respond?") -> str:
        """Test the API connection."""
        try:
            messages = [{"role": "user", "content": test_message}]
            response = self._make_api_call(messages)
            result = response.choices[0].message.content
            logger.info("✅ Connection test successful")
            return result
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            raise
        

class AsyncLLMAgent(LLMAgent):
    """Async LLM agent that reuses the logic from :class:`LLMAgent` and only overrides
    the pieces that need to be asynchronous. This keeps the two classes in sync
    and dramatically reduces code duplication."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        # Directly create the async client (no need to call the parent constructor
        # which expects a valid `OPENAI_API_KEY` to instantiate a synchronous
        # client first).
        self.client = AsyncOpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url,
        )

        # Re-use the same public attributes as the sync agent so that the parent
        # methods we inherit continue to work as expected.
        self.model = model
        self.temperature = temperature

    # NOTE: The tenacity retry decorator works with `async def` as well.
    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _make_api_call(self, messages: List[Dict[str, str]], **kwargs) -> Any:  # type: ignore[override]
        """Asynchronous variant of :py:meth:`LLMAgent._make_api_call`."""

        response_format = kwargs.get("response_format")
        temperature = kwargs.pop("temperature", self.temperature)

        if self._is_pydantic_model(response_format):
            return await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                temperature=temperature,
                **kwargs,
            )

        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )

    async def get_response_content(self, messages: List[Dict[str, str]], safe_mode: bool = False, **kwargs) -> Union[str, Any]:
        """Async wrapper around :py:meth:`LLMAgent.get_response_content`."""
        #print(safe_mode)
        try:
            response = await self._make_api_call(messages, **kwargs)
            response_format = kwargs.get("response_format")

            if self._is_pydantic_model(response_format):
                return response.choices[0].message.parsed

            return response.choices[0].message.content
        except Exception as e:
            if safe_mode:
                return "LLM_ERROR"
            else:
                raise Exception(f"LLM API call failed: {str(e)}")

    async def test_connection(self, test_message: str = "Hello, can you respond?") -> str:
        """Convenience helper to quickly verify the async client works."""

        messages = [{"role": "user", "content": test_message}]
        response = await self._make_api_call(messages)
        result = response.choices[0].message.content
        logger.info("✅ Async Connection test successful")
        return result


class BatchAsyncLLMAgent(AsyncLLMAgent):
    """Extension of :class:`AsyncLLMAgent` that makes it trivial to send many
    independent chat prompts concurrently while preserving the input order of
    responses.  It exposes a single helper :py:meth:`get_batch_response_contents`.

    Example
    -------
    ```python
    prompts = [
        "Explain quantum computing in 500 words",  # str → will be wrapped for you
        [{"role": "user", "content": "Write a haiku"}],  # already a messages list
    ]

    batch_agent = BatchAsyncLLMAgent()
    results = asyncio.run(batch_agent.get_batch_response_contents(prompts))
    ```
    """

    async def get_batch_response_contents(
        self,
        batch: "list[list[dict[str, str]]]",
        **kwargs,
    ) -> "list[Union[str, Any]]":
        """Process a *batch* of chat prompts concurrently and return responses.

        Parameters
        ----------
        batch : list
            A list where each element is **either** a plain user prompt (*str*)
            **or** a *messages* list that you would normally pass to
            :py:meth:`AsyncLLMAgent.get_response_content`.
        **kwargs : Any
            Additional keyword-arguments forwarded verbatim to
            :py:meth:`AsyncLLMAgent.get_response_content` (e.g. *response_format*,
            *temperature*, *max_tokens*, …).

        Returns
        -------
        list
            A list of model responses in the same order as the *batch* input.
        """

        #import asyncio  # local import to avoid polluting module namespace unnecessarily
        # Schedule concurrent LLM calls – `asyncio.gather` preserves order.
        tasks = [self.get_response_content(msgs, **kwargs) for msgs in batch]
        return await asyncio.gather(*tasks)
    
    async def get_batch_response_contents_auto(
        self,
        batch: "list[list[dict[str, str]]]",
        batch_size: int = 10,
        **kwargs,
    ) -> "list[Union[str, Any]]":
        """
        Process a large batch of chat prompts in smaller sub-batches (chunks) of size `batch_size`.
        This helps avoid overloading the API or running into rate limits.
        The results are returned in the same order as the input batch.
        Progress is tracked with tqdm.

        Parameters
        ----------
        batch : list
            List of message lists (each is a list of dicts for a single prompt).
        batch_size : int, optional
            Number of prompts to process concurrently in each sub-batch (default: 10).
        **kwargs : Any
            Additional keyword-arguments forwarded to get_batch_response_contents.

        Returns
        -------
        list
            List of model responses in the same order as the input batch.
        """
        if not batch:
            return []

        results = [None] * len(batch)
        indices = list(range(len(batch)))
        total = len(batch)

        # tqdm.asyncio.tqdm works with async for, so we use manual loop and update
        with tqdm(total=total, desc="Processing batches", unit="msg") as pbar:
            for i in range(0, total, batch_size):
                sub_batch = batch[i:i + batch_size]
                sub_indices = indices[i:i + batch_size]
                sub_results = await self.get_batch_response_contents(sub_batch, **kwargs)
                for idx, res in zip(sub_indices, sub_results):
                    results[idx] = res
                pbar.update(len(sub_batch))

        return results

 #%%
 # Example usage
if __name__ == "__main__":
    import asyncio

    # Create agent
    agent = LLMAgent()

    # Test connection
    print("Testing connection...")
    result = agent.test_connection()
    print(f"Response: {result}")

    # Example direct API call
    print("\nExample direct API call:")
    messages = [{"role": "user", "content": "What is 2+2?"}]
    response = agent._make_api_call(messages)
    print(f"Response: {response.choices[0].message.content}")

    # Example using result parsing function
    print("\nExample using result parsing function:")
    messages = [{"role": "user", "content": "What is the capital of Japan?"}]
    content = agent.get_response_content(messages)
    print(f"Parsed content: {content}")

    # Example structured output test
    print("\n=== Structured Output Tests ===")
    print("Run 'python unit_test.py' to execute structured output tests")

    async def main():
        print("\n--- Async Agent Tests ---")
        async_agent = AsyncLLMAgent()
        
        # Test connection
        print("Testing async connection...")
        result = await async_agent.test_connection()
        print(f"Response: {result}")
        
        # Example async call
        print("\nExample async call:")
        messages = [{"role": "user", "content": "What is the capital of France?"}]
        content = await async_agent.get_response_content(messages)
        print(f"Parsed content: {content}")

    asyncio.run(main())
 #%%