"""
🚀 Sketchfab Ultimate Search Actor - AI-Powered with LangGraph

This Actor searches for 3D models on Sketchfab using the BEST COMBINED STRATEGY:
1. **Query (q)** - SEO-optimized concise search keywords
2. **Tags** - Precise tags matching how users save models  
3. **Categories** - Auto-detected category slugs for filtering
4. **Pagination** - Full cursor-based pagination support (next/previous)

Features:
- LangGraph state machine for intelligent routing
- Google Gemini converts LONG user text → concise SEO query + smart tags
- Cursor-based pagination (count, cursor params)
- Default downloadable=true and smart defaults
- Comprehensive Sketchfab API integration
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse, parse_qs
from typing import TypedDict, Literal, Any, Optional

from apify import Actor
from httpx import AsyncClient
from pydantic import BaseModel, Field

# LangGraph imports
from langgraph.graph import StateGraph, END

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


# =============================================================================
# 📊 PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================

class SketchfabSearchParams(BaseModel):
    """Structured search parameters for Sketchfab API - ULTIMATE COMBINED STRATEGY"""
    # Core search - COMBINED: query + tags + categories
    q: str = Field(default="", description="SEO-optimized search query (2-5 words, concise)")
    tags: list[str] = Field(default_factory=list, description="Tag slugs for precise filtering")
    categories: list[str] = Field(default_factory=list, description="Category slugs")
    
    # Quality & type filters
    downloadable: Optional[bool] = Field(default=True, description="Only downloadable models - DEFAULT TRUE")
    animated: Optional[bool] = Field(default=None, description="Only animated models")
    rigged: Optional[bool] = Field(default=None, description="Only rigged models")
    staffpicked: Optional[bool] = Field(default=None, description="Staff-picked only")
    sound: Optional[bool] = Field(default=None, description="Models with sound")
    
    # Technical specs
    pbr_type: Optional[str] = Field(default=None, description="PBR workflow type")
    file_format: Optional[str] = Field(default=None, description="File format")
    license: Optional[str] = Field(default=None, description="License type")
    
    # Geometry constraints
    min_face_count: Optional[int] = Field(default=None, description="Minimum polygon faces")
    max_face_count: Optional[int] = Field(default=None, description="Maximum polygon faces")
    
    # Sorting & filtering
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    date: Optional[int] = Field(default=None, description="Last X days")


# =============================================================================
# 🧠 LANGGRAPH STATE DEFINITION
# =============================================================================

class GraphState(TypedDict):
    """State for LangGraph workflow"""
    # Input
    actor_input: dict
    natural_query: str
    use_ai: bool
    
    # Pagination
    cursor: Optional[str]  # Cursor for pagination
    count: int             # Items per page (default 24)
    
    # Processing
    search_params: dict
    route: str
    
    # Output
    results: list
    pagination: dict  # next, previous URLs + cursors
    error: Optional[str]
    metadata: dict


# =============================================================================
# 🎯 SYSTEM PROMPT - ULTIMATE SEARCH OPTIMIZATION
# =============================================================================

SEARCH_SYSTEM_PROMPT = """You are an EXPERT Sketchfab SEO search optimizer. Your job is to convert ANY user text (even long paragraphs) into the PERFECT search parameters that will find exactly what they want.

🎯 YOUR MISSION:
1. **Extract a CONCISE SEO query (q)** - 2-5 words MAX that Sketchfab search will understand
2. **Generate PRECISE tags** - 2-6 tags that match how artists TAG their models
3. **Auto-detect category** - ONLY if clearly detectable, otherwise omit

⚠️ CRITICAL RULES:
- **q field**: Must be SHORT, SEO-friendly (2-5 words). Extract the CORE subject.
- **tags**: Slugified (lowercase-hyphens), 2-6 tags covering style/purpose/type
- **categories**: ONLY include if 100% confident. If unsure, OMIT entirely.
- **downloadable**: ALWAYS true unless user explicitly says "preview only"

---------------------------------------------------
## BREAKDOWN STRATEGY FOR LONG TEXT
---------------------------------------------------

User input: "I need a really cool futuristic sports car that looks like something from cyberpunk 2077 with neon lights and maybe some damage on it, low poly would be nice for my game project in Unity"

Breakdown:
- Core subject: "sports car" → q: "cyberpunk sports car"
- Style: futuristic, cyberpunk, neon → tags: ["cyberpunk", "futuristic", "neon"]
- Quality: low-poly, game → tags: ["low-poly", "game-ready"]
- Modifiers: damaged → tags: ["damaged", "weathered"]
- Category: cars-vehicles (100% confident)

