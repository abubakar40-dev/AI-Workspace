# NUML LMS2 Technical Investigation

**Portal investigated:** <https://lms2.numl.edu.pk/my/>  
**Investigation date:** 2026-11-05  
**Scope:** Public, unauthenticated, read-only inspection only. No username, password, token, browser session, assignment, quiz, or JARVIS project was accessed or changed; no public session cookie was reused.

## Executive summary

| Question | Finding | Label |
|---|---|---|
| Is this Moodle? | Yes. The portal exposes Moodle-specific session cookies, paths, REST, token, AJAX, theme, and upgrade artifacts. | **VERIFIED** |
| Exact Moodle release | Student-scoped `core_webservice_get_site_info` returned `3.8.3+ (Build: 20200522)`. | **SOURCE-VERIFIED** |
| Customization | Yes: NUML branding/logo, a custom faculty/campus notice, and a branded domain/theme asset layout are visible. | **VERIFIED** |
| REST web services | The REST endpoint is live and returns a Moodle `invalidtoken` response for an intentionally invalid token. | **VERIFIED** |
| Student API access | Cannot be established without a student token and the user's authorized service/function list. | **BLOCKED** |
| Moodle Mobile compatibility | The token endpoint is reachable and was probed with the documented Moodle mobile service parameter, but a token was not requested and no account was used. Full mobile compatibility is unknown. | **VERIFIED endpoint / UNVERIFIED service availability** |
| Upload/submission | Moodle's documented mechanism supports upload-to-draft followed by `mod_assign_save_submission` and optionally `mod_assign_submit_for_grading`; NUML enablement and the student's permissions are unknown. | **DOCUMENTED / BLOCKED for NUML validation** |

**Recommendation:** Use a least-privilege, read-only Moodle REST integration first, behind a small typed adapter. Add browser automation only for functions that NUML has not exposed through the student's service. Do not start with a general-purpose MCP server or an account-wide token.

## 1. LMS identification

### Evidence

1. `GET /my/` redirects to the Moodle login page and returns the NUML “Learning Management System” page with Moodle-style login and account flows:
   <https://lms2.numl.edu.pk/my/> (redirect target: `/login/index.php`).
2. The public response sets a `MoodleSession` cookie and exposes Moodle-specific headers such as `X-Powered-By: PHP/7.4.33`, `Content-Language`, and Moodle theme/AJAX assets. **VERIFIED**, based on the public response observed during this investigation.
3. `GET /webservice/rest/server.php` returns:

   ```xml
   <EXCEPTION class="moodle_exception">
   <ERRORCODE>invalidtoken</ERRORCODE>
   <MESSAGE>Invalid token - token not found</MESSAGE>
   </EXCEPTION>
   ```

   This is a Moodle REST dispatcher response, not a generic web-server 404. **VERIFIED**:
   <https://lms2.numl.edu.pk/webservice/rest/server.php>
4. `GET /login/token.php` reaches Moodle's token service and returns a structured Moodle error for a missing username. **VERIFIED**:
   <https://lms2.numl.edu.pk/login/token.php>
5. `GET /lib/upgrade.txt` is publicly readable and contains Moodle's upgrade-history format, beginning with `=== 3.8.4 ===`. **VERIFIED**:
   <https://lms2.numl.edu.pk/lib/upgrade.txt>
6. The public login page contains the NUML logo and a portal-specific notice limiting LMS2 to FAH and FE&C, while linking other faculties/campuses to LMS1/LMS3. **VERIFIED**:
   <https://lms2.numl.edu.pk/login/index.php>

### Version assessment

- **SOURCE-VERIFIED:** The authenticated `core_webservice_get_site_info` response reported `3.8.3+ (Build: 20200522)`.
- **INFERRED:** The public `upgrade.txt` beginning at `3.8.4` is stale or not a reliable installed-version indicator for this deployment.
- **Required authoritative evidence:** an administrator should provide the value of `$release`, `$version`, and `$branch` from the Moodle installation's `version.php`, or the Moodle Site administration notification/version screen. Do not expose that file publicly merely to test it.

### Customization

