#!/usr/bin/env python

import asyncio
import os

from crewai.flow import Flow, listen, start

from docs_translator.agents import docs_developer, translator
from docs_translator.types import (
    DocsTranslatorState,
    IdentifyDocsRepoDirOutput,
    ListFilesToTranslateOutput,
)


class DocsTranslatorFlow(Flow[DocsTranslatorState]):
    @start()
    def identify_docs_repo_dir(self):
        result = docs_developer.kickoff(
            f"""
            Identify the path to the docs repo.
            It can be found at "{self.state.repo_path}".

            IMPORTANT NOTES:
            - Use only the "Repo Docs Directory Inspector" tool to answer this.
            """,
            response_format=IdentifyDocsRepoDirOutput,
        )
        self.state.docs_dir = result.pydantic.docs_dir  # type: ignore

    @listen(identify_docs_repo_dir)
    def list_files_to_translate(self):
        result = docs_developer.kickoff(
            f"""
            List all the docs files in the repo.
            They can be found at:
            - Repo => "{self.state.repo_path}"
            - Docs directory => "{self.state.docs_dir}"

            IMPORTANT NOTES:
            - Use only the "Identify Docs Files" tool to answer this.
            - Make sure the number of files returned in the final answer matches the number of files found in the repo.
            """,
            response_format=ListFilesToTranslateOutput,
        )
        self.state.files = result.pydantic.files  # type: ignore

    @listen(list_files_to_translate)
    async def fetch_files_content(self):
        async def fetch_single_file(file):
            result = await docs_developer.kickoff_async(
                f"""
                Collect the content of the file that needs to be translated.
                - Repo => "{self.state.repo_path}"
                - File => "{file.path}"

                IMPORTANT NOTES:
                - Use only the "Retrieve Individual Docs File" tool to answer this.
                """,
            )
            file.content = result.raw

        files_to_process = [file for file in self.state.files if file.content is None]
        batch_size = 10
        delay_between_batches = 3
        for i in range(0, len(files_to_process), batch_size):
            batch = files_to_process[i : i + batch_size]
            print(
                f"\033[31m\n>> [fetch_files_content] Starting batch {i // batch_size + 1} of {(len(files_to_process) + batch_size - 1) // batch_size}\033[0m"
            )
            tasks = [fetch_single_file(file) for file in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(delay_between_batches)

    @listen(fetch_files_content)
    async def translate_files(self):
        async def translate_single_file(file):
            result = await translator.kickoff_async(
                f"""
                Translate the content of the file.
                - File => "{file.path}"
                - File content => "{file.content}"
                - Desired language => "pt-BR"

                IMPORTANT NOTES:
                - Do not mess up with the .mdx syntax content.
                - Do not translate any code blocks.
                - Do not translate any entity names like "crew", "flow" or "agent".
                - Output only the translated content, no other text.
                """
            )
            file.content_translated = result.raw

        files_to_process = [
            file for file in self.state.files if file.content_translated is None
        ]
        batch_size = 10
        delay_between_batches = 3
        for i in range(0, len(files_to_process), batch_size):
            batch = files_to_process[i : i + batch_size]
            print(
                f"\033[31m\n>> [translate_files] Starting batch {i // batch_size + 1} of {(len(files_to_process) + batch_size - 1) // batch_size}\033[0m"
            )
            tasks = [translate_single_file(file) for file in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(delay_between_batches)

    @listen(translate_files)
    async def double_check_translations(self):
        async def double_check_single_file(file):
            result = await translator.kickoff_async(
                f"""
                Double check the translation of the file. Ensure they are all high-quality.
                - File => "{file.path}"
                - File content => "{file.content}"
                - File content already translated => "{file.content_translated}"
                - Desired language => "pt-BR"

                IMPORTANT NOTES:
                - Do not mess up with the .mdx syntax content.
                - Do not translate any code blocks.
                - Do not translate any entity names like "crew", "flow" or "agent".
                - Output only the translated content, no other text.
                """
            )
            file.content_translated = result.raw

        files_to_process = [file for file in self.state.files]
        batch_size = 10
        delay_between_batches = 3
        for i in range(0, len(files_to_process), batch_size):
            batch = files_to_process[i : i + batch_size]
            print(
                f"\033[31m\n>> [double_check_translations] Starting batch {i // batch_size + 1} of {(len(files_to_process) + batch_size - 1) // batch_size}\033[0m"
            )
            tasks = [double_check_single_file(file) for file in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(delay_between_batches)

    @listen(double_check_translations)
    def save_files(self):
        base_dir = f"tmp/{self.state.id}"  # type: ignore
        for file in self.state.files:
            full_file_path = os.path.join(base_dir, file.path)
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            with open(full_file_path, "w") as f:
                f.write(file.content_translated)  # type: ignore


def kickoff():
    DocsTranslatorFlow().kickoff()


def plot():
    DocsTranslatorFlow().plot()


if __name__ == "__main__":
    kickoff()
