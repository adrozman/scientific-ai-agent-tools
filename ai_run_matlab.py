#!/usr/bin/env python3
"""
AI MATLAB Headless Runner Wrapper
Matches the behavior of ~/.gemini/scripts/ai_run.py for MATLAB scripts.

Usage:
    python3 ~/.gemini/scripts/ai_run_matlab.py <script_name.m>

How it works:
1. Locates the real MATLAB executable (loading environment if needed).
2. Sets `DefaultFigureVisible` to 'off' at the session level so NO GUI windows pop up.
   The user's script can remain interactive (using normal `figure`, `plot`, etc.).
3. Executes the user's script.
4. Auto-detects all generated figures (`findall(groot, 'Type', 'figure')`) and saves
   them to PNG files with informative names (based on figure title/number).
5. Closes all figures.
"""

import sys
import os
import shutil
import subprocess

if len(sys.argv) < 2:
    print("Usage: python3 ~/.gemini/scripts/ai_run_matlab.py <script_name.m>")
    sys.exit(1)

target_script = sys.argv[1]
abs_path = os.path.abspath(target_script)

if not os.path.exists(abs_path):
    print(f"[AI Wrapper] Error: File '{abs_path}' does not exist.")
    sys.exit(1)

script_dir = os.path.dirname(abs_path)
base_name = os.path.basename(abs_path)
if base_name.endswith('.m'):
    base_name = base_name[:-2]

# Resolve real MATLAB executable
matlab_exe = shutil.which("matlab")
if not matlab_exe or matlab_exe == "/usr/local/bin/matlab":
    candidates = [
        "/share/pkg.8/matlab/2026a/install/bin/matlab",
        "/share/pkg.8/matlab/2025b/install/bin/matlab",
        "/share/pkg.8/matlab/2024b/install/bin/matlab",
    ]
    import glob
    # macOS standard install locations
    candidates.extend(sorted(glob.glob("/Applications/MATLAB_R*.app/bin/matlab"), reverse=True))
    # Windows standard install locations
    candidates.extend(sorted(glob.glob(r"C:\Program Files\MATLAB\R*\bin\matlab.exe"), reverse=True))
    for c in candidates:
        if os.path.exists(c):
            matlab_exe = c
            break

if not matlab_exe:
    matlab_exe = "matlab"

# Normalize path with forward slashes for MATLAB string literals across Linux, macOS, and Windows
script_dir_matlab = script_dir.replace("\\", "/")

matlab_commands = (
    f"cd('{script_dir_matlab}'); "
    f"addpath('{script_dir_matlab}'); "
    f"set(groot, 'DefaultFigureVisible', 'off'); "
    f"img_exts = {{'*.png','*.jpg','*.jpeg','*.pdf','*.eps','*.svg','*.fig','*.tif'}}; "
    f"pre_map = containers.Map(); "
    f"for ext = img_exts, "
    f"  d = dir(fullfile(pwd, ext{{1}})); "
    f"  for k = 1:numel(d), pre_map(d(k).name) = d(k).datenum; end; "
    f"end; "
    f"fprintf('[AI Wrapper] Executing {base_name}.m headless...\\n'); "
    f"tic; "
    f"{base_name}; "
    f"elapsed = toc; "
    f"fprintf('[AI Wrapper] Script completed in %.2f s\\n', elapsed); "
    f"new_images = {{}}; "
    f"for ext = img_exts, "
    f"  d = dir(fullfile(pwd, ext{{1}})); "
    f"  for k = 1:numel(d), "
    f"    if ~isKey(pre_map, d(k).name) || d(k).datenum > pre_map(d(k).name), "
    f"      new_images{{end+1}} = d(k).name; "
    f"    end; "
    f"  end; "
    f"end; "
    f"figs = findall(groot, 'Type', 'figure'); "
    f"if isempty(figs), fprintf('[AI Wrapper] No figures found.\\n'); end; "
    f"if ~isempty(new_images), "
    f"  fprintf('[AI Wrapper] Script saved %d plot(s) directly to disk:\\n', numel(new_images)); "
    f"  for k = 1:numel(new_images), fprintf('  -> %s\\n', fullfile(pwd, new_images{{k}})); end; "
    f"  fprintf('[AI Wrapper] Skipping redundant copy to ai_plots/.\\n'); "
    f"elseif ~isempty(figs), "
    f"  plot_dir = fullfile('{script_dir_matlab}', 'ai_plots'); "
    f"  if exist(plot_dir, 'dir'), delete(fullfile(plot_dir, '*')); else, mkdir(plot_dir); end; "
    f"  for idx = 1:numel(figs) "
    f"    f = figs(idx); "
    f"    t_str = ''; "
    f"    if isprop(f, 'Name') && ~isempty(f.Name), t_str = f.Name; "
    f"    else "
    f"      ax = findall(f, 'Type', 'axes'); "
    f"      for a_i = 1:numel(ax) "
    f"        if ~isempty(ax(a_i).Title) && ~isempty(ax(a_i).Title.String) "
    f"          s = ax(a_i).Title.String; if iscell(s), s = s{{1}}; end; "
    f"          if ~isempty(s), t_str = s; break; end; "
    f"        end; "
    f"      end; "
    f"    end; "
    f"    safe_title = regexprep(t_str, '[^a-zA-Z0-9]', '_'); "
    f"    safe_title = regexprep(safe_title, '_+', '_'); "
    f"    if length(safe_title) > 30, safe_title = safe_title(1:30); end; "
    f"    safe_title = regexprep(safe_title, '^_|_$', ''); "
    f"    if isempty(safe_title), fname = sprintf('ai_plot_%d.png', f.Number); "
    f"    else, fname = sprintf('ai_plot_%d_%s.png', f.Number, safe_title); end; "
    f"    full_fname = fullfile(plot_dir, fname); "
    f"    saveas(f, full_fname); "
    f"    fprintf('[AI Wrapper] Saved unsaved figure -> %s\\n', full_fname); "
    f"  end; "
    f"end; "
    f"close all;"
)

if sys.platform == "win32":
    # On Windows, MATLAB does not support -nodisplay (X11 flag).
    # Instead, use -nodesktop -noFigureWindows -nosplash -batch for headless run.
    cmd = [matlab_exe, "-nodesktop", "-noFigureWindows", "-nosplash", "-batch", matlab_commands]
else:
    cmd = [matlab_exe, "-nodisplay", "-nosplash", "-batch", matlab_commands]

print(f"[AI Wrapper] Launching MATLAB ({matlab_exe}) headless for {abs_path}...")
try:
    result = subprocess.run(cmd, cwd=script_dir, check=True)
    sys.exit(result.returncode)
except subprocess.CalledProcessError as e:
    print(f"[AI Wrapper] Error: MATLAB exited with code {e.returncode}")
    sys.exit(e.returncode)
