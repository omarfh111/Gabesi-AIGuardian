"""
main.py - FastAPI Backend
Orchestrates parallel execution of agent_env and agent_finance.
Exposes REST endpoints for the React frontend.
"""

import os
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables from project root .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Set LangSmith env vars (LangChain uses LANGCHAIN_ prefix internally)
os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGSMITH_TRACING", "true"))
os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGSMITH_API_KEY", ""))
os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "gabes"))
os.environ.setdefault("LANGCHAIN_ENDPOINT", os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from .data import USER_DATA
from .services.agent_env import run_env_agent
from .services.agent_finance import run_finance_agent
from .services.agent_energie import run_energie_agent
from .services.agent_expert import run_expert_agent
from .services.orchestrator import build_dashboard


router = APIRouter()


# ── Request / Response Models ────────────────
class UserDataInput(BaseModel):
    """Optional override for user data. If not provided, uses default data."""
    identite: Optional[dict] = None
    logement: Optional[dict] = None
    consommation: Optional[dict] = None


class AgentResult(BaseModel):
    agent: str
    status: str
    analysis: str
    raw_messages_count: int
    execution_time_seconds: float


class ParallelAnalysisResponse(BaseModel):
    total_time_seconds: float
    env_result: AgentResult
    finance_result: AgentResult
    energie_result: AgentResult
    expert_result: AgentResult
    dashboard: dict          # structured data for charts + XAI
    user_profile: dict


# ── Endpoints ────────────────────────────────

@router.get("/")
async def root():
    return {
        "service": "Renewable Energy Advisor API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "This info",
            "GET /health": "Health check",
            "GET /user-data": "Get current user profile data",
            "POST /analyse": "Run all 4 agents + orchestrator dashboard",
            "POST /analyse/env": "Run environment agent only",
            "POST /analyse/finance": "Run finance agent only",
            "POST /analyse/energie": "Run renewable energy recommendation agent only",
            "POST /analyse/expert": "Run expert synthesis agent only",
        },
    }


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "langsmith_tracing": os.getenv("LANGCHAIN_TRACING_V2", "false"),
        "langsmith_project": os.getenv("LANGCHAIN_PROJECT", "N/A"),
    }


@router.get("/user-data")
async def get_user_data():
    """Return the current user profile data."""
    return USER_DATA


def _merge_user_data(override: Optional[UserDataInput]) -> dict:
    """Merge optional overrides with default user data."""
    data = USER_DATA.copy()
    if override:
        if override.identite:
            data["identite"] = {**data["identite"], **override.identite}
        if override.logement:
            data["logement"] = {**data["logement"], **override.logement}
        if override.consommation:
            data["consommation"] = {**data["consommation"], **override.consommation}
    return data


@router.post("/analyse", response_model=ParallelAnalysisResponse)
async def run_parallel_analysis(user_input: Optional[UserDataInput] = None):
    """
    🚀 Pipeline complète : 4 agents avec orchestration intelligente
    - PHASE 1 (parallèle) : agent_env→agent_energie  +  agent_finance
    - PHASE 2 (séquentiel) : agent_expert (synthèse finale) reçoit energie + finance
    """
    data = _merge_user_data(user_input)
    start = time.time()

    try:
        # ── PHASE 1 : env→énergie (séquentiel) vs finance (parallèle) ──
        async def run_env_then_energie():
            env_res = await run_env_agent(data)
            env_res["execution_time_seconds"] = round(time.time() - start, 2)
            energie_start = time.time()
            energie_res = await run_energie_agent(data, env_res)
            energie_res["execution_time_seconds"] = round(time.time() - energie_start, 2)
            return env_res, energie_res

        async def run_finance():
            finance_start = time.time()
            res = await run_finance_agent(data)
            res["execution_time_seconds"] = round(time.time() - finance_start, 2)
            return res

        (env_result, energie_result), finance_result = await asyncio.gather(
            run_env_then_energie(),
            run_finance(),
        )

        # ── PHASE 2 : agent_expert synthèse finale ──
        expert_start = time.time()
        expert_result = await run_expert_agent(data, energie_result, finance_result)
        expert_result["execution_time_seconds"] = round(time.time() - expert_start, 2)

        # ── PHASE 3 : orchestrateur dashboard (déterministe, pas d'appel LLM) ──
        dashboard = build_dashboard(
            user_data=data,
            env_result=env_result,
            finance_result=finance_result,
            energie_result=energie_result,
            expert_result=expert_result,
        )

        total_time = round(time.time() - start, 2)

        return ParallelAnalysisResponse(
            total_time_seconds=total_time,
            env_result=AgentResult(**{k: v for k, v in env_result.items() if k != "execution_time_seconds"},
                                   execution_time_seconds=env_result["execution_time_seconds"]),
            finance_result=AgentResult(**{k: v for k, v in finance_result.items() if k != "execution_time_seconds"},
                                        execution_time_seconds=finance_result["execution_time_seconds"]),
            energie_result=AgentResult(**{k: v for k, v in energie_result.items() if k != "execution_time_seconds"},
                                        execution_time_seconds=energie_result["execution_time_seconds"]),
            expert_result=AgentResult(**{k: v for k, v in expert_result.items() if k != "execution_time_seconds"},
                                       execution_time_seconds=expert_result["execution_time_seconds"]),
            dashboard=dashboard,
            user_profile=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/analyse/env", response_model=AgentResult)
async def run_env_only(user_input: Optional[UserDataInput] = None):
    """Run the environment agent only."""
    data = _merge_user_data(user_input)
    start = time.time()
    try:
        result = await run_env_agent(data)
        return AgentResult(**result, execution_time_seconds=round(time.time() - start, 2))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Env agent failed: {str(e)}")


@router.post("/analyse/finance", response_model=AgentResult)
async def run_finance_only(user_input: Optional[UserDataInput] = None):
    """Run the finance agent only."""
    data = _merge_user_data(user_input)
    start = time.time()
    try:
        result = await run_finance_agent(data)
        return AgentResult(**result, execution_time_seconds=round(time.time() - start, 2))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finance agent failed: {str(e)}")


@router.post("/analyse/energie", response_model=AgentResult)
async def run_energie_only(user_input: Optional[UserDataInput] = None):
    """Run the renewable energy recommendation agent (requires env analysis first)."""
    data = _merge_user_data(user_input)
    start = time.time()
    try:
        env_result = await run_env_agent(data)
        result = await run_energie_agent(data, env_result)
        return AgentResult(**result, execution_time_seconds=round(time.time() - start, 2))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Energie agent failed: {str(e)}")


@router.post("/analyse/expert", response_model=AgentResult)
async def run_expert_only(user_input: Optional[UserDataInput] = None):
    """Run expert synthesis agent (runs all upstream agents first)."""
    data = _merge_user_data(user_input)
    start = time.time()
    try:
        env_res = await run_env_agent(data)
        energie_res, finance_res = await asyncio.gather(
            run_energie_agent(data, env_res),
            run_finance_agent(data),
        )
        result = await run_expert_agent(data, energie_res, finance_res)
        return AgentResult(**result, execution_time_seconds=round(time.time() - start, 2))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expert agent failed: {str(e)}")



