## 🚀 Sketchfab Ultimate Search Actor - AI-Powered with LangGraph

<!-- AI-Powered Apify Actor for Sketchfab 3D Model Discovery -->

A production-grade Apify Actor that searches for 3D models on [Sketchfab](https://sketchfab.com) using the **ULTIMATE COMBINED STRATEGY**: Query + Tags + Categories + Pagination. Features **AI-powered natural language processing** (LangGraph + Google Gemini) that converts even long paragraphs into SEO-optimized search parameters.

## ✨ Key Features

- **🔥 Ultimate Search Strategy**: Combines `q` (SEO query) + `tags` + `categories` for best results
- **🤖 AI-Powered NLP**: Long user text → concise SEO query + precise tags via Google Gemini
- **📄 Full Pagination Support**: Cursor-based pagination with `next`/`previous` navigation
- **🧠 LangGraph State Machine**: Intelligent routing and conditional execution
- **⚡ Smart Defaults**: `downloadable=true` by default, auto-category detection
- **📊 Structured Output**: Pydantic models ensure type-safe, validated results

## 🎯 How It Works

### The Ultimate Search Strategy

```
User Input (even long text)
         │
         ▼
┌─────────────────────────────────────┐
│  🤖 AI Processing (Gemini 2.0)      │
│                                     │
│  "I need a really cool futuristic   │
│   sports car from cyberpunk with    │
│   neon lights, low poly for Unity"  │
│                                     │
│         ▼ BREAKDOWN ▼               │
│                                     │
│  q: "cyberpunk sports car"          │
│  tags: ["cyberpunk", "low-poly",    │
│         "game-ready", "neon"]       │
│  categories: ["cars-vehicles"]      │
│  downloadable: true                 │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  🔍 Sketchfab API                   │
│                                     │
│  GET /v3/search?type=models         │
│    &q=cyberpunk+sports+car          │
│    &tags=cyberpunk,low-poly,...     │
│    &categories=cars-vehicles        │
│    &downloadable=true               │
│    &count=24                        │
│    &cursor=<pagination>             │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  📊 Results + Pagination Info       │
│                                     │
│  • 24 models per page               │
│  • next_cursor for more results     │
│  • previous_cursor to go back       │
└─────────────────────────────────────┘
```

### LangGraph Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────┐                                               │
│   │  INPUT  │ (query + pagination params)                   │
│   └────┬────┘                                               │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────┐                                           │
│   │   ROUTER    │──── useAI=true? ────┐                     │
│   └─────────────┘                     │                     │
│        │                              │                     │
│        │ useAI=false                  │                     │
│        ▼                              ▼                     │
│   ┌──────────────┐           ┌───────────────┐              │
│   │    MANUAL    │           │  AI PROCESS   │              │
│   │  PROCESSING  │           │ Long text →   │              │
│   │              │           │ SEO q + tags  │              │
│   └──────┬───────┘           └───────┬───────┘              │
│          │                           │                      │
│          └─────────┬─────────────────┘                      │
│                    ▼                                        │
│           ┌────────────────┐                                │
│           │ SKETCHFAB API  │ (with pagination)              │
│           └───────┬────────┘                                │
│                   ▼                                         │
│           ┌────────────────┐                                │
│           │    OUTPUT      │                                │
│           │ (Dataset +     │                                │
│           │  Pagination)   │                                │
│           └────────────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Usage

### Mode 1: AI-Powered Natural Language Search

Set `useAI: true` and describe what you're looking for (even long descriptions work!):

```json
{
  "useAI": true,
  "naturalQuery": "I need a really cool futuristic sports car that looks like something from cyberpunk 2077 with neon lights and maybe some damage on it, low poly would be nice for my game project in Unity",
  "googleApiKey": "your-gemini-api-key",
  "count": 24
}
```

The AI automatically converts this to:
```json
{
  "q": "cyberpunk sports car",
  "tags": ["cyberpunk", "low-poly", "game-ready", "neon", "futuristic"],
  "categories": ["cars-vehicles"],
  "downloadable": true
}
```

### Mode 2: Manual Filters

Set `useAI: false` (or omit it) and use traditional filters:

```json
{
  "useAI": false,
  "q": "robot warrior",
  "tags": ["sci-fi", "mech"],
  "categories": ["science-technology"],
  "animated": true,
  "downloadable": true,
  "count": 24
}
```

### Pagination: Getting More Results

Use the `cursor` parameter to navigate through pages:

```json
{
  "useAI": false,
  "q": "cars",
  "cursor": "cD0yNA==",
  "count": 24
}
```

The response includes pagination info:
```json
{
  "_metadata": true,
  "pagination": {
    "has_next": true,
    "has_previous": true,
    "next_cursor": "cD00OA==",
    "previous_cursor": null,
    "next_url": "https://api.sketchfab.com/v3/search?count=24&cursor=cD00OA==&q=cars&type=models",
    "previous_url": "https://api.sketchfab.com/v3/search?count=24&q=cars&type=models"
  }
}
```

## 🌟 Natural Language Examples

| Natural Language Query | AI Generates |
|------------------------|--------------|
| "low poly car for my mobile game, something cartoony" | `q: "cartoon car"`, `tags: ["low-poly", "cartoon", "game-ready"]` |
| "realistic human character with rig for blender, CC0" | `q: "realistic human character"`, `tags: ["realistic", "rigged"]`, `rigged: true`, `license: "CC0"` |
| "best high quality medieval fantasy weapons" | `q: "medieval fantasy weapon"`, `tags: ["medieval", "fantasy", "detailed"]`, `staffpicked: true` |
| "sci fi robot mech warrior" | `q: "sci-fi mech robot"`, `tags: ["sci-fi", "mech", "robot"]` |
| "tree" | `q: "tree"`, `tags: ["tree", "nature"]`, `categories: ["nature-plants"]` |

## 📥 Input Parameters

### AI Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `useAI` | boolean | `false` | Enable AI-powered NLP mode |
| `naturalQuery` | string | - | Plain English description (supports long text!) |
| `googleApiKey` | string | - | Google Gemini API key (or set `GOOGLE_API_KEY` env var) |

### Pagination
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `count` | integer | `24` | Number of results per page (max 24) |
| `cursor` | string | - | Cursor for pagination (from previous response) |

### Search Filters
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (SEO-optimized, 2-5 words recommended) |
| `tags` | array | Tag slugs (e.g., `["low-poly", "game-ready"]`) |
| `categories` | array | Category slugs (e.g., `["cars-vehicles"]`) |

### Quality Filters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `downloadable` | boolean | `true` | Only downloadable models |
| `animated` | boolean | - | Only animated models |
| `rigged` | boolean | - | Only rigged models |
| `staffpicked` | boolean | - | Staff-picked only |
| `sound` | boolean | - | Models with sound |

### Technical Filters
| Parameter | Type | Description |
|-----------|------|-------------|
| `pbr_type` | string | PBR workflow (`metalness`, `specular`, `true`) |
| `file_format` | string | File format (`gltf`, `fbx`, `blend`, `obj`) |
| `license` | string | License (`CC0`, `CC-BY`, `CC-BY-NC`, etc.) |
| `min_face_count` | integer | Minimum polygon faces |
| `max_face_count` | integer | Maximum polygon faces |
| `sort_by` | string | Sort by (`likes`, `views`, `recent`) |
| `date` | integer | Models from last X days |

### Available Categories
```
animals-pets, architecture, art-abstract, cars-vehicles,
characters-creatures, cultural-heritage-history, electronics-gadgets,
fashion-style, food-drink, furniture-home, music, nature-plants,
news-politics, people, places-travel, science-technology,
sports-fitness, weapons-military
```

## 📤 Output Structure

Each run outputs to the dataset:

### 1. Metadata Record
```json
{
  "_metadata": true,
  "search_params": {
    "q": "cyberpunk sports car",
    "tags": ["cyberpunk", "low-poly"],
    "categories": ["cars-vehicles"],
    "downloadable": true
  },
  "ai_powered": true,
  "original_query": "I need a futuristic sports car...",
  "generated_q": "cyberpunk sports car",
  "generated_tags": ["cyberpunk", "low-poly", "game-ready"],
  "result_count": 24,
  "pagination": {
    "has_next": true,
    "has_previous": false,
    "next_cursor": "cD0yNA==",
    "next_url": "https://api.sketchfab.com/v3/search?..."
  }
}
```

### 2. Model Records
```json
{
  "uid": "abc123...",
  "name": "Cyberpunk Car",
  "user": { "username": "artist123", "displayName": "Artist" },
  "thumbnails": { "images": [...] },
  "viewerUrl": "https://sketchfab.com/3d-models/...",
  "isDownloadable": true,
  "faceCount": 5000,
  "license": { "slug": "cc-by-4.0" }
}
```

## 🏗️ Technical Architecture

### Stack
- **Runtime**: Python 3.11+
- **Framework**: Apify SDK 3.x
- **AI/ML**: LangChain + LangGraph + Google Gemini 2.0 Flash
- **HTTP**: HTTPX (async)
- **Validation**: Pydantic 2.x

### Key Components
| Component | Purpose |
|-----------|---------|
| `SketchfabSearchParams` | Pydantic model for structured output |
| `GraphState` | LangGraph state with pagination support |
| `SEARCH_SYSTEM_PROMPT` | AI prompt for SEO-optimized search generation |
| `ai_processing_node` | Converts long text → q + tags + categories |
| `sketchfab_api_node` | API call with cursor pagination |
| `extract_pagination_info` | Parses next/previous cursors |

## 🚀 Deployment

```bash
# Login to Apify
apify login

# Run locally
apify run

# Deploy to cloud
apify push
```

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key (alternative to input param) |

## 📚 Resources

- [Sketchfab API Docs](https://docs.sketchfab.com/data-api/v3/index.html)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Apify SDK Python](https://docs.apify.com/sdk/python)
- [Google AI Studio](https://aistudio.google.com/apikey) - Get your Gemini API key

## 🏆 Built for Apify Challenge

This Actor demonstrates:
- ✅ **Ultimate Search Strategy**: q + tags + categories combined
- ✅ **AI-Powered SEO**: Long text → optimized search params
- ✅ **Full Pagination**: Cursor-based next/previous navigation
- ✅ **LangGraph Architecture**: Intelligent state machine routing
- ✅ **Smart Defaults**: downloadable=true, auto-category detection
- ✅ **Production-Ready**: Error handling, fallbacks, logging

---

**Made with 💜 for intelligent 3D model discovery. Search smarter, not harder!**
