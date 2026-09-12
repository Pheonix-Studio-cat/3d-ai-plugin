# The other half of the link

The GitHub side of the connection is done: this repository names the model, and
the MCP server drives it.

The Hugging Face side is **not**, and cannot be done from a Claude Code session:
the Hugging Face connector available there reads the Hub, it does not write to
it. So the model card at
<https://huggingface.co/Chinook416/3d-gen-1> still says nothing about any of
this.

Closing that half takes about a minute in a browser — including on an iPad,
which is the point:

1. Open <https://huggingface.co/Chinook416/3d-gen-1/blob/main/README.md>
2. Press the pencil (**Edit**)
3. Paste the block below at the **top of the body**, directly under the closing
   `---` of the front matter and above the `<p style="text-align: center;">`
   line
4. **Commit** (straight to `main` is fine — it is a README)

Do **not** touch the front matter. In particular, do not add `base_model:` —
Hugging Face reads that field as a fine-tuning relationship and would put
`base_model:finetune:` on a repository that is a byte copy, which is a false
claim about the model. The relationship belongs in prose, which is what this
block is.

---

```markdown
> ## Running this model
>
> There is no inference endpoint for this repository. `text-to-3d` is not a
> task the Hugging Face Inference Providers serve, and this repository is a
> copy of [`MarcusLoren/MeshGPT-preview`](https://huggingface.co/MarcusLoren/MeshGPT-preview)
> rather than a model card — no provider serves a copy either.
>
> To generate a mesh from text with it, use
> **[3d-ai-plugin](https://github.com/Pheonix-Studio-cat/3d-ai-plugin)**. It
> starts a Hugging Face Job — a GPU rented by the second, on *your* account and
> *your* credit — which loads these weights, generates the mesh and writes the
> `.obj` to a dataset repository in your namespace.
>
> | | |
> | --- | --- |
> | Plugin and job script | <https://github.com/Pheonix-Studio-cat/3d-ai-plugin> |
> | MCP server | <https://github.com/Pheonix-Studio-cat/mcp-server> |
> | MCP address | `https://my-mcp-server.dean-hausmann.workers.dev/mcp` |
>
> **This is a copy, not new weights.** Everything below this block is the
> original author's model card, reproduced as it was. Credit for the model goes
> to MarcusLoren, and to [Phil Wang](https://github.com/lucidrains) for
> `meshgpt-pytorch`, after the MeshGPT paper
> ([arXiv:2311.15475](https://arxiv.org/abs/2311.15475)).
```

---

## While you are in there

Two other things are worth deciding about this repository, and neither is
urgent:

- **The card below the block is the original author's, word for word** — down
  to "Devoloped & trained by: Me" and the demo link to their Space. That is not
  a licence problem (Apache-2.0, and the attribution is intact), but anyone
  reading it will think this repository trained the model. The block above at
  least says otherwise before they get there.
- **`caracat-ai`, `caracat-pro` and `caracat-ai-karakal-2.0-pro`** are the same
  situation: copies of other people's weights taking up space under this
  account, one of them 685 GB. They are already listed as open questions in the
  memory repository under `projekte/caracat/07-offen.md`. `3d-gen-1` is the
  fourth. Worth deciding once for all four rather than four times.
