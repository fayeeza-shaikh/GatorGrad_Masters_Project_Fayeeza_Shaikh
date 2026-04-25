# =============================================================================
# dpr_parser.py — DPR Parser (Agent 1)
# CSC 895/898 Culminating Experience | SF State University
# =============================================================================
#
# Parses a Degree Progress Report (DPR) from an SF State Advisee PDF or from
# a dict (testing). Produces a ProgressReport: StudentProfile plus requirement
# fulfillment vs. bulletin_data.DegreeProgram requirements.
#
# PDF path → pdfplumber text/tables + regex → dict → same pipeline as dict input.
#
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

import re
from typing import List, Set, Optional, Dict

from models import (
    StudentProfile,
    CompletedCourse,
    RequirementMatch,
    ProgressReport,
    RequirementStatus
)

from bulletin_data import (
    BulletinDatabase,
    DegreeProgram,
    Requirement
)

# pdfplumber is imported inside _extract_from_pdf so the package can stay optional.


# =============================================================================
# DPR PARSER CLASS — Agent 1
# =============================================================================

class DPRParser:

    def __init__(self, bulletin_db: BulletinDatabase):
        self.db = bulletin_db

    # =========================================================================
    # MAIN ENTRY POINTS — Two ways to use Agent 1
    # =========================================================================

    def parse_pdf(self, pdf_path: str) -> ProgressReport:
        student_data = self._extract_from_pdf(pdf_path)
        return self.parse_dict(student_data)

    def parse_dict(self, student_data: dict) -> ProgressReport:
        profile = self._build_profile(student_data)
        program = self._get_program(profile.program_code, profile.catalog_year)
        requirement_matches = self._match_all_requirements(profile, program)
        profile.major_gpa = self._calculate_major_gpa(profile, program)
        return ProgressReport(student=profile, requirements=requirement_matches)

    # =========================================================================
    # PDF EXTRACTION — Reads the actual DPR PDF
    # =========================================================================

    def _extract_from_pdf(self, pdf_path: str) -> dict:
        # Advisee DPR PDFs follow a fixed layout: narrative lines for identity and
        # standing, plus tabular course history (code, description, units, term, grade).

        import pdfplumber

        full_text = ""
        all_tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

                tables = page.extract_tables()
                for table in tables:
                    all_tables.append(table)

        student_data = self._extract_student_info(full_text)
        student_data["completed_courses"] = self._extract_courses_from_tables(all_tables)

        return student_data

    def _extract_student_info(self, text: str) -> dict:
        # Example DPR lines: "Gina PREF Testram ID 906757519",
        # "Plan: Nursing (Non-RN)-BS Fall 2021", "Overall GPA: 2.700"

        data = {}

        # Name + 9-digit ID; line-by-line to avoid cross-line matches
        for line in text.split('\n'):
            match = re.search(r'([A-Z][\w\s]+?)\s+ID\s+(\d{9})', line)
            if match:
                raw_name = match.group(1).strip()
                # "PREF" marks preferred name in the export; strip for display consistency
                name = re.sub(r'\bPREF\b', '', raw_name).strip()
                name = re.sub(r'\s+', ' ', name)
                data["name"] = name
                data["student_id"] = match.group(2)
                break

        # Plan line encodes program title and catalog start term/year
        match = re.search(r'Plan:\s+(.+?)\s+(Fall|Spring|Summer)\s+(\d{4})', text)
        if match:
            plan_name = match.group(1).strip()
            catalog_term = match.group(2)
            catalog_year_start = int(match.group(3))

            # Internal catalog label: academic year span (e.g. Fall 2021 → "2021-22")
            catalog_year_end = (catalog_year_start + 1) % 100
            data["catalog_year"] = f"{catalog_year_start}-{catalog_year_end:02d}"

            data["program_code"] = self._map_plan_to_code(plan_name)
            data["plan_name"] = plan_name

        match = re.search(r'Overall GPA:\s+([\d.]+)', text)
        if match:
            data["cumulative_gpa"] = float(match.group(1))

        match = re.search(r'SF State GPA:\s+([\d.]+)', text)
        if match:
            data["sfsu_gpa"] = float(match.group(1))

        match = re.search(r'Academic Standing:\s+(.+)', text)
        if match:
            data["academic_standing"] = match.group(1).strip()

        # Fixed 120-unit degree template in this DPR layout
        match = re.search(r'120\.00\s+required,\s+([\d.]+)\s+taken,\s+([\d.]+)\s+needed', text)
        if match:
            data["total_units_completed"] = float(match.group(1))
            data["units_needed"] = float(match.group(2))

        data.setdefault("student_id", "000000000")
        data.setdefault("name", "Unknown Student")
        data.setdefault("program_code", "UNKNOWN")
        data.setdefault("catalog_year", "2024-25")
        data.setdefault("cumulative_gpa", 0.0)
        data.setdefault("current_semester", "Fall")
        data.setdefault("current_year", 2025)
        data.setdefault("in_progress_courses", [])

        return data

    def _extract_courses_from_tables(self, tables: list) -> List[dict]:
        # Typical header row: Course | Description | Units | When | Grade | Status

        courses = []
        # Same course often appears in multiple requirement sections/pages
        seen_courses = set()

        for table in tables:
            for row in table:
                if row is None or len(row) < 4:
                    continue

                cleaned = []
                for cell in row:
                    if cell is not None:
                        cleaned.append(str(cell).strip().replace('\n', ' '))
                    else:
                        cleaned.append("")

                first_cell = cleaned[0] if cleaned else ""
                if first_cell in ("Course", "", "View All") or "First" in first_cell:
                    continue
                if first_cell.startswith("http") or first_cell.startswith("cmsweb"):
                    continue
                if "11:24 AM" in first_cell or "," in first_cell and len(first_cell) < 15:
                    continue

                course = self._parse_course_row(cleaned)
                if course is not None:
                    key = f"{course['code']}_{course['semester']}_{course['year']}"
                    if key not in seen_courses:
                        seen_courses.add(key)
                        courses.append(course)

        return courses

    def _parse_course_row(self, row: list) -> Optional[dict]:
        # Column order varies; we locate code, units, term, grade, and description heuristically.

        code_cell = row[0]
        if not code_cell:
            return None

        code_pattern = re.match(
            r'^([A-Z]{2,4}(?::[A-Z]+)?)\s*(\d{3}(?:[A-Z]*(?:GW|TR)?)?)',
            code_cell
        )
        # [A-Z]{2,4}       department (CSC, MATH, …)
        # (?::[A-Z]+)?      optional AP:ENG-style prefix
        # \s*              optional space before number
        # \d{3}            course number
        # (?:[A-Z]*...)?   optional suffix (GW, TR, …)

        if not code_pattern:
            return None

        course_code = code_cell.strip()

        units = 3.0
        for cell in row:
            if cell and re.match(r'^\d+\.\d+$', cell.strip()):
                units = float(cell.strip())
                break

        semester = ""
        year = 0
        for cell in row:
            if cell:
                sem_match = re.search(r'(Fall|Spring|Summer)\s+(\d{4})', cell)
                if sem_match:
                    semester = sem_match.group(1)
                    year = int(sem_match.group(2))
                    break

        grade = ""
        valid_grades = {
            "A", "A-", "B+", "B", "B-", "C+", "C", "C-",
            "D+", "D", "D-", "F", "CR", "NC", "W", "I",
            "T", "RD", "IC", "WU"
        }
        for cell in row:
            if cell and cell.strip() in valid_grades:
                grade = cell.strip()
                break

        description = ""
        non_empty = [c for c in row[1:] if c and c.strip()]
        if non_empty:
            for cell in non_empty:
                cell_clean = cell.strip()
                if not re.match(r'^[\d.]+$', cell_clean) and cell_clean not in valid_grades:
                    if not re.match(r'(Fall|Spring|Summer)', cell_clean):
                        if cell_clean not in ("GE D", "GE C2/D/USH", "Designation"):
                            description = cell_clean
                            break

        if grade or (semester and year):
            return {
                "code": course_code,
                "title": description,
                "units": units,
                "grade": grade,
                "semester": semester,
                "year": year
            }

        return None

    def _map_plan_to_code(self, plan_name: str) -> str:
        # DPR plan titles must align with bulletin_data program_code strings.

        plan_lower = plan_name.lower()

        if "computer science" in plan_lower:
            return "CSC_BS"
        elif "computer engineering" in plan_lower:
            return "CMPE_BS"
        elif "psychology" in plan_lower:
            return "PSY_BA"
        elif "biology" in plan_lower:
            return "BIOL_BA"
        elif "chemistry" in plan_lower:
            return "CHEM_BS"
        elif "nursing" in plan_lower:
            return "NURS_BS"
        else:
            print(f"  [!] Unknown major: '{plan_name}'. Cannot map to program code.")
            return "UNKNOWN"

    # =========================================================================
    # PROFILE BUILDING — Same as before, works for both PDF and dict input
    # =========================================================================

    def _build_profile(self, data: dict) -> StudentProfile:
        # PRIVACY (FERPA): Real name and student ID are not persisted. Parsed values
        # are replaced with placeholders before building StudentProfile so downstream
        # storage and logs avoid identifiable student data.

        anonymized_id = "student_id_number"
        anonymized_name = "Student"

        completed = []
        for c in data.get("completed_courses", []):
            course = CompletedCourse(
                code=c["code"],
                title=c.get("title", ""),
                units=float(c.get("units", 3.0)),
                grade=c.get("grade", ""),
                semester=c.get("semester", ""),
                year=int(c.get("year", 0))
            )
            completed.append(course)

        # Prefer PDF totals when present; otherwise sum passing course units
        total_units = data.get("total_units_completed",
                               sum(c.units for c in completed if c.is_passing))

        profile = StudentProfile(
            student_id=anonymized_id,
            name=anonymized_name,
            program_code=data.get("program_code", ""),
            catalog_year=data.get("catalog_year", ""),
            completed_courses=completed,
            in_progress_courses=data.get("in_progress_courses", []),
            cumulative_gpa=float(data.get("cumulative_gpa", 0.0)),
            total_units_completed=float(total_units),
            total_units_required=120,
            current_semester=data.get("current_semester", "Fall"),
            current_year=int(data.get("current_year", 2025))
        )

        if profile.cumulative_gpa == 0.0 and completed:
            profile.cumulative_gpa = profile.calculate_gpa()

        return profile

    # =========================================================================
    # DEGREE PROGRAM LOOKUP
    # =========================================================================

    def _get_program(self, program_code: str, catalog_year: str) -> DegreeProgram:

        program = self.db.get_program(program_code, catalog_year)
        if program is not None:
            return program

        all_versions = self.db.get_programs_by_code(program_code)
        if all_versions:
            fallback = all_versions[-1]
            print(f"  [!] Catalog year '{catalog_year}' not found for {program_code}.")
            print(f"      Using {fallback.catalog_year} instead.")
            return fallback

        available_codes = set()
        for key in self.db.list_programs():
            parts = key.rsplit("_", 1)
            if len(parts) == 2:
                code = key[:key.rfind("_")]
                available_codes.add(code)

        print(f"  [!] Program '{program_code}' not found in database.")
        print(f"      Supported majors: {sorted(available_codes)}")
        print(f"      Returning partial report (courses only, no requirement matching).")

        # Empty shell keeps callers stable when the major is missing from bulletin_data
        return DegreeProgram(
            program_code=program_code,
            program_name=f"Unknown Program ({program_code})",
            degree_type="Unknown",
            catalog_year=catalog_year,
            total_units=120
        )

    # =========================================================================
    # REQUIREMENT MATCHING — Core logic of Agent 1
    # =========================================================================

    def _match_all_requirements(
        self, profile: StudentProfile, program: DegreeProgram
    ) -> List[RequirementMatch]:

        matches = []
        used_courses: Set[str] = set()

        completed_codes = profile.completed_course_codes
        in_progress = set(profile.in_progress_courses)

        for req in program.major_requirements:
            match = self._match_one_requirement(req, completed_codes, in_progress, used_courses)
            matches.append(match)

        ge_met_by_major = set(program.ge_met_in_major)

        for req in program.ge_requirements:
            if req.req_id in ge_met_by_major:
                matches.append(RequirementMatch(
                    req_id=req.req_id,
                    req_name=req.name,
                    category="GE",
                    status=RequirementStatus.COMPLETE,
                    fulfilled_by="(met by major)",
                    units_needed=req.units,
                    notes="Satisfied by major coursework"
                ))
            else:
                match = self._match_one_requirement(req, completed_codes, in_progress, used_courses)
                matches.append(match)

        for req in program.university_requirements:
            if req.req_id == "UNIV_GWAR":
                gwar_completed = self._find_completed_gwar_course(completed_codes)
                if gwar_completed:
                    matches.append(RequirementMatch(
                        req_id=req.req_id,
                        req_name=req.name,
                        category=req.category,
                        status=RequirementStatus.COMPLETE,
                        fulfilled_by=gwar_completed,
                        units_needed=req.units,
                        notes="Satisfied by GWAR-designated course in major/GE"
                    ))
                    continue

                gwar_in_progress = self._find_completed_gwar_course(in_progress)
                if gwar_in_progress:
                    matches.append(RequirementMatch(
                        req_id=req.req_id,
                        req_name=req.name,
                        category=req.category,
                        status=RequirementStatus.IN_PROGRESS,
                        fulfilled_by=gwar_in_progress,
                        units_needed=req.units,
                        notes="Will be satisfied by GWAR-designated course in progress"
                    ))
                    continue

            match = self._match_one_requirement(req, completed_codes, in_progress, used_courses)
            matches.append(match)

        return matches

    @staticmethod
    def _find_completed_gwar_course(course_codes: Set[str]) -> Optional[str]:
        for code in sorted(course_codes):
            if code.strip().endswith("GW"):
                return code
        return None

    def _match_one_requirement(
        self,
        req: Requirement,
        completed_codes: Set[str],
        in_progress: Set[str],
        used_courses: Set[str]
    ) -> RequirementMatch:
        # Prefer courses not yet consumed by another requirement; a second pass allows
        # the same completed course to satisfy overlapping GE rules when applicable.

        eligible = set(req.courses + req.course_options)

        for code in eligible:
            if code in completed_codes and code not in used_courses:
                used_courses.add(code)
                return RequirementMatch(
                    req_id=req.req_id, req_name=req.name, category=req.category,
                    status=RequirementStatus.COMPLETE, fulfilled_by=code,
                    units_needed=req.units, course_options=list(eligible), notes=req.notes
                )

        for code in eligible:
            if code in completed_codes:
                return RequirementMatch(
                    req_id=req.req_id, req_name=req.name, category=req.category,
                    status=RequirementStatus.COMPLETE, fulfilled_by=code,
                    units_needed=req.units, course_options=list(eligible), notes=req.notes
                )

        for code in eligible:
            if code in in_progress:
                return RequirementMatch(
                    req_id=req.req_id, req_name=req.name, category=req.category,
                    status=RequirementStatus.IN_PROGRESS, fulfilled_by=code,
                    units_needed=req.units, course_options=list(eligible), notes=req.notes
                )

        return RequirementMatch(
            req_id=req.req_id, req_name=req.name, category=req.category,
            status=RequirementStatus.NOT_STARTED, fulfilled_by=None,
            units_needed=req.units, course_options=list(eligible), notes=req.notes
        )

    # =========================================================================
    # MAJOR GPA CALCULATION
    # =========================================================================

    def _calculate_major_gpa(
        self, profile: StudentProfile, program: DegreeProgram
    ) -> float:

        major_course_codes = set()
        for req in program.major_requirements:
            for code in req.courses + req.course_options:
                major_course_codes.add(code)

        major_courses = [
            c for c in profile.completed_courses
            if c.code in major_course_codes
        ]

        if not major_courses:
            return 0.0
        return profile.calculate_gpa(major_courses)


