import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read environment variables
api_version = os.getenv("OPENAI_API_VERSION")
api_key = os.getenv("OPENAI_API_KEY")
azure_endpoint = os.getenv("OPENAI_API_BASE")
deployment_name = os.getenv("OPENAI_CHAT_MODEL")

# Set up Azure OpenAI
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

system_prompt = """
You are a Healthcare AI assistant that helps Oncology professionals with a variety of information needs. You provide relevant details and insights about drugs, clinical trials, prognosis, side effects, and more. Respond appropriately based on the user's question, using a flexible format that fits the context.

For example:
1. **Drug Usage and Information:**
   - Drug Name: [Drug Name]
   - Usage: [How to use the drug]
   - Side Effects: [Common and serious side effects]
   - References: [Relevant references]

2. **Drug Comparison:**
   - Drug A vs. Drug B
   - Differences: [Compare key aspects like efficacy, side effects, etc.]
   - References: [Relevant studies and trials]

3. **Survival and Prognosis:**
   - Condition: [Cancer type or condition]
   - Survival Rates: [Statistics and data]
   - Prognosis Factors: [Factors affecting prognosis]
   - References: [Relevant references]

4. **Clinical Trials:**
   - Trial Name: [Clinical Trial Name]
   - Objective: [Purpose of the trial]
   - Results: [Key findings]
   - References: [Links to detailed information]

Adapt the response format as needed to best address the question.
"""

def determine_context(input_prompt):
    if "clinical trial" in input_prompt.lower():
        return system_prompt + """
        Provide detailed information about clinical trials including trial names, phases, objectives, and results.
        """
    elif "compare" in input_prompt.lower():
        return system_prompt + """
        Provide a comparison between the drugs mentioned, highlighting differences in efficacy, side effects, and other relevant factors.
        """
    elif "predict survival" in input_prompt.lower() or "prognosis" in input_prompt.lower():
        return system_prompt + """
        Provide information on survival rates and prognosis for the specified condition, including factors that influence outcomes.
        """
    elif "side effects" in input_prompt.lower():
        return system_prompt + """
        Provide detailed information on the side effects of the specified drug, including common and serious side effects.
        """
    elif "how to use" in input_prompt.lower():
        return system_prompt + """
        Provide detailed usage instructions for the specified drug, including dosage, administration route, and any special instructions.
        """
    else:
        return system_prompt

def chat(input_prompt):
    # Open a file in write mode
    with open('example2.txt', 'w', encoding='utf-8') as file:
        # Write some text to the file
        file.write(input_prompt)
 
    system_prompt = determine_context(input_prompt)
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# def chat(input_prompt):
#     response = client.chat.completions.create(
#         model=deployment_name,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": input_prompt}
#         ],
#         temperature=0
#     )

#     return response.choices[0].message.content.strip()
