# Repository Guidelines

## Project Structure & Module Organization
This repository implements a digital twinning concept for deficiency detection using machine learning.
- **`app.py`**: The core Flask application serving both the API and the frontend. It handles model loading, prediction logic, and integrates with the Google Gemini API for natural language explanations.
- **`ML_models/`**: Contains `models.py`, which is used for training and testing the Random Forest classifier.
- **`datasets/`**: Stores the primary dataset (`vitamin_deficiency_disease_dataset_20260123.csv`) used for model training and inference.
- **`html_files/`**: Contains static HTML assets like `home.html`, served directly by Flask as the web interface.
- **`env_files/`**: Holds environment configuration templates and local settings.

## Build, Test, and Development Commands
The project is a Python-based Flask application.
- **Install dependencies**: `pip install -r requirements.txt`
- **Run the application**: `python app.py`
- **Train/Test the model**: `python ML_models/models.py`

## Coding Style & Naming Conventions
- Follow standard Python (PEP 8) conventions.
- Environment variables should be managed via `.env` or files in `env_files/`.
- Use `LabelEncoder` for categorical feature encoding as established in `app.py`.

## Testing Guidelines
There is currently no automated test suite. Manual verification is performed by running `app.py` and testing the `/predict` and `/explain` endpoints.

## Commit & Pull Request Guidelines
Commit messages should be descriptive of the features or fixes introduced (e.g., "Initial Flask app setup with prediction and explanation routes").
