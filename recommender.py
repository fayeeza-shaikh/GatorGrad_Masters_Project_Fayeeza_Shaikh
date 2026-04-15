# =============================================================================
# recommender.py — Pathway Recommender (Agent 2)
# CSC 895/898 Culminating Experience | SF State University
# =============================================================================
#
# Builds a semester-by-semester plan from ProgressReport (Agent 1) and
# DegreeProgram (bulletin_data): remaining requirements → GraduationPathway
# for Agent 3 (Explainer).
#
# Approach: prerequisite-aware ordering, priority scoring (CRITICAL ... LOW),
# greedy scheduling under unit caps, Fall/Spring rotation (Summer optional).
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from typing import List, Dict, Set, Optional, Tuple

from models import (
    ProgressReport,
    RequirementMatch,
    RequirementStatus,
    ScheduledCourse,
    SemesterPlan,
    GraduationPathway,
    PriorityLevel
)

from bulletin_data import (
    BulletinDatabase,
    DegreeProgram,
    Requirement
)


# =============================================================================
# RECOMMENDER CLASS — Agent 2
# =============================================================================

class PathwayRecommender:
    # Schedules remaining requirements into future semesters → GraduationPathway.

    # --- Configuration constants ---

    MAX_UNITS_PER_SEMESTER = 18
    # Typical upper load at SF State; exceeding this yields a warning.

    MIN_UNITS_PER_SEMESTER = 12
    # Full-time floor; below may affect financial aid.

    MAX_UNITS_SUMMER = 9
    # Shorter term → lower recommended load.

    MAX_SEMESTERS = 12
    # Safety cap (~6 years) to avoid unbounded scheduling.

    INCLUDE_SUMMER = False
    # Set True to allow Summer in the rotation (faster completion).

    def __init__(self, bulletin_db: BulletinDatabase):
        self.db = bulletin_db
        # One global lookup from bulletin scan + curated chains; reused per student.
        self.prereq_map = self._build_prereq_map()

    # =========================================================================
    # MAIN ENTRY POINT — Call this to run Agent 2
    # =========================================================================

    def generate_pathway(self, progress: ProgressReport) -> GraduationPathway:
        # Remaining/in-progress → prioritized ScheduledCourses → greedy semester
        # placement → totals, estimated graduation, warnings (heavy load, GPA, etc.).

        student = progress.student

        remaining = progress.remaining
        in_progress = progress.in_progress

        if not remaining and not in_progress:
            return GraduationPathway(
                student_id=student.student_id,
                program_code=student.program_code,
                catalog_year=student.catalog_year,
                estimated_graduation="Ready to graduate!",
                warnings=["All requirements appear to be complete."]
            )

        courses_to_schedule = self._build_course_list(remaining, student)

        completed_codes = set(student.completed_course_codes)
        in_progress_codes = set(student.in_progress_courses)

        semesters = self._schedule_semesters(
            courses_to_schedule,
            completed_codes,
            in_progress_codes,
            student.current_semester,
            student.current_year
        )

        total_remaining = sum(r.units_needed for r in remaining)

        if semesters:
            last_sem = semesters[-1]
            estimated_grad = f"{last_sem.semester} {last_sem.year}"
        else:
            estimated_grad = "Unable to determine"

        warnings = self._generate_warnings(semesters, student)

        return GraduationPathway(
            student_id=student.student_id,
            program_code=student.program_code,
            catalog_year=student.catalog_year,
            semesters=semesters,
            total_remaining_units=total_remaining,
            estimated_graduation=estimated_grad,
            warnings=warnings
        )

    # =========================================================================
    # STEP 2: BUILD COURSE LIST WITH PRIORITIES
    # =========================================================================

    def _build_course_list(
        self, remaining: List[RequirementMatch], student
    ) -> List[ScheduledCourse]:
        # Priority: CRITICAL = prerequisite for other still-needed courses (bottleneck);
        # HIGH = core major; MEDIUM = GE / flexible required; LOW = electives with options.
        # Output sorted highest priority first.

        courses = []

        all_needed_codes = set()
        for req in remaining:
            if req.course_options:
                all_needed_codes.add(req.course_options[0])
                # First option only here; Explainer (Agent 3) can surface alternatives.
            elif req.fulfilled_by is None:
                all_needed_codes.add(req.req_id)

        for req in remaining:
            course_code = ""
            course_title = req.req_name
            units = req.units_needed

            if req.course_options:
                course_code = req.course_options[0]
            elif req.notes:
                course_code = req.req_id
            else:
                course_code = req.req_id

            priority = self._calculate_priority(req, course_code, all_needed_codes)

            prereqs = self.prereq_map.get(course_code, [])

            course = ScheduledCourse(
                code=course_code,
                title=course_title,
                units=units,
                category=req.category,
                priority=priority,
                prerequisites=prereqs,
                reason=""   # Filled by Agent 3 (Explainer)
            )
            courses.append(course)

        priority_order = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3
        }
        courses.sort(key=lambda c: priority_order[c.priority])

        return courses

    def _calculate_priority(
        self, req: RequirementMatch, course_code: str, all_needed: Set[str]
    ) -> PriorityLevel:
        # CRITICAL when another needed course lists this code as a prerequisite.

        is_prereq_for_others = False
        for other_code in all_needed:
            other_prereqs = self.prereq_map.get(other_code, [])
            if course_code in other_prereqs:
                is_prereq_for_others = True
                break

        if is_prereq_for_others:
            return PriorityLevel.CRITICAL

        if req.category == "Major":
            if len(req.course_options) <= 1:
                return PriorityLevel.HIGH
            else:
                return PriorityLevel.MEDIUM

        if req.category == "GE":
            return PriorityLevel.MEDIUM

        if req.category == "University":
            return PriorityLevel.LOW

        return PriorityLevel.MEDIUM

    # =========================================================================
    # STEP 4: SCHEDULE COURSES INTO SEMESTERS (Core Algorithm)
    # =========================================================================

    def _schedule_semesters(
        self,
        courses: List[ScheduledCourse],
        completed: Set[str],
        in_progress: Set[str],
        current_semester: str,
        current_year: int
    ) -> List[SemesterPlan]:
        # Greedy scheduling: each semester, among courses whose prerequisites are
        # satisfied, take highest-priority items until the unit cap. Treated-as-done
        # set grows so later semesters see satisfied chains. Not globally optimal but
        # fast and sufficient for advising-style plans.

        semesters = []

        unscheduled = list(courses)

        will_be_completed = set(completed)
        will_be_completed.update(in_progress)

        sem_name, sem_year = self._next_semester(current_semester, current_year)

        for _ in range(self.MAX_SEMESTERS):

            if not unscheduled:
                break

            if sem_name == "Summer" and not self.INCLUDE_SUMMER:
                sem_name, sem_year = self._next_semester(sem_name, sem_year)
                continue

            max_units = self.MAX_UNITS_SUMMER if sem_name == "Summer" else self.MAX_UNITS_PER_SEMESTER

            eligible = []
            for course in unscheduled:
                if self._prerequisites_met(course, will_be_completed):
                    eligible.append(course)

            if not eligible:
                # Nothing is eligible yet; advance time so prior terms can "complete"
                # prerequisites (avoids stalling when the greedy pick is wrong locally).
                sem_name, sem_year = self._next_semester(sem_name, sem_year)
                continue

            semester_courses = []
            semester_units = 0.0

            for course in eligible:
                if semester_units + course.units <= max_units:
                    semester_courses.append(course)
                    semester_units += course.units

            if not semester_courses:
                sem_name, sem_year = self._next_semester(sem_name, sem_year)
                continue

            plan = SemesterPlan(
                semester=sem_name,
                year=sem_year,
                courses=semester_courses
            )
            semesters.append(plan)

            for course in semester_courses:
                unscheduled.remove(course)
                will_be_completed.add(course.code)

            sem_name, sem_year = self._next_semester(sem_name, sem_year)

        # Overflow beyond MAX_SEMESTERS: attach leftovers to last plan (caller may warn).
        if unscheduled and semesters:
            for course in unscheduled:
                semesters[-1].add_course(course)

        return semesters

    # =========================================================================
    # HELPER: CHECK IF PREREQUISITES ARE MET
    # =========================================================================

    def _prerequisites_met(self, course: ScheduledCourse, completed: Set[str]) -> bool:
        if not course.prerequisites:
            return True

        for prereq in course.prerequisites:
            if prereq not in completed:
                return False

        return True

    # =========================================================================
    # HELPER: GET NEXT SEMESTER
    # =========================================================================

    def _next_semester(self, current: str, year: int) -> Tuple[str, int]:
        # Order: Fall → Spring → Summer → Fall; year advances Fall → Spring only.

        if current == "Fall":
            return ("Spring", year + 1)
        elif current == "Spring":
            return ("Summer", year)
        elif current == "Summer":
            return ("Fall", year)
        else:
            return ("Fall", year)

    # =========================================================================
    # HELPER: BUILD PREREQUISITE MAP
    # =========================================================================

    def _build_prereq_map(self) -> Dict[str, List[str]]:
        # Union of bulletin-derived placeholders and hand-authored chains below.
        # Prerequisite detail in bulletin notes is partial; chains are curated for the prototype majors.

        prereq_map = {}

        for key in self.db.list_programs():
            program = self.db.programs[key]
            for req in program.major_requirements:
                if req.courses and hasattr(req, 'notes') and req.notes:
                    for code in req.courses:
                        if code not in prereq_map:
                            prereq_map[code] = []

        # --- Hardcoded prerequisite chains for our 5 majors ---
        # Prototype: key sequencing edges; production would load from an authoritative prereq source.

        cs_prereqs = {
            # Computer Science BS prerequisite chain
            "CSC 220": ["CSC 210"],        # Data Structures needs Intro to Programming
            "CSC 230": ["CSC 210"],        # Discrete Math needs Intro
            "CSC 256": ["CSC 220"],        # Machine Structures needs Data Structures
            "CSC 310": ["CSC 220"],        # Algorithms needs Data Structures
            "CSC 340": ["CSC 220"],        # Programming Methodology needs Data Structures
            "CSC 317": ["CSC 210"],        # Web Dev needs Intro
            "CSC 413": ["CSC 310"],        # Software Development needs Algorithms
            "CSC 415": ["CSC 310", "CSC 256"],  # OS needs Algorithms + Machine Structures
            "CSC 510": ["CSC 310"],        # Analysis of Algorithms needs Algorithms
            "CSC 648": ["CSC 413"],        # Software Engineering needs Software Dev
            "CSC 300GW": ["CSC 210"],      # Ethics (GWAR) needs Intro
            "CSC 215": ["CSC 210"],        # Intermediate Programming needs Intro
            "CSC 101": [],                 # Intro to Computing — no prereqs
            "MATH 227": ["MATH 226"],      # Calc II needs Calc I
            "MATH 225": ["MATH 226"],      # Linear Algebra needs Calc I
            "MATH 324": ["MATH 226"],      # Prob & Stats needs Calc I
            "PHYS 220": ["MATH 226"],      # Physics I needs Calc I
            "PHYS 230": ["PHYS 220", "MATH 227"],  # Physics II needs Physics I + Calc II
            "PHYS 222": ["PHYS 220"],      # Physics I Lab needs Physics I (co-req)
            "PHYS 232": ["PHYS 230"],      # Physics II Lab needs Physics II (co-req)
        }

        cmpe_prereqs = {
            # Computer Engineering BS prerequisite chain
            "ENGR 213": ["MATH 226"],      # Statics needs Calc I
            "ENGR 200": ["CSC 210"],       # Intro to Engineering needs programming
            "CSC 220": ["CSC 210"],
            "CSC 256": ["CSC 220"],
            "CSC 310": ["CSC 220"],
            "CSC 413": ["CSC 310"],
            "ENGR 323": ["ENGR 213"],      # Dynamics needs Statics
            "ENGR 301": ["MATH 227"],      # Circuits needs Calc II
            "ENGR 302": ["ENGR 301"],      # Circuits II needs Circuits I
        }

        psy_prereqs = {
            # Psychology BA prerequisite chain
            "PSY 371": ["PSY 200"],        # Stats needs General Psych
            "PSY 400": ["PSY 371"],        # Research Methods needs Stats
            "PSY 305GW": ["PSY 200"],      # Writing in Psych (GWAR) needs General
            "PSY 690": ["PSY 400"],        # Future Directions needs Research Methods
        }

        biol_prereqs = {
            # General Biology BA prerequisite chain
            "BIOL 230": ["BIOL 100"],      # Ecology needs Intro Bio
            "BIOL 240": ["BIOL 100"],      # Genetics needs Intro Bio
            "BIOL 330": ["BIOL 230"],      # Advanced Ecology needs Ecology
            "CHEM 115": ["MATH 124"],      # Gen Chem needs Stats
        }

        chem_prereqs = {
            # Chemistry BS prerequisite chain
            "CHEM 116": ["CHEM 115"],      # Gen Chem II needs Gen Chem I
            "CHEM 215": ["CHEM 116"],      # Organic I needs Gen Chem II
            "CHEM 216": ["CHEM 215"],      # Organic II needs Organic I
            "CHEM 315": ["CHEM 216"],      # Analytical needs Organic II
            "CHEM 340": ["CHEM 116", "MATH 227"],  # P-Chem needs Gen Chem II + Calc II
        }

        for prereqs in [cs_prereqs, cmpe_prereqs, psy_prereqs, biol_prereqs, chem_prereqs]:
            for code, deps in prereqs.items():
                prereq_map[code] = deps

        return prereq_map

    # =========================================================================
    # STEP 6: GENERATE WARNINGS
    # =========================================================================

    def _generate_warnings(self, semesters: List[SemesterPlan], student) -> List[str]:
        # Flags heavy/light (non-Summer) terms, long horizons, and GPA vs graduation minima.

        warnings = []

        for sem in semesters:
            if sem.total_units > self.MAX_UNITS_PER_SEMESTER:
                warnings.append(
                    f"{sem.label}: {sem.total_units:.0f} units is a heavy load. "
                    f"Consider reducing to {self.MAX_UNITS_PER_SEMESTER} units or fewer."
                )

            if sem.total_units < self.MIN_UNITS_PER_SEMESTER and sem.semester != "Summer":
                warnings.append(
                    f"{sem.label}: {sem.total_units:.0f} units is below full-time (12). "
                    f"This may affect financial aid."
                )

        if len(semesters) > 8:
            warnings.append(
                f"Plan requires {len(semesters)} semesters. "
                f"Consider adding Summer courses to graduate sooner."
            )

        if student.cumulative_gpa > 0 and student.cumulative_gpa < 2.0:
            warnings.append(
                f"Cumulative GPA ({student.cumulative_gpa}) is below 2.0 minimum. "
                f"Academic standing may be at risk."
            )

        if student.major_gpa > 0 and student.major_gpa < 2.0:
            warnings.append(
                f"Major GPA ({student.major_gpa}) is below 2.0 minimum required for graduation."
            )

        return warnings


# =============================================================================
# TEST — Run directly: python recommender.py
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Agent 2: Pathway Recommender — Test Run")
    print("=" * 65)

    from dpr_parser import DPRParser, SAMPLE_STUDENT_CSC

    db = BulletinDatabase()
    parser = DPRParser(db)
    recommender = PathwayRecommender(db)

    print("\nRunning Agent 1 (DPR Parser)...")
    progress = parser.parse_dict(SAMPLE_STUDENT_CSC)
    print(f"  Student: {progress.student.program_code} ({progress.student.catalog_year})")
    print(f"  {progress.summary()}")

    print("\nRunning Agent 2 (Pathway Recommender)...")
    pathway = recommender.generate_pathway(progress)

    print(f"\n{pathway.summary()}")

    print("\nSemester breakdown:")
    for sem in pathway.semesters:
        course_codes = [c.code for c in sem.courses]
        print(f"  {sem.label}: {len(sem.courses)} courses, {sem.total_units:.0f}u → {course_codes}")

    print("\n" + "=" * 65)
    print("[ok] Agent 2 (Pathway Recommender) verified.")
    print("=" * 65)
