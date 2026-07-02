import os
import json

class ExperimentConfig:
    def __init__(self, **kwargs):
        self.workers = int(kwargs.get("workers", 10))
        self.max_depth = int(kwargs.get("max_depth", 3))
        self.branch_factor = int(kwargs.get("branch_factor", 2))
        self.merge_threshold = float(kwargs.get("merge_threshold", 0.6))
        self.score_threshold = float(kwargs.get("score_threshold", 0.4))
        self.compression_ratio = float(kwargs.get("compression_ratio", 0.15))
        self.max_nodes = int(kwargs.get("max_nodes", 500))
        self.batch_expansion = bool(kwargs.get("batch_expansion", True))
        self.max_concurrency = int(kwargs.get("max_concurrency", 2))
        self.generations = int(kwargs.get("generations", 2))
        self.mutation_rate = float(kwargs.get("mutation_rate", 0.2))
        
        # Ollama connection configuration
        self.ollama_host = str(kwargs.get("ollama_host", "http://localhost:11434"))
        self.ollama_model = str(kwargs.get("ollama_model", "tinyllama:latest"))

    def to_dict(self):
        return {
            "workers": self.workers,
            "max_depth": self.max_depth,
            "branch_factor": self.branch_factor,
            "merge_threshold": self.merge_threshold,
            "score_threshold": self.score_threshold,
            "compression_ratio": self.compression_ratio,
            "max_nodes": self.max_nodes,
            "batch_expansion": self.batch_expansion,
            "max_concurrency": self.max_concurrency,
            "generations": self.generations,
            "mutation_rate": self.mutation_rate,
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model
        }

    @classmethod
    def load_from_file(cls, filepath):
        if not os.path.exists(filepath):
            return cls()
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"[config] Warning: Failed to parse {filepath} ({e}), using default config.")
                return cls()

    def save_to_file(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

# Default configuration instance
default_config = ExperimentConfig()
