# debug_torchrun.py
import os
import torch.distributed as dist
import torch

def main():
    dist.init_process_group(
        backend="gloo",  # CPU-friendly backend
        init_method="tcp://127.0.0.1:29500",
        rank=int(os.environ["RANK"]),
        world_size=int(os.environ["WORLD_SIZE"])
    )

    print(f"[Rank {dist.get_rank()}] Hello from PID {os.getpid()}")

    if dist.get_rank() == 0:
        print(f"[Rank 0] Doing the S3 download/upload step...")
    else:
        print(f"[Rank {dist.get_rank()}] Skipping S3 step.")

    dist.destroy_process_group()

if __name__ == "__main__":
    main()
