"""
Module for defining the model used in the Jenkins Pipeline Generator.

This module contains an enumeration of available models that can be used for
generating Jenkins pipelines. The models are defined as enum values with their
corresponding names.

Example:
    To use a specific model, you can import the Model enum and access its values:
        from src.engine.model import Model
        model_name = Model.T5_SMALL.value
        print(f"Using model: {model_name}") 
"""

from enum import Enum
from typing import final

@final
class Model(Enum):
    """
    Enum for available models used in the Jenkins Pipeline Generator.

    This enum defines the different models that can be used for generating
    Jenkins pipelines. Each model has a corresponding name that can be used
    to select the appropriate model for a specific task.

    Args:
        Enum (str): The name of the model.
    """
    T5_SMALL: str = "t5-small"
    CODE_T5_SMALL: str = "codet5p_finetuned"
