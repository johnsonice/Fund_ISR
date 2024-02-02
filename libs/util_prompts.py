### LLM util prompts

output_format_list="""Please format it as a numbered list for clarity and ease of understanding. 
For example, structure your answer with each item listed as: 
1) [item 1]
2) [item 2]
and so on."""

format_ram_table = """ 
Please extract information from the table row by row. Please return a clean list. each item of the list and have clean information under each column name; for example:

1)
Source of Risks: ...... || Relative Likelihood: .... || Expected Impact : .... || Policy Response : ....
2)
Source of Risks: ...... || Relative Likelihood: .... || Expected Impact : .... || Policy Response : ....
3) 
... ...


Please make sure you directly copy content from the sources as much as possible. Do not summarize raw information.
Please proceed:
"""

