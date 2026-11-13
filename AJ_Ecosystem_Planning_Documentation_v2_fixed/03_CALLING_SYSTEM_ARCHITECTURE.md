# 03 — HELIX Calling and Communications Architecture

## 1. Scope and terminology

The project context mentions phone connectivity, calls, and call-related
notifications. This document therefore defines **phone-call capability**
as the primary meaning of "calling".

It also separates that capability from: - AJ/JARVIS/HELIX voice
conversations with the user (microphone, speech recognition, TTS). -
VoIP/SIP calls made entirely through a network calling provider. - Audio
routing between the laptop and a mobile phone.

These are related but different systems. They must not be treated as one
feature.

## 2. Design objective

The user should eventually be able to ask AJ to; AJ routes the phone/calling task to HELIX: - Identify a
contact. - Prepare a call. - Ask for confirmation. - Initiate a call
through a supported phone/device integration. - Receive incoming-call
notifications. - View call state where supported. - Potentially answer,
reject, or end a call only if the device bridge exposes a reliable and
permitted control.

The architecture must never promise full Android/iOS telephony control
until the chosen platform APIs are verified.

## 3. Proposed architecture

``` text
User command / AJ voice or chat
                 |
                 v
          Intent Classifier
                 |
        Is this a phone call?
                 |
                 v
         Calling Orchestrator
                 |
       Contact Resolver + Validator
                 |
       Permission / Confirmation Gate
                 |
       Calling Capability Registry
                 |
       +---------+------------------------------+
       |                 |                      |
       v                 v                      v
 Phone Bridge       Native Dialer          VoIP Provider
 (KDE Connect /     (tel: URI /            (SIP/API, if ever
 GSConnect)         OS handoff)             selected)
       |                 |                      |
       +-----------------+----------------------+
                         |
                  Device / Provider
                         |
                 Call State Adapter
                         |
          Verify state + emit call events
                         |
              HELIX call status -> AJ oversight and audit log
```

The calling orchestrator belongs to HELIX (or a HELIX-owned adapter) and must remain subject to AJ-wide policy and approval. It should depend on an interface, not directly on
KDE Connect, Android, a SIP provider, or one particular handset.

## 4. Core modules

### 4.1 Calling intent classifier

Recognizes intents such as: - `prepare_call` - `place_call` -
`incoming_call_event` - `answer_call` - `reject_call` - `end_call` -
`get_call_status` - `open_dialer`

It must distinguish "call Ahmed" from "talk to Jarvis" and from "start a
voice session".

### 4.2 Contact resolver

-   Resolve a name to one or more contacts.
-   Show ambiguity when multiple contacts match.
-   Normalize phone number format.
-   Identify the selected device/SIM if the platform exposes it.
-   Never guess a contact or number when ambiguous.

### 4.3 Calling capability registry

The adapter reports actual capabilities, for example: -
`can_open_dialer` - `can_place_call` - `can_receive_call_events` -
`can_answer_call` - `can_reject_call` - `can_end_call` -
`can_read_call_state` - `can_select_sim` - `can_route_audio`

Capabilities are discovered and verified at runtime. Unsupported actions
must be unavailable, not simulated.

### 4.4 Device bridge adapter

Candidate integration: KDE Connect / GSConnect, already recorded as
installed in the project context.

Possible role: - Discover paired phone. - Receive notification/call
events if exposed. - Open a dialer or hand off a number if supported. -
Exchange device status and supported actions.

Important: KDE Connect/GSConnect presence does not prove that remote
call initiation, answering, ending, or audio routing is supported in the
user's exact Android version and plugin configuration. These are
verification items for a later implementation phase.

### 4.5 Native dialer handoff

A low-risk initial capability may be to open the phone's dialer with a
number prefilled, leaving the user to press Call. This is safer than
claiming remote telephony control. Actual behavior depends on the mobile
OS and bridge.

### 4.6 Optional VoIP adapter

A future SIP/VoIP provider could support calls independently of the
mobile carrier. This is a separate product decision because it
introduces: - Provider accounts and credentials. - Network availability
requirements. - Potential fees. - Caller identity and regulatory
considerations. - Audio device and codec handling.

No VoIP provider is selected.

### 4.7 Call state machine

``` text
IDLE
  |
  +--> PREPARING
          |
          +--> WAITING_FOR_CONFIRMATION
                    |
                    +--> DIALING
                           |
                           +--> RINGING
                                  |
                                  +--> ACTIVE
                                  |      |
                                  |      +--> ENDED
                                  |
                                  +--> BUSY / NO_ANSWER
                           |
                           +--> FAILED
```

