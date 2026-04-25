# =============================================================================
# explainer.py — Pathway Explainer (Agent 3 / XAI)
# CSC 895/898 Culminating Experience | SF State University
# =============================================================================
#
# Produces PathwayExplanation from Agent 2’s GraduationPathway and Agent 1’s
# ProgressReport: per-course rationale, alternatives, trade-offs, semester
# notes, and plan-level risks for transparency in the UI.
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from typing import List, Dict, Set

from models import (
    GraduationPathway,
    ProgressReport,
    ScheduledCourse,
    SemesterPlan,
    CourseExplanation,
    PathwayExplanation,
    PriorityLevel,
    RiskFactor,
    RiskSeverity,
)

from bulletin_data import (
    BulletinDatabase,
    DegreeProgram,
)

from recommender import CS_PROGRAMMING_INTRO


# =============================================================================
# EXPLAINER CLASS — Agent 3
# =============================================================================

class PathwayExplainer:
    """Attaches explanations to each scheduled course and summarizes plan risks."""

    def __init__(self, bulletin_db: BulletinDatabase, prereq_map: Dict[str, List[str]]):
        self.db = bulletin_db
        self.prereq_map = prereq_map
        # course_code → courses that require this course (unlock / delay analysis)
        self.reverse_prereq_map = self._build_reverse_map()

    # =========================================================================
    # MAIN ENTRY POINT — Call this to run Agent 3
    # =========================================================================

    def explain(
        self, pathway: GraduationPathway, progress: ProgressReport
    ) -> PathwayExplanation:
        strategy = self._describe_strategy(pathway, progress)

        course_explanations = []
        for semester in pathway.semesters:
            for course in semester.courses:
                explanation = self._explain_course(course, semester, pathway, progress)
                course_explanations.append(explanation)

        semester_notes = self._generate_semester_notes(pathway)

        risks = self._identify_risks(pathway, progress)

        return PathwayExplanation(
            overall_strategy=strategy,
            course_explanations=course_explanations,
            semester_notes=semester_notes,
            risk_factors=risks
        )

    # =========================================================================
    # STEP 1: OVERALL STRATEGY DESCRIPTION
    # =========================================================================

    def _describe_strategy(self, pathway: GraduationPathway, progress: ProgressReport) -> str:
        student = progress.student
        num_semesters = len(pathway.semesters)
        num_remaining = len(progress.remaining)
        units_remaining = pathway.total_remaining_units

        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for sem in pathway.semesters:
            for course in sem.courses:
                if course.priority == PriorityLevel.CRITICAL:
                    critical_count += 1
                elif course.priority == PriorityLevel.HIGH:
                    high_count += 1
                elif course.priority == PriorityLevel.MEDIUM:
                    medium_count += 1
                else:
                    low_count += 1

        parts = []

        parts.append(
            f"Plan for {student.program_code} ({student.catalog_year}): "
            f"{num_remaining} requirements remaining ({units_remaining:.0f} units) "
            f"across {num_semesters} semesters."
        )

        if critical_count > 0:
            parts.append(
                f"The plan prioritizes {critical_count} critical prerequisite "
                f"course(s) in the earliest semesters to unblock dependent courses."
            )

        if high_count > 0:
            parts.append(
                f"{high_count} core major requirement(s) are scheduled next, "
                f"followed by {medium_count} GE/elective and {low_count} university requirement(s)."
            )

        parts.append(f"Estimated graduation: {pathway.estimated_graduation}.")

        return " ".join(parts)

    # =========================================================================
    # STEP 2: PER-COURSE EXPLANATION
    # =========================================================================

    def _explain_course(
        self,
        course: ScheduledCourse,
        semester: SemesterPlan,
        pathway: GraduationPathway,
        progress: ProgressReport
    ) -> CourseExplanation:
        reasons = []

        alternatives = []

        trade_offs = ""

        prereqs = self.prereq_map.get(course.code, [])
        if prereqs:
            display = [
                "CSC 210 or both CSC 101 and CSC 215" if p == CS_PROGRAMMING_INTRO else p
                for p in prereqs
            ]
            prereq_str = ", ".join(display)
            reasons.append(
                f"Requires {prereq_str} as prerequisite(s), "
                f"which will be completed before {semester.label}."
            )
            if course.code == "CSC 413":
                reasons.append("CSC 413 requires grades of C or better in those prerequisites.")

        unlocks = self.reverse_prereq_map.get(course.code, [])
        if unlocks:
            scheduled_codes = set()
            for sem in pathway.semesters:
                for c in sem.courses:
                    scheduled_codes.add(c.code)

            # Only mention dependents that appear in this pathway (not satisfied elsewhere).
            relevant_unlocks = [u for u in unlocks if u in scheduled_codes]

            if relevant_unlocks:
                unlock_str = ", ".join(relevant_unlocks)
                reasons.append(
                    f"Prerequisite for {unlock_str}. "
                    f"Must be completed before those courses can be taken."
                )

        if course.priority == PriorityLevel.CRITICAL:
            reasons.append(
                "Marked CRITICAL: this is a bottleneck course. "
                "Delaying it cascades delays to all dependent courses."
            )
        elif course.priority == PriorityLevel.HIGH:
            reasons.append(
                "Core major requirement — needed for degree completion."
            )
        elif course.priority == PriorityLevel.MEDIUM:
            reasons.append(
                "GE or elective requirement — flexible but required for graduation."
            )
        elif course.priority == PriorityLevel.LOW:
            reasons.append(
                "University requirement — can be taken in any available semester."
            )

        if course.category == "Major":
            reasons.append(
                "Required by your major program. Cannot be substituted by UAC advisor, can contact major advisor and dept if needed."
            )
        elif course.category == "GE":
            reasons.append(
                "General Education requirement. "
                "Multiple course options may be available."
            )

        if not reasons:
            reasons.append(
                f"Scheduled in {semester.label} based on availability and unit balancing."
            )

        for req in progress.remaining:
            if req.course_options and course.code in req.course_options:
                other_options = [c for c in req.course_options if c != course.code]
                if other_options:
                    alt_str = ", ".join(other_options[:5])
                    alternatives.append(
                        f"Could also be fulfilled by: {alt_str}"
                    )
                break

        if course.category == "GE":
            alternatives.append(
                "Check the class schedule for other courses that satisfy this GE area."
            )

        if course.priority == PriorityLevel.CRITICAL:
            dependent_count = len(unlocks)
            trade_offs = (
                f"Delaying this course by one semester would push back "
                f"{dependent_count} dependent course(s) and likely extend "
                f"your graduation date."
            )
        elif course.priority == PriorityLevel.HIGH:
            trade_offs = (
                "This course is required for your degree. "
                "Delaying it will not affect prerequisites but may extend graduation."
            )
        elif course.priority in (PriorityLevel.MEDIUM, PriorityLevel.LOW):
            trade_offs = (
                "This requirement is flexible. You could move it to a different "
                "semester without affecting your prerequisite chain."
            )

        return CourseExplanation(
            course_code=course.code,
            semester_label=semester.label,
            reasons=reasons,
            alternatives=alternatives,
            trade_offs=trade_offs
        )

    # =========================================================================
    # STEP 3: SEMESTER NOTES
    # =========================================================================

    def _generate_semester_notes(self, pathway: GraduationPathway) -> Dict[str, str]:
        notes = {}

        for semester in pathway.semesters:
            sem_notes = []

            major_count = sum(1 for c in semester.courses if c.category == "Major")
            ge_count = sum(1 for c in semester.courses if c.category == "GE")
            critical_count = sum(1 for c in semester.courses if c.priority == PriorityLevel.CRITICAL)

            if semester.total_units >= 18:
                sem_notes.append(
                    f"Heavy load ({semester.total_units:.0f} units). "
                    f"Budget extra study time."
                )
            elif semester.total_units <= 12:
                sem_notes.append(
                    f"Lighter load ({semester.total_units:.0f} units). "
                    f"Good time for internships or extracurriculars."
                )

            if major_count >= 4:
                sem_notes.append(
                    f"Major-heavy semester ({major_count} major courses). "
                    f"Expect significant workload."
                )

            if critical_count >= 2:
                sem_notes.append(
                    f"{critical_count} critical courses this semester. "
                    f"Do not drop any — they block future courses."
                )

            if ge_count >= 4:
                sem_notes.append(
                    f"GE-focused semester ({ge_count} GE courses). "
                    f"Workload should be manageable."
                )

            if semester.semester == "Summer":
                sem_notes.append(
                    "Summer session — shorter term, more intense pacing."
                )

            if sem_notes:
                notes[semester.label] = " ".join(sem_notes)

        return notes

    # =========================================================================
    # STEP 4: RISK FACTORS
    # =========================================================================

    def _identify_risks(
        self, pathway: GraduationPathway, progress: ProgressReport
    ) -> List[RiskFactor]:
        # Severity drives UI presentation (e.g. heat-map ordering).
        risks: List[RiskFactor] = []
        student = progress.student

        for sem in pathway.semesters:
            for course in sem.courses:
                if course.priority == PriorityLevel.CRITICAL:
                    unlocks = self.reverse_prereq_map.get(course.code, [])
                    if len(unlocks) >= 2:
                        n = len(unlocks)
                        if n >= 5:
                            sev = RiskSeverity.CRITICAL
                        elif n >= 3:
                            sev = RiskSeverity.HIGH
                        else:
                            sev = RiskSeverity.MEDIUM
                        risks.append(
                            RiskFactor(
                                f"{course.code} ({sem.label}) is a bottleneck — "
                                f"it unlocks {n} courses: {', '.join(unlocks[:4])}. "
                                f"Failing or dropping it would cascade delays.",
                                sev,
                            )
                        )

        for sem in pathway.semesters:
            if sem.total_units >= 18:
                critical_in_sem = [c for c in sem.courses if c.priority == PriorityLevel.CRITICAL]
                if critical_in_sem:
                    sev = (
                        RiskSeverity.CRITICAL
                        if sem.total_units >= 21
                        else RiskSeverity.HIGH
                    )
                    risks.append(
                        RiskFactor(
                            f"{sem.label} has {sem.total_units:.0f} units including "
                            f"critical course(s): {', '.join(c.code for c in critical_in_sem)}. "
                            f"Dropping a critical course here would delay graduation.",
                            sev,
                        )
                    )

        n_sem = len(pathway.semesters)
        if n_sem > 6:
            sev = RiskSeverity.MEDIUM if n_sem > 10 else RiskSeverity.LOW
            risks.append(
                RiskFactor(
                    f"Plan spans {n_sem} semesters "
                    f"({n_sem // 2} years). "
                    f"Consider Summer courses to shorten the timeline.",
                    sev,
                )
            )

        g = student.cumulative_gpa
        if g > 0 and g < 2.5:
            if g < 2.0:
                sev = RiskSeverity.CRITICAL
            elif g < 2.2:
                sev = RiskSeverity.HIGH
            else:
                sev = RiskSeverity.MEDIUM
            risks.append(
                RiskFactor(
                    f"Current GPA ({g:.2f}) is close to the "
                    f"2.0 minimum. Poor performance in heavy semesters could "
                    f"trigger academic probation.",
                    sev,
                )
            )

        mg = student.major_gpa
        if mg > 0 and mg < 2.5:
            if mg < 2.0:
                sev = RiskSeverity.HIGH
            elif mg < 2.2:
                sev = RiskSeverity.MEDIUM
            else:
                sev = RiskSeverity.MEDIUM
            risks.append(
                RiskFactor(
                    f"Major GPA ({mg:.2f}) needs attention. "
                    f"Some majors require a 2.0 minimum in major coursework.",
                    sev,
                )
            )

        rem = len(progress.remaining)
        if rem > 30:
            sev = RiskSeverity.HIGH if rem > 45 else RiskSeverity.MEDIUM
            risks.append(
                RiskFactor(
                    f"{rem} requirements remaining. "
                    f"This is a significant number — stay on track each semester.",
                    sev,
                )
            )

        risks.sort(key=lambda r: r.severity.value, reverse=True)
        return risks

    # =========================================================================
    # HELPER: BUILD REVERSE PREREQUISITE MAP
    # =========================================================================

    def _build_reverse_map(self) -> Dict[str, List[str]]:
        # Invert prereq_map so we can see downstream impact if a course is delayed.
        reverse = {}

        for course, prereqs in self.prereq_map.items():
            for prereq in prereqs:
                if prereq.startswith("__"):
                    continue
                if prereq not in reverse:
                    reverse[prereq] = []
                reverse[prereq].append(course)

        return reverse


