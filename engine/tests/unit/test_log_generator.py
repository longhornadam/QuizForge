"""Test log generator."""

from engine.feedback.log_generator import generate_log


def test_generate_log_pass():
    """Test log generation for PASS status."""
    fix_log = [
        "Normalized 5 questions to total 100 points",
        "Shuffled choices for 3 questions"
    ]
    warnings = []
    
    log = generate_log(
        fix_log=fix_log,
        warnings=warnings,
        quiz_title="Test Quiz",
        total_points=100.0,
        question_count=5
    )
    
    assert "STATUS: PASS" in log
    assert "Normalized 5 questions" in log
    assert "WARNINGS:" not in log


def test_generate_log_weak_pass():
    """Test log generation for WEAK_PASS status."""
    fix_log = ["Normalized points"]
    warnings = [
        "Longest answer is correct in 60% of MC questions",
        "Answer position 'C' appears 3 times in a row"
    ]
    
    log = generate_log(
        fix_log=fix_log,
        warnings=warnings,
        quiz_title="Test Quiz",
        total_points=100.0,
        question_count=5
    )
    
    assert "STATUS: WEAK PASS" in log
    assert "WARNINGS:" in log
    assert "Longest answer" in log
    assert "Answer position 'C'" in log


if __name__ == "__main__":
    test_generate_log_pass()
    test_generate_log_weak_pass()
    print("✓ Log generator tests passed")