Result: q="cyberpunk sports car", tags=["cyberpunk", "low-poly", "game-ready", "neon", "futuristic"], categories=["cars-vehicles"]

---------------------------------------------------
## CATEGORY SLUGS (ONLY use if 100% confident)
---------------------------------------------------
- animals-pets (animals, pets, creatures from nature)
- architecture (buildings, interiors, exteriors)
- art-abstract (abstract art, sculptures)
- cars-vehicles (cars, trucks, bikes, planes, boats)
- characters-creatures (humanoids, monsters, fantasy creatures)
- cultural-heritage-history (historical, museums, ancient)
- electronics-gadgets (phones, computers, tech devices)
- fashion-style (clothing, accessories, jewelry)
- food-drink (food items, beverages)
- furniture-home (furniture, decor, household)
- music (instruments, music equipment)
- nature-plants (trees, plants, rocks, terrain)
- news-politics (news related, political)
- people (realistic humans, portraits)
- places-travel (landmarks, cities, landscapes)
- science-technology (robots, sci-fi, tech)
- sports-fitness (sports equipment, fitness)
- weapons-military (guns, swords, military vehicles)

---------------------------------------------------
## OUTPUT FORMAT (JSON ONLY)
---------------------------------------------------

{
  "q": "concise search query",           // 2-5 words, REQUIRED
  "tags": ["tag1", "tag2"],              // 2-6 slugified tags
  "categories": ["category-slug"],        // ONLY if 100% confident, else omit
  "downloadable": true,                   // DEFAULT TRUE
  "animated": null,                       // true if animation mentioned
  "rigged": null,                         // true if rig/skeleton mentioned
  "staffpicked": null,                    // true for "best quality"
  "pbr_type": null,                       // "true" if PBR mentioned
  "file_format": null,                    // gltf, fbx, blend, obj
  "max_face_count": null,                 // integer if poly limit mentioned
  "sort_by": null                         // likes, views, recent
}

---------------------------------------------------
## EXAMPLES
---------------------------------------------------

"i want a low poly car for my mobile game, something cartoony"
→ {{"q": "cartoon car", "tags": ["low-poly", "cartoon", "game-ready", "mobile"], "categories": ["cars-vehicles"], "downloadable": true}}

"looking for a realistic human character model with full body rig and facial expressions for animation in blender, preferably CC0 license"
→ {{"q": "realistic human character", "tags": ["realistic", "rigged", "full-body", "facial-rig"], "categories": ["characters-creatures"], "downloadable": true, "rigged": true, "file_format": "blend", "license": "CC0"}}

"sci fi robot mech warrior"
→ {{"q": "sci-fi mech robot", "tags": ["sci-fi", "mech", "robot", "warrior"], "categories": ["science-technology"], "downloadable": true}}

"tree"
→ {{"q": "tree", "tags": ["tree", "nature"], "categories": ["nature-plants"], "downloadable": true}}

"I need some kind of medieval fantasy weapon, like a sword or axe, with magical glowing effects, high detail for a AAA game cutscene render"
→ {{"q": "medieval fantasy weapon", "tags": ["medieval", "fantasy", "sword", "magical", "high-poly", "detailed"], "categories": ["weapons-military"], "downloadable": true, "staffpicked": true}}

