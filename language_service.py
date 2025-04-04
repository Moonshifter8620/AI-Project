# language_service.py
import os
import logging
import json
import re
import random
import torch
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from contextlib import asynccontextmanager
from transformers import AutoTokenizer, AutoModelForCausalLM
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("language_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("language_service")


# Models for request/response
class DialogueRequest(BaseModel):
    npc_id: str
    npc_name: Optional[str] = None
    npc_type: str
    npc_race: str
    npc_attitude: str
    situation: str
    topic: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []
    personality_traits: Optional[List[str]] = []
    knowledge: Optional[Dict[str, Any]] = {}


class DescriptionRequest(BaseModel):
    location_type: str
    time_of_day: str = "day"
    weather: str = "clear"
    specific_features: Optional[List[str]] = None
    atmosphere: Optional[str] = "neutral"
    visited_before: bool = False
    significant_events: Optional[List[str]] = None


class CombatRequest(BaseModel):
    action_type: str
    outcome: str
    attacker: str
    defender: Optional[str] = None
    weapon: Optional[str] = None
    spell: Optional[str] = None
    damage_amount: Optional[int] = None
    critical: bool = False
    combat_state: Optional[Dict[str, Any]] = {}
    previous_actions: Optional[List[Dict[str, Any]]] = []


class QuestRequest(BaseModel):
    quest_type: Optional[str] = None
    difficulty: str = "medium"
    level: int = 1
    location: Optional[str] = None
    giver: Optional[str] = None
    party_info: Optional[Dict[str, Any]] = {}
    world_state: Optional[Dict[str, Any]] = {}


class TransitionRequest(BaseModel):
    from_scene: str
    to_scene: str
    mood: str = "neutral"
    time_passed: str = "immediate"
    party_state: Optional[Dict[str, Any]] = {}
    significant_events: Optional[List[str]] = None


class GenerationResponse(BaseModel):
    text: str
    alternatives: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = {}
    status: str = "success"
    message: Optional[str] = None


# Model loading context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model on startup
    logger.info("Loading language model...")
    try:
        app.state.model_name = "PygmalionAI/pygmalion-6b"
        app.state.tokenizer = AutoTokenizer.from_pretrained(app.state.model_name)
        app.state.model = AutoModelForCausalLM.from_pretrained(
            app.state.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        logger.info(f"Model {app.state.model_name} loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        # Create dummy model and tokenizer for fallback
        logger.warning("Creating dummy model for fallback")
        app.state.model = None
        app.state.tokenizer = None

    # Initialize cache
    app.state.response_cache = {}

    yield

    # Cleanup on shutdown
    logger.info("Shutting down language service")
    app.state.model = None
    app.state.tokenizer = None
    torch.cuda.empty_cache()


# Create FastAPI app
app = FastAPI(
    title="Fantasy Language Service",
    description="AI-driven language generation for fantasy RPG contexts",
    version="1.0.0",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": app.state.model is not None}


# Dialogue generation endpoint
@app.post("/generate/dialogue", response_model=GenerationResponse)
async def generate_dialogue(request: DialogueRequest):
    try:
        # Generate dialogue using model
        logger.info(f"Generating dialogue for NPC {request.npc_id} ({request.npc_type})")

        # Check cache for similar request
        cache_key = f"dialogue_{request.npc_id}_{request.situation}_{request.topic}"
        if cache_key in app.state.response_cache:
            logger.info(f"Cache hit for {cache_key}")
            return app.state.response_cache[cache_key]

        if app.state.model is None:
            # Fallback if model failed to load
            logger.warning("Using fallback for dialogue generation")
            fallback_text = f"{request.npc_name or 'The ' + request.npc_type}: \"Greetings, adventurer. I'm afraid I cannot be more talkative at the moment.\""
            response = GenerationResponse(
                text=fallback_text,
                status="fallback",
                message="Using template fallback due to model unavailability"
            )
        else:
            # Generate with model
            text = await generate_with_model(
                app.state.model,
                app.state.tokenizer,
                construct_dialogue_prompt(request)
            )

            response = GenerationResponse(
                text=text,
                metadata={
                    "npc_id": request.npc_id,
                    "topic": request.topic
                }
            )

            # Cache the response
            app.state.response_cache[cache_key] = response

        return response
    except Exception as e:
        logger.error(f"Error generating dialogue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Environment description endpoint
@app.post("/generate/description", response_model=GenerationResponse)
async def generate_description(request: DescriptionRequest):
    try:
        logger.info(f"Generating description for {request.location_type}")

        # Check cache
        cache_key = f"description_{request.location_type}_{request.time_of_day}_{request.weather}"
        if cache_key in app.state.response_cache:
            logger.info(f"Cache hit for {cache_key}")
            return app.state.response_cache[cache_key]

        if app.state.model is None:
            # Fallback if model failed to load
            logger.warning("Using fallback for description generation")
            fallback_text = f"You find yourself in a {request.location_type}. It is {request.time_of_day} and the weather is {request.weather}."
            response = GenerationResponse(
                text=fallback_text,
                status="fallback",
                message="Using template fallback due to model unavailability"
            )
        else:
            # Generate with model
            text = await generate_with_model(
                app.state.model,
                app.state.tokenizer,
                construct_description_prompt(request)
            )

            response = GenerationResponse(
                text=text,
                metadata={
                    "location_type": request.location_type,
                    "time_of_day": request.time_of_day,
                    "weather": request.weather
                }
            )

            # Cache the response
            app.state.response_cache[cache_key] = response

        return response
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Combat narration endpoint
@app.post("/generate/combat", response_model=GenerationResponse)
async def generate_combat(request: CombatRequest):
    try:
        logger.info(f"Generating combat narration for {request.action_type} - {request.outcome}")

        if app.state.model is None:
            # Fallback if model failed to load
            logger.warning("Using fallback for combat narration")
            if "hit" in request.outcome:
                fallback_text = f"{request.attacker} attacks {request.defender or 'the enemy'} and hits."
            else:
                fallback_text = f"{request.attacker} attacks {request.defender or 'the enemy'} but misses."

            response = GenerationResponse(
                text=fallback_text,
                status="fallback",
                message="Using template fallback due to model unavailability"
            )
        else:
            # Generate with model
            text = await generate_with_model(
                app.state.model,
                app.state.tokenizer,
                construct_combat_prompt(request)
            )

            response = GenerationResponse(
                text=text,
                metadata={
                    "action_type": request.action_type,
                    "outcome": request.outcome
                }
            )

        return response
    except Exception as e:
        logger.error(f"Error generating combat narration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Quest generation endpoint
@app.post("/generate/quest", response_model=GenerationResponse)
async def generate_quest(request: QuestRequest):
    try:
        logger.info(f"Generating quest of type {request.quest_type or 'random'}")

        if app.state.model is None:
            # Fallback if model failed to load
            logger.warning("Using fallback for quest generation")
            fallback_text = json.dumps({
                "title": "A Simple Task",
                "description": f"A simple task is requested of brave adventurers in {request.location or 'the area'}.",
                "type": request.quest_type or "retrieval",
                "difficulty": request.difficulty,
                "level": request.level,
            })

            response = GenerationResponse(
                text=fallback_text,
                status="fallback",
                message="Using template fallback due to model unavailability"
            )
        else:
            # Generate with model
            text = await generate_with_model(
                app.state.model,
                app.state.tokenizer,
                construct_quest_prompt(request)
            )

            # Parse the response into a structured quest
            try:
                quest_data = json.loads(text)
                response = GenerationResponse(
                    text=json.dumps(quest_data),
                    metadata={
                        "quest_type": request.quest_type,
                        "difficulty": request.difficulty,
                        "level": request.level
                    }
                )
            except json.JSONDecodeError:
                # If the model didn't return valid JSON, wrap the text
                quest_data = {
                    "title": "Mysterious Quest",
                    "description": text,
                    "type": request.quest_type or "mystery",
                    "difficulty": request.difficulty,
                    "level": request.level
                }
                response = GenerationResponse(
                    text=json.dumps(quest_data),
                    status="partial_success",
                    message="Model output was not valid JSON, wrapped in basic structure"
                )

        return response
    except Exception as e:
        logger.error(f"Error generating quest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Narrative transition endpoint
@app.post("/generate/transition", response_model=GenerationResponse)
async def generate_transition(request: TransitionRequest):
    try:
        logger.info(f"Generating transition from {request.from_scene} to {request.to_scene}")

        if app.state.model is None:
            # Fallback if model failed to load
            logger.warning("Using fallback for transition generation")
            fallback_text = f"The party travels from {request.from_scene} to {request.to_scene}."

            response = GenerationResponse(
                text=fallback_text,
                status="fallback",
                message="Using template fallback due to model unavailability"
            )
        else:
            # Generate with model
            text = await generate_with_model(
                app.state.model,
                app.state.tokenizer,
                construct_transition_prompt(request)
            )

            response = GenerationResponse(
                text=text,
                metadata={
                    "from_scene": request.from_scene,
                    "to_scene": request.to_scene,
                    "mood": request.mood
                }
            )

        return response
    except Exception as e:
        logger.error(f"Error generating transition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to generate text with the model
async def generate_with_model(model, tokenizer, prompt, max_length=100, temperature=0.7):
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Generate text
        with torch.no_grad():
            output = model.generate(
                inputs.input_ids,
                max_length=max_length,
                do_sample=True,
                temperature=temperature,
                top_p=0.9,
                repetition_penalty=1.2,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode the generated text
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

        # Extract response part (after prompt)
        response = generated_text[len(prompt):].strip()

        # Clean up response
        response = clean_response(response)

        return response
    except Exception as e:
        logger.error(f"Error in generate_with_model: {e}")
        return f"Error generating text: {str(e)}"


# Helper function to clean model output
def clean_response(text):
    # Remove any trailing incomplete sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if sentences and not sentences[-1].endswith(('.', '!', '?')):
        sentences = sentences[:-1]

    cleaned_text = ' '.join(sentences).strip()

    # Ensure text starts with a capital letter
    if cleaned_text and cleaned_text[0].islower():
        cleaned_text = cleaned_text[0].upper() + cleaned_text[1:]

    # Ensure text ends with punctuation
    if cleaned_text and not cleaned_text[-1] in '.!?':
        cleaned_text += '.'

    return cleaned_text


# Prompt construction functions
def construct_dialogue_prompt(request: DialogueRequest) -> str:
    dialogue_history = ""
    if request.history:
        dialogue_history = "\nPrevious conversation:\n"
        for entry in request.history:
            if 'player' in entry:
                dialogue_history += f"Player: {entry['player']}\n"
            if 'npc' in entry:
                dialogue_history += f"{request.npc_name or 'NPC'}: {entry['npc']}\n"

    personality = ""
    if request.personality_traits:
        personality = "\nPersonality: " + ", ".join(request.personality_traits)

    knowledge_context = ""
    if request.knowledge:
        knowledge_context = "\nRelevant knowledge:\n"
        for key, value in request.knowledge.items():
            knowledge_context += f"- {key}: {value}\n"

    prompt = f"""Generate dialogue for a fantasy RPG non-player character (NPC).

    Character information:
    - Name: {request.npc_name or 'Unknown'}
    - Type: {request.npc_type}
    - Race: {request.npc_race}
    - Attitude: {request.npc_attitude}{personality}

    Current situation: {request.situation}
    Topic: {request.topic or 'General conversation'}{knowledge_context}{dialogue_history}

    The NPC speaks in a way that reflects their race and personality. Their response is:
    """
    return prompt


def construct_description_prompt(request: DescriptionRequest) -> str:
    features = ""
    if request.specific_features:
        features = "\nNotable features:\n- " + "\n- ".join(request.specific_features)

    events = ""
    if request.significant_events:
        events = "\nSignificant events that happened here:\n- " + "\n- ".join(request.significant_events)

    visited = "This is the first time the party has been here." if not request.visited_before else "The party has been here before."

    prompt = f"""Generate a vivid description of a fantasy RPG environment.

    Location: {request.location_type}
    Time of day: {request.time_of_day}
    Weather: {request.weather}
    Atmosphere: {request.atmosphere}
    {visited}{features}{events}

    Provide a rich, evocative description that engages multiple senses and establishes the mood:
    """
    return prompt


def construct_combat_prompt(request: CombatRequest) -> str:
    weapon_info = f"using a {request.weapon}" if request.weapon else ""
    spell_info = f"casting {request.spell}" if request.spell else ""
    damage_info = f"dealing {request.damage_amount} damage" if request.damage_amount else ""

    # Get previous actions context
    history = ""
    if request.previous_actions:
        history = "\nRecent combat actions:\n"
        for i, action in enumerate(request.previous_actions[-3:]):  # Last 3 actions
            history += f"{i + 1}. {action.get('description', 'Unknown action')}\n"

    critical_info = "This is a critical hit/success!" if request.critical and "hit" in request.outcome else ""
    critical_info = "This is a critical failure!" if request.critical and "miss" in request.outcome else critical_info

    prompt = f"""Generate a vivid combat description for a fantasy RPG battle.

    Action: {request.action_type}
    Outcome: {request.outcome}
    Attacker: {request.attacker}
    Defender: {request.defender or 'the enemy'}
    {weapon_info}
    {spell_info}
    {damage_info}
    {critical_info}{history}

    Describe this combat action in a cinematic, exciting way:
    """
    return prompt


def construct_quest_prompt(request: QuestRequest) -> str:
    party_info = ""
    if request.party_info:
        party_info = "\nParty information:\n"
        for key, value in request.party_info.items():
            party_info += f"- {key}: {value}\n"

    world_info = ""
    if request.world_state:
        world_info = "\nWorld state:\n"
        for key, value in request.world_state.items():
            world_info += f"- {key}: {value}\n"

    prompt = f"""Generate a detailed quest for a fantasy RPG game.

    Quest type: {request.quest_type or 'Any appropriate type'}
    Difficulty: {request.difficulty}
    Recommended level: {request.level}
    Location: {request.location or 'To be determined based on the quest'}
    Quest giver: {request.giver or 'An appropriate NPC'}{party_info}{world_info}

    Create a quest with a title, description, objective, and rewards. Format the response as a JSON object with the following structure:
    {{
      "title": "Quest Title",
      "type": "quest_type",
      "description": "Detailed quest description",
      "objective": "What the players need to accomplish",
      "rewards": ["List of rewards"],
      "difficulty": "{request.difficulty}",
      "level": {request.level},
      "location": "Where the quest takes place",
      "giver": "Who gives the quest"
    }}

    Generated quest:
    """
    return prompt


def construct_transition_prompt(request: TransitionRequest) -> str:
    events = ""
    if request.significant_events:
        events = "\nRecent significant events:\n- " + "\n- ".join(request.significant_events)

    party_state = ""
    if request.party_state:
        party_state = "\nParty state:\n"
        for key, value in request.party_state.items():
            party_state += f"- {key}: {value}\n"

    prompt = f"""Generate a narrative transition for a fantasy RPG story.

    Current scene: {request.from_scene}
    Next scene: {request.to_scene}
    Emotional tone: {request.mood}
    Time passage: {request.time_passed}{events}{party_state}

    Create a vivid transition paragraph that bridges these scenes, conveying the appropriate passage of time and emotional tone:
    """
    return prompt


# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)