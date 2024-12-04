import os
import requests
from typing import List, Dict, Optional
import tempfile
import git
import subprocess
from datetime import datetime

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}' if self.token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = "https://api.github.com"

    def get_user_repos(self, username: str) -> List[Dict]:
        repos = []
        page = 1
        
        # First get owned repositories
        while True:
            if self.token:
                # If we have a token, use the authenticated endpoint
                url = f"{self.base_url}/user/repos"
                params = {
                    'per_page': 100,
                    'page': page,
                    'affiliation': 'owner,collaborator,organization_member'
                }
            else:
                # Without token, use the public endpoint
                url = f"{self.base_url}/users/{username}/repos"
                params = {
                    'per_page': 100,
                    'page': page
                }
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            batch = response.json()
            if not batch:
                break
                
            # If using authenticated endpoint, filter for the specific username
            if self.token:
                batch = [repo for repo in batch 
                        if repo['owner']['login'] == username 
                        or username in [collab['login'] for collab in self.get_collaborators(repo['full_name'])]]
            
            repos.extend(batch)
            page += 1
        
        return repos

    def get_collaborators(self, repo_full_name: str) -> List[Dict]:
        """Get list of collaborators for a repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{repo_full_name}/collaborators",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except:
            return []

    def get_authenticated_user(self) -> str:
        """Get the username of the authenticated user"""
        if not self.token:
            raise ValueError("GitHub token is required")
        
        response = requests.get(
            f"{self.base_url}/user",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['login']

    def analyze_repo_contributions(self, username: str, repo_name: str, repo_url: str, author_emails: List[str], year: Optional[int] = None) -> Dict:
        if self.token:
            repo_url = repo_url.replace('https://', f'https://{self.token}@')
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                repo = git.Repo.clone_from(repo_url, temp_dir)
                repo.git.fetch('--all')
                
                added = 0
                deleted = 0
                
                remote_refs = [ref for ref in repo.remote().refs]
                
                for ref in remote_refs:
                    try:
                        repo.git.checkout(ref, force=True)
                        
                        # Base git command
                        git_command = [
                            'git', 'log',
                            '--all',
                            '--pretty=tformat:',
                            '--numstat'
                        ]
                        
                        # Add year filter if specified (year is not None and not 'All time')
                        if year is not None:
                            git_command.extend(['--since', f'{year}-01-01', '--until', f'{year}-12-31'])
                        
                        # Add author parameters for username and all emails
                        git_command.extend(['--author', username])
                        for email in author_emails:
                            git_command.extend(['--author', email])
                        
                        result = subprocess.run(
                            git_command,
                            cwd=temp_dir,
                            capture_output=True,
                            text=True
                        )
                        
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                try:
                                    additions, deletions, _ = line.split('\t')
                                    if additions.isdigit() and deletions.isdigit():
                                        added += int(additions)
                                        deleted += int(deletions)
                                except ValueError:
                                    continue
                
                    except Exception as branch_error:
                        continue
                
                return {
                    'repository': repo_name,
                    'added_lines': added,
                    'deleted_lines': deleted,
                    'total_lines': added - deleted
                }
                
            except Exception as e:
                return {
                    'repository': repo_name,
                    'added_lines': 0,
                    'deleted_lines': 0,
                    'total_lines': 0,
                    'error': str(e)
                }