# model_manager.py
import os
import logging
import torch
import time
from typing import Dict, List, Optional, Union, Any, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("model_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("model_manager")


class ModelManager:
    """Manages language model loading, inference, and caching."""

    def __init__(self, model_name="PygmalionAI/pygmalion-6b", cache_dir=None, device=None,
                 load_in_8bit=False, max_workers=2):
        """
        Initialize the model manager.

        Args:
            model_name: HuggingFace model identifier
            cache_dir: Directory to cache models
            device: Device to load model on ('cuda', 'cpu', etc.)
            load_in_8bit: Whether to load model in 8-bit quantization
            max_workers: Maximum number of worker threads for batch processing
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "model_cache")
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_in_8bit = load_in_8bit
        self.max_workers = max_workers

        # Initialize model and tokenizer to None
        self.model = None
        self.tokenizer = None

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

        # Response cache
        self.response_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # Lock for thread safety
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        # Stats
        self.total_tokens_generated = 0
        self.total_inference_time = 0
        self.inference_count = 0

        logger.info(f"Initialized ModelManager for {model_name} on {self.device}")

    def load_model(self) -> bool:
        """
        Load the model and tokenizer.

        Returns:
            bool: True if successful, False otherwise
        """
        if self.model is not None:
            logger.info("Model already loaded")
            return True

        try:
            logger.info(f"Loading tokenizer for {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )

            logger.info(f"Loading model {self.model_name} on {self.device}")
            start_time = time.time()

            # Determine loading parameters based on device and options
            load_kwargs = {
                "cache_dir": self.cache_dir,
                "device_map": "auto" if self.device == "cuda" else None,
            }

            if self.device == "cuda":
                if self.load_in_8bit:
                    load_kwargs["load_in_8bit"] = True
                else:
                    load_kwargs["torch_dtype"] = torch.float16

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **load_kwargs
            )

            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f} seconds")

            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.tokenizer = None
            return False

    def unload_model(self) -> bool:
        """
        Unload the model to free up memory.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Unloading model from memory")
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None

            # Force garbage collection
            import gc
            gc.collect()

            # Clear CUDA cache if applicable
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Model unloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return False

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None and self.tokenizer is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_model_loaded():
            return {"status": "not_loaded", "model_name": self.model_name}

        parameters = sum(p.numel() for p in self.model.parameters()) / 1_000_000

        return {
            "status": "loaded",
            "model_name": self.model_name,
            "device": self.device,
            "parameters_millions": round(parameters, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_tokens_generated": self.total_tokens_generated,
            "average_inference_time": self.total_inference_time / max(1, self.inference_count),
            "inference_count": self.inference_count
        }

    def check_cache(self, prompt: str, config_hash: str) -> Optional[str]:
        """
        Check if a response is cached for the given prompt and config.

        Args:
            prompt: The input prompt
            config_hash: Hash of generation configuration

        Returns:
            Optional[str]: Cached response if found, None otherwise
        """
        cache_key = f"{prompt}_{config_hash}"
        if cache_key in self.response_cache:
            self.cache_hits += 1
            return self.response_cache[cache_key]

        self.cache_misses += 1
        return None

    def add_to_cache(self, prompt: str, config_hash: str, response: str) -> None:
        """
        Add a response to the cache.

        Args:
            prompt: The input prompt
            config_hash: Hash of generation configuration
            response: Generated response to cache
        """
        cache_key = f"{prompt}_{config_hash}"
        self.response_cache[cache_key] = response

        # Limit cache size
        if len(self.response_cache) > 1000:
            # Remove a random item
            import random
            keys = list(self.response_cache.keys())
            del self.response_cache[random.choice(keys)]

    def generate_text(self, prompt: str, max_length: int = 100, temperature: float = 0.7,
                      top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2,
                      num_beams: int = 1, do_sample: bool = True, use_cache: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text based on a prompt.

        Args:
            prompt: Input prompt
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Penalty for repetition
            num_beams: Number of beams for beam search
            do_sample: Whether to use sampling
            use_cache: Whether to use response caching

        Returns:
            Tuple[str, Dict[str, Any]]: Generated text and metadata
        """
        # Load model if not loaded
        if not self.is_model_loaded():
            self.load_model()

        # Still not loaded? Return error
        if not self.is_model_loaded():
            return "Error: Model not loaded", {"error": "Model not loaded"}

        # Create config hash for caching
        config_hash = f"{max_length}_{temperature}_{top_p}_{top_k}_{repetition_penalty}_{num_beams}_{do_sample}"

        # Check cache if enabled
        if use_cache:
            cached_response = self.check_cache(prompt, config_hash)
            if cached_response:
                return cached_response, {"source": "cache"}

        try:
            # Encode the prompt
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            input_length = inputs.input_ids.shape[1]

            # Setup generation config
            generation_config = GenerationConfig(
                max_length=input_length + max_length,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                num_beams=num_beams,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id
            )

            # Generate text
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    generation_config=generation_config
                )
            inference_time = time.time() - start_time

            # Decode the generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract response (remove the prompt)
            response = generated_text[len(prompt):]

            # Clean up the response
            response = self._clean_response(response)

            # Update stats
            tokens_generated = outputs.shape[1] - input_length
            self.total_tokens_generated += tokens_generated
            self.total_inference_time += inference_time
            self.inference_count += 1

            # Add to cache if enabled
            if use_cache:
                self.add_to_cache(prompt, config_hash, response)

            # Metadata
            metadata = {
                "tokens_generated": tokens_generated,
                "inference_time": inference_time,
                "source": "model"
            }

            return response, metadata
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}", {"error": str(e)}

    def batch_generate(self, prompts: List[str], configs: List[Dict[str, Any]] = None) -> List[
        Tuple[str, Dict[str, Any]]]:
        """
        Generate text for multiple prompts in batch.

        Args:
            prompts: List of input prompts
            configs: List of generation configs (one per prompt)

        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of generated texts and metadata
        """
        # Ensure model is loaded
        if not self.is_model_loaded():
            self.load_model()

        # Still not loaded? Return errors
        if not self.is_model_loaded():
            return [("Error: Model not loaded", {"error": "Model not loaded"})] * len(prompts)

        # Use default config if not provided
        if configs is None:
            configs = [{}] * len(prompts)

        # Ensure configs match prompts
        if len(configs) != len(prompts):
            configs = configs + [{}] * (len(prompts) - len(configs))

        # Submit tasks to executor
        futures = []
        for prompt, config in zip(prompts, configs):
            futures.append(
                self._executor.submit(
                    self.generate_text,
                    prompt=prompt,
                    **config
                )
            )

        # Collect results
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Error in batch generation: {e}")
                results.append((f"Error: {str(e)}", {"error": str(e)}))

        return results

    def _clean_response(self, text: str) -> str:
        """
        Clean up the generated response.

        Args:
            text: Raw generated text

        Returns:
            str: Cleaned text
        """
        # Remove any trailing incomplete sentences
        import re
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

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.unload_model()
        self._executor.shutdown()