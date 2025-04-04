import os
import xml.etree.ElementTree as ET
import re
import sqlite3  # Add this import
import random   # Also good to have
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import warnings
import logging  # Useful for proper logging
# Set up logging
logger = logging.getLogger(__name__)

# Suppress warnings for a cleaner output
warnings.filterwarnings("ignore")


class FantasyTextProcessor:

    def __init__(self, data_folder):
        # Add these debug print statements
        print("Checking GPU Availability:")
        print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")
        print(f"torch.version.cuda: {torch.version.cuda}")
        print(f"torch.backends.cudnn.enabled: {torch.backends.cudnn.enabled}")

        try:
            if torch.cuda.is_available():
                print("CUDA Devices:")
                for i in range(torch.cuda.device_count()):
                    print(f"Device {i}: {torch.cuda.get_device_name(i)}")
                    print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9} GB")
        except Exception as e:
            print(f"Error checking CUDA devices: {e}")
        # Define model name first
        self.model_name = "PygmalionAI/pygmalion-6b"

        self.data_folder = data_folder
        self.books = []
        self.accents = {}
        self.allowed_references = self.load_historical_context()

        # Model and tokenizer initialization with error handling
        self.model = None
        self.tokenizer = None

        try:
            # Determine the best available device
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {device}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side='left',
                truncation_side='left'
            )

            # Ensure the tokenizer has a pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model with fallback for CPU
            if device.type == 'cpu':
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32  # Use float32 for CPU
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",  # Distribute across GPUs
                    torch_dtype=torch.float16,  # Use half-precision
                    low_cpu_mem_usage=True
                ).to(device)

        except Exception as e:
            print(f"Error loading language model: {e}")
            print("Falling back to minimal functionality.")

    def load_historical_context(self):
        # List of allowed 15th-century references aligned with D&D campaign settings
        return {
            "phone": "sending stone",
            "computer": "arcane device",
            "electricity": "magic",
            "car": "carriage",
            "airplane": "griffon",
            "robot": "golem",
            "television": "scrying mirror",
            "internet": "arcane network",
            "battery": "crystal of power",
            "radio": "sending device",
            "satellite": "floating castle",
            "machine": "contraption",
            "artificial intelligence": "awakened construct"
        }

    def load_and_parse_xml(self, file_name):
        file_path = os.path.join(self.data_folder, file_name)
        tree = ET.parse(file_path)
        root = tree.getroot()
        return root

    def process_books(self):
        """
        Process books from the Corpus.xml file with enhanced error handling
        """
        # Construct absolute paths
        corpus_paths = [
            os.path.join(self.data_folder, 'Corpus.xml'),
            os.path.join(self.data_folder, '..', 'NarrativeEngine', 'Corpus', 'Corpus.xml'),
            r'C:\DnD5e\NarrativeEngine\Corpus\Corpus.xml',
            r'C:\DnD5e\.venv1\Scripts\Corpus.xml'
        ]

        # Try multiple potential paths
        corpus_path = None
        for potential_path in corpus_paths:
            if os.path.exists(potential_path):
                corpus_path = potential_path
                break

        if not corpus_path:
            print("ERROR: Corpus.xml file could not be found. Checked paths:")
            for p in corpus_paths:
                print(f"- {p}")
            return  # Fail gracefully instead of raising an error

        try:
            # Parse the XML file
            print(f"Attempting to parse Corpus XML from: {corpus_path}")
            tree = ET.parse(corpus_path)
            root = tree.getroot()

            # Process each book in the corpus
            for book_elem in root.findall('book'):
                # Extract book title
                title_elem = book_elem.find('title')
                title = title_elem.text if title_elem is not None else "Untitled Book"

                # Collect all text entries for the book
                full_text = []
                for entry_elem in book_elem.findall('entry'):
                    text_elem = entry_elem.find('text')
                    if text_elem is not None and text_elem.text:
                        full_text.append(text_elem.text.strip())

                # Join text entries and clean
                book_text = ' '.join(full_text)
                cleaned_text = self.clean_text(book_text)

                # Add to books list
                self.books.append({
                    'title': title,
                    'full_text': cleaned_text
                })

            # Log the number of books processed
            print(f"Processed {len(self.books)} books from Corpus.xml")

        except ET.ParseError as e:
            print(f"XML Parsing Error: {e}")
            print(f"File contents: {open(corpus_path, 'r').read()[:500]}")  # Print first 500 chars for debugging
        except Exception as e:
            print(f"Unexpected error processing corpus: {e}")
            import traceback
            traceback.print_exc()

    def extract_book_data(self, root):
        for story in root.findall('Story'):
            title = story.find('Title').text
            full_text = self.clean_text(story.find('FullText').text.strip())
            self.books.append({
                'title': title,
                'full_text': full_text
            })

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
        return text

    def load_accents(self):
        # Load accents from accents.xml
        accents_root = self.load_and_parse_xml('accents.xml')
        for accent in accents_root.find('Accents'):
            accent_name = accent.attrib.get('name')
            race = accent.attrib.get('race')
            vocabulary = {}
            for word in accent.find('Vocabulary'):
                original = word.attrib.get('original')
                replacement = word.attrib.get('replacement')
                vocabulary[original] = replacement

            phrasing_rules = []
            for rule in accent.find('Phrasing'):
                phrasing_rules.append(rule.text.strip())

            self.accents[accent_name] = {
                'race': race,
                'vocabulary': vocabulary,
                'phrasing_rules': phrasing_rules,
                'region': accent.find('PlaceholderRegion').text.strip()
            }

    def apply_accent(self, text, accent_name):
        accent = self.accents.get(accent_name, None)
        if not accent:
            return text  # If accent is not found, return text unchanged

        # Apply vocabulary replacements
        words = text.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w\s]', '', word).lower()  # Remove punctuation for matching
            if clean_word in accent['vocabulary']:
                words[i] = words[i].replace(clean_word, accent['vocabulary'][clean_word])

        # Apply phrasing rules
        for rule in accent['phrasing_rules']:
            if "sentence_start" in rule:
                words.insert(0, rule.split('"')[1])
            elif "sentence_end" in rule:
                words.append(rule.split('"')[1])

        return ' '.join(words)

    def replace_modern_elements(self, text):
        # Replace modern terms with 15th-century equivalents or fantasy terms
        for modern_term, replacement in self.allowed_references.items():
            text = re.sub(r'\b' + modern_term + r'\b', replacement, text, flags=re.IGNORECASE)
        return text

    def generate_text(self, prompt, max_length=150, accent_name=None, character_role=None, context=None):
        # If model is not loaded, return a fallback response
        if self.model is None or self.tokenizer is None:
            return "I'm unable to generate a response right now."

        """
        Generate fantasy text based on the given prompt with configurable parameters.

        Args:
            prompt: The user's input prompt
            max_length: Maximum length of generated text
            accent_name: Optional accent to apply to the response
            character_role: Optional role/persona for the AI (e.g., "wizard", "innkeeper", "narrator")
            context: Optional context dictionary with additional information

        Returns:
            Generated text with appropriate styling
        """
        # Build a dynamic system message based on provided context
        if context is None:
            context = {}

        # Set default character role if not provided
        if not character_role:
            if "location_type" in context:
                # Adjust role based on location
                if context["location_type"] == "tavern":
                    character_role = "tavern keeper"
                elif context["location_type"] == "forest":
                    character_role = "forest guide"
                elif context["location_type"] == "village":
                    character_role = "village storyteller"
                else:
                    character_role = "fantasy narrator"
            else:
                character_role = "fantasy narrator"

        # Build dynamic context information
        context_info = ""
        if "location_name" in context:
            context_info += f"Current location: {context['location_name']}. "
        if "time" in context:
            context_info += f"Time: {context['time']}. "
        if "weather" in context:
            context_info += f"Weather: {context['weather']}. "
        if "mood" in context:
            context_info += f"Mood: {context['mood']}. "

        # Build the prompt with dynamic elements
        system_msg = f"You are speaking as a {character_role} in a fantasy world. {context_info}"
        full_prompt = f"{system_msg}\n\nUser: {prompt}\nResponse:"

        # Prepare input for GPU
        try:
            device = next(self.model.parameters()).device

            # Tokenize input
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length
            ).to(device)

            # Generate text with PyTorch no_grad for efficiency
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_length=max_length + len(inputs.input_ids[0]),  # Adjust for prompt length
                    do_sample=True,
                    temperature=0.7,  # Slightly higher temperature for creativity
                    top_p=0.92,  # Nucleus sampling for diversity
                    pad_token_id=self.tokenizer.pad_token_id,
                    num_return_sequences=1,
                    use_cache=True
                )

            # Decode the generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract just the response part (remove the prompt)
            if "Response:" in generated_text:
                response_text = generated_text.split("Response:", 1)[1].strip()
            else:
                # Fallback extraction method
                prompt_parts = full_prompt.split("\n")
                last_prompt_part = prompt_parts[-1]
                if last_prompt_part in generated_text:
                    response_text = generated_text.split(last_prompt_part, 1)[1].strip()
                else:
                    # Ultimate fallback
                    response_text = generated_text.replace(full_prompt, "").strip()

            # Clean the generated text
            cleaned_text = self.clean_text(response_text)

            # Apply accent if specified
            if accent_name:
                accented_text = self.apply_accent(cleaned_text, accent_name)
                final_text = self.replace_modern_elements(accented_text)
            else:
                final_text = self.replace_modern_elements(cleaned_text)

            return final_text

        except Exception as e:
            print(f"Text generation error: {e}")
            return "I encountered an error while generating a response."

    def display_books(self):
        for book in self.books:
            print(f"Title: {book['title']}")
            print(f"Full Text: {book['full_text'][:200]}...")  # Display only first 200 characters


