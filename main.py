# =============================================================================
# main.py — System orchestrator (CSC 895/898, SF State)
# =============================================================================
#
# Runs the four advising agents in order and prints a combined report.
#
# Usage:
#   python main.py                  (sample CS student data)
#   python main.py path/to/dpr.pdf  (parse a DPR PDF)
#
# Data flow:
#   Student DPR
#       ↓
#   Agent 1 (Parser) → ProgressReport
#       ↓                    ↓
#   Agent 2 (Recommender)   Agent 4 (Career Guide)
#       ↓                    ↓
#   GraduationPathway       CareerReport
#       ↓
#   Agent 3 (Explainer)
#       ↓
#   PathwayExplanation
#       ↓
#   Combined Report → Student
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

import sys
import os

from bulletin_data import BulletinDatabase
from dpr_parser import DPRParser, SAMPLE_STUDENT_CSC
from recommender import PathwayRecommender
from explainer import PathwayExplainer
from career_guide import CareerGuide


# =============================================================================
# ORCHESTRATOR FUNCTION
# =============================================================================

def run_advising_pipeline(student_data=None, pdf_path=None):
    """Run the full pipeline. Pass ``pdf_path`` and/or ``student_data``; PDF wins if both are set."""

    print("=" * 65)
    print("  GatorGrad: AI-Powered Degree Advising")
    print("  Multi-Agent Pipeline")
    print("=" * 65)

    db = BulletinDatabase()
    parser = DPRParser(db)
    recommender = PathwayRecommender(db)
    # Explainer shares the recommender's prerequisite graph for consistent reasoning.
    explainer = PathwayExplainer(db, recommender.prereq_map)
    guide = CareerGuide()

    # =========================================================================
    # AGENT 1: Parse student data
    # =========================================================================
    print("\n[1/4] Agent 1: DPR Parser")
    print("-" * 40)

    if pdf_path:
        print(f"  Parsing PDF: {pdf_path}")
        progress = parser.parse_pdf(pdf_path)
    elif student_data:
        print("  Parsing from provided data...")
        progress = parser.parse_dict(student_data)
    else:
        print("  No input provided — using sample CS student.")
        progress = parser.parse_dict(SAMPLE_STUDENT_CSC)

    student = progress.student
    print(f"  Student ID: {student.student_id}")
    print(f"  Program: {student.program_code} ({student.catalog_year})")
    print(f"  GPA: {student.cumulative_gpa:.2f} (Major: {student.major_gpa:.2f})")
    print(f"  Units: {student.total_units_completed:.0f} completed")
    print(f"  {progress.summary()}")

    # =========================================================================
    # AGENT 2: Generate graduation pathway
    # =========================================================================
    print("\n[2/4] Agent 2: Pathway Recommender")
    print("-" * 40)

    pathway = recommender.generate_pathway(progress)

    print(f"  Estimated graduation: {pathway.estimated_graduation}")
    print(f"  Semesters remaining: {len(pathway.semesters)}")
    print(f"  Units remaining: {pathway.total_remaining_units:.0f}")

    if pathway.warnings:
        print(f"  Warnings: {len(pathway.warnings)}")
        for w in pathway.warnings:
            print(f"    ! {w}")

    # =========================================================================
    # AGENT 3: Explain the pathway
    # =========================================================================
    print("\n[3/4] Agent 3: Pathway Explainer (XAI)")
    print("-" * 40)

    explanation = explainer.explain(pathway, progress)

    print(f"  Strategy: {explanation.overall_strategy[:100]}...")
    print(f"  Course explanations: {len(explanation.course_explanations)}")
    print(f"  Risk factors: {len(explanation.risk_factors)}")

    # =========================================================================
    # AGENT 4: Career guidance
    # =========================================================================
    print("\n[4/4] Agent 4: Career Guide")
    print("-" * 40)

    career_report = guide.generate_report(progress)

    print(f"  Career matches: {len(career_report.career_paths)}")
    for i, career in enumerate(career_report.career_paths[:3], 1):
        match_pct = int(career.match_score * 100)
        print(f"    {i}. {career.title} ({match_pct}% match) — {career.salary_range}")

    # =========================================================================
    # COMBINED REPORT
    # =========================================================================
    print("\n" + "=" * 65)
    print("  COMPLETE ADVISING REPORT")
    print("=" * 65)

    # --- Section 1: Student Overview ---
    print(f"\n{'─' * 65}")
    print("  STUDENT OVERVIEW")
    print(f"{'─' * 65}")
    print(f"  ID: {student.student_id}")
    print(f"  Program: {student.program_code} ({student.catalog_year})")
    print(f"  Cumulative GPA: {student.cumulative_gpa:.2f}")
    print(f"  Major GPA: {student.major_gpa:.2f}")
    print(f"  Units Completed: {student.total_units_completed:.0f} / 120")
    print(f"  Requirements Completed: {len(progress.completed)} / "
          f"{len(progress.completed) + len(progress.in_progress) + len(progress.remaining)}")

    # --- Section 2: Graduation Pathway ---
    print(f"\n{'─' * 65}")
    print("  GRADUATION PATHWAY")
    print(f"{'─' * 65}")
    print(f"  Estimated Graduation: {pathway.estimated_graduation}")
    print(f"  Semesters Remaining: {len(pathway.semesters)}")
    print()

    for semester in pathway.semesters:
        print(f"  {semester.label} ({semester.total_units:.0f} units)")
        for course in semester.courses:
            priority_tag = course.priority.value.upper()
            print(f"    [{priority_tag:8}] {course.code} — {course.title} ({course.units:.0f}u)")
        print()

    # --- Section 3: Explanations (top courses) ---
    print(f"{'─' * 65}")
    print("  WHY THESE COURSES? (XAI Transparency)")
    print(f"{'─' * 65}")

    for ce in explanation.course_explanations[:6]:
        print(f"\n  {ce.course_code} ({ce.semester_label})")
        for reason in ce.reasons:
            print(f"    → {reason}")
        if ce.trade_offs:
            print(f"    ⇄ {ce.trade_offs}")

    # --- Section 4: Semester Notes ---
    if explanation.semester_notes:
        print(f"\n{'─' * 65}")
        print("  SEMESTER NOTES")
        print(f"{'─' * 65}")
        for label, note in explanation.semester_notes.items():
            print(f"  {label}: {note}")

    # --- Section 5: Risk Factors ---
    if explanation.risk_factors:
        print(f"\n{'─' * 65}")
        print("  RISK FACTORS")
        print(f"{'─' * 65}")
        for risk in explanation.risk_factors:
            print(f"  ⚠ [{risk.severity.name}] {risk.message}")

    # --- Section 6: Career Paths ---
    print(f"\n{'─' * 65}")
    print("  CAREER PATHS")
    print(f"{'─' * 65}")
    print(career_report.summary())

    # --- Section 7: Skills ---
    if career_report.skills_summary:
        print(f"\n{'─' * 65}")
        print("  SKILLS SUMMARY")
        print(f"{'─' * 65}")
        for skill, level in career_report.skills_summary.items():
            print(f"  {skill}: {level}")

    print(f"\n{'=' * 65}")
    print("  Report complete. See a human advisor to finalize your plan.")
    print(f"{'=' * 65}")

    return progress, pathway, explanation, career_report


# =============================================================================
# COMMAND-LINE ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]

        if os.path.exists(pdf_file):
            print(f"Loading DPR from: {pdf_file}")
            run_advising_pipeline(pdf_path=pdf_file)
        else:
            print(f"Error: File not found: {pdf_file}")
            print("Usage: python main.py [path/to/dpr.pdf]")
            sys.exit(1)
    else:
        print("No PDF provided — running with sample CS student data.")
        print("Usage: python main.py [path/to/dpr.pdf]\n")
        run_advising_pipeline()
