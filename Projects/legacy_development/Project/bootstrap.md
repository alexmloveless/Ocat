Based on this project file and the current state of the project based on LLM/project_state.md, this document will be used to bootstrap the Ocat project.

## How to use this document
- You will read this before starting ANY task to remind yourself of the core goals and principles of the project.
- You will read this regularly while in tasks to remind yourself of the core goals and principles of the project.

## Before you start ANY task or action
- Activate the ocat conda environment
- Read the contents of every file in Project/ carefully
- Use the appropriate git commands to check for recent commits and overall activity
- Create a new branch for your task, and commit your changes regularly

##  Housekeeping
- You will log your progress in the LLM/project_state.md file. This will be used to track the state of the project and to provide context for future development.
- Tasks should be broken down into small, manageable steps that can be completed in a single session.
- Tasks should be broken down into the most logical atomic state to minimise pressure on attention and context.
- You will not create any tasks that are not directly related to the core goals and principles of the project.
- You will not create any features or functionality that you were not explicitly asked to create, or that has been agreed by the user.
- You will not interact with ANY parts of the file-system outside the root of the Ocat package, except where explicitly requested by the user.
- You will always employ minimalist design principles while keep as close to best practise as possible.
- You will not use any libraries or tools that are not explicitly allowed by the user.
- All decision made by the user will be documented in the LLM/project_state.md file.
- The project state file as well as this file will be considered sacrosanct and maintained as accurately as possible.
- The file and the scope of the project will be updated as the project progresses, and you will not make any changes to this file without the user's permission.
- You will seek to minimise the number of non-code files in the project, and you will not create any files that are not directly related to the project or required for future development.;w

## What is Ocat?
Ocat is a terminal based chat client and a general purpose LLM back-end that is designed to be modular, extensible, and easy to use. It is primarily a chat client, but it will also have tooling and MCP (Multi-Chat Protocol) capabilities. Ocat is designed to be used as a command line tool, but it can also be imported and used in other Python applications.

Ocat seeks to provide a level of "state", "memory" and recall. Although this can and should be achievable by reprising old exchanges, it will also be able to store and retrieve exchanges from a vector store in real time creating a kind of ambient, episodic memory. One of the reasons for this is to minimise the length of the context load of the LLM making it more flexible, and reduce token usage. 

The ultimate goal is to provide the capability for a chatbot or agent to develop a personality and character, and to adapt over time to the user's preferences and needs. Ocat is not intended to be a one-size-fits-all solution, but rather a flexible and adaptable tool that can be tailored to the user's specific requirements.

Ocat is meant to be evolved, and seeks to facilitates the needs of its creator, rather than adhering to a particular use case. It may be open sourced at some point, but the initial purpose is its utility for the creator and their idiosyncrasies.

## Environment
- You will use the conda env "Ocat". If this is not present of the current device, you will create it and install all dependencies. The Ocat env will have python 12 installed.


## Implementation directives

- You have permission to access URLs but only those that I provide

## Ocat app definition

- The Ocat app is a primarily a chat client, but will have tooling and MCP capability
- Ocat is a python package that can be run as a command line tool
- The chat back-end will be implemented with langchain and langgraph
- The app will have a vector store for storing chat exchanges
- Each prompt/response exchange will be stored as a document in the vector store in real time 
- The app will implement the langgraph memory capability as per this url: https://langgraph.readthedocs.io/en/latest/guide/memory.html 
- The app will implement langgraph tools capability, but no tools will be implemented at this time: https://langchain-ai.github.io/langgraph/tutorials/get-started/2-add-tools/#5-create-a-function-to-run-the-tools
- Ocat's primary format for data exchange will be markdown, with provision for JSON and YAML
- Config will be by YAML file, with a default config file provided
- The user will be able to inspect the context being sent to the LLM in the CLI in real time. This can be enabled by:
    - In the config file
    - Enabling either INFO or DEBUG logging at app initiation which overrides the config setting
    - Changing the login in session via a slash command which overides the config setting and the cmd arg
