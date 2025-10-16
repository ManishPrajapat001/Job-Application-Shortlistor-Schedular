from typing import TypedDict, Optional, Literal, Dict, Any

# External logic modules
from profile_filter import filter_profile
from tech_profile_jd_analyser import analyze_profile_against_jd as analyze_tech
from sales_profile_jd_analyser import analyze_profile_against_jd as analyze_sales
from cultural_fit_analyzer import analyze_cultural_fit
from interview_organiser import organize_interview
from emailer import generate_email


from langgraph.graph import StateGraph, END


class AppState(TypedDict, total=False):
    # Inputs
    user_profile: str
    cover_letter: str

    # Filter outcome
    filter_verdict: Optional[Literal["reject", "tech", "sales"]]
    filter_reason: Optional[str]

    # JD analyser outcome
    jd_verdict: Optional[Literal["select", "reject"]]
    jd_reason: Optional[str]

    # Cultural fit outcome
    cultural_verdict: Optional[Literal["select", "reject"]]
    cultural_reason: Optional[str]

    # Scheduling
    interview_type: Optional[Literal["tech", "sales"]]
    interview_details: Optional[str]
    slots_not_found: Optional[str]

    # Email
    final_email: Optional[str]


def _filter_node(state: AppState) -> AppState:
    print("\n🔍 FILTER NODE - Analyzing profile...")
    profile_text = state.get("user_profile", "")
    try:
        res = filter_profile(profile_text)
        state["filter_verdict"] = res.get("verdict")  # reject|tech|sales
        state["filter_reason"] = res.get("rejection_reason", "")
    except Exception as e:
        state["filter_verdict"] = "reject"
        state["filter_reason"] = f"Filter error: {e}"
    
    print(f"✅ FILTER NODE OUTPUT:")
    print(f"   Verdict: {state.get('filter_verdict')}")
    print(f"   Reason: {state.get('filter_reason')}")
    return state


def _tech_jd_node(state: AppState) -> AppState:
    print("\n💻 TECH JD NODE - Analyzing tech profile match...")
    try:
        res = analyze_tech(state.get("user_profile", ""))
        state["jd_verdict"] = res.get("verdict")  # select|reject
        state["jd_reason"] = res.get("rejection_reason", "")
        if state["jd_verdict"] == "select":
            state["interview_type"] = "tech"
    except Exception as e:
        state["jd_verdict"] = "reject"
        state["jd_reason"] = f"Tech JD error: {e}"
    
    print(f"✅ TECH JD NODE OUTPUT:")
    print(f"   Verdict: {state.get('jd_verdict')}")
    print(f"   Reason: {state.get('jd_reason')}")
    print(f"   Interview Type: {state.get('interview_type')}")
    return state


def _sales_jd_node(state: AppState) -> AppState:
    print("\n💼 SALES JD NODE - Analyzing sales profile match...")
    try:
        res = analyze_sales(state.get("user_profile", ""))
        state["jd_verdict"] = res.get("verdict")  # select|reject
        state["jd_reason"] = res.get("rejection_reason", "")
        if state["jd_verdict"] == "select":
            state["interview_type"] = "sales"
    except Exception as e:
        state["jd_verdict"] = "reject"
        state["jd_reason"] = f"Sales JD error: {e}"
    
    print(f"✅ SALES JD NODE OUTPUT:")
    print(f"   Verdict: {state.get('jd_verdict')}")
    print(f"   Reason: {state.get('jd_reason')}")
    print(f"   Interview Type: {state.get('interview_type')}")
    return state


def _cultural_node(state: AppState) -> AppState:
    print("\n🎭 CULTURAL NODE - Analyzing cultural fit...")
    try:
        res = analyze_cultural_fit(state.get("cover_letter", ""))
        state["cultural_verdict"] = res.get("verdict")  # select|reject
        state["cultural_reason"] = res.get("rejection_reason", "")
    except Exception as e:
        state["cultural_verdict"] = "reject"
        state["cultural_reason"] = f"Cultural fit error: {e}"
    
    print(f"✅ CULTURAL NODE OUTPUT:")
    print(f"   Verdict: {state.get('cultural_verdict')}")
    print(f"   Reason: {state.get('cultural_reason')}")
    return state