- **VERIFIED:** NUML logo and wording are present; the login page is not a stock generic Moodle landing page.
- **VERIFIED:** The deployment uses branded paths/assets such as `/theme/image.php`, `/theme/styles.php`, and a NUML logo pluginfile URL.
- **UNVERIFIED:** Which plugins, authentication backends, local overrides, or theme changes are installed. Public pages do not prove whether SSO, LDAP, CAS, OAuth2, or other authentication plugins are enabled.

## 2. REST, authentication, and permissions

### REST availability

- **VERIFIED:** `/webservice/rest/server.php` is reachable and processes Moodle REST requests.
- **VERIFIED:** `moodlewsrestformat=json` is accepted far enough for the endpoint to return a JSON Moodle error when an invalid token is supplied.
- **UNVERIFIED:** Whether the global web-services switch, REST protocol, a custom service, and each required function are enabled for a NUML student. Moodle can expose the dispatcher while still denying a particular service/function.
- **UNVERIFIED:** CORS policy for authenticated calls. The endpoint response observed publicly included `Access-Control-Allow-Origin: *`; this should not be treated as proof that authenticated browser calls are safe or intended.

### Authentication methods

**Observed/documented:**

- **VERIFIED endpoint:** `/login/token.php` exists.
- **DOCUMENTED:** Moodle's standard token flow uses `/login/token.php` with a username, password, and service shortname, commonly `moodle_mobile_app`; see <https://docs.moodle.org/503/en/Development:Creating_a_web_service_client>.
- **DOCUMENTED:** Permanent web-service tokens are linked to a Moodle user, service, permissions, optional IP restrictions, and optional expiry; see <https://docs.moodle.org/en/Using_web_services>.
- **UNVERIFIED for NUML:** SSO, LDAP, CAS, OAuth2, local-password authentication, MFA, passwordless login, and whether students may create tokens.

No credential or token was sent. The fact that the token endpoint exists does **not** show that a token can be issued to this student or that the mobile service is enabled.

### Student permissions

Moodle web services are permission-driven. The token's service determines the allowed function set, and each function still evaluates the user's Moodle capabilities. Moodle documentation recommends authorized users, only necessary functions, and least privilege:

- <https://docs.moodle.org/en/Using_web_services>
- <https://docs.moodle.org/23/en/Development:External_services_security>

Therefore API access must be tested with a student-owned, least-privilege token or by an administrator inspecting the service/function configuration. A browser login alone does not imply REST access.

## 3. Feature-by-feature feasibility

The table describes Moodle's standard API capability, not a claim that NUML has enabled it for this account.

| Required feature | Standard API/data path | Feasibility | NUML/account result |
|---|---|---|---|
| Enrolled courses/subjects | `core_enrol_get_users_courses` | Readable with enrollment permissions | **UNVERIFIED / BLOCKED** |
| Course teachers/details | `core_enrol_get_enrolled_users` (filter/role), `core_course_get_contents`, course APIs | Technically feasible; teachers may be hidden by role/capability | **UNVERIFIED / BLOCKED** |
| Assignment instructions/deadlines | `mod_assign_get_assignments` (`intro`, `duedate`, `cutoffdate`) | Feasible for visible enrolled assignments | **UNVERIFIED / BLOCKED** |
| Submission status | `mod_assign_get_submission_status` | Feasible for the current user | **UNVERIFIED / BLOCKED** |
| Lecture notes/PDF/resources | `core_course_get_contents`, `/webservice/pluginfile.php` | Feasible if contents and file-download permission are enabled | **UNVERIFIED / BLOCKED** |
| Quizzes/schedules | `mod_quiz_get_quizzes_by_courses` (`timeopen`, `timeclose`) | Feasible for visible quizzes; attempting quizzes is a separate write/risk boundary | **UNVERIFIED / BLOCKED** |
| Grades/results | `gradereport_overview_get_course_grades`, `gradereport_user_get_grade_items` | Feasible where grade-report capabilities permit | **UNVERIFIED / BLOCKED** |
| Announcements | `mod_forum_get_forums_by_courses`, `mod_forum_get_discussions`; sometimes `core_course_get_updates_since` | Feasible, subject to forum visibility and course design | **UNVERIFIED / BLOCKED** |
| Notifications | Moodle message/notification functions and event APIs | Potentially feasible, but function/service exposure varies | **UNVERIFIED / BLOCKED** |
| Calendar/upcoming events | `core_calendar_get_calendar_upcoming_view`, `core_calendar_get_calendar_events` | Feasible for events visible to the user | **UNVERIFIED / BLOCKED** |

