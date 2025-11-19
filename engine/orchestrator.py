"""Main orchestrator for the QuizForge pipeline.

This module coordinates the entire workflow:
1. Scan DropZone for new quiz files
2. Parse TXT → Quiz object
3. Validate and auto-fix Quiz
4. Route to appropriate packagers based on validation status
5. Generate user-facing output (packages or revision prompts)
6. Clean up and archive processed files

The orchestrator is the only component that performs file I/O in user directories.
All other modules work with in-memory data structures.
"""

from pathlib import Path
from typing import List, Optional
import shutil

from .parsing.text_parser import TextOutlineParser
from .validation.validator import QuizValidator, ValidationStatus
from .packagers.packager import package_quiz
from .packaging.folder_creator import create_quiz_folder, write_file
from .feedback.log_generator import generate_log
from .feedback.fail_prompt_generator import generate_fail_prompt


class QuizForgeOrchestrator:
    """Coordinate the quiz processing pipeline."""
    
    def __init__(self, dropzone_path: str, output_path: str):
        """Initialize orchestrator with input/output paths.
        
        Args:
            dropzone_path: Path to DropZone directory (user input)
            output_path: Path to Finished_Exports directory (user output)
        """
        self.dropzone = Path(dropzone_path)
        self.output = Path(output_path)
        self.archive = self.dropzone / "old_quizzes"
        
        # Ensure directories exist
        self.dropzone.mkdir(parents=True, exist_ok=True)
        self.output.mkdir(parents=True, exist_ok=True)
        self.archive.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.parser = TextOutlineParser()
        self.validator = QuizValidator()
    
    def process_all(self) -> None:
        """Scan DropZone and process all .txt files."""
        txt_files = list(self.dropzone.glob("*.txt"))
        
        if not txt_files:
            print("No quiz files found in DropZone.")
            return
        
        print(f"Found {len(txt_files)} quiz file(s) to process...")
        print()
        
        for filepath in txt_files:
            print(f"Processing: {filepath.name}")
            try:
                self.process_file(filepath)
                print(f"  ✓ Success")
            except Exception as e:
                print(f"  ✗ Error: {e}")
            print()
    
    def process_file(self, filepath: Path) -> None:
        """Process a single quiz file through the pipeline.
        
        Args:
            filepath: Path to .txt quiz file
        """
        # Read original text (for fail prompts)
        original_text = filepath.read_text(encoding='utf-8')
        
        # Step 1: Parse
        try:
            quiz = self.parser.parse_file(str(filepath))
        except Exception as e:
            # Parser failed - create fail prompt
            self._handle_parse_failure(filepath, original_text, str(e))
            return
        
        # Step 2a: Calculate point values for quiz (automated)
        try:
            from engine.validation.point_calculator import calculate_points
            from engine.validation.answer_balancer import balance_answers
            from engine.rendering.physical.styles.default_styles import DEFAULT_QUIZ_POINTS
            # Calculate points
            quiz.questions = calculate_points(quiz.questions, total_points=DEFAULT_QUIZ_POINTS)
            # Balance answers (no log path available yet)
            quiz.questions = balance_answers(quiz.questions)
        except Exception:
            # On failure, continue without recalculation/balancing
            pass

        # Step 2b: Validate
        result = self.validator.validate(quiz)
        
        # Step 3: Route based on status
        if result.status == ValidationStatus.FAIL:
            self._handle_validation_failure(filepath, original_text, result)
        else:
            self._handle_validation_success(filepath, result)
    
    def _handle_parse_failure(self, filepath: Path, original_text: str, error: str) -> None:
        """Handle parser failure by creating fail prompt."""
        quiz_name = filepath.stem
        
        # Generate fail prompt
        prompt = generate_fail_prompt(
            original_text=original_text,
            errors=[f"Parse error: {error}"],
            quiz_title=quiz_name
        )
        
        # Write fail prompt to output
        fail_filename = f"{quiz_name}_FAIL_REVISE_WITH_AI.txt"
        fail_path = self.output / fail_filename
        fail_path.write_text(prompt, encoding='utf-8')
        
        print(f"  → Created: {fail_filename}")
        
        # Archive original file
        self._archive_file(filepath)
    
    def _handle_validation_failure(self, filepath: Path, original_text: str, result) -> None:
        """Handle validation failure by creating fail prompt."""
        quiz_name = filepath.stem
        
        # Generate fail prompt
        prompt = generate_fail_prompt(
            original_text=original_text,
            errors=result.errors,
            quiz_title=result.quiz.title
        )
        
        # Write fail prompt to output
        fail_filename = f"{quiz_name}_FAIL_REVISE_WITH_AI.txt"
        fail_path = self.output / fail_filename
        fail_path.write_text(prompt, encoding='utf-8')
        
        print(f"  → Created: {fail_filename}")
        
        # Archive original file
        self._archive_file(filepath)
    
    def _handle_validation_success(self, filepath: Path, result) -> None:
        """Handle validation success by generating packages.""" 
        quiz = result.quiz
        quiz_name = filepath.stem
        
        # Create output folder
        folder = create_quiz_folder(self.output, quiz.title)
        
        # Generate packages (both Canvas and Physical)
        try:
            package_results = package_quiz(quiz, str(folder))
            
            # Report successful outputs to user
            if package_results.get('canvas'):
                canvas = package_results['canvas']
                print(f"  → Created: {folder.name}/{Path(canvas['qti_path']).name}")
            
            if package_results.get('physical'):
                phys = package_results['physical']
                print(f"  → Created: {folder.name}/{Path(phys['quiz_path']).name}")
                print(f"  → Created: {folder.name}/{Path(phys['key_path']).name}")
                print(f"  → Created: {folder.name}/{Path(phys['rationale_path']).name}")
            
            print(f"  → All outputs saved to: {folder.name}")
            
        except Exception as e:
            print(f"  ✗ Packaging failed: {e}")
            # Could create error log here if needed
            return
        
        # Generate success log
        status_label = "PASS" if result.status == ValidationStatus.PASS else "WEAK_PASS"
        log_filename = f"log_{status_label}_FIXED.txt"
        log_content = generate_log(
            fix_log=result.fix_log,
            warnings=result.warnings,
            quiz_title=quiz.title,
            total_points=quiz.total_points(),
            question_count=quiz.question_count()
        )
        write_file(folder, log_filename, log_content.encode('utf-8'))
        print(f"  → Created: {folder.name}/{log_filename}")
        # Log answer distribution if available
        try:
            from engine.validation.answer_balancer import log_distribution_stats
            dist_log = folder / 'answer_distribution.log'
            log_distribution_stats(quiz.questions, str(dist_log))
            print(f"  → Created: {folder.name}/{dist_log.name}")
        except Exception:
            pass
        
        # Archive original file
        self._archive_file(filepath)
    
    def _archive_file(self, filepath: Path) -> None:
        """Move processed file to archive folder."""
        dest = self.archive / filepath.name
        
        # Handle name collision
        if dest.exists():
            counter = 1
            while dest.exists():
                dest = self.archive / f"{filepath.stem}_{counter}{filepath.suffix}"
                counter += 1
        
        shutil.move(str(filepath), str(dest))


def main():
    """Entry point for command-line execution."""
    import sys
    
    # Get project root (where DropZone and Finished_Exports live)
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        # Assume we're in QuizForge/engine/
        project_root = Path(__file__).parent.parent
    
    dropzone = project_root / "DropZone"
    output = project_root / "Finished_Exports"
    
    print("=" * 60)
    print("QuizForge Processing Pipeline")
    print("=" * 60)
    print(f"DropZone: {dropzone}")
    print(f"Output: {output}")
    print("=" * 60)
    print()
    
    orchestrator = QuizForgeOrchestrator(
        dropzone_path=str(dropzone),
        output_path=str(output)
    )
    
    orchestrator.process_all()
    
    print("=" * 60)
    print("Processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
