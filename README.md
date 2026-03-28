# ComfyUI-VideoSlice — **ib video slicer**

Custom ComfyUI node that reads `.mov` / `.mp4` and outputs **one frame** as an **IMAGE** (plus sizes, counters, and a text readout).

### Before you copy commands

- **`YOUR_REAL_GITHUB_USERNAME`** (or any `YOUR_…` URL in this doc) is a **placeholder**. Use your real login, e.g. `https://github.com/octocat/ComfyUI-VideoSlice.git`. **Repository not found** means the URL is wrong or the repo was not created on GitHub yet.
- **`/workspace/...` paths are for RunPod (Linux pods) only.** On your **Mac**, that folder does not exist—use [Local Mac (no GitHub yet)](#local-mac-comfyui-no-github-yet) or your real Comfy path.
- **Do not paste whole blocks including lines that start with `#`** unless you know they are comments. If the shell says `command not found: #`, you pasted a comment line as a command.
- **`cd: too many arguments`:** Usually a bad paste (extra words on the `cd` line) or a “smart” `#` character. Run `cd` on its own line with **only** the path, in quotes if the path has spaces.

---

## Local Mac ComfyUI (no GitHub yet)

If the repo is not on GitHub yet, copy the folder into your local Comfy install:

```bash
# Example: adjust COMFY to where your ComfyUI lives
COMFY="$HOME/path/to/ComfyUI"
cp -R "/Users/ilyaduganov/Desktop/Comfy/Sliser__video/ComfyUI-VideoSlice" "$COMFY/custom_nodes/"
```

Then install deps with the **same** Python as Comfy:

```bash
cd "$COMFY/custom_nodes/ComfyUI-VideoSlice"
pip install -r requirements.txt
```

Restart ComfyUI.

---

## Install from GitHub (any machine)

1. Clone into ComfyUI’s `custom_nodes` folder (name must stay `ComfyUI-VideoSlice` or Comfy will still load it if the folder contains `__init__.py`):

   ```bash
   cd /path/to/ComfyUI/custom_nodes
   git clone https://github.com/YOUR_REAL_GITHUB_USERNAME/ComfyUI-VideoSlice.git
   ```

2. Install **opencv-python** with the **same Python / pip** that runs ComfyUI:

   ```bash
   cd ComfyUI-VideoSlice
   pip install -r requirements.txt
   ```

   Or run the helper (tries common RunPod venv paths; see [RunPod](#runpod-comfyui) below):

   ```bash
   bash install_deps.sh
   ```

3. **Restart ComfyUI** (full process restart, not only refresh).

---

## Publish this repo on GitHub

**Fastest (GitHub CLI):** install and log in once (`brew install gh`, then `gh auth login`), then from this repo:

```bash
bash create_github_repo.sh
```

That creates **`ComfyUI-VideoSlice`** under your GitHub user and pushes **`main`**.

---

From the folder that contains this README (skip **`git init`** if `.git` already exists):

```bash
git init
git add .
git commit -m "Initial commit: ib video slicer custom node"
```

On [github.com/new](https://github.com/new): create a repository named **`ComfyUI-VideoSlice`** (empty repo, no template). Skip **`git init`** below if this folder is already a git repo.

```bash
git branch -M main
git remote add origin https://github.com/YOUR_REAL_GITHUB_USERNAME/ComfyUI-VideoSlice.git
git push -u origin main
```

If you see **remote origin already exists**, do not run `remote add` again—update the URL:

```bash
git remote set-url origin https://github.com/YOUR_REAL_GITHUB_USERNAME/ComfyUI-VideoSlice.git
git push -u origin main
```

Replace **`YOUR_REAL_GITHUB_USERNAME`** with your GitHub login in every clone/push URL.

---

## RunPod ComfyUI

RunPod templates differ slightly; the idea is always: **node code in `custom_nodes/`**, **deps in Comfy’s Python**, **videos in `ComfyUI/input/`** or **`path_override`**.

### A. One-time setup on the pod

1. Open **Terminal** (or SSH) on the pod.
2. Find ComfyUI root (common cases):

   ```bash
   ls /workspace/ComfyUI/custom_nodes 2>/dev/null || ls /workspace/comfyui/custom_nodes 2>/dev/null
   ```

3. `cd` into **`custom_nodes`** on the pod (path varies by template; common: `/workspace/ComfyUI/custom_nodes`). Run **`cd` alone on one line**—no extra words after the path.

   ```bash
   cd /workspace/ComfyUI/custom_nodes
   git clone https://github.com/YOUR_REAL_GITHUB_USERNAME/ComfyUI-VideoSlice.git
   ```

   If that directory does not exist, find Comfy first: `find /workspace -maxdepth 4 -type d -name custom_nodes 2>/dev/null`

4. Install dependencies:

   ```bash
   cd ComfyUI-VideoSlice
   chmod +x install_deps.sh
   bash install_deps.sh
   ```

   If the script cannot find pip, locate Comfy’s venv and set **`COMFYUI_PIP`**:

   ```bash
   export COMFYUI_PIP=/workspace/ComfyUI/venv/bin/pip
   bash install_deps.sh
   ```

5. **Restart** the ComfyUI service / pod (per your template’s docs).

### B. Persistence

- Ephemeral disks: reinstall or clone into a **RunPod volume** mounted at e.g. **`/workspace`** so `custom_nodes` survives stop/start.
- Put large videos on the same volume; reference them with **`path_override`** or copy into **`ComfyUI/input/`**.

### C. Sharing with teammates

They use the **same `git clone` URL** into their pod’s `custom_nodes`, run **`install_deps.sh`** (or `pip install -r requirements.txt`), restart Comfy. No drag-and-drop install for the node itself—only media goes through the Comfy **Input** UI.

## Node: **ib video slicer**

**Category:** `video`  
**Type IDs:** `IBVideoSlicer` (new) or `VideoSliceFrame` (legacy saves — same node).

### Select / upload video (no separate button)

ComfyUI custom nodes cannot add a real “Upload” button in the graph. Use this workflow:

1. Open the **Input** sidebar in ComfyUI (or put files in `ComfyUI/input/` on the server).
2. **Drag-and-drop** your `.mp4` / `.mov` there (same as “upload”).
3. In the node, choose the file from the **video** dropdown.  
4. Optional: **path_override** = full server path (e.g. RunPod `/workspace/...`) to bypass the list.

After adding files, reload the page or run once; **IS_CHANGED** uses the input folder fingerprint so new files are noticed.

### Inputs

| Input | Description |
|--------|-------------|
| **video** | Dropdown of videos under ComfyUI `input/` (when any exist). |
| **path_override** | Full path overrides the dropdown. |
| **video_path** | Used when no videos are in `input/` (remote / empty input). |
| **random_frame** | On = pick a random frame from the slice list (ignores **current_frame_index** for selection). |
| **random_seed** | If random is on: **0** = different frame each run; **>0** = stable random for that seed. |
| **loop_on** | On = wrap **current_frame_index** with modulo (see **loop_every_n_frames**). |
| **loop_every_n_frames** | With loop on: **0** = wrap over the **full** slice list; **N > 0** = wrap only over the **first N** entries in that list. |
| **start_frame** / **end_frame** | Range in the file ( **end_frame** = **-1** = last frame ). |
| **skip_first_n_frames** | Added on top of **start_frame** before building the slice list. |
| **skip_every_n_frames** | **1** = every frame in range; **2** = every 2nd; **3** = every 3rd, … |
| **current_frame_index** | 0-based index into the slice list (ignored when random is on). |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| **image** | IMAGE | Selected frame (batch 1). |
| **image_width** / **image_height** | INT | Pixel size. |
| **slice_index** | INT | 0-based index into the slice list for this run. |
| **video_frame** | INT | Actual frame index inside the video file. |
| **frame_readout** | STRING | Human-readable status, e.g. `slice 3/120 | video frame 42 | sequential loop`. |

### Selection order

1. Build indices from **start** + **skip_first_n_frames** through **end**, stepping by **skip_every_n_frames**.
2. If **random_frame** → random **slice_index** (seeded if **random_seed** > 0).
3. Else if **loop_on** → `current_frame_index % window` (window from **loop_every_n_frames** as above).
4. Else → clamp **current_frame_index** to `[0, len(indices)-1]`.

### Migrating old workflows

Older graphs used **every_nth_frame**; the widget is now **skip_every_n_frames** (same meaning: 1 = all, 2 = every second, …). Re-open the node and set **skip_every_n_frames** to match the old value if you load an old JSON.

## Supported formats

- `.mp4`, `.mov`
