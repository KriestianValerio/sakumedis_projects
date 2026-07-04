import os, json, re
import ollama # pip install ollama (do this before the flight!)
# ----------------------------------------------------------------------
# Config — your main modification dials
# ----------------------------------------------------------------------
MODEL = "llama3.1:8b" # any local model you pulled; see Section 12
WORKDIR = "agent_workspace" # the agent's sandbox folder
MAX_STEPS = 12 # hard stop so we never loop forever
os.makedirs(WORKDIR, exist_ok=True)

# ----------------------------------------------------------------------
# Tools (the "hands") — see Section 4 for the definitions
# ----------------------------------------------------------------------
def write_file(path, content):
    safe = os.path.join(WORKDIR, os.path.basename(path))
    with open(safe, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {safe}"

def read_file(path):
    safe = os.path.join(WORKDIR, os.path.basename(path))
    if not os.path.exists(safe):
        return f"ERROR: no such file {path}"
    return open(safe, encoding="utf-8").read()

def list_files(**_):
    files = os.listdir(WORKDIR)
    return "\n".join(files) if files else "(empty)"

def calculator(expression):
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"ERROR: {e}"
    
TOOLS = {
    "write_file": write_file,
    "read_file": read_file,
    "list_files": list_files,
    "calculator": calculator,
    }
# ----------------------------------------------------------------------
# System prompt — teaches the model the protocol (Option B from Section 5)
# ----------------------------------------------------------------------
SYSTEM_PROMPT = """You are a capable task-solving agent that works step by step.
You can use these tools:
- write_file(path, content): create/overwrite a text file
- read_file(path): read a file
- list_files(): list files in the working directory
- calculator(expression): evaluate a math expression

RULES:
- To use a tool, respond with ONLY a JSON object and nothing else:
{"tool": "<name>", "args": { ... }}
- After you see the tool result, decide your next step.
- When the whole task is finished, respond with ONLY:
{"done": true, "answer": "<your final summary to the user>"}
- Think about one step at a time. Do not invent tool results.
"""
# ----------------------------------------------------------------------
# Helper: pull the first JSON object out of a model reply (tolerant parser)
# ----------------------------------------------------------------------
def extract_json(text):
    # Models sometimes wrap JSON in ```json fences or add stray words.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
# ----------------------------------------------------------------------
# The agent loop — THIS is the agent (Sections 2 & 3)
# ----------------------------------------------------------------------
def run_agent(task):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for step in range(MAX_STEPS):
        # 1. BRAIN: ask the model what to do next
        resp = ollama.chat(model=MODEL, messages=messages,
            options={"temperature": 0})
        reply = resp["message"]["content"]
        messages.append({"role": "assistant", "content": reply})
        print(f"\n--- step {step+1} | model said ---\n{reply}")
    
    # 2. PARSE: is it a tool call or the final answer?
        action = extract_json(reply)
        if action is None:
        # Model went off-script; nudge it back to the protocol.
            messages.append({"role": "user",
                "content": "Please reply with ONLY a JSON tool call or a done object."})
            continue

        if action.get("done"):
            return action.get("answer", "(no answer given)")
        
    # 3. HANDS: run the requested tool
        name = action.get("tool")
        args = action.get("args", {})
        fn = TOOLS.get(name)
        if fn is None:
            observation = f"ERROR: unknown tool '{name}'"
        else:
            try:
                observation = fn(**args)
            except Exception as e:
                observation = f"ERROR running {name}: {e}"
        print(f"--- tool '{name}' -> ---\n{observation}")

        # 4. FEEDBACK: show the model the result, then loop
        messages.append({"role": "user",
            "content": f"TOOL RESULT for {name}:\n{observation}"})
    return "Stopped: hit the step limit without finishing."
# ----------------------------------------------------------------------

if __name__ == "__main__":
    task = ("Create a file called ideas.txt containing three startup ideas, "
        "one per line. Then read it back and tell me how many lines it has.")
    print("FINAL ANSWER:\n", run_agent(task))