def _organiser_node(state: AppState) -> AppState:
    print("\n📅 ORGANISER NODE - Scheduling interviews...")
    try:
        itype = state.get("interview_type") or "tech"
        res = organize_interview(itype)
        state["interview_details"] = res.get("interview_details", "")
        state["slots_not_found"] = res.get("slots_not_found", "")
    except Exception as e:
        state["interview_details"] = ""
        state["slots_not_found"] = f"Organizer error: {e}"
    
    print(f"✅ ORGANISER NODE OUTPUT:")
    print(f"   Interview Type: {state.get('interview_type')}")
    print(f"   Interview Details: {state.get('interview_details')[:100]}{'...' if len(state.get('interview_details', '')) > 100 else ''}")
    print(f"   Slots Not Found: {state.get('slots_not_found')}")
    return state


def _emailer_node(state: AppState) -> AppState:
    print("\n📧 EMAILER NODE - Generating final email...")
    
    # Determine verdict + reason to pass
    reason = ""
    verdict: Literal["select", "reject"]

    # Priority: explicit rejections from filter, JD, cultural
    if state.get("filter_verdict") == "reject":
        verdict = "reject"
        reason = state.get("filter_reason", "Application not suitable at this time.")
    elif state.get("jd_verdict") == "reject":
        verdict = "reject"
        reason = state.get("jd_reason", "Profile does not match the job requirements.")
    elif state.get("cultural_verdict") == "reject":
        verdict = "reject"
        reason = state.get("cultural_reason", "We couldn't establish a cultural fit.")
    else:
        # Assume selected; reason is interview details or slots-not-found
        verdict = "select"
        if state.get("interview_details"):
            reason = state["interview_details"]
        else:
            reason = state.get(
                "slots_not_found",
                "Our interviewers are busy right now and they will try to schedule your interview as soon as possible.",
            )

    try:
        email = generate_email(verdict, reason, state.get("user_profile", ""))
        print(f"✅ EMAILER NODE OUTPUT:", email)
        state["final_email"] = email
    except Exception as e:
        state["final_email"] = f"Email generation failed: {e}"
    
    #print(f"✅ EMAILER NODE OUTPUT:")
    #print(f"   Final Verdict: {verdict}")
    #print(f"   Reason: {reason[:100]}{'...' if len(reason) > 100 else ''}")
    #print(f"   Email Generated: {'Yes' if state.get('final_email') else 'No'}")
    return state


def _after_filter_router(state: AppState) -> str:
    v = state.get("filter_verdict")
    if v == "reject":
        return "emailer"
    if v == "tech":
        return "tech_jd"
    if v == "sales":
        return "sales_jd"
    return "emailer"


def _after_tech_jd_router(state: AppState) -> str:
    return "cultural" if state.get("jd_verdict") == "select" else "emailer"


def _after_sales_jd_router(state: AppState) -> str:
    return "cultural" if state.get("jd_verdict") == "select" else "emailer"


def _after_cultural_router(state: AppState) -> str:
    return "organiser" if state.get("cultural_verdict") == "select" else "emailer"


