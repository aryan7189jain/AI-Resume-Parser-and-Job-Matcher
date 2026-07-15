# ==========================================================
# IMPORTS
# ==========================================================

import os
import json
import re
import string

import nltk
import pdfplumber
import docx

from bs4 import BeautifulSoup
import contractions
import emoji

from transformers import pipeline

# ==========================================================
# LOAD NLP MODELS
# ==========================================================

# Lazy loading (loads only once)
ner = None


def get_ner():
    """
    Load the BERT Named Entity Recognition model only once.
    """

    global ner

    if ner is None:

        print("Loading BERT NER model...")

        ner = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple"
        )

        print("BERT NER model loaded successfully!")

    return ner


# ==========================================================
# REGEX PATTERNS
# ==========================================================

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

PHONE_PATTERN = (
    r"(?:\+?\d{1,3}[-.\s]?)?"
    r"(?:\(?\d{3,5}\)?[-.\s]?)?"
    r"\d{3,5}[-.\s]?\d{4,6}"
)

URL_PATTERN = r"(https?://[^\s]+|www\.[^\s]+)"


# ==========================================================
# LOAD RESOURCES
# ==========================================================

def load_list(file_path):
    """
    Load a text file and return a cleaned list.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip()
        ]


SKILLS = load_list("skills.txt")

COLLEGES = load_list("colleges.txt")

DEGREES = load_list("degrees.txt")


# ==========================================================
# INITIALIZATION
# ==========================================================

print(f"Skills Loaded      : {len(SKILLS)}")
print(f"Colleges Loaded   : {len(COLLEGES)}")
print(f"Degrees Loaded    : {len(DEGREES)}")

# ==========================================================
# PREPROCESSING
# ==========================================================

def extract_text(file_path):
    """
    Extract text from PDF, DOCX, or TXT resume.
    """

    filename = file_path.lower()

    # -------------------------
    # PDF
    # -------------------------
    if filename.endswith(".pdf"):

        text = ""

        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        return text

    # -------------------------
    # DOCX
    # -------------------------
    elif filename.endswith(".docx"):

        document = docx.Document(file_path)

        text = "\n".join(
            para.text
            for para in document.paragraphs
        )

        return text

    # -------------------------
    # TXT
    # -------------------------
    elif filename.endswith(".txt"):

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:

        raise ValueError(
            f"Unsupported file format: {file_path}"
        )


# ----------------------------------------------------------


def load_resumes(folder_path):
    """
    Load every resume from a folder.
    """

    resumes = []

    for file in os.listdir(folder_path):

        if file.lower().endswith(
            (".pdf", ".docx", ".txt")
        ):

            full_path = os.path.join(folder_path, file)

            resumes.append({

                "filename": file,

                "filepath": full_path,

                "text": extract_text(full_path)

            })

    return resumes


# ----------------------------------------------------------


def process_data(text):
    """
    Clean resume text before parsing.
    """

    # Remove HTML
    text = BeautifulSoup(
        text,
        "html.parser"
    ).get_text(separator=" ")

    # Expand contractions
    text = contractions.fix(text)

    # Remove emojis
    text = emoji.replace_emoji(
        text,
        replace=""
    )

    # Keep useful punctuation
    punctuation = string.punctuation

    punctuation = punctuation.replace("@", "")
    punctuation = punctuation.replace(".", "")
    punctuation = punctuation.replace("+", "")
    punctuation = punctuation.replace("-", "")
    punctuation = punctuation.replace("/", "")
    punctuation = punctuation.replace("#", "")

    text = text.translate(
        str.maketrans("", "", punctuation)
    )

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()

# ==========================================================
# EXTRACTION FUNCTIONS
# ==========================================================

def extract_name(text):
    """
    Extract candidate name from the first line of the resume.
    """

    lines = text.strip().splitlines()

    if not lines:
        return None

    first_line = lines[0].strip()

    if (
        len(first_line.split()) <= 4
        and not re.search(r"\d", first_line)
    ):
        return first_line

    return None


# ----------------------------------------------------------


def extract_emails(text):
    """
    Extract all email addresses.
    """

    return list(set(
        re.findall(EMAIL_PATTERN, text)
    ))


# ----------------------------------------------------------


def extract_phone_numbers(text):
    """
    Extract phone numbers.
    """

    return list(set(
        re.findall(PHONE_PATTERN, text)
    ))


# ----------------------------------------------------------


def extract_urls(text):
    """
    Extract LinkedIn, GitHub, Portfolio URLs.
    """

    return list(set(
        re.findall(URL_PATTERN, text)
    ))


# ----------------------------------------------------------


def extract_skills(text):
    """
    Extract skills from skills.txt
    """

    found = []

    text_lower = text.lower()

    for skill in SKILLS:

        if skill.lower() in text_lower:
            found.append(skill)

    return sorted(set(found))


# ----------------------------------------------------------


def extract_education(text):
    """
    Extract colleges and degrees.
    """

    education = {
        "college": [],
        "degree": []
    }

    text_lower = text.lower()

    # Colleges
    for college in COLLEGES:

        pattern = r"\b" + re.escape(college.lower()) + r"\b"

        if re.search(pattern, text_lower):
            education["college"].append(college)

    # Degrees
    for degree in DEGREES:

        pattern = r"\b" + re.escape(degree.lower()) + r"\b"

        if re.search(pattern, text_lower):
            education["degree"].append(degree)

    education["college"] = sorted(
        list(set(education["college"]))
    )

    education["degree"] = sorted(
        list(set(education["degree"]))
    )

    return education


# ----------------------------------------------------------


def extract_entities(text, candidate_name=None):
    """
    Extract PERSON and ORGANIZATION entities using BERT.
    """

    persons = []
    organizations = []

    ner_results = get_ner()(text)

    for entity in ner_results:

        if entity["entity_group"] == "PER":

            if entity["word"] != candidate_name:
                persons.append(entity["word"])

        elif entity["entity_group"] == "ORG":

            if entity["word"] != candidate_name:
                organizations.append(entity["word"])

    persons = sorted(list(set(persons)))
    organizations = sorted(list(set(organizations)))

    return persons, organizations

# ==========================================================
# RESUME PARSING
# ==========================================================

def extract_resume_info(text):
    """
    Parse a resume and return structured information.
    """

    # -------------------------
    # Clean Resume
    # -------------------------

    text = process_data(text)

    # -------------------------
    # Candidate Details
    # -------------------------

    candidate_name = extract_name(text)

    emails = extract_emails(text)

    phones = extract_phone_numbers(text)

    urls = extract_urls(text)

    # -------------------------
    # Skills
    # -------------------------

    skills = extract_skills(text)

    # -------------------------
    # Education
    # -------------------------

    education = extract_education(text)

    # -------------------------
    # BERT Entity Extraction
    # -------------------------

    persons, organizations = extract_entities(
        text,
        candidate_name
    )

    # Remove colleges from organizations

    organizations = [
        org
        for org in organizations
        if org not in education["college"]
    ]

    # -------------------------
    # Resume Dictionary
    # -------------------------

    resume = {

        "candidate":{

            "name": candidate_name,

            "emails": emails,

            "phone_numbers": phones,

            "urls": urls

        },

        "skills": skills,

        "education": education,

        "organizations": organizations,

        "person_names": persons,

        "text": text
        

    }

    return resume

# ==========================================================
# RESUME SCORING
# ==========================================================

def calculate_resume_score(resume):
    """
    Calculate resume quality score out of 100.
    """

    score = 0

    # ------------------------------------------------------
    # Candidate Details (40 Marks)
    # ------------------------------------------------------

    if resume["candidate"]["name"]:
        score += 10

    if resume["candidate"]["emails"]:
        score += 10

    if resume["candidate"]["phone_numbers"]:
        score += 10

    if resume["candidate"]["urls"]:
        score += 10

    # ------------------------------------------------------
    # Skills (30 Marks)
    # ------------------------------------------------------

    skill_count = len(resume["skills"])

    score += min(skill_count * 2, 30)

    # ------------------------------------------------------
    # Education (15 Marks)
    # ------------------------------------------------------

    education_count = max(
        len(resume["education"]["college"]),
        len(resume["education"]["degree"])
    )

    score += min(education_count * 7.5, 15)

    # ------------------------------------------------------
    # Organizations (10 Marks)
    # ------------------------------------------------------

    organization_count = len(resume["organizations"])

    score += min(organization_count * 2, 10)

    # ------------------------------------------------------
    # Resume Length (5 Marks)
    # ------------------------------------------------------

    word_count = len(resume["text"].split())

    if word_count >= 300:
        score += 5

    elif word_count >= 200:
        score += 4

    elif word_count >= 100:
        score += 3

    elif word_count >= 50:
        score += 2

    return round(score, 2)


def extract_jd_skills(job_description):
    """
    Extract required skills from the job description.
    """

    job_description = process_data(job_description)

    found = []

    for skill in SKILLS:

        if skill.lower() in job_description.lower():
            found.append(skill)

    return sorted(set(found))

def calculate_job_match(resume, jd_skills):
    """
    Compare resume skills with JD skills.
    """

    resume_skills = set(
        skill.lower()
        for skill in resume["skills"]
    )

    jd_skills = set(
        skill.lower()
        for skill in jd_skills
    )

    matched = resume_skills.intersection(jd_skills)

    missing = jd_skills - resume_skills

    extra = resume_skills - jd_skills

    if len(jd_skills) == 0:
        match_percent = 0

    else:
        match_percent = (
            len(matched) / len(jd_skills)
        ) * 100

    return {

        "matched_skills": sorted(matched),

        "missing_skills": sorted(missing),

        "extra_skills": sorted(extra),

        "job_match": round(match_percent, 2)

    }
    
def calculate_final_score(
    resume_score,
    job_match,
    resume_weight=0.4,
    job_weight=0.6
):
    """
    Calculate final ATS score.
    """

    final_score = (
        resume_score * resume_weight +
        job_match * job_weight
    )

    return round(final_score, 2)

def parse_multiple_resumes(folder_path):
    """
    Read and parse all resumes from a folder.
    """

    resumes = load_resumes(folder_path)

    parsed_resumes = []

    for resume in resumes:

        try:

            parsed = extract_resume_info(resume["text"])

            parsed["filename"] = resume["filename"]
            parsed["filepath"] = resume["filepath"]

            parsed_resumes.append(parsed)

        except Exception as e:

            print(f"Error parsing {resume['filename']}: {e}")

    return parsed_resumes

import pandas as pd

def create_dataframe(parsed_resumes):
    """
    Convert parsed resumes into a pandas DataFrame.
    """

    rows = []

    for resume in parsed_resumes:

        resume_score = calculate_resume_score(resume)

        rows.append({
            "Filename": resume["filename"],
            "File Path": resume["filepath"],
            # Candidate Details
            "Name": resume["candidate"]["name"],
            "Email": ", ".join(resume["candidate"]["emails"]),
            "Phone": ", ".join(resume["candidate"]["phone_numbers"]),
            "URLs": ", ".join(resume["candidate"]["urls"]),

            # Skills
            "Skills": ", ".join(resume["skills"]),
            "Skill Count": len(resume["skills"]),

            # Education
            "College": ", ".join(resume["education"]["college"]),
            "Degree": ", ".join(resume["education"]["degree"]),

            # Organizations
            "Organizations": ", ".join(resume["organizations"]),
            "Organization Count": len(resume["organizations"]),

            # Resume
            "Resume Length": len(resume["text"].split()),
            "Resume Score": resume_score,

            # Future Columns
            "Job Match %": None,
            "Final Score": None,

            "Experience": None,
            "Projects": None,
            "Certifications": None,

            "Resume Text": resume["text"]

        })

    return pd.DataFrame(rows)

def rank_candidates(df):
    """
    Rank candidates using Final Score.
    """

    if "Final Score" not in df.columns:
        raise ValueError("Final Score column not found.")

    df = df.sort_values(
        by="Final Score",
        ascending=False
    ).reset_index(drop=True)

    df["Rank"] = df.index + 1

    return df

def export_to_csv(df, filename="ranked_candidates.csv"):
    """
    Save DataFrame to CSV.
    """

    df.to_csv(filename, index=False)

    return filename

def get_top_candidates(df, top_n=5):
    """
    Return top N ranked candidates.
    """

    return df.head(top_n)