def interactive_test(processor):
    print("Welcome to the Fantasy Language Tester!")
    print("Type 'exit' to end the conversation.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        # Generate a response based on the user input
        response = processor.generate_text(user_input, accent_name=None)  # Change accent_name as needed
        print(f"Fantasy Language Bot: {response}\n")


if __name__ == "__main__":
    # Set the data folder path accordingly
    data_folder = "F:\\Pycharm\\MasterFolderForNewAI\\DM AI experiment\\Master\\language\\data"  # Corrected path
    processor = FantasyTextProcessor(data_folder)
    processor.load_accents()  # Load accents
    processor.process_books()  # Process books

    # Start the interactive test
    interactive_test(processor)

    class FantasyTextProcessor:
        def __init__(self, data_folder):
            # Define model name first
            self.model_name = "PygmalionAI/pygmalion-6b"

            self.data_folder = data_folder
            self.books = []
            self.accents = {}
            self.allowed_references = self.load_historical_context()

            # Model and tokenizer initialization with error handling
            self.model = None
            self.tokenizer = None

            try:
                # Determine the best available device
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                print(f"Using device: {device}")

                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    padding_side='left',
                    truncation_side='left'
                )

                # Ensure the tokenizer has a pad token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

                # Load model with GPU optimizations
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",  # Distribute across GPUs
                    torch_dtype=torch.float16,  # Use half-precision
                    low_cpu_mem_usage=True
                ).to(device)

            except Exception as e:
                print(f"Error loading language model: {e}")
                print("Falling back to minimal functionality.")

        def generate_dialogue(self, npc_attributes, context):
            # Generate dialogue based on NPC attributes and context
            prompt = self.create_prompt(npc_attributes, context)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(inputs["input_ids"], max_length=150)
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text

        def create_prompt(self, npc_attributes, context):
            # Create a prompt based on NPC attributes
            attributes_str = ', '.join(f"{key}: {value}" for key, value in npc_attributes.items())
            return f"The following NPC has attributes: {attributes_str}. In the context of {context}, generate dialogue."

        def load_historical_context(self):
            # List of allowed references aligned with D&D campaign settings
            return {
                "phone": "sending stone",
                "computer": "arcane device",
                "electricity": "magic",
                "car": "carriage",
                "airplane": "flying beast"
            }

        def apply_accent(self, text, accent_type):
            # Apply an accent style to the generated text
            if accent_type in self.accents:
                return self.accents[accent_type](text)  # Assuming accent functions are defined
            return text  # No accent applied

        def load_accent_data(self):
            # Load or define accent data to enhance speech variability
            self.accents = {
                "elvish": lambda text: text + " (with a melodic tone)",
                "dwarvish": lambda text: text + " (with a gruff voice)",
            }

        def handle_error(self, error):
            # Error handling for model loading and generation
            print(f"Error: {error}. Please check the model configuration or input data.")

