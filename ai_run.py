#!/usr/bin/env python3
"""
AI Python Headless Runner Wrapper
Executes Python scripts containing Matplotlib plots in a headless environment.
Auto-detects and saves figures to an `ai_plots/` directory for AI inspection,
while avoiding redundant saves if the script explicitly writes plots to disk.

Usage:
    python3 ~/.gemini/scripts/ai_run.py <script_name.py>
"""
import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.figure

# Track figures that the script explicitly saves
original_savefig = matplotlib.figure.Figure.savefig
saved_figures = set()

def tracked_savefig(self, *args, **kwargs):
    saved_figures.add(self.number)
    return original_savefig(self, *args, **kwargs)

matplotlib.figure.Figure.savefig = tracked_savefig

def headless_show(*args, **kwargs):
    print("\n[AI Wrapper] Intercepted plt.show()")
    fignums = plt.get_fignums()
    if not fignums:
        print("[AI Wrapper] No figures to save.")
        return
        
    for i in fignums:
        if i in saved_figures:
            print(f"[AI Wrapper] Figure {i} was already saved by script. Skipping duplicate.")

    unsaved_fignums = [i for i in fignums if i not in saved_figures]
    if not unsaved_fignums:
        print("[AI Wrapper] All figures were already saved by the script. No redundant copies in ai_plots/.")
        plt.close('all')
        return

    import os, glob
    target_script = sys.argv[0] if len(sys.argv) > 0 else ""
    script_dir = os.path.dirname(os.path.abspath(target_script)) if target_script else os.getcwd()
    plot_dir = os.path.join(script_dir, "ai_plots")
    
    if os.path.exists(plot_dir):
        for f in glob.glob(os.path.join(plot_dir, "*")):
            try: os.remove(f)
            except: pass
    else:
        os.makedirs(plot_dir, exist_ok=True)

    for i in unsaved_fignums:
        fig = plt.figure(i)
        title = fig._suptitle.get_text() if fig._suptitle else ""
        if not title and fig.axes:
            title = fig.axes[0].get_title()
        
        safe_title = "".join([c if c.isalnum() else "_" for c in title]).strip('_')[:30]
        filename = os.path.join(plot_dir, f"ai_plot_{i}_{safe_title}.png".replace('__', '_').rstrip('_'))
        fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"[AI Wrapper] Saved unsaved figure -> {os.path.abspath(filename)}")
    plt.close('all')

plt.show = headless_show

if len(sys.argv) < 2:
    print("Usage: python ~/.gemini/scripts/ai_run.py <script.py>")
    sys.exit(1)

target_script = sys.argv[1]
sys.argv = sys.argv[1:]

script_dir = os.path.dirname(os.path.abspath(target_script))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

with open(target_script, 'r') as f:
    code = f.read()

print(f"[AI Wrapper] Executing {target_script} headless...")
exec(code, {'__name__': '__main__', '__file__': target_script})