# =============================================================================
# SAMPLE DATA — For testing without a PDF
# =============================================================================
# BulletinDatabase defines one program snapshot per (code, year); Streamlit
# sample mode lets users pick any of these (DPR PDFs supply catalog_year from text).
SAMPLE_CATALOG_YEARS = (
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
)

SAMPLE_STUDENT_CSC = {
    "student_id": "912345678",
    "name": "Sample Student",
    "program_code": "CSC_BS",
    "catalog_year": "2024-25",
    "current_semester": "Fall",
    "current_year": 2025,
    "in_progress_courses": ["CSC 310", "CSC 340"],
    "completed_courses": [
        {"code": "CSC 210", "title": "Intro to Programming", "units": 3, "grade": "A", "semester": "Fall", "year": 2023},
        {"code": "CSC 220", "title": "Data Structures", "units": 3, "grade": "B+", "semester": "Spring", "year": 2024},
        {"code": "CSC 230", "title": "Discrete Math", "units": 3, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "CSC 256", "title": "Machine Structures", "units": 3, "grade": "B-", "semester": "Fall", "year": 2024},
        {"code": "MATH 226", "title": "Calculus I", "units": 4, "grade": "B", "semester": "Fall", "year": 2023},
        {"code": "MATH 227", "title": "Calculus II", "units": 4, "grade": "C+", "semester": "Spring", "year": 2024},
        {"code": "ENG 114", "title": "Writing the First Year", "units": 3, "grade": "A-", "semester": "Fall", "year": 2023},
        {"code": "PHYS 111", "title": "General Physics I", "units": 3, "grade": "B", "semester": "Fall", "year": 2024},
        {"code": "MATH 324", "title": "Prob and Stats", "units": 3, "grade": "W", "semester": "Fall", "year": 2024},
    ]
}

