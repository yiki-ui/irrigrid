#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: AI Agronomist
Provides agronomic advice and design review using Groq LLM with offline fallback.
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Dict
import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Agronomist"])


class AdviceRequest(BaseModel):
    prompt: str
    crop_name: str = "Crop"
    location_name: str = "Rwanda"
    field_area_ha: float = 0.25
    soil_type: str = "Loam"


def _get_groq_key() -> str:
    # Ensure root .env is reloaded if modified
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key and not key.startswith("your_"):
        return key
    return ""


def _get_openrouter_key() -> str:
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def _call_groq(system_prompt: str, user_prompt: str) -> Dict:
    """Live Groq API call with multiple model fallbacks."""
    api_key = _get_groq_key()
    if not api_key or api_key.startswith("your_"):
        return {}

    models_to_try = [
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b",
    ]

    for model in models_to_try:
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.4,
                        "max_tokens": 500,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {"advice": content, "source": f"groq_{model}"}
                else:
                    logger.warning("Groq API returned %s: %s", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Groq API request error (%s): %s", model, e)
            continue

    return {}


def _call_openrouter(system_prompt: str, user_prompt: str) -> Dict:
    """Fallback to OpenRouter if configured."""
    api_key = _get_openrouter_key()
    if not api_key or api_key.startswith("your_"):
        return {}

    models_to_try = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
    ]

    for model in models_to_try:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "IrriGrid DSS",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.4,
                        "max_tokens": 500,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {"advice": content, "source": f"openrouter_{model}"}
        except Exception as e:
            logger.warning("OpenRouter error (%s): %s", model, e)
            continue

    return {}


