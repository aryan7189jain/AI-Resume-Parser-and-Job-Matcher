# ==========================================================
# IMPORTS
# ==========================================================

import os
import tempfile
import shutil

import pandas as pd
import gradio as gr

from parser import (
    parse_multiple_resumes,
    create_dataframe,
    extract_jd_skills,
    calculate_job_match,
    calculate_final_score,
    calculate_resume_score,   # FIX: was used in show_candidate() but never imported
    rank_candidates,
    export_to_csv
)

# ==========================================================
# PREMIUM CSS
# ==========================================================
# Design language: deep navy glass panels, indigo -> cyan accent
# gradient, soft glow shadows, subtle motion on hover/focus.

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root{
    --bg:            #0B1120;
    --bg-soft:       #0F172A;
    --panel:         #141B2E;
    --panel-2:       #1A2338;
    --border:        #263049;
    --border-soft:   #1F2940;
    --accent:        #6366F1;
    --accent-2:      #22D3EE;
    --accent-grad:   linear-gradient(120deg,#6366F1 0%,#8B5CF6 45%,#22D3EE 100%);
    --text:          #E8ECF7;
    --text-dim:      #94A3B8;
    --text-faint:    #5B6884;
    --good:          #34D399;
    --warn:          #FBBF24;
    --danger:        #F87171;
    --radius-lg:     20px;
    --radius-md:     14px;
    --radius-sm:     10px;
}

*{
    font-family:'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif !important;
}

body, .gradio-container{
    background:
        radial-gradient(1200px 600px at 10% -10%, rgba(99,102,241,.14), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, rgba(34,211,238,.10), transparent 55%),
        var(--bg) !important;
}

.gradio-container{
    max-width: 1480px !important;
    margin: auto !important;
}

/* ---------- Hero header ---------- */

.hero{
    position:relative;
    background: var(--accent-grad);
    padding: 36px 40px;
    border-radius: 24px;
    color:white;
    overflow:hidden;
    box-shadow: 0 20px 50px rgba(99,102,241,.28), 0 4px 12px rgba(0,0,0,.35);
    margin-bottom: 22px;
}

.hero::before{
    content:"";
    position:absolute;
    inset:0;
    background: radial-gradient(500px 200px at 90% 10%, rgba(255,255,255,.22), transparent 70%);
    pointer-events:none;
}

.hero h1{
    font-size: 34px;
    font-weight: 800;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
    display:flex;
    align-items:center;
    gap:12px;
}

.hero p{
    font-size: 15.5px;
    font-weight: 500;
    opacity:.92;
    margin:0;
}

.hero .pill{
    display:inline-flex;
    align-items:center;
    gap:6px;
    background:rgba(255,255,255,.16);
    border:1px solid rgba(255,255,255,.28);
    padding:5px 14px;
    border-radius:999px;
    font-size:12.5px;
    font-weight:600;
    margin-top:14px;
    backdrop-filter: blur(6px);
}

/* ---------- Stat / KPI cards ---------- */

.stat-card{
    background: linear-gradient(180deg, var(--panel-2), var(--panel));
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 4px 6px;
    box-shadow: 0 6px 20px rgba(0,0,0,.28);
    transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.stat-card:hover{
    transform: translateY(-3px);
    border-color: rgba(99,102,241,.5);
    box-shadow: 0 12px 28px rgba(99,102,241,.20);
}

.stat-card label span{
    font-size: 12.5px !important;
    font-weight: 700 !important;
    color: var(--text-dim) !important;
    text-transform: uppercase;
    letter-spacing: .04em;
}

.stat-card input, .stat-card textarea{
    font-size: 26px !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    background: transparent !important;
    border: none !important;
}

/* ---------- General panels / cards ---------- */

.card{
    background: linear-gradient(180deg, rgba(26,35,56,.9), rgba(20,27,46,.9));
    border-radius: var(--radius-lg);
    padding: 22px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 26px rgba(0,0,0,.30);
    margin-bottom: 18px;
    transition: box-shadow .25s ease, border-color .25s ease;
}

.card:hover{
    border-color: rgba(99,102,241,.35);
    box-shadow: 0 14px 32px rgba(0,0,0,.4);
}

.section-title{
    display:flex;
    align-items:center;
    gap:8px;
    font-size: 17px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    margin-bottom: 4px !important;
}

.section-sub{
    color: var(--text-dim) !important;
    font-size: 13px !important;
    margin-top: -4px;
    margin-bottom: 10px !important;
}

/* ---------- Buttons ---------- */

button{
    border-radius: var(--radius-sm) !important;
    font-weight: 700 !important;
    letter-spacing: .01em;
    transition: all .2s ease !important;
}

button.primary, .primary button{
    background: var(--accent-grad) !important;
    border: none !important;
    box-shadow: 0 10px 24px rgba(99,102,241,.35) !important;
}

button:hover{
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(99,102,241,.35) !important;
}

button:active{
    transform: translateY(0px);
}

/* ---------- Inputs ---------- */

textarea, input[type='text'], input[type='number']{
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-soft) !important;
    background: rgba(11,17,32,.7) !important;
    color: var(--text) !important;
}

textarea:focus, input:focus{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.18) !important;
}

