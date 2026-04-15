# =============================================================================
# models.py — Data Models for Academic Advising System
# CSC 895/898 Culminating Experience Project | SF State University
# =============================================================================
#
# Defines the data structures (dataclasses) used across all agents.
# Every other module imports from here.
#
# Architecture:
#   Student DPR → [Agent 1: Parser] → ProgressReport
#                                          ↓
#                                     [Agent 2: Recommender] → GraduationPathway
#                                          ↓
#                                     [Agent 3: Explainer]   → PathwayExplanation
#                                     [Agent 4: Career Guide] → CareerReport
#
# =============================================================================

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional, List, Dict


# =============================================================================
# ENUMS — Fixed categories used throughout the system
# =============================================================================

class RequirementStatus(Enum):
    COMPLETE = "complete"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"


class Semester(Enum):
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER = "Summer"


class PriorityLevel(Enum):
    """Scheduling urgency — CRITICAL courses block others if delayed."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskSeverity(IntEnum):
    """Higher value = more severe; drives heat-map styling in the UI."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# =============================================================================
# COMPLETED COURSE
# One course a student has already taken (e.g., CSC 210, 3 units, grade A).
# =============================================================================

@dataclass
class CompletedCourse:
    code: str           # e.g., "CSC 210"
    title: str          # e.g., "Introduction to Computer Programming"
    units: float        # Credit units (usually 1.0–5.0)
    grade: str          # Letter grade: "A", "B+", "CR", "W", etc.
    semester: str       # "Fall", "Spring", or "Summer"
    year: int
    satisfies: List[str] = field(default_factory=list)  # Requirement IDs this fulfills

    @property
    def grade_points(self) -> Optional[float]:
        """Converts letter grade to numeric value. Returns None for non-GPA grades (CR, W, etc.)."""
        grade_map = {
            "A": 4.0, "A-": 3.7,
            "B+": 3.3, "B": 3.0, "B-": 2.7,
            "C+": 2.3, "C": 2.0, "C-": 1.7,
            "D+": 1.3, "D": 1.0, "D-": 0.7,
            "F": 0.0,
            "IC": 0.0,   # Incomplete Counted as F
            "WU": 0.0    # Withdrawal Unauthorized
        }
        return grade_map.get(self.grade)

    @property
    def is_passing(self) -> bool:
        """Returns True if the student earned credit for this course."""
        if self.grade in ("CR", "T"):
            return True
        if self.grade in ("W", "NC", "I", "RD"):
            return False
        pts = self.grade_points
        # D- (0.7) is the lowest passing grade at SF State
        return pts is not None and pts >= 0.7


# =============================================================================
# STUDENT PROFILE
# Complete snapshot of a student's academic situation.
# Created by Agent 1 (Parser) after reading a DPR.
# =============================================================================

@dataclass
class StudentProfile:
    student_id: str
    name: str
    program_code: str       # e.g., "CSC_BS", "PSY_BA"
    catalog_year: str       # e.g., "2024-25" — determines which requirements apply
    completed_courses: List[CompletedCourse] = field(default_factory=list)
    in_progress_courses: List[str] = field(default_factory=list)  # Course codes only
    cumulative_gpa: float = 0.0
    major_gpa: float = 0.0
    total_units_completed: float = 0.0
    total_units_required: int = 120
    current_semester: str = "Fall"
    current_year: int = 2025

    @property
    def completed_course_codes(self) -> set:
        """Set of passing course codes — O(1) lookup for requirement matching."""
        return {c.code for c in self.completed_courses if c.is_passing}

    def has_completed(self, course_code: str) -> bool:
        return course_code in self.completed_course_codes

    def has_completed_any(self, course_codes: List[str]) -> bool:
        """True if the student has passed ANY course in the given list."""
        return bool(self.completed_course_codes.intersection(course_codes))

    def calculate_gpa(self, courses: Optional[List[CompletedCourse]] = None) -> float:
        """GPA = sum(grade_points * units) / sum(units). Pass a subset for major GPA."""
        if courses is None:
            courses = self.completed_courses

        total_points = 0.0
        total_units = 0.0

        for c in courses:
            pts = c.grade_points
            if pts is not None:
                total_points += pts * c.units
                total_units += c.units

        if total_units > 0:
            return round(total_points / total_units, 2)
        return 0.0


