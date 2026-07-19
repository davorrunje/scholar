# honest-scholar

*Research you can defend.*

**honest-scholar** helps you keep research honest — especially now that AI is in
the loop. You (not the AI) make and sign off every material decision, and you must
be able to explain and defend the work; the tool keeps the accounts, advises, and
probes. It **supports** honest, disclosable AI-assisted research — it does **not**
certify that any work is honest.

This package is the **CLI / tooling** behind the
[`honest-scholar` Claude Code plugin](https://github.com/davorrunje/honest-scholar).
The plugin (skills + methodology) stays pure-markdown; this package provides the
`honest-scholar` command it calls — `literature`, `dataset`, `defend`, `backlog`,
and `doctor` — installed **isolated**, so it never touches your project's ML
environment.

## Install

```bash
uv tool install honest-scholar     # recommended (isolated tool env)
# or: pipx install honest-scholar
# or: pip install honest-scholar

honest-scholar --version
honest-scholar doctor              # reports python / uv / rclone
```

Pre-releases are on TestPyPI (`--index-url https://test.pypi.org/simple/
--extra-index-url https://pypi.org/simple/`).

## CLI

```
honest-scholar --version
honest-scholar doctor                                           # environment report
honest-scholar literature resolve|cites|refs|enrich|neighbors   # citation graph (OpenAlex + S2)
honest-scholar dataset    validate|ingest|emit                  # manifest + Croissant
honest-scholar dataset    fetch|verify|mirror|audit             # SHA-256 retrieval + rclone mirror
honest-scholar defend     record                                # understanding-status record
honest-scholar backlog    park|add|list|rank|promote|drop       # exploration backlog
```

Every command is implemented and emits JSON (the skills parse it). Network- and
`rclone`-backed commands degrade gracefully when a key or the binary is absent.

## Learn more

- **Plugin, docs, and full design record:** <https://github.com/davorrunje/honest-scholar>
- **User guide:** <https://github.com/davorrunje/honest-scholar/blob/main/docs/USER-GUIDE.md>
- **Disclose your AI use & cite honest-scholar:** <https://github.com/davorrunje/honest-scholar/blob/main/DISCLOSURE.md>

## Status

Early / pre-release — see
<https://github.com/davorrunje/honest-scholar/blob/main/STATUS.md>.

## License

[Apache-2.0](https://github.com/davorrunje/honest-scholar/blob/main/LICENSE).
