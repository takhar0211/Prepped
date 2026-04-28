import os
import re
from pathlib import Path
import streamlit as st
import requests
from difflib import SequenceMatcher
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Missing OPENAI_API_KEY in .env")
    st.stop()

# ── Supabase Setup ───────────────────────────────────────────
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_API_KEY")
supabase = None

if supabase_url and supabase_key:
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {e}")

# ── Auth Helpers ─────────────────────────────────────────────
def signup_user(email, password, leetcode_username=""):
    if not supabase:
        return None, "Supabase not configured"
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            # Create profile
            supabase.table("user_profiles").insert({
                "user_id": res.user.id,
                "email": email,
                "leetcode_username": leetcode_username
            }).execute()
            return res.user, None
        return None, "Signup failed. Please try again."
    except Exception as e:
        return None, str(e)

def login_user(email, password):
    if not supabase:
        return None, "Supabase not configured"
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            return res.user, None
        return None, "Invalid credentials."
    except Exception as e:
        return None, str(e)

def logout_user():
    if supabase:
        try:
            supabase.auth.sign_out()
        except:
            pass
    for key in ["user_id", "user_email", "leetcode_username", "recommendations", "sidebar_load_count"]:
        if key in st.session_state:
            del st.session_state[key]

def get_user_profile(user_id):
    if not supabase:
        return None
    try:
        res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None

def update_leetcode_username(user_id, new_username):
    if not supabase:
        return
    try:
        supabase.table("user_profiles").update({"leetcode_username": new_username}).eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Update Error: {e}")

def send_password_reset(email):
    """Send a password reset OTP to the user's email via Supabase."""
    if not supabase:
        return False, "Supabase not configured"
    try:
        supabase.auth.reset_password_email(email)
        return True, None
    except Exception as e:
        return False, str(e)

def verify_otp_and_reset(email, token, new_password):
    """Verify the OTP from email and set the new password."""
    if not supabase:
        return False, "Supabase not configured"
    try:
        res = supabase.auth.verify_otp({"email": email, "token": token, "type": "recovery"})
        if res and res.user:
            # OTP verified — session is active, now update password
            supabase.auth.update_user({"password": new_password})
            # Sign out so the user logs in fresh with new password
            supabase.auth.sign_out()
            return True, None
        return False, "Invalid or expired OTP. Please try again."
    except Exception as e:
        return False, str(e)


# ── LLM Setup ─────────────────────────────────────────────
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.3,
)

# ── Constants & Mappings ─────────────────────────────────────
CATEGORY_SEQUENCE = [
    "Arrays",
    "Strings",
    "Recursion & Backtracking",
    "Linked List",
    "Stack & Queue",
    "Trees",
    "Graphs",
    "Heap (Priority Queue)",
    "Greedy Algorithms",
    "Dynamic Programming (DP)",
    "Bit Manipulation",
    "Math & Number Theory",
    "Others"
]

# Maps LeetCode tags → our category + a priority (lower number = MORE specific = wins)
# Generic tags like Array/Hash Table get high priority numbers so they lose to specific ones
CATEGORY_MAPPING = {
    # DP (priority 1 — most specific, should always win)
    "Dynamic Programming": ("Dynamic Programming (DP)", 1),
    "Memoization": ("Dynamic Programming (DP)", 1),
    # Graphs (priority 2)
    "Graph": ("Graphs", 2),
    "Breadth-First Search": ("Graphs", 2),
    "Depth-First Search": ("Graphs", 2),
    "Union Find": ("Graphs", 2),
    "Topological Sort": ("Graphs", 2),
    "Shortest Path": ("Graphs", 2),
    # Trees (priority 3)
    "Tree": ("Trees", 3),
    "Binary Tree": ("Trees", 3),
    "Binary Search Tree": ("Trees", 3),
    "Segment Tree": ("Trees", 3),
    "Binary Indexed Tree": ("Trees", 3),
    # Recursion & Backtracking (priority 4)
    "Recursion": ("Recursion & Backtracking", 4),
    "Backtracking": ("Recursion & Backtracking", 4),
    # Linked List (priority 5)
    "Linked List": ("Linked List", 5),
    "Doubly-Linked List": ("Linked List", 5),
    # Stack & Queue (priority 6)
    "Stack": ("Stack & Queue", 6),
    "Monotonic Stack": ("Stack & Queue", 6),
    "Queue": ("Stack & Queue", 6),
    "Monotonic Queue": ("Stack & Queue", 6),
    # Heap (priority 7)
    "Heap (Priority Queue)": ("Heap (Priority Queue)", 7),
    # Greedy (priority 8)
    "Greedy": ("Greedy Algorithms", 8),
    # Bit Manipulation (priority 9)
    "Bit Manipulation": ("Bit Manipulation", 9),
    # Math (priority 10)
    "Math": ("Math & Number Theory", 10),
    "Number Theory": ("Math & Number Theory", 10),
    "Geometry": ("Math & Number Theory", 10),
    "Combinatorics": ("Math & Number Theory", 10),
    # Strings (priority 11)
    "String": ("Strings", 11),
    "Trie": ("Strings", 11),
    "String Matching": ("Strings", 11),
    # Arrays (priority 12 — most generic, loses to everything)
    "Array": ("Arrays", 12),
    "Hash Table": ("Arrays", 12),
    "Sliding Window": ("Arrays", 12),
    "Prefix Sum": ("Arrays", 12),
    "Two Pointers": ("Arrays", 12),
    "Matrix": ("Arrays", 12),
}

