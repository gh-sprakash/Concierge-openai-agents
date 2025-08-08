import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables (API keys, AWS creds, etc.)
from dotenv import load_dotenv
load_dotenv()

# Ensure project root on sys.path (the script directory is already added by Python)
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.orchestrator import SalesOrchestrator
from src.sessions.manager import session_manager
from utils_kb_references import get_references_dict_from_knowledge_sources


def create_app() -> Flask:
    app = Flask(__name__)
    # Enable CORS for all routes and origins (public API)
    CORS(app)

    # Fixed configuration per requirements
    MODEL_NAME = "openai-gpt-4o"  # use GPT-4o
    SESSION_TYPE = "persistent"   # persistent memory

    orchestrator = SalesOrchestrator(
        model_name=MODEL_NAME,
        enable_guardrails=True,
        enable_tracing=False,
    )

    @app.get("/health")
    def health() -> Any:
        info = orchestrator.health_check()
        return jsonify({
            "status": "ok",
            "orchestrator": info,
            "sessions": {
                "active": len(session_manager.list_active_sessions()),
                "storage": SESSION_TYPE,
            },
        })

    @app.post("/query")
    def query():
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        user_query: str = (data.get("prompt") or data.get("q") or "").strip()
        if not user_query:
            return jsonify({"success": False, "error": "Missing 'query'"}), 400

        user_id: str = data.get("user") or request.headers.get("X-User-Id") or "anon"
        # Always persistent per requirement
        session = session_manager.get_session(user_id=user_id, session_type=SESSION_TYPE)

        # Minimal user context; could be expanded if provided
        user_context = data.get("user_context") or {
            "name": data.get("name", "Sales Representative"),
            "territory": data.get("territory", "Northeast"),
            "role": data.get("role", "Sales Rep"),
        }

        try:
            result = asyncio.run(orchestrator.process_query(
                user_query,
                user_context=user_context,
                session=session,
            ))
            knowledge_sources = result.get("knowledge_sources", [])
            # print(f"Knowledge sources: {knowledge_sources}")
            try:
                references_dict = get_references_dict_from_knowledge_sources(
                    knowledge_sources
                )
            except Exception as e:
                print(f"Error getting references: {e}")
                references_dict = []

            status_code = 200 if result.get("success") else 400
            # Shape the API to return response and knowledge sources if present
            ## generate unique query ID
            query_id = str(uuid.uuid4())
            payload = {
                "queryId": query_id,
                "success": result.get("success", False),
                "response": result.get("response"),
                "model": result.get("model"),
                "tools_used": result.get("tools_used", []),
                "execution_time": result.get("execution_time"),
                "session_type": SESSION_TYPE,
                "references_dict": references_dict
            }
            if not result.get("success"):
                payload["error"] = result.get("error") or result.get("response")

            return jsonify(payload), status_code

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
            }), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Bind to 0.0.0.0 for container/EC2 usage; PORT env var respected
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)