import re

class EnhancedLanguageProcessor:
    def __init__(self):
        pass

    def process_input(self, user_input):
        # Normalize the input for better processing
        user_input = user_input.lower().strip()
        
        # Basic command recognition
        if re.search(r'attack|hit|strike', user_input):
            return self.handle_attack_command(user_input)
        elif re.search(r'help|assist', user_input):
            return "You called for assistance?"
        elif re.search(r'go|move|travel', user_input):
            return self.handle_movement_command(user_input)
        else:
            return "I'm not sure what you mean. Can you clarify?"

    def handle_attack_command(self, user_input):
        # Simplified attack command handling logic
        return "You prepare to attack!"

    def handle_movement_command(self, user_input):
        # Simplified movement command handling logic
        return "You start moving forward."

# Example usage
def main_language_processing():
    processor = EnhancedLanguageProcessor()
    print(processor.process_input("I want to attack the dragon"))
    print(processor.process_input("Help me!"))
    print(processor.process_input("Let's move to the next area"))
    print(processor.process_input("What should I do now?"))

class NPC:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality  # Personality traits
        self.mood = 'neutral'  # Current mood of the NPC
        self.dialogue_options = {
            'greeting': f"{self.name} greets you warmly.",
            'farewell': f"{self.name} bids you farewell.",
            'help': f"{self.name} offers assistance."
        }

    def update_mood(self, new_mood):
        self.mood = new_mood  # Update mood based on interactions

    def generate_dialogue(self):
        dialogue = {
            'brave': f"{self.name} stands tall, ready for anything.",
            'cowardly': f"{self.name} looks around nervously, unsure of what to do.",
            'wise': f"{self.name} offers sage advice.",
            'neutral': f"{self.name} doesn't seem to know what to say."
        }
        return dialogue.get(self.personality, "No dialogue available.")

    def interact(self, action):
        if action in self.dialogue_options:
            return self.dialogue_options[action]
        return f"{self.name} doesn't respond to that."

