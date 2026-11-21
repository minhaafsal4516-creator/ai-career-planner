# CHECKPOINT 1 — "Hello, AI builder"
# This is the file every attendee starts with. If you can see this page
# in the preview on the right, your setup is done.
# It uses the same page layout as the final app, so the look never changes.

import streamlit as st
from google import genai
from google.genai import errors, types

SYSTEM_PROMPT = """
You are a Architecture career counsellor for students and job seekers in India.
Given a person's profile, reply in Markdown with exactly these sections:
## 3 roles that fit you  — Job Title, Why it fits, Key Responsibilities, quired Skills, Entry Requirements, Salary Range,
Career Growth.
## Your skill gaps        — Create a table with columns: Required Skills, Current Skill Level, Missing Skills and How to Improve.
## Your 90-day roadmap    — Create a realistic 90-day action plan divided into three stages: Days 1–30, 31–60 and 61–90. Include weekly tasks.
## One thing to do today  — Give one achievable task the user can complete today in under 30 minutes.
## Opportunities          — Recommend 3 suitable career roles with job descriptions, responsibilities and typical entry-level salary ranges in India.
## Learning resources     — Recommend relevant courses, certifications, practical training and free learning resources.
Rules: never promise a job or a salary, simple English, under 450 words, your own rule, Personalize recommendations according to the user's actual profile, Do not recommend unrealistic or unrelated career paths, Use simple, encouraging and professional language, 
Include realistic Indian salary estimates and identify them as indicative, 
Never invent qualifications, job openings or course availability, 
Ask for missing essential information rather than making assumptions, 
Prioritize practical career development over generic motivation.
"""

st.set_page_config(page_title="AI Career Planner", page_icon="🎯", layout="centered")

# A little CSS (page styling). "centered" layout keeps everything in a middle
# column; we make that column a bit wider so the 3 role cards fit side by side.
st.markdown(
    """
    <style>
    [data-testid="stMainBlockContainer"] { max-width: 1000px; padding-top: 2.5rem; }
    .hero { text-align: center; margin-bottom: 1.5rem; }
    .hero h1 { font-size: 2.6rem; margin-bottom: 0.2rem; }
    .hero p { color: #475569; font-size: 1.1rem; margin: 0; }
    .step { color: #2563EB; font-weight: 600; font-size: 0.85rem;
            letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem; }
    .score { font-size: 2.4rem; font-weight: 700; color: #2563EB; line-height: 1.1; }
    .score span { font-size: 1rem; font-weight: 500; color: #475569; }
    .footer { text-align: center; color: #64748B; font-size: 0.85rem; padding: 0.5rem 0 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Centered title and subtitle
st.markdown(
    """
    <div class="hero">
      <h1>🎯 AI Career Planner</h1>
      <p>My first AI product, built by Minha.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Profile form
with st.form("about_you"):
    st.subheader("About you")

    name_col, education_col = st.columns(2)
    with name_col:
        name = st.text_input("Your name")
    with education_col:
        education = st.selectbox(
            "Highest education",
            [
                "Plus Two / 12th",
                "Diploma",
                "B.Tech / B.E.",
                "B.Sc / BCA",
                "B.Com / BBA",
                "BA",
                "Master's degree",
                "Other",
            ],
        )

    status = st.radio(
        "Where are you right now?",
        [
            "Student",
            "Graduate looking for a job",
            "Working, want to switch",
            "Career break",
        ],
        horizontal=True,
    )

    skills_col, interests_col = st.columns(2)
    with skills_col:
        skills = st.text_area("Skills you already have")
    with interests_col:
        interests = st.text_area("What do you enjoy?")

    goal = st.text_input("Your goal")
    hours = st.slider("Hours per week you can study", 2, 40, 10)

    submitted = st.form_submit_button(
        "🚀 Plan my career",
        type="primary",
        use_container_width=True,
    )

if submitted:
    missing = []
    if not name.strip():
        missing.append("Your name")
    if not skills.strip():
        missing.append("Skills you already have")
    if not goal.strip():
        missing.append("Your goal")

    if missing:
        st.session_state.profile_answers = None
        st.session_state.ai_answer = None
        st.warning("Please fill: " + ", ".join(missing))
    else:
        st.session_state.profile_answers = {
            "name": name.strip(),
            "education": education,
            "status": status,
            "skills": skills.strip(),
            "interests": interests.strip(),
            "goal": goal.strip(),
            "hours_per_week": hours,
        }
        st.session_state.ai_answer = None

        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"],
                http_options=types.HttpOptions(api_version="v1beta"),
            )

            def call_gemini(model):
                profile = "\n".join([
                    f"Name: {name.strip()}",
                    f"Highest education: {education}",
                    f"Where are you right now: {status}",
                    f"Skills: {skills.strip()}",
                    f"What you enjoy: {interests.strip()}",
                    f"Goal: {goal.strip()}",
                    f"Hours per week available to study: {hours}",
                ])
                return client.models.generate_content(
                    model=model,
                    contents=f"Person's profile:\n{profile}",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                    ),
                )

            with st.spinner("Thinking about your career..."):
                try:
                    response = call_gemini("gemini-3.5-flash-lite")
                except errors.APIError as first_error:
                    if first_error.code not in (429, 500, 503, 504):
                        raise
                    try:
                        response = call_gemini("gemini-3.5-flash-lite")
                    except errors.APIError as retry_error:
                        if retry_error.code not in (429, 500, 503, 504):
                            raise
                        response = call_gemini("gemini-3.5-flash-lite")

            st.session_state.ai_answer = response.text
        except KeyError:
            st.error(
                "Gemini API key is missing. Add GEMINI_API_KEY to your Streamlit secrets, then try again."
            )
        except errors.APIError as error:
            if error.code == 429:
                st.error("Gemini's usage limit was reached. Check your API quota, then try again.")
            elif error.code in (500, 503, 504):
                st.error("Gemini is temporarily unavailable. Please wait a moment and try again.")
            elif error.code in (401, 403):
                st.error("Gemini rejected the API key. Check that it is correct and has API access.")
            else:
                st.error(f"Gemini could not complete the request (error {error.code}). Please try again.")
        except Exception as error:
            st.error(
                f"Something unexpected happened ({type(error).__name__}). "
                "Check the app logs for details, then try again."
            )

