import time
import os
import psutil
import json

class EngineLogger:
    def __init__(self):
        self.nodes_generated = 0
        self.nodes_merged = 0
        self.nodes_deleted = 0
        self.process = psutil.Process(os.getpid())
        self.cpu_start = 0.0
        self.mem_start = 0.0
        self.reset_metrics()

    def reset_metrics(self):
        self.nodes_generated = 0
        self.nodes_merged = 0
        self.nodes_deleted = 0
        self.cpu_start = self._sample_cpu()
        self.mem_start = self._sample_mem()

    def _sample_cpu(self) -> float:
        # Sample global CPU usage or current process CPU usage
        try:
            return psutil.cpu_percent(interval=None)
        except Exception:
            return 0.0

    def _sample_mem(self) -> float:
        # Sample resident set size in MB
        try:
            return self.process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def increment_nodes_generated(self):
        self.nodes_generated += 1

    def increment_nodes_merged(self):
        self.nodes_merged += 1

    def increment_nodes_deleted(self):
        self.nodes_deleted += 1

    def log_info(self, msg: str):
        print(f"[INFO] {msg}", flush=True)

    def log_error(self, msg: str):
        print(f"[ERROR] {msg}", flush=True)

    def compile_stats(self, start_time: float, phase_times: dict, raw_node_count: int, consolidated_node_count: int, compressed_node_count: int) -> dict:
        duration = time.time() - start_time
        cpu_end = self._sample_cpu()
        mem_end = self._sample_mem()
        
        # Calculate rates and densities
        dup_ratio = 0.0
        if raw_node_count > 0:
            dup_ratio = round(self.nodes_merged / raw_node_count, 3)
            
        compression_ratio = 0.0
        if consolidated_node_count > 0:
            compression_ratio = round(compressed_node_count / consolidated_node_count, 3)
            
        return {
            "execution_time_s": round(duration, 2),
            "phase_times_s": {k: round(v, 2) for k, v in phase_times.items()},
            "nodes": {
                "generated": self.nodes_generated,
                "merged": self.nodes_merged,
                "deleted": self.nodes_deleted,
                "raw_total": raw_node_count,
                "consolidated_total": consolidated_node_count,
                "compressed_total": compressed_node_count
            },
            "metrics": {
                "duplicate_ratio": dup_ratio,
                "compression_ratio": compression_ratio,
                "cpu_start_pct": self.cpu_start,
                "cpu_end_pct": cpu_end,
                "cpu_diff_pct": round(max(0.0, cpu_end - self.cpu_start), 2),
                "memory_start_mb": round(self.mem_start, 2),
                "memory_end_mb": round(mem_end, 2),
                "memory_diff_mb": round(max(0.0, mem_end - self.mem_start), 2)
            }
        }

engine_logger = EngineLogger()
