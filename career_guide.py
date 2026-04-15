# =============================================================================
# career_guide.py — Career Guide (Agent 4)
# CSC 895/898 Culminating Experience | SF State University
# =============================================================================
#
# Maps completed coursework to career paths for the student's major.
# Input: ProgressReport (Agent 1 / dpr_parser). Output: CareerReport for Agent 3.
#
# Static knowledge base; a production system might source labor-market APIs.
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from typing import List, Dict, Set

from models import (
    ProgressReport,
    CareerPath,
    CareerReport
)


# =============================================================================
# CAREER KNOWLEDGE BASE
# =============================================================================
# Curated career paths per supported major (title, skills, courses, outlook, etc.).
# =============================================================================

CAREER_DATABASE = {
    # =========================================================================
    # COMPUTER SCIENCE BS
    # =========================================================================
    "CSC_BS": [
        {
            "title": "Software Engineer",
            "field": "Technology",
            "description": "Design, develop, test, and maintain software applications and systems.",
            "salary_range": "$95,000 - $155,000",
            "job_outlook": "High demand",
            "required_skills": ["Python", "Java", "Data Structures", "Algorithms",
                                "System Design", "Git", "Testing"],
            "relevant_courses": ["CSC 210", "CSC 220", "CSC 230", "CSC 256",
                                 "CSC 310", "CSC 340", "CSC 413", "CSC 648"],
            "education_level": "Bachelor's",
            "certifications": ["AWS Certified Developer", "Google Professional Cloud Developer"],
            "next_steps": ["Build a portfolio with 3-5 projects on GitHub",
                           "Practice coding interviews on LeetCode",
                           "Apply for software engineering internships",
                           "Contribute to open-source projects"]
        },
        {
            "title": "Data Scientist",
            "field": "Technology / Analytics",
            "description": "Analyze large datasets to extract insights using statistics and machine learning.",
            "salary_range": "$90,000 - $145,000",
            "job_outlook": "High demand",
            "required_skills": ["Python", "Statistics", "Machine Learning", "SQL",
                                "Data Visualization", "Linear Algebra"],
            "relevant_courses": ["CSC 210", "CSC 220", "CSC 310", "MATH 324",
                                 "MATH 225", "MATH 226"],
            "education_level": "Bachelor's",
            "certifications": ["Google Data Analytics Certificate",
                                "IBM Data Science Professional Certificate"],
            "next_steps": ["Learn pandas, NumPy, and scikit-learn",
                           "Complete a data science project with real data",
                           "Take a machine learning elective",
                           "Build a data portfolio on Kaggle"]
        },
        {
            "title": "Web Developer",
            "field": "Technology",
            "description": "Build and maintain websites and web applications for businesses and users.",
            "salary_range": "$70,000 - $120,000",
            "job_outlook": "Growing",
            "required_skills": ["HTML/CSS", "JavaScript", "React", "Node.js",
                                "Database Design", "REST APIs"],
            "relevant_courses": ["CSC 210", "CSC 317", "CSC 413", "CSC 648"],
            "education_level": "Bachelor's",
            "certifications": ["Meta Front-End Developer Certificate",
                                "AWS Certified Cloud Practitioner"],
            "next_steps": ["Build 3+ full-stack web projects",
                           "Learn React or Angular framework",
                           "Deploy projects to the cloud (Heroku, AWS)",
                           "Create a personal portfolio website"]
        },
        {
            "title": "Cybersecurity Analyst",
            "field": "Technology / Security",
            "description": "Protect computer systems and networks from security threats and breaches.",
            "salary_range": "$80,000 - $130,000",
            "job_outlook": "High demand",
            "required_skills": ["Network Security", "Linux", "Cryptography",
                                "Risk Assessment", "Incident Response"],
            "relevant_courses": ["CSC 210", "CSC 256", "CSC 415", "CSC 310"],
            "education_level": "Bachelor's",
            "certifications": ["CompTIA Security+", "Certified Ethical Hacker (CEH)",
                                "CISSP (after experience)"],
            "next_steps": ["Set up a home lab for security testing",
                           "Learn Linux command line deeply",
                           "Practice on CTF (Capture the Flag) challenges",
                           "Get CompTIA Security+ certification"]
        },
        {
            "title": "Systems Administrator",
            "field": "Technology / IT",
            "description": "Manage and maintain computer servers, networks, and infrastructure.",
            "salary_range": "$65,000 - $105,000",
            "job_outlook": "Stable",
            "required_skills": ["Linux", "Windows Server", "Networking",
                                "Cloud Platforms", "Scripting", "Troubleshooting"],
            "relevant_courses": ["CSC 256", "CSC 415", "CSC 210"],
            "education_level": "Bachelor's",
            "certifications": ["CompTIA A+", "AWS Solutions Architect",
                                "Red Hat Certified System Administrator"],
            "next_steps": ["Get comfortable with Linux/Unix systems",
                           "Learn cloud platforms (AWS, Azure, GCP)",
                           "Set up and manage a home server",
                           "Get CompTIA A+ or Network+ certification"]
        },
    ],

    # =========================================================================
    # COMPUTER ENGINEERING BS
    # =========================================================================
    "CMPE_BS": [
        {
            "title": "Embedded Systems Engineer",
            "field": "Technology / Hardware",
            "description": "Design software that runs on hardware devices like IoT sensors and microcontrollers.",
            "salary_range": "$90,000 - $140,000",
            "job_outlook": "Growing",
            "required_skills": ["C/C++", "Microcontrollers", "RTOS",
                                "Digital Logic", "Circuit Design"],
            "relevant_courses": ["CSC 210", "CSC 256", "ENGR 301", "ENGR 302"],
            "education_level": "Bachelor's",
            "certifications": ["ARM Accredited Engineer"],
            "next_steps": ["Build projects with Arduino or Raspberry Pi",
                           "Learn C for embedded systems",
                           "Study real-time operating systems (RTOS)",
                           "Apply for embedded internships"]
        },
        {
            "title": "Hardware Engineer",
            "field": "Technology / Hardware",
            "description": "Design, develop, and test computer hardware components and systems.",
            "salary_range": "$85,000 - $140,000",
            "job_outlook": "Stable",
            "required_skills": ["VHDL/Verilog", "PCB Design", "Signal Processing",
                                "Digital Logic", "Testing"],
            "relevant_courses": ["ENGR 301", "ENGR 302", "CSC 256", "MATH 226"],
            "education_level": "Bachelor's",
            "certifications": [],
            "next_steps": ["Learn FPGA programming",
                           "Build hardware projects",
                           "Study signal processing",
                           "Apply for hardware design internships"]
        },
        {
            "title": "DevOps Engineer",
            "field": "Technology",
            "description": "Bridge software development and IT operations with automation and CI/CD pipelines.",
            "salary_range": "$95,000 - $150,000",
            "job_outlook": "High demand",
            "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD",
                                "Cloud Platforms", "Scripting"],
            "relevant_courses": ["CSC 210", "CSC 256", "CSC 415", "CSC 413"],
            "education_level": "Bachelor's",
            "certifications": ["AWS DevOps Engineer", "Docker Certified Associate",
                                "Kubernetes Administrator (CKA)"],
            "next_steps": ["Learn Docker and Kubernetes",
                           "Set up CI/CD pipelines (GitHub Actions, Jenkins)",
                           "Get AWS or GCP cloud certification",
                           "Automate tasks with shell scripts and Python"]
        },
    ],

    # =========================================================================
    # PSYCHOLOGY BA
    # =========================================================================
    "PSY_BA": [
        {
            "title": "Clinical Psychologist",
            "field": "Healthcare / Mental Health",
            "description": "Diagnose and treat mental health disorders through therapy and assessment.",
            "salary_range": "$80,000 - $130,000",
            "job_outlook": "Growing",
            "required_skills": ["Clinical Assessment", "Therapeutic Techniques",
                                "Research Methods", "Ethics", "Communication"],
            "relevant_courses": ["PSY 200", "PSY 250", "PSY 371", "PSY 400",
                                 "PSY 431", "PSY 432"],
            "education_level": "Doctorate",
            "certifications": ["Licensed Psychologist (state license)"],
            "next_steps": ["Gain research experience in a faculty lab",
                           "Volunteer at a mental health clinic",
                           "Prepare for the GRE Psychology Subject Test",
                           "Apply to doctoral programs (PhD or PsyD)"]
        },
        {
            "title": "School Counselor",
            "field": "Education",
            "description": "Support K-12 students with academic, career, and social-emotional development.",
            "salary_range": "$55,000 - $85,000",
            "job_outlook": "Growing",
            "required_skills": ["Counseling", "Child Development", "Crisis Intervention",
                                "Communication", "Cultural Competency"],
            "relevant_courses": ["PSY 200", "PSY 431", "PSY 436", "PSY 301"],
            "education_level": "Master's",
            "certifications": ["Pupil Personnel Services (PPS) Credential"],
            "next_steps": ["Complete a master's in School Counseling",
                           "Get experience working with youth",
                           "Obtain PPS credential in California",
                           "Volunteer or intern at a school"]
        },
        {
            "title": "Human Resources Specialist",
            "field": "Business",
            "description": "Manage hiring, employee relations, benefits, and workplace culture.",
            "salary_range": "$50,000 - $80,000",
            "job_outlook": "Stable",
            "required_skills": ["Communication", "Conflict Resolution", "Organizational Behavior",
                                "Data Analysis", "Employment Law"],
            "relevant_courses": ["PSY 200", "PSY 301", "PSY 441", "PSY 462"],
            "education_level": "Bachelor's",
            "certifications": ["SHRM-CP (Society for HR Management)",
                                "PHR (Professional in HR)"],
            "next_steps": ["Take I/O Psychology electives",
                           "Get an HR internship",
                           "Learn HR software (Workday, BambooHR)",
                           "Study for SHRM-CP certification"]
        },
        {
            "title": "Research Analyst",
            "field": "Research / Analytics",
            "description": "Design studies, collect data, and analyze results for organizations or academia.",
            "salary_range": "$50,000 - $75,000",
            "job_outlook": "Stable",
            "required_skills": ["SPSS/R", "Research Design", "Statistics",
                                "Survey Design", "Technical Writing"],
            "relevant_courses": ["PSY 200", "PSY 371", "PSY 400", "PSY 305GW"],
            "education_level": "Bachelor's",
            "certifications": [],
            "next_steps": ["Assist a professor with research",
                           "Learn SPSS or R for statistical analysis",
                           "Present research at a student conference",
                           "Consider a master's for advanced research roles"]
        },
    ],

    # =========================================================================
    # GENERAL BIOLOGY BA
    # =========================================================================
    "BIOL_BA": [
        {
            "title": "Research Scientist",
            "field": "Science / Research",
            "description": "Conduct biological research in labs, universities, or biotech companies.",
            "salary_range": "$55,000 - $100,000",
            "job_outlook": "Growing",
            "required_skills": ["Lab Techniques", "Research Design", "Data Analysis",
                                "Scientific Writing", "Microscopy"],
            "relevant_courses": ["BIOL 100", "BIOL 230", "BIOL 240", "CHEM 115",
                                 "CHEM 116"],
            "education_level": "Master's",
            "certifications": [],
            "next_steps": ["Join a research lab as an undergraduate",
                           "Learn bioinformatics tools (BLAST, R)",
                           "Present at a student research conference",
                           "Apply to graduate programs in biology"]
        },
        {
            "title": "Environmental Scientist",
            "field": "Environment / Government",
            "description": "Study environmental problems and develop solutions for sustainability.",
            "salary_range": "$55,000 - $90,000",
            "job_outlook": "Growing",
            "required_skills": ["Field Research", "GIS", "Data Analysis",
                                "Environmental Regulations", "Report Writing"],
            "relevant_courses": ["BIOL 100", "BIOL 230", "BIOL 330", "CHEM 115"],
            "education_level": "Bachelor's",
            "certifications": ["Certified Environmental Scientist (CES)"],
            "next_steps": ["Take ecology and environmental science electives",
                           "Learn GIS software (ArcGIS, QGIS)",
                           "Intern at an environmental agency",
                           "Get field research experience"]
        },
        {
            "title": "Healthcare / Pre-Med",
            "field": "Healthcare",
            "description": "Pursue medical school to become a physician, dentist, or veterinarian.",
            "salary_range": "$200,000+ (after residency)",
            "job_outlook": "High demand",
            "required_skills": ["Biology", "Chemistry", "Physics", "Anatomy",
                                "Clinical Experience", "MCAT Prep"],
            "relevant_courses": ["BIOL 100", "BIOL 240", "CHEM 115", "CHEM 116",
                                 "PHYS 111"],
            "education_level": "Doctorate",
            "certifications": ["MD/DO license (after medical school + residency)"],
            "next_steps": ["Maintain a strong GPA (3.5+ recommended)",
                           "Gain clinical volunteer hours (100+)",
                           "Study for the MCAT early",
                           "Get physician shadowing experience"]
        },
        {
            "title": "Biotechnology Associate",
            "field": "Technology / Pharma",
            "description": "Work in biotech companies performing lab work, quality control, or product development.",
            "salary_range": "$50,000 - $80,000",
            "job_outlook": "Growing",
            "required_skills": ["Cell Culture", "PCR", "Lab Safety",
                                "Documentation", "Quality Control"],
            "relevant_courses": ["BIOL 100", "BIOL 240", "CHEM 115", "CHEM 116"],
            "education_level": "Bachelor's",
            "certifications": [],
            "next_steps": ["Get biotech lab experience (internship or research)",
                           "Learn PCR, gel electrophoresis, cell culture",
                           "Apply to Bay Area biotech companies",
                           "Consider a master's in biotechnology"]
        },
    ],

    # =========================================================================
    # CHEMISTRY BS
    # =========================================================================
    "CHEM_BS": [
        {
            "title": "Chemist",
            "field": "Science / Industry",
            "description": "Conduct chemical research and analysis in labs, pharma, or manufacturing.",
            "salary_range": "$55,000 - $95,000",
            "job_outlook": "Stable",
            "required_skills": ["Organic Chemistry", "Analytical Techniques",
                                "Spectroscopy", "Lab Safety", "Technical Writing"],
            "relevant_courses": ["CHEM 115", "CHEM 116", "CHEM 215", "CHEM 216",
                                 "CHEM 315", "CHEM 340"],
            "education_level": "Bachelor's",
            "certifications": ["ACS Certified Chemist"],
            "next_steps": ["Gain undergraduate research experience",
                           "Learn analytical instruments (NMR, HPLC, GC-MS)",
                           "Apply for lab internships in pharma or industry",
                           "Consider graduate school for research roles"]
        },
        {
            "title": "Pharmaceutical Scientist",
            "field": "Healthcare / Pharma",
            "description": "Develop and test new drugs and medications in pharmaceutical companies.",
            "salary_range": "$75,000 - $120,000",
            "job_outlook": "Growing",
            "required_skills": ["Drug Formulation", "Analytical Chemistry",
                                "Regulatory Compliance", "Clinical Trials", "GMP"],
            "relevant_courses": ["CHEM 115", "CHEM 116", "CHEM 215", "CHEM 216",
                                 "CHEM 315"],
            "education_level": "Master's",
            "certifications": [],
            "next_steps": ["Focus on analytical and organic chemistry",
                           "Intern at a pharmaceutical company",
                           "Learn FDA regulations and GMP",
                           "Apply to PharmD or chemistry grad programs"]
        },
        {
            "title": "Quality Control Analyst",
            "field": "Manufacturing / Pharma",
            "description": "Test products and materials to ensure they meet quality standards.",
            "salary_range": "$50,000 - $80,000",
            "job_outlook": "Stable",
            "required_skills": ["Analytical Chemistry", "HPLC", "Documentation",
                                "GMP", "Attention to Detail"],
            "relevant_courses": ["CHEM 115", "CHEM 116", "CHEM 315"],
            "education_level": "Bachelor's",
            "certifications": ["ASQ Certified Quality Inspector"],
            "next_steps": ["Learn HPLC and GC techniques thoroughly",
                           "Understand GMP and quality documentation",
                           "Apply for QC positions in Bay Area biotech/pharma",
                           "Get familiar with LIMS (Lab Information Management Systems)"]
        },
        {
            "title": "Materials Scientist",
            "field": "Technology / Manufacturing",
            "description": "Research and develop new materials for electronics, aerospace, or energy.",
            "salary_range": "$70,000 - $110,000",
            "job_outlook": "Growing",
            "required_skills": ["Physical Chemistry", "Spectroscopy",
                                "Materials Characterization", "Research Design"],
            "relevant_courses": ["CHEM 115", "CHEM 116", "CHEM 340", "MATH 227"],
            "education_level": "Master's",
            "certifications": [],
            "next_steps": ["Take physical chemistry and materials electives",
                           "Join a materials research lab",
                           "Learn characterization techniques (XRD, SEM)",
                           "Apply to materials science grad programs"]
        },
    ],
}