if st.session_state.get("ai_answer"):
    with st.container(border=True):
        st.markdown(st.session_state.ai_answer)

# Footer
st.divider()
st.markdown(
    '<div class="footer">Built at the Techolas AI Wing weekend · AI suggestions, not guarantees.</div>',
    unsafe_allow_html=True,
)























# import streamlit as st
# import time
# from google import genai
# from google.genai import errors


# # --------------------------------------------------
# # PAGE CONFIGURATION
# # --------------------------------------------------

# st.set_page_config(
#     page_title="AI Career Planner",
#     page_icon="🎯",
#     layout="wide"
# )


# # --------------------------------------------------
# # CUSTOM CSS
# # --------------------------------------------------

# st.markdown("""
# <style>

#     .stApp {
#         background-color: #F7F8FC;
#     }

#     .main-title {
#         font-size: 42px;
#         font-weight: 800;
#         color: #20243A;
#         text-align: center;
#         margin-bottom: 5px;
#     }

#     .subtitle {
#         font-size: 17px;
#         color: #666B80;
#         text-align: center;
#         margin-bottom: 35px;
#     }

#     .section-title {
#         font-size: 23px;
#         font-weight: 700;
#         color: #20243A;
#         margin-top: 20px;
#     }

#     .result-box {
#         background-color: white;
#         padding: 25px;
#         border-radius: 14px;
#         border: 1px solid #E5E7EF;
#         margin-bottom: 20px;
#     }

#     div.stButton > button {
#         background-color: #5B5FEF;
#         color: white;
#         border-radius: 9px;
#         border: none;
#         padding: 12px 25px;
#         font-weight: 600;
#         width: 100%;
#     }

#     div.stButton > button:hover {
#         background-color: #4448D8;
#         color: white;
#     }

#     .footer {
#         text-align: center;
#         color: #888888;
#         font-size: 13px;
#         margin-top: 50px;
#     }

# </style>
# """, unsafe_allow_html=True)


# # --------------------------------------------------
# # CAREER COUNSELLOR SYSTEM PROMPT
# # --------------------------------------------------

# SYSTEM_PROMPT = """
# You are an experienced and practical AI Career Counsellor.

# Your role is to guide students, fresh graduates and job seekers
# towards suitable career opportunities based on their education,
# skills, interests, experience and career goals.

# The user may be from India. Consider the Indian education system,
# job market, entry-level opportunities and salary ranges.

# IMPORTANT INSTRUCTIONS:

# 1. Personalise the recommendations using the user's actual profile.
# 2. Do not recommend careers only because they are popular.
# 3. Recommend realistic career paths based on the user's current
#    abilities and interests.
# 4. Do not invent qualifications, experience or achievements.
# 5. Identify skill gaps honestly.
# 6. Give practical actions that can be completed within the
#    user's available time.
# 7. Keep the language simple, clear and professional.
# 8. Avoid unnecessary motivational statements.
# 9. Do not guarantee employment, salary or career success.
# 10. Salary ranges must be indicative estimates for India.
#     Mention that they vary by location, company and experience.
# 11. Suggest relevant learning resources. Do not invent courses,
#     certifications, institutions or website links.
# 12. Avoid repeating the same information in different sections.

