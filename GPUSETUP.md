# LLMDegeneration Experiments GPU Setup

## Getting Started
Assuming you're on a fresh install of Ubuntu 24.04

### Clean up first
```
sudo rm -f /etc/apt/sources.list.d/docker.list
sudo rm -f /etc/apt/keyrings/docker.gpg
```

### Install prerequisites
```
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

### Add Docker’s official GPG key
```
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

### Add the Docker repo (using 'jammy' for compatibility)
```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Update package index
```
sudo apt update
```

### Install Docker
```
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Test It
```
sudo docker run hello-world
```

### Add your user to the docker group
```
sudo usermod -aG docker $USER
newgrp docker
```
After this step, you should be able to run docker containers without sudo!

## Using GPUs with the Docker Container
Please run this:
### Download NVIDIA Container Repo
```
sudo apt-get update
sudo apt-get install -y curl gnupg ca-certificates

# Add the NVIDIA Docker GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Add the NVIDIA Docker repo
curl -s -L https://nvidia.github.io/libnvidia-container/ubuntu22.04/libnvidia-container.list | \
  sed 's#deb #deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] #' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install the toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### Install the Runtime
```
sudo apt-get install -y nvidia-container-runtime
```

### Manual install: Edit Docker Daemon config
```
sudo nano /etc/docker/daemon.json
```

#### Add this
```
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```

### Restart Docker
```
sudo systemctl restart docker
```

### Verify
```
docker info | grep -i runtime
```
You should see something like the following: 
```
 Runtimes: io.containerd.runc.v2 nvidia runc
 Default Runtime: nvidia
```

### Test GPU Access in Docker
```
sudo ./dev.sh
```

## Run LoRa Training
From within the dev docker (either pull with `sudo ./pull.sh` or get into it with `sudo ./dev.sh`), run the following: 
```
python3 train.py
```

### Verify output
```
python3 inference.py
```

You'll see that GrugLLM got fine tuned and is now spewing some strange things:
```
=== Output ===
### Prompt:
How do I train a neural network?

### Response:
1. Find the value of the algorithm in a data-driven machine learning algorithm
2. Write a good blog post about how to use data in a real-world scenario.
3. Discover the best way to use a neural network to solve a problem.
4. Learn about the most common mistakes in data science.
5. Find a way to take a photo of a plant with a camera.
6. Find a way to get a new device to work.
7.
```
