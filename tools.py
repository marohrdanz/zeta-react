from langchain_core.tools import tool
from log_setup import configure_logging
from ddgs import DDGS

logger = configure_logging()

# --- Define Tools ---

# The docstrings are important for the model to understand how to use the tools,
# so be sure to include clear instructions and examples.
# The @tool decorator is what makes these functions available as tools that
# the model can call during the conversation.

@tool
def get_major_scale(key: str) -> list[str]:
    """Given a musical key, return the major scale for that key.

    Example input: 'C'

    Example output for 'C': ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    """
    # All notes in chromatic scale (using sharps)
    chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Enharmonic equivalents (flat -> sharp)
    enharmonic = {
        "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#",
        "Ab": "G#", "Bb": "A#", "Cb": "B"
    }

    # Major scale interval pattern: W W H W W W H
    # (in semitones: 2 2 1 2 2 2 1)
    intervals = [2, 2, 1, 2, 2, 2, 1]

    # Normalize the key
    key = key.strip().capitalize()
    if len(key) > 1:
        key = key[0].upper() + key[1:].lower()
    key = enharmonic.get(key, key)

    if key not in chromatic:
        raise ValueError(f"Invalid key: '{key}'. Use note names like C, D#, Bb, etc.")

    # Build the scale
    start = chromatic.index(key)
    scale = []
    pos = start
    for interval in intervals:
        scale.append(chromatic[pos % 12])
        pos += interval

    return scale

@tool
def get_blues_scale(key: str) -> list[str]:
    """Given a musical key, return the blues scale for that key.

    Example input: 'C'

    Example output for 'C': ['C', 'Eb', 'F', 'Gb', 'G', 'Bb']
    """
    # All notes in chromatic scale
    chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Enharmonic equivalents (flat -> sharp)
    enharmonic = {
        "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#",
        "Ab": "G#", "Bb": "A#", "Cb": "B"
    }

    # Blues scale intervals (semitones): 3 2 1 1 3 2
    # Formula: Root, b3, 4, b5, 5, b7, Root
    intervals = [3, 2, 1, 1, 3, 2]

    # Normalize the key
    key = key.strip()
    if len(key) > 1:
        key = key[0].upper() + key[1:].lower()
    else:
        key = key.upper()
    key = enharmonic.get(key, key)

    if key not in chromatic:
        raise ValueError(f"Invalid key: '{key}'. Use note names like C, D#, Bb, etc.")

    # Build the scale
    start = chromatic.index(key)
    scale = []
    pos = start
    for interval in intervals:
        scale.append(chromatic[pos % 12])
        pos += interval

    return scale


@tool
def search(query: str) -> str:
    """Search the web for information about a topic."""
    try:
      with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        if not results:
          return "No results found."
        formatted = "\n\n".join(
            f"{r['title']}\n{r['href']}\n{r['body']}"
            for r in results
        )
        return formatted
    except Exception as e:
      logger.error(f"Search.run failed for {query}: {e}")
      result = f"Error: {e}"
    return result


tools = [search, get_major_scale, get_blues_scale]
