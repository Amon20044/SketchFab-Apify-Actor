## 🚀 Sketchfab Model Search Actor - AI-Powered with LangGraph

<!-- AI-Powered Apify Actor for Sketchfab 3D Model Discovery -->

A production-grade Apify Actor that searches for 3D models on [Sketchfab](https://sketchfab.com) using either **AI-powered natural language processing** (LangGraph + Google Gemini) or **manual filters**. Built for the Apify Challenge with enterprise-level architecture.

## ✨ Key Features

- **🤖 Dual-Mode Operation**: Switch between AI-powered NLP and manual filtering with a single flag
- **🧠 LangGraph State Machine**: Intelligent routing and conditional execution
- **💬 Natural Language Search**: Describe what you want in plain English
- **🔗 Google Gemini Integration**: Leverages Gemini 2.0 Flash for blazing-fast NLP
- **📊 Structured Output**: Pydantic models ensure type-safe, validated results
- **⚡ Async Everything**: Built for performance with async HTTPX and LangChain

## 🎯 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────┐                                               │
│   │  INPUT  │                                               │
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
│   │  PROCESSING  │           │ (LangChain +  │              │
│   └──────┬───────┘           │   Gemini)     │              │
│          │                   └───────┬───────┘              │
│          │                           │                      │
│          └─────────┬─────────────────┘                      │
│                    ▼                                        │
│           ┌────────────────┐                                │
│           │ SKETCHFAB API  │                                │
│           └───────┬────────┘                                │
│                   ▼                                         │
│           ┌────────────────┐                                │
│           │    OUTPUT      │                                │
│           │   (Dataset)    │                                │
│           └────────────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Usage Modes

### Mode 1: AI-Powered Natural Language Search

Set `useAI: true` and describe what you're looking for:

```json
{
  "useAI": true,
  "naturalQuery": "low poly game-ready cars under 10k faces with PBR textures, downloadable for free",
  "googleApiKey": "your-gemini-api-key"
}
```

The AI will automatically convert this to:
```json
{
  "q": "cars",
  "tags": ["low-poly", "game-ready"],
  "categories": ["cars-vehicles"],
  "max_face_count": 10000,
  "pbr_type": "true",
  "downloadable": true,
  "license": "CC0"
}
```

### Mode 2: Manual Filters

Set `useAI: false` (or omit it) and use traditional filters:

```json
{
  "useAI": false,
  "q": "robot",
  "categories": ["science-technology"],
  "animated": true,
  "downloadable": true,
  "file_format": "gltf"
}
```

## 🌟 Natural Language Examples

| Natural Language Query | AI Interpretation |
|------------------------|-------------------|
| "best high quality characters rigged for blender" | staffpicked=true, rigged=true, file_format=blend |
| "free weapons models, no attribution required" | license=CC0, downloadable=true, categories=weapons-military |
| "animated robots from this month" | animated=true, date=30, categories=science-technology |
| "low poly trees under 5k faces" | max_face_count=5000, tags=low-poly, categories=nature-plants |

## 📥 Input Parameters

### AI Configuration
| Parameter | Type | Description |
|-----------|------|-------------|
| `useAI` | boolean | Enable AI-powered NLP mode (default: false) |
| `naturalQuery` | string | Plain English description of desired models |
| `googleApiKey` | string | Google Gemini API key (or set GOOGLE_API_KEY env var) |

### Manual Filters (20+ parameters)
- **Core**: `q`, `user`, `tags`, `categories`
- **Quality**: `downloadable`, `animated`, `rigged`, `staffpicked`, `sound`
- **Technical**: `pbr_type`, `file_format`, `license`
- **Geometry**: `min_face_count`, `max_face_count`, `max_uv_layer_count`
- **Archives**: `archives_max_size`, `archives_max_face_count`, etc.
- **Sorting**: `sort_by`, `date`, `collection`

## 📤 Output Structure

Each run outputs to the dataset:
1. **Metadata record** with search params, AI status, and result count
2. **Model records** with full Sketchfab data (uid, name, user, thumbnails, etc.)

## 🏗️ Technical Architecture

### Stack
- **Runtime**: Python 3.11+
- **Framework**: Apify SDK 3.x
- **AI/ML**: LangChain + LangGraph + Google Gemini
- **HTTP**: HTTPX (async)
- **Validation**: Pydantic 2.x

### LangGraph Components
- **StateGraph**: Manages workflow state across nodes
- **Conditional Router**: Switches between AI/manual modes
- **AI Processing Node**: LangChain + Gemini for NLP
- **Manual Processing Node**: Direct filter extraction
- **API Node**: Sketchfab API integration
- **Output Node**: Dataset push logic

## 🚀 Deployment

```bash
# Login to Apify
apify login

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
- ✅ Advanced state machine architecture with LangGraph
- ✅ AI/ML integration with production-grade error handling
- ✅ Conditional routing for flexible operation modes
- ✅ Enterprise-level code structure and documentation
- ✅ Real-world API integration with Sketchfab
- ✅ Seamless Vercel AI SDK compatibility

---

**Made with 💜 by leveraging LangGraph, LangChain, and the power of AI for intelligent 3D model discovery.**
