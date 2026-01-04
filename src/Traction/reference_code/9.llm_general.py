'''
Zero-shot sentiment analysis using GPT.
Input: df_documents.csv
Output: df_documents_general.csv
'''
from util import *

directory = r'../../data/'

# read data
df_documents = pd.read_csv(directory+'output/df_documents.csv')

for i, row in df_documents.iterrows():
    if i >= 0:
        chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": '''You are an experience macroeconomist from IMF. Given two pieces of texts describing the views of IMF staff and a country's authorities, assess whether and how the country's authorities agree or disagree with the views of IMF staff by using only the information from the given texts.
First, assign a numerical value to the extent of the authorities' agreement with IMF staff in general, ranging from -5 to 5, where -5 stands for completely disagree, 5 stands for completely agree.
Second, for each of the five sectors - Monetary, Fiscal, External, Financial, and Real (economic conditions and outlooks) - assign a numerical value reflecting the level of agreement specific to that sector, following the same scale of -5 to 5. If the text do not provide sufficient information on the authorities' views regarding a specific sector, assign a value of 99.
Third, for each of the five sectors, summarize the specific area(s) of disagreement in concise phrase(s) (for example, "monetary policy direction", "debt sustainability", etc) and list them as a dictionary (keys: area name; values: level of disagreement scaled from -5 (highest degree of disagreement) to -1). If the text do not provide sufficient information in this sector or there is no identified disagreement in this sector, return an empty dictionary.
Fourth, if there are any disagreements that do not fall into any of the above sectors, summarize the area(s) in concise phrase(s) and list them in the "other_areas" field as a dictionary (keys: area name; values: level of disagreement) - for example, Climate Change, Inclusion, Digitalization and Technology, Governance and Corruption, Structural Reforms, and so on.

Definitions of sectors:
1. Monetary Sector: Deals with the supply of money, interest rates, and the overall monetary policy managed by a country's central bank.
2. Fiscal Sector: Involves government revenue and expenditure. It includes taxation, government spending, budget deficits/surpluses, and public debt.
3. External Sector: Covers a country's international economic transactions, including trade in goods and services, cross-border investment, and foreign exchange markets.
4. Financial Sector: Includes institutions and markets that facilitate the flow of funds between savers and borrowers. It encompasses banks, stock markets, bond markets, and other financial intermediaries.
5. Real Sector: Encompasses the production and consumption of goods and services in an economy. It includes activities related to agriculture, manufacturing, services, and trade.

Please respond in a clean json dictionary: \"Agreement_General\", \"Agreement_Monetary\", \"Agreement_Fiscal\", \"Agreement_External\", \"Agreement_Financial\", \"Agreement_Real\", \"Monetary Sector\", \"Fiscal Sector\", \"External Sector\", \"Financial Sector\", \"Real Sector\", \"other_areas\".''',},
                {   "role": "user",
                    "content":  '''Country: %s; Year: %s\n\nPart1 - IMF staff:\n%s\n\nPart2 - Authorities:\n%s''' % (row['country'], row['year'], row['staff'], row['buff'])}
            ],
            model="gpt-4o-2024-08-06",
            temperature=0
        )
        try:
            result = json.loads(chat_completion.choices[0].message.content.replace('```json','').replace('```',''))
            df_documents.loc[i, 'agreement_gpt'] = result['Agreement_General']
            for sector in ['Monetary', 'Fiscal', 'External', 'Financial', 'Real']:
                df_documents.loc[i, 'agreement_gpt_'+sector] = str(result['Agreement_'+sector])
                df_documents.loc[i, sector+'_gpt'] = str(result[sector+' Sector'])
            if 'other_areas' in result:
                df_documents.loc[i, 'other_areas_gpt'] = str(result['other_areas'])
        except Exception:
            df_documents.loc[i, 'error_gpt'] = chat_completion.choices[0].message.content.replace('```json','').replace('```','')


# deal with errors
i = df_documents[df_documents['error_gpt']!='nan'].index[0]
df_documents.loc[i, 'error_gpt'] = '{\n  "Agreement_General": 4,\n  "Agreement_Monetary": 4,\n  "Agreement_Fiscal": 3,\n  "Agreement_External": 4,\n  "Agreement_Financial": 4,\n  "Agreement_Real": 4,\n  "Monetary Sector": {\n    "monetary policy": 0\n  },\n  "Fiscal Sector": {\n    "fiscal consolidation": -3,\n    "revenue measures": -1\n  },\n  "External Sector": {},\n  "Financial Sector": {},\n  "Real Sector": {},\n  "other_areas": {\n    "climate change": -3,\n    "judicial reform": -1\n  }\n}'
result = json.loads(df_documents.loc[i, 'error_gpt'])
df_documents.loc[i, 'agreement_gpt'] = result['Agreement_General']
for sector in ['Monetary', 'Fiscal', 'External', 'Financial', 'Real']:
    df_documents.loc[i, 'agreement_gpt_'+sector] = str(result['Agreement_'+sector])
    df_documents.loc[i, sector+'_gpt'] = str(result[sector+' Sector'])
if 'other_areas' in result:
    df_documents.loc[i, 'other_areas_gpt'] = str(result['other_areas'])

# save
df_documents.to_csv(directory+'output/gpt/df_documents_general.csv', index=False)