# ── Pattern Mappings ─────────────────────────────────────────
PATTERN_SEQUENCE = [
    "Two Pointers",
    "Sliding Window",
    "Binary Search",
    "Prefix Sum / Difference Array",
    "Hashing (Map/Set)",
    "Recursion",
    "Backtracking",
    "Fast & Slow Pointer",
    "Merge Intervals",
    "Monotonic Stack",
    "Heap / Top-K",
    "Greedy",
    "Tree DFS",
    "Tree BFS (Level Order)",
    "Graph BFS / DFS",
    "Topological Sort",
    "Union Find",
    "Shortest Path",
    "Dynamic Programming",
    "Bit Manipulation",
    "Others"
]

# Maps LeetCode tags → DSA pattern + priority (lower = more specific = wins)
PATTERN_MAPPING = {
    # DP (priority 1 — most specific, always wins)
    "Dynamic Programming": ("Dynamic Programming", 1),
    "Memoization": ("Dynamic Programming", 1),
    # Topological Sort (priority 2)
    "Topological Sort": ("Topological Sort", 2),
    # Shortest Path (priority 3)
    "Shortest Path": ("Shortest Path", 3),
    # Union Find (priority 4)
    "Union Find": ("Union Find", 4),
    # Backtracking (priority 5)
    "Backtracking": ("Backtracking", 5),
    # Monotonic Stack (priority 6)
    "Monotonic Stack": ("Monotonic Stack", 6),
    "Monotonic Queue": ("Monotonic Stack", 6),
    # Sliding Window (priority 7)
    "Sliding Window": ("Sliding Window", 7),
    # Binary Search (priority 8)
    "Binary Search": ("Binary Search", 8),
    # Prefix Sum (priority 9)
    "Prefix Sum": ("Prefix Sum / Difference Array", 9),
    # Bit Manipulation (priority 10)
    "Bit Manipulation": ("Bit Manipulation", 10),
    # Two Pointers (priority 11)
    "Two Pointers": ("Two Pointers", 11),
    # Greedy (priority 12)
    "Greedy": ("Greedy", 12),
    # Heap (priority 13)
    "Heap (Priority Queue)": ("Heap / Top-K", 13),
    # Recursion (priority 14)
    "Recursion": ("Recursion", 14),
    # Graph (priority 15 — wins over generic DFS/BFS)
    "Graph": ("Graph BFS / DFS", 15),
    # Tree DFS / BFS (priority 16-17)
    "Depth-First Search": ("Tree DFS", 16),
    "Breadth-First Search": ("Tree BFS (Level Order)", 17),
    "Tree": ("Tree DFS", 18),
    "Binary Tree": ("Tree DFS", 18),
    "Binary Search Tree": ("Tree DFS", 18),
    # Linked List → Fast & Slow Pointer (priority 19)
    "Linked List": ("Fast & Slow Pointer", 19),
    "Doubly-Linked List": ("Fast & Slow Pointer", 19),
    # Sorting → Merge Intervals (priority 20)
    "Merge Sort": ("Merge Intervals", 20),
    # Hashing (priority 25 — generic, loses to everything)
    "Hash Table": ("Hashing (Map/Set)", 25),
}

# ── Structured Output Models ───────────────────────────────────
class DSAQuestion(BaseModel):
    title: str = Field(description="The title of the LeetCode question")
    leetcode_link: str = Field(description="A valid URL to the question on LeetCode")
    why_it_matters: str = Field(description="One line on why this question is important or frequently asked")
    description: str = Field(description="Clear and concise problem description in exactly 3 lines")
    companies: List[str] = Field(description="A list of 3-5 top tech companies that frequently ask this question (e.g. ['Google', 'Amazon', 'Meta'])")

class DSAQuestionList(BaseModel):
    questions: List[DSAQuestion]

