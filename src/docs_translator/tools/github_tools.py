import os
from typing import Type

from crewai.tools import BaseTool
from github import Auth, Github
from pydantic import BaseModel, Field

from docs_translator.types import File


class GithubTool(BaseTool):
    @property
    def github(self) -> Github:
        auth = Auth.Token(os.getenv("GITHUB_AUTH_KEY", ""))
        return Github(auth=auth)


class IdentifyDocsDirectoryTool(GithubTool):
    class IdentifyDocsDirectoryToolInput(BaseModel):
        """Input schema for IdentifyDocsDirectoryTool."""

        repo_path: str = Field(..., description="The path of the repo to inspect.")

    name: str = "Repo Docs Folder Inspector"
    description: str = "Inspect a repo and return all its internal folders."
    args_schema: Type[BaseModel] = IdentifyDocsDirectoryToolInput

    def _run(self, repo_path: str) -> list[str]:
        repo = self.github.get_repo(repo_path)
        sha = repo.get_branch(repo.default_branch).commit.sha
        tree = repo.get_git_tree(sha=sha, recursive=True).tree

        directories = []

        for element in tree:
            if element.type == "tree":
                directories.append(element.path)

        return directories


class IdentifyDocsFilesTool(GithubTool):
    class IdentifyDocsFilesToolInput(BaseModel):
        """Input schema for IdentifyDocsFilesTool."""

        repo_path: str = Field(..., description="The path of the repo to inspect.")
        docs_dir: str = Field(..., description="The path of the docs directory.")

    name: str = "Identify Docs Files"
    description: str = "Fetch all the docs files in the repo."
    args_schema: Type[BaseModel] = IdentifyDocsFilesToolInput

    def _run(self, repo_path: str, docs_dir: str) -> list[File]:
        repo = self.github.get_repo(repo_path)
        sha = repo.get_branch(repo.default_branch).commit.sha
        tree = repo.get_git_tree(sha=sha, recursive=True).tree

        return [
            File(
                path=item.path,
                content=None,
                content_translated=None,
            )
            for item in tree
            if item.path.startswith(docs_dir + "/")
            and item.path.endswith((".mdx", ".md"))
        ]


class RetrieveIndividualDocsFileTool(GithubTool):
    class RetrieveIndividualDocsFileToolInput(BaseModel):
        """Input schema for RetrieveIndividualDocsFileTool."""

        repo_path: str = Field(..., description="The path of the repo to inspect.")
        file_path: str = Field(..., description="The path of the file to fetch.")

    name: str = "Retrieve Individual Docs File"
    description: str = "Fetch an individual file from the repo."
    args_schema: Type[BaseModel] = RetrieveIndividualDocsFileToolInput

    def _run(self, repo_path: str, file_path: str) -> str:
        repo = self.github.get_repo(repo_path)
        contents = repo.get_contents(file_path)

        return contents.decoded_content.decode("utf-8")  # type: ignore
