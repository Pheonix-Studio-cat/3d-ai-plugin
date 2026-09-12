# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = [
#   "torch",
#   "huggingface_hub>=0.34",
#   "meshgpt-pytorch @ git+https://github.com/MarcusLoppe/meshgpt-pytorch.git",
# ]
# ///
"""Generate a 3D mesh with 3d-gen-1 and push the .obj to a dataset repo.

This is the script a Hugging Face Job runs. It is never executed on the
caller's machine and never on a server: `hf jobs` rents a machine, runs this,
uploads the result and shuts the machine down again.

Why a Job and not an inference call
-----------------------------------
There is no endpoint to call. `text-to-3d` is not a task the Hugging Face
Inference Providers serve, and `Chinook416/3d-gen-1` is a byte copy of
`MarcusLoren/MeshGPT-preview` rather than a card — no provider serves a copy
either. Running this model means renting a machine for it, which is what this
script is for.

Who pays
--------
Whoever's token starts the Job. The Job runs in that account's namespace and
is billed to that account's credit balance, by the second. Nothing here holds
a token of its own: `HF_TOKEN` arrives as a Job secret, set by the caller.

Attribution
-----------
3d-gen-1 is a copy of MeshGPT-preview by MarcusLoren, built on
meshgpt-pytorch by Phil Wang (lucidrains), after the MeshGPT paper
(arXiv:2311.15475). Apache-2.0. The attribution is written into every .obj
this script produces, because a mesh file travels further than its README.

Status
------
**This script has never completed a real run.** It is written from the usage
section of the model card and from the huggingface_hub Jobs API, both read
directly, but the environment it was written in cannot reach huggingface.co
and cannot rent a GPU. The first person to run it should expect to fix
something; see `docs/HOW-IT-WORKS.md` in this repository for what is known to
be verified and what is not.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM = "MarcusLoren/MeshGPT-preview"

ATTRIBUTION = (
    "3d-gen-1 is a copy of MeshGPT-preview by MarcusLoren, built on "
    "meshgpt-pytorch by Phil Wang (lucidrains), after the MeshGPT paper "
    "(arXiv:2311.15475). Licensed Apache-2.0."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a 3D mesh with 3d-gen-1 and upload it.",
    )
    parser.add_argument(
        "--model",
        default="Chinook416/3d-gen-1",
        help="Model repo to load the transformer from.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="What to generate. Several objects: separate them with commas.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="0.0 is the model card's own example and the steadiest.",
    )
    parser.add_argument(
        "--output-repo",
        required=True,
        help="Dataset repo to write the .obj to, as owner/name.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Path inside that repo, e.g. generated/2026-09-12-chair.obj",
    )
    parser.add_argument(
        "--private",
        default="true",
        choices=("true", "false"),
        help="Create the output repo private if it does not exist. Default true.",
    )
    return parser.parse_args()


def log(message: str) -> None:
    """Job logs are the only window into a machine that no longer exists.

    Never log the token. It arrives as a Job secret and stays in the
    huggingface_hub call it is passed to.
    """
    print(message, flush=True)


def main() -> int:
    args = parse_args()

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        log(
            "ERROR: no HF_TOKEN. This job needs the caller's own token as a "
            "secret — it is what pays for this machine and what uploads the "
            "result."
        )
        return 2

    objects = [part.strip() for part in args.prompt.split(",") if part.strip()]
    if not objects:
        log("ERROR: the prompt names nothing to generate.")
        return 2

    # Imported here rather than at the top: the imports below cost a GPU
    # context and tens of seconds, and there is no reason to pay for them
    # before knowing the arguments are usable.
    import torch
    from huggingface_hub import HfApi
    from meshgpt_pytorch import MeshTransformer, mesh_render

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"Device: {device}")
    if device == "cpu":
        # Not an error — the model card puts CPU at roughly a quarter of GPU
        # speed — but a job that silently fell back to CPU and then timed out
        # would look like a broken model rather than a wrong flavor.
        log(
            "Running on CPU. The model card puts this at about 10 triangles/s "
            "against 40 on a 3060, so expect it to be slow or to hit the "
            "job timeout."
        )

    log(f"Loading {args.model} …")
    try:
        transformer = MeshTransformer.from_pretrained(args.model).to(device)
    except Exception as error:  # noqa: BLE001 - the message is the whole point
        log(f"ERROR: could not load {args.model}: {error}")
        log(
            f"If that repo is a copy without the files meshgpt-pytorch expects, "
            f"the upstream original is {UPSTREAM}."
        )
        return 1

    log(f"Generating {len(objects)} object(s) at temperature {args.temperature}: "
        f"{', '.join(objects)}")
    output = [transformer.generate(texts=objects, temperature=args.temperature)]

    local = Path("/tmp/generated.obj")
    mesh_render.save_rendering(str(local), output)
    if not local.exists() or local.stat().st_size == 0:
        # A silent empty file is the failure that looks like success. The
        # upload would go green and the caller would download nothing.
        log("ERROR: the renderer wrote no mesh.")
        return 1
    log(f"Wrote {local.stat().st_size} bytes.")

    # The attribution rides along inside the file. A .obj gets copied into
    # projects, engines and asset folders long after anyone reads the repo it
    # came from, and the licence follows the copy, not the README.
    header = "\n".join(
        [
            f"# Generated by 3d-gen-1 ({args.model}) on "
            f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}",
            f"# Prompt: {args.prompt}",
            f"# {ATTRIBUTION}",
            "# https://github.com/Pheonix-Studio-cat/3d-ai-plugin",
            "",
        ]
    )
    local.write_text(header + local.read_text(), encoding="utf-8")

    api = HfApi(token=token)
    log(f"Uploading to {args.output_repo}:{args.output_path} …")
    api.create_repo(
        repo_id=args.output_repo,
        repo_type="dataset",
        private=args.private == "true",
        exist_ok=True,
    )
    api.upload_file(
        path_or_fileobj=str(local),
        path_in_repo=args.output_path,
        repo_id=args.output_repo,
        repo_type="dataset",
        commit_message=f"3d-gen-1: {args.prompt}",
    )

    log(
        "Done: https://huggingface.co/datasets/"
        f"{args.output_repo}/resolve/main/{args.output_path}"
    )
    log(ATTRIBUTION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