Incoming calls use a separate event path:
`INCOMING_RINGING -> USER_DECISION -> ANSWERED | REJECTED | MISSED`

If the adapter cannot verify state, report `UNKNOWN`; do not infer
`ACTIVE` or `ENDED`.

## 5. User approval and safety policy

### Outgoing calls

Before placing a call, show: - Contact display name. - Resolved number
(masked except enough digits to disambiguate). - Device/SIM if known. -
Call route/provider. - Any known cost warning.

Require an explicit confirmation such as "Call this contact now?". A
prior conversation or general instruction is not sufficient for an
individual consequential call unless the user has separately configured
a bounded policy.

### Incoming calls

-   Notify the user and identify caller only when the phone exposes it.
-   Do not auto-answer by default.
-   Answer/reject actions require a clear user instruction and supported
    adapter capability.

### Ending calls

-   Require a clear instruction to hang up.
-   Never end a call merely because the agent believes it is finished.

### Emergency calls

-   Do not automate emergency dialing.
-   Do not intercept, delay, or manipulate emergency calls.
-   The user should use the handset's native emergency interface.

### Recording and transcription

-   No call recording by default.
-   No call transcription by default.
-   Any future recording/transcription requires separate legal, privacy,
    consent, retention, and security review.

### Logs

Log action metadata (task ID, selected device, requested action,
approval, outcome). Do not log full contact lists, full phone numbers,
call audio, or message content unnecessarily.

## 6. Voice architecture is separate

AJ/JARVIS/HELIX voice conversation:
`Microphone -> Wake/Push-to-talk -> STT -> Intent/Conversation -> Provider Gateway -> Response -> TTS -> Speaker`

Phone call:
`Calling Intent -> Contact Resolution -> Approval -> Phone/VoIP Adapter -> Telephony Network`

The two may share: - Audio device selection. - Speech recognition
components (only if explicitly enabled). - TTS engine. - Permission and
audit infrastructure.

They must not share call state or assume that the laptop
microphone/speaker is automatically connected to a cellular call.

## 7. Failure handling

  -----------------------------------------------------------------------
  Failure                             Required behavior
  ----------------------------------- -----------------------------------
  Phone disconnected                  Report unavailable; do not retry
                                      indefinitely

  Contact ambiguous                   Ask user to select; do not guess

  Number invalid                      Stop before dialing

  Adapter lacks call control          Offer only supported handoff, if
                                      available

  State cannot be verified            Report UNKNOWN

  Call request times out              Check state before retry to avoid
                                      duplicate calls

  User cancels                        Cancel before dialing if possible;
                                      report if already placed

  Device changes mid-task             Stop and re-resolve target device

  Provider rejects request            Report exact safe error category;
                                      do not claim call placed
  -----------------------------------------------------------------------

## 8. Test plan for a future implementation phase

1.  Detect paired device and connection state.
2.  Discover actual calling capabilities.
3.  Resolve one test contact.
4.  Open dialer with a test number without placing a call.
5.  Verify incoming-call event delivery.
6.  Verify call-state transitions with a controlled test call.
7.  Test answer/reject/end only if the adapter officially exposes them.
8.  Test phone disconnection during a call workflow.
9.  Test duplicate prevention after timeouts.
10. Verify approval prompts and audit events.
11. Confirm that voice-chat mode and phone-call mode cannot accidentally
    cross-trigger.
12. Confirm no call audio or contact data is written to ordinary logs.

## 9. Decision status

  -----------------------------------------------------------------------
  Item                                Status
  ----------------------------------- -----------------------------------
  Route phone calling through HELIX under AJ policy  FINALIZED DIRECTION
  voice chat                          

  KDE Connect / GSConnect as          CURRENT DIRECTION / VERIFICATION
  candidate bridge                    REQUIRED

  Dialer handoff as safe first        PROPOSED
  capability                          

  Remote answer/reject/end            UNVERIFIED

  Audio routing                       UNVERIFIED
  laptop-to-cellular-call             

  SIP/VoIP provider                   UNDER DISCUSSION

  Auto-answer                         NOT APPROVED

  Call recording/transcription        NOT APPROVED

  Emergency-call automation           OUT OF SCOPE
  -----------------------------------------------------------------------

No calling code is included or authorized in this phase. AJ is the overall manager; HELIX owns the calling workflow; JARVIS is not the default calling executor.
