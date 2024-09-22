### Prompts 


############################
topic_identify_simple_pt = {
    'System':'You are an experience macroeconomist from IMF. Your job is to assign topic labels to a given paragraph from IMF document',
    'Human':"""
You are given a list of topics with their definition and key indicators as below:
----------------
----------------
**Economic Outlook**:
- **Definition**: The assessment of cyclical position and economic outlook involves evaluating the current and projected state of an economy over various time horizons. This includes analyzing near-term and medium-term growth prospects, understanding the business cycle phases (expansion and contraction), and identifying potential economic risks and uncertainties. Key indicators such as GDP growth, inflation, and the output gap are scrutinized to gauge macroeconomic stability. The evaluation also considers the impacts of fiscal and monetary policies on economic trends and forecasts potential scenarios, highlighting recession risks and opportunities for economic expansion.
- **Key Indicators**: economic outlook, near-term growth, medium-term growth, economic assessment, GDP growth, business cycle, economic forecast, projected growth, output gap, cyclical analysis, economic risks, economic indicators, macroeconomic stability, recession risk, expansion phase, contraction phase, economic trends

**Monetary Policy**:
- **Definition**: Monetary policy refers to the actions undertaken by a central bank, such as the Federal Reserve or the European Central Bank, to manage the economy by controlling the money supply, interest rates, and inflation. It aims to achieve price stability, full employment, and economic growth. Key aspects include setting the policy rate, managing inflation expectations and targets, addressing inflationary pressures, and ensuring financial stability. Monetary policy can involve conventional measures, such as adjusting interest rates, and unconventional tools, like quantitative easing and monetary tightening. It also encompasses the monetary transmission mechanism, which describes how policy actions affect the economy, and the interaction with fiscal policy.
- **Key Indicators**: inflation expectations, inflation target, inflationary pressures, monetary policy stance, policy rate, price stability, interest rates, central bank, quantitative easing, monetary tightening, unconventional monetary policy, monetary transmission mechanism, currency exchange rates, liquidity management, money supply, aggregate demand

**Fiscal Stance**:
- **Definition**: The fiscal stance and debt topic encompasses the analysis and evaluation of a government's fiscal policies and their impact on economic sustainability. This includes assessing fiscal sustainability, consolidation efforts, and the overarching fiscal framework that guides policy decisions. Key considerations involve the management of fiscal space, budget allocations, and the balance between fiscal deficits and surpluses. The topic also examines the influence of oil and non-oil revenues on fiscal health, the intricacies of managing government debt, and strategies for ensuring debt sustainability. Understanding the relationship between fiscal policy, expenditure, GDP, and various forms of debt (public, external, and domestic) is crucial for formulating effective economic strategies and maintaining financial stability.
- **Key Indicators**: fiscal sustainability, fiscal consolidation, fiscal framework, fiscal policy, fiscal space, budget, fiscal deficit, primary deficit, balanced budget, fiscal stance, oil revenue, non-oil revenue, government debt, expenditure, debt sustainability, debt management, external debt, public debt, domestic debt

**Financial Stability**:
- **Definition**: Financial stability refers to the resilience of the financial system, including banks, financial markets, and other financial institutions, in withstanding economic shocks and maintaining efficient functioning. It encompasses various aspects such as risk management, credit growth, and the health of the banking sector. Key elements include the implementation of macroprudential policies, management of non-performing loans (NPLs), maintenance of adequate capital and liquidity levels, assessment of risks in the housing market; and robust supervision and stress testing of financial institutions. Effective governance, rigorous internal and external audits, and adherence to reporting standards and safeguards assessments are essential to ensure financial stability.
- **Key Indicators**: financial stability, banking sector, credit growth, financial institutions, macroprudential, non-performing loans (NPLs), capital, credit risk, liquidity, supervision, stress tests, bank governance, internal audit, reporting standards, safeguards assessment, external audit, regulatory measures, overvaluation, bubbles, booms, real estate sector risks 

**External Stance**:
- **Definition**: The topic covers the macroeconomic analysis of a country's external economic health and the dynamics of its currency's exchange rate. Key elements include international reserves, current account deficits and surpluses, and the effective exchange rate, which are essential indicators of external balance. The topic also encompasses the analysis of implied fundamentals through models like the EBA-lite, and the impact of capital grants, trade policies, and trade elasticities on the external position. Understanding trade liberalization, integration, and barriers further helps in evaluating the broader context of global trade influences on exchange rates.
- **Key Indicators**: international reserves, current account deficit, implied fundamentals, external balance, effective exchange rate, current account surplus, EBA-lite model, external deficit, capital grants, exchange rate, import elasticity, export elasticity, trade liberalization, trade policy, trade integration, bilateral trade, global trade, tariff barriers

**Climate Change**:
- **Definition**: Climate mitigation, adaptation, and transition encompass strategies and actions aimed at reducing greenhouse gas emissions, enhancing resilience to climate impacts, and shifting towards sustainable and low-carbon energy systems. These efforts include the development and implementation of renewable energy sources, improving energy efficiency, securing energy resources, and financing green initiatives. Key policies such as carbon pricing and green finance play a critical role in driving sustainable development and achieving carbon neutrality. The transition to a low-carbon economy involves not only technological advancements but also comprehensive environmental policies and frameworks to support ecosystem services and build resilience against climate-related risks.
- **Key Indicators**: climate mitigation, climate adaptation, climate transition, energy security, climate change, renewable energy, energy efficiency, sustainability, climate finance, carbon pricing, emissions reduction, green finance, environmental policy, sustainable development, carbon neutrality, climate resilience, low-carbon technology, decarbonization, net-zero emissions, ecosystem services

**Inclusion**:
- **Definition**: Inclusion in the context of macroeconomics refers to the equitable participation and access to resources across various segments of society. This encompasses gender equality, labor force participation, and the provision of social spending aimed at improving financial inclusion, education, housing and health. Key aspects include promoting skilled labor, increasing employment opportunities, improve housing affordability and addressing labor market disparities. Social assistance programs and policies targeting poverty reduction and social protection play a critical role in mitigating inequality. Furthermore, pension reforms and the management of public wages are essential for ensuring sustainable economic growth and social stability. Addressing employment effects and wage growth, including the implementation of minimum wage policies, are vital components of fostering inclusive economic development.
- **Key Indicators**: gender, social spending, financial inclusion, education, health, skilled labor, employment, female labor, labor market, social assistance, poverty reduction, social protection, inequality, pension reform, retirement, wage, housing affordability

**Technology**:
- **Definition**: Digitalization and technology encompass the integration of digital technologies into various sectors, leading to significant transformations in the economy, government, and society. This topic covers the development of digital infrastructure and innovation, the adoption of new technologies, and the formulation of digital strategies. Key aspects include the digital economy, platforms, skills, and government initiatives. Additionally, it addresses the regulation and legal frameworks for emerging technologies like Bitcoin and digital assets, ensuring consumer protection and financial inclusion while managing risks. The role of Artificial Intelligence, blockchain, cybersecurity, and data privacy are also critical in this digital landscape.
- **Key Indicators**: digital infrastructure, digital innovation, technology adoption, digital strategy, digital economy, digital technologies, digital platforms, digital skills, digital government, bitcoin regulation, legal framework, consumer protection, financial inclusion, regulatory framework, risks, digital assets, Artificial Intelligence, blockchain, cybersecurity, data privacy, bitcoin, legal tender, Fintech

**Governance**:
- **Definition**: Governance in the context of macroeconomic policy involves the frameworks and practices that ensure the effective, transparent, and accountable management of public resources. Key elements include combating corruption through robust anti-corruption strategies and enforcement mechanisms, enhancing Anti-Money Laundering and Countering the Financing of Terrorism (AML/CFT) frameworks, and promoting fiscal transparency to ensure that government financial operations are open and clear to the public. Central bank independence and institutional reforms are crucial for maintaining the integrity and stability of financial systems. Effective governance also involves setting and adhering to reporting standards, conducting internal and external audits, and implementing safeguards assessments to detect and prevent misuse of funds. Legislation, compliance, and prosecution are fundamental in enforcing these principles, while continuous efforts to refine and implement recommendations are essential for improving governance structures.
- **Key Indicators**: Corruption, AML/CFT, Fiscal transparency, Central bank independence, Institutional reforms, Corruption strategy, Enforcement, Legislation, Compliance, Prosecution, Bank governance, Internal audit, External audit, Safeguards assessment, Reporting standards, Governance, Anti-corruption, Audit, Transparency, Implementing recommendations

**Structural Reforms**:
- **Definition**: Structural reforms refer to policies and measures aimed at improving the overall productivity and efficiency of an economy. These reforms are distinct from social reforms and focus on enhancing the functioning of product markets, fostering innovation, and increasing economic diversification and competitiveness. Key areas include product market reforms, improving the business environment, public and private investment management, and fostering technological advancement. By implementing regulatory, labor market, trade, and financial sector reforms, these measures aim to create a more dynamic and competitive economy capable of sustaining long-term growth and development.
- **Key Indicators**: product market reforms, productivity enhancement, economic diversification, increasing competitiveness, business environment, public investment, investment management, private sector development, innovation, regulatory reforms, entrepreneurship, market efficiency, technological advancement, labor market reforms, trade liberalization, infrastructure development, financial sector reforms, institutional reforms, foreign direct investment, competition policy

**Other Topics**:
- **Definition**: Any content that do not fit into the *predefined categories above*. Examples include discussions on IMF program performance, data provision, data quality and dissemination, expressions of appreciation for Fund support, including capacity development; and other macroeconomic subjects that are not predefined.
- **Key Indicators**: no specific key indicators 

----------------
----------------
    
You are also given a paragraph from a report published by the International Monetary Fund as below: 

----------------
----------------
{PARA}
----------------
----------------

Please carefully analyze the paragraph and classify the provided paragraph using ONLY the provided topics. 
Try your best to assign only one topic to the paragraph. You can use multiple categories only if you are very confident that multiple topics are extensively discussed in the paragraph.
Please be aware that there is a **Other Topics** category. If the paragraph does not fit into any of the predefined topics before **Other Topics** category, put it as **Other Topics**. 
Please provide your reasoning for your classification first, and then provide the topic label and a confidence score from 0-100.

Please respond in clean json format as follow:
```json
{{"reasoning": "<reasoning process>", 
"topic_labels": [{{"topic_label":"<identified topic label>","confidence_score":<confidence score>}},...]}}
```
Response:

"""}
#########################

output_fixing_pt = {'System':"You are an intelligent assistant specialized in formatting text. Your task is to take raw LLM output and format it according to user-provided instructions. Follow the specific formatting guidelines given and ensure the final output is clean, readable, and adheres to the specified style.",
      'Human':"""
Here is the raw LLM output:
----------------
----------------
{LLM_OUTPUT}
----------------
----------------

You are supposed to extract appropriate information for reasoning and topic_labels. topic_labels has additional information for confidence score.

Please respond in clean json format as follow:
```json
{{"reasoning": "<reasoning process>", 
"topic_labels": [{{"topic_label":"<identified topic label>","confidence_score":<confidence score>}},...]}}
```
Response:
"""}

#########################################################################################################################
output_fixing_pt = {'System':"""
                    You are an experience macroeconomist from IMF. You will be given a paragraph from IMF Staff repoart in the user prompt.
                    Your job is to determine if the paragraph discussed about gender issues in economic context. 
                    Please think step by step, and provide your thoughts and then give a Yes or No answer. 
                    The output format shoud follow:
                    ```json
                    {{"reasoning": "<reasoning process>", 
                    "answer": "<Yes or No>"
                    ```
                    """,
                    'Human':"""{USER_INPUT}"""}
