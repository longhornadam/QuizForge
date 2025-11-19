"""Physical quiz DOCX packager.

Converts validated Quiz objects into printable DOCX files.
Generates student quiz + answer key.
Performs NO validation - trusts input is perfect.

TODO: Full implementation pending.
"""

from typing import Tuple
from ...core.quiz import Quiz


class PhysicalPackager:
    """Generate printable DOCX files."""
    
    def package(self, quiz: Quiz) -> Tuple[bytes, bytes]:
        """Create student quiz and answer key DOCX files.
        
        Args:
            quiz: Validated Quiz object
            
        Returns:
            Tuple of (quiz_docx_bytes, key_docx_bytes)
        
        Raises:
            NotImplementedError: Full implementation pending
        """
        raise NotImplementedError(
            "Physical quiz rendering not yet implemented. "
            "Use Canvas packager for now."
        )