# Example usage within the AI's main loop:
def main_npc_interaction():
    npc = NPC("Eldrin", "wise")
    print(npc.interact('greeting'))  # Greeting interaction
    print(npc.interact('help'))  # Help interaction
    npc.update_mood('happy')  # Update mood
    print(npc.generate_dialogue())  # Generate dialogue based on personality

class NPC:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality  # Personality traits
        self.mood = 'neutral'  # Current mood of the NPC
        self.relationship_score = 0  # Relationship score with the player
        self.dialogue_options = {
            'greeting': f"{self.name} greets you warmly.",
            'farewell': f"{self.name} bids you farewell.",
            'help': f"{self.name} offers assistance."
        }

    def update_mood(self, new_mood):
        self.mood = new_mood  # Update mood based on interactions

    def update_relationship(self, change):
        self.relationship_score += change  # Modify relationship score
        if self.relationship_score > 10:
            self.relationship_score = 10  # Max cap
        elif self.relationship_score < -10:
            self.relationship_score = -10  # Min cap

    def generate_dialogue(self):
        dialogue = {
            'brave': f"{self.name} stands tall, ready for anything.",
            'cowardly': f"{self.name} looks around nervously, unsure of what to do.",
            'wise': f"{self.name} offers sage advice.",
            'neutral': f"{self.name} doesn't seem to know what to say."
        }
        return dialogue.get(self.personality, "No dialogue available.")

    def interact(self, action):
        if action in self.dialogue_options:
            return self.dialogue_options[action]
        return f"{self.name} doesn't respond to that."

    def display_relationship_status(self):
        if self.relationship_score > 5:
            return f"{self.name} seems to really like you!"
        elif self.relationship_score < -5:
            return f"{self.name} does not trust you."
        else:
            return f"{self.name} feels neutral about you."

