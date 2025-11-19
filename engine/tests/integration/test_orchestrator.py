"""Integration test for full orchestrator pipeline."""

import tempfile
import shutil
from pathlib import Path
from engine.orchestrator import QuizForgeOrchestrator


def test_full_pipeline():
    """Test complete pipeline with temporary directories."""
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        dropzone = tmpdir / "DropZone"
        output = tmpdir / "Finished_Exports"
        dropzone.mkdir()
        output.mkdir()
        
        # Create a sample quiz file
        sample_quiz = """Title: Integration Test Quiz

---
Type: MC
Prompt: What is 2+2?
Choices:
- [x] 4
- [ ] 3
- [ ] 5
---

Type: TF
Prompt: Python is a programming language.
Answer: true
---
"""
        quiz_file = dropzone / "test_quiz.txt"
        quiz_file.write_text(sample_quiz)
        
        # Run orchestrator
        orchestrator = QuizForgeOrchestrator(
            dropzone_path=str(dropzone),
            output_path=str(output)
        )
        orchestrator.process_all()
        
        # Verify outputs
        # Should have created a quiz folder
        quiz_folders = list(output.glob("*"))
        assert len(quiz_folders) == 1, f"Expected 1 folder, found {len(quiz_folders)}"
        
        quiz_folder = quiz_folders[0]
        
        # Should have .zip file
        zip_files = list(quiz_folder.glob("*.zip"))
        assert len(zip_files) == 1, "Expected Canvas ZIP file"
        
        # Should have log file
        log_files = list(quiz_folder.glob("log_*.txt"))
        assert len(log_files) == 1, "Expected log file"
        
        # Original file should be archived
        assert not quiz_file.exists(), "Original file should be moved"
        archived = dropzone / "old_quizzes" / "test_quiz.txt"
        assert archived.exists(), "File should be archived"
        
        print("✓ Full pipeline test passed")


if __name__ == "__main__":
    test_full_pipeline()