- There will be a simple progress indicators for long-running operations

- each chat will be given a unique id
- each exchange will be given a unique id
- Only the text of each exchange will be stored denoted by the prompt response labels

## Core capabilities

### Vector storage

- Each time a user submits a prompt, the last n (as defined by vector_store_chat_window), will be used to query the vector store for similar documents. Documents with a similarity of n (as defined by exchange_context_results) or greater will be returned and used as context for the prompt. 
- Any items in the current chat will be ignored by the query

### LLM back end
- Model/providor agonostic
- Self-contained - no external dependencies
- No hardcoded values - maximally configurable. If the user will notice the effect of a setting, it should be configurable.

### Prompt reuse and templating

Users will be able to construct custom prompts, particularly system prompts, created from parts that are either available within Ocat, or that they provide. The prompts will be stored in text/markdown files. It will employ 

### INFO logging
- Show a truncated version of retrieved context in the CLI

### Debug and debug logging

Logging should be focussed on clarity and optimised to isolate problem areas as quickly as possible. Therefore errors should be unique and relate to  specific functions or code sections. 

Try/except loops should be wrapped around the smallest possible code block that can throw an error, and should be as specific as possible. **NEVER NEVER use catch-all exceptions!** 

Informational debug logging that exposes state, variables, object use, configurations etc. should be employed throughout the codebase. This should be used to provide insight into the state of the application at any given time, and should be used to help diagnose issues. 


### CLI "slash" Commands

- The app will have internal "slash" commands. Here are some examples:
  /attach: Attach up to 5 text files as context: /attach <file1> [file2] [file3] [file4] [file5]
  /clear: Clear conversation history: /clear
  /config: Show current configuration settings: /confighe 
  /delete: Remove n most recent exchanges: /delete [n=1]
  /exit: Exit the Ocat application: /exit
  /help: Show available commands: /help
  /history: Show chat history: /history
  /showsys: Show current system prompt: /showsys
  /vadd: Add a text document to the vector store: /vadd <text>
  /vdelete: Delete a document by ID: /vdelete <id>
  /vget: Retrieve a specific exchange by ID: /vget <id>
  /vquery: Query similar exchanges from vector store: /vquery <query> [k]
  /vstats: Display vector store statistics: /vstats
  /writecode: Extract code from last response: /writecode <filepath>
  /writejson: Export conversation to JSON: /writejson <filepath>
  /writemd: Export conversation to Markdown: /writemd <filepath>
  /writeresp: Export last exchange: /writeresp <filepath> [format=md|json]
  /model <model_name>: Change the LLM model used for response
  /showcontext: Toggle output of context in responses: /showcontext [on|off]
  /loglevel <level>: Set logging level (DEBUG, INFO, WARN, ERROR): /loglevel <level>


### CLI facets
- Ability to up-arrow to get previous inputs even across sessions

### RAG and attachments

### Ocat Configuration File

```yaml

# Ocat Configuration File

profile_name: "Ada"              # Name of the profile for this configuration (optional

# Model Configuration
model: "gpt-4o-mini"                    # Name of the model to use
temperature: 1.0                  # Controls randomness in responses (0.0-1.0)
max_tokens: 4000
system_prompt_files:              # List of files containing system prompts to concatenate
  - "/Users/alex/Dropbox/Vaults/Ada/sysprompts/Ada_by_ada_v1.md"  # Main system prompt file

# Vector Store Options (for Retrieval-Augmented Generation)
vector_store_enabled: true      # Enable the vector database for conversation memory
vector_store_path: /Users/alex/Dropbox/Projects/genai/enchillama/Ocat/vector_stores/bad_ada/
vector_similarity_threshold: 0.65  # Threshold for similarity matching (0.0-1.0)
vector_store_chat_window: 3

exchange_context_results: 5

user_label: "User"                # Label for user input
assistant_label: "Assistant"          # Label for assistant responses

# Display Options
no_rich: false                   # Disable rich text formatting
no_color: false                  # Disable ANSI color output

# Location aliases for commands
# Define shortcuts for commonly used directories
locations:
  conv: "~/Dropbox/Vaults/Ada/conversations/archive/ada_cli/"

```

