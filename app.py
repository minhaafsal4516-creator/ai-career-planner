import json

import streamlit as st
from google import genai
from google.genai import errors, types

SYSTEM_PROMPT = """
You are a practical Architecture career counsellor for students and job seekers in India.
Keep the user's real profile in mind and give realistic, personalised advice.
Rules:
- Never promise a job or a salary.
- Personalise recommendations to the user's actual profile.
- Do not assume skills the user did not mention.
- If essential information is missing, ask for it instead of making assumptions.
- Use simple, encouraging and professional language.
- Salary ranges are indicative estimates for India and vary by location, company and experience.
- Suggest only free and real learning resources that are practical.
- Do not invent qualifications, job openings or course availability.
- Prioritize practical career development over generic motivation.
- Return exactly the requested JSON structure.
"""

st.set_page_config(page_title="AI Career Planner", page_icon="🎯", layout="centered")

# Page styling
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
    .today-box { background: #DCFCE7; border: 1px solid #86EFAC; border-radius: 12px;
                 padding: 1rem 1.2rem; margin: 0.5rem 0 1.2rem; color: #166534; }
    .project-box { background: #EFF6FF; border: 1px solid #93C5FD; border-radius: 10px;
                   padding: 0.8rem 1rem; margin-top: 0.8rem; }
    .footer { text-align: center; color: #64748B; font-size: 0.85rem; padding: 0.5rem 0 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="hero">
      <h1>🎯 AI Career Planner</h1>
      <p>My first AI product, built by Minha.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Resume upload
st.markdown('<div class="step">Step 1 · Resume (optional)</div>', unsafe_allow_html=True)
resume_pdf = st.file_uploader("Upload your resume PDF", type=["pdf"])
st.caption(
    "Your resume is sent to Google Gemini to make your plan and is not stored by "
    "this app. On Gemini's free tier Google may use it to improve its products."
)

with st.form("about_you"):
    st.subheader("Step 2 · About you")

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
        skills_label = "Skills you already have (optional with resume)" if resume_pdf else "Skills you already have"
        skills = st.text_area(skills_label)
    with interests_col:
        interests = st.text_area("What do you enjoy?")

    goal = st.text_input("Your goal")
    hours = st.slider("Hours per week you can study", 2, 40, 10)

    submitted = st.form_submit_button(
        "🚀 Build my career dashboard",
        type="primary",
        use_container_width=True,
    )


def career_response_schema():
    text_schema = lambda description: types.Schema(type=types.Type.STRING, description=description)

    role_schema = types.Schema(
        type=types.Type.OBJECT,
        required=["title", "why_it_fits", "match_score", "salary_range_lpa"],
        properties={
            "title": text_schema("Career role title"),
            "why_it_fits": text_schema("Why this role fits the user's profile"),
            "match_score": types.Schema(
                type=types.Type.INTEGER,
                minimum=0,
                maximum=100,
            ),
            "salary_range_lpa": text_schema("Indicative salary range in lakh rupees per year"),
        },
    )

    skill_schema = types.Schema(
        type=types.Type.OBJECT,
        required=["skill", "current_level", "needed_level", "free_resource"],
        properties={
            "skill": text_schema("Skill name"),
            "current_level": types.Schema(
                type=types.Type.INTEGER,
                minimum=0,
                maximum=10,
            ),
            "needed_level": types.Schema(
                type=types.Type.INTEGER,
                minimum=0,
                maximum=10,
            ),
            "free_resource": text_schema("A free learning resource"),
        },
    )

    phase_schema = types.Schema(
        type=types.Type.OBJECT,
        required=["tasks", "mini_project"],
        properties={
            "tasks": types.Schema(
                type=types.Type.ARRAY,
                min_items=3,
                max_items=3,
                items=text_schema("One practical roadmap task"),
            ),
            "mini_project": text_schema("A small practical project"),
        },
    )

    return types.Schema(
        type=types.Type.OBJECT,
        required=["roles", "skill_gaps", "roadmap", "todays_action"],
        properties={
            "roles": types.Schema(
                type=types.Type.ARRAY,
                min_items=3,
                max_items=3,
                items=role_schema,
            ),
            "skill_gaps": types.Schema(
                type=types.Type.ARRAY,
                min_items=4,
                max_items=6,
                items=skill_schema,
            ),
            "roadmap": types.Schema(
                type=types.Type.OBJECT,
                required=["days_1_30", "days_31_60", "days_61_90"],
                properties={
                    "days_1_30": phase_schema,
                    "days_31_60": phase_schema,
                    "days_61_90": phase_schema,
                },
            ),
            "todays_action": text_schema("One achievable action for today"),
        },
    )


# This schema keeps the role comparisons and location suggestions consistent.
def opportunity_response_schema():
    text_schema = lambda description: types.Schema(type=types.Type.STRING, description=description)

    comparison_schema = types.Schema(
        type=types.Type.OBJECT,
        required=[
            "title",
            "match_score",
            "why_it_fits",
            "strong_matches",
            "missing_skills",
            "requirements",
            "salary_range_lpa",
            "next_step",
        ],
        properties={
            "title": text_schema("Career role title"),
            "match_score": types.Schema(
                type=types.Type.INTEGER,
                minimum=0,
                maximum=100,
            ),
            "why_it_fits": text_schema("How this role fits the user's existing profile"),
            "strong_matches": types.Schema(
                type=types.Type.ARRAY,
                min_items=1,
                max_items=4,
                items=text_schema("An existing strength relevant to the role"),
            ),
            "missing_skills": types.Schema(
                type=types.Type.ARRAY,
                min_items=1,
                max_items=4,
                items=text_schema("A skill to build for this role"),
            ),
            "requirements": text_schema("Typical skills or qualifications employers may expect"),
            "salary_range_lpa": text_schema("Indicative annual salary range in lakh rupees"),
            "next_step": text_schema("One practical action to improve prospects for this role"),
        },
    )

    recommendation_schema = types.Schema(
        type=types.Type.OBJECT,
        required=["category", "title", "details", "search_query"],
        properties={
            "category": text_schema(
                "One of: Nearby roles, Companies to explore, Internships, Remote work, Career paths"
            ),
            "title": text_schema("A type of opportunity or organization to explore"),
            "details": text_schema("A location-aware suggestion; do not claim an opening is confirmed"),
            "search_query": text_schema("A practical search phrase the user can try"),
        },
    )

    return types.Schema(
        type=types.Type.OBJECT,
        required=["comparisons", "recommendations", "action_plan"],
        properties={
            "comparisons": types.Schema(
                type=types.Type.ARRAY,
                min_items=2,
                max_items=3,
                items=comparison_schema,
            ),
            "recommendations": types.Schema(
                type=types.Type.ARRAY,
                min_items=5,
                max_items=7,
                items=recommendation_schema,
            ),
            "action_plan": types.Schema(
                type=types.Type.ARRAY,
                min_items=3,
                max_items=3,
                items=text_schema("An actionable next step for the user's career"),
            ),
        },
    )


def call_opportunity_gemini(client, model, contents):
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a practical career adviser for students and job seekers in India. "
                "Compare only the selected roles using the user's actual profile and existing career plan. "
                "Do not assume skills the user did not mention, promise a job or salary, or invent current "
                "vacancies, hiring activity, internships, or company presence. Give indicative salary ranges "
                "in lakh rupees per year. Location-based recommendations are research leads and search ideas "
                "that the user must verify, not confirmed openings. Suggest realistic requirements and "
                "personalized next steps. Return exactly the requested JSON structure."
            ),
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=opportunity_response_schema(),
        ),
    )


