Using a Large Language Model through Ollama for Task Generation

Each of these api prompts connect to the LLM and saves the code to generated_llm.py.
The LLM prompt refers to stack_pos_env_cfg.py as a library of references.

For a single task generation:
- Run api_prompt_onetask.py

For two task generation:
- Run api.py

The user_input for the prompt is written in the terminal after the file is run.

The locations of the files are found below:
stack/
├── __init__.py
├── mdp
    ├── __init__.py
    ├── observations.py
    └── terminations.py
├── lab_env_cfg.py
└── config
    └── franka
        ├── agent
        ├── __init__.py  # <- this is where we register the environment and configurations to gym registry
        ├── api_prompt_onetask.py
        ├── api.py
        ├── generated_llm.py
        ├── glassware_files.py
        └── stack_pos_env_cfg.py