# STRICT OUTPUT FORMAT:

# ## 1. Three Roles That Fit You

# Recommend exactly THREE suitable career roles.

# For each role include:

# - Job Title
# - Why It Fits
# - Key Responsibilities
# - Required Skills
# - Entry Requirements
# - Indicative Entry-Level Salary in India
# - Career Growth

# Rank the roles from most suitable to least suitable.

# ## 2. Your Skill Gaps

# Create a table with these columns:

# | Required Skills | Current Skill Level | Missing Skills | How to Improve |

# Identify the important skills the user needs to develop
# for the recommended career roles.

# Do not assume the user has a skill unless they mentioned it.

# ## 3. Your 90-Day Roadmap

# Divide the roadmap into three stages:

# ### Days 1–30: Foundation
# ### Days 31–60: Skill Development
# ### Days 61–90: Career Preparation

# Provide practical weekly tasks for each stage.

# Consider the user's available learning hours per week.

# Include measurable outcomes wherever possible.

# ## 4. One Thing to Do Today

# Suggest ONE specific, achievable task that the user
# can complete in less than 30 minutes.

# It must be relevant to their career goal.

# ## 5. Learning Resources

# Recommend relevant resources such as:

# - Free online courses
# - Professional certifications
# - Learning platforms
# - Practical projects
# - Relevant training opportunities

# Clearly distinguish free and paid resources.

# Keep the complete response concise, useful and personalised.
# """


# # --------------------------------------------------
# # GEMINI API FUNCTION
# # --------------------------------------------------

# def generate_career_plan(profile):

#     try:
#         api_key = st.secrets["GEMINI_API_KEY"]
#     except Exception:
#         raise ValueError(
#             "Gemini API key is missing. Add GEMINI_API_KEY "
#             "to your Streamlit secrets."
#         )

#     client = genai.Client(api_key=api_key)

#     user_prompt = f"""
#     Analyse the following user profile and create a personalised
#     career guidance plan.

#     USER PROFILE:

#     Name: {profile['name']}

#     Education: {profile['education']}

#     Current Status: {profile['status']}

#     Skills: {profile['skills']}

#     Interests: {profile['interests']}

#     Career Goal: {profile['goal']}

#     Available Learning Time: {profile['hours']} hours per week.

#     Provide recommendations based only on this information.
#     Follow the required output format exactly.
#     """

#     # Primary model followed by fallback model
#     models = [
#         "gemini-3.5-flash",
#         "gemini-3.5-flash lite"
#     ]

#     last_error = None

#     for model in models:

#         for attempt in range(3):

#             try:

#                 response = client.models.generate_content(
#                     model=model,
#                     contents=user_prompt,
#                     config={
#                         "system_instruction": SYSTEM_PROMPT,
#                         "temperature": 0.5,
#                         "max_output_tokens": 6000
#                     }
#                 )

#                 if response.text:
#                     return response.text

#                 raise ValueError(
#                     "Gemini returned an empty response. Please try again."
#                 )

#             except errors.APIError as e:

#                 last_error = e

#                 error_code = getattr(e, "code", None)

#                 # Retry temporary server and rate-limit errors
#                 if error_code in [429, 500, 503, 504]:

#                     if attempt < 2:
#                         time.sleep(2 ** (attempt + 1))
#                         continue

#                     # Move to fallback model
#                     break

#                 # Other API errors should be shown immediately
#                 raise e

#             except ValueError:
#                 raise

#             except Exception as e:
#                 last_error = e
#                 break

#     raise last_error or Exception(
#         "Unable to generate the career plan."
#     )


# # --------------------------------------------------
# # HEADER
# # --------------------------------------------------

# st.markdown(
#     '<div class="main-title">🎯 AI Career Planner</div>',
#     unsafe_allow_html=True
# )

# st.markdown(
#     '<div class="subtitle">'
#     'Discover suitable career paths and build a practical plan '
#     'for your future.'
#     '</div>',
#     unsafe_allow_html=True
# )


# # --------------------------------------------------
# # USER PROFILE FORM
# # --------------------------------------------------

# st.markdown(
#     '<div class="section-title">Tell us about yourself</div>',
#     unsafe_allow_html=True
# )

# st.write(
#     "Share a few details so we can understand your background "
#     "and recommend suitable career paths."
# )

# with st.form("career_form"):