# =============================================================================
# REQUIREMENT MATCH
# Links one degree requirement to its completion status.
# Think of it as one row in a checklist:
#   [done] CSC 210 - Intro Programming (fulfilled by CSC 210, grade A)
#   [    ] CSC 310 - Algorithms (not started, 3 units)
# =============================================================================

@dataclass
class RequirementMatch:
    req_id: str                 # Unique ID from bulletin_data.py (e.g., "CSC_CORE1")
    req_name: str               # Display name (e.g., "CSC 210 - Intro to Programming")
    category: str               # "Major", "GE", or "University"
    status: RequirementStatus = RequirementStatus.NOT_STARTED
    fulfilled_by: Optional[str] = None   # Course code that satisfied this, or None
    units_needed: float = 3.0
    course_options: List[str] = field(default_factory=list)  # Courses that CAN fulfill this
    notes: str = ""


# =============================================================================
# PROGRESS REPORT
# Agent 1's output and Agent 2's input.
# Answers: "What has the student done, and what is left?"
# =============================================================================

@dataclass
class ProgressReport:
    student: StudentProfile
    requirements: List[RequirementMatch] = field(default_factory=list)

    @property
    def completed(self) -> List[RequirementMatch]:
        return [r for r in self.requirements if r.status == RequirementStatus.COMPLETE]

    @property
    def in_progress(self) -> List[RequirementMatch]:
        return [r for r in self.requirements if r.status == RequirementStatus.IN_PROGRESS]

    @property
    def remaining(self) -> List[RequirementMatch]:
        return [r for r in self.requirements if r.status == RequirementStatus.NOT_STARTED]

    @property
    def percent_complete(self) -> float:
        if not self.requirements:
            return 0.0
        return round(len(self.completed) / len(self.requirements) * 100, 1)

    @property
    def remaining_units(self) -> float:
        return sum(r.units_needed for r in self.remaining)

    def summary(self) -> str:
        return (
            f"Progress: {self.percent_complete}% | "
            f"Complete: {len(self.completed)} | "
            f"In Progress: {len(self.in_progress)} | "
            f"Remaining: {len(self.remaining)} ({self.remaining_units:.0f} units)"
        )


# =============================================================================
# SCHEDULED COURSE
# One course that Agent 2 has placed into a future semester.
# =============================================================================

@dataclass
class ScheduledCourse:
    code: str
    title: str
    units: float
    category: str               # "Major", "GE", or "University"
    priority: PriorityLevel = PriorityLevel.MEDIUM
    prerequisites: List[str] = field(default_factory=list)
    reason: str = ""            # Filled in by Agent 3 (Explainer)


# =============================================================================
# SEMESTER PLAN
# All courses for one future semester (e.g., Fall 2025: CSC 310, CSC 340).
# =============================================================================

@dataclass
class SemesterPlan:
    semester: str       # "Fall", "Spring", or "Summer"
    year: int

    courses: List[ScheduledCourse] = field(default_factory=list)

    @property
    def total_units(self) -> float:
        return sum(c.units for c in self.courses)

    @property
    def label(self) -> str:
        return f"{self.semester} {self.year}"

    def add_course(self, course: ScheduledCourse):
        self.courses.append(course)


# =============================================================================
# GRADUATION PATHWAY
# Complete semester-by-semester plan until graduation.
# Main output of Agent 2 (Recommender).
# =============================================================================

@dataclass
class GraduationPathway:
    student_id: str
    program_code: str
    catalog_year: str
    semesters: List[SemesterPlan] = field(default_factory=list)
    total_remaining_units: float = 0.0
    estimated_graduation: str = ""
    warnings: List[str] = field(default_factory=list)

    @property
    def num_semesters(self) -> int:
        return len(self.semesters)

    def summary(self) -> str:
        lines = [
            f"Graduation Pathway: {self.program_code} ({self.catalog_year})",
            f"Estimated graduation: {self.estimated_graduation}",
            f"Semesters remaining: {self.num_semesters}",
            f"Units remaining: {self.total_remaining_units:.0f}",
            ""
        ]

        for sem in self.semesters:
            lines.append(f"--- {sem.label} ({sem.total_units:.0f} units) ---")
            for c in sem.courses:
                lines.append(f"  {c.code}: {c.title} ({c.units:.0f}u) [{c.priority.value}]")
                if c.reason:
                    lines.append(f"    -> {c.reason}")
            lines.append("")

        if self.warnings:
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)


