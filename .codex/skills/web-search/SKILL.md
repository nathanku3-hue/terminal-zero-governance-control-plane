---
name: web-search
description: Search the web for current information, API documentation, or external references. Use when local context is insufficient.
---

# Web-Search Skill

Perform web searches and fetch external content when local knowledge is insufficient.

## 0. Activation Triggers
- User asks about current events or recent information
- User requests API documentation not in local files
- User says "search for", "look up", "find online"
- Expert-researcher escalates for external references

## 1. Search Strategy
1. Formulate precise search query based on user request
2. Identify search scope:
   - General web search (news, articles, discussions)
   - Technical documentation (API docs, library references)
   - Academic sources (papers, research)
3. Execute search with appropriate filters
4. Rank results by relevance and recency

## 2. Content Extraction
1. Fetch top N results (default: 3-5)
2. Extract key information:
   - Title and URL
   - Publication date
   - Relevant snippets
   - Author/source credibility
3. Synthesize findings into coherent summary

## 3. Citation Requirements
1. Always cite sources with URLs
2. Include publication dates when available
3. Note source credibility (official docs vs forum posts)
4. Flag conflicting information across sources

## 4. Output Contract
1. Emit search summary:
   ```
   WebSearch Results for: "<query>"

   Source 1: [Title](URL) - [Date]
   - Key finding: ...
   - Relevance: high/medium/low

   Source 2: [Title](URL) - [Date]
   - Key finding: ...
   - Relevance: high/medium/low

   Synthesis: ...

   Confidence: <0-100>
   ```
2. If confidence < 80, recommend expert-researcher escalation
3. Include "Sources:" section with all URLs

## 5. Limitations
- Cannot access authenticated services (GitHub private repos, Google Docs)
- Cannot verify information accuracy beyond source credibility
- Results may be outdated if search index is stale

## 6. Model Routing
Use `claude` model for reasoning and synthesis.
