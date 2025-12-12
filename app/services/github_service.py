"""
GitHub Integration Service for Roundtable Coder.

Provides functionality to fetch code from GitHub repositories,
list files, and create pull requests.
"""

import requests
import base64
from typing import Optional, List, Dict, Any


class GitHubService:
    """Service for GitHub API interactions."""

    def __init__(self, token: str):
        """
        Initialize the GitHub service.

        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"

    def get_file_content(
        self,
        repo: str,
        path: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Fetch file content from GitHub.

        Args:
            repo: Repository in format "owner/repo"
            path: Path to file in repository
            branch: Branch name (default: main)

        Returns:
            Dictionary with content and metadata, or error info
        """
        url = f"{self.base_url}/repos/{repo}/contents/{path}"
        params = {"ref": branch}

        try:
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data["content"]).decode("utf-8")
                return {
                    "success": True,
                    "content": content,
                    "sha": data.get("sha"),
                    "size": data.get("size"),
                    "path": data.get("path"),
                    "name": data.get("name"),
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": f"File not found: {path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"GitHub API error: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def list_files(
        self,
        repo: str,
        path: str = "",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        List files in a directory.

        Args:
            repo: Repository in format "owner/repo"
            path: Path to directory (empty for root)
            branch: Branch name (default: main)

        Returns:
            Dictionary with file list or error info
        """
        url = f"{self.base_url}/repos/{repo}/contents/{path}"
        params = {"ref": branch}

        try:
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    files = []
                    for item in data:
                        files.append({
                            "name": item.get("name"),
                            "path": item.get("path"),
                            "type": item.get("type"),  # "file" or "dir"
                            "size": item.get("size"),
                            "sha": item.get("sha"),
                        })
                    return {
                        "success": True,
                        "files": files,
                        "count": len(files)
                    }
                else:
                    # Single file, not a directory
                    return {
                        "success": True,
                        "files": [{
                            "name": data.get("name"),
                            "path": data.get("path"),
                            "type": "file",
                            "size": data.get("size"),
                        }],
                        "count": 1
                    }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Path not found: {path or '/'}"
                }
            else:
                return {
                    "success": False,
                    "error": f"GitHub API error: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def get_repo_info(self, repo: str) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            repo: Repository in format "owner/repo"

        Returns:
            Dictionary with repo info or error
        """
        url = f"{self.base_url}/repos/{repo}"

        try:
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "name": data.get("name"),
                    "full_name": data.get("full_name"),
                    "description": data.get("description"),
                    "default_branch": data.get("default_branch"),
                    "private": data.get("private"),
                    "language": data.get("language"),
                    "stars": data.get("stargazers_count"),
                    "forks": data.get("forks_count"),
                }
            else:
                return {
                    "success": False,
                    "error": f"Repository not found or access denied: {repo}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def list_branches(self, repo: str) -> Dict[str, Any]:
        """
        List branches in a repository.

        Args:
            repo: Repository in format "owner/repo"

        Returns:
            Dictionary with branch list or error
        """
        url = f"{self.base_url}/repos/{repo}/branches"

        try:
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                branches = [b["name"] for b in response.json()]
                return {
                    "success": True,
                    "branches": branches,
                    "count": len(branches)
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not list branches: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def create_branch(
        self,
        repo: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a new branch.

        Args:
            repo: Repository in format "owner/repo"
            branch_name: Name for the new branch
            from_branch: Branch to create from (default: main)

        Returns:
            Dictionary with result or error
        """
        # First, get the SHA of the source branch
        ref_url = f"{self.base_url}/repos/{repo}/git/refs/heads/{from_branch}"

        try:
            ref_response = requests.get(ref_url, headers=self.headers)
            if ref_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Source branch not found: {from_branch}"
                }

            sha = ref_response.json()["object"]["sha"]

            # Create new branch
            create_url = f"{self.base_url}/repos/{repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": sha
            }

            create_response = requests.post(
                create_url,
                headers=self.headers,
                json=data
            )

            if create_response.status_code == 201:
                return {
                    "success": True,
                    "branch": branch_name,
                    "sha": sha
                }
            elif create_response.status_code == 422:
                return {
                    "success": False,
                    "error": f"Branch already exists: {branch_name}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create branch: {create_response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def create_or_update_file(
        self,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
        sha: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a file in the repository.

        Args:
            repo: Repository in format "owner/repo"
            path: Path for the file
            content: File content
            message: Commit message
            branch: Branch to commit to
            sha: SHA of existing file (required for updates)

        Returns:
            Dictionary with result or error
        """
        url = f"{self.base_url}/repos/{repo}/contents/{path}"

        # Encode content to base64
        encoded_content = base64.b64encode(content.encode()).decode()

        data = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }

        if sha:
            data["sha"] = sha

        try:
            response = requests.put(url, headers=self.headers, json=data)

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "path": result["content"]["path"],
                    "sha": result["content"]["sha"],
                    "commit_sha": result["commit"]["sha"],
                    "commit_url": result["commit"]["html_url"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create/update file: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a pull request.

        Args:
            repo: Repository in format "owner/repo"
            title: PR title
            body: PR body/description
            head: Source branch
            base: Target branch (default: main)

        Returns:
            Dictionary with PR info or error
        """
        url = f"{self.base_url}/repos/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)

            if response.status_code == 201:
                pr = response.json()
                return {
                    "success": True,
                    "number": pr["number"],
                    "url": pr["html_url"],
                    "title": pr["title"],
                    "state": pr["state"]
                }
            elif response.status_code == 422:
                error_data = response.json()
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message", "Validation failed") if errors else "Validation failed"
                return {
                    "success": False,
                    "error": f"PR creation failed: {error_msg}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create PR: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def list_prs(
        self,
        repo: str,
        state: str = "open"
    ) -> Dict[str, Any]:
        """
        List pull requests.

        Args:
            repo: Repository in format "owner/repo"
            state: PR state filter (open, closed, all)

        Returns:
            Dictionary with PR list or error
        """
        url = f"{self.base_url}/repos/{repo}/pulls"
        params = {"state": state}

        try:
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                prs = []
                for pr in response.json():
                    prs.append({
                        "number": pr["number"],
                        "title": pr["title"],
                        "state": pr["state"],
                        "url": pr["html_url"],
                        "user": pr["user"]["login"],
                        "created_at": pr["created_at"],
                    })
                return {
                    "success": True,
                    "pull_requests": prs,
                    "count": len(prs)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to list PRs: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }


def validate_github_token(token: str) -> Dict[str, Any]:
    """
    Validate a GitHub token by making a test API call.

    Args:
        token: GitHub personal access token

    Returns:
        Dictionary with validation result
    """
    if not token or not token.strip():
        return {
            "valid": False,
            "error": "Token is empty"
        }

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=headers
        )

        if response.status_code == 200:
            user = response.json()
            return {
                "valid": True,
                "username": user.get("login"),
                "name": user.get("name"),
                "scopes": response.headers.get("X-OAuth-Scopes", "")
            }
        elif response.status_code == 401:
            return {
                "valid": False,
                "error": "Invalid or expired token"
            }
        else:
            return {
                "valid": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Request failed: {str(e)}"
        }
