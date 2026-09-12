# How it works, and what is actually verified

Two things live in this file: the chain from a prompt to an `.obj`, and an
honest line-by-line account of which parts of that chain have been checked
against reality and which have only been read out of documentation.

The second part matters more. This project has a written history of checks that
went green and proved nothing, and the way that keeps happening is by nobody
writing down which was which.

---

## The chain

```
 you                    the plugin              the Worker                 Hugging Face
 ───                    ──────────              ──────────                 ────────────
 "a wooden chair"
        │
        │  MCP over HTTP, Authorization: Bearer <your HF token>
        ├──────────────────────────────────────►
        │                                       │
        │                                       │ GET /api/whoami-v2
        │                                       ├──────────────────────────►
        │                                       │◄── { name: "you" }
        │                                       │
        │                                       │ POST /api/jobs/you
        │                                       │   command: uv run <this repo>/jobs/generate_3d.py …
        │                                       │   dockerImage: ghcr.io/astral-sh/uv:python3.12-bookworm
        │                                       │   flavor: t4-small, timeoutSeconds: 1200
        │                                       │   secrets: { HF_TOKEN: <your token> }
        │                                       ├──────────────────────────►
        │◄── job_id ────────────────────────────┤◄── { id, url, status }
        │                                                                   │
        │                                          a GPU is rented, on YOUR account
        │                                                                   │
        │                                          uv installs meshgpt-pytorch
        │                                          MeshTransformer.from_pretrained("Chinook416/3d-gen-1")
        │                                          transformer.generate(texts=[...])
        │                                          mesh_render.save_rendering("/tmp/generated.obj")
        │                                          upload_file → datasets/you/3d-gen-1-output
        │                                                                   │
        │  get_3d_job { job_id }                                            │
        ├──────────────────────────────────────►│ GET /api/jobs/you/<id>    │
        │◄── COMPLETED + result_url ────────────┤◄──────────────────────────┘
```

### Why a Job and not an inference call

Because there is nothing to call.

1. **`text-to-3d` is not a task the Hugging Face Inference Providers serve.**
   Their task list covers `text-to-image` and `text-to-video`; this is not on
   it.
2. **`Chinook416/3d-gen-1` is a copy, not a card.** It carries the same
   `README.md`, the same `config.json` and the same 1.2 GB
   `mesh-transformer.bin` as `MarcusLoren/MeshGPT-preview`. No provider serves
   a copy — and this copy has also lost the `transformers` /
   `endpoints_compatible` tags the original carries, so it is *less* servable
   than the original, not more.

So the model has to be run on a machine somebody rents. `generate_3d` rents one
for the length of one generation, on the account of whoever called it.

### Why the namespace is not a parameter

The job is created at `POST /api/jobs/{namespace}` and billed to that
namespace. If a caller could name it, a caller could try to spend someone
else's balance. It would fail on write permission — but a tool should not have
to be rescued by the far end. The Worker asks `whoami-v2` and uses the answer.

### Why the script URL is not a parameter

`uv run <url>` executes whatever is at that URL, on a rented machine, with the
caller's token in the environment. A parameter there would be "run arbitrary
code on this account". It is a constant in the Worker's source, pointing at one
file in this repository.

The same rule already applies to the Caracat tools in the same server, for the
same reason, and it is why that server's `fetch_url` was removed in September
2026.

### Why the token is in `secrets` and nowhere else

The container has to upload the finished `.obj`, so it needs a token, and job
secrets are the mechanism Hugging Face provides. That is one more place than
the Caracat tools allow themselves, and it is written down rather than waved
through: header and `secrets.HF_TOKEN`, never `environment`, never `command`,
never `labels`, never the reply. `checks/counterproof-3d.mjs` in the server
repository moves it into each of those and confirms the check notices.

---

## What is verified, and what is not

### Verified against a primary source

| Claim | How |
| --- | --- |
| `Chinook416/3d-gen-1` exists, is `text-to-3d`, Apache-2.0 | Hub API, read directly |
| It is a copy of `MarcusLoren/MeshGPT-preview` | both `README.md` and `config.json` read and compared; same `mesh-transformer.bin` |
| The copy lacks the original's `transformers` / `endpoints_compatible` tags | Hub metadata for both repos |
| `text-to-3d` is not an Inference Providers task | the providers' own task documentation |
| Jobs are pay-as-you-go and need a positive balance | `huggingface_hub` Jobs guide |
| Jobs HTTP API lives under `https://huggingface.co/api/jobs`, Bearer auth | `hub/jobs-reference.md` |
| `POST /api/jobs/{namespace}`, `GET …/{id}`, `POST …/{id}/cancel` | `huggingface_hub` source, `hf_api.py` |
| The job spec field names (`command`, `environment`, `secrets`, `flavor`, `timeoutSeconds`, `labels`, `dockerImage`) | `_create_job_spec` in `huggingface_hub/_jobs_api.py` |
| The namespace comes from `GET /api/whoami-v2` | `hf_api.py` |
| A URL script runs as `uv run <url> <args>` in `ghcr.io/astral-sh/uv:python3.12-bookworm` | `_create_uv_command_env_and_secrets` and `DEFAULT_UV_IMAGE` |
| The model card's usage: `MeshTransformer.from_pretrained(...)`, `mesh_render.save_rendering(...)` | the model card itself |
| The Worker builds exactly the command this script's parser accepts | the parser was run against the exact argument list the Worker emits |
| The Worker's behaviour under every branch above | `checks/check-3d.mjs`, counter-proved by `checks/counterproof-3d.mjs` against 14 deliberate breaks |

### Not verified — read, believed, never run

| Claim | Why it is open |
| --- | --- |
| **`meshgpt-pytorch` installs cleanly under `uv` with these dependencies** | never installed. The dependency line pins nothing but a git ref |
| **`MeshTransformer.from_pretrained("Chinook416/3d-gen-1")` loads** | never attempted. The copy may be missing a file the loader wants; if it is, the upstream original is the fallback |
| **`mesh_render.save_rendering` produces a usable `.obj`** | never run. The script checks for an empty file, which is a guard, not a proof |
| **A `t4-small` finishes inside the 20-minute timeout** | never timed. The model card's throughput figures are the only basis, and they are the original author's, not measured here |
| **The upload lands where the Worker predicts** | the URL shape is standard, but no file has been written |
| **The whole thing costs what one would guess** | no run, no bill, no number. Nothing in this repository states a price per generation, and nothing should until one has been paid |

**Why none of it could be verified here:** the session this was built in reaches
`huggingface.co` only through a read-only connector. Direct HTTPS to
`huggingface.co` is refused by the egress proxy, as are `*.hf.space` and
`*.workers.dev`. So the deployed Worker cannot be called from here either — the
checks import the handler and drive it with fabricated `Request` objects
instead, which is the established practice in this project and is why the
checks are worth something despite the address being unreachable.

### The first real run

Whoever does it should:

1. Start with `list_3d_models` — it costs nothing and confirms the address and
   the token plumbing work.
2. Then one `generate_3d` with `"prompt": "chair"` and `"flavor": "cpu-basic"`.
   Cheapest possible first attempt; it may hit the timeout, and that is still a
   useful result.
3. Read the job logs either way, at the `job_url`.
4. Write down what actually happened — including how long it took and what it
   cost — and strike the corresponding line out of the table above.

A row that moves from the second table to the first is worth more than a new
feature.