You should also create a set of sensible settings for:
    - Embedding model and parameters
    - chunking and other vector store parameters

### CMD args
- Config file path: --config <path>
- Headless mode that provides args to:
    - add documents to the vector store
    - query the vector store

- Dummy mode that performs every action except the LLM call - returns a static response - for testing purposes
- Log level: --log-level <level> (default: WARN)


## User experience

The UI should follow a simple user/assistant model, where the user inputs a prompt and the assistant responds. The user should be able to see the context being sent to the LLM in real time, and should be able to interact with the app using slash commands. The app should be responsive and provide feedback on long-running operations.

There should be a config item to toggle whether responses are rendered on the same line as the label, or on a new line. The default should be on a new line.

Emphasis should be on clarity and a clutter from interface. The app should be easy to use and understand, with clear feedback on what is happening at all times. The app should be able to handle long-running operations without blocking the UI, and should provide progress feedback on these operations.

The creator is dyslexic, so the app should be designed with this in mind. This means that the app should be easy to read and understand, with clear feedback on what is happening at all times. This also means that plenty of space should be provided between elements, and that the app should be easy to navigate. High contrast in terms of colours and relative brightness should be used to ensure readability. 

The width of the CLI should be configurable, but should default to 80 characters. The app should be able to handle long lines of text without mid-word wrapping.

There should a clear and configurable delimiter between each exchange.

On start up, there should be a short but informative message that clearly shows the model being used, and where provided, the profile name from the config file. Here is an example:

╭────────────────────────────────────────────────────────────────────╮
│ Welcome to Ocat - Otherworldy Chats at (the) Terminal              │
│ Type your messages to chat with the LLM.                           │
│ Type /help to see available commands.                              │
│ Type /exit to quit the application.                                │
│ Model: gpt-4o-mini                                                 │
│ Profile: Ada                                                       │
╰────────────────────────────────────────────────────────────────────╯


- Colouring for "user" and "assistant" labels and emphasis
- markdown rendering for responses kept simple and clear
- Code highlighting

## Nice to haves
The items may be requested at a later date, but should be acknowledged now so that architectural decision can be made to support them.

- Vim key bindings
- File-system auto-completion
- Agent mode that can run semi-autonomously
- Copilot like functionality

## Design Principles
- NEVER use catch-all exceptions
- NEVER use catch-all exceptions
- NEVER use catch-all exceptions

- Golden rule: Explicit is better than implicit!

- Minimal/MVP
- Modular and extensible

- Use of type hints on all classes, methods, and functions
- Numpy style docstrings on all classes, methods, and functions

- Code spread across multiple files so that LLMs don't need to read the entire codebase to understand the app.
- You will prefer the most recent version of any give library or package except where this is incompatible with one of the core packages required by the project.

- Although the primary means of Ocat is a chat client via the terminal, it's capabilities should be available to be imported and incorporated into other python apps.

- You will clear up redundant code and files as you go, so that the codebase is always clean and tidy.
- Sensible defaults should be provided for all configuration options, but all options should be configurable via the config file.

## Vector Store 

The store schema should be minimal. Don't try and implement anything sophisticated. We will evolve over time. User prompts should be stored in the same object as the assistant's response with the two labels being used to differentiate between the two. Each object should also store the n prior user/assistant exchanges as context. The IDs for prior exchanges will be stored in the object within which they are referenced.

Every exchange should have a unique ID, but also a thread ID (for distinct chats where the user clears history between chats), and session ID (a session delineated). Exchanges, threads and sessions should be able to be queried by ID, and the vector store should be able to return exchanges by ID.

The default embedding model should be OpenAI's text-embedding-3-small, but this should be configurable in the config file. The vector store should be able to be queried by ID, and the vector store should be able to return exchanges by ID. Sensible default dimensions and chunk size should be provided, but these should also be configurable in the config file.