# =============================================================================
# COURSE EXPLANATION
# Agent 3's explanation for why a specific course was placed in a semester.
# =============================================================================

@dataclass
class CourseExplanation:
    course_code: str
    semester_label: str         # e.g., "Fall 2025"
    reasons: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    trade_offs: str = ""        # What happens if the student delays this course


@dataclass
class RiskFactor:
    message: str
    severity: RiskSeverity = RiskSeverity.MEDIUM


# =============================================================================
# PATHWAY EXPLANATION
# Full transparency report for the entire graduation plan.
# Main output of Agent 3 (Explainer).
# =============================================================================

@dataclass
class PathwayExplanation:
    overall_strategy: str = ""
    course_explanations: List[CourseExplanation] = field(default_factory=list)
    semester_notes: Dict[str, str] = field(default_factory=dict)
    risk_factors: List[RiskFactor] = field(default_factory=list)


# =============================================================================
# CAREER PATH
# One career option recommended by Agent 4.
# =============================================================================

@dataclass
class CareerPath:
    title: str              # e.g., "Software Engineer"
    field: str              # e.g., "Technology"
    description: str        # 1–2 sentence summary
    salary_range: str       # e.g., "$95,000 - $145,000"
    job_outlook: str        # e.g., "High demand", "Growing", "Stable"
    required_skills: List[str] = field(default_factory=list)
    relevant_courses: List[str] = field(default_factory=list)
    match_score: float = 0.0        # 0.0–1.0 based on completed relevant courses
    education_level: str = "Bachelor's"
    certifications: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


# =============================================================================
# CAREER REPORT
# Full output of Agent 4 (Career Guide).
# Ranked career options tailored to the student's coursework.
# =============================================================================

@dataclass
class CareerReport:
    student_id: str
    program_code: str
    career_paths: List[CareerPath] = field(default_factory=list)
    skills_summary: Dict[str, str] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Career Report: {self.program_code}",
            f"Top {len(self.career_paths)} career matches:",
            ""
        ]

        for i, career in enumerate(self.career_paths, 1):
            match_pct = int(career.match_score * 100)
            lines.append(f"  {i}. {career.title} ({career.field})")
            lines.append(f"     Salary: {career.salary_range}")
            lines.append(f"     Outlook: {career.job_outlook}")
            lines.append(f"     Match: {match_pct}%")
            lines.append(f"     Skills: {', '.join(career.required_skills[:5])}")
            lines.append("")

        if self.strengths:
            lines.append("Strengths:")
            for s in self.strengths:
                lines.append(f"  + {s}")
            lines.append("")

        if self.gaps:
            lines.append("Gaps to consider:")
            for g in self.gaps:
                lines.append(f"  - {g}")

        return "\n".join(lines)


