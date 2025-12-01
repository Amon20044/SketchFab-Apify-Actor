"""
🚀 Sketchfab Model Search Actor - AI-Powered with LangGraph

This Actor searches for 3D models on Sketchfab using either:
1. Manual filters (useAI=false) - Direct API query with provided parameters
2. AI-powered NLP (useAI=true) - Natural language converted to search params via LangGraph

Features:
- LangGraph state machine for intelligent routing
- Google Gemini integration for NLP
- Conditional execution based on useAI flag
- Comprehensive Sketchfab API integration
"""

from __future__ import annotations

import os
from typing import TypedDict, Literal, Any, Optional
from dataclasses import dataclass, field

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
    """Structured search parameters for Sketchfab API"""
    # Core search
    q: str = Field(default="", description="Main search keywords (2-6 words)")
    user: Optional[str] = Field(default=None, description="Sketchfab username")
    tags: list[str] = Field(default_factory=list, description="Tag slugs")
    categories: list[str] = Field(default_factory=list, description="Category slugs")
    
    # Quality & type filters
    downloadable: Optional[bool] = Field(default=None, description="Only downloadable models")
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
    max_uv_layer_count: Optional[int] = Field(default=None, description="Max UV layers")
    
    # Archive constraints
    available_archive_type: Optional[str] = Field(default=None, description="Archive type")
    archives_max_size: Optional[int] = Field(default=None, description="Max archive size in bytes")
    archives_max_face_count: Optional[int] = Field(default=None, description="Max faces in archive")
    archives_max_vertex_count: Optional[int] = Field(default=None, description="Max vertices in archive")
    archives_max_texture_count: Optional[int] = Field(default=None, description="Max texture count")
    archives_texture_max_resolution: Optional[int] = Field(default=None, description="Max texture resolution")
    archives_flavours: Optional[bool] = Field(default=None, description="All texture resolutions")
    
    # Sorting & filtering
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    date: Optional[int] = Field(default=None, description="Last X days")
    collection: Optional[str] = Field(default=None, description="Collection UID")


# =============================================================================
# 🧠 LANGGRAPH STATE DEFINITION
# =============================================================================

class GraphState(TypedDict):
    """State for LangGraph workflow"""
    # Input
    actor_input: dict
    natural_query: str
    use_ai: bool
    
    # Processing
    search_params: dict
    route: str
    
    # Output
    results: list
    error: Optional[str]
    metadata: dict


# =============================================================================
# 🎯 SYSTEM PROMPT FOR NLP CONVERSION
# =============================================================================

SEARCH_SYSTEM_PROMPT = """You are an expert 3D model search assistant for Sketchfab. Convert any natural language search query into precise, structured Sketchfab search parameters.

IMPORTANT: All fields except "q" MUST be returned as SLUGS (lowercase, hyphens). 
Only "q" stays human-readable text. Everything else must match the API slug format.

Return ONLY valid parameters as a JSON object. If a value is not relevant, omit it.

---------------------------------------------------
## VALID PARAMETERS (STRICT, SLUG OUTPUT)
---------------------------------------------------

### Core Search
- q (string, normal text, not slugified) - REQUIRED, 2-6 words max
- user (string, slugified)
- tags (array[string], slugs)
- categories (array[string], slugs ONLY):
  - animals-pets
  - architecture
  - art-abstract
  - cars-vehicles
  - characters-creatures
  - cultural-heritage-history
  - electronics-gadgets
  - fashion-style
  - food-drink
  - furniture-home
  - music
  - nature-plants
  - news-politics
  - people
  - places-travel
  - science-technology
  - sports-fitness
  - weapons-military

### Date (integer, in days)
- "all-time" → omit date
- "this-month" → 30
- "this-week" → 7
- "today" → 1

### Sort By (STRICT SLUG OUTPUT)
- relevance
- likes
- views
- recent
- publishedAt

### Boolean Filters
- downloadable (boolean) - defaults to true unless user says otherwise
- animated (boolean)
- rigged (boolean)
- staffpicked (boolean)
- sound (boolean)

### Technical Specs
- pbr_type: metalness | specular | true | false
- file_format: obj | fbx | blend | gltf | stl | ply | dae | x3d
- license: CC0 | CC-BY | CC-BY-SA | CC-BY-ND | CC-BY-NC | CC-BY-NC-SA | CC-BY-NC-ND

License inference:
- "no attribution" → CC0
- "commercial use" → CC0 or CC-BY
- "non-commercial" → CC-BY-NC

### Geometry Constraints (integers)
- min_face_count
- max_face_count
- max_uv_layer_count

### Archive Constraints (integers)
- archives_max_size (bytes)
- archives_max_face_count
- archives_max_vertex_count
- archives_max_texture_count
- archives_texture_max_resolution

---------------------------------------------------
## SMART RULES
---------------------------------------------------

1. Keep "q" short (2-6 words), move descriptors into tags
2. Infer categories:
   - "car" → cars-vehicles
   - "gun" → weapons-military
   - "tree" → nature-plants
   - "robot" → science-technology
   - "human" → characters-creatures
3. Set downloadable=true by default unless user says "preview only"
4. Set staffpicked=true for "best", "top quality", "curated", "featured"
5. Set animated=true for "animation", "animated"
6. Set rigged=true for "rig", "skeleton", "bones"

---------------------------------------------------
## EXAMPLES
---------------------------------------------------

"low poly game-ready cars under 10k faces, glb"
→ {{"q": "cars", "tags": ["low-poly", "game-ready"], "categories": ["cars-vehicles"], "file_format": "gltf", "max_face_count": 10000, "downloadable": true}}

"free downloadable robots with animation, no attribution"
→ {{"q": "robots", "categories": ["science-technology"], "downloadable": true, "animated": true, "license": "CC0"}}

"best high quality characters rigged for blender"
→ {{"q": "characters", "categories": ["characters-creatures"], "staffpicked": true, "rigged": true, "file_format": "blend", "downloadable": true}}

---------------------------------------------------
Return ONLY the JSON object, no markdown, no explanation.
"""


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
    Actor.log.info("🤖 AI Processing: Converting natural language query...")
    
    try:
        # Get API key from environment or input
        api_key = os.environ.get("GOOGLE_API_KEY") or state["actor_input"].get("googleApiKey")
        
        if not api_key:
            Actor.log.warning("⚠️ No Google API key found, falling back to basic extraction")
            # Fallback: use the query as-is
            state["search_params"] = {"q": state["natural_query"], "downloadable": True}
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
            ("human", "Convert this search query to Sketchfab parameters: \"{query}\"")
        ])
        
        # JSON output parser
        parser = JsonOutputParser(pydantic_object=SketchfabSearchParams)
        
        # Create chain
        chain = prompt | llm | parser
        
        # Execute
        result = await chain.ainvoke({"query": state["natural_query"]})
        
        Actor.log.info(f"🎯 AI-generated params: {result}")
        
        state["search_params"] = result
        state["metadata"]["ai_used"] = True
        state["metadata"]["original_query"] = state["natural_query"]
        
    except Exception as e:
        Actor.log.error(f"❌ AI processing error: {e}")
        # Fallback to basic search
        state["search_params"] = {"q": state["natural_query"], "downloadable": True}
        state["metadata"]["ai_used"] = False
        state["metadata"]["ai_error"] = str(e)
    
    return state


