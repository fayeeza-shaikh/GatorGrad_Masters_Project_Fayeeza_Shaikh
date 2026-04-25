"""
SF State Bulletin Data - Degree Requirements
CSC 895/898 Culminating Experience Project

5 Majors x 6 Catalog Years = 30 Degree Programs
Source: bulletin.sfsu.edu

Majors:
1. Computer Science BS
2. Computer Engineering BS
3. Psychology BA
4. General Biology BA
5. Chemistry BS

Catalog Years: 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26

To add more catalog years:
1. Copy the most recent create_*_program function
2. Update catalog_year and note any requirement changes
3. Add to BulletinDatabase._load_all_programs()
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Course:
    """A course from the bulletin"""
    code: str
    title: str
    units: float
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class Requirement:
    """A degree requirement"""
    req_id: str
    name: str
    category: str          # "Major", "GE", "University"
    subcategory: str = ""
    units: float = 3.0
    courses: List[str] = field(default_factory=list)
    course_options: List[str] = field(default_factory=list)  # Choose from
    notes: str = ""


@dataclass
class DegreeProgram:
    """Complete degree requirements for a major + catalog year"""
    program_code: str
    program_name: str
    degree_type: str       # "BS" or "BA"
    catalog_year: str
    total_units: int
    major_requirements: List[Requirement] = field(default_factory=list)
    ge_requirements: List[Requirement] = field(default_factory=list)
    university_requirements: List[Requirement] = field(default_factory=list)
    ge_met_in_major: List[str] = field(default_factory=list)
    min_gpa_overall: float = 2.0
    min_gpa_major: float = 2.0


# =============================================================================
# GENERAL EDUCATION REQUIREMENTS
# NOTE: SF State adopted a new GE framework starting 2025-26.
#       2020-21 through 2024-25 use the old A/B/C/D/E area system.
#       2025-26 uses the new numbered area system (1A, 1B, 2, 3A, 3B, 4, 5A, 5B, 5C, 6).
# =============================================================================

def create_ge_requirements() -> List[Requirement]:
    """
    Standard GE requirements for 2020-21 through 2024-25 (old area system).
    Consistent across those catalog years for all majors.
    """
    return [
        # Area A - Communication (9 units)
        Requirement("GE_A1", "Area A1 - Oral Communication", "GE", "Area A", 3),
        Requirement("GE_A2", "Area A2 - Written Communication", "GE", "Area A", 3),
        Requirement("GE_A3", "Area A3 - Critical Thinking", "GE", "Area A", 3),

        # Area B - Science & Math (10 units)
        Requirement("GE_B1", "Area B1 - Physical Science", "GE", "Area B", 3),
        Requirement("GE_B2", "Area B2 - Life Science", "GE", "Area B", 3),
        Requirement("GE_B3", "Area B3 - Laboratory Science", "GE", "Area B", 1),
        Requirement("GE_B4", "Area B4 - Quantitative Reasoning", "GE", "Area B", 3),

        # Area C - Arts & Humanities (9 units)
        Requirement("GE_C1", "Area C1 - Arts", "GE", "Area C", 3),
        Requirement("GE_C2", "Area C2 - Humanities", "GE", "Area C", 3),
        Requirement("GE_C3", "Area C1/C2 - Arts or Humanities", "GE", "Area C", 3),

        # Area D - Social Sciences (9 units)
        Requirement("GE_D1", "Area D1 - Social Sciences", "GE", "Area D", 3),
        Requirement("GE_D2", "Area D2 - US History", "GE", "Area D", 3),
        Requirement("GE_D3", "Area D3 - US & CA Government", "GE", "Area D", 3),

        # Area E - Lifelong Learning (3 units)
        Requirement("GE_E", "Area E - Lifelong Learning", "GE", "Area E", 3),

        # Area F - Ethnic Studies (3 units)
        Requirement("GE_F", "Area F - Ethnic Studies", "GE", "Area F", 3),

        # Upper Division GE (9 units)
        Requirement("GE_UDB", "UD-B - Upper Division Science", "GE", "Upper Division", 3),
        Requirement("GE_UDC", "UD-C - Upper Division Arts/Humanities", "GE", "Upper Division", 3),
        Requirement("GE_UDD", "UD-D - Upper Division Social Sciences", "GE", "Upper Division", 3),
    ]


def create_ge_requirements_2025_26() -> List[Requirement]:
    """
    New GE framework adopted starting 2025-26.
    Replaces the old A/B/C/D/E area designations.
    """
    return [
        # Area 1 - Communication (9 units)
        Requirement("GE_1A", "Area 1A - English Composition", "GE", "Area 1", 3),
        Requirement("GE_1B", "Area 1B - Critical Thinking", "GE", "Area 1", 3),
        Requirement("GE_1C", "Area 1C - Oral Communication", "GE", "Area 1", 3),

        # Area 2 - Quantitative Reasoning (3 units)
        Requirement("GE_2", "Area 2 - Mathematical Concepts and Quantitative Reasoning", "GE", "Area 2", 3),

        # Area 3 - Arts & Humanities (6 units)
        Requirement("GE_3A", "Area 3A - Arts", "GE", "Area 3", 3),
        Requirement("GE_3B", "Area 3B - Humanities", "GE", "Area 3", 3),

        # Area 4 - Social & Behavioral Sciences (6 units)
        Requirement("GE_4", "Area 4 - Social and Behavioral Sciences", "GE", "Area 4", 6),

        # Area 5 - Science (7 units)
        Requirement("GE_5A", "Area 5A - Physical Science", "GE", "Area 5", 3),
        Requirement("GE_5B", "Area 5B - Biological Science", "GE", "Area 5", 3),
        Requirement("GE_5C", "Area 5C - Laboratory", "GE", "Area 5", 1),

        # Area 6 - Ethnic Studies (3 units)
        Requirement("GE_6", "Area 6 - Ethnic Studies", "GE", "Area 6", 3),

        # Upper Division GE (9 units)
        Requirement("GE_5UD", "Area 5UD/2UD - Upper Division Science or Math", "GE", "Upper Division", 3),
        Requirement("GE_3UD", "Area 3UD - Upper Division Arts or Humanities", "GE", "Upper Division", 3),
        Requirement("GE_4UD", "Area 4UD - Upper Division Social & Behavioral Sciences", "GE", "Upper Division", 3),
    ]


def create_university_requirements() -> List[Requirement]:
    """University requirements (SF State Studies) - consistent across all years."""
    return [
        Requirement("UNIV_AERM", "SF State Studies: American Ethnic & Racial Minorities", "University", "SF State Studies", 3),
        Requirement("UNIV_ES", "SF State Studies: Environmental Sustainability", "University", "SF State Studies", 3,
                    notes="Renamed to 'Environmental Sustainability and Climate Action' in 2025-26"),
        Requirement("UNIV_GP", "SF State Studies: Global Perspectives", "University", "SF State Studies", 3),
        Requirement("UNIV_SJ", "SF State Studies: Social Justice", "University", "SF State Studies", 3),
    ]


# =============================================================================
# 1. COMPUTER SCIENCE BS
# =============================================================================

def create_csc_bs_2020_21() -> DegreeProgram:
    """
    Computer Science BS - 2020-21 Catalog
    Total Major Units: 71 | Total Degree Units: ~120
    """
    math_physics = [
        Requirement("CSC_MATH226", "MATH 226 - Calculus I", "Major", "Math/Physics", 4, ["MATH 226"]),
        Requirement("CSC_MATH227", "MATH 227 - Calculus II", "Major", "Math/Physics", 4, ["MATH 227"]),
        Requirement("CSC_MATH324", "MATH 324 - Probability & Statistics with Computing", "Major", "Math/Physics", 3, ["MATH 324"]),
        Requirement("CSC_MATH325", "MATH 325 - Linear Algebra", "Major", "Math/Physics", 3, ["MATH 325"]),
        Requirement("CSC_PHYS220", "PHYS 220 - General Physics with Calculus I", "Major", "Math/Physics", 3, ["PHYS 220"]),
        Requirement("CSC_PHYS222", "PHYS 222 - General Physics I Laboratory", "Major", "Math/Physics", 1, ["PHYS 222"]),
        Requirement("CSC_PHYS230", "PHYS 230 - General Physics with Calculus II", "Major", "Math/Physics", 3, ["PHYS 230"]),
        Requirement("CSC_PHYS232", "PHYS 232 - General Physics II Laboratory", "Major", "Math/Physics", 1, ["PHYS 232"]),
    ]

    core_cs = [
        Requirement("CSC_210", "CSC 210 - Introduction to Computer Programming", "Major", "Core", 3, ["CSC 210"]),
        Requirement("CSC_211", "CSC 211 - Introduction to Software Lab", "Major", "Core", 1, ["CSC 211"]),
        Requirement("CSC_220", "CSC 220 - Data Structures", "Major", "Core", 3, ["CSC 220"]),
        Requirement("CSC_230", "CSC 230 - Discrete Mathematical Structures for CS", "Major", "Core", 3, ["CSC 230"]),
        Requirement("CSC_256", "CSC 256 - Machine Structures", "Major", "Core", 3, ["CSC 256"]),
        Requirement("CSC_300GW", "CSC 300GW - Ethics, Communication, and Tools (GWAR)", "Major", "Core", 3, ["CSC 300GW"]),
        Requirement("CSC_317", "CSC 317 - Introduction to Web Software Development", "Major", "Core", 3, ["CSC 317"]),
        Requirement("CSC_340", "CSC 340 - Programming Methodology", "Major", "Core", 3, ["CSC 340"]),
        Requirement("CSC_413", "CSC 413 - Software Development", "Major", "Core", 3, ["CSC 413"]),
    ]

    advanced_cs = [
        Requirement("CSC_415", "CSC 415 - Operating System Principles", "Major", "Advanced", 3, ["CSC 415"]),
        Requirement("CSC_510", "CSC 510 - Analysis of Algorithms I", "Major", "Advanced", 3, ["CSC 510"]),
        Requirement("CSC_600", "CSC 600 - Programming Paradigms and Languages", "Major", "Advanced", 3, ["CSC 600"]),
        Requirement("CSC_648", "CSC 648 - Software Engineering", "Major", "Advanced", 3, ["CSC 648"]),
    ]

    electives = [
        Requirement("CSC_ELEC", "Upper Division CS Electives", "Major", "Electives", 12,
                    course_options=["CSC 520", "CSC 615", "CSC 620", "CSC 621", "CSC 630", "CSC 631",
                                    "CSC 637", "CSC 641", "CSC 642", "CSC 645", "CSC 651", "CSC 656",
                                    "CSC 658", "CSC 664", "CSC 665", "CSC 667", "CSC 668", "CSC 675",
                                    "CSC 690", "CSC 698", "CSC 699", "MATH 400"],
                    notes="Select 4 courses (12 units). Senior presentation required."),
    ]

    return DegreeProgram(
        program_code="CSC_BS",
        program_name="Computer Science",
        degree_type="BS",
        catalog_year="2020-21",
        total_units=120,
        major_requirements=math_physics + core_cs + advanced_cs + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=[]
    )


def create_csc_bs_2021_22() -> DegreeProgram:
    """
    Computer Science BS - 2021-22 Catalog
    Changes from 2020-21:
    - Added CSC 508, CSC 652, MATH 425 to elective options
    - Clarified elective rules (at least 9 units must be CSC)
    """
    program = create_csc_bs_2020_21()
    program.catalog_year = "2021-22"

    for req in program.major_requirements:
        if req.req_id == "CSC_ELEC":
            req.course_options = [
                "CSC 508", "CSC 520", "CSC 615", "CSC 620", "CSC 621", "CSC 630",
                "CSC 631", "CSC 637", "CSC 641", "CSC 642", "CSC 645", "CSC 651",
                "CSC 652", "CSC 656", "CSC 658", "CSC 664", "CSC 665", "CSC 667",
                "CSC 668", "CSC 675", "CSC 690", "CSC 698", "CSC 699",
                "MATH 400", "MATH 425"
            ]
            req.notes = "Select 4 courses (12 units). At least 9 units must be CSC courses."

    return program


def create_csc_bs_2022_23() -> DegreeProgram:
    """
    Computer Science BS - 2022-23 Catalog
    Changes from 2021-22:
    - Total units 72 (same major structure)
    - CSC 637 removed from electives; no major structural changes
    - Elective rule: at least 9 units CSC; one grad course allowed (700+ level)
    """
    program = create_csc_bs_2021_22()
    program.catalog_year = "2022-23"
    return program


def create_csc_bs_2023_24() -> DegreeProgram:
    """
    Computer Science BS - 2023-24 Catalog
    Changes from 2022-23:
    - Total units increased to 74
    - Math/Physics: MATH 325 (4 units) replaced by MATH 225 (3 units) - Introduction to Linear Algebra
    - Core CS: CSC 210/211 replaced by CSC 101 (Introduction to Computing, 3 units)
              + CSC 215 (Intermediate Computer Programming, 4 units)
    - Advanced CS: reduced to 9 units (CSC 600 dropped from required; becomes elective option)
    - Electives: increased to 15 units (5 courses), at least 12 units must be CSC
    - Added: CSC 676, CSC 680 to elective options; MATH 448 added
    """
    math_physics = [
        Requirement("CSC_MATH225", "MATH 225 - Introduction to Linear Algebra", "Major", "Math/Physics", 3, ["MATH 225"]),
        Requirement("CSC_MATH226", "MATH 226 - Calculus I", "Major", "Math/Physics", 4, ["MATH 226"]),
        Requirement("CSC_MATH227", "MATH 227 - Calculus II", "Major", "Math/Physics", 4, ["MATH 227"]),
        Requirement("CSC_MATH324", "MATH 324 - Probability & Statistics with Computing", "Major", "Math/Physics", 3, ["MATH 324"]),
        Requirement("CSC_PHYS220", "PHYS 220 - General Physics with Calculus I", "Major", "Math/Physics", 3, ["PHYS 220"]),
        Requirement("CSC_PHYS222", "PHYS 222 - General Physics I Laboratory", "Major", "Math/Physics", 1, ["PHYS 222"]),
        Requirement("CSC_PHYS230", "PHYS 230 - General Physics with Calculus II", "Major", "Math/Physics", 3, ["PHYS 230"]),
        Requirement("CSC_PHYS232", "PHYS 232 - General Physics II Laboratory", "Major", "Math/Physics", 1, ["PHYS 232"]),
    ]

    core_cs = [
        Requirement("CSC_101", "CSC 101 - Introduction to Computing", "Major", "Core", 3, ["CSC 101"]),
        Requirement("CSC_215", "CSC 215 - Intermediate Computer Programming", "Major", "Core", 4, ["CSC 215"]),
        Requirement("CSC_220", "CSC 220 - Data Structures", "Major", "Core", 3, ["CSC 220"]),
        Requirement("CSC_230", "CSC 230 - Discrete Mathematical Structures for CS", "Major", "Core", 3, ["CSC 230"]),
        Requirement("CSC_256", "CSC 256 - Machine Structures", "Major", "Core", 3, ["CSC 256"]),
        Requirement("CSC_300GW", "CSC 300GW - Ethics, Communication, and Tools (GWAR)", "Major", "Core", 3, ["CSC 300GW"]),
        Requirement("CSC_317", "CSC 317 - Introduction to Web Software Development", "Major", "Core", 3, ["CSC 317"]),
        Requirement("CSC_340", "CSC 340 - Programming Methodology", "Major", "Core", 3, ["CSC 340"]),
        Requirement("CSC_413", "CSC 413 - Software Development", "Major", "Core", 3, ["CSC 413"]),
    ]

    advanced_cs = [
        Requirement("CSC_415", "CSC 415 - Operating System Principles", "Major", "Advanced", 3, ["CSC 415"]),
        Requirement("CSC_510", "CSC 510 - Analysis of Algorithms I", "Major", "Advanced", 3, ["CSC 510"]),
        Requirement("CSC_648", "CSC 648 - Software Engineering", "Major", "Advanced", 3, ["CSC 648"]),
    ]

    electives = [
        Requirement("CSC_ELEC", "Upper Division CS Electives", "Major", "Electives", 15,
                    course_options=[
                        "CSC 508", "CSC 520", "CSC 600", "CSC 615", "CSC 620", "CSC 621",
                        "CSC 631", "CSC 641", "CSC 642", "CSC 645", "CSC 651", "CSC 652",
                        "CSC 656", "CSC 658", "CSC 664", "CSC 665", "CSC 667", "CSC 668",
                        "CSC 675", "CSC 676", "CSC 680", "CSC 690", "CSC 698", "CSC 699",
                        "MATH 400", "MATH 425", "MATH 448"
                    ],
                    notes="Select 5 courses (15 units). At least 12 units must be CSC. One grad course (700+) allowed."),
    ]

    return DegreeProgram(
        program_code="CSC_BS",
        program_name="Computer Science",
        degree_type="BS",
        catalog_year="2023-24",
        total_units=120,
        major_requirements=math_physics + core_cs + advanced_cs + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=[]
    )


def create_csc_bs_2024_25() -> DegreeProgram:
    """
    Computer Science BS - 2024-25 Catalog
    Changes from 2023-24:
    - Added grade requirement: C or better in CSC 510 and CSC 648
    - Added CSC 647 (Intro to Quantum Computing), CSC 649 (Search Engines),
      CSC 657 (Bioinformatics Computing), CSC 671 (Deep Learning) to electives
    - Removed CSC 508 from elective list
    - Exception list for excluded courses: CSC 601, CSC 602, CSC 648, CSC 694
    """
    program = create_csc_bs_2023_24()
    program.catalog_year = "2024-25"

    for req in program.major_requirements:
        if req.req_id == "CSC_ELEC":
            req.course_options = [
                "CSC 520", "CSC 600", "CSC 615", "CSC 620", "CSC 621", "CSC 630",
                "CSC 631", "CSC 641", "CSC 642", "CSC 645", "CSC 647", "CSC 649",
                "CSC 651", "CSC 652", "CSC 656", "CSC 657", "CSC 658", "CSC 664",
                "CSC 665", "CSC 667", "CSC 668", "CSC 671", "CSC 675", "CSC 676",
                "CSC 680", "CSC 690", "CSC 698", "CSC 699",
                "MATH 400", "MATH 425", "MATH 448"
            ]
            req.notes = (
                "Select 5 courses (15 units). At least 12 units must be CSC. "
                "One grad course (700+) allowed. Excluded: CSC 601, 602, 648, 694. "
                "C or better required in CSC 510 and CSC 648."
            )

    return program


def create_csc_bs_2025_26() -> DegreeProgram:
    """
    Computer Science BS - 2025-26 Catalog
    Changes from 2024-25:
    - GE framework changed to new numbered system (1A, 1B, 1C, 2, 3A, 3B, 4, 5A, 5B, 5C, 6)
    - CSC 615 renamed: 'UNIX Programming' -> 'Embedded Linux Systems and Physical Computing'
    - CSC 630 (Computer Graphics Systems Design) added back to electives
    - CSC 649 (Search Engines) removed from elective list
    - Otherwise same 74-unit structure
    """
    program = create_csc_bs_2024_25()
    program.catalog_year = "2025-26"
    program.ge_requirements = create_ge_requirements_2025_26()

    for req in program.major_requirements:
        if req.req_id == "CSC_ELEC":
            req.course_options = [
                "CSC 520", "CSC 600", "CSC 615", "CSC 620", "CSC 621", "CSC 630",
                "CSC 631", "CSC 641", "CSC 642", "CSC 645", "CSC 647",
                "CSC 651", "CSC 652", "CSC 656", "CSC 657", "CSC 658", "CSC 664",
                "CSC 665", "CSC 667", "CSC 668", "CSC 671", "CSC 675", "CSC 676",
                "CSC 680", "CSC 690", "CSC 698", "CSC 699",
                "MATH 400", "MATH 425", "MATH 448"
            ]
            req.notes = (
                "Select 5 courses (15 units). At least 12 units must be CSC. "
                "One grad course (700+) allowed. Excluded: CSC 601, 602, 648, 694. "
                "C or better required in CSC 510 and CSC 648."
            )

    return program


# =============================================================================
# 2. COMPUTER ENGINEERING BS
# =============================================================================

def create_cmpe_bs_2020_21() -> DegreeProgram:
    """
    Computer Engineering BS - 2020-21 Catalog
    Total Major Units: 92 | Total Degree Units: 128
    GE met in major: A3 (via ENGR 205+213), UD-B (via ENGR 300+301/302)
    """
    math_science = [
        Requirement("CMPE_CHEM", "CHEM 115 or CHEM 180 - Chemistry", "Major", "Math/Science", 5,
                    course_options=["CHEM 115", "CHEM 180"]),
        Requirement("CMPE_MATH226", "MATH 226 - Calculus I", "Major", "Math/Science", 4, ["MATH 226"]),
        Requirement("CMPE_MATH227", "MATH 227 - Calculus II", "Major", "Math/Science", 4, ["MATH 227"]),
        Requirement("CMPE_MATH228", "MATH 228 - Calculus III", "Major", "Math/Science", 4, ["MATH 228"]),
        Requirement("CMPE_MATH245", "MATH 245 - Diff Equations & Linear Algebra", "Major", "Math/Science", 3, ["MATH 245"]),
        Requirement("CMPE_PHYS220", "PHYS 220/222 - Physics I with Lab", "Major", "Math/Science", 4, ["PHYS 220", "PHYS 222"]),
        Requirement("CMPE_PHYS230", "PHYS 230/232 - Physics II with Lab", "Major", "Math/Science", 4, ["PHYS 230", "PHYS 232"]),
    ]

    csc_reqs = [
        Requirement("CMPE_CSC210", "CSC 210 - Introduction to Computer Programming", "Major", "CSC", 3, ["CSC 210"]),
        Requirement("CMPE_CSC220", "CSC 220 - Data Structures", "Major", "CSC", 3, ["CSC 220"]),
        Requirement("CMPE_CSC230", "CSC 230 - Discrete Mathematical Structures", "Major", "CSC", 3, ["CSC 230"]),
        Requirement("CMPE_CSC340", "CSC 340 - Programming Methodology", "Major", "CSC", 3, ["CSC 340"]),
        Requirement("CMPE_CSC413", "CSC 413 - Software Development", "Major", "CSC", 3, ["CSC 413"]),
    ]

    engr_core = [
        Requirement("CMPE_ENGR100", "ENGR 100 - Introduction to Engineering", "Major", "ENGR Core", 1, ["ENGR 100"]),
        Requirement("CMPE_ENGR121", "ENGR 121 - Gateway to Computer Engineering", "Major", "ENGR Core", 1, ["ENGR 121"]),
        Requirement("CMPE_ENGR205", "ENGR 205 - Electric Circuits", "Major", "ENGR Core", 3, ["ENGR 205"]),
        Requirement("CMPE_ENGR206", "ENGR 206 - Circuits and Instrumentation Laboratory", "Major", "ENGR Core", 1, ["ENGR 206"]),
        Requirement("CMPE_ENGR212", "ENGR 212 - Introduction to Unix and Linux", "Major", "ENGR Core", 2, ["ENGR 212"]),
        Requirement("CMPE_ENGR213", "ENGR 213 - Introduction to C Programming", "Major", "ENGR Core", 3, ["ENGR 213"]),
        Requirement("CMPE_ENGR300", "ENGR 300 - Engineering Experimentation", "Major", "ENGR Core", 3, ["ENGR 300"]),
        Requirement("CMPE_ENGR301", "ENGR 301 - Microelectronics Laboratory", "Major", "ENGR Core", 1, ["ENGR 301"]),
        Requirement("CMPE_ENGR305", "ENGR 305 - Linear Systems Analysis", "Major", "ENGR Core", 3, ["ENGR 305"]),
        Requirement("CMPE_ENGR353", "ENGR 353 - Microelectronics", "Major", "ENGR Core", 3, ["ENGR 353"]),
        Requirement("CMPE_ENGR356", "ENGR 356 - Digital Design", "Major", "ENGR Core", 3, ["ENGR 356"]),
        Requirement("CMPE_ENGR357", "ENGR 357 - Digital Design Laboratory", "Major", "ENGR Core", 1, ["ENGR 357"]),
        Requirement("CMPE_ENGR378", "ENGR 378 - Digital Systems Design", "Major", "ENGR Core", 3, ["ENGR 378"]),
        Requirement("CMPE_ENGR451", "ENGR 451 - Digital Signal Processing", "Major", "ENGR Core", 4, ["ENGR 451"]),
        Requirement("CMPE_ENGR456", "ENGR 456 - Computer Systems", "Major", "ENGR Core", 3, ["ENGR 456"]),
        Requirement("CMPE_ENGR476", "ENGR 476 - Computer Communications Networks", "Major", "ENGR Core", 3, ["ENGR 476"]),
        Requirement("CMPE_ENGR478", "ENGR 478 - Design with Microprocessors", "Major", "ENGR Core", 4, ["ENGR 478"]),
        Requirement("CMPE_ENGR696", "ENGR 696 - Engineering Design Project I", "Major", "ENGR Core", 1, ["ENGR 696"]),
        Requirement("CMPE_ENGR697", "ENGR 697GW - Engineering Design Project II (GWAR)", "Major", "ENGR Core", 2, ["ENGR 697GW"]),
    ]

    electives = [
        Requirement("CMPE_ELEC", "Upper Division Electives", "Major", "Electives", 6,
                    course_options=[
                        "CSC 415", "CSC 510", "CSC 645", "CSC 648", "CSC 667", "CSC 668",
                        "ENGR 306", "ENGR 350", "ENGR 442", "ENGR 446", "ENGR 447", "ENGR 449",
                        "ENGR 453", "ENGR 491", "ENGR 492", "ENGR 498", "ENGR 610",
                        "ENGR 844", "ENGR 845", "ENGR 848", "ENGR 849", "ENGR 850",
                        "ENGR 851", "ENGR 852", "ENGR 853", "ENGR 854", "ENGR 855",
                        "ENGR 856", "ENGR 858", "ENGR 868", "ENGR 869", "ENGR 870", "ENGR 890"
                    ],
                    notes="6-7 units required. Must have advisor approval. GPA 3.0+ can take 800-level courses."),
    ]

    return DegreeProgram(
        program_code="CMPE_BS",
        program_name="Computer Engineering",
        degree_type="BS",
        catalog_year="2020-21",
        total_units=128,
        major_requirements=math_science + csc_reqs + engr_core + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=["GE_A3", "GE_UDB"]
    )


def create_cmpe_bs_2021_22() -> DegreeProgram:
    """Computer Engineering BS - 2021-22 (identical to 2020-21)"""
    program = create_cmpe_bs_2020_21()
    program.catalog_year = "2021-22"
    return program


def create_cmpe_bs_2022_23() -> DegreeProgram:
    """
    Computer Engineering BS - 2022-23 Catalog
    Changes from 2021-22:
    - Same 92-unit structure, same course list
    - CHEM 115 unit note: listed as 3-5 units (CHEM 180 remains option)
    """
    program = create_cmpe_bs_2021_22()
    program.catalog_year = "2022-23"
    return program


def create_cmpe_bs_2023_24() -> DegreeProgram:
    """
    Computer Engineering BS - 2023-24 Catalog
    Major restructure from 2022-23:
    - Total units: 93 minimum
    - GE also met: Area E (by ENGR 100, now 3 units)
    - ENGR 100 increased from 1 to 3 units
    - ENGR 121 removed
    - ENGR 300, ENGR 301, ENGR 353 removed from core
    - Added: ENGR 214 (C Programming Lab, 1 unit), ENGR 221 (Data Structures in Python, 4 units),
             ENGR 281 (Probability and Statistics, 2 units), ENGR 340 (Programming Methodology, 4 units),
             ENGR 354 (Electronics for CE, 4 units), ENGR 413 (3 units), ENGR 498 (4 units)
    - CSC courses in core removed; replaced by ENGR equivalents
    - Elective list updated: added ENGR 415 (Mechatronics), ENGR 859 (On-Device ML),
      ENGR 871, ENGR 890 renamed; removed ENGR 306, 350, 491, 498, 610, 854, 855, 870
    - CSC 652 added to electives
    """
    math_science = [
        Requirement("CMPE_CHEM", "CHEM 115 or CHEM 180 - Chemistry", "Major", "Math/Science", 4,
                    course_options=["CHEM 115", "CHEM 180"],
                    notes="CHEM 115: 3-5 units; CHEM 180: 3 units"),
        Requirement("CMPE_MATH226", "MATH 226 - Calculus I", "Major", "Math/Science", 4, ["MATH 226"]),
        Requirement("CMPE_MATH227", "MATH 227 - Calculus II", "Major", "Math/Science", 4, ["MATH 227"]),
        Requirement("CMPE_MATH228", "MATH 228 - Calculus III", "Major", "Math/Science", 4, ["MATH 228"]),
        Requirement("CMPE_MATH245", "MATH 245 - Diff Equations & Linear Algebra", "Major", "Math/Science", 3, ["MATH 245"]),
        Requirement("CMPE_PHYS220", "PHYS 220/222 - Physics I with Lab", "Major", "Math/Science", 4, ["PHYS 220", "PHYS 222"]),
        Requirement("CMPE_PHYS230", "PHYS 230/232 - Physics II with Lab", "Major", "Math/Science", 4, ["PHYS 230", "PHYS 232"]),
    ]

    lower_engr = [
        Requirement("CMPE_ENGR100", "ENGR 100 - Introduction to Engineering", "Major", "Lower ENGR", 3, ["ENGR 100"],
                    notes="Satisfies GE Area E (Lifelong Learning)"),
        Requirement("CMPE_ENGR205", "ENGR 205 - Electric Circuits", "Major", "Lower ENGR", 3, ["ENGR 205"]),
        Requirement("CMPE_ENGR206", "ENGR 206 - Circuits and Instrumentation Laboratory", "Major", "Lower ENGR", 1, ["ENGR 206"]),
        Requirement("CMPE_ENGR212", "ENGR 212 - Introduction to Unix and Linux", "Major", "Lower ENGR", 2, ["ENGR 212"]),
        Requirement("CMPE_ENGR213", "ENGR 213 - Introduction to C Programming", "Major", "Lower ENGR", 3, ["ENGR 213"]),
        Requirement("CMPE_ENGR214", "ENGR 214 - C Programming Laboratory", "Major", "Lower ENGR", 1, ["ENGR 214"]),
        Requirement("CMPE_ENGR221", "ENGR 221 - Data Structures and Algorithms in Python", "Major", "Lower ENGR", 4, ["ENGR 221"]),
        Requirement("CMPE_ENGR281", "ENGR 281 - Probability and Statistics for Engineers", "Major", "Lower ENGR", 2, ["ENGR 281"]),
    ]

    upper_engr = [
        Requirement("CMPE_ENGR305", "ENGR 305 - Linear Systems Analysis", "Major", "Upper ENGR", 3, ["ENGR 305"]),
        Requirement("CMPE_ENGR340", "ENGR 340 - Programming Methodology for Engineers", "Major", "Upper ENGR", 4, ["ENGR 340"]),
        Requirement("CMPE_ENGR354", "ENGR 354 - Electronics for Computer Engineers", "Major", "Upper ENGR", 4, ["ENGR 354"]),
        Requirement("CMPE_ENGR356", "ENGR 356 - Digital Design", "Major", "Upper ENGR", 3, ["ENGR 356"]),
        Requirement("CMPE_ENGR357", "ENGR 357 - Digital Design Laboratory", "Major", "Upper ENGR", 1, ["ENGR 357"]),
        Requirement("CMPE_ENGR378", "ENGR 378 - Digital Systems Design", "Major", "Upper ENGR", 3, ["ENGR 378"]),
        Requirement("CMPE_ENGR413", "ENGR 413", "Major", "Upper ENGR", 3, ["ENGR 413"]),
        Requirement("CMPE_ENGR451", "ENGR 451 - Digital Signal Processing", "Major", "Upper ENGR", 4, ["ENGR 451"]),
        Requirement("CMPE_ENGR456", "ENGR 456 - Computer Systems", "Major", "Upper ENGR", 3, ["ENGR 456"]),
        Requirement("CMPE_ENGR476", "ENGR 476 - Computer Communications Networks", "Major", "Upper ENGR", 3, ["ENGR 476"]),
        Requirement("CMPE_ENGR478", "ENGR 478 - Design with Microprocessors", "Major", "Upper ENGR", 4, ["ENGR 478"]),
        Requirement("CMPE_ENGR498", "ENGR 498 - Advanced Design with Microcontrollers", "Major", "Upper ENGR", 4, ["ENGR 498"]),
        Requirement("CMPE_ENGR696", "ENGR 696 - Engineering Design Project I", "Major", "Upper ENGR", 1, ["ENGR 696"]),
        Requirement("CMPE_ENGR697", "ENGR 697GW - Engineering Design Project II (GWAR)", "Major", "Upper ENGR", 2, ["ENGR 697GW"]),
    ]

    electives = [
        Requirement("CMPE_ELEC", "Upper Division Electives", "Major", "Electives", 6,
                    course_options=[
                        "CSC 415", "CSC 510", "CSC 645", "CSC 648", "CSC 652", "CSC 667", "CSC 668",
                        "ENGR 415", "ENGR 442", "ENGR 446", "ENGR 447", "ENGR 449",
                        "ENGR 453", "ENGR 491", "ENGR 492",
                        "ENGR 844", "ENGR 845", "ENGR 848", "ENGR 849", "ENGR 850",
                        "ENGR 851", "ENGR 852", "ENGR 853", "ENGR 854", "ENGR 855",
                        "ENGR 856", "ENGR 858", "ENGR 859", "ENGR 868", "ENGR 869",
                        "ENGR 870", "ENGR 871", "ENGR 890"
                    ],
                    notes="6 units minimum. Must have advisor approval. GPA 3.0+ can take 800-level courses."),
    ]

    return DegreeProgram(
        program_code="CMPE_BS",
        program_name="Computer Engineering",
        degree_type="BS",
        catalog_year="2023-24",
        total_units=128,
        major_requirements=math_science + lower_engr + upper_engr + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=["GE_A3", "GE_E", "GE_UDB"]
    )


def create_cmpe_bs_2024_25() -> DegreeProgram:
    """
    Computer Engineering BS - 2024-25 Catalog
    Changes from 2023-24:
    - ENGR 413 now named 'Artificial Intelligence in Engineering'
    - UD-B now satisfied by ENGR 478 (instead of ENGR 300+301/302)
    - CHEM 115 unit note updated: 3-4 units
    - ENGR 491 removed from elective list; ENGR 854/855 still listed but partial
    - Otherwise same 93-unit structure
    """
    program = create_cmpe_bs_2023_24()
    program.catalog_year = "2024-25"

    for req in program.major_requirements:
        if req.req_id == "CMPE_ENGR413":
            req.name = "ENGR 413 - Artificial Intelligence in Engineering"

    return program


def create_cmpe_bs_2025_26() -> DegreeProgram:
    """
    Computer Engineering BS - 2025-26 Catalog
    Changes from 2024-25:
    - GE framework changed to new numbered system
    - GE met in major: 1B (Critical Thinking) by ENGR 205+213; 5UD by ENGR 478
    - ENGR 871 Advanced Electrical Power Systems removed from electives
    - Program description substantially expanded (added career section, program webpage)
    - PLO 5 wording updated: 'inclusive environment' → 'collaborative environment'
    """
    program = create_cmpe_bs_2024_25()
    program.catalog_year = "2025-26"
    program.ge_requirements = create_ge_requirements_2025_26()
    program.ge_met_in_major = ["GE_1B", "GE_5UD"]

    for req in program.major_requirements:
        if req.req_id == "CMPE_ELEC":
            req.course_options = [
                "CSC 415", "CSC 510", "CSC 645", "CSC 648", "CSC 652", "CSC 667", "CSC 668",
                "ENGR 415", "ENGR 442", "ENGR 446", "ENGR 447", "ENGR 449",
                "ENGR 453", "ENGR 492",
                "ENGR 844", "ENGR 845", "ENGR 848", "ENGR 849", "ENGR 850",
                "ENGR 851", "ENGR 852", "ENGR 853",
                "ENGR 856", "ENGR 858", "ENGR 859", "ENGR 868", "ENGR 869",
                "ENGR 870", "ENGR 890"
            ]

    return program


# =============================================================================
# 3. PSYCHOLOGY BA
# =============================================================================

def create_psy_ba_2020_21() -> DegreeProgram:
    """
    Psychology BA - 2020-21 Catalog
    Total Major Units: 41 | Total Degree Units: ~120
    """
    core = [
        Requirement("PSY_200", "PSY 200 - General Psychology", "Major", "Core", 3, ["PSY 200"],
                    notes="Prerequisite for all UD psychology courses. Grade C or better required."),
        Requirement("PSY_303", "PSY 303 - Psychology: The Major and the Profession", "Major", "Core", 1, ["PSY 303"],
                    notes="Online course. CR grade required."),
        Requirement("PSY_371", "PSY 371 - Psychological Statistics", "Major", "Core", 3, ["PSY 371"],
                    notes="Prerequisite: PSY 171 or any QR course. Grade C or better required."),
        Requirement("PSY_400", "PSY 400 - Introduction to Research in Psychology", "Major", "Core", 3, ["PSY 400"],
                    notes="Grade C or better required."),
        Requirement("PSY_305GW", "PSY 305GW - Writing in Psychology (GWAR)", "Major", "Core", 3, ["PSY 305GW"],
                    notes="Satisfies GWAR. Grade C or better required."),
        Requirement("PSY_690", "PSY 690 - Future Directions for Psychology Majors", "Major", "Core", 1, ["PSY 690"],
                    notes="Online course. CR grade required."),
    ]

    area1_options = ["PSY 432", "PSY 491", "PSY 492", "PSY 493", "PSY 494",
                     "PSY 495", "PSY 498", "PSY 531", "PSY 581", "PSY 582"]
    area2_options = ["PSY 430", "PSY 431", "PSY 433", "PSY 434", "PSY 435",
                     "PSY 436", "PSY 442", "PSY 451", "PSY 452", "PSY 521"]
    area3_options = ["PSY 440", "PSY 441", "PSY 455", "PSY 456", "PSY 461", "PSY 462",
                     "PSY 463", "PSY 465", "PSY 466", "PSY 472", "PSY 474", "PSY 475",
                     "PSY 525", "PSY 547", "PSY 558", "PSY 559", "PSY 645"]

    basic = [
        Requirement("PSY_AREA1", "Area 1: Basic Psychological Processes", "Major", "Basic Courses", 6,
                    course_options=area1_options,
                    notes="Choose 2 courses"),
        Requirement("PSY_AREA2", "Area 2: Development & Individual Differences", "Major", "Basic Courses", 6,
                    course_options=area2_options,
                    notes="Choose 2 courses"),
        Requirement("PSY_AREA3", "Area 3: Social, Cultural, Organizational", "Major", "Basic Courses", 6,
                    course_options=area3_options,
                    notes="Choose 2 courses"),
    ]

    all_elective_options = area1_options + area2_options + area3_options + [
        "PSY 300", "PSY 320", "PSY 330", "PSY 443", "PSY 450", "PSY 571",
        "PSY 601", "PSY 668", "PSY 680", "PSY 685", "PSY 693", "PSY 694",
        "PSY 697", "PSY 698", "PSY 699"
    ]

    electives = [
        Requirement("PSY_ELEC", "Psychology Electives", "Major", "Electives", 9,
                    course_options=all_elective_options,
                    notes="Choose 3 courses from Areas 1-3 (not used for Basic) or additional UD psychology courses."),
    ]

    complementary = [
        Requirement("PSY_COMP", "Complementary Studies", "Major", "Complementary", 12,
                    notes="12 units from non-PSY prefix courses. Options: ANTH, BIO, CAD, CJ, CSC, COUN, EDUC, ETHS, PHIL, SOC, or foreign language, Study Abroad, or certificate courses."),
    ]

    return DegreeProgram(
        program_code="PSY_BA",
        program_name="Psychology",
        degree_type="BA",
        catalog_year="2020-21",
        total_units=120,
        major_requirements=core + basic + electives + complementary,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=[]
    )


def create_psy_ba_2021_22() -> DegreeProgram:
    """
    Psychology BA - 2021-22 Catalog
    Changes from 2020-21:
    - Added PSY 464 (Psychology of Career Pursuit) and PSY 540 (Decision Making) to Area 3
    - Unit range clarified as 41-47
    """
    program = create_psy_ba_2020_21()
    program.catalog_year = "2021-22"

    for req in program.major_requirements:
        if req.req_id == "PSY_AREA3":
            req.course_options = [
                "PSY 440", "PSY 441", "PSY 455", "PSY 456", "PSY 461", "PSY 462",
                "PSY 463", "PSY 464", "PSY 465", "PSY 466", "PSY 472", "PSY 474",
                "PSY 475", "PSY 525", "PSY 540", "PSY 547", "PSY 558", "PSY 559", "PSY 645"
            ]

    return program


def create_psy_ba_2022_23() -> DegreeProgram:
    """
    Psychology BA - 2022-23 Catalog
    Changes from 2021-22:
    - Program impaction details added (350-400 students/year, applications Oct 1-Nov 30)
    - Added PSY 490 (Introduction to Data Science for Psychology) to Area 1
    - Area 2: PSY 434 (Aging) still listed; PSY 452 renamed to 'Abnormal Psychology: Minor Variants'
    - PSY 601 (Theoretical Backgrounds) added to elective-only courses
    """
    program = create_psy_ba_2021_22()
    program.catalog_year = "2022-23"

    for req in program.major_requirements:
        if req.req_id == "PSY_AREA1":
            req.course_options = [
                "PSY 432", "PSY 490", "PSY 491", "PSY 492", "PSY 493", "PSY 494",
                "PSY 495", "PSY 498", "PSY 531", "PSY 581", "PSY 582"
            ]

    return program


def create_psy_ba_2023_24() -> DegreeProgram:
    """
    Psychology BA - 2023-24 Catalog
    Changes from 2022-23:
    - Area 2: PSY 434 (Aging) removed; PSY 435 renamed to 'Developmental Psychopathology';
      PSY 452 renamed to 'Clinical Psychopathology'
    - Impaction section removed from bulletin page
    - PSY 601 removed from elective list
    - PSY 668 (Leadership) still available as elective
    """
    program = create_psy_ba_2022_23()
    program.catalog_year = "2023-24"

    for req in program.major_requirements:
        if req.req_id == "PSY_AREA2":
            req.course_options = [
                "PSY 430", "PSY 431", "PSY 433", "PSY 435", "PSY 436",
                "PSY 442", "PSY 451", "PSY 452", "PSY 521"
            ]
            req.notes = "Choose 2 courses. PSY 435 = Developmental Psychopathology; PSY 452 = Clinical Psychopathology"

    return program


def create_psy_ba_2024_25() -> DegreeProgram:
    """
    Psychology BA - 2024-25 Catalog
    Changes from 2023-24:
    - PSY/SXS 436 renamed: 'The Development of Femaleness and Maleness' ->
      'The Development of Gender Identities'
    - PSY 463 renamed: 'Human Factors' -> 'Human Factors in Technology'
    - Otherwise identical structure
    """
    program = create_psy_ba_2023_24()
    program.catalog_year = "2024-25"
    return program


def create_psy_ba_2025_26() -> DegreeProgram:
    """
    Psychology BA - 2025-26 Catalog
    Changes from 2024-25:
    - GE framework changed to new numbered system
    - Unit minimum clarified: 41 units minimum
    - PLO reordered (Professional Development listed first)
    - Electives: PSY 601 removed; PSY 453 (Psychology of Death and Dying) added;
      PSY 698 renamed 'Honors Project in Psychology'; PSY 668 removed
    - PSY 330 note: 'Students may not use PSY 330 if taken PSY 431' footnote removed
    """
    program = create_psy_ba_2024_25()
    program.catalog_year = "2025-26"
    program.ge_requirements = create_ge_requirements_2025_26()

    for req in program.major_requirements:
        if req.req_id == "PSY_ELEC":
            area1 = ["PSY 432", "PSY 490", "PSY 491", "PSY 492", "PSY 493", "PSY 494",
                     "PSY 495", "PSY 498", "PSY 531", "PSY 581", "PSY 582"]
            area2 = ["PSY 430", "PSY 431", "PSY 433", "PSY 435", "PSY 436",
                     "PSY 442", "PSY 451", "PSY 452", "PSY 521"]
            area3 = ["PSY 440", "PSY 441", "PSY 455", "PSY 456", "PSY 461", "PSY 462",
                     "PSY 463", "PSY 464", "PSY 465", "PSY 466", "PSY 472", "PSY 474",
                     "PSY 475", "PSY 525", "PSY 540", "PSY 547", "PSY 558", "PSY 559", "PSY 645"]
            req.course_options = area1 + area2 + area3 + [
                "PSY 300", "PSY 320", "PSY 330", "PSY 443", "PSY 450", "PSY 453",
                "PSY 571", "PSY 680", "PSY 685", "PSY 693", "PSY 694",
                "PSY 697", "PSY 698", "PSY 699"
            ]
            req.notes = "Choose 3 courses. PSY 698 = Honors Project in Psychology in 2025-26."

    return program


# =============================================================================
# 4. GENERAL BIOLOGY BA
# =============================================================================

def create_biol_ba_2020_21() -> DegreeProgram:
    """
    General Biology BA - 2020-21 Catalog
    Total Major Units: 49-64 | Total Degree Units: ~120
    GE met in major: B1 (CHEM 130/233), B2+B3 (BIOL 240), UD-B (BIOL 355)
    """
    lower_div = [
        Requirement("BIOL_230", "BIOL 230 - Introductory Biology I", "Major", "Lower Division", 5, ["BIOL 230"]),
        Requirement("BIOL_240", "BIOL 240 - Introductory Biology II", "Major", "Lower Division", 5, ["BIOL 240"]),
        Requirement("BIOL_CHEM115", "CHEM 115 - General Chemistry I", "Major", "Lower Division", 5, ["CHEM 115"]),
        Requirement("BIOL_CHEM130", "CHEM 130 - General Organic Chemistry", "Major", "Lower Division", 3, ["CHEM 130"],
                    notes="CHEM 233 also acceptable"),
        Requirement("BIOL_CHEM215", "CHEM 215 - General Chemistry II", "Major", "Lower Division", 3, ["CHEM 215"],
                    notes="CHEM 216 recommended"),
        Requirement("BIOL_MATH", "MATH 124 or MATH 226", "Major", "Lower Division", 4,
                    course_options=["MATH 124", "MATH 226"],
                    notes="Elementary Statistics or Calculus I"),
        Requirement("BIOL_PHYS111", "PHYS 111 - General Physics I", "Major", "Lower Division", 3, ["PHYS 111"]),
        Requirement("BIOL_PHYS112", "PHYS 112 - General Physics I Laboratory", "Major", "Lower Division", 1, ["PHYS 112"]),
        Requirement("BIOL_PHYS121", "PHYS 121 - General Physics II", "Major", "Lower Division", 3, ["PHYS 121"]),
        Requirement("BIOL_PHYS122", "PHYS 122 - General Physics II Laboratory", "Major", "Lower Division", 1, ["PHYS 122"]),
    ]

    upper_core = [
        Requirement("BIOL_355", "BIOL 355 - Genetics", "Major", "Upper Division Core", 3, ["BIOL 355"]),
        Requirement("BIOL_PHYSIO", "Physiology Course", "Major", "Upper Division Core", 3,
                    course_options=["BIOL 442", "BIOL 525", "BIOL 612", "BIOL 630"],
                    notes="Choose 1: Microbial, Plant, Human, or Animal Physiology"),
        Requirement("BIOL_CELL", "Cell Biology Course", "Major", "Upper Division Core", 3,
                    course_options=["BIOL 350", "BIOL 358", "BIOL 401", "BIOL 435", "BIOL 453", "CHEM 349"],
                    notes="Choose 1: Cell Bio, Forensic Genetics, Microbiology, Immunology, Parasitology, or Biochemistry"),
        Requirement("BIOL_LAB", "Physiology/Cell Biology Laboratory", "Major", "Upper Division Core", 2,
                    course_options=["BIOL 351GW", "BIOL 402GW", "BIOL 436", "BIOL 443", "BIOL 454",
                                    "BIOL 526", "BIOL 613GW", "BIOL 631GW"],
                    notes="Choose 1 lab associated with selected Physiology or Cell Biology course"),
        Requirement("BIOL_ECOL", "Ecology Course", "Major", "Upper Division Core", 4,
                    course_options=["BIOL 482", "BIOL 490", "BIOL 529GW", "BIOL 532", "BIOL 534",
                                    "BIOL 580", "BIOL 582", "BIOL 585", "BIOL 586GW"],
                    notes="Choose 1 ecology course"),
        Requirement("BIOL_EVOL", "Evolution/Organismal Biology Course", "Major", "Upper Division Core", 3,
                    course_options=["BIOL 328", "BIOL 337", "BIOL 380", "BIOL 382", "BIOL 425",
                                    "BIOL 453", "BIOL 454", "BIOL 460", "BIOL 475GW", "BIOL 478GW",
                                    "BIOL 500", "BIOL 502", "BIOL 504", "BIOL 505", "BIOL 514",
                                    "BIOL 555", "BIOL 570GW", "BIOL 600", "BIOL 638"],
                    notes="Choose 1 evolution or organismal biology course"),
    ]

    electives = [
        Requirement("BIOL_ELEC", "Upper Division Biology Electives", "Major", "Electives", 6,
                    notes="4-8 units from approved upper-division BIOL courses with BIOL 230/240 prereqs. Only one of BIOL 317, 327, 330, 349 allowed. Up to 3 units BIOL 699 allowed."),
    ]

    return DegreeProgram(
        program_code="BIOL_BA",
        program_name="General Biology",
        degree_type="BA",
        catalog_year="2020-21",
        total_units=120,
        major_requirements=lower_div + upper_core + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=["GE_B1", "GE_B2", "GE_B3", "GE_UDB"]
    )


def create_biol_ba_2021_22() -> DegreeProgram:
    """
    General Biology BA - 2021-22 Catalog
    Changes from 2020-21: minor renaming (BIOL 582 full name updated). Identical otherwise.
    """
    program = create_biol_ba_2020_21()
    program.catalog_year = "2021-22"
    return program


def create_biol_ba_2022_23() -> DegreeProgram:
    """
    General Biology BA - 2022-23 Catalog
    Changes from 2021-22:
    - Same lower/upper division structure
    - CHEM 115 now listed as 5 units explicitly
    - Elective list in bulletin truncated (some course names missing) but structure unchanged
    """
    program = create_biol_ba_2021_22()
    program.catalog_year = "2022-23"
    return program


def create_biol_ba_2023_24() -> DegreeProgram:
    """
    General Biology BA - 2023-24 Catalog
    Same as 2022-23. Minor formatting changes only.
    """
    program = create_biol_ba_2022_23()
    program.catalog_year = "2023-24"
    return program


def create_biol_ba_2024_25() -> DegreeProgram:
    """
    General Biology BA - 2024-25 Catalog
    Major restructure from 2023-24:
    - Total units: NOW 58 (was 49-64)
    - Lower Division: reduced to 22 units
      * Removed: CHEM 215, PHYS 121, PHYS 122 (Physics II sequence)
      * Added: BIOL 231 (Advising for Success, 1 unit)
      * CHEM 115 reduced to 4 units
      * Math: replaced MATH 124/226 choice with tiered QR options
        (MATH 197+198, MATH 199, or MATH 226)
    - Upper Division: restructured
      * Added BIOL 337 (Evolution) as required core (new!)
      * BIOL 355 (Genetics) remains required core
      * Physiology/Cell Biology course: expanded options (added BIOL 357, BIOL 446)
      * Physiology/Cell Biology Lab: added BIOL 638 as option
      * Ecology + Evolution categories merged into 'Two Ecology, Evolution, or Organismal Biology Courses'
    - GE met in major: B1 no longer listed (CHEM 215 removed); B2+B3 still via BIOL 240; UD-B via BIOL 355
    - Complementary Studies: now includes 'computer science' explicitly
    """
    lower_div = [
        Requirement("BIOL_230", "BIOL 230 - Introductory Biology I", "Major", "Lower Division", 5, ["BIOL 230"]),
        Requirement("BIOL_231", "BIOL 231 - Advising for Success as a Biology Major", "Major", "Lower Division", 1, ["BIOL 231"]),
        Requirement("BIOL_240", "BIOL 240 - Introductory Biology II", "Major", "Lower Division", 5, ["BIOL 240"]),
        Requirement("BIOL_CHEM115", "CHEM 115 - General Chemistry I", "Major", "Lower Division", 4, ["CHEM 115"]),
        Requirement("BIOL_CHEM130", "CHEM 130 or CHEM 233 - Organic Chemistry", "Major", "Lower Division", 3,
                    course_options=["CHEM 130", "CHEM 233"]),
        Requirement("BIOL_PHYS111", "PHYS 111 - General Physics I", "Major", "Lower Division", 3, ["PHYS 111"]),
        Requirement("BIOL_PHYS112", "PHYS 112 - General Physics I Laboratory", "Major", "Lower Division", 1, ["PHYS 112"]),
        Requirement("BIOL_QR", "Quantitative Reasoning", "Major", "Lower Division", 4,
                    course_options=["MATH 197+MATH 198", "MATH 199", "MATH 226"],
                    notes="MATH 197+198 = 6 units; MATH 199 = 4 units; MATH 226 = 4 units"),
    ]

    upper_core = [
        Requirement("BIOL_337", "BIOL 337 - Evolution", "Major", "Upper Division Core", 3, ["BIOL 337"]),
        Requirement("BIOL_355", "BIOL 355 - Genetics", "Major", "Upper Division Core", 3, ["BIOL 355"]),
        Requirement("BIOL_PHYSIO_CELL", "Physiology or Cell Biology Course", "Major", "Upper Division Core", 3,
                    course_options=["BIOL 328", "BIOL 350", "BIOL 357", "BIOL 382", "BIOL 401", "BIOL 435",
                                    "BIOL 442", "BIOL 446", "BIOL 453", "BIOL 525", "BIOL 612", "BIOL 630", "CHEM 349"],
                    notes="Choose 1 course"),
        Requirement("BIOL_LAB", "Physiology or Cell Biology Laboratory", "Major", "Upper Division Core", 2,
                    course_options=["BIOL 351GW", "BIOL 402GW", "BIOL 436", "BIOL 443", "BIOL 454",
                                    "BIOL 526", "BIOL 613GW", "BIOL 631GW", "BIOL 638"],
                    notes="Choose 1 lab; take GWAR course if not already satisfied"),
        Requirement("BIOL_ECO_EVO", "Two Ecology, Evolution, or Organismal Biology Courses", "Major", "Upper Division Core", 8,
                    course_options=["BIOL 380", "BIOL 425", "BIOL 460", "BIOL 470", "BIOL 475GW",
                                    "BIOL 478GW", "BIOL 482", "BIOL 490", "BIOL 500", "BIOL 502",
                                    "BIOL 504", "BIOL 505", "BIOL 514", "BIOL 529GW", "BIOL 532",
                                    "BIOL 534", "BIOL 555", "BIOL 570GW", "BIOL 580", "BIOL 582",
                                    "BIOL 585", "BIOL 586GW", "BIOL 600"],
                    notes="Choose 2 courses; take GWAR course if not already satisfied"),
    ]

    electives = [
        Requirement("BIOL_ELEC", "Upper Division Biology Electives", "Major", "Electives", 10,
                    notes="Take enough units to reach 58 total. GWAR must be satisfied. "
                          "Max 6 units from non-BIOL courses (AA S, AFRS, AIS, ANTH, CSC, ENVS, ERTH, etc.). "
                          "Only one of BIOL 317, 327, 330, 349 allowed. Up to 3 units BIOL 699."),
    ]

    return DegreeProgram(
        program_code="BIOL_BA",
        program_name="General Biology",
        degree_type="BA",
        catalog_year="2024-25",
        total_units=120,
        major_requirements=lower_div + upper_core + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=["GE_B2", "GE_B3", "GE_UDB"]
    )


def create_biol_ba_2025_26() -> DegreeProgram:
    """
    General Biology BA - 2025-26 Catalog
    Changes from 2024-25:
    - GE framework changed to new numbered system (5B replaces B2; 5UD replaces UD-B)
    - Two new PLO Core Concepts added (#4 Pathways/Energy, #5 Systems)
    - BIOL 529GW renamed to BIOL 529 (Plant Ecology, GWAR designation removed from name)
    - BIOL 504 (Biology of the Fungi) - title truncated/missing in PDF but still listed at 4 units
    - Lab options: BIOL 351GW now paired with BIOL 351 discussion; similarly BIOL 631GW+631,
      BIOL 478GW+478, BIOL 570GW+570, BIOL 586GW+586 now listed as pairs
    - BIOL 670 renamed: 'BIOL 670GW Ecology and Evolution of Marine Systems I' ->
      'BIOL 670 Ecology and Evolution of Marine Systems I' (GW removed in 2025-26)
    """
    program = create_biol_ba_2024_25()
    program.catalog_year = "2025-26"
    program.ge_requirements = create_ge_requirements_2025_26()
    program.ge_met_in_major = ["GE_5B", "GE_5C", "GE_5UD"]

    return program


# =============================================================================
# 5. CHEMISTRY BS
# =============================================================================

def create_chem_bs_2020_21() -> DegreeProgram:
    """
    Chemistry BS - 2020-21 Catalog
    Total Major Units: 72 | Total Degree Units: ~120
    GE met in major: B1 (CHEM 233), B3 (CHEM 234)
    """
    lower_div = [
        Requirement("CHEM_115", "CHEM 115 - General Chemistry I", "Major", "Lower Division", 5, ["CHEM 115"]),
        Requirement("CHEM_215", "CHEM 215 - General Chemistry II", "Major", "Lower Division", 3, ["CHEM 215"]),
        Requirement("CHEM_216", "CHEM 216 - General Chemistry II Laboratory", "Major", "Lower Division", 2, ["CHEM 216"]),
        Requirement("CHEM_233", "CHEM 233 - Organic Chemistry I", "Major", "Lower Division", 3, ["CHEM 233"]),
        Requirement("CHEM_234", "CHEM 234 - Organic Chemistry I Laboratory", "Major", "Lower Division", 2, ["CHEM 234"]),
        Requirement("CHEM_251", "CHEM 251 - Mathematics and Physics for Chemistry", "Major", "Lower Division", 3, ["CHEM 251"]),
        Requirement("CHEM_MATH226", "MATH 226 - Calculus I", "Major", "Lower Division", 4, ["MATH 226"]),
        Requirement("CHEM_MATH227", "MATH 227 - Calculus II", "Major", "Lower Division", 4, ["MATH 227"]),
        Requirement("CHEM_PHYS", "Physics I and II with Labs", "Major", "Lower Division", 8,
                    course_options=["PHYS 111+112+121+122", "PHYS 220+222+230+232"],
                    notes="Choose either algebra-based (PHYS 111-122) or calculus-based (PHYS 220-232) sequence"),
    ]

    upper_req = [
        Requirement("CHEM_321", "CHEM 321 - Quantitative Chemical Analysis", "Major", "Upper Division", 3, ["CHEM 321"]),
        Requirement("CHEM_322", "CHEM 322 - Quantitative Chemical Analysis Laboratory", "Major", "Upper Division", 2, ["CHEM 322"]),
        Requirement("CHEM_325", "CHEM 325 - Inorganic Chemistry", "Major", "Upper Division", 3, ["CHEM 325"]),
        Requirement("CHEM_335", "CHEM 335 - Organic Chemistry II", "Major", "Upper Division", 3, ["CHEM 335"]),
        Requirement("CHEM_336", "CHEM 336 - Organic Chemistry II Laboratory", "Major", "Upper Division", 2, ["CHEM 336"],
                    notes="CHEM 338 may substitute"),
        Requirement("CHEM_340", "CHEM 340 - Biochemistry I", "Major", "Upper Division", 3, ["CHEM 340"]),
        Requirement("CHEM_351", "CHEM 351 - Physical Chemistry I: Thermodynamics and Kinetics", "Major", "Upper Division", 3, ["CHEM 351"]),
        Requirement("CHEM_353", "CHEM 353 - Physical Chemistry II: Quantum Chemistry and Spectroscopy", "Major", "Upper Division", 3, ["CHEM 353"]),
        Requirement("CHEM_390GW", "CHEM 390GW - Contemporary Chemistry and Biochemistry Research (GWAR)", "Major", "Upper Division", 3, ["CHEM 390GW"]),
        Requirement("CHEM_426", "CHEM 426 - Advanced Inorganic Chemistry Laboratory", "Major", "Upper Division", 2, ["CHEM 426"],
                    notes="CHEM 343 may substitute with advisor approval"),
        Requirement("CHEM_451", "CHEM 451 - Experimental Physical Chemistry Laboratory", "Major", "Upper Division", 2, ["CHEM 451"],
                    notes="CHEM 343 may substitute with advisor approval"),
    ]

    electives = [
        Requirement("CHEM_ELEC", "Upper Division Chemistry Electives", "Major", "Electives", 9,
                    course_options=[
                        "CHEM 341", "CHEM 343", "CHEM 370", "CHEM 420", "CHEM 422",
                        "CHEM 433", "CHEM 443", "CHEM 645GW", "CHEM 680", "CHEM 699",
                        "CSC 306", "CSC 508", "CSC 509"
                    ],
                    notes="9 units minimum. Community college courses cannot substitute. CHEM 699 by petition only. Must select one CSC course."),
    ]

    return DegreeProgram(
        program_code="CHEM_BS",
        program_name="Chemistry",
        degree_type="BS",
        catalog_year="2020-21",
        total_units=120,
        major_requirements=lower_div + upper_req + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=["GE_B1", "GE_B3"]
    )


def create_chem_bs_2021_22() -> DegreeProgram:
    """Chemistry BS - 2021-22 Catalog (identical to 2020-21)"""
    program = create_chem_bs_2020_21()
    program.catalog_year = "2021-22"
    return program


def create_chem_bs_2022_23() -> DegreeProgram:
    """
    Chemistry BS - 2022-23 Catalog
    Changes from 2021-22:
    - CHEM 215+216 now listed together as 5-unit block
    - CSC elective option: CSC 508 replaced with CSC 508 (same course, renamed)
    - Otherwise identical 72-unit structure
    """
    program = create_chem_bs_2021_22()
    program.catalog_year = "2022-23"

    # Update lower div: CHEM 215+216 combined
    for req in program.major_requirements:
        if req.req_id == "CHEM_216":
            req.notes = "Included with CHEM 215 as a 5-unit block in 2022-23"

    return program


def create_chem_bs_2023_24() -> DegreeProgram:
    """
    Chemistry BS - 2023-24 Catalog
    Changes from 2022-23:
    - Added CHEM 667 (Optical Engineering for Biological Sciences) to elective options
    - Elective notes updated: grad courses in chem OR appropriate biology/physics/geosciences/CSC
      may substitute with advisor approval
    - CHEM 699 footnote updated: 'minimum 3 units in single semester'
    - CSC option updated: CSC 508 (same number, minor description update)
    """
    program = create_chem_bs_2022_23()
    program.catalog_year = "2023-24"

    for req in program.major_requirements:
        if req.req_id == "CHEM_ELEC":
            req.course_options = [
                "CHEM 341", "CHEM 343", "CHEM 370", "CHEM 420", "CHEM 422",
                "CHEM 433", "CHEM 443", "CHEM 645GW", "CHEM 667", "CHEM 680", "CHEM 699",
                "CSC 306", "CSC 508", "CSC 509"
            ]
            req.notes = (
                "9 units minimum. Community college courses cannot substitute. "
                "Grad-level chem or approved biology/physics/geosciences/CSC courses may substitute with advisor approval. "
                "CHEM 699 by petition only (min 3 units, same semester). Must include one CSC course."
            )

    return program


def create_chem_bs_2024_25() -> DegreeProgram:
    """
    Chemistry BS - 2024-25 Catalog
    Changes from 2023-24:
    - Total units: 70 (reduced from 72)
    - Lower Division: CHEM 215+216 now listed separately as CHEM 215 (4 units) only;
      CHEM 216 lab no longer separately listed (absorbed into CHEM 215 block)
      Total lower div: 32 units
    - Upper Division Required: 29 units (same courses)
    - Electives: Added CHEM 685 (Projects in Teaching, 1 unit) and CHEM 686 (Experiences in Teaching, 2 units)
    - CSC option: CSC 508 renamed to CSC 408 (Machine Learning and Data Science for Personalized Medicine)
    - CHEM 699 note: 'May be repeated and up to 2 units used towards Elective requirement'
    """
    lower_div = [
        Requirement("CHEM_115", "CHEM 115 - General Chemistry I", "Major", "Lower Division", 4, ["CHEM 115"]),
        Requirement("CHEM_215", "CHEM 215 - General Chemistry II", "Major", "Lower Division", 4, ["CHEM 215"]),
        Requirement("CHEM_233", "CHEM 233 - Organic Chemistry I", "Major", "Lower Division", 3, ["CHEM 233"]),
        Requirement("CHEM_234", "CHEM 234 - Organic Chemistry I Laboratory", "Major", "Lower Division", 2, ["CHEM 234"]),
        Requirement("CHEM_251", "CHEM 251 - Mathematics and Physics for Chemistry", "Major", "Lower Division", 3, ["CHEM 251"]),
        Requirement("CHEM_MATH226", "MATH 226 - Calculus I", "Major", "Lower Division", 4, ["MATH 226"]),
        Requirement("CHEM_MATH227", "MATH 227 - Calculus II", "Major", "Lower Division", 4, ["MATH 227"]),
        Requirement("CHEM_PHYS", "Physics I and II with Labs", "Major", "Lower Division", 8,
                    course_options=["PHYS 111+112+121+122", "PHYS 220+222+230+232"],
                    notes="Choose either algebra-based (PHYS 111-122) or calculus-based (PHYS 220-232) sequence"),
    ]

    upper_req = [
        Requirement("CHEM_321", "CHEM 321 - Quantitative Chemical Analysis", "Major", "Upper Division", 3, ["CHEM 321"]),
        Requirement("CHEM_322", "CHEM 322 - Quantitative Chemical Analysis Laboratory", "Major", "Upper Division", 2, ["CHEM 322"]),
        Requirement("CHEM_325", "CHEM 325 - Inorganic Chemistry", "Major", "Upper Division", 3, ["CHEM 325"]),
        Requirement("CHEM_335", "CHEM 335 - Organic Chemistry II", "Major", "Upper Division", 3, ["CHEM 335"]),
        Requirement("CHEM_336", "CHEM 336 - Organic Chemistry II Laboratory", "Major", "Upper Division", 2, ["CHEM 336"]),
        Requirement("CHEM_340", "CHEM 340 - Biochemistry I", "Major", "Upper Division", 3, ["CHEM 340"]),
        Requirement("CHEM_351", "CHEM 351 - Physical Chemistry I: Thermodynamics and Kinetics", "Major", "Upper Division", 3, ["CHEM 351"]),
        Requirement("CHEM_353", "CHEM 353 - Physical Chemistry II: Quantum Chemistry and Spectroscopy", "Major", "Upper Division", 3, ["CHEM 353"]),
        Requirement("CHEM_390GW", "CHEM 390GW - Contemporary Chemistry and Biochemistry Research (GWAR)", "Major", "Upper Division", 3, ["CHEM 390GW"]),
        Requirement("CHEM_426", "CHEM 426 - Advanced Inorganic Chemistry Laboratory", "Major", "Upper Division", 2, ["CHEM 426"],
                    notes="CHEM 343 may substitute with advisor approval"),
        Requirement("CHEM_451", "CHEM 451 - Experimental Physical Chemistry Laboratory", "Major", "Upper Division", 2, ["CHEM 451"],
                    notes="CHEM 343 may substitute with advisor approval"),
    ]

    electives = [
        Requirement("CHEM_ELEC", "Upper Division Chemistry Electives", "Major", "Electives", 9,
                    course_options=[
                        "CHEM 341", "CHEM 343", "CHEM 370", "CHEM 420", "CHEM 422",
                        "CHEM 433", "CHEM 443", "CHEM 645GW", "CHEM 667", "CHEM 680",
                        "CHEM 685", "CHEM 686", "CHEM 699",
                        "CSC 306", "CSC 408", "CSC 509"
                    ],
                    notes=(
                        "9 units minimum. Community college courses cannot substitute. "
                        "CHEM 699: may be repeated, up to 2 units count; by petition only (same semester). "
                        "CHEM 685/686 may be repeated, up to 2 units. Must include one CSC course."
                    )),
    ]

    return DegreeProgram(
        program_code="CHEM_BS",
        program_name="Chemistry",
        degree_type="BS",
        catalog_year="2024-25",
        total_units=120,
        major_requirements=lower_div + upper_req + electives,
        ge_requirements=create_ge_requirements(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=["GE_B1", "GE_B3"]
    )


def create_chem_bs_2025_26() -> DegreeProgram:
    """
    Chemistry BS - 2025-26 Catalog
    Changes from 2024-25:
    - Total units: 71 minimum (increased by 1 from 70)
    - GE framework changed to new numbered system
    - Lower Division: now 37 units (increased from 32)
      * Added CHEM 235 - Organic Chemistry II (3 units) to lower division
      * Added CHEM 236 - Organic Chemistry II Laboratory (2 units) to lower division
      * CHEM 115: 4 units; CHEM 215: 4 units (separate, no lab listed separately)
    - Upper Division Required: reduced to 25 units
      * CHEM 335 and CHEM 336 removed (moved to lower division as CHEM 235/236)
      * CHEM 451 now 'Experimental Physical Chemistry with Laboratory' (3 units, was 2)
    - Electives: CHEM 685 renamed to 'Instructional Methods in Teaching Chemistry and Biochemistry'
    """
    lower_div = [
        Requirement("CHEM_115", "CHEM 115 - General Chemistry I", "Major", "Lower Division", 4, ["CHEM 115"]),
        Requirement("CHEM_215", "CHEM 215 - General Chemistry II", "Major", "Lower Division", 4, ["CHEM 215"]),
        Requirement("CHEM_233", "CHEM 233 - Organic Chemistry I", "Major", "Lower Division", 3, ["CHEM 233"]),
        Requirement("CHEM_234", "CHEM 234 - Organic Chemistry I Laboratory", "Major", "Lower Division", 2, ["CHEM 234"]),
        Requirement("CHEM_235", "CHEM 235 - Organic Chemistry II", "Major", "Lower Division", 3, ["CHEM 235"]),
        Requirement("CHEM_236", "CHEM 236 - Organic Chemistry II Laboratory", "Major", "Lower Division", 2, ["CHEM 236"]),
        Requirement("CHEM_251", "CHEM 251 - Mathematics and Physics for Chemistry", "Major", "Lower Division", 3, ["CHEM 251"]),
        Requirement("CHEM_MATH226", "MATH 226 - Calculus I", "Major", "Lower Division", 4, ["MATH 226"]),
        Requirement("CHEM_MATH227", "MATH 227 - Calculus II", "Major", "Lower Division", 4, ["MATH 227"]),
        Requirement("CHEM_PHYS", "Physics I and II with Labs", "Major", "Lower Division", 8,
                    course_options=["PHYS 111+112+121+122", "PHYS 220+222+230+232"],
                    notes="Choose either algebra-based (PHYS 111-122) or calculus-based (PHYS 220-232) sequence"),
    ]

    upper_req = [
        Requirement("CHEM_321", "CHEM 321 - Quantitative Chemical Analysis", "Major", "Upper Division", 3, ["CHEM 321"]),
        Requirement("CHEM_322", "CHEM 322 - Quantitative Chemical Analysis Laboratory", "Major", "Upper Division", 2, ["CHEM 322"]),
        Requirement("CHEM_325", "CHEM 325 - Inorganic Chemistry", "Major", "Upper Division", 3, ["CHEM 325"]),
        Requirement("CHEM_340", "CHEM 340 - Biochemistry I", "Major", "Upper Division", 3, ["CHEM 340"]),
        Requirement("CHEM_351", "CHEM 351 - Physical Chemistry I: Thermodynamics and Kinetics", "Major", "Upper Division", 3, ["CHEM 351"]),
        Requirement("CHEM_353", "CHEM 353 - Physical Chemistry II: Quantum Chemistry and Spectroscopy", "Major", "Upper Division", 3, ["CHEM 353"]),
        Requirement("CHEM_390GW", "CHEM 390GW - Contemporary Chemistry and Biochemistry Research (GWAR)", "Major", "Upper Division", 3, ["CHEM 390GW"]),
        Requirement("CHEM_426", "CHEM 426 - Advanced Inorganic Chemistry Laboratory", "Major", "Upper Division", 2, ["CHEM 426"],
                    notes="CHEM 343 may substitute with advisor approval"),
        Requirement("CHEM_451", "CHEM 451 - Experimental Physical Chemistry with Laboratory", "Major", "Upper Division", 3, ["CHEM 451"],
                    notes="CHEM 343 may substitute with advisor approval. Now 3 units (was 2)."),
    ]

    electives = [
        Requirement("CHEM_ELEC", "Upper Division Chemistry Electives", "Major", "Electives", 9,
                    course_options=[
                        "CHEM 341", "CHEM 343", "CHEM 370", "CHEM 420", "CHEM 422",
                        "CHEM 433", "CHEM 443", "CHEM 645GW", "CHEM 667", "CHEM 680",
                        "CHEM 685", "CHEM 686", "CHEM 699",
                        "CSC 306", "CSC 408", "CSC 509"
                    ],
                    notes=(
                        "9 units minimum. Community college courses cannot substitute. "
                        "CHEM 685 = Instructional Methods in Teaching Chemistry (3 units). "
                        "CHEM 686 may be repeated, up to 2 units. "
                        "CHEM 699: by petition only, same semester. Must include one CSC course."
                    )),
    ]

    return DegreeProgram(
        program_code="CHEM_BS",
        program_name="Chemistry",
        degree_type="BS",
        catalog_year="2025-26",
        total_units=120,
        major_requirements=lower_div + upper_req + electives,
        ge_requirements=create_ge_requirements_2025_26(),
        university_requirements=create_university_requirements(),
        ge_met_in_major=[]  # B1/B3 no longer explicitly listed as met in major in 2025-26
    )


# =============================================================================
# BULLETIN DATABASE
# =============================================================================

class BulletinDatabase:
    """Central registry of all degree programs — 5 majors x 6 catalog years = 30 programs"""

    CATALOG_YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
    PROGRAM_CODES = ["CSC_BS", "CMPE_BS", "PSY_BA", "BIOL_BA", "CHEM_BS"]

    def __init__(self):
        self.programs: Dict[str, DegreeProgram] = {}
        self._load_all_programs()

    def _load_all_programs(self):
        """Load all encoded degree programs"""

        # ===== 2020-21 Catalog =====
        self._add(create_csc_bs_2020_21())
        self._add(create_cmpe_bs_2020_21())
        self._add(create_psy_ba_2020_21())
        self._add(create_biol_ba_2020_21())
        self._add(create_chem_bs_2020_21())

        # ===== 2021-22 Catalog =====
        self._add(create_csc_bs_2021_22())
        self._add(create_cmpe_bs_2021_22())
        self._add(create_psy_ba_2021_22())
        self._add(create_biol_ba_2021_22())
        self._add(create_chem_bs_2021_22())

        # ===== 2022-23 Catalog =====
        self._add(create_csc_bs_2022_23())
        self._add(create_cmpe_bs_2022_23())
        self._add(create_psy_ba_2022_23())
        self._add(create_biol_ba_2022_23())
        self._add(create_chem_bs_2022_23())

        # ===== 2023-24 Catalog =====
        self._add(create_csc_bs_2023_24())
        self._add(create_cmpe_bs_2023_24())
        self._add(create_psy_ba_2023_24())
        self._add(create_biol_ba_2023_24())
        self._add(create_chem_bs_2023_24())

        # ===== 2024-25 Catalog =====
        self._add(create_csc_bs_2024_25())
        self._add(create_cmpe_bs_2024_25())
        self._add(create_psy_ba_2024_25())
        self._add(create_biol_ba_2024_25())
        self._add(create_chem_bs_2024_25())

        # ===== 2025-26 Catalog =====
        self._add(create_csc_bs_2025_26())
        self._add(create_cmpe_bs_2025_26())
        self._add(create_psy_ba_2025_26())
        self._add(create_biol_ba_2025_26())
        self._add(create_chem_bs_2025_26())

    def _add(self, program: DegreeProgram):
        key = f"{program.program_code}_{program.catalog_year}"
        self.programs[key] = program

    def get_program(self, program_code: str, catalog_year: str) -> Optional[DegreeProgram]:
        key = f"{program_code}_{catalog_year}"
        return self.programs.get(key)

    def list_programs(self) -> List[str]:
        return sorted(self.programs.keys())

    def get_programs_by_code(self, code: str) -> List[DegreeProgram]:
        return [p for k, p in self.programs.items() if k.startswith(code)]

    def get_programs_by_year(self, year: str) -> List[DegreeProgram]:
        return [p for k, p in self.programs.items() if year in k]


# =============================================================================
# MAIN - TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SF STATE BULLETIN DATABASE")
    print("5 Majors x 6 Catalog Years = 30 Degree Programs")
    print("=" * 70)

    db = BulletinDatabase()

    print(f"\nLoaded {len(db.programs)} programs:\n")

    for year in BulletinDatabase.CATALOG_YEARS:
        print(f"\n--- {year} ---")
        for p in db.get_programs_by_year(year):
            major_units = sum(r.units for r in p.major_requirements)
            print(f"  {p.program_name} ({p.degree_type}): {len(p.major_requirements)} reqs | "
                  f"~{major_units:.0f} major units | GE met: {p.ge_met_in_major or 'none'}")

    print("\n" + "=" * 70)
    print("SAMPLE: Computer Science BS across all years")
    print("=" * 70)
    for p in db.get_programs_by_code("CSC_BS"):
        elec = next((r for r in p.major_requirements if r.req_id == "CSC_ELEC"), None)
        elec_units = elec.units if elec else 0
        print(f"  {p.catalog_year}: {len(p.major_requirements)} reqs, elective units={elec_units}")

    print("\n" + "=" * 70)
    print("SAMPLE: General Biology BA - Key Changes Over Time")
    print("=" * 70)
    for p in db.get_programs_by_code("BIOL_BA"):
        ld_units = sum(r.units for r in p.major_requirements if r.subcategory == "Lower Division")
        print(f"  {p.catalog_year}: Lower div units={ld_units:.0f} | GE met={p.ge_met_in_major}")