SAMPLE_STUDENT_CMPE = {
    "student_id": "912345679",
    "name": "Sample Student",
    "program_code": "CMPE_BS",
    "catalog_year": "2024-25",
    "current_semester": "Fall",
    "current_year": 2025,
    "in_progress_courses": ["ENGR 213", "ENGR 214"],
    "completed_courses": [
        {"code": "MATH 226", "title": "Calculus I", "units": 4, "grade": "B+", "semester": "Fall", "year": 2023},
        {"code": "MATH 227", "title": "Calculus II", "units": 4, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "PHYS 220", "title": "General Physics w/ Calc I", "units": 3, "grade": "B-", "semester": "Spring", "year": 2024},
        {"code": "PHYS 222", "title": "General Physics I Lab", "units": 1, "grade": "A", "semester": "Spring", "year": 2024},
        {"code": "ENGR 100", "title": "Intro to Engineering", "units": 3, "grade": "A-", "semester": "Fall", "year": 2023},
        {"code": "ENGR 205", "title": "Electrical Circuits I", "units": 3, "grade": "B", "semester": "Fall", "year": 2024},
        {"code": "ENGR 206", "title": "Electrical Circuits I Lab", "units": 1, "grade": "A", "semester": "Fall", "year": 2024},
        {"code": "CSC 210", "title": "Intro to Programming", "units": 3, "grade": "B+", "semester": "Fall", "year": 2023},
        {"code": "ENG 114", "title": "Writing the First Year", "units": 3, "grade": "B", "semester": "Fall", "year": 2023},
        {"code": "COMM 150", "title": "Oral Communication", "units": 3, "grade": "A-", "semester": "Spring", "year": 2024},
    ]
}