::placeholder{
    color: var(--text-faint) !important;
}

/* ---------- Upload box ---------- */

.upload-box{
    border: 2px dashed rgba(99,102,241,.45) !important;
    border-radius: var(--radius-md) !important;
    background: rgba(99,102,241,.05) !important;
    transition: all .2s ease;
}

.upload-box:hover{
    border-color: var(--accent-2) !important;
    background: rgba(34,211,238,.06) !important;
}

/* ---------- Dataframe / table ---------- */
/* Gradio's Dataframe ships its own light-mode styles with high specificity,
   so every rule here is !important and targeted at the raw table tags plus
   the common wrapper classes Gradio uses across versions. */

.table-wrap, .dataframe, [data-testid="dataframe"]{
    background: var(--panel) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}

table{
    border-radius: var(--radius-md);
    overflow: hidden;
    background: var(--panel) !important;
}

table thead, .dataframe thead, [data-testid="dataframe"] thead{
    background: rgba(99,102,241,.18) !important;
}

table thead th, .dataframe thead th, [data-testid="dataframe"] thead th,
table th, .dataframe th{
    color: var(--text) !important;
    background: rgba(99,102,241,.18) !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 11.5px !important;
    letter-spacing: .04em;
    border-color: var(--border-soft) !important;
}

table tbody td, .dataframe tbody td, [data-testid="dataframe"] tbody td,
table td, .dataframe td{
    color: var(--text) !important;
    background: var(--panel) !important;
    border-color: var(--border-soft) !important;
}

table tbody tr:nth-child(even) td,
.dataframe tbody tr:nth-child(even) td{
    background: var(--panel-2) !important;
}

table tbody tr:hover td, .dataframe tbody tr:hover td,
[data-testid="dataframe"] tbody tr:hover td{
    background: rgba(99,102,241,.14) !important;
}

/* cell text that Gradio wraps in an inner span/div */
table td *, .dataframe td *, [data-testid="dataframe"] td *{
    color: var(--text) !important;
}

/* ---------- Labels ---------- */

label > span{
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: var(--text-dim) !important;
}

/* ---------- Sliders ---------- */

input[type='range']{
    accent-color: var(--accent) !important;
    background: transparent !important;
}

input[type='range']::-webkit-slider-runnable-track{
    background: var(--border-soft) !important;
    border-radius: 999px !important;
    height: 6px !important;
}

input[type='range']::-moz-range-track{
    background: var(--border-soft) !important;
    border-radius: 999px !important;
    height: 6px !important;
}

input[type='range']::-webkit-slider-thumb{
    background: var(--accent-2) !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 0 0 4px rgba(34,211,238,.20) !important;
}