def call_gemini(client, model, contents):
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=career_response_schema(),
        ),
    )


if submitted:
    missing = []
    if not name.strip():
        missing.append("Your name")
    if not resume_pdf and not skills.strip():
        missing.append("Skills you already have")
    if not goal.strip():
        missing.append("Your goal")

    if missing:
        st.session_state.profile_answers = None
        st.session_state.career_plan = None
        st.warning("Please fill: " + ", ".join(missing))
    else:
        st.session_state.profile_answers = {
            "name": name.strip(),
            "education": education,
            "status": status,
            "skills": skills.strip() or "Not provided; use the uploaded resume",
            "interests": interests.strip(),
            "goal": goal.strip(),
            "hours_per_week": hours,
        }
        st.session_state.career_plan = None
        st.session_state.chat_history = []
        st.session_state.opportunity_result = None

        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"],
                http_options=types.HttpOptions(api_version="v1beta"),
            )

            profile = "\n".join([
                f"Name: {name.strip()}",
                f"Highest education: {education}",
                f"Where are you right now: {status}",
                f"Skills: {skills.strip() or 'Not provided; use the uploaded resume'}",
                f"What you enjoy: {interests.strip()}",
                f"Goal: {goal.strip()}",
                f"Hours per week available to study: {hours}",
            ])
            contents = [f"Person's profile:\n{profile}"]
            if resume_pdf:
                contents.append(
                    types.Part.from_bytes(
                        data=resume_pdf.getvalue(),
                        mime_type="application/pdf",
                    )
                )

            with st.spinner("Building your career dashboard..."):
                try:
                    response = call_gemini(client, "gemini-3.5-flash-lite", contents)
                except errors.APIError as first_error:
                    if first_error.code not in (429, 500, 503, 504):
                        raise
                    try:
                        response = call_gemini(client, "gemini-3.5-flash-lite", contents)
                    except errors.APIError as retry_error:
                        if retry_error.code not in (429, 500, 503, 504):
                            raise
                        response = call_gemini(client, "gemini-3.5-flash-lite-lite", contents)

            plan = json.loads(response.text)
            st.session_state.career_plan = plan
        except KeyError:
            st.error("Gemini API key is missing. Add GEMINI_API_KEY to your Streamlit secrets, then try again.")
        except errors.APIError as error:
            if error.code == 429:
                st.error("Gemini's usage limit was reached. Check your API quota, then try again.")
            elif error.code in (500, 503, 504):
                st.error("Gemini is temporarily unavailable. Please wait a moment and try again.")
            elif error.code in (401, 403):
                st.error("Gemini rejected the API key. Check that it is correct and has API access.")
            else:
                st.error(f"Gemini could not complete the request (error {error.code}). Please try again.")
        except json.JSONDecodeError:
            st.error("Gemini returned an incomplete plan. Please try again.")
        except Exception as error:
            st.error(f"Something unexpected happened ({type(error).__name__}). Please try again.")


