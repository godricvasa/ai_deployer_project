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
target_path = r"C:\Users\vasanth\Desktop\ai_deployer_project\test-repos\flask"

# Step 1: Initialize Local Executor
executor = LocalCommandLineCodeExecutor(work_dir=target_path)
python_tool = PythonCodeExecutionTool(executor)

# Step 2: OpenAI Client
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

# Agent 1: Code Generator
code_generator_agent = AssistantAgent(
    name="code_generator",
    model_client=model_client,
    tools=[],
    system_message="You are a Python expert. Generate code to list the directory structure of the given path using os.walk() with indentation for subdirectories."
)

# Agent 2: Code Executor
code_executor_agent = AssistantAgent(
    name="code_executor",
    model_client=model_client,
    tools=[python_tool],
    system_message="You are a Python code executor. Run the given code and return the output string in a tree format like this:"
)

# Agent 3: Output Processor
output_processor = AssistantAgent(
    name="output_processor",
    model_client=model_client,
    system_message="Analyze the given directory structure and detect build files like 'requirements.txt', 'pom.xml', or 'package.json'. Respond with only the build file name, without any explanation."
)

# Agent 4: Build File Reader
build_file_reader = AssistantAgent(
    name="build_file_reader",
    model_client=model_client,
    tools=[python_tool],
    system_message="You are a code generator. Write Python code to read and print all data present in the provided build file (e.g., 'requirements.txt').",
    reflect_on_tool_use=True
)

# Agent 5: Framework Extractor
framework_extractor = AssistantAgent(
    name="framework_extractor",
    model_client=model_client,
    tools=[python_tool],
    system_message="You are a code executor. Run the given Python code to read the build file data. Then, extract and return only the tech stack details like the framework (e.g., FastAPI), database (e.g., MySQL), and other key libraries."
)
# Agent 6 : Framework Extractor
dockerfile_generator_agent = AssistantAgent(
    name="dockerfile_generator",
    model_client=model_client,
    system_message="""
    You are a Dockerfile generator. Based on the detected tech stack (FastAPI, Uvicorn,etc...) and the project structure, generate an optimized Dockerfile.
    """
)

# Path to target directory
# target_path = r"C:\Users\vasanth\Desktop\ai_deployer_project\test-repos\flask"

# User Prompt for Directory Listing
user_prompt = f"Generate Python code to list the directory structure of the path: '{target_path}'. Use indentation for subdirectories."


# Multi-Agent Orchestration
async def run_agents():
    # Step 1: Code Generation
    gen_response = await code_generator_agent.run(task=user_prompt)
    generated_code = gen_response.messages[-1].content

    # Step 2: Code Execution
    exec_response = await code_executor_agent.run(task=generated_code)
    directory_tree = exec_response.messages[-1].content
    print("\n🚀 Final Output from Code Execution:\n", directory_tree)

    # Step 3: Build File Detection
    build_file_result = await output_processor.run(task=f"From this directory structure, find all build files: {directory_tree}")
    build_file_name = build_file_result.messages[-1].content
    print("\n🚀 Final Output from Build File Detection:\n", build_file_name)

    # Step 4: Build File Reader
    build_file_reader_response = await build_file_reader.run(
        task=f"Generate Python code to read all data from the build file '{build_file_name}' located at {target_path}."
    )
    code_to_read_build_file = build_file_reader_response.messages[-1].content
    print("\n🚀 Final Output from Build File Reader:\n", code_to_read_build_file)

    # Step 5: Framework Extractor - Run the code to read and extract frameworks
    clean_code = code_to_read_build_file.replace("\\n", "\n")  # Handle newline escape
    framework_extraction_response = await framework_extractor.run(task=clean_code)

    print("\n🚀 Final Output from Framework Extractor:\n", framework_extraction_response.messages[-1].content)

    dockerfile_response = await dockerfile_generator_agent.run(
    task=f"Create a  Dockerfile for this project with the following directory structure:\n{exec_response.messages[-1].content}\n\nDetected build file: {build_file_result.messages[-1].content} and use this for finding the right framework and dependencies : {framework_extraction_response.messages[-1].content}. the response should not have any explaination and ignore temp files while creating docker file."
)

    print("\n🚀 Final Output from Dockerfile Generator:")
    print(dockerfile_response.messages[-1].content)

    dockerfile_path = os.path.join(target_path, "Dockerfile")
    with open(dockerfile_path, "w") as file:
        docker_file = dockerfile_response.messages[-1].content
        if docker_file.startswith("```dockerfile"):
          docker_file = docker_file[len("```dockerfile"):].lstrip()
    
    # Remove ``` from the end
        if docker_file.endswith("```"):
         docker_file = docker_file[:-3].rstrip()  

        file.write(docker_file)

    print("\n🚀 Final Dockerfile has been saved to:", dockerfile_path)


if __name__ == "__main__":
    asyncio.run(run_agents())
