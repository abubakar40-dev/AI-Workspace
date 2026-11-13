"""Small, local-only Moodle client for the NUML LMS.

Credentials are read from ~/.config/helix/lms.env and are never returned by the
HTTP API or written to the repository. Network writes are limited to Moodle
login and explicitly requested download/upload operations.
"""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://lms2.numl.edu.pk/"
CONFIG = Path.home() / ".config" / "helix" / "lms.env"
DOWNLOAD_DIR = Path.home() / "Downloads" / "helix-lms"


def _env():
    values = {}
    if CONFIG.is_file():
        for line in CONFIG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def _safe_name(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return value[:160] or "download"


def _moodle_datetime(value):
    value = " ".join(value.split()).strip()
    for fmt in ("%A, %d %B %Y, %I:%M %p", "%A, %d %B %Y, %H:%M"):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue
    return None


class LMSClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Helix LMS connector (local)"})
        self.logged_in = False

    def _url(self, path):
        return urljoin(BASE_URL, path)

    def login(self):
        env = _env()
        username, password = env.get("LMS_USERNAME"), env.get("LMS_PASSWORD")
        if not username or not password:
            raise RuntimeError(f"Missing LMS credentials in {CONFIG}")
        page = self.session.get(self._url("login/index.php"), timeout=20)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        token = soup.select_one('input[name="logintoken"]')
        data = {"username": username, "password": password}
        if token:
            data["logintoken"] = token.get("value", "")
        response = self.session.post(self._url("login/index.php"), data=data,
                                     timeout=20, allow_redirects=True)
        response.raise_for_status()
        self.logged_in = "/login/" not in response.url and (
            "You are not logged in" not in response.text
        )
        if not self.logged_in:
            raise RuntimeError("NUML LMS login was rejected")
        return response

    def _get(self, path):
        if not self.logged_in:
            self.login()
        response = self.session.get(self._url(path), timeout=25)
        response.raise_for_status()
        if "You are not logged in" in response.text:
            self.logged_in = False
            self.login()
            response = self.session.get(self._url(path), timeout=25)
            response.raise_for_status()
        return response

    def dashboard(self):
        soup = BeautifulSoup(self._get("my/").text, "html.parser")
        courses = []
        seen = set()
        for link in soup.select('a[href*="/course/view.php?id="]'):
            match = re.search(r"[?&]id=(\d+)", link.get("href", ""))
            if not match or match.group(1) in seen:
                continue
            seen.add(match.group(1))
            name = " ".join(link.get_text(" ", strip=True).split())
            courses.append({"id": int(match.group(1)), "name": name,
                            "url": urljoin(BASE_URL, link["href"])})
        return {"ok": True, "user": soup.title.get_text(strip=True) if soup.title else "",
                "courses": courses}

    def course(self, course_id):
        soup = BeautifulSoup(self._get(f"course/view.php?id={int(course_id)}").text,
                             "html.parser")
        modules = []
        seen = set()
        for link in soup.select('a[href]'):
            href = urljoin(BASE_URL, html.unescape(link.get("href", "")))
            parsed = urlparse(href)
            if parsed.netloc != urlparse(BASE_URL).netloc:
                continue
            if not re.search(r"/mod/(resource|assign|forum|url|folder|attendance)/",
                             parsed.path):
                continue
            if href in seen:
                continue
            seen.add(href)
            activity_id = re.search(r"(?:^|&)id=(\d+)", parsed.query)
            modules.append({
                "name": " ".join(link.get_text(" ", strip=True).split()) or "Untitled",
                "url": href,
                "kind": parsed.path.split("/")[2],
                "id": int(activity_id.group(1)) if activity_id else None,
            })
        title = soup.select_one("h1") or soup.select_one(".page-header-headings")
        return {"ok": True, "id": int(course_id),
                "name": title.get_text(" ", strip=True) if title else str(course_id),
                "modules": modules,
                "assignments": [self.assignment(m["id"], m["name"]) for m in modules
                                if m["kind"] == "assign" and m["id"]],
                "attendance": [self.attendance(m["id"]) for m in modules
                               if m["kind"] == "attendance" and m["id"]]}

    def assignment(self, assignment_id, fallback_title=""):
        soup = BeautifulSoup(
            self._get(f"mod/assign/view.php?id={int(assignment_id)}").text,
            "html.parser",
        )
        values = {}
        table = soup.select_one(".submissionsummarytable")
        for row in table.select("tr") if table else []:
            cells = row.select("th, td")
            if len(cells) >= 2:
                values[" ".join(cells[0].stripped_strings).lower()] = \
                    " ".join(cells[1].stripped_strings)
        title = soup.select_one(".activity-header h1") or soup.select_one("h1")
        status = values.get("submission status", "")
        status_lower = status.lower()
        submitted = (
            bool(status)
            and "no attempt" not in status_lower
            and "not submitted" not in status_lower
            and "nothing has been submitted" not in status_lower
        )
        return {
            "id": int(assignment_id),
            "title": (fallback_title or (title.get_text(" ", strip=True)
                     if title else str(assignment_id))),
            "submission_status": status,
            "submitted": submitted,
            "grading_status": values.get("grading status", ""),
            "due": _moodle_datetime(values.get("due date", "")),
            "last_modified": values.get("last modified", ""),
            "raw": values,
        }

    def attendance(self, attendance_id):
        soup = BeautifulSoup(
            self._get(f"mod/attendance/view.php?id={int(attendance_id)}").text,
            "html.parser",
        )
        summary = {}
        for row in soup.select("table")[-1].select("tr") if soup.select("table") else []:
            cells = row.select("th, td")
            if len(cells) >= 2:
                summary[" ".join(cells[0].stripped_strings).lower()] = \
                    " ".join(cells[1].stripped_strings)
        percent = summary.get("percentage over taken sessions", "0%")
        match = re.search(r"(\d+(?:\.\d+)?)%", percent)
        sessions = []
        tables = soup.select("table")
        if len(tables) > 1:
            for row in tables[1].select("tr")[1:]:
                cells = [" ".join(c.stripped_strings) for c in row.select("th, td")]
                if cells:
                    sessions.append({
                        "date": cells[0],
                        "description": cells[1] if len(cells) > 1 else "",
                        "status": cells[2] if len(cells) > 2 else "",
                        "points": cells[3] if len(cells) > 3 else "",
                    })
        return {
            "id": int(attendance_id),
            "taken_sessions": summary.get("taken sessions", "0"),
            "points": summary.get("points over taken sessions", "0 / 0"),
            "percentage": float(match.group(1)) if match else 0.0,
            "sessions": sessions,
            "raw": summary,
        }

    def download(self, url):
        parsed = urlparse(url)
        if parsed.netloc != urlparse(BASE_URL).netloc:
            raise ValueError("Downloads are restricted to lms2.numl.edu.pk")
        response = self._get(url)
        name = _safe_name(Path(urlparse(response.url).path).name)
        if not Path(name).suffix:
            name += ".html"
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target = DOWNLOAD_DIR / name
        target.write_bytes(response.content)
        return {"ok": True, "path": str(target), "name": target.name,
                "bytes": len(response.content), "url": response.url}

    def upload_assignment_draft(self, assignment_id, file_path):
        """Upload a file to an assignment draft, but do not submit it for grading."""
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise ValueError("upload file does not exist")
        page = self._get(
            f"mod/assign/view.php?id={int(assignment_id)}&action=editsubmission"
        )
        soup = BeautifulSoup(page.text, "html.parser")
        form = soup.select_one('form[action*="savesubmission"]')
        item = soup.select_one('input[name="files_filemanager"]')
        sesskey = soup.select_one('input[name="sesskey"]')
        config_script = next(
            (s.get_text() for s in soup.find_all("script")
             if "M.form_filemanager.init" in s.get_text()), ""
        )
        marker = "M.form_filemanager.init("
        start = config_script.find(marker)
        if not form or not item or not sesskey or start < 0:
            raise RuntimeError("Moodle assignment upload form was not recognized")
        decoder = json.JSONDecoder()
        config_start = config_script.find("{", start)
        config, _ = decoder.raw_decode(config_script[config_start:])
        upload_url = self._url("repository/repository_ajax.php")
        with path.open("rb") as stream:
            response = self.session.post(
                upload_url,
                params={"action": "upload"},
                data={
                    "repo_id": os.environ.get("LMS_UPLOAD_REPO_ID", "4"),
                    "itemid": config["itemid"],
                    "savepath": "/",
                    "client_id": config["client_id"],
                    "sesskey": sesskey["value"],
                    "author": _env().get("LMS_USERNAME", ""),
                    "license": "allrightsreserved",
                },
                files={"repo_upload_file": (path.name, stream, "application/octet-stream")},
                timeout=60,
            )
        response.raise_for_status()
        try:
            uploaded = response.json()
        except ValueError as e:
            raise RuntimeError("Moodle rejected the file upload") from e
        if uploaded.get("error"):
            raise RuntimeError(str(uploaded["error"]))
        fields = {
            element.get("name"): element.get("value", "")
            for element in form.select("input[name]")
            if element.get("name") != "submitbutton"
        }
        fields["files_filemanager"] = str(config["itemid"])
        fields["submitbutton"] = "Save changes"
        saved = self.session.post(form.get("action") or page.url, data=fields,
                                  timeout=30, allow_redirects=True)
        saved.raise_for_status()
        if "Edit submission" not in saved.text and "Submission status" not in saved.text:
            raise RuntimeError("Moodle did not confirm the assignment draft upload")
        return {"ok": True, "assignment_id": int(assignment_id),
                "file": path.name, "submitted": False}


_client = None


def client():
    global _client
    if _client is None:
        _client = LMSClient()
    return _client


def state():
    c = client()
    dashboard = c.dashboard()
    return {"ok": True, "authenticated": True, **dashboard}