def _generate_offline_advice(prompt: str, crop: str, loc: str, area: float, soil: str) -> str:
    """Domain-specific agronomic advice engine for Rwanda. Handles a wide range of topics."""
    p = prompt.lower().strip()

    # ── Model / Identity inquiries ───────────────────────────────────────────
    if any(k in p for k in ["llama", "model", "generic", "who are you", "what are you", "are you ai", "are you real", "bot", "offline", "chatgpt", "gemini", "groq"]):
        return (
            f"You are speaking with the **IrriGrid Agri-Expert** (Rwanda Offline Engine).\n\n"
            f"• **Why this response?**: A live `GROQ_API_KEY` is not set in `.env`, so I am using the built-in agronomic knowledge base.\n"
            f"• **Want real Llama 3.3?**: \n"
            f"  1. Grab a free API key at **[console.groq.com/keys](https://console.groq.com/keys)** (free, no credit card required).\n"
            f"  2. Add `GROQ_API_KEY=gsk_...` to your `.env` file.\n"
            f"  3. Send your next message and I will answer with live **Llama 3.3 70B** reasoning!\n\n"
            f"Even in offline mode, you can ask about watering schedules, drip pipe sizing, fertigation, pest management, or expected yields for **{crop}** in **{loc}**."
        )

    # ── Greetings / very short messages ──────────────────────────────────────
    if p in {"hi", "hello", "hey", "hii", "helo", "yo", "sup", "salut", "bonjour", "muraho", "mwiriwe"} or (len(p) <= 4 and p.isalpha()):
        return (
            f"Hello! 👋 I'm your IrriGrid Agri-Expert for {loc}, Rwanda. "
            f"Your current project: **{crop}** on {area:.2f} ha of **{soil}**.\n\n"
            f"I can help you with:\n"
            f"• 💧 Irrigation scheduling & water requirements\n"
            f"• 🔧 Drip system design (emitter spacing, pipe sizing, pressure)\n"
            f"• 🌱 Crop management & fertigation\n"
            f"• 🪱 Pest & disease identification\n"
            f"• 💰 Cost estimation in RWF\n"
            f"• 🌾 Yield targets & harvest timing\n\n"
            f"What would you like to know?"
        )

    # ── Drip system / engineering ─────────────────────────────────────────────
    if any(k in p for k in ["drip", "pipe", "emitter", "spacing", "lateral", "layout", "pressure", "uniformity", "eu", "mainline", "filter", "submain"]):
        return (
            f"Drip system design for {crop} in {loc} ({area:.2f} ha on {soil}):\n\n"
            f"• **Laterals**: 16 mm PE tubing at 1.0 m row spacing.\n"
            f"• **Emitters**: 0.3 m inline dripper spacing at 1.5–2.0 L/h — gives ~92% Emission Uniformity (EU).\n"
            f"• **Mainline**: 63 mm PVC or HDPE; sub-main 40 mm.\n"
            f"• **Operating pressure**: 1.0–1.2 bar at the submain manifold. Use a pressure gauge and relief valve.\n"
            f"• **Filtration**: 120-mesh disc filter at the head unit — flush weekly in clay soils.\n"
            f"• **Flushing**: Open lateral end-caps for 3–5 minutes every 2 weeks to flush sediment."
        )

    # ── Water / irrigation scheduling ────────────────────────────────────────
    if any(k in p for k in ["water", "irrigat", "schedule", "frequency", "how often", "how much", "mm", "liter", "litre", "requirement", "eto", "etc", "kc"]):
        return (
            f"Irrigation schedule for {crop} in {loc} ({soil}):\n\n"
            f"• **Early stage (0–30 days)**: 2.5–3.0 mm/day — irrigate every 2 days.\n"
            f"• **Vegetative / flowering (30–70 days)**: 4.0–5.0 mm/day — daily irrigation.\n"
            f"• **Fruit filling (70–100 days)**: 4.5–5.5 mm/day — critical stage, do not skip.\n"
            f"• **Ripening / late (100–harvest)**: Reduce to 2.0 mm/day; stop 7–10 days before harvest.\n"
            f"• **Best time**: Irrigate between 06:00–08:30 AM to cut evaporation losses by up to 25%.\n"
            f"• In {soil}: Apply in 45–60 min cycles to match infiltration rate and avoid runoff."
        )

    # ── Soil ──────────────────────────────────────────────────────────────────
    if any(k in p for k in ["soil", "moisture", "retention", "clay", "loam", "volcanic", "sandy", "field capacity", "wilting", "taw", "raw", "compaction"]):
        return (
            f"Soil management for {soil} in {loc}:\n\n"
            f"• **Total Available Water (TAW)**: ~140–180 mm per metre depth.\n"
            f"• **Readily Available Water (RAW)**: 40% of TAW — irrigate before depletion crosses this.\n"
            f"• **Management depletion threshold**: Soil moisture sensor should read >60% field capacity.\n"
            f"• **Mulching**: Apply 5–8 cm of dry grass, coffee husks, or rice straw to conserve moisture.\n"
            f"• **Compaction**: Avoid heavy machinery on wet volcanic loam; subsoil rip to 45 cm before planting."
        )

    # ── Fertilizer / fertigation ──────────────────────────────────────────────
    if any(k in p for k in ["fertiliz", "fertigation", "nutrient", "npk", "urea", "nitrogen", "phosph", "potassium", "dap", "can"]):
        return (
            f"Fertigation plan for {crop} in Rwanda:\n\n"
            f"• **Equipment**: Venturi injector (7–20 L/min) or dosing pump — install after the filter.\n"
            f"• **Stage 1 (0–30 days)**: NPK 20-20-20 at 5 kg/ha/week — promotes root development.\n"
            f"• **Stage 2 (30–70 days)**: CAN or Urea + MAP at 8 kg/ha/week — supports rapid vegetative growth.\n"
            f"• **Stage 3 (70–harvest)**: K-rich (NPK 8-8-32 or KNO₃) — improves fruit quality and Brix.\n"
            f"• **pH**: Keep irrigation water pH at 5.5–6.5 for optimal nutrient uptake.\n"
            f"• **Flushing**: Always flush drip lines with plain water for 10 minutes after fertigation."
        )

    # ── Pest / disease ────────────────────────────────────────────────────────
    if any(k in p for k in ["pest", "disease", "insect", "fungus", "fungi", "blight", "aphid", "mite", "wilt", "rot", "virus", "bacterial", "spray", "treatment"]):
        return (
            f"Pest & disease management for {crop} in {loc}:\n\n"
            f"• **Early blight (Alternaria)**: Apply Mancozeb 80 WP at 2.5 g/L every 7–10 days during wet seasons.\n"
            f"• **Late blight (Phytophthora)**: Spray Metalaxyl-M + Mancozeb at first sign; remove infected leaves immediately.\n"
            f"• **Aphids / whitefly**: Use neem oil (5 ml/L) or imidacloprid at label rate. Monitor weekly.\n"
            f"• **Spider mites**: Avoid water stress — dry plants attract mites. Use abamectin if severe.\n"
            f"• **Bacterial wilt (Ralstonia)**: No chemical cure — rotate crops, use resistant varieties, remove infected plants.\n"
            f"• **IPM**: Intercrop with marigold or basil to deter pests naturally."
        )

    # ── Yield / harvest ───────────────────────────────────────────────────────
    if any(k in p for k in ["yield", "harvest", "tons", "kg", "production", "output", "rwf", "earn", "income", "profit", "market", "season"]):
        area_str = f"{area:.2f}"
        yield_low = int(area * 15_000)
        yield_high = int(area * 25_000)
        revenue_low = yield_low * 400
        revenue_high = yield_high * 400
        return (
            f"Yield & economic outlook for {crop} in {loc} ({area_str} ha):\n\n"
            f"• **Expected yield**: {yield_low:,}–{yield_high:,} kg ({int(yield_low/1000*10)/10}–{int(yield_high/1000*10)/10} tonnes) per season with drip irrigation.\n"
            f"• **Market price** (Kigali/Musanze average): ~400 RWF/kg fresh tomato.\n"
            f"• **Gross revenue**: {revenue_low:,}–{revenue_high:,} RWF per season.\n"
            f"• **Key seasons**: Long rains (Feb–Jun) and short rains (Sep–Dec) — plan planting 2–4 weeks before rain onset.\n"
            f"• **Post-harvest**: Grade produce (A/B/C) on-farm; transport within 24h to avoid loss."
        )

    # ── Cost ─────────────────────────────────────────────────────────────────
    if any(k in p for k in ["cost", "budget", "price", "expense", "rwf", "how much", "investment", "capital"]):
        cost_est = int(area * 1_200_000 + 150_000)
        return (
            f"Cost estimation for {area:.2f} ha drip system in {loc}:\n\n"
            f"• **Equipment (pipes, drippers, fittings)**: ~{int(area * 800_000):,} RWF\n"
            f"• **Head unit (filter, pressure gauge, valve)**: ~150,000 RWF\n"
            f"• **Installation labour**: ~{int(area * 200_000):,} RWF\n"
            f"• **Total estimated cost**: **{cost_est:,} RWF** ({int(cost_est/1300):,} USD approx.)\n\n"
            f"Tip: MINAGRI and RAB often offer 30–50% subsidy on drip kits for smallholders — check with your local agriculture office."
        )

    # ── Generic / catch-all ───────────────────────────────────────────────────
    return (
        f"📋 IrriGrid Agronomist — {crop} in {loc} ({soil}, {area:.2f} ha):\n\n"
        f"I didn't fully understand your question. Try asking about:\n"
        f"• **Watering**: \"How much water does {crop} need per day?\"\n"
        f"• **System**: \"What drip pipe size for my field?\"\n"
        f"• **Soil**: \"How do I manage moisture in {soil}?\"\n"
        f"• **Fertilizer**: \"What NPK should I use for {crop}?\"\n"
        f"• **Pests**: \"How do I treat blight on {crop}?\"\n"
        f"• **Cost**: \"How much will the drip system cost?\"\n"
        f"• **Yield**: \"What yield can I expect from {area:.2f} ha?\""
    )