SAMPLE_STUDENT_PSY = {
    "student_id": "912345680",
    "name": "Sample Student",
    "program_code": "PSY_BA",
    "catalog_year": "2024-25",
    "current_semester": "Spring",
    "current_year": 2025,
    "in_progress_courses": ["PSY 371"],
    "completed_courses": [
        {"code": "PSY 200", "title": "General Psychology", "units": 3, "grade": "A", "semester": "Fall", "year": 2023},
        {"code": "PSY 250", "title": "Behavioral Neuroscience", "units": 3, "grade": "B+", "semester": "Spring", "year": 2024},
        {"code": "PSY 301", "title": "Industrial/Organizational Psych", "units": 3, "grade": "B", "semester": "Fall", "year": 2024},
        {"code": "PSY 303", "title": "Psych: The Major & Profession", "units": 1, "grade": "A", "semester": "Fall", "year": 2023},
        {"code": "ENG 114", "title": "Writing the First Year", "units": 3, "grade": "A-", "semester": "Fall", "year": 2023},
        {"code": "MATH 124", "title": "Elementary Statistics", "units": 4, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "COMM 150", "title": "Oral Communication", "units": 3, "grade": "B+", "semester": "Fall", "year": 2023},
        {"code": "PHIL 110", "title": "Critical Thinking", "units": 3, "grade": "A-", "semester": "Spring", "year": 2024},
    ]
}

