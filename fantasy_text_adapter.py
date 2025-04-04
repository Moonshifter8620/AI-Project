import os
import logging
import json
import hashlib
import re
import random
import sqlite3  # Add this import
from typing import Dict, List, Optional, Union, Any

# Use relative import for fantasy_Language
from .fantasy_Language import FantasyTextProcessor, EnhancedLanguageProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_adapter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fantasy_text_adapter")


class TextGenerationAdapter:
    """
    Adapter class to integrate FantasyTextProcessor with the context-aware
    language generation framework. Acts as a bridge between your existing
    corpus-based approach and the new service architecture.
    """

    def __init__(self, data_folder: str = None, cache_dir: str = None):
        """
        Initialize the adapter with FantasyTextProcessor.

        Args:
            data_folder: Directory containing corpus data
            cache_dir: Directory for caching responses
        """
        # Set default paths if not provided
        self.data_folder = data_folder or os.path.join(os.getcwd(), "data")
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "cache")

        # Create directories if they don't exist
        os.makedirs(self.data_folder, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        # Check for corpus.sqlite and create if missing
        corpus_file = os.path.join(self.data_folder, 'corpus.sqlite')
        if not os.path.exists(corpus_file):
            logger.warning(f"Corpus file not found: {corpus_file}")
            try:
                # Create a simple database with some sample data
                conn = sqlite3.connect(corpus_file)
                cursor = conn.cursor()

                # Create books table if it doesn't exist
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    title TEXT, 
                    full_text TEXT
                )
                ''')

                # Add a sample book if the table is empty
                cursor.execute("SELECT COUNT(*) FROM books")
                count = cursor.fetchone()[0]

                if count == 0:
                    sample_text = """
                    In the heart of the ancient forest stood the village of Oakhollow, 
                    where magic and mundane life intertwined. The tavern keeper, old Thaddeus,
                    knew every story worth telling, and the blacksmith's daughter could speak 
                    to birds. Beyond the village, mountains rose like sentinels, their peaks 
                    touching the clouds where dragons made their lairs.
                    """
                    cursor.execute("INSERT INTO books VALUES (?, ?)",
                                   ("Tales of Fantasy", sample_text))

                conn.commit()
                conn.close()
                logger.info(f"Created basic corpus file at {corpus_file}")
            except Exception as e:
                logger.error(f"Failed to create corpus database: {e}")

        # Initialize the FantasyTextProcessor
        logger.info(f"Initializing FantasyTextProcessor with data folder: {self.data_folder}")
        self.processor = FantasyTextProcessor(self.data_folder)

        # Load accents and other resources with error handling
        try:
            self.processor.load_accents()
        except Exception as e:
            logger.warning(f"Error loading accents: {e}")

        try:
            self.processor.process_books()
        except Exception as e:
            logger.warning(f"Error processing books: {e}, but continuing anyway")

        # Initialize the EnhancedLanguageProcessor for command processing
        self.command_processor = EnhancedLanguageProcessor()

        # Response cache
        self.response_cache = {}

        logger.info("TextGenerationAdapter initialized successfully")