def plan_to_markdown(plan):
    lines = ["# My Career Plan", "", "## Do this today", plan["todays_action"], "", "## Matching roles"]
    for role in plan["roles"]:
        lines.extend([
            f"### {role['title']} - {role['match_score']}%",
            f"**Why it fits:** {role['why_it_fits']}",
            f"**Salary (indicative):** {role['salary_range_lpa']}",
            "",
        ])
    lines.extend(["## Skill gaps"])
    for gap in plan["skill_gaps"]:
        lines.append(
            f"- **{gap['skill']}:** {gap['current_level']}/10 now, "
            f"{gap['needed_level']}/10 needed. Free resource: {gap['free_resource']}"
        )
    lines.extend(["", "## 90-day roadmap"])
    for key, label in [
        ("days_1_30", "Days 1-30"),
        ("days_31_60", "Days 31-60"),
        ("days_61_90", "Days 61-90"),
    ]:
        phase = plan["roadmap"][key]
        lines.extend([f"### {label}"])
        lines.extend([f"- [ ] {task}" for task in phase["tasks"]])
        lines.extend([f"**Mini project:** {phase['mini_project']}", ""])
    return "\n".join(lines)


plan = st.session_state.get("career_plan")
if plan:
    st.markdown(
        f'<div class="today-box"><strong>Do this today</strong><br>{plan["todays_action"]}</div>',
        unsafe_allow_html=True,
    )

    st.subheader("3 roles that fit you")
    role_cols = st.columns(3)
    for column, role in zip(role_cols, plan["roles"]):
        with column:
            with st.container(border=True):
                st.markdown(f"### {role['title']}")
                st.markdown(
                    f'<div class="score">{role["match_score"]}<span>/100 match</span></div>',
                    unsafe_allow_html=True,
                )
                st.progress(max(0, min(100, role["match_score"])) / 100)
                st.write(role["why_it_fits"])
                st.write(f"**Salary:** {role['salary_range_lpa']} **(indicative)**")

    st.subheader("Skill gaps")
    chart_data = [
        {
            "Skill": gap["skill"],
            "Current": gap["current_level"],
            "Needed": gap["needed_level"],
        }
        for gap in plan["skill_gaps"]
    ]
    st.bar_chart(chart_data, x="Skill", y=["Current", "Needed"], horizontal=True)

    for gap in plan["skill_gaps"]:
        st.write(f"**{gap['skill']}:** {gap['free_resource']}")

    roadmap_tab, opportunities_tab = st.tabs(["Your 90-day roadmap", "Career Opportunities"])
    with roadmap_tab:
        st.subheader("Your 90-day roadmap")
        tab_1, tab_2, tab_3 = st.tabs(["Days 1-30", "Days 31-60", "Days 61-90"])
        phases = [
            (tab_1, "days_1_30"),
            (tab_2, "days_31_60"),
            (tab_3, "days_61_90"),
        ]
        for tab, phase_key in phases:
            with tab:
                phase = plan["roadmap"][phase_key]
                for task_index, task in enumerate(phase["tasks"]):
                    st.checkbox(task, key=f"{phase_key}_task_{task_index}")
                st.markdown(
                    f'<div class="project-box"><strong>Mini project</strong><br>{phase["mini_project"]}</div>',
                    unsafe_allow_html=True,
                )

    # This tab compares selected roles and suggests local job-search leads.
    with opportunities_tab:
        st.subheader("Compare roles and explore opportunities")
        st.caption(
            "Compare roles using your saved career plan, then explore location-based leads. "
            "Suggestions are not confirmed vacancies; check current details with employers."
        )
        with st.form("career_opportunities"):
            preferred_location = st.text_input(
                "Preferred city or region",
                value=st.session_state.get("opportunity_location", ""),
                placeholder="For example, Kochi or Bengaluru",
            )
            selected_roles = st.multiselect(
                "Choose roles to compare",
                options=[role["title"] for role in plan["roles"]],
                default=[role["title"] for role in plan["roles"]],
                max_selections=3,
            )
            work_preference = st.selectbox(
                "Work preference",
                ["Any", "On-site or nearby", "Remote", "Internship"],
            )
            find_opportunities = st.form_submit_button(
                "🔎 Compare roles and find opportunities",
                type="primary",
                use_container_width=True,
            )

        if find_opportunities:
            missing = []
            if not preferred_location.strip():
                missing.append("your preferred city or region")
            if len(selected_roles) < 2:
                missing.append("at least two roles to compare")

            if missing:
                st.warning("Please add " + " and ".join(missing) + ".")
            else:
                st.session_state.opportunity_location = preferred_location.strip()
                st.session_state.opportunity_result = None
                profile = st.session_state.profile_answers
                opportunity_prompt = (
                    "Compare the selected career roles and suggest location-aware opportunities. "
                    "Use the user's answers and existing plan as the only evidence about their skills. "
                    "Include nearby role search ideas, companies to research, internship search ideas, "
                    "remote work search ideas, and realistic related career paths where relevant. "
                    "Do not claim that an opening, company office, or internship is currently available.\n\n"
                    f"USER PROFILE:\n{json.dumps(profile, ensure_ascii=False)}\n\n"
                    f"EXISTING CAREER PLAN:\n{json.dumps(plan, ensure_ascii=False)}\n\n"
                    f"SELECTED ROLES:\n{json.dumps(selected_roles, ensure_ascii=False)}\n\n"
                    f"PREFERRED LOCATION: {preferred_location.strip()}\n"
                    f"WORK PREFERENCE: {work_preference}"
                )

                try:
                    client = genai.Client(
                        api_key=st.secrets["GEMINI_API_KEY"],
                        http_options=types.HttpOptions(api_version="v1beta"),
                    )
                    with st.spinner("Comparing roles and finding relevant search leads..."):
                        try:
                            response = call_opportunity_gemini(
                                client,
                                "gemini-3.5-flash-lite",
                                opportunity_prompt,
                            )
                        except errors.APIError as first_error:
                            if first_error.code not in (429, 500, 503, 504):
                                raise
                            try:
                                response = call_opportunity_gemini(
                                    client,
                                    "gemini-3.5-flash-lite",
                                    opportunity_prompt,
                                )
                            except errors.APIError as retry_error:
                                if retry_error.code not in (429, 500, 503, 504):
                                    raise
                                response = call_opportunity_gemini(
                                    client,
                                    "gemini-3.5-flash-lite-lite",
                                    opportunity_prompt,
                                )

                    st.session_state.opportunity_result = json.loads(response.text)
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
                except json.JSONDecodeError:
                    st.error("Gemini returned an incomplete comparison. Please try again.")
                except Exception as error:
                    st.error(f"Something unexpected happened ({type(error).__name__}). Please try again.")

        opportunity_result = st.session_state.get("opportunity_result")
        if opportunity_result:
            st.markdown("#### Role comparison")
            st.bar_chart(
                {
                    "Role": [comparison["title"] for comparison in opportunity_result["comparisons"]],
                    "Match score": [
                        comparison["match_score"] for comparison in opportunity_result["comparisons"]
                    ],
                },
                x="Role",
                y="Match score",
            )
            comparison_rows = [
                {
                    "Role": comparison["title"],
                    "Skill match": f'{comparison["match_score"]}%',
                    "Indicative salary (LPA)": comparison["salary_range_lpa"],
                    "Key requirements": comparison["requirements"],
                }
                for comparison in opportunity_result["comparisons"]
            ]
            st.dataframe(comparison_rows, use_container_width=True, hide_index=True)

            for comparison in opportunity_result["comparisons"]:
                with st.expander(f'{comparison["title"]} · {comparison["match_score"]}% match'):
                    st.progress(max(0, min(100, comparison["match_score"])) / 100)
                    st.write(comparison["why_it_fits"])
                    st.write(f'**Strong matches:** {", ".join(comparison["strong_matches"])}')
                    st.write(f'**Skills to build:** {", ".join(comparison["missing_skills"])}')
                    st.write(f'**Typical requirements:** {comparison["requirements"]}')
                    st.write(f'**Salary potential:** {comparison["salary_range_lpa"]} (indicative)')
                    st.write(f'**Next step:** {comparison["next_step"]}')

            st.markdown("#### Location-based recommendations")
            st.caption(
                f"Search leads for {st.session_state.get('opportunity_location', 'your area')}; "
                "verify current openings, locations, and eligibility before applying."
            )
            for recommendation in opportunity_result["recommendations"]:
                with st.container(border=True):
                    st.markdown(f'**{recommendation["category"]}: {recommendation["title"]}**')
                    st.write(recommendation["details"])
                    st.caption(f'Try searching: {recommendation["search_query"]}')

            st.markdown("#### Your next steps")
            for action in opportunity_result["action_plan"]:
                st.markdown(f"- {action}")

    st.download_button(
        "⬇️ Download my plan",
        data=plan_to_markdown(plan),
        file_name="my_career_plan.md",
        mime="text/markdown",
        use_container_width=True,
    )

    st.subheader("Ask about your plan")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    chat_question = st.chat_input("Ask about your plan")
    if chat_question:
        st.session_state.chat_history.append({"role": "user", "content": chat_question})
        with st.chat_message("user"):
            st.write(chat_question)

        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"],
                http_options=types.HttpOptions(api_version="v1beta"),
            )
            chat_prompt = (
                "Use this career plan as context. Answer the question in under 150 words.\n\n"
                f"PLAN:\n{json.dumps(plan, ensure_ascii=False)}\n\n"
                f"QUESTION:\n{chat_question}"
            )
            with st.spinner("Thinking..."):
                try:
                    chat_response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=chat_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=(
                                "Answer follow-up career questions clearly and in under 150 words. "
                                "Do not promise jobs or salaries. Label salary estimates as indicative."
                            ),
                            temperature=0.7,
                        ),
                    )
                except errors.APIError as chat_error:
                    if chat_error.code not in (429, 500, 503, 504):
                        raise
                    chat_response = client.models.generate_content(
                        model="gemini-3.5-flash-lite-lite",
                        contents=chat_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=(
                                "Answer follow-up career questions clearly and in under 150 words. "
                                "Do not promise jobs or salaries. Label salary estimates as indicative."
                            ),
                            temperature=0.7,
                        ),
                    )
            answer = chat_response.text
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)
        except KeyError:
            st.error("Gemini API key is missing. Add GEMINI_API_KEY to your Streamlit secrets.")
        except Exception as chat_error:
            st.error(f"Could not answer that question ({type(chat_error).__name__}). Please try again.")

# Footer
st.divider()
st.markdown(
    '<div class="footer">Built at the Techolas AI Wing weekend · AI suggestions, not guarantees.</div>',
    unsafe_allow_html=True,
)
