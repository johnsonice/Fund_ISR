#%%
import frontmatter
import re
from typing import Dict, Mapping

SECTION_RE = re.compile(r"^##\s*(?P<section>\w+)\s*$", re.MULTILINE)

class Prompt:
    def __init__(self, metadata: Mapping, sections: Dict[str,str]):
        self.metadata = metadata
        self.sections = sections

def load_prompt(prompt_path) -> Prompt:
    """Load a prompt Markdown file, parse front-matter and split by ## headings."""
    post = frontmatter.load(prompt_path)

    # split on lines beginning with "## " to capture section headings
    parts = SECTION_RE.split(post.content)
    # SECTION_RE.split gives: [prelude, sec1, content1, sec2, content2, ...]
    it = iter(parts)
    _prelude = next(it)  # should be empty or description text
    sections = {}
    for section, body in zip(it, it):
        sections[section.strip()] = body.strip()

    return Prompt(metadata=post.metadata, sections=sections)

def format_messages(prompt: Prompt, add_schema=False) -> list:
    """Format the Prompt object into OpenAI chat message format.
    
    Args:
        prompt (Prompt): The prompt object containing .
        schema (str, optional): Schema to append to system message.
    
    Returns:
        list: A list of message dictionaries with 'role' and 'content' keys.
    """
    messages = []
    
    # Add system message if present, optionally with schema
    if "system" in prompt:
        system_content = prompt["system"]
        messages.append({
            "role": "system",
            "content": system_content
        })
    
    # Add user message if present
    if "user" in prompt:
        messages.append({
            "role": "user",
            "content": prompt["user"]
        })
    # Add schema to system message if it exists, otherwise to user message
    if add_schema and "schema" in prompt:
        schema_content = prompt["schema"]
        if "system" in prompt and messages:
            # Add to system message
            system_idx = next((i for i, msg in enumerate(messages) if msg["role"] == "system"), None)
            if system_idx is not None:
                messages[system_idx]["content"] = f"{messages[system_idx]['content']}\n\n{schema_content}"
        elif "user" in prompt and messages:
            # Add to user message
            user_idx = next((i for i, msg in enumerate(messages) if msg["role"] == "user"), None)
            if user_idx is not None:
                messages[user_idx]["content"] = f"{messages[user_idx]['content']}\n\n{schema_content}"

    # # Add any other sections as their own role types
    # for section, content in prompt.sections.items():
    #     if section.lower() not in ["system", "user"]:
    #         messages.append({
    #             "role": section.lower(),
    #             "content": content
    #         })
    
    return messages

#%%
if __name__ == "__main__":
    prompt_path = "../src/Traction/prompts/topic_classification.md"
    chat_messages = load_prompt(prompt_path)
    print(chat_messages.sections)
    print(format_messages(chat_messages.sections,add_schema=True))
# %%
