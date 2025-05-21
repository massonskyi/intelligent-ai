"""Test module for the JenkinsPipelineGenerator class.

This module contains tests for the JenkinsPipelineGenerator class, which is
responsible for generating Jenkins pipelines based on project metadata.

Example:
    To run the tests, use the following command:
        $ pytest tests/test_model_handler.py
"""
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from concurrent.futures import Future
from typing import Generator

import pytest

# Add the project root to Python path
PROJECT_ROOT: str = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.model_handler import JenkinsPipelineGenerator


# Mock the transformers library and its dependencies
@pytest.fixture(autouse=True)
def mock_transformers() -> Generator[tuple[MagicMock, MagicMock], None, None]:
    """
    Mock the transformers library and its dependencies.

    This fixture is used to mock the transformers library and its dependencies
    for testing purposes. It patches the T5Tokenizer and T5ForConditionalGeneration
    classes and the requires_backends function.
    """
    with patch('transformers.T5Tokenizer') as mock_tokenizer_class, \
         patch('transformers.T5ForConditionalGeneration') as mock_model_class, \
         patch('transformers.utils.import_utils.requires_backends') as mock_requires_backends:
        # Setup mock tokenizer
        mock_tokenizer: MagicMock = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer
        mock_tokenizer_class.from_pretrained = mock_tokenizer.from_pretrained
        # Setup mock model
        mock_model: MagicMock = MagicMock()
        mock_model.from_pretrained.return_value = mock_model
        mock_model_class.from_pretrained = mock_model.from_pretrained
        # Mock the requires_backends to prevent dependency checks
        mock_requires_backends.return_value = None
        yield mock_tokenizer, mock_model


@pytest.fixture
def model_handler() -> JenkinsPipelineGenerator:
    """
    Fixture for creating a ModelHandler instance.

    This fixture initializes a ModelHandler instance and sets up its executor
    mock to return a proper Future object.
    """
    handler = JenkinsPipelineGenerator()
    # Initialize attributes
    handler._executor = Mock()
    
    # Create a future for mock returns
    future = Future()
    future.set_result(None)  # Set a result so it's considered done
    
    # Configure the executor mock to return a proper Future object
    handler._executor.submit.return_value = future
    
    return handler


@pytest.fixture
def sample_project_config():
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
def sample_pipeline():
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


@pytest.mark.asyncio
async def test_initialize(model_handler, mock_transformers):
    """Test model initialization"""
    mock_tokenizer, mock_model = mock_transformers
    
    await model_handler.initialize()
    
    mock_tokenizer.from_pretrained.assert_called_once()
    mock_model.from_pretrained.assert_called_once()
    assert model_handler.tokenizer is not None
    assert model_handler.model is not None


@pytest.mark.asyncio
async def test_generate_pipeline(model_handler, sample_project_config, mock_transformers):
    """Test pipeline generation"""
    mock_tokenizer, mock_model = mock_transformers
    
    # Setup mock responses
    mock_tokenizer.return_value = {
        "input_ids": Mock(),
        "attention_mask": Mock()
    }
    mock_model.generate.return_value = [[1, 2, 3]]  # Mock tensor output
    mock_tokenizer.decode.return_value = "stage('Build') steps sh 'mvn clean install'"
    
    # Generate pipeline
    result = await model_handler.generate_pipeline(sample_project_config)
    
    # Verify results
    assert isinstance(result, str)
    assert "pipeline {" in result
    assert "agent any" in result
    assert "stages {" in result


@pytest.mark.asyncio
async def test_generate_pipeline_with_callback(model_handler, sample_project_config, mock_transformers):
    """Test pipeline generation with callback"""
    mock_tokenizer, mock_model = mock_transformers
    
    # Setup mock responses
    mock_tokenizer.return_value = {
        "input_ids": Mock(),
        "attention_mask": Mock()
    }
    mock_model.generate.return_value = [[1, 2, 3]]  # Mock tensor output
    mock_tokenizer.decode.return_value = "stage('Build') steps sh 'mvn clean install'"
    
    # Mock the callback
    callback_mock = AsyncMock()
    
    # Generate pipeline with callback
    result = await model_handler.generate_pipeline(sample_project_config, callback_mock)
    
    # Verify results
    assert isinstance(result, str)
    callback_mock.assert_called_once_with(result)


def test_format_jenkinsfile(model_handler, sample_pipeline):
    """Test Jenkins pipeline formatting"""
    # Test with well-formed pipeline
    formatted = model_handler.format_jenkinsfile(sample_pipeline)
    assert "pipeline {" in formatted
    assert "agent any" in formatted
    assert "stages {" in formatted
    
    # Test with malformed pipeline
    malformed = "stage('Build') steps sh 'mvn clean install'"
    formatted = model_handler.format_jenkinsfile(malformed)
    assert "pipeline {" in formatted
    assert "agent any" in formatted
    assert "stages {" in formatted
    assert "stage('Build')" in formatted


@pytest.mark.asyncio
async def test_close(model_handler):
    """Test resource cleanup"""
    mock_model = Mock()
    mock_tokenizer = Mock()
    model_handler.model = mock_model
    model_handler.tokenizer = mock_tokenizer
    
    await model_handler.close()
    
    model_handler._executor.shutdown.assert_called_once_with(wait=True)
    assert model_handler.model is None
    assert model_handler.tokenizer is None


@pytest.mark.asyncio
async def test_generate_pipeline_error_handling(model_handler, sample_project_config, mock_transformers):
    """Test error handling in pipeline generation"""
    mock_tokenizer, mock_model = mock_transformers
    
    # Setup mock responses
    mock_tokenizer.return_value = {
        "input_ids": Mock(),
        "attention_mask": Mock()
    }
    mock_model.generate.side_effect = Exception("Model error")
    
    with pytest.raises(Exception) as exc_info:
        await model_handler.generate_pipeline(sample_project_config)
    
    assert "Model error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_demo_formatter(model_handler, sample_pipeline, mock_transformers):
    """Test the demo formatter with sample pipeline"""
    # Mock format_jenkinsfile to return a known result
    model_handler.format_jenkinsfile = AsyncMock(return_value=sample_pipeline)
    
    # Mock highlight function (since we don't need to test terminal output)
    with patch('src.engine.model_handler.highlight') as mock_highlight:
        mock_highlight.return_value = "highlighted code"
        
        # Test with pipeline text
        result = await model_handler.demo_formatter(sample_pipeline)
        
        # Verify results
        assert result == sample_pipeline
        mock_highlight.assert_called_once()
        model_handler.format_jenkinsfile.assert_called_once_with(sample_pipeline)


@pytest.mark.asyncio
async def test_demo_formatter_with_callback(model_handler, sample_pipeline):
    """Test the demo formatter with callback"""
    # Mock format_jenkinsfile to return a known result
    model_handler.format_jenkinsfile = AsyncMock(return_value=sample_pipeline)
    
    # Mock callback
    callback = Mock()
    
    # Mock highlight function
    with patch('src.engine.model_handler.highlight') as mock_highlight:
        mock_highlight.return_value = "highlighted code"
        
        # Test with pipeline text and callback
        result = await model_handler.demo_formatter(sample_pipeline, callback)
        
        # Verify results
        assert result == sample_pipeline
        callback.assert_called_once_with(sample_pipeline)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 