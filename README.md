# ComfyUI-VideoSlice — **ib video slicer**

Custom ComfyUI node that reads `.mov` / `.mp4` and outputs **one frame** as an **IMAGE** (plus sizes, slice index, and file frame counters).

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

RunPod templates differ slightly; the idea is always: **node code in `custom_nodes/`**, **deps in Comfy’s Python**, **videos in `ComfyUI/input/`** (upload or copy).

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
- Put large videos on the same volume; place them under **`ComfyUI/input/`** (or a subfolder) so they appear in the **video** dropdown.

### C. Sharing with teammates

They use the **same `git clone` URL** into their pod’s `custom_nodes`, run **`install_deps.sh`** (or `pip install -r requirements.txt`), restart Comfy. No drag-and-drop install for the node itself—only media goes through the Comfy **Input** UI.

---

## Comfy Registry (shows in ComfyUI-Manager)

There is no separate “merge into ComfyUI’s GitHub list” flow. **Discoverability** for installs like *Manager → Install Custom Nodes* comes from the **[Comfy Registry](https://registry.comfy.org/)**, which ComfyUI-Manager uses.

1. **Create a publisher** at [registry.comfy.org](https://registry.comfy.org/) (your **Publisher ID** is fixed; it appears after `@` on your profile).
2. **Create a Registry publishing API key** under [registry.comfy.org/nodes](https://registry.comfy.org/nodes) (not a normal GitHub token).
3. **`PublisherId`** is set in **`pyproject.toml`** (registry **ftfftft**).
4. Install **[comfy-cli](https://docs.comfy.org/comfy-cli/getting-started)** and publish:

   ```bash
   comfy node publish
   ```

   **GitHub Actions (auto-publish):** [Comfy-Org/publish-node-action](https://github.com/Comfy-Org/publish-node-action). Repo secret name used here: **`REGISTER_ACTION_COMFYUI`** (Comfy Registry publishing key from [registry.comfy.org/nodes](https://registry.comfy.org/nodes)). Workflow: [`.github/workflows/publish-to-comfy-registry.yml`](.github/workflows/publish-to-comfy-registry.yml) — on push to **`main`** when **`pyproject.toml`** changes, or **workflow_dispatch**. Bump **`version`** in `pyproject.toml` for each release.

   **If `git push` rejects workflow files:** your **GitHub** PAT needs the **`workflow`** scope (this is not the registry secret).

5. After publish, users can install via Manager / `comfy node install ib-video-slicer` (see registry for the exact id).

Docs: [Publishing nodes](https://docs.comfy.org/registry/publishing), [pyproject spec](https://docs.comfy.org/registry/specifications).

## Node: **ib video slicer** (v1.1)

**Category:** `video` · **Type IDs:** `IBVideoSlicer` / `VideoSliceFrame`.

### Video

- **choose file to upload** — one button; uploads `.mp4`/`.mov` into `input/` (same API as image upload); refreshes the **video** list.
- **video** — file under `input/` (relative path / subfolders allowed).

### Inputs

| Input | Description |
|--------|-------------|
| **frame_mode** | **increment** / **decrement** / **random** over the slice list (per-video index state; **random** uses a new internal seed each run). |
| **lag_on** | ~50%: random `Δ ∈ {-3,-2,-1,1,2,3}` in **slice-index** space, clamped; each time lag **applies**, `Δ` is never the same as the last applied `Δ` for that video. |
| **loop_on** / **loop_every_n_frames** | Wrap window for increment/decrement. |
| **start_frame** … **skip_every_n_frames** | Build slice list (from **start** through **end**, step **skip_every_n**). |

### Outputs

| Output | Meaning |
|--------|---------|
| **image**, **image_width**, **image_height** | Usual IMAGE outputs. |
| **total_frames_count** | **INT** — `CAP_PROP_FRAME_COUNT` for the file (total frames reported by the container/decoder). |
| **slice_index** | **INT** — index in the **slice list** (0…n−1 after start/end/skip-every-n). |

### Slice list

Range from **start** through **end** (`-1` = last), step **skip_every_n**. Then **frame_mode** + optional **lag**.

**Breaking:** old widgets **random_frame**, **random_seed**, **current_frame_index** removed — use **frame_mode** and **lag_on**. Saved **every_nth_frame** is still read if present.

### Migrating old workflows

Older graphs used **every_nth_frame**; the widget is now **skip_every_n_frames** (same meaning: 1 = all, 2 = every second, …). Re-open the node and set **skip_every_n_frames** to match the old value if you load an old JSON.

## Supported formats

- `.mp4`, `.mov`