# Bind the model
structured_llm = llm.with_structured_output(DSAQuestionList)

# ── Helper Functions ─────────────────────────────────────────
def normalize_title(title: str) -> str:
    return re.sub(r'[^a-z0-9]', '', title.lower())

def is_fuzzy_match(title1: str, title2: str, threshold: float = 0.85) -> bool:
    return SequenceMatcher(None, title1, title2).ratio() > threshold

def extract_slug_from_url(url: str) -> str:
    match = re.search(r'leetcode\.com/problems/([^/]+)', url)
    return match.group(1).lower() if match else ""

@st.cache_data(ttl=600, show_spinner=False)
def get_recent_solved_questions(username, limit=50):
    url = "https://leetcode.com/graphql"
    query = '''
    query recentAcSubmissions($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        title
        titleSlug
        timestamp
      }
    }
    '''
    variables = {
        "username": username,
        "limit": limit
    }
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            return [], f"GraphQL Error: {data['errors'][0]['message']}"
            
        if "data" in data and data["data"].get("recentAcSubmissionList") is not None:
            submissions = data["data"]["recentAcSubmissionList"]
            solved = []
            seen = set()
            for sub in submissions:
                title = sub.get("title")
                slug = sub.get("titleSlug")
                timestamp_str = sub.get("timestamp")
                date_str = ""
                if timestamp_str:
                    try:
                        from datetime import datetime
                        date_str = datetime.fromtimestamp(int(timestamp_str)).strftime('%Y-%m-%d')
                    except:
                        pass
                if title and slug and slug not in seen:
                    seen.add(slug)
                    solved.append({"title": title, "slug": slug, "date": date_str})
            return solved, None
        else:
            return [], "Invalid username or no public recent submissions found."
    except requests.exceptions.RequestException as e:
        return [], f"Network Error: {str(e)}"
    except Exception as e:
        return [], f"Unexpected Error: {str(e)}"

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_raw_tags(slugs_key: str) -> dict:
    """Fetch raw topic tags for multiple slugs. Returns dict of slug -> list of tag names.
    slugs_key is a comma-joined string of slugs (for cache hashing)."""
    slugs = slugs_key.split(",") if slugs_key else []
    if not slugs:
        return {}
    
    url = "https://leetcode.com/graphql"
    result_map = {}
    
    batch_size = 50
    for i in range(0, len(slugs), batch_size):
        batch_slugs = slugs[i:i+batch_size]
        query_parts = []
        for j, slug in enumerate(batch_slugs):
            alias = f"q_{j}"
            query_parts.append(f'{alias}: question(titleSlug: "{slug}") {{ topicTags {{ name }} }}')
        
        query = "query { " + " ".join(query_parts) + " }"
        try:
            response = requests.post(url, json={"query": query}, timeout=10)
            if response.status_code == 200:
                data = response.json().get("data", {})
                for j, slug in enumerate(batch_slugs):
                    alias = f"q_{j}"
                    question_data = data.get(alias)
                    tags = []
                    if question_data and question_data.get("topicTags"):
                        tags = [t["name"] for t in question_data["topicTags"]]
                    result_map[slug] = tags
        except Exception:
            for slug in batch_slugs:
                if slug not in result_map:
                    result_map[slug] = []
    
    return result_map

def _map_tags(slugs: List[str], mapping: dict, default: str = "Others") -> dict:
    """Map raw tags to a category/pattern using a priority-based mapping dict."""
    slugs_key = ",".join(slugs)
    raw_tags = _fetch_raw_tags(slugs_key)
    result = {}
    for slug in slugs:
        tags = raw_tags.get(slug, [])
        best_priority = 999
        assigned = default
        for tag in tags:
            if tag in mapping:
                name, priority = mapping[tag]
                if priority < best_priority:
                    best_priority = priority
                    assigned = name
        result[slug] = assigned
    return result

def get_batched_question_categories(slugs: List[str]) -> dict:
    """Map slugs to our major DSA categories."""
    return _map_tags(slugs, CATEGORY_MAPPING)

def get_batched_question_patterns(slugs: List[str]) -> dict:
    """Map slugs to DSA technique patterns."""
    return _map_tags(slugs, PATTERN_MAPPING)

# ── Supabase Helpers ───────────────────────────────────────
def get_user_solved_supabase(username):
    if not supabase: return []
    try:
        response = supabase.table("user_solved_questions").select("title_slug, title, topic, created_at").eq("username", username).execute()
        
        result = []
        for row in response.data:
            date_str = ""
            created_at = row.get("created_at")
            if created_at:
                date_str = created_at.split("T")[0]
            result.append({"slug": row["title_slug"], "title": row["title"], "topic": row.get("topic", "General"), "date": date_str})
        return result
    except Exception as e:
        st.error(f"Supabase Fetch Error: {e}")
        return []

