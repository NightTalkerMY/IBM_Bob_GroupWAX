from google import genai
from google.genai import types
import time
import config

class ResilientClient:
    def __init__(self, api_keys, model=config.GEMINI_MODEL_NAME, verbose=True):
        self.keys = [k for k in api_keys if k]
        self.model = model
        self.verbose = verbose
        self.current_key_idx = 0
        
        if not self.keys:
            raise ValueError("No valid API keys provided.")
        self._init_client()

    def _init_client(self):
        self.client = genai.Client(api_key=self.keys[self.current_key_idx])

    def _rotate_key(self, reason):
        prev_idx = self.current_key_idx
        self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
        if self.verbose:
            print(f"[System] Key {prev_idx} unavailable ({reason}). Switching to Key {self.current_key_idx}.")
        self._init_client()

    def chat(self, user_input, history=None, system_instruction=None):
        """
        Now accepts 'history' as an argument for this specific turn.
        """
        if history is None:
            history = []

        attempts = 0
        # Configuration for system instruction
        sys_config = None
        if system_instruction:
            sys_config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7 
            )

        while attempts < len(self.keys):
            try:
                # Create a session using the USER'S specific history
                chat_session = self.client.chats.create(
                    model=self.model,
                    history=history,
                    config=sys_config
                )
                
                response = chat_session.send_message(user_input)
                
                # We return the text AND the new turn data so the Brain can save it
                return response.text

            except Exception as e:
                error_msg = str(e).upper()
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    self._rotate_key("Quota Exhausted")
                    attempts += 1
                elif "503" in error_msg:
                    time.sleep(1)
                    attempts += 1
                else:
                    return f"System Error: {e}"
                    
        return "System Notification: All API keys are currently unavailable."