"""Test module for the FastAPI server endpoints.

This module contains tests for the FastAPI server endpoints, including
generate-pipeline and demo-format routes.

Example:
    To run the tests, use the following command:
        $ pytest tests/test_api.py
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Add the project root to Python path
PROJECT_ROOT: str = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.server.server import app


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


@pytest.fixture
def sample_pipeline_response():
    """Returns a sample pipeline response."""
    return """pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean install'
            }
        }
        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
    }
}"""


@patch("src.engine.model_handler.JenkinsPipelineGenerator.generate_pipeline")
def test_generate_pipeline_endpoint(mock_generate, client, sample_project_config, sample_pipeline_response):
    """Test the generate-pipeline endpoint with a valid request."""
    # Configure the mock to return a sample pipeline
    mock_generate.return_value = sample_pipeline_response

    # Make a request to the endpoint
    response = client.post(
        "/generate-pipeline",
        json={"input_data": sample_project_config}
    )
    
    # Check the response
    assert response.status_code == 200
    assert "pipeline" in response.json()
    assert response.json()["pipeline"] == sample_pipeline_response
    
    # Verify the mock was called with the correct arguments
    mock_generate.assert_called_once_with(sample_project_config)


@patch("src.engine.model_handler.JenkinsPipelineGenerator.generate_pipeline")
def test_generate_pipeline_error(mock_generate, client, sample_project_config):
    """Test the generate-pipeline endpoint with an error response."""
    # Configure the mock to raise an exception
    mock_generate.side_effect = Exception("Model error")

    # Make a request to the endpoint
    response = client.post(
        "/generate-pipeline",
        json={"input_data": sample_project_config}
    )
    
    # Check the response
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Model error" in response.json()["detail"]


@patch("src.engine.model_handler.JenkinsPipelineGenerator.demo_formatter")
def test_demo_format_endpoint(mock_formatter, client, sample_project_config, sample_pipeline_response):
    """Test the demo-format endpoint with a valid request."""
    # Configure the mock to return a sample formatted pipeline
    mock_formatter.return_value = sample_pipeline_response

    # Make a request to the endpoint
    response = client.post(
        "/demo-format",
        json={"input_data": sample_project_config}
    )
    
    # Check the response
    assert response.status_code == 200
    assert "formatted_pipeline" in response.json()
    assert response.json()["formatted_pipeline"] == sample_pipeline_response
    
    # Verify the mock was called with the correct arguments
    mock_formatter.assert_called_once_with(json.dumps(sample_project_config))


@patch("src.engine.model_handler.JenkinsPipelineGenerator.demo_formatter")
def test_demo_format_error(mock_formatter, client, sample_project_config):
    """Test the demo-format endpoint with an error response."""
    # Configure the mock to raise an exception
    mock_formatter.side_effect = Exception("Formatter error")

    # Make a request to the endpoint
    response = client.post(
        "/demo-format",
        json={"input_data": sample_project_config}
    )
    
    # Check the response
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Formatter error" in response.json()["detail"]


def test_invalid_request_format(client):
    """Test the endpoints with invalid request formats."""
    # Test with an empty request
    response = client.post("/generate-pipeline", json={})
    assert response.status_code == 422
    
    # Test with missing required field
    response = client.post("/generate-pipeline", json={"wrong_field": {}})
    assert response.status_code == 422
    
    # Test with invalid JSON
    response = client.post("/generate-pipeline", data="not a json")
    assert response.status_code == 422 