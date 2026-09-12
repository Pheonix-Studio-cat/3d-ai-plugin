---
name: generate-3d
description: Generate a 3D mesh (.obj) from a text prompt using the 3d-gen-1 model on Hugging Face. Use when someone asks for a 3D model, mesh, or .obj of an object from a description, or asks about a running 3d-gen-1 job. Generation rents a GPU on the user's own Hugging Face account, so always tell them before starting one.
---

# Generating a 3D mesh with 3d-gen-1

## The one thing to say before you start

**Every generation rents a GPU on the user's own Hugging Face account, billed
by the second.** Say so and get a yes before calling `generate_3d`. It is not a
free inference call, and there is no shared quota behind it.

If they have no credit, the job fails with a clear message rather than
silently: Jobs need a positive balance at
<https://huggingface.co/settings/billing>.

## The tools

| Tool | What it does |
| --- | --- |
| `list_3d_models` | What the model is and what it can do. Free, needs no token. |
| `generate_3d` | Starts a job. Returns a job id immediately. |
| `get_3d_job` | Status, and the `.obj` URL once it is done. |
| `cancel_3d_job` | Stops a running job and releases the machine. |

## How to run one

1. Call `list_3d_models` first if you are unsure whether the request is in
   scope. It costs nothing.
2. Call `generate_3d` with a short, plain prompt. One object per name:
   `chair`, `wooden table`, `ladder`. Several objects go in one prompt
   separated by commas — that is one job, not several, and cheaper than
   several.
3. It returns a `job_id` and comes straight back. **Do not busy-poll.**
   Generation takes minutes: the job installs `meshgpt-pytorch`, downloads the
   weights, and only then generates. Tell the user the id and check back rather
   than calling `get_3d_job` in a tight loop.
4. When `get_3d_job` reports `COMPLETED`, give the user the `result_url`.

## What this model can actually do

Per its model card, it was trained on about 4,000 objects of at most 250
triangles, with 800 text labels. That is the whole vocabulary.

- ✅ Single everyday objects: chair, table, bed, ladder, key, bench, shovel.
- ❌ Scenes, characters, anything detailed, anything with a specific style.
- ⚠️ Face orientation is known-wrong in this version; the model card says so.

If someone asks for a detailed asset, say plainly that this model will not
produce it rather than spending their money finding out.

## Choosing the machine

Default is `t4-small`. That is the right answer almost always.

- `cpu-basic` — cheapest, and the model card puts CPU at roughly a quarter of
  GPU speed. Fine for one small object; risks the 20-minute job timeout.
- `t4-small`, `t4-medium`, `l4x1`, `a10g-small` — GPUs, in rising order of cost.

A 184M-parameter transformer does not get meaningfully faster on a big machine.
Do not reach for a larger flavor to fix a slow job; check the logs instead.

## Where the result goes

A dataset repo in the user's own namespace, `<them>/3d-gen-1-output` by
default, created **private** if it does not exist. Pass `output_repo` to send
it somewhere else — it must be `owner/name`, and they must have write access.

## Attribution is not optional

`3d-gen-1` is a copy of
[`MarcusLoren/MeshGPT-preview`](https://huggingface.co/MarcusLoren/MeshGPT-preview),
built on [meshgpt-pytorch](https://github.com/lucidrains/meshgpt-pytorch) by
Phil Wang, after the MeshGPT paper (arXiv:2311.15475). Apache-2.0.

These are not new weights, and nobody should be told otherwise. The tools carry
the attribution in their output and the job writes it into every `.obj`
header — pass it along rather than stripping it.

## When something goes wrong

- **`ERROR` stage** — open the `job_url` and read the logs. The most likely
  causes are the weights not loading (the copy may be missing a file the
  original has) and the job hitting its timeout on CPU.
- **401/403** — the token needs write access to the user's own namespace.
- **402** — no credit. That is a billing page, not a bug.
- **Job still `RUNNING` after twenty minutes** — it will be stopped by its own
  timeout. `cancel_3d_job` stops it sooner.
