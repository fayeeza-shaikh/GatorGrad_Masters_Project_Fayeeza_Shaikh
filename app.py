# =============================================================================
# app.py — Streamlit Web Interface
# CSC 895/898 Culminating Experience Project | SF State University
# =============================================================================
#
# Browser-based interface where students can:
#   1. Upload their DPR PDF
#   2. See their progress (completed, in-progress, remaining)
#   3. View a semester-by-semester graduation plan
#   4. Read explanations for every recommendation
#   5. Explore career paths matching their coursework
#
# Run: streamlit run app.py
#
# =============================================================================


# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

import streamlit as st
import tempfile
import os
import json
import datetime

from bulletin_data import BulletinDatabase
from dpr_parser import DPRParser, SAMPLE_STUDENTS
from recommender import PathwayRecommender
from explainer import PathwayExplainer
from career_guide import CareerGuide
from models import PriorityLevel, RiskFactor, RiskSeverity


def _pdf_safe_text(text: str) -> str:
    """Map common Unicode to Latin-1 for PDF core fonts (Helvetica)."""
    if not text:
        return ""
    replacements = {
        "\u2192": "->",
        "\u2014": "--",
        "\u2013": "-",
        "\u2022": "*",
        "\u21c4": "<->",
        "\u2713": "[x]",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
    }
    out = text
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def _build_advising_report_pdf(report_text: str) -> bytes:
    """Build a multi-page PDF from the same plain-text report used for .txt export."""
    from fpdf import FPDF

    class AdvisingPDF(FPDF):
        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(110, 110, 110)
            self.cell(
                0,
                8,
                "GatorGrad | For planning only -- consult your advisor.",
                align="C",
            )

    pdf = AdvisingPDF()
    pdf.set_margins(14, 14, 14)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(28, 28, 28)

    width = pdf.epw
    for raw_line in report_text.split("\n"):
        line = _pdf_safe_text(raw_line)
        if not line.strip():
            pdf.ln(2)
            continue
        pdf.multi_cell(width, 4.6, line)

    return bytes(pdf.output())


# =============================================================================
# PAGE CONFIGURATION
# Must be the first Streamlit command in the script.
# =============================================================================