# Example usage within the AI's main loop:
def main_relationship_interaction():
    npc = NPC("Eldrin", "wise")
    print(npc.interact('greeting'))  # Greeting interaction
    npc.update_relationship(5)  # Positive interaction
    print(npc.display_relationship_status())  # Display relationship status
    npc.update_relationship(-7)  # Negative interaction
    print(npc.display_relationship_status())  # Display relationship status

class NPC:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality  # Personality traits
        self.mood = 'neutral'  # Current mood of the NPC
        self.relationship_score = 0  # Relationship score with the player
        self.dialogue_options = {
            'greeting': f"{self.name} greets you warmly.",
            'farewell': f"{self.name} bids you farewell.",
            'help': f"{self.name} offers assistance."
        }

    def update_mood(self, new_mood):
        self.mood = new_mood  # Update mood based on interactions

    def update_relationship(self, change):
        self.relationship_score += change  # Modify relationship score
        if self.relationship_score > 10:
            self.relationship_score = 10  # Max cap
        elif self.relationship_score < -10:
            self.relationship_score = -10  # Min cap

    def generate_dialogue(self):
        dialogue = {
            'brave': f"{self.name} stands tall, ready for anything.",
            'cowardly': f"{self.name} looks around nervously, unsure of what to do.",
            'wise': f"{self.name} offers sage advice.",
            'neutral': f"{self.name} doesn't seem to know what to say."
        }
        return dialogue.get(self.personality, "No dialogue available.")

    def interact(self, action):
        if action in self.dialogue_options:
            return self.dialogue_options[action]
        return f"{self.name} doesn't respond to that."

    def display_relationship_status(self):
        if self.relationship_score > 5:
            return f"{self.name} seems to really like you!"
        elif self.relationship_score < -5:
            return f"{self.name} does not trust you."
        else:
            return f"{self.name} feels neutral about you."

    def react_based_on_relationship(self):
        if self.relationship_score > 5:
            return f"{self.name} smiles and offers you a gift."
        elif self.relationship_score < -5:
            return f"{self.name} glares at you suspiciously."
        else:
            return f"{self.name} nods and keeps a neutral stance."

# Example usage within the AI's main loop:
def main_dynamic_behavior_interaction():
    npc = NPC("Eldrin", "wise")
    print(npc.interact('greeting'))  # Greeting interaction
    npc.update_relationship(6)  # Positive interaction
    print(npc.react_based_on_relationship())  # React based on relationship
    npc.update_relationship(-8)  # Negative interaction
    print(npc.react_based_on_relationship())  # React based on relationship

import random

