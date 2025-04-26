import os
import json
import yaml
import re
from pathlib import Path
import openai
from jinja2 import Template

class SybilDetector:
    def __init__(self, config_path: str = "../config/config.yaml"):
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / config_path.lstrip("./")
        self.prompt_path = self.project_root / "prompts/is_sybil.txt"
        self.load_config()
        self.load_prompt_template()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key and 'openai_api_key' in self.config:
                openai.api_key = self.config['openai_api_key']
                
            if not openai.api_key:
                print("Warning: No OpenAI API key found in config or environment variables.")
                print("Please set OPENAI_API_KEY environment variable or add 'openai_api_key' to config.yaml")
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {}

    def load_prompt_template(self):
        try:
            with open(self.prompt_path, 'r') as f:
                self.prompt_template = Template(f.read())
        except Exception as e:
            print(f"Error loading prompt template: {e}")
            self.prompt_template = None

    def format_prompt(self, wallet_address: str, features: dict[str]) -> str:
        if not self.prompt_template:
            raise ValueError("Prompt template not loaded")
        
        features_with_address = features.copy()
        features_with_address["wallet_address"] = wallet_address
        
        return self.prompt_template.render(**features_with_address)

    def detect_sybil(self, wallet_address: str, features: dict[str]) -> int:
        if not openai.api_key:
            raise ValueError("OpenAI API key not configured")
        
        prompt = self.format_prompt(wallet_address, features)
        
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a blockchain analyst specializing in sybil detection."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        
        response_text = response.choices[0].message.content.strip()
        
        match = re.search(r'wallet_address:.*?,\s*is_sybil:\s*(\d+)', response_text)
        if match:
            is_sybil = int(match.group(1))
            return is_sybil
        else:
            match = re.search(r'is_sybil[^\d]*(\d+)', response_text)
            if match:
                is_sybil = int(match.group(1))
                return is_sybil
            
            print(f"Warning: Could not parse response for wallet {wallet_address}: {response_text}")
            return 0

    def process_wallets(self, wallets_data: dict[str, dict[str]], output_path: str = None) -> dict[str, int]:
        results = {}
        
        for wallet_address, features in wallets_data.items():
            print(f"Processing wallet: {wallet_address}")
            try:
                is_sybil = self.detect_sybil(wallet_address, features)
                results[wallet_address] = is_sybil
            except Exception as e:
                print(f"Error processing wallet {wallet_address}: {e}")
        
        if output_path:
            self.save_results(results, output_path)
            
        return results
    
    def save_results(self, results: dict[str, int], output_path: str):
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect sybil wallets using OpenAI API')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file with wallet features')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file for results')
    parser.add_argument('--config', '-c', default='config/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    detector = SybilDetector(config_path=args.config)
    
    with open(args.input, 'r') as f:
        wallets_data = json.load(f)
    
    detector.process_wallets(wallets_data, args.output)


if __name__ == "__main__":
    main()