#     col1, col2 = st.columns(2)

#     with col1:

#         name = st.text_input(
#             "Your Name",
#             placeholder="Enter your name"
#         )

#         education = st.selectbox(
#             "Highest Education / Current Education",
#             [
#                 "High School",
#                 "Diploma",
#                 "Undergraduate",
#                 "Postgraduate",
#                 "Doctorate",
#                 "Other"
#             ]
#         )

#         status = st.selectbox(
#             "Current Status",
#             [
#                 "School Student",
#                 "College Student",
#                 "Recent Graduate",
#                 "Working Professional",
#                 "Looking for a Job",
#                 "Career Change"
#             ]
#         )

#     with col2:

#         skills = st.text_area(
#             "Your Current Skills",
#             placeholder=(
#                 "Example: Communication, Python, "
#                 "Design, Writing, Excel..."
#             ),
#             height=110
#         )

#         interests = st.text_area(
#             "Your Interests",
#             placeholder=(
#                 "Example: Technology, Business, "
#                 "Healthcare, Creativity..."
#             ),
#             height=110
#         )

#     goal = st.text_area(
#         "What is your Career Goal?",
#         placeholder=(
#             "Example: I want to get a job in the IT industry "
#             "or start my own business."
#         ),
#         height=100
#     )

#     hours = st.slider(
#         "How many hours can you spend learning per week?",
#         min_value=1,
#         max_value=40,
#         value=5
#     )

#     submitted = st.form_submit_button(
#         "Generate My Career Plan"
#     )


# # --------------------------------------------------
# # GENERATE CAREER PLAN
# # --------------------------------------------------

# if submitted:

#     if not name.strip():
#         st.warning("Please enter your name.")

#     elif not skills.strip():
#         st.warning("Please enter your current skills.")

#     elif not goal.strip():
#         st.warning("Please describe your career goal.")

#     else:

#         profile = {
#             "name": name.strip(),
#             "education": education,
#             "status": status,
#             "skills": skills.strip(),
#             "interests": interests.strip() or "Not specified",
#             "goal": goal.strip(),
#             "hours": hours
#         }

#         with st.spinner(
#             "Analysing your profile and preparing your career plan..."
#         ):

#             try:

#                 career_plan = generate_career_plan(profile)

#                 st.session_state["career_plan"] = career_plan
#                 st.session_state["profile_name"] = name.strip()

#             except errors.APIError as e:

#                 error_code = getattr(e, "code", "Unknown")
#                 error_message = getattr(e, "message", str(e))

#                 if error_code == 429:

#                     st.error(
#                         "API rate limit or quota exceeded. "
#                         "Check your Gemini API usage and limits, "
#                         "then try again."
#                     )

#                 elif error_code in [500, 503, 504]:

#                     st.error(
#                         "Gemini is temporarily unavailable. "
#                         "Please try again in a few minutes."
#                     )

#                 elif error_code in [401, 403]:

#                     st.error(
#                         "API authentication failed. "
#                         "Check your Gemini API key and permissions."
#                     )

#                 else:

#                     st.error(
#                         f"Gemini API Error ({error_code}): "
#                         f"{error_message}"
#                     )

#             except ValueError as e:

#                 st.error(str(e))

#             except Exception as e:

#                 st.error(
#                     f"Something went wrong: {str(e)}"
#                 )


# # --------------------------------------------------
# # DISPLAY CAREER PLAN
# # --------------------------------------------------

# if "career_plan" in st.session_state:

#     st.markdown("---")

#     st.markdown(
#         f'<div class="section-title">'
#         f'Your Career Plan, {st.session_state["profile_name"]}!'
#         f'</div>',
#         unsafe_allow_html=True
#     )

#     st.markdown(
#         '<div class="result-box">',
#         unsafe_allow_html=True
#     )

#     st.markdown(
#         st.session_state["career_plan"]
#     )

#     st.markdown(
#         '</div>',
#         unsafe_allow_html=True
#     )

#     # Download career plan
#     st.download_button(
#         label="⬇️ Download My Career Plan",
#         data=st.session_state["career_plan"],
#         file_name="my_career_plan.md",
#         mime="text/markdown"
#     )

#     # Generate another plan
#     if st.button("Create a New Career Plan"):
#         del st.session_state["career_plan"]
#         st.rerun()


# # --------------------------------------------------
# # FOOTER
# # --------------------------------------------------

# st.markdown(
#     """
#     <div class="footer">
#         Built at the Techolas AI Wing Weekend<br>
#         AI-generated career suggestions are guidance, not guarantees.
#     </div>
#     """,
#     unsafe_allow_html=True
# )