class NPC:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality  # Personality traits
        self.mood = 'neutral'  # Current mood of the NPC
        self.relationship_score = 0  # Relationship score with the player
        self.dialogue_options = {
            'greeting': f"{self.name} greets you warmly.",
            'farewell': f"{self.name} bids you farewell.",
            'help': f"{self.name} offers assistance."
        }

    def update_mood(self, new_mood):
        self.mood = new_mood  # Update mood based on interactions

    def update_relationship(self, change):
        self.relationship_score += change  # Modify relationship score
        if self.relationship_score > 10:
            self.relationship_score = 10  # Max cap
        elif self.relationship_score < -10:
            self.relationship_score = -10  # Min cap

    def generate_dialogue(self):
        dialogue = {
            'brave': f"{self.name} stands tall, ready for anything.",
            'cowardly': f"{self.name} looks around nervously, unsure of what to do.",
            'wise': f"{self.name} offers sage advice.",
            'neutral': f"{self.name} doesn't seem to know what to say."
        }
        return dialogue.get(self.personality, "No dialogue available.")

    def interact(self, action):
        if action in self.dialogue_options:
            return self.dialogue_options[action]
        return f"{self.name} doesn't respond to that."

    def display_relationship_status(self):
        if self.relationship_score > 5:
            return f"{self.name} seems to really like you!"
        elif self.relationship_score < -5:
            return f"{self.name} does not trust you."
        else:
            return f"{self.name} feels neutral about you."

    def react_based_on_relationship(self):
        if self.relationship_score > 5:
            return f"{self.name} smiles and offers you a gift."
        elif self.relationship_score < -5:
            return f"{self.name} glares at you suspiciously."
        else:
            return f"{self.name} nods and keeps a neutral stance."

    def random_event(self):
        events = [
            f"{self.name} shares a local rumor with you.",
            f"{self.name} asks you to help with a small task.",
            f"{self.name} seems distracted and lost in thought.",
            f"{self.name} offers you a drink.",
            f"{self.name} warns you about a danger nearby."
        ]
        return random.choice(events)

# Example usage within the AI's main loop:
def main_random_event_interaction():
    npc = NPC("Eldrin", "wise")
    print(npc.interact('greeting'))  # Greeting interaction
    print(npc.random_event())  # Trigger a random NPC event

class Quest:
    def __init__(self, title, description, rewards):
        self.title = title
        self.description = description
        self.rewards = rewards  # List of rewards for completing the quest
        self.completed = False  # Quest completion status

    def complete_quest(self):
        self.completed = True  # Mark the quest as completed

class NPC:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality  # Personality traits
        self.mood = 'neutral'  # Current mood of the NPC
        self.relationship_score = 0  # Relationship score with the player
        self.dialogue_options = {
            'greeting': f"{self.name} greets you warmly.",
            'farewell': f"{self.name} bids you farewell.",
            'help': f"{self.name} offers assistance."
        }
        self.quests = []  # List of quests assigned by the NPC

    def update_mood(self, new_mood):
        self.mood = new_mood  # Update mood based on interactions

    def update_relationship(self, change):
        self.relationship_score += change  # Modify relationship score
        if self.relationship_score > 10:
            self.relationship_score = 10  # Max cap
        elif self.relationship_score < -10:
            self.relationship_score = -10  # Min cap

    def generate_dialogue(self):
        dialogue = {
            'brave': f"{self.name} stands tall, ready for anything.",
            'cowardly': f"{self.name} looks around nervously, unsure of what to do.",
            'wise': f"{self.name} offers sage advice.",
            'neutral': f"{self.name} doesn't seem to know what to say."
        }
        return dialogue.get(self.personality, "No dialogue available.")

    def interact(self, action):
        if action in self.dialogue_options:
            return self.dialogue_options[action]
        return f"{self.name} doesn't respond to that."

    def display_relationship_status(self):
        if self.relationship_score > 5:
            return f"{self.name} seems to really like you!"
        elif self.relationship_score < -5:
            return f"{self.name} does not trust you."
        else:
            return f"{self.name} feels neutral about you."

    def react_based_on_relationship(self):
        if self.relationship_score > 5:
            return f"{self.name} smiles and offers you a gift."
        elif self.relationship_score < -5:
            return f"{self.name} glares at you suspiciously."
        else:
            return f"{self.name} nods and keeps a neutral stance."

    def random_event(self):
        events = [
            f"{self.name} shares a local rumor with you.",
            f"{self.name} asks you to help with a small task.",
            f"{self.name} seems distracted and lost in thought.",
            f"{self.name} offers you a drink.",
            f"{self.name} warns you about a danger nearby."
        ]
        return random.choice(events)

    def assign_quest(self, title, description, rewards):
        quest = Quest(title, description, rewards)  # Create a new quest
        self.quests.append(quest)  # Add the quest to the NPC's quest list
        return f"{self.name} has assigned you a new quest: {title}"

