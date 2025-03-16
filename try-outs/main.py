import nest_asyncio
nest_asyncio.apply()

import asyncio
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool, CodeExecutionInput
from autogen import AssistantAgent, UserProxyAgent
from dotenv import load_dotenv
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
load_dotenv()



model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",)
   # api_key=os.environ.get("OPENAI_API_KEY")



# Initialize the LocalCommandLineCodeExecutor
executor = LocalCommandLineCodeExecutor(work_dir=".")

# Wrap it inside the PythonCodeExecutionTool
python_tool = PythonCodeExecutionTool(executor)
path = r"C:\Users\vasanth\Desktop\ai_deployer_project\test-repos\fastapi"

# Command to list the directory structure
code = f"""
import os
for root, dirs, files in os.walk(r'{path}'):
    level = root.replace(os.getcwd(), '').count(os.sep)
    indent = ' ' * 4 * level
    print(f'{{indent}}{{os.path.basename(root)}}/')
    sub_indent = ' ' * 4 * (level + 1)
    for file in files:
        print(f'{{sub_indent}}{{file}}')
"""

# Async function to run the code
async def run_code():
    # Create a cancellation token
    token = CancellationToken()
    
    # Wrap the code inside CodeExecutionInput
    code_input = CodeExecutionInput(code=code)

    # Run the code with the cancellation token
    result = await python_tool.run(code_input, token)
    print("Execution Output:")
    print(result.output)

# Run the async function directly in the notebook
asyncio.run(run_code())