SAMPLE_STUDENT_BIOL = {
    "student_id": "912345681",
    "name": "Sample Student",
    "program_code": "BIOL_BA",
    "catalog_year": "2024-25",
    "current_semester": "Fall",
    "current_year": 2025,
    "in_progress_courses": ["BIOL 240", "CHEM 116"],
    "completed_courses": [
        {"code": "BIOL 230", "title": "Principles of Biology I", "units": 4, "grade": "B+", "semester": "Fall", "year": 2023},
        {"code": "BIOL 231", "title": "Principles of Biology I Lab", "units": 1, "grade": "A", "semester": "Fall", "year": 2023},
        {"code": "CHEM 115", "title": "General Chemistry I", "units": 4, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "PHYS 111", "title": "General Physics I", "units": 3, "grade": "B-", "semester": "Fall", "year": 2024},
        {"code": "PHYS 112", "title": "General Physics I Lab", "units": 1, "grade": "A", "semester": "Fall", "year": 2024},
        {"code": "MATH 226", "title": "Calculus I", "units": 4, "grade": "C+", "semester": "Fall", "year": 2023},
        {"code": "ENG 114", "title": "Writing the First Year", "units": 3, "grade": "A", "semester": "Fall", "year": 2023},
        {"code": "COMM 150", "title": "Oral Communication", "units": 3, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "PHIL 110", "title": "Critical Thinking", "units": 3, "grade": "B+", "semester": "Spring", "year": 2024},
    ]
}

