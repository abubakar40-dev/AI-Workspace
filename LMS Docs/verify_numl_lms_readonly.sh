#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MOODLE_BASE_URL:-https://lms2.numl.edu.pk}"
REST_URL="$BASE_URL/webservice/rest/server.php"
TOKEN_URL="$BASE_URL/login/token.php"

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

if [[ ! -t 0 || ! -t 1 ]]; then
  exec 3</dev/tty 4>/dev/tty
  PROMPT_INPUT=3
  PROMPT_OUTPUT=4
else
  PROMPT_INPUT=0
  PROMPT_OUTPUT=1
fi

printf 'NUML read-only verification starting.\n' >&"$PROMPT_OUTPUT"
printf 'Credentials are used only in memory and are not written to the result file.\n' >&"$PROMPT_OUTPUT"
read -r -p "NUML username: " USERNAME <&"$PROMPT_INPUT" >&"$PROMPT_OUTPUT"
read -r -s -p "NUML password: " PASSWORD <&"$PROMPT_INPUT" >&"$PROMPT_OUTPUT"
printf '\n' >&"$PROMPT_OUTPUT"

TOKEN_RESPONSE="$(
  curl --fail-with-body --silent --show-error --max-time 30 \
    --data-urlencode "username=$USERNAME" \
    --data-urlencode "password=$PASSWORD" \
    --data-urlencode "service=moodle_mobile_app" \
    "$TOKEN_URL"
)"
unset PASSWORD

if jq -e '.error' >/dev/null 2>&1 <<<"$TOKEN_RESPONSE"; then
  echo "Token request failed (credentials/token service response):"
  jq '{error, errorcode, message}' <<<"$TOKEN_RESPONSE"
  exit 2
fi

TOKEN="$(jq -er '.token' <<<"$TOKEN_RESPONSE")" || {
  echo "No token was returned. NUML may require SSO or may disable this service." >&2
  exit 2
}

call_api() {
  local function_name="$1"
  shift
  local response
  if ! response="$(
    curl --silent --show-error --max-time 45 \
      --data-urlencode "wstoken=$TOKEN" \
      --data-urlencode "wsfunction=$function_name" \
      --data-urlencode "moodlewsrestformat=json" \
      "$@" "$REST_URL"
  )"; then
    jq -n --arg function "$function_name" \
      '{exception: "transport_error", errorcode: "curl_failed", message: ("Unable to call " + $function)}'
    return 0
  fi
  if ! jq -e . >/dev/null 2>&1 <<<"$response"; then
    jq -n --arg function "$function_name" \
      '{exception: "invalid_response", errorcode: "non_json_response", message: ("Non-JSON response from " + $function)}'
    return 0
  fi
  printf '%s\n' "$response"
}

echo "=== Site info and authorized function inventory ==="
SITE_INFO="$(call_api core_webservice_get_site_info)"
if jq -e '.exception' >/dev/null 2>&1 <<<"$SITE_INFO"; then
  jq '{exception, errorcode, message}' <<<"$SITE_INFO"
  exit 3
fi
jq '{
  site: .sitename,
  user_id: .userid,
  username: .username,
  release: .release,
  authorized_functions: ([.functions[]?.name] | sort),
  read_only_upload_related_functions: ([.functions[]?.name | select(test("upload|save_submission|submit_for_grading|attempt"; "i"))] | sort)
}' <<<"$SITE_INFO"

USER_ID="$(jq -er '.userid' <<<"$SITE_INFO")"

echo "=== Enrolled courses ==="
COURSES="$(call_api core_enrol_get_users_courses --data-urlencode "userid=$USER_ID")"
jq 'if type == "array" then map({id, fullname, shortname, visible, startdate, enddate, progress}) else {exception, errorcode, message} end' <<<"$COURSES"

if ! jq -e 'type == "array"' >/dev/null 2>&1 <<<"$COURSES"; then
  exit 4
fi