# =============================================================================
# TEST — Run directly: python explainer.py
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Agent 3: Pathway Explainer — Test Run")
    print("=" * 65)

    from dpr_parser import DPRParser, SAMPLE_STUDENT_CSC
    from recommender import PathwayRecommender

    db = BulletinDatabase()
    parser = DPRParser(db)
    recommender = PathwayRecommender(db)

    print("\nAgent 1: Parsing student data...")
    progress = parser.parse_dict(SAMPLE_STUDENT_CSC)
    print(f"  {progress.summary()}")

    print("\nAgent 2: Generating pathway...")
    pathway = recommender.generate_pathway(progress)
    print(f"  Estimated graduation: {pathway.estimated_graduation}")
    print(f"  Semesters: {len(pathway.semesters)}")

    print("\nAgent 3: Generating explanations...")
    explainer = PathwayExplainer(db, recommender.prereq_map)
    explanation = explainer.explain(pathway, progress)

    print(f"\n{'=' * 65}")
    print("OVERALL STRATEGY")
    print(f"{'=' * 65}")
    print(explanation.overall_strategy)

    print(f"\n{'=' * 65}")
    print("COURSE EXPLANATIONS (first 8)")
    print(f"{'=' * 65}")
    for i, ce in enumerate(explanation.course_explanations[:8]):
        print(f"\n  [{ce.semester_label}] {ce.course_code}")
        for reason in ce.reasons:
            print(f"    WHY: {reason}")
        for alt in ce.alternatives:
            print(f"    ALT: {alt}")
        if ce.trade_offs:
            print(f"    TRADE-OFF: {ce.trade_offs}")

    if explanation.semester_notes:
        print(f"\n{'=' * 65}")
        print("SEMESTER NOTES")
        print(f"{'=' * 65}")
        for sem_label, note in explanation.semester_notes.items():
            print(f"  {sem_label}: {note}")

    if explanation.risk_factors:
        print(f"\n{'=' * 65}")
        print("RISK FACTORS")
        print(f"{'=' * 65}")
        for risk in explanation.risk_factors:
            print(f"  ⚠ [{risk.severity.name}] {risk.message}")

    print(f"\n{'=' * 65}")
    print("[ok] Agent 3 (Pathway Explainer) verified.")
    print(f"{'=' * 65}")
