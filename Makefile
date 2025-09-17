# Makefile for FastAPI backend with Docker and PostgreSQL

# Variables
PROJECT_NAME=myproject
DOCKER_COMPOSE=docker-compose

# Targets
.PHONY: up down build restart logs shell install format test clean purge

# Start the backend and DB services
up:
	$(DOCKER_COMPOSE) up -d

# Stop the services
down:
	$(DOCKER_COMPOSE) down

# Build the Docker images
build:
	$(DOCKER_COMPOSE) build

# Restart the services
restart:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d --build

# Show container logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Open a shell inside the backend container
shell:
	$(DOCKER_COMPOSE) exec backend sh

# Install Python dependencies inside backend container
install:
	$(DOCKER_COMPOSE) exec backend pip install --no-cache-dir -r requirements.txt

# Format code using black
format:
	$(DOCKER_COMPOSE) exec backend black /code/app

# Run tests (pytest must be in requirements.txt)
test:
	$(DOCKER_COMPOSE) exec backend pytest

# Remove all containers (running + stopped) but keep images & volumes
clean:
	docker rm -f $$(docker ps -aq) || true

# Remove everything: containers, images, volumes, networks
purge:
	docker system prune -af --volumes
