"""Create output folder structures for finished quizzes."""

from pathlib import Path
from typing import Optional


def create_quiz_folder(output_dir: Path, quiz_title: str) -> Path:
    """Create folder for quiz outputs.
    
    Args:
        output_dir: Base output directory (Finished_Exports)
        quiz_title: Quiz title (used for folder name)
        
    Returns:
        Path to created folder
    """
    # Sanitize title for folder name
    safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in quiz_title)
    safe_title = safe_title.strip().replace(' ', '_')
    
    folder = output_dir / safe_title
    folder.mkdir(parents=True, exist_ok=True)
    
    return folder


def write_file(folder: Path, filename: str, content: bytes) -> Path:
    """Write bytes to file in folder.
    
    Args:
        folder: Folder path
        filename: File name
        content: File content as bytes
        
    Returns:
        Path to written file
    """
    filepath = folder / filename
    filepath.write_bytes(content)
    return filepath