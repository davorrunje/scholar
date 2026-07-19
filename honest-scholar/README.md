# Honest Scholar

*Research you can defend.*

**Honest Scholar** helps you keep research honest — especially now that AI is in
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

**Documentation:** <https://honest-scholar.science/>

## CLI

```
honest-scholar --version
honest-scholar doctor                                           # environment report
honest-scholar literature resolve|cites|refs|enrich|neighbors   # citation graph (OpenAlex + S2)
honest-scholar dataset    validate|ingest|emit                  # manifest + Croissant
honest-scholar dataset    fetch|verify|mirror|audit             # SHA-256 retrieval + rclone mirror
honest-scholar defend     record                                # understanding-status record
honest-scholar backlog    park|add|list|rank|promote|drop       # exploration backlog
honest-scholar keys       set|list|check|unset|path             # API-key & credential store
```

Every command is implemented and emits JSON (the skills parse it). **Failures are
surfaced honestly:** a rate-limit or transient network error is retried with
backoff (honoring `Retry-After`) and, if it persists, reported as a distinct,
actionable message — never a silent "not found" and never a traceback. A missing
API key or `rclone` binary is reported cleanly, and an optional key (e.g.
`S2_API_KEY`) simply lifts the rate ceiling — see
[API keys & credentials](#api-keys--credentials).

## API keys & credentials

Some services throttle hard without a key. Providing one is optional (the tooling
degrades gracefully) but lifts the ceiling:

| Key | Service | What it buys | How to obtain |
|---|---|---|---|
| `S2_API_KEY` | Semantic Scholar | Rate limit well above the shared keyless pool. | <https://www.semanticscholar.org/product/api#api-key> |
| `OPENALEX_MAILTO` | OpenAlex | The "polite pool" (a contact email) — faster, more reliable. | <https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication> |
| `RCLONE_CONFIG_<REMOTE>_*` | Private dataset mirror | rclone remote credentials passed as scoped env vars (no config file). | Per your rclone remote. |

Keys live in a **CLI-managed JSON store** at `.honest-scholar/keys.json`
(gitignored, created `0600`), read with **`os.environ` > store > unset**
precedence, so an environment variable always wins. Manage it with `keys`:

```bash
honest-scholar keys set S2_API_KEY        # hidden prompt, or reads piped stdin
echo "$MY_KEY" | honest-scholar keys set S2_API_KEY
honest-scholar keys set < keys.json       # a JSON object sets many at once
honest-scholar keys list                  # presence + source (never the value)
honest-scholar keys check | unset | path
```

The value is read only from stdin or a hidden prompt — never `argv` — so it never
hits your shell history or the process list, and `list`/`check`/`doctor` report
presence only.

> **Plaintext at rest.** The store is **not encrypted**; gitignore + `0600` limit
> exposure but are not a vault. OS-keychain backing is a planned follow-up (#49).

## Learn more

- **Documentation:** <https://honest-scholar.science/>
- **User guide:** <https://honest-scholar.science/get-started/user-guide>
- **Plugin, source & full design record:** <https://github.com/davorrunje/honest-scholar>
- **Disclose your AI use & cite Honest Scholar:** <https://github.com/davorrunje/honest-scholar/blob/main/DISCLOSURE.md>

## Changelog

<https://github.com/davorrunje/honest-scholar/blob/main/CHANGELOG.md>

## License

[Apache-2.0](https://github.com/davorrunje/honest-scholar/blob/main/LICENSE).
