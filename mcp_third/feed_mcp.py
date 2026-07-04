from fastmcp import FastMCP
import feedparser

mcp = FastMCP(name="FreeCodeCamp Feed Searcher")

@mcp.tool()
def fcc_new_search(query:str, max_results:int=3):
    """Search freecodecamp news feed via RSS by title/description"""
    feed = feedparser.parse("https://www.freecodecamp.org/news/rss/")
    results = []
    query_lower = query.lower()
    
    for entry in feed.entries:
        title = entry.get("title", '')
        description = entry.get("description", '')
        
        if query_lower in title.lower() or query_lower in description.lower():
            results.append({"title": title, "url": entry.get("link", "")})
        if len(results) >= max_results:
            break
        
    return results or [{"message":"No results found"}]

@mcp.tool()
def fcc_youtube_search(query:str, max_results: int=3):
    """Search FreeCodeCamp Youtube Channel via RSS by title"""
    feed = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UC8butISFwT-Wl7EV0hUK0BQ")
    results = []
    query_lower = query.lower()
    for entry in feed.entries:
        title = entry.get("title", "")
        if query_lower in title.lower():
            results.append({"title": title, "url":entry.get("link", "")})
        if len(results) >= max_results:
            break
    return results or [{"message": "No results found"}]

@mcp.tool()
def fcc_secret_message():
    """Returns a secret message"""
    return "hi im rio"

if __name__ == "__main__":
        mcp.run() #STDIO