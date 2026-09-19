"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio
import httpx

from . import storage
from .storage import delete_conversation
from .council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
    calculate_consensus_metrics,
    stage1_collect_responses_stream,
    stage2_collect_rankings_stream,
    stage3_synthesize_final_stream,
    COUNCIL_PERSONAS,
    get_persona
)
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    council_models: Optional[List[str]] = None
    chairman_model: Optional[str] = None
    persona: Optional[str] = "strict_truth"


class CouncilSettings(BaseModel):
    """Council settings model."""
    council_models: List[str]
    chairman_model: str
    persona: Optional[str] = "strict_truth"



class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


# Curated catalog of tested models
CURATED_MODELS = [
    {
        "id": "deepseek/deepseek-v4-flash-0731:free",
        "name": "DeepSeek V4 Flash",
        "provider": "DeepSeek",
        "is_free": True,
        "description": "Ultra fast, high reasoning capability, excellent peer reviewer",
        "category": "Recommended Free"
    },
    {
        "id": "nvidia/nemotron-3.5-lightning:free",
        "name": "Nvidia Nemotron 3.5 Lightning",
        "provider": "Nvidia",
        "is_free": True,
        "description": "Powerful instruction following and analytical precision",
        "category": "Recommended Free"
    },
    {
        "id": "liquid/lfm-2.5-2.6b:free",
        "name": "Liquid LFM 2.5",
        "provider": "Liquid AI",
        "is_free": True,
        "description": "Compact, efficient model with fast turnaround",
        "category": "Recommended Free"
    },
    {
        "id": "nex-agi/nex-n2.5-pro:free",
        "name": "Nex-AGI N2.5 Pro",
        "provider": "Nex AGI",
        "is_free": True,
        "description": "High-accuracy open model for complex queries",
        "category": "Recommended Free"
    },
    {
        "id": "google/gemma-4-26b-a4b-it:free",
        "name": "Google Gemma 4 26B",
        "provider": "Google",
        "is_free": True,
        "description": "Google's open-weights model fine-tuned for instruction",
        "category": "Free"
    },
    {
        "id": "qwen/qwen3.8-27b:free",
        "name": "Qwen 3.8 27B",
        "provider": "Alibaba Qwen",
        "is_free": True,
        "description": "Strong multi-domain knowledge and coding logic",
        "category": "Free"
    },
    {
        "id": "z-ai/glm-5.2:free",
        "name": "GLM 5.2",
        "provider": "Zhipu AI",
        "is_free": True,
        "description": "Bilingual flagship reasoning model",
        "category": "Free"
    },
    {
        "id": "openai/gpt-4o",
        "name": "OpenAI GPT-4o",
        "provider": "OpenAI",
        "is_free": False,
        "description": "Industry flagship multimodal model",
        "category": "Frontier Flagship"
    },
    {
        "id": "openai/gpt-4o-mini",
        "name": "OpenAI GPT-4o Mini",
        "provider": "OpenAI",
        "is_free": False,
        "description": "Cost-effective, fast, high intelligence",
        "category": "Fast Paid"
    },
    {
        "id": "anthropic/claude-3.7-sonnet",
        "name": "Anthropic Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "is_free": False,
        "description": "State-of-the-art hybrid reasoning and coding model",
        "category": "Frontier Flagship"
    },
    {
        "id": "google/gemini-2.5-pro",
        "name": "Google Gemini 2.5 Pro",
        "provider": "Google",
        "is_free": False,
        "description": "Deep reasoning with massive context window",
        "category": "Frontier Flagship"
    },
    {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "DeepSeek",
        "is_free": False,
        "description": "Open-weight reasoning model matching frontier standards",
        "category": "Reasoning"
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Meta Llama 3.3 70B",
        "provider": "Meta",
        "is_free": False,
        "description": "Meta's flagship open model with immense general capability",
        "category": "Frontier Flagship"
    }
]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/settings", response_model=CouncilSettings)
async def get_council_settings():
    """Get currently active council settings."""
    settings = storage.get_settings()
    return settings


