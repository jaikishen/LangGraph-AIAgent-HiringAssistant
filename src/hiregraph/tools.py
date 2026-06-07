from langchain_core.tools import tool
from hiregraph.services import tavily_search as svc_tavily, github_profile as svc_github


@tool
def search_web(query: str) -> str:
    """Search the web for information about a candidate or topic.

    Use this to look up public writing, conference talks, or professional presence.
    Returns a summary of the top results.
    """
    print(f"[tool called] search_web: {query}")
    results = svc_tavily(query)
    if not results:
        return "No results found."
    return "\n".join(
        f"- {r.get('title', 'Untitled')}: {r.get('content', '')[:200]}"
        for r in results[:3]
    )


@tool
def lookup_github(username: str) -> str:
    """Look up a public GitHub profile by username.

    Returns repository count, top languages, and bio.
    Extract the username from the resume's GitHub URL if available.
    """
    profile = svc_github(username)
    return (
        f"GitHub profile for {username}: "
        f"{profile.get('repos', 0)} public repos, "
        f"languages: {profile.get('languages', [])}, "
        f"bio: {profile.get('bio', 'none')}"
    )
