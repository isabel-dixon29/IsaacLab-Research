Using a Large Language Model through Ollama for Task Generation

For a single task generation:
- Run api_prompt_onetask.py

For two task generation:
- Run api.py

Each of these api prompts connect to the LLM and saves the code to generated_llm.py.

The locations of the files are found below:
stack/
├── __init__.py
├── mdp
├── lab_env_cfg.py
└── config
    ├── franka
    │   ├── agent
    │   ├── __init__.py  # <- this is where we register the environment and configurations to gym registry
    │   ├── api_prompt_onetask.py
    │   ├── api.py
    │   └── generated_llm.py
    ├── __init__.py
    └── velocity_env_cfg.py