def mark_question_solved_supabase(username, slug, title, topic="General"):
    if not supabase: return
    try:
        supabase.table("user_solved_questions").insert({
            "username": username,
            "title_slug": slug,
            "title": title,
            "topic": topic
        }).execute()
    except Exception as e:
        st.error(f"Supabase Insert Error: {e}")

# ── Session State Initialization ─────────────────────────────
for key, default in [("recommendations", []), ("sidebar_load_count", 10), ("user_id", None), ("user_email", None), ("leetcode_username", ""), ("reset_stage", "email"), ("reset_email", "")]:
    if key not in st.session_state:
        st.session_state[key] = default

# Callback for the Already Attempted button
def handle_already_attempted(idx, username, slug, title, topic):
    mark_question_solved_supabase(username, slug, title, topic)
    # Remove it from the current session recommendations
    if 0 <= idx < len(st.session_state.recommendations):
        st.session_state.recommendations.pop(idx)

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(page_title="DSA Prep Hub", page_icon="🧠", layout="centered")

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ── */
    .stApp { font-family: 'Inter', sans-serif; }

    /* ── Hero Header ── */
    .hero { text-align: center; padding: 2.5rem 0 0.8rem 0; }
    .hero h1 {
        font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #a855f7 50%, #ec4899 100%);
        background-size: 200% 200%;
        animation: gradientShift 4s ease infinite;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem; letter-spacing: -0.5px;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .hero p { font-size: 1rem; color: #9ca3af; margin-top: 0; letter-spacing: 0.2px; }
    .divider {
        height: 2px; border-radius: 2px;
        background: linear-gradient(90deg, transparent, #667eea, #a855f7, #ec4899, transparent);
        margin: 0.5rem 0 2rem 0; opacity: 0.5;
    }

    /* ── Auth Card ── */
    .auth-wrapper { max-width: 420px; margin: 0 auto; }
    .auth-subtitle {
        text-align: center; color: #9ca3af; margin-bottom: 1.5rem;
        font-size: 0.95rem; line-height: 1.5;
    }

    /* ── Section Headers ── */
    .section-header {
        display: flex; align-items: center; gap: 0.6rem;
        margin-bottom: 1.2rem; margin-top: 0.5rem;
    }
    .section-header .icon {
        width: 36px; height: 36px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(168,85,247,0.15));
        border: 1px solid rgba(168,85,247,0.2);
    }
    .section-header .text {
        font-size: 1.15rem; font-weight: 700; color: #e2e8f0;
        letter-spacing: -0.3px;
    }

    /* ── Result Cards ── */
    .result-box {
        background: rgba(30, 30, 46, 0.6);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(102, 126, 234, 0.12);
        border-left: 4px solid #a855f7;
        border-radius: 16px; padding: 1.4rem 1.6rem;
        margin-bottom: 0.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative; overflow: hidden;
    }
    .result-box::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(168,85,247,0.3), transparent);
    }
    .result-box:hover {
        border-color: rgba(168, 85, 247, 0.3);
        box-shadow: 0 8px 32px rgba(168, 85, 247, 0.08);
        transform: translateY(-2px);
    }
    .result-box h4 {
        margin-top: 0; margin-bottom: 0.5rem; color: #f1f5f9;
        font-weight: 700; font-size: 1.05rem; letter-spacing: -0.2px;
    }
    .result-box p { color: #cbd5e1; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.5rem; }
    .result-box a {
        color: #a855f7; text-decoration: none; font-weight: 600;
        transition: color 0.2s;
    }
    .result-box a:hover { color: #c084fc; }

    /* ── Company Badges ── */
    .company-badge {
        background: rgba(168, 85, 247, 0.1); color: #c084fc;
        padding: 3px 10px; border-radius: 20px; font-size: 0.7rem;
        font-weight: 600; margin-right: 5px;
        border: 1px solid rgba(168, 85, 247, 0.2);
        display: inline-block; margin-bottom: 4px; letter-spacing: 0.3px;
    }

    /* ── Sidebar ── */
    .sidebar-user-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(168,85,247,0.1));
        border: 1px solid rgba(168,85,247,0.15);
        border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 0.8rem;
    }
    .sidebar-user-card .email {
        font-size: 0.85rem; font-weight: 600; color: #e2e8f0;
        margin-bottom: 2px;
    }
    .sidebar-user-card .role {
        font-size: 0.7rem; color: #818cf8; font-weight: 500;
    }
    .sidebar-item {
        background: rgba(30, 30, 46, 0.4);
        border: 1px solid rgba(102, 126, 234, 0.08);
        border-radius: 10px; padding: 0.6rem 0.8rem;
        margin-bottom: 0.45rem; transition: all 0.25s ease;
    }
    .sidebar-item:hover {
        border-color: rgba(168, 85, 247, 0.25);
        background: rgba(168, 85, 247, 0.05);
    }
    .sidebar-item a {
        color: #e2e8f0 !important; text-decoration: none;
        font-weight: 500; font-size: 0.82rem;
    }
    .sidebar-item a:hover { color: #c084fc !important; }
    .sidebar-meta { font-size: 0.68rem; color: #6b7280; margin-top: 2px; }
    .sidebar-cat-badge {
        font-size: 0.62rem; background: rgba(102,126,234,0.1);
        color: #818cf8; padding: 1px 7px; border-radius: 5px; font-weight: 500;
    }

    /* ── Stats Row ── */
    .stat-pill {
        display: inline-block; background: rgba(168,85,247,0.08);
        border: 1px solid rgba(168,85,247,0.15); border-radius: 20px;
        padding: 4px 14px; font-size: 0.78rem; color: #c084fc;
        font-weight: 600; margin-right: 8px;
    }

    /* ── Footer ── */
    .footer {
        text-align: center; color: #4b5563; font-size: 0.75rem;
        margin-top: 3rem; padding: 1rem 0;
        border-top: 1px solid rgba(107,114,128,0.1);
    }
    .footer a { color: #a855f7; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🧠 DSA Prep Hub</h1>
    <p>Find the most trending &amp; important DSA questions — powered by AI</p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# AUTH GATE: Show Login/Signup if not authenticated
# ══════════════════════════════════════════════════════════════
if not st.session_state.user_id:
    st.markdown('<p class="auth-subtitle">Sign in to track your progress and get personalized recommendations</p>', unsafe_allow_html=True)
    
    auth_tab_login, auth_tab_signup, auth_tab_forgot = st.tabs(["🔑 Login", "✨ Sign Up", "🔒 Forgot Password"])
    
    with auth_tab_login:
        with st.form("login_form"):
            login_email = st.text_input("Email", placeholder="you@example.com", key="login_email_input")
            login_pass = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass_input")
            login_submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if login_submit:
                if not login_email or not login_pass:
                    st.warning("Please fill in all fields.")
                else:
                    user, err = login_user(login_email, login_pass)
                    if user:
                        st.session_state.user_id = user.id
                        st.session_state.user_email = user.email
                        profile = get_user_profile(user.id)
                        if profile:
                            st.session_state.leetcode_username = profile.get("leetcode_username", "")
                        st.success("✅ Logged in successfully!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {err}")
    
    with auth_tab_signup:
        with st.form("signup_form"):
            signup_email = st.text_input("Email", placeholder="you@example.com", key="signup_email_input")
            signup_pass = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_pass_input")
            signup_pass2 = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="signup_pass2_input")
            signup_lc = st.text_input("LeetCode Username (optional)", placeholder="e.g. neetcode", key="signup_lc_input")
            signup_submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            
            if signup_submit:
                if not signup_email or not signup_pass:
                    st.warning("Email and password are required.")
                elif signup_pass != signup_pass2:
                    st.error("Passwords do not match.")
                elif len(signup_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user, err = signup_user(signup_email, signup_pass, signup_lc.strip())
                    if user:
                        st.session_state.user_id = user.id
                        st.session_state.user_email = user.email
                        st.session_state.leetcode_username = signup_lc.strip()
                        st.success("✅ Account created! You're now logged in.")
                        st.rerun()
                    else:
                        st.error(f"Signup failed: {err}")

    with auth_tab_forgot:
        # ── Stage 1: Enter email to receive OTP ──
        if st.session_state.reset_stage == "email":
            st.markdown('<p style="color:#9ca3af; font-size:0.9rem; margin-bottom:1rem;">Enter your registered email and we\'ll send you a one-time code to reset your password.</p>', unsafe_allow_html=True)
            with st.form("forgot_email_form"):
                reset_email = st.text_input("Email", placeholder="you@example.com", key="forgot_email_input")
                send_otp_btn = st.form_submit_button("📧 Send OTP", use_container_width=True, type="primary")
                
                if send_otp_btn:
                    if not reset_email:
                        st.warning("Please enter your email.")
                    else:
                        with st.spinner("Sending OTP..."):
                            success, err = send_password_reset(reset_email.strip())
                        if success:
                            st.session_state.reset_email = reset_email.strip()
                            st.session_state.reset_stage = "otp"
                            st.success("✅ OTP sent! Check your email inbox (and spam folder).")
                            st.rerun()
                        else:
                            st.error(f"Failed to send OTP: {err}")

        # ── Stage 2: Enter OTP + new password ──
        elif st.session_state.reset_stage == "otp":
            st.markdown(f"""
            <div style="background: rgba(102,126,234,0.08); border: 1px solid rgba(102,126,234,0.2);
                        border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1rem;">
                <p style="color:#c084fc; font-size:0.85rem; margin:0;">📬 OTP sent to <strong>{st.session_state.reset_email}</strong></p>
                <p style="color:#9ca3af; font-size:0.78rem; margin:0.3rem 0 0 0;">Enter the code from your email and set a new password below.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("otp_verify_form"):
                otp_code = st.text_input("OTP Code", placeholder="Enter code from email", key="otp_code_input")
                new_pass = st.text_input("New Password", type="password", placeholder="Min 6 characters", key="reset_new_pass")
                new_pass2 = st.text_input("Confirm New Password", type="password", placeholder="••••••••", key="reset_new_pass2")
                reset_btn = st.form_submit_button("🔐 Reset Password", use_container_width=True, type="primary")
                
                if reset_btn:
                    if not otp_code or not new_pass:
                        st.warning("Please fill in all fields.")
                    elif new_pass != new_pass2:
                        st.error("Passwords do not match.")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        with st.spinner("Verifying OTP..."):
                            success, err = verify_otp_and_reset(
                                st.session_state.reset_email,
                                otp_code.strip(),
                                new_pass
                            )
                        if success:
                            st.session_state.reset_stage = "done"
                            st.rerun()
                        else:
                            st.error(f"Reset failed: {err}")
            
            col_back, col_resend = st.columns(2)
            with col_back:
                if st.button("← Back", key="back_to_email", use_container_width=True):
                    st.session_state.reset_stage = "email"
                    st.session_state.reset_email = ""
                    st.rerun()
            with col_resend:
                if st.button("🔄 Resend OTP", key="resend_otp", use_container_width=True):
                    success, err = send_password_reset(st.session_state.reset_email)
                    if success:
                        st.success("OTP resent! Check your email.")
                    else:
                        st.error(f"Failed: {err}")

        # ── Stage 3: Success ──
        elif st.session_state.reset_stage == "done":
            st.markdown("""
            <div style="text-align:center; padding: 2rem 0;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">✅</div>
                <h3 style="color: #e2e8f0; font-weight: 700;">Password Reset Successful!</h3>
                <p style="color: #9ca3af; font-size: 0.9rem;">You can now log in with your new password.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔑 Go to Login", use_container_width=True, type="primary", key="go_to_login"):
                st.session_state.reset_stage = "email"
                st.session_state.reset_email = ""
                st.rerun()

    st.markdown('<div class="footer">Built with ❤️ using LangChain &amp; Streamlit</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════
# MAIN APP (user is authenticated)
# ══════════════════════════════════════════════════════════════
lc_username = st.session_state.leetcode_username

# ── Sidebar: User Info & Settings ────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-user-card">
        <div class="email">👤 {st.session_state.user_email}</div>
        <div class="role">DSA Prep Member</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("⚙️ Profile Settings"):
        new_lc = st.text_input("LeetCode Username", value=lc_username, key="profile_lc_input")
        if st.button("Save", key="save_profile", use_container_width=True):
            update_leetcode_username(st.session_state.user_id, new_lc.strip())
            st.session_state.leetcode_username = new_lc.strip()
            lc_username = new_lc.strip()
            st.success("Saved!")
            st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.rerun()
    
    st.markdown("---")

# ── Sidebar Progress Tracker ─────────────────────────────────
if "sidebar_load_count" not in st.session_state:
    st.session_state.sidebar_load_count = 10

if lc_username:
    username_clean = lc_username.strip()
    supa_solved = get_user_solved_supabase(username_clean)
    pub_solved, _ = get_recent_solved_questions(username_clean)
    
    # Combine all unique slugs
    all_solved_questions = supa_solved + (pub_solved if pub_solved else [])
    
    # Deduplicate by slug
    seen_sidebar_slugs = set()
    deduped_questions = []
    for q in all_solved_questions:
        slug = q['slug']
        if slug not in seen_sidebar_slugs:
            seen_sidebar_slugs.add(slug)
            deduped_questions.append(q)
    
    # Fetch categories
    unique_slugs = list({q['slug'] for q in deduped_questions})
    
    with st.sidebar:
        with st.spinner("Fetching categories & patterns..."):
            category_map = get_batched_question_categories(unique_slugs)
            pattern_map = get_batched_question_patterns(unique_slugs)
    
    # Group into categories for the "By Category" tab
    grouped_solved = {cat: [] for cat in CATEGORY_SEQUENCE}
    for q in deduped_questions:
        cat = category_map.get(q['slug'], "Others")
        if cat not in grouped_solved:
            grouped_solved[cat] = []
        grouped_solved[cat].append(q)
    
    # Group into patterns for the "By Pattern" tab
    grouped_patterns = {pat: [] for pat in PATTERN_SEQUENCE}
    for q in deduped_questions:
        pat = pattern_map.get(q['slug'], "Others")
        if pat not in grouped_patterns:
            grouped_patterns[pat] = []
        grouped_patterns[pat].append(q)
                
    st.sidebar.title("📚 Your Progress")
    
    if not deduped_questions:
        st.sidebar.info("No solved questions found yet!")
    else:
        tab_latest, tab_category, tab_pattern = st.sidebar.tabs(["🕐 Latest", "📂 Category", "🧩 Pattern"])
        
        # ── Tab 1: Latest Questions ──────────────────────────
        with tab_latest:
            # Sort by date (newest first), questions without dates go to the end
            sorted_questions = sorted(
                deduped_questions,
                key=lambda q: q.get('date', '') or '0000-00-00',
                reverse=True
            )
            
            display_count = st.session_state.sidebar_load_count
            visible = sorted_questions[:display_count]
            
            for q in visible:
                date_str = q.get('date', '') or ''
                cat_label = category_map.get(q['slug'], 'Others')
                st.markdown(f"""
                <div class="sidebar-item">
                    <a href="https://leetcode.com/problems/{q['slug']}/" target="_blank">{q['title']}</a>
                    <div class="sidebar-meta">{date_str} &nbsp; <span class="sidebar-cat-badge">{cat_label}</span></div>
                </div>
                """, unsafe_allow_html=True)
            
            if display_count < len(sorted_questions):
                remaining = len(sorted_questions) - display_count
                if st.button(f"Load More ({remaining} remaining)", key="load_more_sidebar", use_container_width=True):
                    st.session_state.sidebar_load_count += 10
                    st.rerun()
        
        # ── Tab 2: By Category ───────────────────────────────
        with tab_category:
            for t in CATEGORY_SEQUENCE:
                questions = grouped_solved.get(t, [])
                if questions:
                    with st.expander(f"{t} ({len(questions)})"):
                        for q in questions:
                            date_str = q.get('date', '') or ''
                            st.markdown(f"""
                            <div class="sidebar-item">
                                <a href="https://leetcode.com/problems/{q['slug']}/" target="_blank">{q['title']}</a>
                                <div class="sidebar-meta">{date_str}</div>
                            </div>
                            """, unsafe_allow_html=True)
        
        # ── Tab 3: By Pattern ────────────────────────────────
        with tab_pattern:
            for p in PATTERN_SEQUENCE:
                questions = grouped_patterns.get(p, [])
                if questions:
                    with st.expander(f"{p} ({len(questions)})"):
                        for q in questions:
                            date_str = q.get('date', '') or ''
                            st.markdown(f"""
                            <div class="sidebar-item">
                                <a href="https://leetcode.com/problems/{q['slug']}/" target="_blank">{q['title']}</a>
                                <div class="sidebar-meta">{date_str}</div>
                            </div>
                            """, unsafe_allow_html=True)

st.markdown('<div class="section-header"><div class="icon">📚</div><div class="text">Search Criteria</div></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    topic = st.text_input("📚 DSA Topic", placeholder="e.g. Binary Trees, Graphs, DP...")

with col2:
    level = st.selectbox("🎯 Difficulty Level", ["Easy", "Medium", "Hard"])

number = st.slider("🎯 Number of Questions", 1, 20, 3)

# ── Prompt Template ──────────────────────────────────────────
template = PromptTemplate(
    template="""
You are an expert DSA coach and interview preparation specialist.

Your task is to curate exactly {number} Data Structures and Algorithms questions on the topic "{topic}" at the "{level}" difficulty level.

{avoid_instructions}

Selection Criteria (in order of priority):
1. Questions that are MOST FREQUENTLY asked in recent tech interviews (2024-2025) across top companies.
2. Questions that are trending on LeetCode (most liked, most discussed).
3. Classic must-know questions that are considered essential for mastering this topic.

Ensure you return exactly {number} questions.
""",
    input_variables=["topic", "level" , "number", "avoid_instructions"],
)

# ── Action Button ────────────────────────────────────────────
st.markdown("")  # spacing

if st.button("🔍  Find Questions", use_container_width=True, type="primary"):
    if not topic:
        st.warning("⚠️ Please enter a DSA topic to search.")
    else:
        with st.spinner("🔎 Searching and filtering questions..."):
            solved_data = []
            
            if lc_username:
                username = lc_username.strip()
                
                # 1. Fetch from Supabase Memory
                supa_solved = get_user_solved_supabase(username)
                
                # 2. Fetch from Public API Baseline
                pub_solved, error_msg = get_recent_solved_questions(username)
                
                if error_msg:
                    st.toast(f"⚠️ Unable to fetch public LeetCode data. Reason: {error_msg}")
                
                # Combine and deduplicate
                combined = supa_solved + (pub_solved if pub_solved else [])
                seen = set()
                for item in combined:
                    if item['slug'] not in seen:
                        seen.add(item['slug'])
                        solved_data.append(item)
                        
                st.success(f"✅ Found {len(solved_data)} total solved questions for `{username}` in memory & public profile. Filtering them out...")

            # Extract slugs and normalized titles for fast checking
            solved_slugs = {item['slug'] for item in solved_data}
            solved_titles_norm = [normalize_title(item['title']) for item in solved_data]

            approved_questions = []
            attempts = 0
            max_attempts = 5

            while len(approved_questions) < number and attempts < max_attempts:
                attempts += 1
                needed = number - len(approved_questions)
                
                avoid_instructions = ""
                if approved_questions:
                    avoid_instructions += "DO NOT RECOMMEND these already selected questions:\n"
                    for q in approved_questions:
                        avoid_instructions += f"- {q.title}\n"
                
                if solved_data:
                    avoid_instructions += "\nCRITICAL: The user has already solved the following questions. DO NOT recommend them:\n"
                    sample_solved = [item['title'] for item in solved_data[:50]]
                    for q in sample_solved:
                        avoid_instructions += f"- {q}\n"
                        
                prompt = template.format(
                    topic=topic,
                    level=level,
                    number=needed,
                    avoid_instructions=avoid_instructions
                )
                
                try:
                    result = structured_llm.invoke(prompt)
                    if not result or not result.questions:
                        continue
                        
                    for q in result.questions:
                        if len(approved_questions) >= number:
                            break
                            
                        q_slug = extract_slug_from_url(q.leetcode_link)
                        q_norm = normalize_title(q.title)
                        
                        is_solved = False
                        
                        if q_slug and q_slug in solved_slugs:
                            is_solved = True
                            
                        if not is_solved:
                            for solved_norm in solved_titles_norm:
                                if is_fuzzy_match(q_norm, solved_norm):
                                    is_solved = True
                                    break
                                    
                        for existing_q in approved_questions:
                            if is_fuzzy_match(q_norm, normalize_title(existing_q.title)):
                                is_solved = True
                                break

                        if not is_solved:
                            approved_questions.append(q)
                            
                except Exception as e:
                    st.error(f"Error communicating with LLM: {str(e)}")
                    break

            if not approved_questions:
                st.error("Failed to generate valid questions. The topic might be too narrow or all classic questions are already solved.")
            else:
                st.session_state.recommendations = approved_questions

# ── Render Recommendations ───────────────────────────────────
if st.session_state.recommendations:
    st.markdown('<div class="section-header"><div class="icon">✨</div><div class="text">Your Custom Recommendations</div></div>', unsafe_allow_html=True)
    
    for i, q in enumerate(st.session_state.recommendations):
        with st.container():
            companies_html = " ".join([f"<span class='company-badge'>{c}</span>" for c in q.companies]) if hasattr(q, 'companies') and q.companies else ""
            
            st.markdown(f"""
            <div class="result-box">
                <h4>{q.title}</h4>
                <div style="margin-bottom: 0.8rem;">{companies_html}</div>
                <p><strong>Why it matters:</strong> {q.why_it_matters}</p>
                <p><strong>Description:</strong><br/>{q.description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            q_slug = extract_slug_from_url(q.leetcode_link)
            col_solve, col_done = st.columns(2)
            
            with col_solve:
                st.link_button("🔗 Solve on LeetCode", q.leetcode_link, use_container_width=True)
            
            with col_done:
                if lc_username:
                    st.button("✅ Mark as Done",
                             key=f"attempt_{q_slug}_{i}",
                             on_click=handle_already_attempted,
                             args=(i, lc_username.strip(), q_slug, q.title, topic.strip() if topic else "General"),
                             use_container_width=True)
                else:
                    st.button("✅ Mark as Done", key=f"attempt_no_lc_{i}", disabled=True,
                             use_container_width=True, help="Set your LeetCode username in Profile Settings to enable this")
            
            st.markdown("<br/>", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Built with ❤️ using LangChain &amp; Streamlit
</div>
""", unsafe_allow_html=True)