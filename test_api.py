#!/usr/bin/env python3
"""End-to-end smoke test for the current Cloud Storage API."""

from __future__ import annotations

import time
import requests


BASE_URL = "http://localhost:8000/api/v1"


class APISmokeTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token: str | None = None

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _must(self, condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(message)

    def health_check(self) -> None:
        response = requests.get(f"{self.base_url}/health", timeout=15)
        self._must(response.status_code == 200, "Health check failed")
        print("[OK] health check")

    def register(self, username: str, email: str, password: str) -> None:
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        self._must(response.status_code == 200, f"Register failed: {response.text}")
        self.access_token = response.json()["access_token"]
        print("[OK] register")

    def get_me(self) -> dict:
        response = requests.get(f"{self.base_url}/auth/me", headers=self._auth_headers(), timeout=15)
        self._must(response.status_code == 200, f"/auth/me failed: {response.text}")
        print("[OK] auth/me")
        return response.json()

    def multipart_upload(self, file_name: str, content: bytes, mime_type: str = "text/plain") -> int:
        init_response = requests.post(
            f"{self.base_url}/files/multipart/init",
            json={
                "file_name": file_name,
                "file_size": len(content),
                "file_type": mime_type,
            },
            headers=self._auth_headers(),
            timeout=30,
        )
        self._must(init_response.status_code == 200, f"multipart init failed: {init_response.text}")
        init_data = init_response.json()

        parts = []
        total_parts = init_data["total_parts"]
        part_size = init_data["part_size"]

        for part_number in range(1, total_parts + 1):
            presign_response = requests.post(
                f"{self.base_url}/files/multipart/presign-part",
                json={
                    "upload_id": init_data["upload_id"],
                    "s3_key": init_data["s3_key"],
                    "part_number": part_number,
                },
                headers=self._auth_headers(),
                timeout=30,
            )
            self._must(
                presign_response.status_code == 200,
                f"presign part {part_number} failed: {presign_response.text}",
            )
            presign_data = presign_response.json()

            start = (part_number - 1) * part_size
            chunk = content[start : start + part_size]
            upload_response = requests.put(presign_data["url"], data=chunk, timeout=30)
            self._must(upload_response.status_code == 200, f"upload part {part_number} failed")

            etag = (upload_response.headers.get("ETag") or f"part-{part_number}").replace('"', "")
            parts.append({"part_number": part_number, "etag": etag})

        complete_response = requests.post(
            f"{self.base_url}/files/multipart/complete",
            json={
                "upload_id": init_data["upload_id"],
                "s3_key": init_data["s3_key"],
                "parts": parts,
            },
            headers=self._auth_headers(),
            timeout=30,
        )
        self._must(complete_response.status_code == 200, f"multipart complete failed: {complete_response.text}")

        file_id = complete_response.json()["file_id"]
        print("[OK] multipart upload")
        return file_id

    def list_files(self) -> list[dict]:
        response = requests.get(f"{self.base_url}/files", headers=self._auth_headers(), timeout=15)
        self._must(response.status_code == 200, f"list files failed: {response.text}")
        files = response.json()
        print(f"[OK] list files ({len(files)})")
        return files

    def download_url_and_fetch(self, file_id: int) -> str:
        response = requests.get(
            f"{self.base_url}/files/{file_id}/download-url",
            headers=self._auth_headers(),
            timeout=15,
        )
        self._must(response.status_code == 200, f"download-url failed: {response.text}")
        url = response.json()["url"]
        fetched = requests.get(url, timeout=15)
        self._must(fetched.status_code == 200, f"download URL fetch failed: {fetched.status_code}")
        print("[OK] download-url")
        return url

    def restore_latest_version(self, file_id: int) -> None:
        versions_response = requests.get(
            f"{self.base_url}/files/{file_id}/versions",
            headers=self._auth_headers(),
            timeout=15,
        )
        self._must(versions_response.status_code == 200, f"versions failed: {versions_response.text}")
        versions = versions_response.json()
        self._must(len(versions) > 0, "No versions found")
        version_number = versions[0]["version_number"]

        restore_response = requests.post(
            f"{self.base_url}/files/{file_id}/versions/{version_number}/restore",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=15,
        )
        self._must(restore_response.status_code == 200, f"restore failed: {restore_response.text}")
        print("[OK] restore version")

    def delete_file(self, file_id: int) -> None:
        response = requests.delete(
            f"{self.base_url}/files/{file_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=15,
        )
        self._must(response.status_code == 200, f"delete failed: {response.text}")
        print("[OK] delete file")


def main() -> None:
    tester = APISmokeTester(BASE_URL)

    username = f"smoke_{int(time.time())}"
    email = f"{username}@example.com"
    password = "Smoketest123!"

    print("Running API smoke test...")
    tester.health_check()
    tester.register(username=username, email=email, password=password)
    tester.get_me()

    content = ("cloud smoke test line\n" * 150).encode("utf-8")
    file_id = tester.multipart_upload(file_name="smoke.txt", content=content)

    files = tester.list_files()
    if not any(row.get("file_id") == file_id for row in files):
        raise RuntimeError("Uploaded file not found in listing")

    tester.download_url_and_fetch(file_id)
    tester.restore_latest_version(file_id)
    tester.delete_file(file_id)

    files_after = tester.list_files()
    if any(row.get("file_id") == file_id for row in files_after):
        raise RuntimeError("Deleted file still present in listing")

    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