def build_graph():
    graph = StateGraph(AppState)

    # Nodes
    graph.add_node("filter", _filter_node)
    graph.add_node("tech_jd", _tech_jd_node)
    graph.add_node("sales_jd", _sales_jd_node)
    graph.add_node("cultural", _cultural_node)
    graph.add_node("organiser", _organiser_node)
    graph.add_node("emailer", _emailer_node)

    # Entry
    graph.set_entry_point("filter")

    # Conditional edges
    graph.add_conditional_edges("filter", _after_filter_router, {
        "emailer": "emailer",
        "tech_jd": "tech_jd",
        "sales_jd": "sales_jd",
    })

    graph.add_conditional_edges("tech_jd", _after_tech_jd_router, {
        "cultural": "cultural",
        "emailer": "emailer",
    })

    graph.add_conditional_edges("sales_jd", _after_sales_jd_router, {
        "cultural": "cultural",
        "emailer": "emailer",
    })

    graph.add_conditional_edges("cultural", _after_cultural_router, {
        "organiser": "organiser",
        "emailer": "emailer",
    })

    # From organiser we always email
    graph.add_edge("organiser", "emailer")
    graph.add_edge("emailer", END)

    return graph.compile()


def run_once(user_profile: str, cover_letter: str) -> Dict[str, Any]:
    """Run the full flow once and return final state using LangGraph."""
    initial: AppState = {
        "user_profile": user_profile,
        "cover_letter": cover_letter,
    }

    app = build_graph()
    final_state = app.invoke(initial)
    return dict(final_state)


