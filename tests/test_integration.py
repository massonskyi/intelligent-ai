"""Integration test module for Jenkins Pipeline Generator.

This module contains integration tests that test the complete flow from
API request to model pipeline generation and formatting.

Example:
    To run the tests, use the following command:
        $ pytest tests/test_integration.py
"""
import json
import sys
from pathlib import Path
import asyncio
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Add the project root to Python path
PROJECT_ROOT: str = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.server.server import app, generator


@pytest.fixture(autouse=True)
def mock_model_dependencies():
    """Mock model dependencies for testing."""
    with patch.object(T5ForConditionalGeneration, 'from_pretrained') as mock_model, \
            patch.object(T5Tokenizer, 'from_pretrained') as mock_tokenizer, \
            patch.object(T5ForConditionalGeneration, 'generate') as mock_generate, \
            patch.object(T5Tokenizer, 'decode') as mock_decode, \
            patch.object(T5Tokenizer, '__call__') as mock_tokenizer_call:
        
        # Configure mock responses
        mock_model.return_value = MagicMock()
        mock_tokenizer.return_value = MagicMock()
        mock_generate.return_value = [[1, 2, 3]]  # Mock tensor output
        mock_decode.return_value = "stage('Build') steps sh 'mvn clean install'"
        mock_tokenizer_call.return_value = {
            "input_ids": MagicMock(),
            "attention_mask": MagicMock()
        }
        
        yield


@pytest.fixture
def client():
    """Returns a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_project_config():
    """Returns a sample project configuration."""
    return {
        "project": {
            "type": "java",
            "build_tool": "maven",
            "test_frameworks": ["junit5"],
            "dockerfile_present": True,
            "files": ["pom.xml", "src/main/java/App.java"],
            "dependencies": ["spring-boot"],
            "scripts": {"build": "mvn clean install"}
        }
    }


@pytest.mark.asyncio
async def test_initialize_model():
    """Test model initialization."""
    # Reset model and tokenizer
    generator.model = None
    generator.tokenizer = None
    
    # Initialize model
    await generator.initialize()
    
    # Check model and tokenizer are initialized
    assert generator.model is not None
    assert generator.tokenizer is not None


def test_generate_pipeline_integration(client, sample_project_config):
    """Test the complete integration from API to model."""
    # Initialize model before test
    asyncio.run(generator.initialize())
    
    # Make a request to the endpoint
    response = client.post(
        "/generate-pipeline",
        json={"input_data": sample_project_config}
    )
    
    # Check the response
    assert response.status_code == 200
    assert "pipeline" in response.json()
    
    # Check that response contains formatted Jenkins pipeline
    pipeline = response.json()["pipeline"]
    assert "pipeline {" in pipeline
    assert "agent any" in pipeline
    assert "stages {" in pipeline
    assert "stage('Build')" in pipeline


def test_demo_format_integration(client, sample_project_config):
    """Test the demo-format endpoint with a valid request."""
    # Initialize model before test
    asyncio.run(generator.initialize())
    
    # Make a request to the endpoint
    response = client.post(
        "/demo-format",
        json={"input_data": sample_project_config}
    )
    
    # Check the response
    assert response.status_code == 200
    assert "formatted_pipeline" in response.json()
    
    # Check that response contains formatted Jenkins pipeline
    formatted = response.json()["formatted_pipeline"]
    assert "pipeline {" in formatted
    assert "agent any" in formatted
    assert "stages {" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 