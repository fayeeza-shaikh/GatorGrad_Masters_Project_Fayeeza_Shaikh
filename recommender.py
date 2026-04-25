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

import re
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

# Sentinel stored in prereq_map lists — satisfied by legacy CSC 210 or 2023+ CSC 101+CSC 215.
CS_PROGRAMMING_INTRO = "__CS_PROGRAMMING_INTRO__"
# Do not schedule these until first-programming intro courses are cleared from the plan.
_CS_INTRO_GATE_CODES = frozenset({"CSC 101", "CSC 215", "CSC 210"})
# Upper-division core that should not run ahead of a coherent CS intro sequence.
_CS_UPPER_CORE_GATE = frozenset({"CSC 413", "CSC 415", "CSC 510", "CSC 648"})
# Foundational GE areas to front-load before other GE buckets when possible.
_FOUNDATIONAL_GE_IDS = frozenset({
    "GE_1A", "GE_1B", "GE_1C", "GE_2",  # 2025-26+ framework
    "GE_A1", "GE_A2", "GE_A3", "GE_B4",  # legacy equivalents
})
_CHEM_LOWER_GATE_CODES = frozenset({
    "CHEM 115", "CHEM 215", "CHEM 233", "CHEM 234", "CHEM 235", "CHEM 236", "CHEM 251"
})


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
        has_major_or_ge_gwar_course = any(
            self._is_gwar_designated_requirement(req) and req.req_id != "UNIV_GWAR"
            for req in remaining
        )

        all_needed_codes = set()
        for req in remaining:
            if req.course_options:
                all_needed_codes.add(req.course_options[0])
                # First option only here; Explainer (Agent 3) can surface alternatives.
            elif req.fulfilled_by is None:
                all_needed_codes.add(req.req_id)

        for req in remaining:
            if req.req_id == "UNIV_GWAR" and has_major_or_ge_gwar_course:
                # Avoid duplicate planning rows when GWAR is already represented by a
                # specific GW-designated course requirement (e.g., PSY 305GW).
                continue

            course_code = ""
            course_title = self._display_requirement_title(req.req_name)
            units = req.units_needed

            if req.course_options:
                if "Elective" in req.req_name:
                    prefix = req.course_options[0].split()[0] if req.course_options else "COURSE"
                    slot_units = 3.0
                    remaining_units = max(slot_units, float(req.units_needed))
                    priority = self._calculate_priority(req, prefix, all_needed_codes)
                    slot_idx = 1
                    while remaining_units > 0:
                        this_slot = min(slot_units, remaining_units)
                        slot_code = f"{prefix} ELECTIVE {slot_idx}"
                        course = ScheduledCourse(
                            code=slot_code,
                            title=f"{self._display_requirement_title(req.req_name)} (Choose from approved options)",
                            units=this_slot,
                            category=req.category,
                            priority=priority,
                            prerequisites=[],
                            reason=""
                        )
                        courses.append(course)
                        remaining_units -= this_slot
                        slot_idx += 1
                    continue
                else:
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

    @staticmethod
    def _is_gwar_designated_requirement(req: RequirementMatch) -> bool:
        codes = set(req.course_options or [])
        if req.fulfilled_by:
            codes.add(req.fulfilled_by)
        return any(str(code).strip().endswith("GW") for code in codes if code)

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
            if req.req_id in _FOUNDATIONAL_GE_IDS:
                return PriorityLevel.HIGH
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

            semester_courses = []
            semester_units = 0.0

            # Pack semester with term-level prerequisite enforcement:
            # only courses whose prerequisites were completed before this term starts
            # are eligible (no same-semester prereq chaining).
            term_completed = set(will_be_completed)
            while True:
                pending_intro = {c.code for c in unscheduled} & _CS_INTRO_GATE_CODES
                intro_gate = bool(pending_intro)
                lower_ge_pending = any(
                    self._is_lower_div_ge_course(c) for c in unscheduled
                )
                chem_lower_pending = any(
                    str(c.code) in _CHEM_LOWER_GATE_CODES for c in unscheduled
                )

                eligible: List[ScheduledCourse] = []
                for course in unscheduled:
                    if intro_gate and course.code in _CS_UPPER_CORE_GATE:
                        continue
                    if chem_lower_pending and self._is_upper_div_chem_course(course):
                        continue
                    if lower_ge_pending and self._is_upper_div_ge_course(course):
                        # Keep UD GE buckets (3UD/4UD/5UD and legacy UDB/UDC/UDD)
                        # behind all lower-division GE requirements.
                        continue
                    if not self._prerequisites_met(course, term_completed):
                        continue
                    if semester_units + course.units > max_units:
                        continue
                    eligible.append(course)

                if not eligible:
                    break

                major_units = sum(
                    c.units for c in semester_courses if self._is_major_course(c)
                )
                non_major_units = semester_units - major_units
                need_major = major_units < non_major_units

                preferred = [
                    c for c in eligible if self._is_major_course(c) == need_major
                ]
                picked: Optional[ScheduledCourse] = preferred[0] if preferred else eligible[0]

                if picked is None:
                    break

                semester_courses.append(picked)
                semester_units += picked.units
                unscheduled.remove(picked)

            if not semester_courses:
                # Nothing fits this term; advance time so prerequisites can clear.
                sem_name, sem_year = self._next_semester(sem_name, sem_year)
                continue

            plan = SemesterPlan(
                semester=sem_name,
                year=sem_year,
                courses=semester_courses
            )
            semesters.append(plan)
            for course in semester_courses:
                will_be_completed.add(course.code)

            sem_name, sem_year = self._next_semester(sem_name, sem_year)

        # Overflow beyond MAX_SEMESTERS: attach leftovers to last plan (caller may warn).
        if unscheduled and semesters:
            for course in unscheduled:
                semesters[-1].add_course(course)

        return semesters

    @staticmethod
    def _is_major_course(course: ScheduledCourse) -> bool:
        """Treat Major bucket as one side of 50/50 mix; GE+University on the other."""
        return course.category == "Major"

    @staticmethod
    def _is_upper_div_ge_course(course: ScheduledCourse) -> bool:
        if course.category != "GE":
            return False
        code = str(course.code).strip().upper()
        return code in {"GE_3UD", "GE_4UD", "GE_5UD", "GE_UDB", "GE_UDC", "GE_UDD"}

    def _is_lower_div_ge_course(self, course: ScheduledCourse) -> bool:
        if course.category != "GE":
            return False
        return not self._is_upper_div_ge_course(course)

    @staticmethod
    def _is_upper_div_chem_course(course: ScheduledCourse) -> bool:
        if course.category != "Major":
            return False
        code = str(course.code).strip().upper()
        if not code.startswith("CHEM "):
            return False
        parts = code.split()
        if len(parts) < 2:
            return False
        number_part = "".join(ch for ch in parts[1] if ch.isdigit())
        if not number_part:
            return False
        return int(number_part) >= 300

    @staticmethod
    def _display_requirement_title(req_name: str) -> str:
        """
        Keep UI labels concise for area-bucket requirements.
        Example: "Area 1: Basic Psychological Processes" -> "Area 1"
        """
        m = re.match(r"^(Area\s+\d+)\s*:", req_name.strip(), flags=re.IGNORECASE)
        if m:
            return m.group(1)
        return req_name

    # =========================================================================
    # HELPER: CHECK IF PREREQUISITES ARE MET
    # =========================================================================

    @staticmethod
    def _cs_programming_intro_done(completed: Set[str]) -> bool:
        """CSC 210 (legacy) or CSC 101 + CSC 215 (2023+ catalog) satisfies first programming."""
        if "CSC 210" in completed:
            return True
        return "CSC 101" in completed and "CSC 215" in completed

    def _prerequisite_token_met(self, token: str, completed: Set[str]) -> bool:
        if token == CS_PROGRAMMING_INTRO:
            return self._cs_programming_intro_done(completed)
        return token in completed

    def _prerequisites_met(self, course: ScheduledCourse, completed: Set[str]) -> bool:
        prereqs = course.prerequisites
        if not prereqs:
            return True

        for prereq in prereqs:
            if not self._prerequisite_token_met(prereq, completed):
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
            # Computer Science BS — intro: CSC 210 (legacy) or CSC 101 + CSC 215 (2023+ bulletins)
            "CSC 101": [],
            "CSC 215": ["CSC 101"],
            "CSC 220": [CS_PROGRAMMING_INTRO],
            "CSC 230": ["CSC 220"],
            "CSC 256": ["CSC 220"],
            "CSC 310": ["CSC 220"],
            "CSC 340": ["CSC 220"],
            "CSC 317": ["CSC 220"],
            "CSC 413": ["CSC 220", "CSC 317"],
            "CSC 415": ["CSC 310", "CSC 256"],
            "CSC 510": ["CSC 310"],
            "CSC 648": ["CSC 413"],
            "CSC 300GW": ["CSC 220"],
            "MATH 227": ["MATH 226"],      # Calc II needs Calc I
            "MATH 225": ["MATH 226"],      # Linear Algebra needs Calc I
            "MATH 324": ["MATH 226"],      # Prob & Stats needs Calc I
            "PHYS 220": ["MATH 226"],      # Physics I needs Calc I
            "PHYS 230": ["PHYS 220", "MATH 227"],  # Physics II needs Physics I + Calc II
            "PHYS 222": ["PHYS 220"],      # Physics I Lab needs Physics I (co-req)
            "PHYS 232": ["PHYS 230"],      # Physics II Lab needs Physics II (co-req)
        }

        cmpe_prereqs = {
            # Computer Engineering BS prerequisite chain (shared CSC keys must match CS intro logic)
            "ENGR 213": ["MATH 226"],      # Statics needs Calc I
            "ENGR 200": [CS_PROGRAMMING_INTRO],
            "CSC 220": [CS_PROGRAMMING_INTRO],
            "CSC 256": ["CSC 220"],
            "CSC 310": ["CSC 220"],
            "CSC 413": ["CSC 220", "CSC 317"],
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
            # Chemistry BS prerequisite chain (updated for recent catalogs)
            "CHEM 215": ["CHEM 115"],              # General Chem II after Chem I
            "CHEM 233": ["CHEM 215"],              # Organic I after Gen Chem II
            "CHEM 234": ["CHEM 233"],              # Organic I Lab after Organic I
            "CHEM 235": ["CHEM 233"],              # Organic II after Organic I
            "CHEM 236": ["CHEM 235"],              # Organic II Lab after Organic II
            "CHEM 321": ["CHEM 235"],              # Quantitative Analysis after Org II
            "CHEM 322": ["CHEM 321"],              # Quant Analysis Lab after lecture
            "CHEM 325": ["CHEM 235"],              # Inorganic Chemistry after Org II
            "CHEM 340": ["CHEM 235", "MATH 227"],  # Biochemistry I after Org II + Calc II
            "CHEM 351": ["CHEM 251", "MATH 227"],  # P-Chem I after math/physics foundation
            "CHEM 353": ["CHEM 351"],              # P-Chem II after P-Chem I
            "CHEM 390GW": ["CHEM 235"],            # GW writing/research after core chemistry
            "CHEM 426": ["CHEM 325"],              # Adv Inorganic Lab after Inorganic Chem
            "CHEM 451": ["CHEM 351"],              # Exp Physical Chemistry after P-Chem I
        }

        for prereqs in [cs_prereqs, cmpe_prereqs, psy_prereqs, biol_prereqs, chem_prereqs]:
            for code, deps in prereqs.items():
                # Preserve the first non-empty mapping for shared codes to avoid
                # cross-program overrides (e.g., CSC keys present in both CS and CMPE).
                if code not in prereq_map or not prereq_map[code]:
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
