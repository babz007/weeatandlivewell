# Flask Application

A simple Flask web application with a modern design.

## Setup

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5001`

### Docker Setup

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

2. To run in detached mode:
```bash
docker-compose up -d
```

3. To stop the containers:
```bash
docker-compose down
```

## Project Structure

```
.
├── app.py              # Main application file
├── requirements.txt    # Project dependencies
├── static/            # Static files (CSS, JS, images)
│   └── css/
│       └── style.css
├── templates/         # HTML templates
│   └── index.html
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
└── .dockerignore      # Files to exclude from Docker build
``` 