input[type='range']::-moz-range-thumb{
    background: var(--accent-2) !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 0 0 4px rgba(34,211,238,.20) !important;
}

/* the little numeric readout Gradio renders next to a slider */
.gradio-container [data-testid="number-input"],
.gradio-container .slider input[type='number']{
    color: var(--text) !important;
    background: transparent !important;
}

/* ---------- Dropdown ---------- */

.dropdown, select{
    background: rgba(11,17,32,.7) !important;
    border-radius: var(--radius-sm) !important;
}

/* ---------- Tabs ---------- */

.tab-nav button{
    font-weight: 700 !important;
    color: var(--text-dim) !important;
    background: transparent !important;
    box-shadow:none !important;
}

.tab-nav button.selected{
    color: var(--text) !important;
    border-bottom: 2px solid var(--accent-2) !important;
}

/* ---------- Footer ---------- */

.footer{
    text-align:center;
    color: var(--text-faint);
    font-size: 12.5px;
    padding: 18px;
    margin-top: 8px;
    border-top: 1px solid var(--border-soft);
}

/* ---------- Scrollbars ---------- */

::-webkit-scrollbar{ width:10px; height:10px; }
::-webkit-scrollbar-thumb{
    background: linear-gradient(180deg,#6366F1,#22D3EE);
    border-radius: 20px;
}
::-webkit-scrollbar-track{ background: transparent; }

/* ---------- Misc ---------- */

.mono textarea, .mono input{
    font-family:'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}
"""

THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), "sans-serif"],
).set(
    body_background_fill="#0B1120",
    background_fill_primary="#141B2E",
    background_fill_secondary="#1A2338",
    border_color_primary="#263049",
    block_background_fill="#141B2E",
    block_border_color="#263049",
    block_label_text_color="#94A3B8",
    body_text_color="#E8ECF7",
    button_primary_background_fill="linear-gradient(120deg,#6366F1,#22D3EE)",
    button_primary_text_color="#ffffff",
)

# ==========================================================
# HELPERS
# ==========================================================

def _score_badge(score):
    """Return a little emoji indicator for a 0-100 score."""
    try:
        score = float(score)
    except (TypeError, ValueError):
        return ""
    if score >= 75:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


# ==========================================================
# APP LAYOUT
# ==========================================================

with gr.Blocks(title="AI Resume Screening System", css=CUSTOM_CSS, theme=THEME) as app:

    # ------------------------------------------------------
    # HERO HEADER
    # ------------------------------------------------------

    gr.HTML(
        """
        <div class="hero">
            <h1>🤖 AI Resume Screening System</h1>
            <p>Parse resumes, extract skills &amp; education, match against any job description,
               and rank candidates automatically — powered by NLP.</p>
            <span class="pill">⚡ Instant parsing &nbsp;•&nbsp; 🎯 Smart JD matching &nbsp;•&nbsp; 📊 Auto-ranked results</span>
        </div>
        """
    )

    # ------------------------------------------------------
    # DASHBOARD / KPI ROW
    # ------------------------------------------------------

    with gr.Row():
        with gr.Column(elem_classes=["stat-card"]):
            total_resumes = gr.Number(label="📄  Total Resumes", value=0, interactive=False)
        with gr.Column(elem_classes=["stat-card"]):
            highest_score = gr.Number(label="🏆  Highest Score", value=0, interactive=False)
        with gr.Column(elem_classes=["stat-card"]):
            average_match = gr.Number(label="🎯  Average Match %", value=0, interactive=False)
        with gr.Column(elem_classes=["stat-card"]):
            top_candidate = gr.Textbox(label="⭐  Top Candidate", value="--", interactive=False)

    # ------------------------------------------------------
    # MAIN: UPLOAD + RANKING
    # ------------------------------------------------------

    with gr.Row(equal_height=True):

        # ---------------- LEFT PANEL ----------------
        with gr.Column(scale=1, elem_classes=["card"]):

            gr.Markdown("### 📄 Job Description", elem_classes=["section-title"])
            gr.Markdown("Paste the role you're hiring for — skills mentioned here drive the match score.",
                        elem_classes=["section-sub"])

            job_description = gr.Textbox(
                placeholder="e.g. Looking for a Python developer with experience in Machine Learning, "
                            "Flask, SQL and AWS...",
                lines=14,
                show_label=False,
                elem_classes=["mono"],
            )

            gr.Markdown("### 📂 Upload Resumes", elem_classes=["section-title"])
            gr.Markdown("PDF, DOCX or TXT — drop in as many candidates as you like.",
                        elem_classes=["section-sub"])

            resume_files = gr.File(
                file_count="multiple",
                file_types=[".pdf", ".docx", ".txt"],
                label="Upload Multiple Resumes",
                elem_classes=["upload-box"],
            )

            analyze_btn = gr.Button("🚀  Analyze Candidates", variant="primary", size="lg", elem_classes=["primary"])

            download_csv = gr.File(label="📥  Download Ranked CSV", interactive=False)

        # ---------------- RIGHT PANEL ----------------
        with gr.Column(scale=2, elem_classes=["card"]):

            gr.Markdown("### 🏆 Candidate Ranking", elem_classes=["section-title"])
            gr.Markdown("Sorted automatically by Final Score (40% resume quality + 60% JD match).",
                        elem_classes=["section-sub"])

            ranking_table = gr.Dataframe(
                headers=["Rank", "Name", "Resume Score", "Job Match %", "Final Score"],
                datatype=["number", "str", "number", "number", "number"],
                interactive=False,
                wrap=True,
                row_count=10,
                col_count=(5, "fixed"),
            )

    # ------------------------------------------------------
    # CANDIDATE DETAILS
    # ------------------------------------------------------

    with gr.Column(elem_classes=["card"]):

        gr.Markdown("### 👤 Candidate Details", elem_classes=["section-title"])
        gr.Markdown("Pick a candidate from the dropdown to inspect their full profile.",
                    elem_classes=["section-sub"])

        candidate_selector = gr.Dropdown(label="Select Candidate", choices=[], interactive=True)

        with gr.Row():

            with gr.Column(scale=1):
                candidate_name = gr.Textbox(label="Name", interactive=False)
                candidate_email = gr.Textbox(label="Email", interactive=False)
                candidate_phone = gr.Textbox(label="Phone", interactive=False)
                candidate_urls = gr.Textbox(label="LinkedIn / GitHub / Portfolio", interactive=False)

            with gr.Column(scale=2):
                candidate_skills = gr.Textbox(label="Skills", lines=4, interactive=False)
                candidate_education = gr.Textbox(label="Education", lines=2, interactive=False)
                candidate_organizations = gr.Textbox(label="Organizations", lines=2, interactive=False)

        with gr.Row():
            resume_score = gr.Slider(minimum=0, maximum=100, label="Resume Score", interactive=False)
            job_match = gr.Slider(minimum=0, maximum=100, label="Job Match %", interactive=False)
            final_score = gr.Slider(minimum=0, maximum=100, label="Final Score", interactive=False)

        with gr.Accordion("📃 Full Resume Text", open=False):
            candidate_resume = gr.Textbox(label="", lines=15, interactive=False, show_label=False,
                                           elem_classes=["mono"])

    gr.HTML('<div class="footer">Built with ❤️ using Gradio · AI Resume Screening System</div>')

    # ==========================================================
    # STATE
    # ==========================================================

    parsed_state = gr.State([])

    # ==========================================================
    # CALLBACKS
    # ==========================================================

    def analyze_candidates(job_description, uploaded_files, progress=gr.Progress()):

        if not uploaded_files:
            raise gr.Error("Please upload at least one resume.")

        if not job_description.strip():
            raise gr.Error("Please enter a job description.")

        progress(0.05, desc="Saving uploaded files...")

        temp_dir = tempfile.mkdtemp()

        try:
            # Save uploaded files
            for file in uploaded_files:
                destination = os.path.join(temp_dir, os.path.basename(file.name))
                shutil.copy(file.name, destination)

            progress(0.25, desc="Parsing resumes...")

            # Parse resumes
            parsed_resumes = parse_multiple_resumes(temp_dir)

            if not parsed_resumes:
                raise gr.Error("Couldn't parse any of the uploaded resumes. Please check the file formats.")

            progress(0.5, desc="Building candidate table...")

            # Create dataframe
            df = create_dataframe(parsed_resumes)

            progress(0.6, desc="Extracting job description skills...")

            # JD Skills
            jd_skills = extract_jd_skills(job_description)

            progress(0.75, desc="Scoring candidates against the job description...")

            # Calculate scores
            for i, resume in enumerate(parsed_resumes):

                result = calculate_job_match(resume, jd_skills)

                r_score = df.loc[i, "Resume Score"]
                f_score = calculate_final_score(r_score, result["job_match"])

                df.loc[i, "Job Match %"] = result["job_match"]
                df.loc[i, "Final Score"] = f_score

                # FIX: stash the computed scores on the resume dict itself so
                # show_candidate() can display real Job Match % / Final Score
                # values instead of the previous hardcoded None.
                resume["resume_score"] = r_score
                resume["job_match"] = result["job_match"]
                resume["final_score"] = f_score

            progress(0.9, desc="Ranking candidates...")

            # Rank
            df = rank_candidates(df)

            # Dashboard Statistics
            total = len(df)
            highest = float(df["Final Score"].max())
            average = round(float(df["Job Match %"].mean()), 2)
            top = df.iloc[0]["Name"]

            # CSV
            csv_file = export_to_csv(df)

            # Dropdown Choices
            choices = df["Name"].tolist()

            progress(1.0, desc="Done!")

            return (
                df[["Rank", "Name", "Resume Score", "Job Match %", "Final Score"]],
                csv_file,
                total,
                highest,
                average,
                top,
                gr.update(choices=choices, value=choices[0] if choices else None),
                parsed_resumes,
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def show_candidate(name, parsed_resumes):

        if not name:
            return [None] * 11

        for resume in parsed_resumes:

            if resume["candidate"]["name"] == name:

                # Use the scores computed during analysis if present (this is
                # the normal path); fall back to recomputing the resume score
                # only, since job/final score need the job description.
                r_score = resume.get("resume_score", calculate_resume_score(resume))
                j_match = resume.get("job_match", 0)
                f_score = resume.get("final_score", 0)

                return (
                    resume["candidate"]["name"],
                    ", ".join(resume["candidate"]["emails"]) or "—",
                    ", ".join(resume["candidate"]["phone_numbers"]) or "—",
                    ", ".join(resume["candidate"]["urls"]) or "—",
                    ", ".join(resume["skills"]) or "—",
                    ", ".join(resume["education"]["degree"]) or "—",
                    ", ".join(resume["organizations"]) or "—",
                    r_score,
                    j_match,
                    f_score,
                    resume["text"],
                )

        return [None] * 11

    analyze_btn.click(
        fn=analyze_candidates,
        inputs=[job_description, resume_files],
        outputs=[
            ranking_table,
            download_csv,
            total_resumes,
            highest_score,
            average_match,
            top_candidate,
            candidate_selector,
            parsed_state,
        ],
    )

    candidate_selector.change(
        fn=show_candidate,
        inputs=[candidate_selector, parsed_state],
        outputs=[
            candidate_name,
            candidate_email,
            candidate_phone,
            candidate_urls,
            candidate_skills,
            candidate_education,
            candidate_organizations,
            resume_score,
            job_match,
            final_score,
            candidate_resume,
        ],
    )


if __name__ == "__main__":
    app.launch()