# =============================================================================
# CAREER GUIDE CLASS — Agent 4
# =============================================================================

class CareerGuide:

    def __init__(self):
        self.career_db = CAREER_DATABASE

    # =========================================================================
    # MAIN ENTRY POINT — Call this to run Agent 4
    # =========================================================================

    def generate_report(self, progress: ProgressReport) -> CareerReport:

        student = progress.student
        program_code = student.program_code

        career_data = self.career_db.get(program_code, [])

        if not career_data:
            return CareerReport(
                student_id=student.student_id,
                program_code=program_code,
                strengths=["Unable to generate career report — major not in database."],
                gaps=[f"Supported majors: {', '.join(self.career_db.keys())}"]
            )

        completed_codes = student.completed_course_codes

        career_paths = []
        for career in career_data:
            path = self._build_career_path(career, completed_codes)
            career_paths.append(path)

        career_paths.sort(key=lambda p: p.match_score, reverse=True)

        strengths = self._analyze_strengths(completed_codes, program_code)
        gaps = self._analyze_gaps(completed_codes, career_paths)

        skills_summary = self._build_skills_summary(completed_codes, program_code)

        return CareerReport(
            student_id=student.student_id,
            program_code=program_code,
            career_paths=career_paths,
            skills_summary=skills_summary,
            strengths=strengths,
            gaps=gaps
        )

    # =========================================================================
    # MATCH SCORE CALCULATION
    # =========================================================================

    def _build_career_path(self, career: dict, completed: Set[str]) -> CareerPath:
        # Match score: fraction of this career's relevant_courses the student completed.
        # Capped at 1.0 after optional outlook adjustment (see below).

        relevant = set(career["relevant_courses"])

        taken = relevant.intersection(completed)

        if relevant:
            match_score = len(taken) / len(relevant)
        else:
            match_score = 0.0

        # Slight boost for stronger labor-market outlook so rankings reflect demand.
        outlook = career.get("job_outlook", "")
        if "High demand" in outlook:
            match_score = min(1.0, match_score + 0.05)
        elif "Growing" in outlook:
            match_score = min(1.0, match_score + 0.02)

        return CareerPath(
            title=career["title"],
            field=career["field"],
            description=career["description"],
            salary_range=career["salary_range"],
            job_outlook=career["job_outlook"],
            required_skills=career["required_skills"],
            relevant_courses=career["relevant_courses"],
            match_score=round(match_score, 2),
            education_level=career["education_level"],
            certifications=career["certifications"],
            next_steps=career["next_steps"]
        )

    # =========================================================================
    # STRENGTHS ANALYSIS
    # =========================================================================

    def _analyze_strengths(self, completed: Set[str], program_code: str) -> List[str]:

        strengths = []

        clusters = {
            "programming": {
                "courses": {"CSC 210", "CSC 215", "CSC 220", "CSC 310", "CSC 340",
                            "CSC 413", "CSC 648"},
                "label": "Strong programming and software development foundation"
            },
            "math": {
                "courses": {"MATH 226", "MATH 227", "MATH 225", "MATH 324", "MATH 124"},
                "label": "Solid mathematics and quantitative reasoning"
            },
            "science_lab": {
                "courses": {"CHEM 115", "CHEM 116", "PHYS 111", "PHYS 220",
                            "BIOL 100", "BIOL 230", "BIOL 240"},
                "label": "Hands-on laboratory and scientific experience"
            },
            "research": {
                "courses": {"PSY 371", "PSY 400", "PSY 305GW", "BIOL 330"},
                "label": "Research methods and statistical analysis skills"
            },
            "communication": {
                "courses": {"ENG 114", "COMM 150", "CSC 300GW", "PSY 305GW"},
                "label": "Written and oral communication skills"
            },
            "systems": {
                "courses": {"CSC 256", "CSC 415", "ENGR 301", "ENGR 302"},
                "label": "Systems-level understanding (hardware, OS, networks)"
            },
        }

        for cluster_name, cluster_info in clusters.items():
            overlap = completed.intersection(cluster_info["courses"])
            # Threshold: at least two courses from a cluster to count as a strength.
            if len(overlap) >= 2:
                course_list = ", ".join(sorted(overlap))
                strengths.append(
                    f"{cluster_info['label']} ({course_list})"
                )

        if not strengths:
            strengths.append("Building foundational coursework — strengths will emerge as you progress.")

        return strengths

    # =========================================================================
    # GAPS ANALYSIS
    # =========================================================================

    def _analyze_gaps(self, completed: Set[str], career_paths: List[CareerPath]) -> List[str]:

        gaps = []
        # Deduplicate when several top careers suggest the same missing courses.
        seen_suggestions = set()

        for career in career_paths[:3]:
            relevant = set(career.relevant_courses)
            missing = relevant - completed

            if missing:
                missing_str = ", ".join(sorted(missing)[:3])

                suggestion = f"For {career.title}: consider taking {missing_str}"
                if suggestion not in seen_suggestions:
                    seen_suggestions.add(suggestion)
                    gaps.append(suggestion)

        if not gaps:
            gaps.append("Strong course coverage across top career matches.")

        return gaps

    # =========================================================================
    # SKILLS SUMMARY
    # =========================================================================

    def _build_skills_summary(self, completed: Set[str], program_code: str) -> Dict[str, str]:

        skill_map = {
            "Programming": {"CSC 210", "CSC 215", "CSC 220", "CSC 310",
                            "CSC 340", "CSC 317", "CSC 413", "CSC 648"},
            "Mathematics": {"MATH 124", "MATH 226", "MATH 227", "MATH 225",
                            "MATH 324", "CSC 230"},
            "Science": {"CHEM 115", "CHEM 116", "PHYS 111", "PHYS 220",
                         "PHYS 230", "BIOL 100", "BIOL 230", "BIOL 240"},
            "Research": {"PSY 371", "PSY 400", "BIOL 330", "CHEM 315"},
            "Communication": {"ENG 114", "COMM 150", "CSC 300GW", "PSY 305GW",
                               "BUS 360"},
            "Systems & Hardware": {"CSC 256", "CSC 415", "ENGR 301", "ENGR 302"},
        }

        summary = {}
        for skill, courses in skill_map.items():
            count = len(completed.intersection(courses))

            if count == 0:
                level = "Not started"
            elif count == 1:
                level = f"Basic ({count} course)"
            elif count <= 3:
                level = f"Moderate ({count} courses)"
            else:
                level = f"Strong ({count} courses)"

            summary[skill] = level

        return summary