@router.get("/status")
def get_ai_status():
    """Returns whether live LLM (Groq or OpenRouter) is configured."""
    groq_key = _get_groq_key()
    has_groq = bool(groq_key and not groq_key.startswith("your_"))
    openrouter_key = _get_openrouter_key()
    has_openrouter = bool(openrouter_key and not openrouter_key.startswith("your_"))
    
    if has_groq:
        provider = "Groq AI"
        model = "qwen/qwen3.8-27b"
    elif has_openrouter:
        provider = "OpenRouter"
        model = "meta-llama/llama-3.3-70b-instruct:free"
    else:
        provider = "Offline Rule Engine"
        model = "Rwanda Agronomic Knowledge Base"

    return {
        "is_live_llm": has_groq or has_openrouter,
        "provider": provider,
        "model": model,
    }


@router.post("/advice")
async def get_agronomic_advice(req: AdviceRequest) -> Dict:
    """Consult the AI Agronomist on irrigation schedule, crop health, or system setup."""
    system_prompt = (
        f"You are IrriGrid's Expert Agronomist and Irrigation Engineer for Rwanda. "
        f"Farmer Context: Location: {req.location_name}, Rwanda; Crop: {req.crop_name}; "
        f"Field size: {req.field_area_ha} ha; Soil: {req.soil_type}. "
        f"Provide direct, concise, practical, and highly actionable advice tailored specifically "
        f"to Rwandan agriculture and drip irrigation engineering."
    )

    # 1. Try live Groq LLM if key is configured
    groq_key = _get_groq_key()
    if groq_key and not groq_key.startswith("your_"):
        result = await run_in_threadpool(_call_groq, system_prompt, req.prompt)
        if result and "advice" in result:
            return result

    # 2. Try OpenRouter if configured
    openrouter_key = _get_openrouter_key()
    if openrouter_key and not openrouter_key.startswith("your_"):
        result = await run_in_threadpool(_call_openrouter, system_prompt, req.prompt)
        if result and "advice" in result:
            return result

    # 3. Domain-specific rule-based fallback
    advice = _generate_offline_advice(
        req.prompt, req.crop_name, req.location_name, req.field_area_ha, req.soil_type
    )
    return {"advice": advice, "source": "offline_agronomist_engine"}