if __name__ == "__main__":
    # Test profiles and cover letters for experimentation
    
    # Profile 1: HR professional
    profile_1 = "Sarah Johnson, Human Resources Manager with 4 years of experience. Graduated in 2020 with a degree in Psychology. Specialized in recruitment, employee relations, and HR policy development. Led hiring processes for 200+ employees across various departments. Experienced in conducting interviews, managing employee onboarding, and handling workplace conflicts."
    cover_letter_1 = "I am passionate about people management and organizational development. I believe in creating inclusive work environments where every employee can thrive. My experience in HR has taught me the importance of understanding both business needs and employee well-being. I am excited about the opportunity to contribute to your team's growth and success."
    
    # Profile 2: B.Tech student (current student)
    profile_2 = "Alex Kumar, currently pursuing B.Tech in Computer Science from IIT Delhi, expected graduation in 2026. Strong foundation in programming languages including Python, Java, and C++. Completed several academic projects including a web application and a machine learning model. Active member of coding clubs and participated in hackathons. Internship experience at a startup working on mobile app development."
    cover_letter_2 = "As a current B.Tech student, I am eager to apply my theoretical knowledge in a real-world setting. I am passionate about technology and constantly learning new skills. I believe in the power of continuous learning and am excited about the opportunity to grow professionally while contributing to innovative projects. I am ready to work hard and learn from experienced professionals."
    
    # Profile 3: Seasoned software engineer (matches TechJD)
    profile_3 = "Michael Chen, Senior Software Engineer with 5 years of experience in backend development. B.Tech in Computer Science from 2019. Expert in Python, FastAPI, Django, PostgreSQL, and AWS. Built scalable microservices handling millions of requests. Experience with Docker, Kubernetes, CI/CD pipelines, and system design. Led a team of 4 developers and mentored junior engineers. Strong background in data structures, algorithms, and distributed systems."
    cover_letter_3 = "I am passionate about building robust, scalable systems that solve real-world problems. Throughout my career, I have always taken ownership of my projects from conception to deployment, learning from both successes and failures. I believe in working backwards from customer needs to deliver simple, delightful experiences. I value transparency and open communication, always assuming positive intent when collaborating with diverse teams. I have a strong growth mindset and continuously experiment with new technologies while maintaining high standards for code quality and maintainability. I am excited about the opportunity to work in an office environment where I can collaborate closely with the team and contribute to building innovative solutions together."
    
    # Profile 4: Seasoned software engineer (prefers work from home)
    profile_4 = "David Rodriguez, Senior Software Engineer with 6 years of experience in full-stack development. B.Tech in Computer Science from 2018. Expert in Python, FastAPI, React, PostgreSQL, and cloud technologies. Built multiple production systems and led technical initiatives. Strong experience with agile methodologies and remote collaboration. Prefers working from home for better work-life balance and productivity."
    cover_letter_4 = "I am passionate about technology and building innovative solutions. My experience in remote work has taught me the importance of clear communication and self-discipline. I believe I can be most productive and contribute effectively while working from home. I am excited about the opportunity to join your team and deliver high-quality work while maintaining the flexibility of remote work."
    
    # Profile 5: B2C sales person (doesn't match SalesJD)
    profile_5 = "Lisa Wang, Sales Representative with 3 years of experience in B2C retail sales. Graduated in 2021 with a degree in Marketing. Specialized in selling consumer electronics and home appliances in retail stores. Experience in customer service, product demonstrations, and closing sales with individual customers. Strong interpersonal skills and ability to build rapport with customers. No experience in B2B sales or enterprise software."
    cover_letter_5 = "I am passionate about sales and helping customers find the right products for their needs. My experience in retail has taught me the importance of understanding customer pain points and providing personalized solutions. I believe in building long-term relationships with customers and providing excellent service. I am excited about the opportunity to apply my sales skills in a new environment."
    
    # Profile 6: B2B sales person (matches SalesJD)
    profile_6 = "James Thompson, Account Executive with 4 years of experience in B2B SaaS sales. Graduated in 2020 with a degree in Business Administration. Specialized in selling enterprise software solutions to mid-market and enterprise clients. Consistently exceeded quota by 120% over the past 2 years. Experience with Salesforce CRM, MEDDICC methodology, and complex sales cycles. Led deals worth $500K+ ARR and managed a pipeline of 50+ opportunities. Strong experience in discovery, objection handling, and closing enterprise deals."
    cover_letter_6 = "I am passionate about B2B sales and helping businesses solve their challenges through technology. Throughout my career, I have taken complete ownership of my sales pipeline and outcomes, learning from both successful deals and rejections. I work backwards from customer pain points to deliver solutions that truly add value. I believe in transparent communication with both customers and internal teams, always focusing on the problem rather than personal dynamics. I have a growth mindset and continuously learn about new technologies and sales methodologies. I thrive in collaborative environments where diverse perspectives lead to better solutions, and I am committed to maintaining high standards while being pragmatic about what works. I am excited about the opportunity to work in an office environment where I can collaborate closely with the team and build strong relationships with both customers and colleagues."
    
    # Test with profile 1 (HR professional)
    print("=" * 80)
    print("TESTING PROFILE 1: HR Professional")
    print("=" * 80)
    out = run_once(profile_1, cover_letter_1)
    #print("Final Email:\n", out.get("final_email", "<no email>"))
    
    print("\n" + "=" * 80)
    print("TESTING PROFILE 2: B.Tech Student")
    print("=" * 80)
    out = run_once(profile_2, cover_letter_2)
    #print("Final Email:\n", out.get("final_email", "<no email>"))
    
    print("\n" + "=" * 80)
    print("TESTING PROFILE 3: Seasoned Software Engineer")
    print("=" * 80)
    out = run_once(profile_3, cover_letter_3)
    #print("Final Email:\n", out.get("final_email", "<no email>"))
    
    print("\n" + "=" * 80)
    print("TESTING PROFILE 4: Software Engineer (WFH preference)")
    print("=" * 80)
    out = run_once(profile_4, cover_letter_4)
    #print("Final Email:\n", out.get("final_email", "<no email>"))
    
    print("\n" + "=" * 80)
    print("TESTING PROFILE 5: B2C Sales (doesn't match)")
    print("=" * 80)
    out = run_once(profile_5, cover_letter_5)
    #print("Final Email:\n", out.get("final_email", "<no email>"))
    
    print("\n" + "=" * 80)
    print("TESTING PROFILE 6: B2B Sales (matches)")
    print("=" * 80)
    out = run_once(profile_6, cover_letter_6)
    #print("Final Email:\n", out.get("final_email", "<no email>"))


