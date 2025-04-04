# language_service_integration.py
import os
import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn

from fantasy_text_adapter import TextGenerationAdapter

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

# Define data folder path
DATA_FOLDER = os.environ.get("DATA_FOLDER", "./data")
CACHE_DIR = os.environ.get("CACHE_DIR", "./cache")

# Model loading context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the adapter on startup
    logger.info("Initializing TextGenerationAdapter...")
    try:
        app.state.adapter = TextGenerationAdapter(
            data_folder=DATA_FOLDER,
            cache_dir=CACHE_DIR
        )
        logger.info("TextGenerationAdapter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize adapter: {e}")
        app.state.adapter = None

    yield

    # Cleanup on shutdown
    logger.info("Shutting down language service")
    app.state.adapter = None


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
    return {
        "status": "healthy", 
        "adapter_loaded": app.state.adapter is not None,
        "cache_size": len(app.state.adapter.response_cache) if app.state.adapter else 0
    }


# Dialogue generation endpoint
@app.post("/generate/dialogue")
async def generate_dialogue(request: Request):
    try:
        # Parse request body
        data = await request.json()
        
        # Generate dialogue using adapter
        if app.state.adapter:
            response = app.state.adapter.generate_dialogue(
                npc_id=data.get("npc_id", ""),
                npc_type=data.get("npc_type", "commoner"),
                npc_race=data.get("npc_race", "human"),
                npc_attitude=data.get("npc_attitude", "neutral"),
                situation=data.get("situation", ""),
                topic=data.get("topic"),
                npc_name=data.get("npc_name"),
                history=data.get("history"),
                personality_traits=data.get("personality_traits"),
                knowledge=data.get("knowledge", {})
            )
            return response
        else:
            # Fallback if adapter not loaded
            fallback_text = f"{data.get('npc_name', 'The ' + data.get('npc_type', 'NPC'))}: \"Greetings, adventurer. I'm afraid I cannot be more talkative at the moment.\""
            return {
                "text": fallback_text,
                "status": "fallback",
                "message": "Using template fallback due to adapter unavailability"
            }
            
    except Exception as e:
        logger.error(f"Error generating dialogue: {e}")
        return {
            "text": "Error generating dialogue.",
            "status": "error",
            "message": str(e)
        }


# Environment description endpoint
@app.post("/generate/description")
async def generate_description(request: Request):
    try:
        # Parse request body
        data = await request.json()
        
        # Generate description using adapter
        if app.state.adapter:
            response = app.state.adapter.generate_description(
                location_type=data.get("location_type", "area"),
                time_of_day=data.get("time_of_day", "day"),
                weather=data.get("weather", "clear"),
                specific_features=data.get("specific_features"),
                atmosphere=data.get("atmosphere", "neutral"),
                visited_before=data.get("visited_before", False),
                significant_events=data.get("significant_events")
            )
            return response
        else:
            # Fallback if adapter not loaded
            fallback_text = f"You find yourself in a {data.get('location_type', 'area')}. It is {data.get('time_of_day', 'day')} and the weather is {data.get('weather', 'clear')}."
            return {
                "text": fallback_text,
                "status": "fallback",
                "message": "Using template fallback due to adapter unavailability"
            }
            
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        return {
            "text": "Error generating description.",
            "status": "error",
            "message": str(e)
        }


# Combat narration endpoint
@app.post("/generate/combat")
async def generate_combat(request: Request):
    try:
        # Parse request body
        data = await request.json()
        
        # Generate combat description using adapter
        if app.state.adapter:
            response = app.state.adapter.generate_combat(
                action_type=data.get("action_type", "melee_attack"),
                outcome=data.get("outcome", "hit"),
                attacker=data.get("attacker", "The attacker"),
                defender=data.get("defender"),
                weapon=data.get("weapon"),
                spell=data.get("spell"),
                damage_amount=data.get("damage_amount"),
                critical=data.get("critical", False),
                combat_state=data.get("combat_state", {}),
                previous_actions=data.get("previous_actions", [])
            )
            return response
        else:
            # Fallback if adapter not loaded
            attacker = data.get("attacker", "The attacker")
            defender = data.get("defender", "the enemy")
            outcome = data.get("outcome", "hit")
            
            if "hit" in outcome:
                fallback_text = f"{attacker} attacks {defender} and hits."
            else:
                fallback_text = f"{attacker} attacks {defender} but misses."
                
            return {
                "text": fallback_text,
                "status": "fallback",
                "message": "Using template fallback due to adapter unavailability"
            }
            
    except Exception as e:
        logger.error(f"Error generating combat narration: {e}")
        return {
            "text": "Error generating combat narration.",
            "status": "error",
            "message": str(e)
        }


# Quest generation endpoint
@app.post("/generate/quest")
async def generate_quest(request: Request):
    try:
        # Parse request body
        data = await request.json()
        
        # Generate quest using adapter
        if app.state.adapter:
            response = app.state.adapter.generate_quest(
                quest_type=data.get("quest_type"),
                difficulty=data.get("difficulty", "medium"),
                level=data.get("level", 1),
                location=data.get("location"),
                giver=data.get("giver"),
                party_info=data.get("party_info", {}),
                world_state=data.get("world_state", {})
            )
            return response
        else:
            # Fallback if adapter not loaded
            import json
            
            fallback_quest = {
                "title": "A Simple Task",
                "description": f"A simple task is requested of brave adventurers in {data.get('location', 'the area')}.",
                "type": data.get("quest_type", "retrieval"),
                "difficulty": data.get("difficulty", "medium"),
                "level": data.get("level", 1),
                "location": data.get("location", "Nearby"),
                "giver": data.get("giver", "Village Elder"),
                "objective": "Complete the task",
                "rewards": {
                    "gold": 50 * data.get("level", 1),
                    "experience": 100 * data.get("level", 1)
                }
            }
                
            return {
                "text": json.dumps(fallback_quest),
                "status": "fallback",
                "message": "Using template fallback due to adapter unavailability"
            }
            
    except Exception as e:
        logger.error(f"Error generating quest: {e}")
        return {
            "text": "Error generating quest.",
            "status": "error",
            "message": str(e)
        }


# Narrative transition endpoint
@app.post("/generate/transition")
async def generate_transition(request: Request):
    try:
        # Parse request body
        data = await request.json()
        
        # Generate transition using adapter
        if app.state.adapter:
            response = app.state.adapter.generate_transition(
                from_scene=data.get("from_scene", "the previous location"),
                to_scene=data.get("to_scene", "the new location"),
                mood=data.get("mood", "neutral"),
                time_passed=data.get("time_passed", "immediate"),
                party_state=data.get("party_state", {}),
                significant_events=data.get("significant_events")
            )
            return response
        else:
            # Fallback if adapter not loaded
            from_scene = data.get("from_scene", "the previous location")
            to_scene = data.get("to_scene", "the new location")
            fallback_text = f"The party travels from {from_scene} to {to_scene}."
                
            return {
                "text": fallback_text,
                "status": "fallback",
                "message": "Using template fallback due to adapter unavailability"
            }
            
    except Exception as e:
        logger.error(f"Error generating transition: {e}")
        return {
            "text": "Error generating transition.",
            "status": "error",
            "message": str(e)
        }


# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)