### Async Handling Patterns for LLM Calls

Core Principles
•  Non-blocking UI: The CLI interface must remain responsive during LLM calls
•  Graceful cancellation: Users should be able to interrupt long-running requests
•  Progress feedback: Clear indication of operation status and progress
•  Error resilience: Robust handling of network timeouts, API errors, and rate limits

### Cancellation Handling
•  Keyboard interrupt: Ctrl+C should cleanly cancel current operation
•  Timeout management: Configurable timeouts for different operation types

## LLM support

Ocat should be able to support any LLM that is compatible with the LangGraph framework. This includes Ollama, OpenAI, and any other LLM that can be integrated with LangGraph. The app should be able to switch between different LLMs without requiring changes to the codebase. At the outset, Ocat should at minimum support the following LLM families:

- OpenAI/GPT (default GPT-4o-mini)
- Gemini
- Claude

## Python version
- You should optimise for python version 3.12+. It does not need to be compatible with earlier versions of python.

## Preferred python libraries
The following libraries are preferred for this project, if and only if they have functionality required by the project. You may use other libraries if they are required to complete a task, but you should always prefer these libraries where possible.

- poetry # for package management
- pydantic
- FastAPI
- Rich # for CLI and output
- Pandas # for data manipulation
- Langchain/LangGraph # for LLM back-end
- Annoy # for vector store
- Mustache # for templating
- Ollama # for local models
- asyncio: Core async framework
- aiohttp: For async HTTP requests to LLM APIs
- prompt_toolkit: Already supports async input

## Testing

Testing should focus on validating edge functionality rather than exhaustive unit test coverage at component level. You must prove that the app still functions as expected after each change, but you do not need to write unit tests for every component. You will use pytest for testing. You will be asked to create a small suite of test scenarios that seeks to cover the widest range of functionality with the least amount of code. 

## Continuous Integration Strategy for Ocat

Given Ocat's nature as a CLI tool with LLM integrations, the CI strategy should focus on functional testing without requiring live API calls during builds.

GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: Ocat CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run tests with mocked LLM calls
      run: poetry run pytest tests/ -v --mock-llm
    
    - name: Check code formatting
      run: poetry run black --check .
    
    - name: Type checking
      run: poetry run mypy src/
    
    - name: Lint code
      run: poetry run ruff check .
```

Testing Strategy for CI
•  Mock LLM responses: Use pytest fixtures to mock all LLM API calls
•  Dummy mode testing: Leverage the planned "dummy mode" for integration tests
•  Vector store mocking: Use in-memory vector stores for testing
•  CLI simulation: Test slash commands and user interactions without real I/O

Key CI Considerations
•  No API keys required: All tests run with mocked responses
•  Fast execution: Tests complete in under 5 minutes
•  Comprehensive coverage: Focus on core functionality, error handling, and async patterns
•  Configuration validation: Test various config file scenarios
•  Cross-platform compatibility: Ensure CLI works on different terminals

Quality Gates
•  All tests must pass
•  Code coverage > 80% (focused on core logic)
•  No type errors from mypy
•  Code formatted with black
•  No linting violations

## Version control

You will use git for version control. You will commit your changes regularly, and you will not commit any code that does not work. You will use branches to manage your work, and you will merge your changes into the main branch when they are complete. You will not push any code to the main branch that does not work. You will use semantic versioning for the project, and you will update the version number in the __init__.py file when you make changes to the codebase.

## Completed tasks

- create the skeleton of a python package called "Ocat" that has the ability to be installed and run as a command line tool. The root of the package should be this directory. The build configuration should use poetry.
- use the Rich family of tools for the CLI as well as prompt_toolkit 
- don't use Click. All CLI functionality should be either Rich based or prompt_toolkit based.
- create a directory called LLM which contains files to enable you to quickly resume development in future. Document what has been done to date, the app directory structure, and any other relevant information. The aim is to allow you to complete dev tasks with as few tokens as possible.