# =============================================================================
# TEST — Verify all data structures
# Run: python models.py
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("models.py — Data Structure Test")
    print("=" * 60)

    # --- Test 1: Completed courses ---
    c1 = CompletedCourse("CSC 210", "Intro to Programming", 3.0, "A", "Fall", 2024)
    c2 = CompletedCourse("CSC 220", "Data Structures", 3.0, "B+", "Spring", 2025)
    c3 = CompletedCourse("ENG 114", "Writing Composition", 3.0, "CR", "Fall", 2024)
    c4 = CompletedCourse("MATH 226", "Calculus I", 4.0, "W", "Fall", 2024)

    print(f"\n--- Completed Courses ---")
    print(f"{c1.code}: grade={c1.grade}, points={c1.grade_points}, passing={c1.is_passing}")
    print(f"{c3.code}: grade={c3.grade}, points={c3.grade_points}, passing={c3.is_passing}")
    print(f"{c4.code}: grade={c4.grade}, points={c4.grade_points}, passing={c4.is_passing}")

    # --- Test 2: Student profile ---
    student = StudentProfile(
        student_id="912345678",
        name="Test Student",
        program_code="CSC_BS",
        catalog_year="2024-25",
        completed_courses=[c1, c2, c3, c4],
        current_semester="Fall",
        current_year=2025
    )

    print(f"\n--- Student Profile ---")
    print(f"Name: {student.name}")
    print(f"Completed (passing only): {student.completed_course_codes}")
    print(f"Has CSC 210? {student.has_completed('CSC 210')}")
    print(f"Has CSC 310? {student.has_completed('CSC 310')}")
    print(f"Calculated GPA: {student.calculate_gpa()}")

    # --- Test 3: Progress report ---
    reqs = [
        RequirementMatch("CSC_CORE1", "CSC 210", "Major",
                         RequirementStatus.COMPLETE, "CSC 210"),
        RequirementMatch("CSC_CORE2", "CSC 220", "Major",
                         RequirementStatus.COMPLETE, "CSC 220"),
        RequirementMatch("CSC_CORE3", "CSC 310 - Algorithms", "Major",
                         RequirementStatus.NOT_STARTED, units_needed=3.0),
        RequirementMatch("GE_A2", "Written Communication", "GE",
                         RequirementStatus.COMPLETE, "ENG 114"),
        RequirementMatch("GE_B4", "Quantitative Reasoning", "GE",
                         RequirementStatus.NOT_STARTED, units_needed=3.0),
    ]
    report = ProgressReport(student=student, requirements=reqs)

    print(f"\n--- Progress Report ---")
    print(report.summary())

    # --- Test 4: Graduation pathway ---
    pathway = GraduationPathway(
        student_id="912345678",
        program_code="CSC_BS",
        catalog_year="2024-25",
        semesters=[
            SemesterPlan("Fall", 2025, [
                ScheduledCourse("CSC 310", "Algorithms", 3.0, "Major",
                                PriorityLevel.CRITICAL, ["CSC 220"],
                                "Prerequisite for CSC 413 and CSC 415"),
                ScheduledCourse("MATH 324", "Prob & Stats", 3.0, "Major",
                                PriorityLevel.HIGH, ["MATH 226"]),
            ]),
            SemesterPlan("Spring", 2026, [
                ScheduledCourse("CSC 413", "Software Engineering", 3.0, "Major",
                                PriorityLevel.HIGH, ["CSC 310"]),
            ]),
        ],
        total_remaining_units=42.0,
        estimated_graduation="Spring 2027",
        warnings=["MATH 226 was withdrawn — must retake before MATH 324"]
    )

    print(f"\n--- Graduation Pathway ---")
    print(pathway.summary())

    # --- Test 5: Career report ---
    career1 = CareerPath(
        title="Software Engineer",
        field="Technology",
        description="Design, develop, and maintain software applications and systems",
        salary_range="$95,000 - $145,000",
        job_outlook="High demand",
        required_skills=["Python", "Data Structures", "Algorithms", "System Design"],
        relevant_courses=["CSC 210", "CSC 220", "CSC 310", "CSC 413"],
        match_score=0.50,
        certifications=["AWS Certified Developer"],
        next_steps=["Build a portfolio of 3-5 projects", "Apply for internships"]
    )
    career2 = CareerPath(
        title="Data Analyst",
        field="Technology / Business",
        description="Analyze data sets to identify trends and support business decisions",
        salary_range="$65,000 - $95,000",
        job_outlook="Growing",
        required_skills=["Python", "Statistics", "SQL", "Data Visualization"],
        relevant_courses=["CSC 210", "MATH 324"],
        match_score=0.50,
        next_steps=["Learn SQL and Tableau", "Take a data science elective"]
    )

    career_report = CareerReport(
        student_id="912345678",
        program_code="CSC_BS",
        career_paths=[career1, career2],
        strengths=["Strong programming foundation (CSC 210, CSC 220)"],
        gaps=["No database coursework yet", "Limited math — MATH 226 was withdrawn"]
    )

    print(f"\n--- Career Report ---")
    print(career_report.summary())

    print("\n[ok] All models verified successfully (including Agent 4).")
