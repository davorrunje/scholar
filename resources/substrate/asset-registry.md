# Asset-provenance substrate

`literature` and `dataset` are distinct front-ends over one shared substrate: a
git-committed registry of externally-sourced, persistently-identified,
license-bearing, mirror-able assets, plus the machinery to materialize and verify
durable copies. They share the **mechanism**, not the **file**.
(Design: `docs/design/04-substrate-and-contract.md` §2; ADR-0011, ADR-0012.)

## Base asset record (the spine)

Every asset (a PDF for `literature`, a data file for `dataset`) conforms to this
base; each front-end extends it.

| Field | Meaning |
|---|---|
| `id` | stable slug, unique within the registry |
| `pid` | persistent identifier — DOI / arXiv-id / DataCite DOI (preferred) |
| `title` / `description` | human labels |
| `source` | canonical URL / API locator, or acquisition instructions |
| `files[]` | each: `path`, `checksum` (`sha256:…`), `size` |
| `license` | SPDX id or explicit terms + URL |
| `redistributable` | bool — may we republish the bytes? |
| `access` | `open` \| `gated` |
| `mirror` | logical rclone remote + content-addressed key (present iff mirrored) |
| `citation` | DataCite 6-tuple when a citable record exists |

- **`literature`** extends with bibliographic fields + a triage sidecar; its file
  format is CSL-JSON + YAML (ADR-0008, ADR-0020), not this manifest.
- **`dataset`** extends with `tier`, a `retrieval` recipe, `datasheet`,
  `sensitivity`; its file is `datasets.yml`.

## Persistent-ID & citation

One shared module resolves/records persistent identifiers (DOI/arXiv/DataCite) and
emits citations. Papers and datasets are both DOI-citable; the same code fills
`pid`/`citation` and is the seam to external archives (Zenodo/figshare/Dryad) and
to Croissant/BibTeX export.

## Private mirror + fixity

- **Engine: `rclone`** (subprocess; a single Go binary, **not** a Python dep).
  Backend-agnostic (Google Drive first; S3/B2/R2/SFTP/WebDAV/… by config). The
  registry names a **logical remote + base path**; the credential-bearing
  `rclone.conf` is **never committed** (untracked file via `RCLONE_CONFIG`, or
  env-var remotes from CI secrets). Ship a `rclone.conf.example` (name/type only).
  `rclone obscure` is not encryption and is never committed.
- **Fixity — two layers.** The **authoritative checksum is SHA-256, stored in the
  registry** (integrity == identity == citation-verifiability). rclone's native
  per-backend hash (often MD5 on Drive/S3) is only a transport check; after any
  transfer, **re-hash the local bytes against the registry SHA-256** — so
  verification is backend-independent and the manifest is the single source of
  truth.
- **Store:** gitignored cache; **content-addressed on the wire**
  (`sha256/<hash>` mirror keys → dedup, integrity == identity), name-addressed for
  use (symlink/copy from the content-addressed blob).

## Resolution chain

`materialize(asset)` — verify fixity at **every** hop; a file that fails
verification is treated as absent and the chain continues:

```
1  LOCAL CACHE      exists and sha256==registry  → return; else discard-if-corrupt
2  PRIVATE MIRROR   (if configured) rclone copy mirror:base/<key> → verify → return; else fall through
3  PUBLIC SOURCE    front-end fetcher (literature: PDF/DOI; dataset: Tier A git-LFS, Tier B pooch/http/doi)
                    → assert sha256==registry (hard fail) → populate mirror → return
4  GATED / MANUAL   print acquisition instructions → wait for operator drop → verify → populate mirror → return
```

Front-ends supply step-3 fetchers; the substrate owns steps 1, 2, 4 and all
fixity checks. The mirror is populated on first successful acquisition.

## License rule (non-negotiable)

Redistribution rights are set by the **license**, recorded on the base record, and
are **never** implied by the existence of a mirror. A private mirror is storage,
not a redistribution grant. Never treat mirror presence as permission to commit
bytes in-repo; never surface mirror contents publicly. (Applies identically to
copyrighted PDFs and licensed data.)

## Plugin vs. consumer

- **Plugin:** the base-record schema + loader/validator; the persistent-ID/citation
  module; the rclone mirror integration + fixity + content-addressed cache; the
  resolution chain (steps 1/2/4); the `rclone.conf.example` generator + secret
  hygiene. Deps: `rclone` (subprocess) + `pyyaml` (+ `pooch`, owned by `dataset`).
- **Consumer:** registry entries + SHA-256 checksums; the real rclone remote
  config (untracked/CI); mirror blobs; the gitignored cache.
