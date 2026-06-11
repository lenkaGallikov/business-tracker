# Define variables
IMAGE_NAME = business-tracker-app
CONTAINER_NAME = tracker_instance
PORT = 8501

.PHONY: update run stop clean

# The default action when you just type 'make'
update: stop clean build run

build:
	@echo "🔨 Building the Docker image..."
	docker build -t $(IMAGE_NAME) .

run:
	@echo "🚀 Launching the container..."
	docker run -d -p $(PORT):$(PORT) -v "$$(pwd)/data:/app/data" --name $(CONTAINER_NAME) $(IMAGE_NAME)
	@echo "✅ App is live at http://localhost:$(PORT)"

stop:
	@echo "🛑 Stopping old container if it exists..."
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true

clean:
	@echo "🧹 Removing old container profile..."
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true