# A single course can contain an activity with a version-specific response
# shape or permission error. Keep processing the remaining enrolled courses.
set +e
while IFS= read -r COURSE_ID; do
  COURSE_NAME="$(jq -r --argjson id "$COURSE_ID" '.[] | select(.id == $id) | .fullname' <<<"$COURSES")"
  echo "=== Course $COURSE_ID: $COURSE_NAME ==="

  echo "-- contents/resources --"
  CONTENT="$(call_api core_course_get_contents --data-urlencode "courseid=$COURSE_ID")"
  jq '[.[]? | {
    section: .name,
    visible: .visible,
    uservisible: .uservisible,
    modules: [.modules[]? | {
      id, name, modname, visible, uservisible, url,
      files: [.contents[]? | {type, filename, filesize, mimetype, fileurl}]
    }]
  }]' <<<"$CONTENT"

  echo "-- assignments --"
  ASSIGNMENTS="$(call_api mod_assign_get_assignments --data-urlencode "courseids[0]=$COURSE_ID")"
  jq 'if .exception then {exception, errorcode, message} else [.courses[]?.assignments[]? | {id, name, intro, duedate, cutoffdate, allowsubmissionsfromdate, grade}] end' <<<"$ASSIGNMENTS"

  echo "-- assignment submission status --"
  while IFS= read -r ASSIGNMENT_ID; do
    call_api mod_assign_get_submission_status \
      --data-urlencode "assignid=$ASSIGNMENT_ID" |
      jq --argjson id "$ASSIGNMENT_ID" 'if .exception then {assignment_id: $id, exception, errorcode, message} else {
        assignment_id: $id,
        status: (.lastattempt.submission.status // "not submitted"),
        graded: (.lastattempt.graded // false),
        grading_status: (.lastattempt.gradingstatus // null),
        grade: (.feedback.gradefordisplay // null),
        last_modified: (.lastattempt.submission.timemodified // null)
      } end'
  done < <(jq -r '.courses[]?.assignments[]?.id' <<<"$ASSIGNMENTS")

  echo "-- teachers/enrolled users (if permitted) --"
  ENROLLED_USERS="$(call_api core_enrol_get_enrolled_users \
    --data-urlencode "courseid=$COURSE_ID" |
    jq 'if type == "object" and .exception then {exception, errorcode, message} else [.[]? | {
      id, fullname, username, roles: [.roles[]? | {roleid, shortname, name}]
    }] end')"
  printf '%s\n' "$ENROLLED_USERS"

  echo "-- quiz metadata --"
  call_api mod_quiz_get_quizzes_by_courses --data-urlencode "courseids[0]=$COURSE_ID" |
    jq 'if .exception then {exception, errorcode, message} else [.quizzes[]? | {id, name, intro, timeopen, timeclose, timelimit, attempts}] end'

  echo "-- grades --"
  call_api gradereport_user_get_grade_items \
    --data-urlencode "courseid=$COURSE_ID" \
    --data-urlencode "userid=$USER_ID" |
    jq 'if .exception then {exception, errorcode, message} else [.usergrades[]?.gradeitems[]? | {id, itemname, itemtype, gradeformatted, percentageformatted, feedback}] end'

  echo "-- course events --"
  call_api core_calendar_get_calendar_events \
    --data-urlencode "courseid=$COURSE_ID" \
    --data-urlencode "timesortfrom=0" \
    --data-urlencode "timesortto=2147483647" |
    jq 'if .exception then {exception, errorcode, message} else [.events[]? | {id, name, description, timestart, timeduration, modname, instance}] end'

  echo "-- forums/announcements --"
  call_api mod_forum_get_forums_by_courses \
    --data-urlencode "courseids[0]=$COURSE_ID" |
    jq 'if type == "object" and .exception then {exception, errorcode, message} else [.[]? | {id, course, name, type, intro}] end'
done < <(jq -r '.[].id' <<<"$COURSES" | head -50)
set -e

echo "=== Global upcoming events ==="
call_api core_calendar_get_calendar_upcoming_view |
  jq 'if .exception then {exception, errorcode, message} else [.events[]? | {id, name, description, formattedtime, timestart, url}] end'

echo "=== Notifications ==="
call_api message_popup_get_unread_popup_notification_count |
  jq 'if type == "object" and .exception then {exception, errorcode, message} else . end'
call_api message_popup_get_popup_notifications |
  jq 'if type == "object" and .exception then {exception, errorcode, message} else . end'

unset TOKEN TOKEN_RESPONSE SITE_INFO COURSES USERNAME USER_ID ASSIGNMENTS ASSIGNMENT_ID ENROLLED_USERS
echo "Verification complete. No upload, save, submit, quiz-attempt, forum-post, or messaging function was called."
