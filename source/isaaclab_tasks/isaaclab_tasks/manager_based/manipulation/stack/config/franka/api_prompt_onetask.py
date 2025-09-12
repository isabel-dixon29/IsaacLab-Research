from openai import OpenAI
import re
import subprocess

# Create the client to talk to Ollama running locally
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

class LLMClient:
    # def __init__(self, model_name="qwen3:8b"):
    #     self.model_name = model_name
    # def __init__(self, model_name="gemma3:1b"):
    #     self.model_name = model_name
    # def __init__(self, model_name="gemma3:12b"):
    #     self.model_name = model_name
    # def __init__(self, model_name="dolphin3:8b"):
    #     self.model_name = model_name
    def __init__(self, model_name="devstral:24b"):
        self.model_name = model_name
    # def __init__(self, model_name="codestral:22b"):
    #     self.model_name = model_name

    def read_file(self, file_path: str):
        """Reads a file."""
        with open(file_path, "r") as f:
            return f.read()

    def extract_code(self, text: str) -> str:
        """Extracts the Python code block (```python ...```) from the LLM code."""
        # Extract the first Python code block (```python ... ```)
        code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        return code_blocks[0] if code_blocks else text  # fallback to full text

    def output_file(self, file_path: str, output_file: str):
        """Reads a given file, connects to LLM through API and python code part of comment is written into a new file."""

        user_input = input("Please give a description of the environment: ")
        file_content = self.read_file(file_path)

        prompt = f"""

    Your task is to generate a single, valid Python file for an IsaacLab simulation. 
    This file's content should only differ from the reference file by the objects and configurations required for the user's task.
    Use the `@configclass` decorator for any Classes.

    ### Task description

    User description: {user_input}
    Think about which laboratory equipment from the original file would be used to complete the task in the user description.

    ### DoneTerm Definitions

    Create **exactly** 4 DoneTerms for  the TerminationsCfg class, following these specific rules:
        - Two terms for object dropping as shown in the given file, one for object1 and one for object2.
        - One of (Success Term):
            Final Subtask	DoneTerm Function	Required Parameters
            Placing object1 on object2	mdp.objects_stacked	"lower_object_cfg": SceneEntityCfg("object2")
            All other tasks	mdp.object_reached_goal	None
        - A time out term, the DoneTerm includes: func=mdp.time_out, time_out=True.

    ### ObsGroup/ObsTerm Definitions

    - Create an ObservationsCfg Class.
    - Within the ObservationsCfg Class, create two Classes: PolicyCfg and SubtasksCfg, inheriting from ObsGroup.

    - Inside the PolicyCfg, define ObsTerms for only the following **9** observation functions and no params: `last_action`, `joint_pos_rel`, `joint_vel_rel`, `object_obs`, 
    `object_positions_in_world_frame`, `object_orientations_in_world_frame`, `ee_frame_pos`, `ee_frame_quat`, `gripper_pos`.

    SUBTASK GENERATION RULES:
        Before generating any subtasks, analyze the specific action words in the user's task description for each task.
        The subtasks you generate must directly correspond to these specific actions.
        In SubtasksCfg, create a logical sequence of subtasks using ObsTerm for a robot to complete the user-defined task.
        - Task → Subtasks use object1 as the main object, object2 as apparatus.

    Available Subtask Functions & Parameters (func=):
        - **Core Subtasks**: reach_object, object_grasped, is_object_lifted, object_reached_midgoal, reach_object2 requires `object_cfg`
        - **Optional Subtasks (for a subtask involving pouring, in the following specific order)**: pouring_solution, reorient_object
        - **Final Termination Subtask** must include **one of** (ObsTerm(func=)): `object_stacked`, `object_near_goal`
        - Use reach_object2 for a second reach in a task

    Termination Function Rules:
        - `object_stacked` (used for tasks involving placing object1 onto apparatus) requires params: `upper_object_cfg`, `lower_object_cfg`
        - `object_near_goal` (used if `object_stacked` isn't applicable for final subtask) requires: `object_cfg`
        - **The termination function must be the final subtask for each sequence of subtasks**.

    Subtask Parameters:

    Parameter	Main Object	Apparatus/Glassware
    object_cfg	SceneEntityCfg("object1")	SceneEntityCfg("object2")
    upper_object_cfg	SceneEntityCfg("object1")	N/A
    lower_object_cfg	N/A	SceneEntityCfg("object2")

    General Parameter Mapping Rules:
        For any subtask parameter that refers to the main object (e.g., object_cfg, upper_object_cfg), always use SceneEntityCfg("object1").
        For any subtask parameter that refers to the apparatus (e.g., object_cfg (only for reach_object2), lower_object_cfg):
            If generating subtasks for Task, use SceneEntityCfg("object2").

    Logical Sequence Self-Correction:
    For each task sequence you generate, perform a logical check.
        Does the sequence begin by reaching for and grasping the main object (object1)?
        Does the sequence end with a termination function (object_stacked or object_near_goal)?
        For a stacking task, is there a reach_object2 to move to the apparatus immediately before the object_stacked termination?
        For a pouring task, is the pouring_solution and reorient_object subtask included?

    At the end of `ObservationsCfg` Class create instances for: `PolicyCfg` named policy and `SubtasksCfg` named subtasks.
    Within each of the `PolicyCfg` and `SubtasksCfg` instances, include terms: `enable_corruption`, `concatenate_terms` which are both `False`.
    Note: All of the functions for the ObsTerms and are from the folder mdp.

    ### Task Specific Objects

    - Use **only** objects defined in the original file — do **not invent new ones**.
    - Instantiate only the **Franka robot** and the **objects required** to complete the user-defined task.
    - **Do not use all of the objects from the original file**.
    - The **hot plate** object in the USD file refers to a **magnetic stir plate**.
    - The “main object” is the one moved within the task. You must decide which one that is based on the task description.
    - This main object will be a piece of glassware.

    In the output file:
        ***CRITICAL NAMING RULE — FOLLOW EXACTLY*** 
        For the task's **main object**, use this naming style:

        DO NOT USE THIS (placeholder style — REMOVE IT):  
        ```python
        self.scene.<glassware> = glassware.<glassware>
        ```
        INSTEAD, RENAME LIKE THIS (example if object1):
        ```python
        self.scene.object1 = glassware.<glassware>
        ```
        Do not include any placeholder code like <glassware> in your final output.
    - Replace <glassware> with the actual object name from the task, and assign it to a standardized scene name like object1.
    - Replace the lab equipment that is completing the task or is the target to follow the naming convention for object2 similar to above.
    - If there are two names for an instance, keep only the name involving object1.
    - Add a side comment indicating which objects were chosen as the main object and object2 for the task.

    Given/Original file to reference: {file_content}
    ```plaintext
    REMINDER: ALL object assignments **must use the format `self.scene.object1 = ...`** and **must not include placeholder code like `<glassware>`**.
    REMINDER: Do not use objects_stacked if both objects are **glassware**.
    REMINDER: `SubtasksCfg` **must include a Termination Function**.

    """

        response = client.chat.completions.create(
            temperature=0,
            model=self.model_name,
            stream=True,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        raw_response = ""
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                raw_response += delta.content

        print("\n\nFull response received.\n")
        code = self.extract_code(raw_response)

        with open(output_file, "w") as f:
            f.write(code)

        if "weigh" in user_input.lower():
            state_machine = "weigh_lab_sm"
        elif "pour" in user_input.lower():
            state_machine = "pour_lab_sm"
        else:
            state_machine = "stack_lab_sm"

        print(f"Extracted code saved to: {output_file}")

        terminal_code = [
            f"./isaaclab.sh",
            f"-p",
            f"scripts/environments/state_machine/{state_machine}.py",
            f"--num_envs",
            f"1",
            ]
        # Run another .py file automatically
        terminal_result = subprocess.run(terminal_code)

        return code


def main():
    file_name = "source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/stack/config/franka/stack_joint_pos_env_cfg.py"
    output_file = "source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/stack/config/franka/generated_llm.py"
    model_client = LLMClient()
    code = model_client.output_file(file_name, output_file)



if __name__ == "__main__":
    main()