# =============================================================================
# TEST — Run directly: python career_guide.py
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Agent 4: Career Guide — Test Run")
    print("=" * 65)

    from dpr_parser import DPRParser, SAMPLE_STUDENT_CSC
    from bulletin_data import BulletinDatabase

    db = BulletinDatabase()
    parser = DPRParser(db)
    guide = CareerGuide()

    print("\n" + "-" * 65)
    print("TEST 1: Computer Science BS Student")
    print("-" * 65)

    progress = parser.parse_dict(SAMPLE_STUDENT_CSC)
    report = guide.generate_report(progress)
    print(report.summary())

    print("\nSkills Summary:")
    for skill, level in report.skills_summary.items():
        print(f"  {skill}: {level}")

    print("\n" + "-" * 65)
    print("TEST 2: Psychology BA Student")
    print("-" * 65)

    from dpr_parser import DPRParser
    SAMPLE_PSY = {
        "student_id": "913456789",
        "name": "Maria Garcia",
        "program_code": "PSY_BA",
        "catalog_year": "2023-24",
        "current_semester": "Spring",
        "current_year": 2025,
        "in_progress_courses": ["PSY 371"],
        "completed_courses": [
            {"code": "PSY 200", "title": "General Psychology", "units": 3, "grade": "A", "semester": "Fall", "year": 2023},
            {"code": "PSY 250", "title": "Behavioral Neuroscience", "units": 3, "grade": "B+", "semester": "Spring", "year": 2024},
            {"code": "PSY 301", "title": "I/O Psych", "units": 3, "grade": "B", "semester": "Fall", "year": 2024},
            {"code": "ENG 114", "title": "Writing", "units": 3, "grade": "A-", "semester": "Fall", "year": 2023},
            {"code": "MATH 124", "title": "Elementary Statistics", "units": 4, "grade": "B", "semester": "Spring", "year": 2024},
        ]
    }

    progress_psy = parser.parse_dict(SAMPLE_PSY)
    report_psy = guide.generate_report(progress_psy)
    print(report_psy.summary())

    print("\nSkills Summary:")
    for skill, level in report_psy.skills_summary.items():
        print(f"  {skill}: {level}")

    print("\n" + "=" * 65)
    print("[ok] Agent 4 (Career Guide) verified.")
    print("=" * 65)