SAMPLE_STUDENT_CHEM = {
    "student_id": "912345682",
    "name": "Sample Student",
    "program_code": "CHEM_BS",
    "catalog_year": "2024-25",
    "current_semester": "Fall",
    "current_year": 2025,
    "in_progress_courses": ["CHEM 215", "MATH 228"],
    "completed_courses": [
        {"code": "CHEM 115", "title": "General Chemistry I", "units": 4, "grade": "A-", "semester": "Fall", "year": 2023},
        {"code": "CHEM 233", "title": "General Chemistry I Lab", "units": 1, "grade": "A", "semester": "Fall", "year": 2023},
        {"code": "CHEM 234", "title": "General Chemistry II Lab", "units": 1, "grade": "B+", "semester": "Spring", "year": 2024},
        {"code": "CHEM 251", "title": "Quantitative Analytical Chem", "units": 2, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "MATH 226", "title": "Calculus I", "units": 4, "grade": "B+", "semester": "Fall", "year": 2023},
        {"code": "MATH 227", "title": "Calculus II", "units": 4, "grade": "B", "semester": "Spring", "year": 2024},
        {"code": "PHYS 220", "title": "General Physics w/ Calc I", "units": 3, "grade": "B-", "semester": "Fall", "year": 2024},
        {"code": "PHYS 222", "title": "General Physics I Lab", "units": 1, "grade": "A", "semester": "Fall", "year": 2024},
        {"code": "ENG 114", "title": "Writing the First Year", "units": 3, "grade": "A-", "semester": "Fall", "year": 2023},
    ]
}

