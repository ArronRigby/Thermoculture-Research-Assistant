import os
import pytest
from pydantic import ValidationError
from app.core.config import Settings

def test_production_secret_key_validation():
    # Keep track of original environment variable state
    original_env = os.environ.get("THERMOCULTURE_ENV")
    
    try:
        # 1. Dev/default behavior should not raise even with placeholder key
        os.environ["THERMOCULTURE_ENV"] = "development"
        settings = Settings(SECRET_KEY="change-me-in-production-use-a-long-random-string")
        assert settings.SECRET_KEY == "change-me-in-production-use-a-long-random-string"
        
        # 2. Production behavior with custom secure key should succeed
        os.environ["THERMOCULTURE_ENV"] = "production"
        settings = Settings(SECRET_KEY="custom-secure-key-1234567890")
        assert settings.SECRET_KEY == "custom-secure-key-1234567890"

        # 3. Production behavior with placeholder keys should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Settings(SECRET_KEY="change-me-in-production-use-a-long-random-string")
        assert "SECRET_KEY cannot be a placeholder value in production environment" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            Settings(SECRET_KEY="change-this-to-a-random-secret-key")
        assert "SECRET_KEY cannot be a placeholder value in production environment" in str(exc_info.value)

    finally:
        # Clean up and restore original environment
        if original_env is not None:
            os.environ["THERMOCULTURE_ENV"] = original_env
        else:
            os.environ.pop("THERMOCULTURE_ENV", None)
