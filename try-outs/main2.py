import nest_asyncio
nest_asyncio.apply()
from dotenv import load_dotenv

import asyncio
import os

load_dotenv()

# Configuration for the assistant
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent


# Step 1: Initialize Local Executor
executor = LocalCommandLineCodeExecutor(work_dir=r"C:\Users\vasanth\Desktop\ai_deployer_project\test-repos\fastapi")
python_tool = PythonCodeExecutionTool(executor)

# Step 2: OpenAI Client
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

# agent 1
code_generator_agent = AssistantAgent(
    name="code_generator",
    model_client=model_client,
    tools=[],
    system_message="You are a Python expert. Generate code to list the directory structure of the given path using os.walk() with indentation for subdirectories."
)

# agent 2
code_executor_agent = AssistantAgent(
    name="code_executor",
    model_client=model_client,
    tools=[python_tool],
    system_message="""You are a Python code executor. Run the given code and return the output string.give the response like a tree format like this:"
    project/
│
├── src/
│   ├── main.py
│   ├── utils.py
│   └── config.py
│
├── templates/
│   ├── index.html
│   └── layout.html
│
├── static/
│   ├── styles.css
│   └── script.js
│
└── README.md

    
    """
)

#agent 3
output_processor = AssistantAgent(
    name="output_processor",
    model_client=model_client,
    system_message="Analyze the given directory structure and detect build files like 'requirements.txt','pom.xml' or 'package.json' that contain data about the tech stack. Give only the build file that i will later use to read, so dont give any explainations."
)
build_file_reader = AssistantAgent(
    name="framework_detector",
    model_client=model_client,
    tools=[python_tool],
    system_message="You are a code generator. Write Python code to read all the data present in the build file info given to you",
    reflect_on_tool_use=True
)


# Path to get directory structure
target_path = r"C:\Users\vasanth\Desktop\ai_deployer_project\test-repos\fastapi"

# User Prompt to generate code
user_prompt = f"Generate Python code to list the directory structure of the path: '{target_path}'. Use indentation for subdirectories."


# Multi-Agent Orchestration
async def run_agents():
    # Step 1: Code Generation by code_generator_agent
    gen_response = await code_generator_agent.run(
        task=user_prompt
    )
    generated_code = gen_response.messages[-1].content

    # Step 2: Code Execution by code_executor_agent
    exec_response = await code_executor_agent.run(
        task=generated_code, # Force execution
    )

    print("\n🚀 Final Output from Code Execution:")
    print(exec_response.messages[-1].content)

    build_file_result = await output_processor.run(
        task=f"From this directory structure, find all build files and tech stack information: {exec_response.messages[-1].content}"
    )
    print("\n🚀 Final Output from build file detection:")
    print(build_file_result.messages[-1].content)
   
    build_file_reader = await build_file_reader.run(
task=f"generate a python code to read all the data present in the build file {build_file_result.messages[-1].content} from the project path: {target_path}"
    )
    print("\n🚀 Final Output from build_file_reader:")
    print(build_file_reader.messages[-1].content)



 



if __name__ == "__main__":
    asyncio.run(run_agents())
