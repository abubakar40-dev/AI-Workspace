# 04 — GitHub Repository Catalogue (AJ Ecosystem)

## 1. Purpose and evidence limits

This catalogue separates: 1. Repositories belonging to or used by the
user's projects. 2. Third-party repositories already identified as
upstreams or candidates. 3. Repositories that must not be treated as
part of the AJ ecosystem.

The connected GitHub repository listing returned no results during this
session. Therefore, the private/account-wide inventory could not be
completed from the GitHub connection. The table below is a grounded
partial catalogue using previously recorded local remotes and public
upstream sources.

## 2. User project repositories and remotes

  -----------------------------------------------------------------------------------------------------------------------------
  Repository     URL / remote                                              Role            Ownership /          Status
                                                                                           relationship         
  -------------- --------------------------------------------------------- --------------- -------------------- ---------------
  JARVIS local   No remote configured in the previously recorded workspace Personal        User project; no     CONFIRMED LOCAL
  repository     snapshot                                                  assistant and   GitHub target        / GITHUB TARGET
                                                                           coordinator     identified           UNVERIFIED

  HELIX          `https://github.com/abubakar40-dev/helix.git`             Calling and     User project remote  REMOTE
                                                                           communications  recorded previously  RECORDED;
                                                                           sub-agent                             current GitHub
                                                                                                                visibility not
                                                                                                                independently
                                                                                                                verified

  God's Eye View `https://github.com/bilawalsidhu/gods-eye-view.git`       External        Third-party          UPSTREAM
  local copy                                                               visualization   upstream; not a      CONFIRMED
                                                                           project         AJ-ecosystem-owned   
                                                                           used/modified   repository           
                                                                           locally                              

  Dental Lounge  `https://github.com/dentallounge-rwp/Dental-Lounge.git`   Separate dental Separate client      REMOTE
                                                                           clinic client   repository; excluded RECORDED;
                                                                           project         from AJ/JARVIS/HELIX    PROTECT FROM
                                                                                           scope                CROSS-PROJECT
                                                                                                                CHANGES
  -----------------------------------------------------------------------------------------------------------------------------

### Local backup repositories

Previously identified local-only Git repositories: -
`backup/JARVIS-nested-duplicate-20261106` -
`backup/JARVIS-old-repo-20261106`

Both had no remote configured in the recorded snapshot. They are local
preservation copies, not GitHub targets. Do not upload them as
repositories or merge them into the active JARVIS repository without a
separate decision.

## 3. External upstreams and technical candidates

  -----------------------------------------------------------------------------------------------------------
  Repository        URL                                              Intended relevance     Classification
  ----------------- ------------------------------------------------ ---------------------- -----------------
  Hermes Agent      https://github.com/NousResearch/hermes-agent     Agent runtime, tools,  OFFICIAL UPSTREAM
                                                                     skills, execution      
                                                                     lifecycle              

  Computer Use      https://github.com/agent-sh/computer-use-linux   Linux desktop          PROMISING
  Linux                                                              automation via         CANDIDATE; local
                                                                     MCP/CLI, accessibility compatibility
                                                                     and Wayland support    still requires
                                                                                            tests

  Agent Desktop     https://github.com/vercel-labs/agent-desktop     Cross-platform         EVALUATED
                                                                     accessibility-based    ALTERNATIVE
                                                                     computer use           

  Dogtail           https://gitlab.com/dogtail/dogtail               AT-SPI accessibility   ALTERNATIVE
                                                                     automation             

  OpenAdapt         https://github.com/OpenAdaptAI/OpenAdapt         Workflow               ALTERNATIVE
                                                                     recording/replay       
                                                                     research               

  SikuliX           https://github.com/oculix-org/SikuliX            Image-based visual     ALTERNATIVE
                                                                     automation fallback    

  Colibri           https://github.com/JustVugg/colibri              Experimental           EXPERIMENTAL
                                                                     disk-backed model      
                                                                     execution              
                                                                     investigation          

  God's Eye View    https://github.com/bilawalsidhu/gods-eye-view    Existing               THIRD-PARTY
  upstream                                                           spatial-intelligence   UPSTREAM
                                                                     visualization project  
  -----------------------------------------------------------------------------------------------------------

## 4. Repository role decisions

### JARVIS and HELIX

-   Keep separate repositories and histories.
-   Do not create a monorepo by default.
-   Shared contracts should initially be documented in the workspace;
    repository ownership can be decided later.
-   No GitHub push or remote change is authorized by this catalogue.

### Hermes

-   Treat NousResearch/hermes-agent as the upstream project.
-   Do not fork it merely to integrate AJ/JARVIS/HELIX.
-   Prefer a documented adapter/plugin/skill boundary where supported.
-   Keep canonical AJ canonical memory independent from Hermes storage.

### Computer-use candidates

-   `computer-use-linux` is the leading candidate in the existing
    project context, but no installation or adoption is approved.
-   `agent-desktop`, Dogtail, OpenAdapt, and SikuliX remain alternatives
    with distinct roles.
-   Avoid installing all tools. Select based on tested capability gaps.

### God's Eye View

-   Keep as an external project and separate repository boundary.
-   Do not treat the upstream repository as owned by the user.
-   Local modifications must not be pushed upstream without explicit
    authorization and appropriate contribution review.

### Dental Lounge

-   It is unrelated to the AJ/AJ/JARVIS/HELIX architecture.
-   Keep its GitHub/Vercel workflow and account protection separate.
-   Do not switch credentials, remotes, branches, or deployment
    configuration as part of this project.

## 5. Missing inventory required for a truly complete catalogue

The following cannot be truthfully declared complete yet: - All private
repositories under `abubakar40-dev`. - All repositories under
`dentallounge-rwp`. - Any other GitHub account or organization used by
the user. - Whether the JARVIS local repository should receive a new
remote or has a private repository not represented in the recorded local
remotes. - Whether other workspace folders map to GitHub repositories
not present in the known remote list.

These are documentation gaps, not reasons to run another broad local
audit. The cleanest later completion step is to connect the correct
GitHub account(s) with read access and retrieve repository names,
descriptions, visibility, default branch, and URL only. No repository
writes are needed.

## 6. Public source notes

-   Official Hermes sources identify the NousResearch organization and
    `NousResearch/hermes-agent` as the source repository:
    https://hermes-agent.nousresearch.com/docs/getting-started/official-domains
-   `computer-use-linux` documents an MCP/CLI interface and a Hermes
    skill integration path:
    https://github.com/agent-sh/computer-use-linux
-   `agent-desktop` describes accessibility-tree-based desktop
    interaction: https://github.com/vercel-labs/agent-desktop
-   God's Eye View upstream identifies itself as a public-data globe
    visualization project: https://github.com/bilawalsidhu/gods-eye-view


## 7. AJ hierarchy and repository implications

AJ is the central AI identity and logical control plane. The currently recorded repository evidence identifies separate JARVIS and HELIX repositories/remotes, but does **not** establish a dedicated AJ repository. Do not invent an AJ GitHub repository, change remotes, rename repositories, or move code based on the new hierarchy alone. The future coding agent must inspect the actual repositories after the user approves implementation and propose the safest AJ orchestration boundary.

Current agent roles: JARVIS — general-purpose and major-work sub-agent; HELIX — calling and communications sub-agent; AJ — parent identity and governance layer.
