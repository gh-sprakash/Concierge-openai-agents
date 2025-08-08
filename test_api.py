"""Concierge Sales Assistant API – Quick Reference

Base URL
http://ec2-44-244-230-255.us-west-2.compute.amazonaws.com:8080

GET /health
- Checks orchestrator and session health.
- Response 200 JSON:
```json
{
  "status": "ok",
  "orchestrator": {
    "orchestrator": "healthy",
    "guardrails_enabled": true,
    "tracing_enabled": false,
    "tools_count": 5,
    "model_config": {
      "name": "openai-gpt-4o",
      "display_name": "🤖 OpenAI GPT-4o",
      "description": "Latest GPT-4 Omni model - Best overall performance",
      "provider": "openai",
      "model_id": "gpt-4o",
      "temperature": 0.2,
      "max_tokens": 1500
    }
  },
  "sessions": {
    "active": 0,
    "storage": "persistent"
  }
}
```












POST /query
- Processes a user question and returns an answer plus metadata and source docs when available.
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "user_id": "string (required)",
  "query": "string (required)",
  "user_context": {
    "name": "optional string",
    "territory": "optional string",
    "role": "optional string"
  }
}
```
- Response 200 JSON (success):
```json
{
  "success": true,
  "response": "string - assistant reply",
  "model": "🤖 OpenAI GPT-4o",
  "tools_used": ["query_knowledge_tool", "query_salesforce_tool"],
  "execution_time": 4.21,
  "session_type": "persistent",
  "knowledge_sources": [
    {
      "uri": "s3://bucket/path/doc.pdf",
      "title": "Optional title",
      "snippet": "Optional matched text",
      "metadata": { "k": "v" }
    }
  ]
}
```
- Response 400 JSON (guardrail or handled error):
```json
{
  "success": false,
  "error": "message",
  "response": "message",
  "execution_time": 0.88,
  "model": "🤖 OpenAI GPT-4o"
}
```
- Response 500 JSON (unexpected error):
```json
{ "success": false, "error": "message" }
```



Examples

- Health:
```bash
curl -s http://ec2-44-244-230-255.us-west-2.compute.amazonaws.com:8080/health
```

- Query:
```bash
curl -s -X POST http://ec2-44-244-230-255.us-west-2.compute.amazonaws.com:8080/query \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"demo","query":"What are Guardant360 features?"}'
```

- Python:
```python
import requests
r = requests.post("http://ec2-44-244-230-255.us-west-2.compute.amazonaws.com:8080/query", json={
  "user_id": "demo",
  "query": "What are Guardant360 features?"
}, timeout=60)
print(r.json())
```

Notes
- Knowledge sources appear when the Knowledge Base returns citations; if unavailable (mock mode or no citations), `knowledge_sources` may be empty.
- Guardrails block disallowed content; blocked requests return `success=false` with an explanatory message.
- Sessions are keyed by `user_id` and persist across calls.

"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests

host = os.getenv("API_HOST", "http://ec2-44-244-230-255.us-west-2.compute.amazonaws.com:8080")

def get_health():
    url = f"{host}/health"
    response = requests.get(url)
    return response.json()

def query_api(user_id, query, user_context=None):
    url = f"{host}/query"
    headers = {"Content-Type": "application/json"}
    body = {
        "user": user_id,
        "prompt": query,
        "user_context": user_context or {}
    }
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def main():
    # health = get_health()
    # print(json.dumps(health, indent=2))
    # query_response = query_api("demo", "What are Guardant360 features?")
    # print(json.dumps(query_response, indent=2))

    user_id = "demo"
    query = "What are Guardant360 features?"
    user_context = {
        "name": "John Doe",
        "territory": "West Coast",
        "role": "Sales Representative"
    }
    try:
        response = query_api(user_id, query, user_context)
        print(json.dumps(response, indent=2))
    except requests.RequestException as e:
        print(f"Error querying API: {e}")


if __name__ == "__main__":
    main()


