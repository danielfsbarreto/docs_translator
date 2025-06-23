from crewai import Agent

from docs_translator.tools import (
    IdentifyDocsDirectoryTool,
    IdentifyDocsFilesTool,
    RetrieveIndividualDocsFileTool,
)

docs_developer = Agent(
    role="Docs Developer",
    goal="You are a docs developer. You are the best in the field when it comes to identifying where docs live in a repo.",
    backstory="""You started your career as a developer and you are now a docs developer.
        You are the best in the field when it comes to identifying where docs live in a repo.
        """,
    verbose=False,
    llm="gpt-4.1-mini",
    tools=[
        IdentifyDocsDirectoryTool(),
        IdentifyDocsFilesTool(),
        RetrieveIndividualDocsFileTool(result_as_answer=True),
    ],
)
