# AI Headless Execution Wrappers

This repository contains lightweight wrappers designed to help AI coding agents (like Google Antigravity, Claude Code, Cursor, and OpenAI Codex) safely run and inspect Python and MATLAB plotting scripts in headless environments like remote HPC clusters or cloud servers.

## The Problem
For scientific computing, visualizing data is an important part of data analysis that serves to check ones work.
However, plotting can be very tedious, requiring sometimes dozens of lines of code.
For simple but tedious tasks like these, AI agents can greatly optimize an engineer's workflow.
However, when an AI agent tests a script that generates plots by running it in the terminal:
- **Python:** `plt.show()` blocks execution, waiting for a GUI window that never appears, freezing the agent.
- **MATLAB:** Opens a hidden figure, and the script completes, but the agent cannot see the visual output (or MATLAB crashes entirely on a headless node).

Agents often try to fix this by adding lines `matplotlib.use('Agg')` or `set(groot, 'DefaultFigureVisible', 'off')` into the script. However, then the script does not behave as the engineer originally intended when running it again interactively.

## The Solution
These wrappers execute your scripts as a *headless session subprocess*, automatically detecting and saving any plots the script generates into a local `ai_plots/` directory without modifying the script.

### Python Wrapper (`ai_run.py`)
- Automatically sets the `Agg` backend before any imports.
- Monkey-patches `plt.show()` to intercept and save figures to `ai_plots/`.
- **Smart Duplicate Avoidance:** Tracks if your script already explicitly saved a figure (e.g., via `savefig`), and skips making redundant copies.

**Usage:**
```bash
python3 ai_run.py <script_name.py>
```

### MATLAB Wrapper (`ai_run_matlab.py`)
- Locates your MATLAB executable and launches it with `-nodisplay -nosplash -batch`.
- Suppresses GUI windows at the session level (`set(groot, 'DefaultFigureVisible', 'off')`).
- **Smart Duplicate Avoidance:** Takes a snapshot of your directory's images before and after execution. If your script explicitly saved plots (via `saveas` or `exportgraphics`), it skips redundant copies. Otherwise, it detects open figures and saves them to `ai_plots/`.

**Usage:**
```bash
python3 ai_run_matlab.py <script_name.m>
```

These wrappers should work across different operating systems.

## How to Instruct Your AI Agent to Use These

To get the use of these wrappers, you need to tell your AI agent to *always* use these wrappers instead of running scripts directly. 

Add the following to your agent's system prompt, global instructions (e.g., `AGENTS.md`):

```markdown
# Python Plotting Guidelines
Whenever you (the AI agent) need to run or test a Python script that generates 
Matplotlib plots, use the global AI Wrapper:

    python3 /path/to/ai-headless-wrappers/ai_run.py <script_name.py>

# MATLAB Plotting Guidelines
Whenever you (the AI agent) need to run or test a MATLAB script:

    python3 /path/to/ai-headless-wrappers/ai_run_matlab.py <script_name.m>
```

By separating the execution wrappers from your research code, you allow the AI to act as a true autonomous collaborator—running experiments, inspecting outputs, and iterating—without interrupting your workflow or polluting your repository.