st.set_page_config(
    page_title="GatorGrad: AI-Powered Degree Advising",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CUSTOM STYLING
# =============================================================================

st.markdown("""
<style>
    /* Main header — SF State purple */
    .main-header {
        background: linear-gradient(135deg, #813661 0%, #5C2748 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        color: #F3E2EC;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }

    /* Metric cards — light gold background */
    .metric-card {
        background: #FAF0DF;
        border: 1px solid #F1D8AA;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        color: #3E2723;
    }
    .metric-card h3 {
        color: #813661;
        font-size: 1.8rem;
        margin: 0;
    }
    .metric-card p {
        color: #5C4033;
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }

    /* Priority badges */
    .badge-critical { background: #813661; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-high { background: #E8C076; color: #5C2748; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-medium { background: #ECD2F7; color: #5C2748; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-low { background: #F1D8AA; color: #5C2748; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }

    /* Risk factors — heat map (cool to hot by severity) */
    .risk-box {
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 6px 6px 0;
        border-left: 5px solid;
    }
    .risk-heat-1 {
        background: linear-gradient(90deg, #FFFDE7 0%, #FFF9C4 100%);
        border-left-color: #F9A825;
        color: #3E2723;
    }
    .risk-heat-2 {
        background: linear-gradient(90deg, #FFF3E0 0%, #FFE0B2 100%);
        border-left-color: #FB8C00;
        color: #3E2723;
    }
    .risk-heat-3 {
        background: linear-gradient(90deg, #FBE9E7 0%, #FFCCBC 100%);
        border-left-color: #F4511E;
        color: #3E0A00;
    }
    .risk-heat-4 {
        background: linear-gradient(90deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left-color: #C62828;
        color: #4A1014;
    }
    .risk-heat-legend {
        font-size: 0.8rem;
        color: #9E9E9E;
        margin: 0.25rem 0 0.75rem 0;
    }

    /* Career match bar */
    .match-bar {
        background: #F3E2EC;
        border-radius: 6px;
        height: 12px;
        overflow: hidden;
    }
    .match-fill {
        background: linear-gradient(90deg, #813661, #ECD2F7);
        height: 100%;
        border-radius: 6px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #ADB5BD;
        padding: 2rem 0 1rem 0;
        font-size: 0.85rem;
    }

    /* Override Streamlit accent colors to SF State purple */
    .stButton > button[kind="primary"] {
        background-color: #813661;
        border-color: #813661;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #5C2748;
        border-color: #5C2748;
    }
    .stProgress > div > div > div {
        background-color: #813661;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #FAF0DF;
        color: #3E2723;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] div.stMarkdown,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] small {
        color: #3E2723 !important;
    }
    /* File uploader — cream to match sidebar in both themes */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
        background: #F5E6D0 !important;
        border: 1px solid #C4A882 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] * {
        color: #3E2723 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] small {
        color: #5C4033 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button {
        color: #3E2723 !important;
        border: 1px solid #C4A882 !important;
        background: #FAF0DF !important;
    }
    /* Generate button */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        color: white !important;
        background-color: #A0527E;
        border-color: #A0527E;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #813661;
        border-color: #813661;
    }
    [data-testid="stSidebar"] .stAlert p {
        color: #3E2723 !important;
    }

    /* Feedback section */
    .feedback-section {
        background: #FAF0DF;
        border: 1px solid #F1D8AA;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-top: 2rem;
        color: #3E2723;
    }
    .feedback-section h3 {
        color: #813661;
        margin-top: 0;
    }
    .emoji-row {
        display: flex;
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .emoji-btn {
        font-size: 2rem;
        background: white;
        border: 2px solid #F1D8AA;
        border-radius: 12px;
        padding: 0.5rem 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
        text-align: center;
    }
    .emoji-btn:hover {
        transform: scale(1.15);
        border-color: #813661;
    }
    .emoji-btn.selected {
        border-color: #813661;
        background: #F3E2EC;
        box-shadow: 0 0 0 2px #813661;
        transform: scale(1.15);
    }
    .emoji-label {
        font-size: 0.7rem;
        color: #6C757D;
        display: block;
        margin-top: 0.2rem;
    }
    .feedback-thanks {
        background: linear-gradient(135deg, #813661 0%, #5C2748 100%);
        color: white !important;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-top: 1rem;
    }
    .feedback-thanks strong {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# INITIALIZE SYSTEM (cached — loads only once)
# =============================================================================

@st.cache_resource
def init_system(_schema_version: int = 4):
    """Initialize all agents. Bump _schema_version to invalidate stale cache."""
    db = BulletinDatabase()
    parser = DPRParser(db)
    recommender = PathwayRecommender(db)
    explainer = PathwayExplainer(db, recommender.prereq_map)
    guide = CareerGuide()
    return db, parser, recommender, explainer, guide

db, parser, recommender, explainer, guide = init_system()


# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🐊 GatorGrad: AI-Powered Degree Advising</h1>
    <p>Upload your Degree Progress Report (DPR) to get a personalized graduation pathway, 
    course explanations, and career guidance.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "⚠️ **This tool is not a replacement for your academic advisor.** "
    "It provides an initial analysis to help you prepare for your advising appointment. "
    "Please meet with your UAC or your major advisor to confirm any changes to your academic plan. "
    "Visit [advising.sfsu.edu](https://advising.sfsu.edu/) or check the resource links at the bottom of this page."
)


# =============================================================================
# SIDEBAR — Input Controls
# =============================================================================

with st.sidebar:
    st.header("📄 Student Input")

    input_mode = st.radio(
        "How would you like to provide your data?",
        ["Upload DPR PDF", "Use Sample Data"],
        index=0
    )

    uploaded_file = None
    sample_major = None

    if input_mode == "Upload DPR PDF":
        uploaded_file = st.file_uploader(
            "Upload your DPR PDF",
            type=["pdf"],
            help="Download your DPR from SF State's Student Center, then upload it here."
        )

        st.caption(
            "Don't know how to access your DPR? "
            "[Check out this guide](https://registrar.sfsu.edu/dprguide)"
        )

        st.info(
            "🔒 **Privacy:** Your name and student ID are automatically "
            "anonymized. No personal data is stored."
        )

    else:
        sample_major = st.selectbox(
            "Select a major to preview",
            list(SAMPLE_STUDENTS.keys()),
            index=0,
            help="Pick a sample student to see the full advising report for that major."
        )

        st.caption(
            "⚠️ Sample data is for trial purposes only. "
            "Please upload your own DPR for personalized advising."
        )

    st.divider()

    st.markdown("**Supported Majors:**")
    st.markdown("""
    - Computer Science BS
    - Computer Engineering BS
    - Psychology BA
    - General Biology BA
    - Chemistry BS
    """)

    st.markdown("*More majors coming soon!*")

    st.markdown("**Catalog Years:** 2020-21 through 2025-26")

    st.divider()

    st.header("⚙️ Settings")

    include_summer = st.checkbox(
        "Include Summer semesters",
        value=False,
        help="Check this to schedule courses in Summer terms for faster graduation."
    )

    max_units = st.slider(
        "Max units per semester",
        min_value=12,
        max_value=21,
        value=18,
        step=1,
        help="Maximum units to schedule per semester."
    )

    run_button = st.button("🚀 Generate Advising Report", type="primary", use_container_width=True)


# =============================================================================
# MAIN CONTENT — Run pipeline when button clicked
# =============================================================================

if run_button:
    # Apply settings
    recommender.INCLUDE_SUMMER = include_summer
    recommender.MAX_UNITS_PER_SEMESTER = max_units

    progress = None

    if input_mode == "Upload DPR PDF" and uploaded_file is not None:
        with st.spinner("Parsing your DPR PDF..."):
            # Save uploaded bytes to a temp file (pdfplumber needs a file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                progress = parser.parse_pdf(tmp_path)
            finally:
                os.unlink(tmp_path)

    elif input_mode == "Upload DPR PDF" and uploaded_file is None:
        st.warning("Please upload a DPR PDF first.")
        st.stop()

    else:
        with st.spinner(f"Loading sample data for {sample_major}..."):
            progress = parser.parse_dict(SAMPLE_STUDENTS[sample_major])

    # Check if major is supported
    if progress.student.program_code == "UNKNOWN" or \
       (len(progress.remaining) == 0 and len(progress.completed) == 0 and
        len(progress.in_progress) == 0):
        st.error(
            f"⚠️ Major **{progress.student.program_code}** is not currently supported. "
            f"Supported majors: Computer Science BS, Computer Engineering BS, "
            f"Psychology BA, General Biology BA, Chemistry BS."
        )

        if progress.student.completed_courses:
            st.subheader("📋 Extracted Courses")
            for c in progress.student.completed_courses:
                st.write(f"- {c.code}: {c.title} | {c.units} units | {c.grade} | {c.semester} {c.year}")

        st.stop()

    # =========================================================================
    # Run remaining agents
    # =========================================================================

    with st.spinner("Generating graduation pathway..."):
        pathway = recommender.generate_pathway(progress)

    with st.spinner("Generating explanations..."):
        explanation = explainer.explain(pathway, progress)

    with st.spinner("Analyzing career paths..."):
        career_report = guide.generate_report(progress)

    st.success("✅ Advising report generated successfully!")

    # =========================================================================
    # SECTION 1: Student Overview
    # =========================================================================

    st.header("📊 Student Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Program", progress.student.program_code)
    with col2:
        st.metric("Cumulative GPA", f"{progress.student.cumulative_gpa:.2f}")
    with col3:
        st.metric("Major GPA", f"{progress.student.major_gpa:.2f}")
    with col4:
        st.metric("Units", f"{progress.student.total_units_completed:.0f} / 120")

    pct = progress.percent_complete / 100
    st.progress(pct, text=f"Degree Progress: {progress.percent_complete:.1f}%")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("✅ Completed", len(progress.completed))
    with col_b:
        st.metric("🔄 In Progress", len(progress.in_progress))
    with col_c:
        st.metric("📝 Remaining", len(progress.remaining))

    # =========================================================================
    # SECTION 2: Graduation Pathway
    # =========================================================================

    st.header("📅 Graduation Pathway")
    st.write(f"**Estimated Graduation:** {pathway.estimated_graduation} "
             f"| **Semesters Remaining:** {len(pathway.semesters)}")

    for idx, semester in enumerate(pathway.semesters):
        with st.expander(
            f"📘 {semester.label} — {semester.total_units:.0f} units, "
            f"{len(semester.courses)} courses",
            expanded=(idx == 0),
        ):
            for course in semester.courses:
                priority = course.priority.value
                badge_class = f"badge-{priority}"
                badge_html = f'<span class="{badge_class}">{priority.upper()}</span>'

                # Flag large elective blocks so students know it represents multiple courses
                if course.units >= 9 and "Elective" in course.title:
                    num_courses = int(course.units // 3)
                    st.markdown(
                        f"{badge_html} **{course.code}** — {course.title} "
                        f"({course.units:.0f} units — pick {num_courses} courses of 3 units each)",
                        unsafe_allow_html=True
                    )
                else:
                    unit_str = f" ({course.units:.0f} units)" if course.units > 1 else ""
                    st.markdown(
                        f"{badge_html} **{course.code}** — {course.title}{unit_str}",
                        unsafe_allow_html=True
                    )

    # =========================================================================
    # SECTION 3: XAI Explanations
    # =========================================================================

    st.header("🧠 Why These Courses? (XAI Transparency)")
    st.write(explanation.overall_strategy)

    from collections import OrderedDict
    semester_groups = OrderedDict()
    for ce in explanation.course_explanations:
        semester_groups.setdefault(ce.semester_label, []).append(ce)

    # Show first 3 semesters expanded, rest behind a toggle
    semester_list = list(semester_groups.items())
    initial_count = 3

    for sem_label, courses in semester_list[:initial_count]:
        st.subheader(f"📘 {sem_label}")
        for ce in courses:
            with st.expander(f"💡 {ce.course_code}"):
                st.markdown("**Reasons:**")
                for reason in ce.reasons:
                    st.write(f"→ {reason}")
                if ce.alternatives:
                    st.markdown("**Alternatives:**")
                    for alt in ce.alternatives:
                        st.write(f"↔ {alt}")
                if ce.trade_offs:
                    st.markdown("**Trade-offs:**")
                    st.write(f"⇄ {ce.trade_offs}")

    if len(semester_list) > initial_count:
        with st.expander(f"📖 Show remaining {len(semester_list) - initial_count} semesters"):
            for sem_label, courses in semester_list[initial_count:]:
                st.subheader(f"📘 {sem_label}")
                for ce in courses:
                    with st.expander(f"💡 {ce.course_code}"):
                        st.markdown("**Reasons:**")
                        for reason in ce.reasons:
                            st.write(f"→ {reason}")
                        if ce.alternatives:
                            st.markdown("**Alternatives:**")
                            for alt in ce.alternatives:
                                st.write(f"↔ {alt}")
                        if ce.trade_offs:
                            st.markdown("**Trade-offs:**")
                            st.write(f"⇄ {ce.trade_offs}")

    # --- Semester Notes ---
    if explanation.semester_notes:
        st.subheader("📝 Semester Notes")
        for label, note in explanation.semester_notes.items():
            st.info(f"**{label}:** {note}")

    # --- Risk Factors ---
    if explanation.risk_factors:
        st.subheader("⚠️ Risk Factors")
        st.markdown(
            '<p class="risk-heat-legend">'
            "Severity heat map: <strong>low</strong> (yellow) → "
            "<strong>medium</strong> (amber) → <strong>high</strong> (orange) → "
            "<strong>critical</strong> (red)."
            "</p>",
            unsafe_allow_html=True,
        )
        for item in explanation.risk_factors:
            # Handle RiskFactor objects, stale cached objects, or plain strings
            if isinstance(item, RiskFactor):
                msg = item.message
                heat = int(item.severity)
            elif hasattr(item, "message") and hasattr(item, "severity"):
                msg = item.message
                try:
                    heat = int(item.severity)
                except (ValueError, TypeError):
                    heat = 2
            else:
                msg = str(item)
                heat = 2

            heat = max(1, min(4, heat))
            severity_names = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
            label = severity_names.get(heat, "Medium")
            st.markdown(
                f'<div class="risk-box risk-heat-{heat}">'
                f'<strong>{label}</strong> — ⚠️ {msg}</div>',
                unsafe_allow_html=True,
            )

    # =========================================================================
    # SECTION 4: Career Paths
    # =========================================================================

    st.header("💼 Career Paths")

    if career_report.career_paths:
        for i, career in enumerate(career_report.career_paths):
            with st.expander(
                f"{'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else '📌'} "
                f"{career.title} — {int(career.match_score * 100)}% match"
            ):
                col_left, col_right = st.columns([2, 1])

                with col_left:
                    st.write(career.description)
                    st.write(f"**Field:** {career.field}")
                    st.write(f"**Salary Range:** {career.salary_range}")
                    st.write(f"**Job Outlook:** {career.job_outlook}")
                    st.write(f"**Education:** {career.education_level}")

                    if career.certifications:
                        st.write(f"**Certifications:** {', '.join(career.certifications)}")

                with col_right:
                    match_pct = int(career.match_score * 100)
                    st.markdown(f"### {match_pct}% Match")
                    st.progress(career.match_score)

                    st.markdown("**Required Skills:**")
                    for skill in career.required_skills[:6]:
                        st.write(f"• {skill}")

                if career.next_steps:
                    st.markdown("**Recommended Next Steps:**")
                    for step in career.next_steps:
                        st.write(f"✓ {step}")

        col_s, col_g = st.columns(2)
        with col_s:
            st.subheader("💪 Strengths")
            for s in career_report.strengths:
                st.success(f"+ {s}")

        with col_g:
            st.subheader("📈 Gaps to Address")
            for g in career_report.gaps:
                st.warning(f"- {g}")

    else:
        st.info("Career analysis not available for this major.")

    # --- Skills Summary ---
    if career_report.skills_summary:
        st.subheader("🎯 Skills Summary")
        cols = st.columns(2)

        for i, (skill, level) in enumerate(career_report.skills_summary.items()):
            with cols[i % 2]:
                if "Strong" in level:
                    st.success(f"**{skill}**: {level}")
                elif "Moderate" in level:
                    st.info(f"**{skill}**: {level}")
                elif "Basic" in level:
                    st.warning(f"**{skill}**: {level}")
                else:
                    st.error(f"**{skill}**: {level}")

    # =========================================================================
    # SECTION 5: Feedback
    # =========================================================================

    FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "feedback.json")

    def _load_feedback():
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
        return []

    def _save_feedback(entry: dict):
        data = _load_feedback()
        data.append(entry)
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(data, f, indent=2)

    st.divider()
    st.header("💬 How was your experience?")

    EMOJI_OPTIONS = [
        ("😍", "Loved it"),
        ("😊", "Good"),
        ("😐", "Okay"),
        ("😕", "Confusing"),
        ("😞", "Not helpful"),
    ]

    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False

    if not st.session_state.feedback_submitted:
        emoji_cols = st.columns(len(EMOJI_OPTIONS))
        selected_emoji = None

        for idx, (emoji, label) in enumerate(EMOJI_OPTIONS):
            with emoji_cols[idx]:
                if st.button(emoji, key=f"emoji_{idx}", use_container_width=True):
                    st.session_state.selected_emoji = (emoji, label)

        if "selected_emoji" in st.session_state:
            chosen_emoji, chosen_label = st.session_state.selected_emoji
            st.markdown(f"You selected: **{chosen_emoji} {chosen_label}**")

        feedback_text = st.text_area(
            "Anything else you'd like to share? (optional)",
            placeholder="e.g., The pathway was helpful but I wish it showed elective options...",
            max_chars=1000,
            key="feedback_text",
        )

        if st.button("Submit Feedback", type="primary", key="submit_feedback"):
            if "selected_emoji" not in st.session_state:
                st.warning("Please select an emoji rating first.")
            else:
                emoji, label = st.session_state.selected_emoji
                entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "rating_emoji": emoji,
                    "rating_label": label,
                    "comment": feedback_text.strip() if feedback_text else "",
                    "program": progress.student.program_code,
                }
                _save_feedback(entry)
                st.session_state.feedback_submitted = True
                st.rerun()
    else:
        st.markdown(
            '<div class="feedback-thanks">'
            "🎉 <strong>Thank you for your feedback!</strong><br>"
            "Your input helps us improve GatorGrad for future students."
            "</div>",
            unsafe_allow_html=True,
        )

    # =========================================================================
    # SECTION 6: Advising Resources
    # =========================================================================

    DEPT_LINKS = {
        "CSC_BS": ("Computer Science Department", "https://cs.sfsu.edu/"),
        "CMPE_BS": ("School of Engineering", "https://engineering.sfsu.edu/"),
        "PSY_BA": ("Psychology Department", "https://psychology.sfsu.edu/"),
        "BIOL_BA": ("Department of Biology", "https://biology.sfsu.edu/"),
        "CHEM_BS": ("Chemistry & Biochemistry Department", "https://chemistry.sfsu.edu/"),
    }

    st.divider()
    st.header("🏫 Need Help? Contact Your Advisors")

    col_uac, col_dept = st.columns(2)

    with col_uac:
        st.subheader("📋 GE & Degree Planning")
        st.markdown(
            "For **General Education**, degree planning, academic standing, "
            "or registration questions, contact the **Undergraduate Advising Center (UAC)**:"
        )
        st.markdown("**[Undergraduate Advising Center (UAC)](https://advising.sfsu.edu/)**")
        st.markdown(
            "📍 Administration Building, Room 203  \n"
            "📞 (415) 338-2101  \n"
            "📧 uacadvising@sfsu.edu"
        )

    with col_dept:
        dept_name, dept_url = DEPT_LINKS.get(
            progress.student.program_code,
            ("your major department", "https://sfsu.edu")
        )
        st.subheader("🎓 Major-Specific Questions")
        st.markdown(
            f"For questions about **major requirements**, course sequencing, "
            f"elective selection, or faculty advising, contact the **{dept_name}**:"
        )
        st.markdown(f"**[{dept_name}]({dept_url})**")

    st.markdown("<br>", unsafe_allow_html=True)

    st.info(
        "💡 **Tip:** Bring this advising report to your appointment! "
        "It gives your advisor a head start on understanding your progress."
    )

    # --- Download report (PDF uses Streamlit's download like .txt; browser Print is unreliable in embedded apps) ---
    col_pdf, col_txt = st.columns(2)

    lines = []
    lines.append("=" * 60)
    lines.append("GatorGrad — Advising Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Program: {progress.student.program_code}")
    lines.append(f"Catalog Year: {progress.student.catalog_year}")
    lines.append(f"GPA: {progress.student.cumulative_gpa:.2f} (Major: {progress.student.major_gpa:.2f})")
    lines.append(f"Units: {progress.student.total_units_completed:.0f} / 120")
    lines.append(f"Progress: {progress.percent_complete:.1f}%")
    lines.append(f"Completed: {len(progress.completed)} | In Progress: {len(progress.in_progress)} | Remaining: {len(progress.remaining)}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("GRADUATION PATHWAY")
    lines.append("-" * 60)
    lines.append(f"Estimated Graduation: {pathway.estimated_graduation}")
    lines.append(f"Semesters Remaining: {len(pathway.semesters)}")
    lines.append("")
    for sem in pathway.semesters:
        lines.append(f"  {sem.label} ({sem.total_units:.0f} units)")
        for c in sem.courses:
            unit_part = f" ({c.units:.0f} units)" if c.units > 1 else ""
            lines.append(f"    [{c.priority.value.upper()}] {c.code} — {c.title}{unit_part}")
        lines.append("")

    lines.append("-" * 60)
    lines.append("COURSE EXPLANATIONS")
    lines.append("-" * 60)
    lines.append(explanation.overall_strategy)
    lines.append("")
    for ce in explanation.course_explanations:
        lines.append(f"  {ce.course_code} ({ce.semester_label})")
        for r in ce.reasons:
            lines.append(f"    → {r}")
        lines.append("")

    if career_report.career_paths:
        lines.append("-" * 60)
        lines.append("CAREER PATHS")
        lines.append("-" * 60)
        for career in career_report.career_paths:
            lines.append(f"  {career.title} — {int(career.match_score * 100)}% match")
            lines.append(f"    {career.salary_range} | {career.job_outlook}")
        lines.append("")

    lines.append("-" * 60)
    lines.append("ADVISING RESOURCES")
    lines.append("-" * 60)
    lines.append("  UAC (GE & Degree Planning): https://advising.sfsu.edu/")
    dept_name_dl, dept_url_dl = DEPT_LINKS.get(
        progress.student.program_code,
        ("your major department", "https://sfsu.edu")
    )
    lines.append(f"  {dept_name_dl}: {dept_url_dl}")
    lines.append("")
    lines.append("This report is for planning purposes only.")
    lines.append("Please consult a human advisor to finalize your plan.")

    report_text = "\n".join(lines)
    pdf_bytes = _build_advising_report_pdf(report_text)

    with col_pdf:
        st.download_button(
            label="📥 Download Report (.pdf)",
            data=pdf_bytes,
            file_name="GatorGrad_Advising_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col_txt:
        st.download_button(
            label="📥 Download Report (.txt)",
            data=report_text,
            file_name="GatorGrad_Advising_Report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.caption(
        "To print the on-screen layout, use your browser: **File → Print** (or Ctrl/Cmd+P) "
        "and choose **Save as PDF** if you want a PDF from the web view."
    )

    # =========================================================================
    # Resources & References
    # =========================================================================

    st.divider()
    with st.expander("📚 Resources & References"):
        st.markdown("""
- [San Francisco State University](https://www.sfsu.edu/)
- [Undergraduate Advising Center (UAC)](https://advising.sfsu.edu/)
- [Department of Computer Science](https://cs.sfsu.edu/)
- [School of Engineering](https://engineering.sfsu.edu/)
- [Department of Psychology](https://psychology.sfsu.edu/)
- [Department of Biology](https://biology.sfsu.edu/)
- [Department of Chemistry & Biochemistry](https://chemistry.sfsu.edu/)
        """)

    # =========================================================================
    # FOOTER
    # =========================================================================

    st.divider()
    st.markdown(
        '<div class="footer">'
        'GatorGrad: AI-Powered Degree Advising | CSC 895/898 Culminating Experience Project<br>'
        'This tool provides initial guidance. Please consult a human advisor to finalize your plan.'
        '</div>',
        unsafe_allow_html=True
    )

else:
    # Landing page — shown before generating a report
    st.markdown("""
    ### 👋 Welcome!

    This system uses **4 AI agents** to analyze your academic progress and generate 
    personalized guidance:

    | Agent | Role | What It Does |
    |-------|------|-------------|
    | 🔍 **Agent 1** | DPR Parser | Reads your transcript and identifies completed/remaining requirements |
    | 📅 **Agent 2** | Pathway Recommender | Builds a semester-by-semester graduation plan |
    | 🧠 **Agent 3** | Explainer (XAI) | Explains WHY each course was recommended |
    | 💼 **Agent 4** | Career Guide | Maps your coursework to career paths and salaries |

    **To get started:**
    1. Choose your input method in the sidebar (upload PDF or use sample data)
    2. Adjust settings if desired (Summer semesters, max units)
    3. Click **Generate Advising Report**

    ---
    *This tool provides initial guidance and is designed to complement — not replace — 
    human academic advisors.*

    **Resources & References:**
    - [San Francisco State University](https://www.sfsu.edu/)
    - [Undergraduate Advising Center (UAC)](https://advising.sfsu.edu/)
    - [Department of Computer Science](https://cs.sfsu.edu/)
    - [School of Engineering](https://engineering.sfsu.edu/)
    - [Department of Psychology](https://psychology.sfsu.edu/)
    - [Department of Biology](https://biology.sfsu.edu/)
    - [Department of Chemistry & Biochemistry](https://chemistry.sfsu.edu/)
    """)
