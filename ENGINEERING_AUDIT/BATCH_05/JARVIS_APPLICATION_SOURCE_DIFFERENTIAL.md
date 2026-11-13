# JARVIS Application-Source Differential (Workstream D)

**Repositories:** `backup/JARVIS-old-repo-20261106` vs `backup/JARVIS-nested-duplicate-20261106` (A1 read-only; **no deletion/merge/restore**). Analytical exclusion only.

## D1. Exclusions (non-source artifacts)
Excluded from source manifests: `.git`, `__pycache__`, `.pytest_cache`, `*.pyc`, `./venv/*`, `./.venv/*`, `*/node_modules/*`, `*/config/jarvis_browser_profile/*`, `*/chat_history/*`. (Batch 04 full-file diff showed old-only bulk in `venv/lib`, browser profile, chat history.)

## D2. Application-source comparison (VERIFIED)
Manifests: `BATCH_05/jarvis_old.src.files`, `BATCH_05/jarvis_nested.src.files`.

| Metric | Value |
|---|---|
| Old repo source-filtered files | **259** |
| Nested repo source-filtered files | **259** |
| Only-old source files | **0** |
| Only-nested source files | **0** |
| Common source files | **259** |
| Content hash differences across common files | **1** — `./Jarvis/startup.log` (runtime/log artifact) |

## D3. Uniqueness determination
1. **Unique application code in old repo?** **No evidence of unique application source** in the filtered set. Batch 04’s 4,044 old-only files are explained by venv/runtime/profile/chat-history artifacts.
2. **Unique application code in nested repo?** **No** (0 source-only; 2 nested-only in full diff were browser session files).
3. **Features existing only in one?** **Not identified** by source-file presence/content (except differing `startup.log`). Deeper semantic diff not required by manifest/hash evidence.
4. **Meaningful differences vs environment/runtime artifacts?** Prior differences are **primarily environment/runtime artifacts**. `Jarvis/startup.log` differs (log content) — **runtime artifact, not application source uniqueness**.
5. **Can either be safely considered canonical?** **No.** They appear equivalent as application-source snapshots in the filtered comparison, but **neither is mapped to an active runtime**, `/home/abubakargcx/JARVIS` is missing, and full unexcluded-history/runtime provenance still requires caution. Canonical selection requires runtime/launcher evidence and user decision.
6. **Missing evidence:** active runtime/entrypoint using either path; whether unfiltered generated/runtime artifacts matter to recovery; any files outside chosen exclusion rules that represent source.

**Conclusion:** JARVIS application-source uniqueness (old vs nested) is **resolved as “no unique application source detected in filtered comparison; differences are runtime/artifact-dominated”** with **low residual risk** from exclusion choices/log artifact. Canonical runtime/source identity remains **unresolved** (Workstream C).
