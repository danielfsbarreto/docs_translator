from typing import Optional

from pydantic import BaseModel, Field


class IdentifyDocsRepoDirOutput(BaseModel):
    docs_dir: Optional[str] = Field(
        ..., description="The relative path to the docs directory."
    )


class File(BaseModel):
    path: str = Field(..., description="The path of the file.")
    content: Optional[str] = Field(
        None, description="The content of the file in the original language."
    )
    content_translated: Optional[str] = Field(
        None,
        description="The content of the file already translated to the desired language.",
    )


class ListFilesToTranslateOutput(BaseModel):
    files: list[File] = Field(
        default_factory=list, description="The list of files to translate."
    )


class DocsTranslatorState(BaseModel):
    repo_path: str = "crewAIInc/crewAI"
    docs_dir: str = "docs"
    files: list[File] = Field(default_factory=list)
    whitelist_paths: list[str] = Field(
        default_factory=list,
        description="The list of paths to files that should be translated.",
    )