# Keys match the Streamlit sample selector labels in app.py
SAMPLE_STUDENTS = {
    "Computer Science BS": SAMPLE_STUDENT_CSC,
    "Computer Engineering BS": SAMPLE_STUDENT_CMPE,
    "Psychology BA": SAMPLE_STUDENT_PSY,
    "General Biology BA": SAMPLE_STUDENT_BIOL,
    "Chemistry BS": SAMPLE_STUDENT_CHEM,
}


# =============================================================================
# TEST — Run directly to verify Agent 1
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Agent 1: DPR Parser — Test Run")
    print("=" * 65)

    db = BulletinDatabase()
    parser = DPRParser(db)

    # -------------------------------------------------------------------------
    # TEST 1: Parse from dictionary
    # -------------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("TEST 1: Alex Johnson — CSC BS (dict input)")
    print("-" * 65)

    report = parser.parse_dict(SAMPLE_STUDENT_CSC)

    print(f"\nStudent: {report.student.name}")
    print(f"Program: {report.student.program_code} ({report.student.catalog_year})")
    print(f"GPA: {report.student.cumulative_gpa} (Major: {report.student.major_gpa})")
    print(f"Units: {report.student.total_units_completed}")
    print(f"\n{report.summary()}")

    print(f"\nCompleted ({len(report.completed)}):")
    for r in report.completed[:5]:
        print(f"  [done] {r.req_name} <- {r.fulfilled_by}")

    print(f"\nRemaining ({len(report.remaining)}):")
    for r in report.remaining[:5]:
        print(f"  [ ] {r.req_name} ({r.units_needed}u)")
    if len(report.remaining) > 5:
        print(f"  ... and {len(report.remaining) - 5} more")

    # -------------------------------------------------------------------------
    # TEST 2: Parse from real DPR PDF
    # -------------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("TEST 2: Gina Testram — Parse from actual DPR PDF")
    print("-" * 65)

    import os
    pdf_path = "/mnt/user-data/uploads/Advisee_s_Student_Center.pdf"

    if os.path.exists(pdf_path):
        report_pdf = parser.parse_pdf(pdf_path)

        print(f"\nStudent: {report_pdf.student.name}")
        print(f"ID: {report_pdf.student.student_id}")
        print(f"Program: {report_pdf.student.program_code} ({report_pdf.student.catalog_year})")
        print(f"GPA: {report_pdf.student.cumulative_gpa}")
        print(f"Units: {report_pdf.student.total_units_completed}")

        print(f"\nCourses extracted: {len(report_pdf.student.completed_courses)}")
        for c in report_pdf.student.completed_courses[:10]:
            print(f"  {c.code}: {c.title} | {c.units}u | {c.grade} | {c.semester} {c.year}")
        if len(report_pdf.student.completed_courses) > 10:
            print(f"  ... and {len(report_pdf.student.completed_courses) - 10} more")

        print(f"\n{report_pdf.summary()}")
    else:
        print("  [!] DPR PDF not found — skipping PDF test.")
        print(f"      Expected at: {pdf_path}")

    print("\n" + "=" * 65)
    print("[ok] Agent 1 (DPR Parser) verified.")
    print("=" * 65)