@app.post("/api/settings", response_model=CouncilSettings)
async def update_council_settings(settings: CouncilSettings):
    """Update active council models and chairman."""
    if not settings.council_models:
        raise HTTPException(status_code=400, detail="Council must have at least 1 model.")
    if settings.chairman_model not in settings.council_models:
        # If chairman is not in council, add it or default to first
        settings.council_models.append(settings.chairman_model)

    saved = storage.save_settings(settings.model_dump())
    return saved


@app.get("/api/models")
async def list_available_models():
    """Return available models for council selection."""
    return CURATED_MODELS


@app.get("/api/personas")
async def list_available_personas():
    """Return available specialized council personas."""
    return list(COUNCIL_PERSONAS.values())



@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}", status_code=204)
async def remove_conversation(conversation_id: str):
    """Delete a specific conversation permanently."""
    deleted = delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    settings = storage.get_settings()
    council_models = request.council_models or settings.get("council_models")
    chairman_model = request.chairman_model or settings.get("chairman_model")
    persona = request.persona or settings.get("persona", "strict_truth")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content, chairman_model=chairman_model)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content,
        council_models=council_models,
        chairman_model=chairman_model,
        persona=persona
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result,
        metadata=metadata
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    settings = storage.get_settings()
    council_models = request.council_models or settings.get("council_models")
    chairman_model = request.chairman_model or settings.get("chairman_model")
    persona = request.persona or settings.get("persona", "strict_truth")
    persona_obj = get_persona(persona)

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(
                    generate_conversation_title(request.content, chairman_model=chairman_model)
                )

            # Emit persona info
            yield f"data: {json.dumps({'type': 'persona_info', 'persona': persona_obj})}\n\n"

            # Stage 1: Collect responses with live streaming
            yield f"data: {json.dumps({'type': 'stage1_start', 'models': council_models, 'persona': persona})}\n\n"
            stage1_results = []
            async for ev in stage1_collect_responses_stream(
                request.content,
                council_models=council_models,
                persona=persona
            ):
                if ev["type"] == "token":
                    yield f"data: {json.dumps({'type': 'stage1_token', 'model': ev['model'], 'token': ev['token']})}\n\n"
                elif ev["type"] == "complete":
                    stage1_results = ev["data"]
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings with live streaming
            stage2_models = [r['model'] for r in stage1_results if r.get('response')]
            yield f"data: {json.dumps({'type': 'stage2_start', 'models': stage2_models, 'persona': persona})}\n\n"
            stage2_results = []
            label_to_model = {}
            async for ev in stage2_collect_rankings_stream(
                request.content,
                stage1_results,
                council_models=council_models,
                persona=persona
            ):
                if ev["type"] == "token":
                    yield f"data: {json.dumps({'type': 'stage2_token', 'model': ev['model'], 'token': ev['token']})}\n\n"
                elif ev["type"] == "complete":
                    stage2_results = ev["data"]
                    label_to_model = ev["label_to_model"]

            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            consensus = calculate_consensus_metrics(stage2_results, label_to_model, aggregate_rankings)
            metadata = {
                'label_to_model': label_to_model,
                'aggregate_rankings': aggregate_rankings,
                'consensus': consensus,
                'persona': persona_obj
            }
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': metadata})}\n\n"

            # Stage 3: Synthesize final answer with token-by-token streaming
            yield f"data: {json.dumps({'type': 'stage3_start', 'chairman': chairman_model, 'persona': persona})}\n\n"
            stage3_result = None
            async for ev in stage3_synthesize_final_stream(
                request.content,
                stage1_results,
                stage2_results,
                chairman_model=chairman_model,
                persona=persona
            ):
                if ev["type"] == "token":
                    yield f"data: {json.dumps({'type': 'stage3_token', 'token': ev['token']})}\n\n"
                elif ev["type"] == "complete":
                    stage3_result = ev["data"]

            if not stage3_result:
                stage3_result = {"model": chairman_model, "response": "Error generating synthesis."}

            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message with metadata
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result,
                metadata=metadata
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)