async def manual_processing_node(state: GraphState) -> GraphState:
    """Manual Processing Node - Uses provided filters directly"""
    Actor.log.info("🎛️ Manual Processing: Using provided filters...")
    
    # Extract search params from actor input (excluding control flags)
    excluded_keys = {"useAI", "naturalQuery", "googleApiKey"}
    search_params = {
        k: v for k, v in state["actor_input"].items() 
        if k not in excluded_keys and v is not None and v != "" and v != []
    }
    
    state["search_params"] = search_params
    state["metadata"]["ai_used"] = False
    
    return state


async def sketchfab_api_node(state: GraphState) -> GraphState:
    """Sketchfab API Node - Executes the actual search"""
    Actor.log.info("🔍 Executing Sketchfab API search...")
    
    try:
        # Build API params
        params = {"type": "models"}
        
        for key, value in state["search_params"].items():
            if value is not None and value != "" and value != []:
                # Handle arrays (tags, categories)
                if isinstance(value, list):
                    params[key] = value
                else:
                    params[key] = value
        
        Actor.log.info(f"📤 API params: {params}")
        
        # Make API request
        url = "https://api.sketchfab.com/v3/search"
        async with AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        
        state["results"] = results
        state["metadata"]["result_count"] = len(results)
        state["metadata"]["api_url"] = str(response.url)
        
        Actor.log.info(f"✅ Found {len(results)} models")
        
    except Exception as e:
        Actor.log.error(f"❌ Sketchfab API error: {e}")
        state["error"] = str(e)
        state["results"] = []
    
    return state


async def output_node(state: GraphState) -> GraphState:
    """Output Node - Pushes results to Apify dataset"""
    Actor.log.info("💾 Saving results to dataset...")
    
    # Push metadata first
    await Actor.push_data({
        "_metadata": True,
        "search_params": state["search_params"],
        "ai_powered": state["metadata"].get("ai_used", False),
        "original_query": state["metadata"].get("original_query"),
        "result_count": state["metadata"].get("result_count", 0),
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
        Actor.log.info("🚀 Starting Sketchfab Model Search Actor (LangGraph Edition)")
        
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Extract control flags
        use_ai = actor_input.get("useAI", False)
        natural_query = actor_input.get("naturalQuery", "")
        
        Actor.log.info(f"📥 Input received - useAI: {use_ai}, query: '{natural_query}'")
        
        # Initialize state
        initial_state: GraphState = {
            "actor_input": actor_input,
            "natural_query": natural_query,
            "use_ai": use_ai,
            "search_params": {},
            "route": "",
            "results": [],
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
        
        Actor.log.info(f"""
╔══════════════════════════════════════════════════════════════╗
║  🎉 SEARCH COMPLETE                                          ║
╠══════════════════════════════════════════════════════════════╣
║  Mode: {'🤖 AI-Powered' if ai_used else '🎛️ Manual'}                                        ║
║  Results: {result_count} models found                                  ║
║  Query: {natural_query[:40] if natural_query else 'N/A'}{'...' if len(natural_query) > 40 else ''}
╚══════════════════════════════════════════════════════════════╝
        """)
        
        if final_state.get("error"):
            Actor.log.error(f"⚠️ Error occurred: {final_state['error']}")