# Example usage within the AI's main loop:
def main_quest_system_interaction():
    npc = NPC("Eldrin", "wise")
    print(npc.interact('greeting'))  # Greeting interaction
    quest_assignment_output = npc.assign_quest("Find the Lost Amulet", "Retrieve the amulet from the ancient ruins.", ["gold", "experience"])
    print(quest_assignment_output)  # Print the quest assignment

class Faction:
    def __init__(self, name, goals):
        self.name = name
        self.goals = goals  # List of goals for the faction
        self.npc_members = []  # List of NPCs belonging to the faction

    def add_npc(self, npc):
        self.npc_members.append(npc)  # Add NPC to the faction

class NPC:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality  # Personality traits
        self.mood = 'neutral'  # Current mood of the NPC
        self.relationship_score = 0  # Relationship score with the player
        self.dialogue_options = {
            'greeting': f"{self.name} greets you warmly.",
            'farewell': f"{self.name} bids you farewell.",
            'help': f"{self.name} offers assistance."
        }
        self.quests = []  # List of quests assigned by the NPC
        self.faction = None  # Faction the NPC belongs to

    def update_mood(self, new_mood):
        self.mood = new_mood  # Update mood based on interactions

    def update_relationship(self, change):
        self.relationship_score += change  # Modify relationship score
        if self.relationship_score > 10:
            self.relationship_score = 10  # Max cap
        elif self.relationship_score < -10:
            self.relationship_score = -10  # Min cap

    def generate_dialogue(self):
        dialogue = {
            'brave': f"{self.name} stands tall, ready for anything.",
            'cowardly': f"{self.name} looks around nervously, unsure of what to do.",
            'wise': f"{self.name} offers sage advice.",
            'neutral': f"{self.name} doesn't seem to know what to say."
        }
        return dialogue.get(self.personality, "No dialogue available.")

    def interact(self, action):
        if action in self.dialogue_options:
            return self.dialogue_options[action]
        return f"{self.name} doesn't respond to that."

    def display_relationship_status(self):
        if self.relationship_score > 5:
            return f"{self.name} seems to really like you!"
        elif self.relationship_score < -5:
            return f"{self.name} does not trust you."
        else:
            return f"{self.name} feels neutral about you."

    def react_based_on_relationship(self):
        if self.relationship_score > 5:
            return f"{self.name} smiles and offers you a gift."
        elif self.relationship_score < -5:
            return f"{self.name} glares at you suspiciously."
        else:
            return f"{self.name} nods and keeps a neutral stance."

    def random_event(self):
        events = [
            f"{self.name} shares a local rumor with you.",
            f"{self.name} asks you to help with a small task.",
            f"{self.name} seems distracted and lost in thought.",
            f"{self.name} offers you a drink.",
            f"{self.name} warns you about a danger nearby."
        ]
        return random.choice(events)

    def assign_quest(self, title, description, rewards):
        quest = Quest(title, description, rewards)  # Create a new quest
        self.quests.append(quest)  # Add the quest to the NPC's quest list
        return f"{self.name} has assigned you a new quest: {title}"

    def join_faction(self, faction):
        self.faction = faction  # Assign faction to the NPC
        faction.add_npc(self)  # Add NPC to the faction's member list
        return f"{self.name} has joined the {faction.name} faction!"

# Example usage within the AI's main loop:
def main_faction_system_interaction():
    faction = Faction("Guardians of the Realm", ["Protect the kingdom", "Defend against invaders"])
    npc = NPC("Eldrin", "wise")
    npc.join_faction(faction)  # NPC joins a faction
    print(npc.interact('greeting'))  # Greeting interaction
    print(f"{npc.name} is part of the {npc.faction.name} faction.")  # Check NPC faction
    