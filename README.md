# 3d-ai-plugin

Text to 3D mesh, from any MCP client, on **your own** Hugging Face account.

This plugin connects three things that already exist:

| | |
| --- | --- |
| the model | [`Chinook416/3d-gen-1`](https://huggingface.co/Chinook416/3d-gen-1) on Hugging Face |
| the server | [`Pheonix-Studio-cat/mcp-server`](https://github.com/Pheonix-Studio-cat/mcp-server), a Cloudflare Worker speaking MCP |
| the compute | a Hugging Face Job — a GPU rented by the second, on your account |

The MCP address:

```
https://my-mcp-server.dean-hausmann.workers.dev/mcp
```

## Install

As a Claude Code plugin, from this repository. Then set one environment
variable:

```bash
export HF_TOKEN=hf_...      # your own token, with write access to your namespace
```

That token is the whole billing arrangement. See **[Who pays](#who-pays)**.

Any other MCP client works too — the plugin is a thin wrapper around a remote
MCP server. Point the client at the address above and send the same header:

```json
{
  "mcpServers": {
    "3d-gen-1": {
      "type": "http",
      "url": "https://my-mcp-server.dean-hausmann.workers.dev/mcp",
      "headers": { "Authorization": "Bearer hf_..." }
    }
  }
}
```

## Use

| Tool | What it does |
| --- | --- |
| `list_3d_models` | what the model is, where it came from, what it can do. Free |
| `generate_3d` | starts a generation and returns a job id straight away |
| `get_3d_job` | how it is going, and the `.obj` URL once it is done |
| `cancel_3d_job` | stops a running job and releases the machine |

```
generate_3d  { "prompt": "wooden chair" }
  → job abc123…, result at
    https://huggingface.co/datasets/<you>/3d-gen-1-output/resolve/main/generated/….obj

get_3d_job   { "job_id": "abc123…" }
  → RUNNING … then COMPLETED, with the URL
```

Generation takes **minutes**, not seconds: the job installs `meshgpt-pytorch`,
downloads the weights, and only then generates. That is why it is three tools
and not one — an MCP call held open for ten minutes is a timeout in every
client.

## What the model can do

Per its model card, `3d-gen-1` was trained on roughly 4,000 objects of at most
250 triangles, with 800 text labels.

- ✅ single everyday objects — chair, table, bed, ladder, key, bench
- ❌ scenes, characters, detailed or styled assets
- ⚠️ face orientation is wrong in this version; the model card says so

## Who pays

**You do, on your own Hugging Face credit.** There is no shared quota here and
no key held by anyone else.

The chain is deliberately arranged so that nothing in the middle can spend
anyone else's money:

1. The plugin sends **your** token as `Authorization: Bearer`.
2. The Worker holds **no token of its own**, and never has. It reads yours from
   the header.
3. It asks Hugging Face `whoami-v2` whose token it is, and starts the job in
   **that** namespace. There is no parameter for the namespace, on purpose.
4. Hugging Face rents the machine to that account and bills it by the second.

You need:

- a Hugging Face token with **write access to your own namespace**;
- a **positive credit balance** — <https://huggingface.co/settings/billing>.
  Jobs are pay-as-you-go; the Inference Providers free tier does not apply.

Costs are per second of machine time. Current rates:
<https://huggingface.co/docs/hub/jobs-pricing>. Default machine is the smallest
GPU (`t4-small`), every job has a 20-minute timeout, and the large flavors are
not offered — a typo should cost small change.

`cancel_3d_job` is the one call here that saves money. A job rents its machine
until it finishes or times out.

## What is in this repository

| Path | What it is |
| --- | --- |
| `jobs/generate_3d.py` | the script the rented machine runs. A self-contained UV script |
| `.mcp.json` | the MCP server entry, with `${HF_TOKEN}` expanded from your environment |
| `.claude-plugin/plugin.json` | the plugin manifest |
| `skills/generate-3d/SKILL.md` | how an assistant should use the tools, and when not to |
| `docs/HOW-IT-WORKS.md` | the whole chain, and **what has and has not been verified** |
| `docs/model-card-snippet.md` | the one step left, which needs a browser: linking back from the model card |

The MCP tools themselves live in the server repository, in
[`src/threed.ts`](https://github.com/Pheonix-Studio-cat/mcp-server/blob/main/src/threed.ts) —
one source, not a copy that drifts.

## Status

> ⚠️ **The job has never completed a real run.**
>
> The MCP tools are checked against the real handler and counter-proved against
> fourteen deliberate breaks. The job script's arguments are verified against
> exactly what the server sends. But no GPU has been rented and no `.obj` has
> been produced: the environment this was built in reaches `huggingface.co`
> only through a read-only connector and cannot start a Job.
>
> `docs/HOW-IT-WORKS.md` lists line by line what is verified and what is not.
> Whoever runs it first should expect to fix something.

## Attribution

`3d-gen-1` is a **copy** of
[`MarcusLoren/MeshGPT-preview`](https://huggingface.co/MarcusLoren/MeshGPT-preview) —
same README, same `config.json`, same weights file. It is built on
[meshgpt-pytorch](https://github.com/lucidrains/meshgpt-pytorch) by Phil Wang
(lucidrains), after the MeshGPT paper ([arXiv:2311.15475](https://arxiv.org/abs/2311.15475)).

These are not new weights. Everything here says so, and the job writes the
attribution into every `.obj` it produces — a mesh file travels further than
the repository it came from.

## Licence

Apache-2.0. See [`LICENSE`](LICENSE).