---------------------------------------------------
Return ONLY the JSON object, no markdown, no explanation.
"""


# =============================================================================
# 🔧 HELPER FUNCTIONS
# =============================================================================

def parse_cursor_from_url(url: str) -> Optional[str]:
    """Extract cursor value from a Sketchfab API URL"""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get("cursor", [None])[0]
    except Exception:
        return None


def extract_pagination_info(api_response: dict) -> dict:
    """Extract pagination info from Sketchfab API response"""
    return {
        "next_url": api_response.get("next"),
        "previous_url": api_response.get("previous"),
        "next_cursor": parse_cursor_from_url(api_response.get("next")),
        "previous_cursor": parse_cursor_from_url(api_response.get("previous")),
        "has_next": api_response.get("next") is not None,
        "has_previous": api_response.get("previous") is not None,
    }


# =============================================================================
# 🔀 LANGGRAPH NODE FUNCTIONS
# =============================================================================

def route_decision(state: GraphState) -> Literal["ai_processing", "manual_processing"]:
    """Router node - decides which path to take based on useAI flag"""
    if state["use_ai"] and state["natural_query"]:
        return "ai_processing"
    return "manual_processing"


async def ai_processing_node(state: GraphState) -> GraphState:
    """AI Processing Node - Uses LangChain to convert natural language to search params"""
    Actor.log.info("🤖 AI Processing: Converting long text → SEO query + tags...")
    
    try:
        # Get API key from environment or input
        api_key = os.environ.get("GOOGLE_API_KEY") or state["actor_input"].get("googleApiKey")
        
        if not api_key:
            Actor.log.warning("⚠️ No Google API key found, falling back to basic extraction")
            # Fallback: use first few words as query, rest as tags
            words = state["natural_query"].lower().split()
            q = " ".join(words[:3])
            tags = [w.replace(" ", "-") for w in words[:5] if len(w) > 2]
            state["search_params"] = {"q": q, "tags": tags, "downloadable": True}
            state["metadata"]["ai_used"] = False
            state["metadata"]["fallback"] = True
            return state
        
        # Initialize Gemini via LangChain
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.1,  # Low temp for consistent results
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", SEARCH_SYSTEM_PROMPT),
            ("human", "Convert this to optimal Sketchfab search parameters: \"{query}\"")
        ])
        
        # JSON output parser
        parser = JsonOutputParser(pydantic_object=SketchfabSearchParams)
        
        # Create chain
        chain = prompt | llm | parser
        
        # Execute
        result = await chain.ainvoke({"query": state["natural_query"]})
        
        # Ensure downloadable is true by default
        if "downloadable" not in result or result["downloadable"] is None:
            result["downloadable"] = True
        
        Actor.log.info(f"🎯 AI-generated params:")
        Actor.log.info(f"   q: {result.get('q', '')}")
        Actor.log.info(f"   tags: {result.get('tags', [])}")
        Actor.log.info(f"   categories: {result.get('categories', [])}")
        
        state["search_params"] = result
        state["metadata"]["ai_used"] = True
        state["metadata"]["original_query"] = state["natural_query"]
        state["metadata"]["generated_q"] = result.get("q", "")
        state["metadata"]["generated_tags"] = result.get("tags", [])
        
    except Exception as e:
        Actor.log.error(f"❌ AI processing error: {e}")
        # Fallback to basic extraction
        words = state["natural_query"].lower().split()
        q = " ".join(words[:3])
        tags = [w.replace(" ", "-") for w in words[:5] if len(w) > 2]
        state["search_params"] = {"q": q, "tags": tags, "downloadable": True}
        state["metadata"]["ai_used"] = False
        state["metadata"]["ai_error"] = str(e)
    
    return state


async def manual_processing_node(state: GraphState) -> GraphState:
    """Manual Processing Node - Uses provided filters directly"""
    Actor.log.info("🎛️ Manual Processing: Using provided filters...")
    
    # Extract search params from actor input (excluding control flags)
    excluded_keys = {"useAI", "naturalQuery", "googleApiKey", "cursor", "count"}
    search_params = {
        k: v for k, v in state["actor_input"].items() 
        if k not in excluded_keys and v is not None and v != "" and v != []
    }
    
    # Ensure downloadable is true by default if not specified
    if "downloadable" not in search_params:
        search_params["downloadable"] = True
    
    state["search_params"] = search_params
    state["metadata"]["ai_used"] = False
    
    return state


async def sketchfab_api_node(state: GraphState) -> GraphState:
    """Sketchfab API Node - Executes the search with pagination support"""
    Actor.log.info("🔍 Executing Sketchfab API search...")
    
    try:
        # Build API params
        params = {"type": "models"}
        
        # Add search params
        for key, value in state["search_params"].items():
            if value is not None and value != "" and value != []:
                params[key] = value
        
        # Add pagination params
        params["count"] = state["count"]
        if state["cursor"]:
            params["cursor"] = state["cursor"]
            Actor.log.info(f"📄 Using cursor for pagination: {state['cursor']}")
        
        Actor.log.info(f"📤 API params: {params}")
        
        # Make API request
        url = "https://api.sketchfab.com/v3/search"
        async with AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        
        # Extract pagination info
        pagination = extract_pagination_info(data)
        
        state["results"] = results
        state["pagination"] = pagination
        state["metadata"]["result_count"] = len(results)
        state["metadata"]["api_url"] = str(response.url)
        
        Actor.log.info(f"✅ Found {len(results)} models")
        Actor.log.info(f"📄 Pagination: has_next={pagination['has_next']}, has_previous={pagination['has_previous']}")
        
    except Exception as e:
        Actor.log.error(f"❌ Sketchfab API error: {e}")
        state["error"] = str(e)
        state["results"] = []
        state["pagination"] = {}
    
    return state


async def output_node(state: GraphState) -> GraphState:
    """Output Node - Pushes results to Apify dataset"""
    Actor.log.info("💾 Saving results to dataset...")
    
    # Push metadata first (includes pagination info)
    await Actor.push_data({
        "_metadata": True,
        "search_params": state["search_params"],
        "ai_powered": state["metadata"].get("ai_used", False),
        "original_query": state["metadata"].get("original_query"),
        "generated_q": state["metadata"].get("generated_q"),
        "generated_tags": state["metadata"].get("generated_tags", []),
        "result_count": state["metadata"].get("result_count", 0),
        "pagination": state["pagination"],
        "error": state.get("error"),
    })
    
    # Push each result
    for result in state["results"]:
        await Actor.push_data(result)
    
    return state


# =============================================================================
# 🏗️ LANGGRAPH WORKFLOW BUILDER
# =============================================================================

def build_search_graph() -> StateGraph:
    """Build the LangGraph workflow for model search"""
    
    # Create graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("ai_processing", ai_processing_node)
    workflow.add_node("manual_processing", manual_processing_node)
    workflow.add_node("sketchfab_api", sketchfab_api_node)
    workflow.add_node("output", output_node)
    
    # Set conditional entry point based on useAI flag
    workflow.set_conditional_entry_point(
        route_decision,
        {
            "ai_processing": "ai_processing",
            "manual_processing": "manual_processing"
        }
    )
    
    # Add edges
    workflow.add_edge("ai_processing", "sketchfab_api")
    workflow.add_edge("manual_processing", "sketchfab_api")
    workflow.add_edge("sketchfab_api", "output")
    workflow.add_edge("output", END)
    
    return workflow.compile()


# =============================================================================
# 🚀 MAIN ENTRY POINT
# =============================================================================

async def main() -> None:
    """Main entry point for the Apify Actor"""
    async with Actor:
        Actor.log.info("🚀 Starting Sketchfab Ultimate Search Actor (Query + Tags + Pagination)")
        
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Extract control flags
        use_ai = actor_input.get("useAI", False)
        natural_query = actor_input.get("naturalQuery", "")
        
        # Pagination params
        cursor = actor_input.get("cursor")  # For pagination
        count = actor_input.get("count", 24)  # Items per page, default 24
        
        Actor.log.info(f"📥 Input received:")
        Actor.log.info(f"   useAI: {use_ai}")
        Actor.log.info(f"   query: '{natural_query[:50]}{'...' if len(natural_query) > 50 else ''}'")
        Actor.log.info(f"   cursor: {cursor}")
        Actor.log.info(f"   count: {count}")
        
        # Initialize state
        initial_state: GraphState = {
            "actor_input": actor_input,
            "natural_query": natural_query,
            "use_ai": use_ai,
            "cursor": cursor,
            "count": count,
            "search_params": {},
            "route": "",
            "results": [],
            "pagination": {},
            "error": None,
            "metadata": {}
        }
        
        # Build and run graph
        graph = build_search_graph()
        
        Actor.log.info("🔄 Executing LangGraph workflow...")
        
        # Execute the graph
        final_state = await graph.ainvoke(initial_state)
        
        # Log summary
        result_count = final_state["metadata"].get("result_count", 0)
        ai_used = final_state["metadata"].get("ai_used", False)
        pagination = final_state.get("pagination", {})
        
        Actor.log.info(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🎉 SEARCH COMPLETE                                              ║
╠══════════════════════════════════════════════════════════════════╣
║  Mode: {'🤖 AI-Powered (SEO Optimized)' if ai_used else '🎛️ Manual Filters'}                     ║
║  Results: {result_count} models found                                       ║
║  Query (q): {final_state['search_params'].get('q', 'N/A')[:30]}
║  Tags: {final_state['search_params'].get('tags', [])[:4]}
║  Has Next Page: {pagination.get('has_next', False)}                                       ║
║  Has Previous: {pagination.get('has_previous', False)}                                      ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        if pagination.get("next_cursor"):
            Actor.log.info(f"📄 Next cursor for pagination: {pagination['next_cursor']}")
        
        if final_state.get("error"):
            Actor.log.error(f"⚠️ Error occurred: {final_state['error']}")
