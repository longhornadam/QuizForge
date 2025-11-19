"""Test physical packager stub."""

import pytest
from engine.rendering.physical.physical_packager import PhysicalPackager
from engine.core.quiz import Quiz


def test_physical_packager_not_implemented():
    """Test that physical packager raises NotImplementedError."""
    packager = PhysicalPackager()
    quiz = Quiz(title="Test", questions=[])
    
    with pytest.raises(NotImplementedError):
        packager.package(quiz)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])