### Assignment file upload and submission

**DOCUMENTED:** Moodle's external-file design is:

1. `POST /webservice/upload.php` with a valid web-service token uploads a file into the user's draft file area.
2. The returned draft `itemid` is supplied to a file-accepting web-service function.
3. `mod_assign_save_submission` saves assignment submission data/files.
4. `mod_assign_submit_for_grading` can transition a saved submission to submitted/grading state where supported.

Source/documentation: <https://moodledev.io/docs/6.0/apis/subsystems/external/files>.

**Important boundaries:**

- This investigation did not upload a file or call a submission function.
- The exact function names, parameters, assignment submission plugins, file-size limits, cutoff rules, and student capabilities must be confirmed against NUML's installed release and service configuration.
- A read-only integration must not include upload or submit functions in its token.
- Uploading a draft file is not the same as submitting an assignment; both are state-changing operations and require explicit user confirmation in any future JARVIS design.

## 4. Source-level review of existing repositories

### 4.1 `1alexandrer/moodle-mcp`

Repository: <https://github.com/1alexandrer/moodle-mcp>  
License file: <https://github.com/1alexandrer/moodle-mcp/blob/master/LICENSE>  
Metadata observed through GitHub API: MIT license, non-archived, default branch `master`, package version `0.2.0`.

**SOURCE-VERIFIED functionality**

- REST client and site discovery: [`src/moodle-client.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/moodle-client.ts) lines 23-63.
- Token or password-to-token login using `service=moodle_mobile_app`: same file lines 65-96. This is a capability of the repository, not a recommendation to give it a password.
- REST calls use `wstoken`, `wsfunction`, and `moodlewsrestformat=json`: same file lines 98-122.
- Enrolled courses and course contents: [`src/tools/courses.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/tools/courses.ts) lines 24-43.
- Assignments/status: [`src/tools/assignments.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/tools/assignments.ts) lines 45-91.
- Grades: [`src/tools/grades.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/tools/grades.ts) lines 23-44.
- Quizzes and attempt history: [`src/tools/quizzes.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/tools/quizzes.ts) lines 47-112.
- Resource listing and file downloads: [`src/tools/files.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/tools/files.ts) lines 20-91 and [`src/tools/download.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/tools/download.ts) lines 35-131.
- The download path restricts hosts/paths to Moodle-managed `pluginfile.php`, reauthorizes visibility, attaches the token only outbound, and caps file size: `src/moodle-client.ts` lines 124-172 and `src/tools/download.ts` lines 35-72.
- Tool registration includes courses, files, downloads, assignments, grades, calendar, quizzes, forums, notifications, and site info: [`src/register-tools.ts`](https://github.com/1alexandrer/moodle-mcp/blob/master/src/register-tools.ts) lines 4-23.

**Limitations/security**

- **SOURCE-VERIFIED:** No assignment upload or submission tool appears in the reviewed source tree; assignment support is read/status/grade oriented.
- **SOURCE-VERIFIED:** The client supports a password-based token exchange. Do not use that mode for JARVIS; prefer a separately issued token and never persist a Moodle password.
- **SOURCE-VERIFIED:** File IDs are sealed and reauthorized, which is a useful pattern, but binary files are returned to the MCP client and therefore need client-side data handling controls.
- **SOURCE-VERIFIED:** It sends REST parameters in a POST body, while file downloads put the token in the URL query. Query-string tokens can leak through proxy/access logs; a deployment should verify Moodle's required download mechanism and protect logs.
- **SOURCE-VERIFIED:** MIT license is explicit. Maintenance and compatibility still require local build/test review; repository activity is not a guarantee of production support.

### 4.2 `loyaniu/moodle-mcp`

Repository: <https://github.com/loyaniu/moodle-mcp>  
Source tree: <https://github.com/loyaniu/moodle-mcp/tree/main>  
Metadata observed through GitHub API: non-archived, default branch `main`; no `LICENSE` file was present in the repository tree inspected.

**SOURCE-VERIFIED functionality**

- Configuration is `MOODLE_URL` plus `MOODLE_TOKEN`: [`.env.example`](https://github.com/loyaniu/moodle-mcp/blob/main/.env.example) lines 1-4.
- The client uses `requests.get` with `wstoken`, `wsfunction`, and `moodlewsrestformat=json`: [`src/moodle_mcp/moodle.py`](https://github.com/loyaniu/moodle-mcp/blob/main/src/moodle_mcp/moodle.py) lines 9-10 and 89-114.
- API enum includes courses, contents, assignments, submission status, grades, forums, completion, calendar, and updates: same file lines 20-42.
- MCP tools expose courses, contents, assignments/status/deadlines, grades, search, announcements, events, progress, and summaries: [`src/moodle_mcp/server.py`](https://github.com/loyaniu/moodle-mcp/blob/main/src/moodle_mcp/server.py) lines 6-178.
- Course content keeps module contents but explicitly deletes several file metadata fields, including MIME type and license, in `moodle.py` lines 46-83.

**Limitations/security**

- **SOURCE-VERIFIED:** No upload endpoint, `mod_assign_save_submission`, `mod_assign_submit_for_grading`, or file-download implementation was found in the reviewed source.
- **SOURCE-VERIFIED:** The token is read from environment configuration and sent as a URL query parameter using `requests.get`; protect process environment, logs, command history, and HTTP/proxy logs.
- **SOURCE-VERIFIED:** `api.py` writes raw API responses to local JSON files through `to_json_file` (for example courses, assignments, status, grades, and calendar). This can persist sensitive student data and must be disabled or encrypted in a production JARVIS deployment.
- **SOURCE-VERIFIED:** Several high-level tools call multiple API functions and catch some exceptions to continue summaries. This is convenient but can produce partial dashboards unless JARVIS marks partial results explicitly.
- **UNVERIFIED license:** No repository license file was found; do not assume MIT/GPL permission. Obtain author permission or a clear license before redistribution.

### 4.3 `onbirdev/moodle-webservice_mcp`

Repository: <https://github.com/onbirdev/moodle-webservice_mcp>  
Source tree: <https://github.com/onbirdev/moodle-webservice_mcp/tree/main>  
Metadata observed through GitHub API: non-archived, default branch `main`; no root `LICENSE` file was present in the inspected tree.

**SOURCE-VERIFIED functionality**

- This is a Moodle plugin, not a standalone REST client. It registers a Moodle `mcp` web-service protocol and runs at `server.php`: [`server.php`](https://github.com/onbirdev/moodle-webservice_mcp/blob/main/server.php) lines 27-48.
- It authenticates through Moodle's permanent-token mechanism: `server.php` line 46.
- It accepts a Bearer token or `wstoken` query fallback: [`classes/local/server.php`](https://github.com/onbirdev/moodle-webservice_mcp/blob/main/classes/local/server.php) lines 137-169.
- It discovers the functions attached to the token's external service and converts Moodle external-function schemas into MCP tool schemas: [`classes/local/tool_provider.php`](https://github.com/onbirdev/moodle-webservice_mcp/blob/main/classes/local/tool_provider.php) lines 45-91.
- Therefore its tool set is dynamic: it can expose whatever Moodle functions an administrator adds to the token's service. It does not itself implement course/assignment/file business logic.
- The plugin declares Moodle requirement `2024100700`, beta maturity, and release `0.6.0`: [`version.php`](https://github.com/onbirdev/moodle-webservice_mcp/blob/main/version.php) lines 25-31.
- It defines a course-level `webservice/mcp:use` capability with no default archetypes: [`db/access.php`](https://github.com/onbirdev/moodle-webservice_mcp/blob/main/db/access.php) lines 22-31.
- The included test client sends a token as a URL parameter: [`lib.php`](https://github.com/onbirdev/moodle-webservice_mcp/blob/main/lib.php) lines 39-66.

**Limitations/security**

- **SOURCE-VERIFIED:** It can expose write functions if an administrator adds them to the external service. That flexibility is powerful but dangerous for an AI client; create a dedicated read-only service.
- **SOURCE-VERIFIED:** It supports a query-string token fallback even though Bearer headers are supported. Prefer headers and prevent URL/token logging.
- **SOURCE-VERIFIED:** It is a beta plugin and requires a newer Moodle build than the inferred NUML 3.8.x family. Compatibility with NUML cannot be assumed.
- **SOURCE-VERIFIED:** PHP headers state GNU GPL v3 or later, but no repository `LICENSE` file was found. Treat the PHP headers as the available licensing evidence and verify with the author before distribution.
- **UNVERIFIED:** Its dynamic schema accurately represents every installed NUML function across the inferred old release; this needs a real compatibility test on a non-production Moodle.

## 5. Integration option comparison

| Option | Strengths | Risks/limitations | Assessment |
|---|---|---|---|
| Direct Moodle REST API | Small attack surface; typed, explicit functions; least-privilege service; no browser/session scraping | NUML must enable functions; Moodle version/function differences; file upload is multi-step | **Best primary path** |
| Existing standalone Moodle MCP (`1alexandrer` or `loyaniu`) | Fast read-only prototype; many read tools already mapped | Third-party code/data persistence; incomplete upload support; token/password handling differs; license concerns for loyaniu | Use only after code audit/fork/pinning |
| `onbirdev` Moodle MCP plugin | Native Moodle permission/function discovery; MCP tool schemas generated from service | Requires installing a Moodle plugin, beta/release compatibility risk, can expose writes dynamically | Not first choice for a university production site |
| Playwright/browser automation | Works when no REST function is exposed; follows the actual student UI | Fragile selectors/CSRF/session/MFA; hard to audit; browser can accidentally submit/attempt; credential/session risk | Fallback only |
| Hybrid API + browser | API for stable reads/files, browser only for gaps | Two security models and more operational complexity | Best long-term fallback architecture |

## 6. Recommended JARVIS architecture

1. **Dedicated Moodle external service:** Ask NUML administration to create a service for one student integration. Start with read-only functions only:
   `core_webservice_get_site_info`, `core_enrol_get_users_courses`,
   `core_course_get_contents`, `core_enrol_get_enrolled_users` (if approved),
   assignment/quiz/grade/calendar/forum read functions, and the required file-download permission.
2. **Token policy:** Use a dedicated student token, with expiry and IP restriction where possible. Store it in an OS secret manager or encrypted secret store, never in source, `.env` committed files, chat, logs, URLs, or MCP tool output.
3. **Typed adapter:** Implement a small JARVIS Moodle adapter that checks `site_info.functions` before calls, validates response schemas, distinguishes permission errors from empty data, and records no raw student payloads by default.
4. **Read-only guard:** Do not include `core_files_upload`, `mod_assign_save_submission`, `mod_assign_submit_for_grading`, quiz attempt/start functions, forum posting, or messaging functions in the initial service.
5. **File handling:** Download only Moodle-managed URLs, verify host/path, enforce size/type limits, scan or sandbox documents, and avoid returning raw tokens in URLs. Use opaque short-lived file references if JARVIS needs deferred access.
6. **Browser fallback:** If required data is absent from REST, use a separately isolated Playwright worker with explicit allowlisted read-only routes, no automatic form submission, no quiz launch, no credential recording, and a visible confirmation boundary for any state-changing action.
7. **Observability:** Log function name, duration, HTTP status, and Moodle error code—not tokens, cookies, passwords, assignment contents, grades, or downloaded documents.

## 7. Security assessment

### Threats

- A Moodle token is effectively a user-scoped password for the functions/service attached to it.
- Query-string tokens can appear in reverse-proxy logs, browser history, referrers, monitoring, and exception traces.
- Assignment files and grades are sensitive educational records. Local JSON caches are a data-retention risk.
- A generic MCP server can accidentally expose write functions if its service contains them.
- Browser automation can submit forms or start quizzes if selectors/actions are not explicitly restricted.

### Required controls

- HTTPS certificate verification and no HTTP fallback.
- Secret-manager storage, process isolation, rotation, expiry, and revocation procedure.
- Dedicated read-only external service; authorized-user restriction; minimal functions; IP restriction if viable.
- No password-based token exchange in JARVIS. If NUML uses SSO, use an administrator-issued token or an approved OAuth/device flow rather than automating the password.
- Redacted logs and encrypted temporary storage with a short retention period.
- Schema validation, rate limits, timeouts, retry limits, and explicit handling of `invalidtoken`, `nopermission`, and `webservicefunctionnotavailable`.
- User confirmation before any future upload/save/submit/quiz action; default deny.

## 8. Testing requirements

Testing must be performed by the student or NUML administrator with a test/dedicated account and written permission. Do not test by submitting a real assignment.

### Read-only API test plan

1. Confirm the exact Moodle release and enabled authentication method with NUML.
2. Create a dedicated read-only external service and token with expiry.
3. Call `core_webservice_get_site_info`; record `release`, user ID, and the returned function list without storing the token.
4. Verify each feature in the matrix using one known enrolled course and compare results with the UI.
5. Test visibility rules: hidden module, unavailable resource, forum announcement, assignment with no submission, graded and ungraded item, quiz open/closed.
6. Test file download with a harmless small PDF and verify token/log redaction.
7. Verify rate limits, timeout behavior, token revocation, expired token, and permission errors.
8. Confirm no write function is attached by enumerating the external service functions.

### Upload/submission test plan (separate approval)

- Use a sandbox/test assignment only.
- Upload a harmless test file to draft storage.
- Verify the returned `itemid` is scoped to the intended user.
- Save, inspect, and delete/clean up the draft without submitting.
- Only after explicit authorization, test submission and verify the resulting status in the UI.

## 9. Unknowns requiring access

The following cannot be determined from public unauthenticated evidence:

- Exact Moodle `$release`, `$version`, `$branch`, patch level, and security-patch status.
- Whether NUML has enabled REST globally, the REST protocol, the Moodle Mobile service, custom services, or file download.
- Which authentication backend and MFA/SSO flow are enabled.
- Whether a student may create a token, and which functions/capabilities are attached to a student token.
- Whether course teachers are exposed to students through `core_enrol_get_enrolled_users`.
- Actual enrolled courses, content, deadlines, submission status, grades, announcements, notifications, and calendar events.
- Upload limits, assignment submission plugins, cutoff behavior, plagiarism/antivirus integration, and whether save/submit functions are permitted.
- Installed local plugins and their external functions.
- University policy on external AI access, student-record processing, and retention.

## 10. Recommended next steps

1. Ask NUML LMS administration for the exact release and whether a student-scoped read-only REST service can be issued.
2. Request only the read functions needed for the initial feature set and ask whether `/webservice/pluginfile.php` downloads are permitted.
3. Run the read-only test plan with a dedicated token; do not send the token to this report or chat.
4. Build a direct typed adapter and contract tests against captured **redacted** response fixtures.
5. Evaluate `1alexandrer/moodle-mcp` only as auditable prototype code; do not use its password flow. Treat `loyaniu/moodle-mcp` licensing and JSON persistence as blockers until resolved.
6. Do not install `onbirdev/moodle-webservice_mcp` on NUML until its Moodle-version requirement, beta status, capability behavior, and university change-control approval are confirmed.
7. Add Playwright only for documented REST gaps, with read-only route/action allowlists.

## 11. Student-side verification status

**SOURCE-VERIFIED from a local student-side run:** The read-only verifier successfully obtained site information and a student-scoped token, then returned the following account-level facts. The credential was entered locally and was not included in this report.

- Exact Moodle release: `3.8.3+ (Build: 20200522)`.
- Enrolled-course API returned 10 courses, including lecture/lab courses for Computer Networks, Data Structures, Software Requirement Engineering, plus other BSSE courses.
- Course contents/resources were readable for the tested Computer Networks course, including PDFs, PPT/PPTX resources, an announcements forum, attendance, and two assignments.
- Assignment metadata and `mod_assign_get_submission_status` were readable. The tested assignments returned `new`, not graded, with no grade.
- The authorized function inventory includes the read APIs and also state-changing functions such as `mod_assign_save_submission`, `mod_assign_submit_for_grading`, forum posting, messaging, calendar writes, and grade-write functions. This is a **HIGH-RISK configuration finding**: the token/service is not least-privilege read-only and must not be given to an autonomous JARVIS integration.
- The first three saved runs stopped while processing the first course because of version-specific response shapes/parameters. The verifier now continues after per-feature errors and processes up to the first 50 enrolled courses, rather than limiting the investigation to Computer Networks. Each course is checked independently for contents/resources, assignments/status, teachers, quizzes, grades, calendar events, and forums.

The third and fifth runs **SOURCE-VERIFIED**:

- Teacher/enrolled-user visibility works. The tested course returned an `editingteacher` role and student memberships.
- Quiz discovery works and returned an empty list for the tested Computer Networks course.
- Grade access works. The tested course exposed attendance at `100.00%`, ungraded assignment items, and a course total of `100.00%`.
- Course-calendar invocation reached Moodle but returned `invalid_parameter`; the script now supplies explicit time bounds.
- The fifth run processed all 10 enrolled courses, not just Computer Networks. Each course reached the contents, assignments, submission-status, teacher, quiz, grades, course-events, and forum sections; the global upcoming-events call also returned upcoming attendance events.
- The enrolled course list contains 10 visible courses. Reported progress included 37.5% for Computer Networks Lab, 33.33% for Data Structures, 82.35% for Data Structures Lab, and 77.78% for Software Requirement Engineering Lab; the remaining listed courses reported 0% at run time.
- Forum calls returned arrays, but the prior parser expected a `.forums` object. The parser is now corrected. Course-calendar calls still return Moodle `invalidparameter`, and both tested popup-notification calls return `invalidparameter`; these remain API/version-specific limitations rather than proof that the data is absent.

Announcements/forum output, notifications, calendar results, and file-download transfer behavior remain **UNVERIFIED** until the next corrected run. Do not share the existing result files because they contain student/course data and Moodle file URLs.

The script:

- prompts interactively for the username and password;
- keeps the password and returned token in process memory only and unsets them before exit;
- never prints or writes the token;
- calls only site information, enrolled courses, course contents/resources, assignments, quizzes, grades, calendar, and forum read endpoints;
- reports the token's authorized function inventory, including whether upload/submission/quiz-attempt functions are present;
- deliberately does not upload files, save submissions, submit assignments, start/attempt quizzes, post forums, send messages, or modify Moodle state.

Run locally with:

```bash
chmod 700 ./verify_numl_lms_readonly.sh
./verify_numl_lms_readonly.sh > numl-readonly-results.txt
```

`numl-readonly-results.txt` may contain grades, course names, assignment instructions, and file URLs. Keep it private, redact student/course-sensitive values before sharing, and delete it securely after analysis. The report's feature matrix should be updated only from the actual output, not from assumptions. If the token request fails, NUML may use SSO or disable the Moodle Mobile token service; do not bypass that with password automation.

## Sources

- NUML public portal: <https://lms2.numl.edu.pk/my/>
- NUML public login: <https://lms2.numl.edu.pk/login/index.php>
- NUML REST endpoint: <https://lms2.numl.edu.pk/webservice/rest/server.php>
- NUML token endpoint: <https://lms2.numl.edu.pk/login/token.php>
- NUML public upgrade artifact: <https://lms2.numl.edu.pk/lib/upgrade.txt>
- Moodle web-service function reference: <https://docs.moodle.org/dev/Web_service_API_functions>
- Moodle web-service client/token documentation: <https://docs.moodle.org/503/en/Development:Creating_a_web_service_client>
- Moodle web-service setup/security: <https://docs.moodle.org/en/Using_web_services>
- Moodle external-service security: <https://docs.moodle.org/23/en/Development:External_services_security>
- Moodle external file handling/upload/submission model: <https://moodledev.io/docs/6.0/apis/subsystems/external/files>
- Repository 1: <https://github.com/1alexandrer/moodle-mcp>
- Repository 2: <https://github.com/loyaniu/moodle-mcp>
- Repository 3: <https://github.com/onbirdev/moodle-webservice_mcp>
