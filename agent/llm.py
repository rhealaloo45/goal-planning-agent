"""
LLM Integration Module
-----------------------
Azure OpenAI integration with simulation fallback.
Updated for detailed weekly plans with hours, resources per topic,
and option-based clarification questions.
"""

import json
import os
import re
import random

from openai import AzureOpenAI

_client = None


def _get_client():
    global _client
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_key:
        return None
    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-12-01-preview",
        )
    return _client


def call_llm(prompt: str, system_prompt: str = "You are a helpful AI assistant.", expect_json: bool = False) -> str:
    if expect_json:
        system_prompt += "\nYou MUST respond with valid JSON only. No markdown fences, no extra text."

    client = _get_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

    if client is not None:
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LLM] Azure OpenAI failed: {repr(e)}, using simulation.")

    return _simulate_response(prompt, expect_json)


# ---------------------------------------------------------------------------
# Simulation Router
# ---------------------------------------------------------------------------

def _simulate_response(prompt: str, expect_json: bool) -> str:
    lower = prompt.lower()
    if "needs_clarification" in lower or "enough information" in lower:
        return _simulate_clarification(prompt)
    if "refine" in lower or "modify" in lower or "user's change request" in lower:
        return _simulate_refinement(prompt)
    if "complete" in lower and "plan" in lower or "comprehensive plan" in lower or "weekly plan" in lower:
        return _simulate_full_plan(prompt)
    if expect_json:
        return json.dumps({"response": "Simulated response."})
    return "Simulated response."

def _simulate_refinement(prompt: str) -> str:
    """Mock a refined plan by slightly altering the existing one."""
    match = re.search(r'```json\n(.*?)\n```', prompt, re.DOTALL)
    if not match: return json.dumps({"timeline": [], "goal_summary": "Error: could not parse plan for simulation"})
    
    try:
        plan = json.loads(match.group(1))
        # Add a note to the goal summary
        plan["goal_summary"] = plan.get("goal_summary", "") + " (Refined with your suggestions)"
        # Maybe change hours slightly
        if plan.get("timeline"):
            plan["timeline"][0]["total_hours"] = 100 
        return json.dumps(plan)
    except:
        return match.group(1) # Return as is


# ---------------------------------------------------------------------------
# Clarification (with options)
# ---------------------------------------------------------------------------

def _simulate_clarification(prompt: str) -> str:
    goal = _extract_goal(prompt)
    gl = goal.lower()
    word_count = len(goal.split())
    specific_signals = ["using", "with", "in python", "in react", "for my",
                        "week", "month", "deadline", "budget", "beginner", "advanced"]
    has_specifics = any(s in gl for s in specific_signals)

    if word_count < 6 and not has_specifics:
        questions = _generate_questions(goal)
        return json.dumps({"needs_clarification": True, "questions": questions})
    return json.dumps({"needs_clarification": False})


def _generate_questions(goal: str) -> list:
    gl = goal.lower()

    timeline_q = {
        "question": "What is your target timeline for this goal?",
        "options": ["1-2 weeks", "1 month", "2-3 months", "6 months", "No fixed deadline"]
    }
    experience_q = {
        "question": "What is your current experience level?",
        "options": ["Complete beginner", "Some basics", "Intermediate", "Advanced"]
    }
    commitment_q = {
        "question": "How many hours per week can you dedicate?",
        "options": ["2-5 hours", "5-10 hours", "10-15 hours", "15-20 hours", "20+ hours"]
    }

    if any(w in gl for w in ["website", "web", "app", "software", "build", "create"]):
        return [timeline_q, experience_q, commitment_q, {
            "question": "What technologies do you prefer?",
            "options": ["HTML/CSS/JS (Vanilla)", "React", "Next.js", "Python/Flask", "WordPress", "No preference"]
        }]

    if any(w in gl for w in ["learn", "study", "master", "understand"]):
        return [timeline_q, experience_q, commitment_q, {
            "question": "How do you prefer to learn?",
            "options": ["Video courses", "Reading documentation", "Hands-on projects", "Interactive exercises", "Mix of everything"]
        }]

    if any(w in gl for w in ["business", "startup", "launch", "company"]):
        return [timeline_q, experience_q, {
            "question": "What is your budget situation?",
            "options": ["Bootstrapping (no budget)", "Small budget ($100-500)", "Moderate budget ($500-2000)", "Well-funded"]
        }, {
            "question": "Have you validated the idea?",
            "options": ["Just an idea", "Talked to potential users", "Have early interest/waitlist", "Already have paying customers"]
        }]

    if any(w in gl for w in ["market", "campaign", "brand", "social", "seo"]):
        return [timeline_q, commitment_q, {
            "question": "What is your target audience?",
            "options": ["Gen Z (18-24)", "Millennials (25-40)", "Professionals (30-50)", "General audience", "B2B / Companies"]
        }, {
            "question": "Do you have an existing brand presence?",
            "options": ["Starting from scratch", "Have a website only", "Some social media presence", "Established brand"]
        }]

    if any(w in gl for w in ["ml", "machine learning", "ai", "data", "model"]):
        return [timeline_q, experience_q, commitment_q, {
            "question": "What type of ML project?",
            "options": ["Learning ML concepts", "Building a prediction model", "Computer vision", "NLP / Text analysis", "General AI exploration"]
        }]

    return [timeline_q, experience_q, commitment_q, {
        "question": "What specific outcome do you expect?",
        "options": ["A finished project/product", "Knowledge & skills", "A written plan/strategy", "Portfolio piece", "Other"]
    }]


# ---------------------------------------------------------------------------
# Full Plan Generation (detailed weekly with hours & resources per topic)
# ---------------------------------------------------------------------------

def _simulate_full_plan(prompt: str) -> str:
    goal = _extract_goal(prompt)
    plan = _build_plan_for_goal(goal)
    return json.dumps(plan)


def _build_plan_for_goal(goal: str) -> dict:
    gl = goal.lower()

    if any(w in gl for w in ["website", "web app", "landing page", "portfolio", "frontend"]):
        return _plan_website(goal)
    if any(w in gl for w in ["learn", "study", "course", "tutorial", "master", "understand"]):
        return _plan_learning(goal)
    if any(w in gl for w in ["business", "startup", "company", "launch product", "saas"]):
        return _plan_business(goal)
    if any(w in gl for w in ["machine learning", "ml", "ai", "model", "data science", "predict"]):
        return _plan_ml(goal)
    if any(w in gl for w in ["marketing", "campaign", "social media", "brand", "growth", "seo"]):
        return _plan_marketing(goal)
    if any(w in gl for w in ["mobile app", "android", "ios", "flutter", "react native"]):
        return _plan_mobile(goal)
    return _plan_generic(goal)


def _plan_website(goal: str) -> dict:
    return {
        "goal_summary": f"Build a professional, modern website: {goal}. Fully responsive, optimized for performance, and ready for deployment.",
        "assumptions": [
            "Basic knowledge of HTML, CSS, and JavaScript",
            "Building from scratch with modern tools",
            "Hosting on a cloud platform (Vercel/Netlify)",
        ],
        "timeline": [
            {
                "week": "Week 1",
                "title": "Planning & Design System",
                "total_hours": 12,
                "topics": [
                    {"name": "Site Architecture & Wireframing", "hours": 3, "resource": "Figma Crash Course", "resource_url": "https://www.figma.com/resources/learn-design/", "description": "Define all pages, navigation structure, and create wireframes for each major page."},
                    {"name": "Color Palette & Typography", "hours": 2, "resource": "Coolors.co", "resource_url": "https://coolors.co", "description": "Generate and select a harmonious color scheme. Choose complementary Google Fonts."},
                    {"name": "Component Design in Figma", "hours": 4, "resource": "Figma for Beginners (YouTube)", "resource_url": "https://www.youtube.com/results?search_query=figma+for+beginners", "description": "Design reusable components: buttons, cards, headers, footers, navigation bars."},
                    {"name": "Content Planning & Copywriting", "hours": 3, "resource": "Copywriting Guide", "resource_url": "https://www.nngroup.com/topic/writing-web/", "description": "Draft all page copy: hero headlines, about section, service descriptions, CTAs."},
                ],
                "milestone": "Complete wireframes and visual design system ready for development."
            },
            {
                "week": "Week 2",
                "title": "HTML/CSS Foundation",
                "total_hours": 14,
                "topics": [
                    {"name": "Project Setup & Git", "hours": 2, "resource": "MDN Web Docs", "resource_url": "https://developer.mozilla.org/en-US/docs/Learn", "description": "Initialize project with your chosen stack, set up Git repository, configure linting."},
                    {"name": "Semantic HTML Structure", "hours": 3, "resource": "HTML Best Practices", "resource_url": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "description": "Build the HTML skeleton for all pages using semantic elements (header, nav, main, section, footer)."},
                    {"name": "CSS Grid & Flexbox Layouts", "hours": 5, "resource": "CSS-Tricks Complete Guide", "resource_url": "https://css-tricks.com/snippets/css/complete-guide-grid/", "description": "Implement all page layouts using CSS Grid for page structure and Flexbox for component alignment."},
                    {"name": "Responsive Design (Mobile-First)", "hours": 4, "resource": "Responsive Design Guide", "resource_url": "https://web.dev/responsive-web-design-basics/", "description": "Add media queries for mobile, tablet, and desktop. Test on multiple viewports."},
                ],
                "milestone": "All pages built with responsive HTML/CSS, looking good on all screen sizes."
            },
            {
                "week": "Week 3",
                "title": "JavaScript & Interactivity",
                "total_hours": 12,
                "topics": [
                    {"name": "Navigation & Hamburger Menu", "hours": 2, "resource": "JS Navigation Tutorial", "resource_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "description": "Build responsive navigation with mobile hamburger menu, scroll-based styling changes."},
                    {"name": "Form Validation & Submission", "hours": 3, "resource": "Form Validation Guide", "resource_url": "https://developer.mozilla.org/en-US/docs/Learn/Forms/Form_validation", "description": "Create contact form with client-side validation. Set up form submission (Formspree/Netlify Forms)."},
                    {"name": "Scroll Animations & Transitions", "hours": 4, "resource": "Intersection Observer API", "resource_url": "https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API", "description": "Add scroll-triggered animations, smooth scrolling, hover effects, and micro-interactions."},
                    {"name": "Image Optimization & Lazy Loading", "hours": 3, "resource": "Web.dev Image Guide", "resource_url": "https://web.dev/fast/#optimize-your-images", "description": "Compress all images (WebP), implement lazy loading, add proper alt tags for SEO."},
                ],
                "milestone": "Fully interactive site with working forms, animations, and optimized assets."
            },
            {
                "week": "Week 4",
                "title": "SEO, Testing & Deployment",
                "total_hours": 10,
                "topics": [
                    {"name": "SEO & Meta Tags", "hours": 2, "resource": "Google SEO Starter Guide", "resource_url": "https://developers.google.com/search/docs/fundamentals/seo-starter-guide", "description": "Add title tags, meta descriptions, Open Graph tags, structured data, and sitemap.xml."},
                    {"name": "Cross-Browser Testing", "hours": 3, "resource": "BrowserStack", "resource_url": "https://www.browserstack.com", "description": "Test on Chrome, Firefox, Safari, Edge. Fix rendering inconsistencies and CSS issues."},
                    {"name": "Lighthouse Performance Audit", "hours": 2, "resource": "Lighthouse Docs", "resource_url": "https://developer.chrome.com/docs/lighthouse/", "description": "Run Lighthouse audits. Optimize for Performance, Accessibility, Best Practices, and SEO scores."},
                    {"name": "Deploy to Vercel/Netlify", "hours": 3, "resource": "Vercel Deployment Guide", "resource_url": "https://vercel.com/docs", "description": "Connect GitHub repo, configure custom domain, set up SSL, deploy to production."},
                ],
                "milestone": "Website live in production with custom domain, SSL, and 90+ Lighthouse scores."
            },
        ],
        "resources": [
            {"category": "Design Tools", "items": [
                {"name": "Figma", "url": "https://www.figma.com"},
                {"name": "Coolors", "url": "https://coolors.co"},
                {"name": "Google Fonts", "url": "https://fonts.google.com"},
                {"name": "Unsplash (free images)", "url": "https://unsplash.com"},
            ]},
            {"category": "Documentation", "items": [
                {"name": "MDN Web Docs", "url": "https://developer.mozilla.org"},
                {"name": "CSS-Tricks", "url": "https://css-tricks.com"},
                {"name": "Web.dev by Google", "url": "https://web.dev"},
            ]},
            {"category": "Deployment", "items": [
                {"name": "Vercel", "url": "https://vercel.com"},
                {"name": "Netlify", "url": "https://www.netlify.com"},
                {"name": "GitHub Pages", "url": "https://pages.github.com"},
            ]},
        ],
        "time_commitment": "10-14 hours per week for 4 weeks (total ~48 hours)",
        "execution_strategy": "Start with design before code. Build mobile-first, test on real devices frequently. Deploy to staging early so you can share progress. Focus on one page at a time rather than working across all simultaneously.",
    }


def _plan_learning(goal: str) -> dict:
    subject = re.sub(r'\b(learn|study|master|understand)\b', '', goal, flags=re.IGNORECASE).strip()
    if not subject:
        subject = "the subject"
    return {
        "goal_summary": f"Structured learning path to {goal}. Progresses from fundamentals through advanced topics with hands-on projects.",
        "assumptions": [
            "Starting from beginner to intermediate level",
            "Can dedicate 1-2 hours daily for focused study",
            "Access to a computer and internet for practice",
        ],
        "timeline": [
            {
                "week": "Week 1",
                "title": "Fundamentals & Setup",
                "total_hours": 10,
                "topics": [
                    {"name": "Core concepts overview", "hours": 3, "resource": "freeCodeCamp", "resource_url": "https://www.freecodecamp.org", "description": f"Watch introductory videos and read about the fundamental concepts of {subject}."},
                    {"name": "Environment setup", "hours": 2, "resource": "Official Documentation", "resource_url": "https://developer.mozilla.org", "description": "Install all necessary tools, IDEs, and configure your development environment."},
                    {"name": "First hands-on exercise", "hours": 3, "resource": "Exercism", "resource_url": "https://exercism.org", "description": "Complete 5 beginner-level exercises to get comfortable with the basics."},
                    {"name": "Note-taking & vocabulary", "hours": 2, "resource": "Notion", "resource_url": "https://notion.so", "description": "Create a structured knowledge base with key terms, concepts, and code snippets."},
                ],
                "milestone": "Understand the core concepts and have a working development environment."
            },
            {
                "week": "Week 2-3",
                "title": "Intermediate Concepts",
                "total_hours": 18,
                "topics": [
                    {"name": "Deep-dive into key topics", "hours": 6, "resource": "Coursera", "resource_url": "https://www.coursera.org", "description": f"Follow a structured course covering intermediate {subject} topics."},
                    {"name": "Practice challenges", "hours": 5, "resource": "HackerRank", "resource_url": "https://www.hackerrank.com", "description": "Complete 10-15 medium-difficulty challenges to solidify understanding."},
                    {"name": "Study real-world examples", "hours": 4, "resource": "GitHub", "resource_url": "https://github.com/explore", "description": "Read and analyze 3-5 well-written open-source projects."},
                    {"name": "Community participation", "hours": 3, "resource": "Stack Overflow / Reddit", "resource_url": "https://stackoverflow.com", "description": "Ask and answer questions. Engage in relevant subreddits or Discord communities."},
                ],
                "milestone": "Comfortable with intermediate concepts and able to solve problems independently."
            },
            {
                "week": "Week 4-5",
                "title": "Build Real Projects",
                "total_hours": 20,
                "topics": [
                    {"name": "Guided project #1", "hours": 6, "resource": "YouTube Tutorial", "resource_url": "https://www.youtube.com", "description": "Follow a tutorial to build a complete project from start to finish."},
                    {"name": "Independent project #2", "hours": 8, "resource": "Your own design", "resource_url": "#", "description": "Design and build your own project without following a guide. Apply all concepts learned."},
                    {"name": "Code review & refactoring", "hours": 3, "resource": "Clean Code principles", "resource_url": "https://refactoring.guru", "description": "Review your code for best practices, refactor for readability and performance."},
                    {"name": "Version control & documentation", "hours": 3, "resource": "Git Documentation", "resource_url": "https://git-scm.com/doc", "description": "Push projects to GitHub with proper README, comments, and commit history."},
                ],
                "milestone": "Two completed projects in your portfolio demonstrating practical skills."
            },
            {
                "week": "Week 6",
                "title": "Advanced Topics & Portfolio",
                "total_hours": 12,
                "topics": [
                    {"name": "Advanced patterns & best practices", "hours": 4, "resource": "Advanced courses", "resource_url": "https://www.udemy.com", "description": f"Study advanced {subject} patterns, optimization techniques, and industry standards."},
                    {"name": "Capstone project", "hours": 5, "resource": "Self-directed", "resource_url": "#", "description": "Build a substantial project that showcases your full range of skills."},
                    {"name": "Portfolio & documentation", "hours": 3, "resource": "GitHub Pages", "resource_url": "https://pages.github.com", "description": "Create a portfolio page, write blog posts about what you learned, update LinkedIn."},
                ],
                "milestone": "Advanced skills demonstrated through a capstone project and public portfolio."
            },
        ],
        "resources": [
            {"category": "Courses", "items": [
                {"name": "freeCodeCamp", "url": "https://www.freecodecamp.org"},
                {"name": "Coursera", "url": "https://www.coursera.org"},
                {"name": "Udemy", "url": "https://www.udemy.com"},
            ]},
            {"category": "Practice", "items": [
                {"name": "Exercism", "url": "https://exercism.org"},
                {"name": "HackerRank", "url": "https://www.hackerrank.com"},
                {"name": "LeetCode", "url": "https://leetcode.com"},
            ]},
            {"category": "Community", "items": [
                {"name": "Stack Overflow", "url": "https://stackoverflow.com"},
                {"name": "Dev.to", "url": "https://dev.to"},
                {"name": "Reddit", "url": "https://reddit.com"},
            ]},
        ],
        "time_commitment": "10-12 hours per week for 6 weeks (total ~60 hours)",
        "execution_strategy": "Follow the 70/30 rule: 70% hands-on practice, 30% theory. Build projects as early as possible. Don't try to learn everything at once - master one concept before moving to the next.",
    }


def _plan_business(goal: str) -> dict:
    return {
        "goal_summary": f"Roadmap to {goal}. Covers validation, MVP development, launch strategy, and initial growth.",
        "assumptions": [
            "You have a general business idea to validate",
            "Initial budget for tools and basic marketing available",
            "Goal is to validate and launch within 3 months",
        ],
        "timeline": [
            {
                "week": "Week 1-2",
                "title": "Market Research & Validation",
                "total_hours": 16,
                "topics": [
                    {"name": "Competitive analysis", "hours": 4, "resource": "SimilarWeb / Crunchbase", "resource_url": "https://www.similarweb.com", "description": "Analyze 5-10 competitors: pricing, features, positioning, reviews, weaknesses."},
                    {"name": "Customer interviews", "hours": 5, "resource": "The Mom Test (book)", "resource_url": "https://www.momtestbook.com", "description": "Interview 10-15 potential customers. Ask about their problems, not your solution."},
                    {"name": "Value proposition design", "hours": 3, "resource": "Strategyzer Canvas", "resource_url": "https://www.strategyzer.com/canvas", "description": "Define your unique value proposition, customer segments, and revenue model."},
                    {"name": "Lean business canvas", "hours": 4, "resource": "Lean Canvas Template", "resource_url": "https://leanstack.com/lean-canvas", "description": "Complete a lean canvas covering problem, solution, channels, revenue, and metrics."},
                ],
                "milestone": "Validated problem-solution fit with real customer feedback and a clear business model."
            },
            {
                "week": "Week 3-6",
                "title": "MVP Development",
                "total_hours": 40,
                "topics": [
                    {"name": "Define MVP scope", "hours": 4, "resource": "Product prioritization frameworks", "resource_url": "https://www.productplan.com/glossary/feature-prioritization/", "description": "Use MoSCoW method to define must-have vs nice-to-have features. Cut ruthlessly."},
                    {"name": "Build the MVP", "hours": 24, "resource": "Bubble / Carrd / Code", "resource_url": "https://bubble.io", "description": "Build the simplest version that delivers core value. Use no-code tools if faster."},
                    {"name": "Set up analytics", "hours": 4, "resource": "Mixpanel / PostHog", "resource_url": "https://posthog.com", "description": "Integrate product analytics to track sign-ups, feature usage, and retention."},
                    {"name": "Beta testing", "hours": 8, "resource": "Beta user outreach", "resource_url": "https://www.betalist.com", "description": "Recruit 20-30 beta users, collect feedback systematically, fix critical bugs."},
                ],
                "milestone": "Working MVP tested with real users and iterated based on feedback."
            },
            {
                "week": "Week 7-8",
                "title": "Launch Preparation",
                "total_hours": 16,
                "topics": [
                    {"name": "Landing page optimization", "hours": 4, "resource": "Carrd / Framer", "resource_url": "https://carrd.co", "description": "Create a conversion-optimized landing page with clear CTAs, social proof, and pricing."},
                    {"name": "Marketing materials", "hours": 4, "resource": "Canva", "resource_url": "https://www.canva.com", "description": "Design social media graphics, product screenshots, and launch announcement assets."},
                    {"name": "Pricing strategy", "hours": 3, "resource": "Pricing psychology", "resource_url": "https://www.priceintelligently.com", "description": "Research competitor pricing, define your pricing tiers, set up payment processing."},
                    {"name": "Launch plan & timeline", "hours": 5, "resource": "Product Hunt guide", "resource_url": "https://www.producthunt.com", "description": "Plan your launch sequence: Product Hunt, social media, email announcements, PR."},
                ],
                "milestone": "All launch materials ready, landing page live, and pricing finalized."
            },
            {
                "week": "Week 9-12",
                "title": "Launch & Initial Growth",
                "total_hours": 24,
                "topics": [
                    {"name": "Execute launch", "hours": 8, "resource": "Product Hunt / Social", "resource_url": "https://www.producthunt.com", "description": "Publish on Product Hunt, post on social media, send email announcements, engage communities."},
                    {"name": "Content marketing setup", "hours": 6, "resource": "Buffer / Ghost", "resource_url": "https://buffer.com", "description": "Start a blog, schedule social media content, build an email list with valuable content."},
                    {"name": "Analyze & iterate", "hours": 6, "resource": "Google Analytics", "resource_url": "https://analytics.google.com", "description": "Review acquisition/activation/retention metrics. Identify winning channels and double down."},
                    {"name": "Customer success setup", "hours": 4, "resource": "Intercom / Crisp", "resource_url": "https://crisp.chat", "description": "Set up customer support, onboarding emails, and feedback collection systems."},
                ],
                "milestone": "Product launched publicly with initial users, revenue, and growth channels identified."
            },
        ],
        "resources": [
            {"category": "Business Planning", "items": [
                {"name": "Lean Canvas", "url": "https://leanstack.com/lean-canvas"},
                {"name": "Strategyzer", "url": "https://www.strategyzer.com"},
                {"name": "The Mom Test", "url": "https://www.momtestbook.com"},
            ]},
            {"category": "Building", "items": [
                {"name": "Bubble (no-code)", "url": "https://bubble.io"},
                {"name": "Stripe (payments)", "url": "https://stripe.com"},
                {"name": "Vercel (hosting)", "url": "https://vercel.com"},
            ]},
            {"category": "Marketing & Launch", "items": [
                {"name": "Product Hunt", "url": "https://www.producthunt.com"},
                {"name": "Canva", "url": "https://www.canva.com"},
                {"name": "Mailchimp", "url": "https://mailchimp.com"},
            ]},
        ],
        "time_commitment": "12-15 hours per week for 12 weeks (total ~150 hours)",
        "execution_strategy": "Validate before building. Talk to customers before writing code. Build the smallest possible MVP, launch fast, and iterate. Revenue is the ultimate validation.",
    }


def _plan_ml(goal: str) -> dict:
    return {
        "goal_summary": f"Complete roadmap for: {goal}. Covers fundamentals, data preparation, model development, and deployment.",
        "assumptions": [
            "Basic Python programming knowledge",
            "Access to a computer with 8GB+ RAM or cloud resources",
            "Working with structured data (can adapt to images/text)",
        ],
        "timeline": [
            {
                "week": "Week 1",
                "title": "ML Foundations & Environment",
                "total_hours": 12,
                "topics": [
                    {"name": "ML concepts & theory", "hours": 4, "resource": "Andrew Ng's ML Course", "resource_url": "https://www.coursera.org/learn/machine-learning", "description": "Supervised vs unsupervised learning, bias-variance tradeoff, overfitting, evaluation metrics."},
                    {"name": "Python for data science", "hours": 3, "resource": "Kaggle Learn: Python", "resource_url": "https://www.kaggle.com/learn/python", "description": "NumPy, pandas basics. Loading, inspecting, and manipulating datasets."},
                    {"name": "Environment setup", "hours": 2, "resource": "Jupyter Documentation", "resource_url": "https://jupyter.org", "description": "Install Python, Jupyter Lab, scikit-learn, pandas, matplotlib. Set up virtual environment."},
                    {"name": "Data visualization", "hours": 3, "resource": "Kaggle Learn: Visualization", "resource_url": "https://www.kaggle.com/learn/data-visualization", "description": "Matplotlib & Seaborn basics. Histograms, scatter plots, heatmaps, box plots."},
                ],
                "milestone": "Understand ML fundamentals and can load, explore, and visualize datasets."
            },
            {
                "week": "Week 2",
                "title": "Data Preparation & Feature Engineering",
                "total_hours": 12,
                "topics": [
                    {"name": "Data cleaning techniques", "hours": 4, "resource": "Kaggle Learn: Data Cleaning", "resource_url": "https://www.kaggle.com/learn/data-cleaning", "description": "Handle missing values, outliers, duplicate rows, inconsistent formats. Imputation strategies."},
                    {"name": "Feature engineering", "hours": 4, "resource": "Feature Engineering Guide", "resource_url": "https://www.kaggle.com/learn/feature-engineering", "description": "Create new features, encode categoricals (one-hot, label), scale numericals (StandardScaler, MinMax)."},
                    {"name": "Train-test split strategy", "hours": 2, "resource": "scikit-learn Docs", "resource_url": "https://scikit-learn.org/stable/modules/cross_validation.html", "description": "Proper splitting, stratification, cross-validation setup, preventing data leakage."},
                    {"name": "EDA on a real dataset", "hours": 2, "resource": "Kaggle Notebooks", "resource_url": "https://www.kaggle.com/code", "description": "Complete a full EDA on a public dataset: distributions, correlations, insights."},
                ],
                "milestone": "Can prepare any raw dataset for ML modeling with clean features."
            },
            {
                "week": "Week 3-4",
                "title": "Model Training & Optimization",
                "total_hours": 20,
                "topics": [
                    {"name": "Baseline models", "hours": 5, "resource": "scikit-learn Tutorials", "resource_url": "https://scikit-learn.org/stable/tutorial/", "description": "Train Logistic Regression, Decision Tree, Random Forest. Compare with baseline metrics."},
                    {"name": "Advanced algorithms", "hours": 5, "resource": "XGBoost Documentation", "resource_url": "https://xgboost.readthedocs.io", "description": "XGBoost, LightGBM, SVM. When to use which algorithm."},
                    {"name": "Hyperparameter tuning", "hours": 4, "resource": "Optuna Documentation", "resource_url": "https://optuna.org", "description": "GridSearchCV, RandomizedSearch, Bayesian optimization with Optuna."},
                    {"name": "Model evaluation", "hours": 3, "resource": "ML Metrics Guide", "resource_url": "https://scikit-learn.org/stable/modules/model_evaluation.html", "description": "Precision, recall, F1, AUC-ROC, confusion matrix. Choosing the right metric."},
                    {"name": "Experiment tracking", "hours": 3, "resource": "Weights & Biases", "resource_url": "https://wandb.ai", "description": "Track experiments, compare runs, log metrics and hyperparameters systematically."},
                ],
                "milestone": "Trained and tuned multiple models with proper evaluation and experiment tracking."
            },
            {
                "week": "Week 5-6",
                "title": "Deployment & Documentation",
                "total_hours": 14,
                "topics": [
                    {"name": "Model serving with Flask/FastAPI", "hours": 4, "resource": "FastAPI Documentation", "resource_url": "https://fastapi.tiangolo.com", "description": "Wrap your best model in a REST API. Accept input, return predictions."},
                    {"name": "Testing & validation", "hours": 3, "resource": "ML Testing Guide", "resource_url": "https://madewithml.com/courses/mlops/testing/", "description": "Test edge cases, validate on holdout data, check for bias and robustness."},
                    {"name": "Documentation & report", "hours": 4, "resource": "Jupyter + Markdown", "resource_url": "https://jupyter.org", "description": "Create a comprehensive notebook with methodology, results, visualizations, and conclusions."},
                    {"name": "Portfolio project page", "hours": 3, "resource": "GitHub", "resource_url": "https://github.com", "description": "Push to GitHub with clean README, requirements.txt, and demo instructions."},
                ],
                "milestone": "Complete ML project with API deployment, documentation, and portfolio-ready presentation."
            },
        ],
        "resources": [
            {"category": "Courses", "items": [
                {"name": "fast.ai (Practical Deep Learning)", "url": "https://www.fast.ai"},
                {"name": "Andrew Ng's ML (Coursera)", "url": "https://www.coursera.org/learn/machine-learning"},
                {"name": "Kaggle Learn", "url": "https://www.kaggle.com/learn"},
            ]},
            {"category": "Tools", "items": [
                {"name": "scikit-learn", "url": "https://scikit-learn.org"},
                {"name": "Jupyter Lab", "url": "https://jupyter.org"},
                {"name": "Weights & Biases", "url": "https://wandb.ai"},
            ]},
            {"category": "Datasets", "items": [
                {"name": "Kaggle Datasets", "url": "https://www.kaggle.com/datasets"},
                {"name": "UCI ML Repository", "url": "https://archive.ics.uci.edu/ml"},
                {"name": "Papers With Code", "url": "https://paperswithcode.com"},
            ]},
        ],
        "time_commitment": "10-12 hours per week for 6 weeks (total ~70 hours)",
        "execution_strategy": "Spend 60% of time on data quality and feature engineering, 20% on modeling, 20% on evaluation. Start simple with baseline models before trying complex algorithms. Track every experiment.",
    }


def _plan_marketing(goal: str) -> dict:
    return {
        "goal_summary": f"Comprehensive marketing strategy for: {goal}. Audience research, content creation, channel optimization, and measurement.",
        "assumptions": ["Product or service ready to market", "Modest advertising budget available", "Targeting a specific audience"],
        "timeline": [
            {
                "week": "Week 1", "title": "Strategy & Audience Research", "total_hours": 10,
                "topics": [
                    {"name": "Audience persona creation", "hours": 3, "resource": "HubSpot Persona Tool", "resource_url": "https://www.hubspot.com/make-my-persona", "description": "Create 2-3 detailed buyer personas with demographics, pain points, and preferred channels."},
                    {"name": "Competitive audit", "hours": 3, "resource": "SimilarWeb / SpyFu", "resource_url": "https://www.similarweb.com", "description": "Analyze competitor marketing channels, content strategy, ad spend, and messaging."},
                    {"name": "KPI definition", "hours": 2, "resource": "Analytics planning", "resource_url": "https://analytics.google.com", "description": "Define measurable goals: monthly reach, engagement rate, conversion rate, CAC."},
                    {"name": "Channel selection", "hours": 2, "resource": "Channel strategy guides", "resource_url": "https://buffer.com/resources", "description": "Select 2-3 primary channels based on where your audience spends time."},
                ],
                "milestone": "Clear audience personas, competitive insights, and channel strategy defined."
            },
            {
                "week": "Week 2-3", "title": "Content Creation & Launch", "total_hours": 18,
                "topics": [
                    {"name": "Content calendar", "hours": 3, "resource": "Notion / Trello", "resource_url": "https://notion.so", "description": "Plan 4-6 weeks of content with themes, formats, and publishing schedule."},
                    {"name": "Content production", "hours": 8, "resource": "Canva / CapCut", "resource_url": "https://www.canva.com", "description": "Create 15-20 content pieces: posts, graphics, short videos, blog articles."},
                    {"name": "Ad campaign setup", "hours": 4, "resource": "Meta/Google Ads", "resource_url": "https://ads.google.com", "description": "Create targeted campaigns with proper audience segments, budgets, and A/B tests."},
                    {"name": "Analytics setup", "hours": 3, "resource": "Google Analytics / UTMs", "resource_url": "https://analytics.google.com", "description": "Configure tracking pixels, UTM parameters, and performance dashboards."},
                ],
                "milestone": "Content published, ad campaigns live, and tracking fully configured."
            },
            {
                "week": "Week 4", "title": "Optimize & Scale", "total_hours": 8,
                "topics": [
                    {"name": "Performance analysis", "hours": 3, "resource": "Google Analytics", "resource_url": "https://analytics.google.com", "description": "Review metrics against KPIs, identify top performers and underperformers."},
                    {"name": "A/B testing", "hours": 3, "resource": "Ad platforms", "resource_url": "https://ads.google.com", "description": "Test headlines, visuals, CTAs, audiences. Scale winners, pause losers."},
                    {"name": "Monthly reporting", "hours": 2, "resource": "Google Data Studio", "resource_url": "https://lookerstudio.google.com", "description": "Create a reporting template for ongoing monthly performance reviews."},
                ],
                "milestone": "Data-driven optimizations applied, reporting cadence established."
            },
        ],
        "resources": [
            {"category": "Tools", "items": [
                {"name": "Canva", "url": "https://www.canva.com"},
                {"name": "Buffer", "url": "https://buffer.com"},
                {"name": "Google Analytics", "url": "https://analytics.google.com"},
            ]},
            {"category": "Advertising", "items": [
                {"name": "Google Ads", "url": "https://ads.google.com"},
                {"name": "Meta Business Suite", "url": "https://business.facebook.com"},
            ]},
        ],
        "time_commitment": "8-12 hours per week for 4 weeks (total ~45 hours)",
        "execution_strategy": "Build organic presence on 1-2 channels before paying for ads. Always test small before scaling. Create content in batches for efficiency.",
    }


def _plan_mobile(goal: str) -> dict:
    return {
        "goal_summary": f"Complete mobile app development roadmap: {goal}. Design, development, testing, and store submission.",
        "assumptions": ["Building for iOS and/or Android", "Basic programming knowledge", "App requires backend API"],
        "timeline": [
            {
                "week": "Week 1-2", "title": "Design & Architecture", "total_hours": 16,
                "topics": [
                    {"name": "Requirements & user flows", "hours": 4, "resource": "Miro / FigJam", "resource_url": "https://miro.com", "description": "Map every screen, user action, and navigation path. Define core vs nice-to-have features."},
                    {"name": "UI/UX design in Figma", "hours": 6, "resource": "Figma", "resource_url": "https://www.figma.com", "description": "Design all screens with platform-specific patterns (Material Design / iOS HIG)."},
                    {"name": "Tech stack decision", "hours": 2, "resource": "Framework comparison", "resource_url": "https://docs.flutter.dev", "description": "Choose between Flutter, React Native, or native. Set up development environment."},
                    {"name": "API & database design", "hours": 4, "resource": "Firebase / Supabase", "resource_url": "https://firebase.google.com", "description": "Plan data models, API endpoints, authentication, and real-time data needs."},
                ],
                "milestone": "Complete designs and architecture documentation ready for development."
            },
            {
                "week": "Week 3-6", "title": "Core Development", "total_hours": 48,
                "topics": [
                    {"name": "Project scaffolding & CI/CD", "hours": 4, "resource": "Official docs", "resource_url": "https://reactnative.dev", "description": "Initialize project, configure testing, linting, and automated build pipeline."},
                    {"name": "Core UI components", "hours": 16, "resource": "Component libraries", "resource_url": "https://callstack.github.io/react-native-paper/", "description": "Build all screens with navigation, state management, and reusable components."},
                    {"name": "Backend integration", "hours": 16, "resource": "Firebase / Supabase", "resource_url": "https://supabase.com", "description": "Connect to backend for auth, CRUD operations, real-time sync, and push notifications."},
                    {"name": "Offline support & caching", "hours": 4, "resource": "AsyncStorage / SQLite", "resource_url": "https://react-native-async-storage.github.io/async-storage/", "description": "Implement local storage, offline mode, and smart caching strategies."},
                    {"name": "Performance optimization", "hours": 8, "resource": "Performance guides", "resource_url": "https://reactnative.dev/docs/performance", "description": "Profile for memory leaks, optimize renders, reduce bundle size, test on low-end devices."},
                ],
                "milestone": "Fully functional app with backend integration, ready for testing."
            },
            {
                "week": "Week 7-8", "title": "Testing & Launch", "total_hours": 16,
                "topics": [
                    {"name": "QA & bug fixing", "hours": 6, "resource": "TestFlight / Internal Testing", "resource_url": "https://developer.apple.com/testflight/", "description": "Distribute to beta testers, run systematic QA, fix critical and high-priority bugs."},
                    {"name": "App store preparation", "hours": 4, "resource": "App Store Guidelines", "resource_url": "https://developer.apple.com/app-store/review/guidelines/", "description": "Create store listing, screenshots, app preview video, privacy policy, and metadata."},
                    {"name": "Submit for review", "hours": 2, "resource": "Play Console / App Store Connect", "resource_url": "https://play.google.com/console", "description": "Submit to App Store and/or Google Play. Address any review feedback promptly."},
                    {"name": "Launch marketing", "hours": 4, "resource": "Product Hunt / Social", "resource_url": "https://www.producthunt.com", "description": "Announce on social media, Product Hunt, relevant communities. Reach out to press/blogs."},
                ],
                "milestone": "App published on app stores with initial users and feedback loop established."
            },
        ],
        "resources": [
            {"category": "Frameworks", "items": [
                {"name": "Flutter", "url": "https://docs.flutter.dev"},
                {"name": "React Native", "url": "https://reactnative.dev"},
            ]},
            {"category": "Backend", "items": [
                {"name": "Firebase", "url": "https://firebase.google.com"},
                {"name": "Supabase", "url": "https://supabase.com"},
            ]},
            {"category": "Design", "items": [
                {"name": "Figma", "url": "https://www.figma.com"},
                {"name": "Material Design", "url": "https://material.io/design"},
            ]},
        ],
        "time_commitment": "15-20 hours per week for 8 weeks (total ~130 hours)",
        "execution_strategy": "Design everything before coding. Build core feature first, not all features. Ship an MVP to beta users ASAP. Iterate based on real user behavior, not assumptions.",
    }


def _plan_generic(goal: str) -> dict:
    return {
        "goal_summary": f"A comprehensive, phased plan to achieve: {goal}. Structured into research, execution, and review phases.",
        "assumptions": ["Starting with limited experience", "Moderate time and resources available", "Achievable within 4-8 weeks"],
        "timeline": [
            {
                "week": "Week 1-2", "title": "Research & Foundation", "total_hours": 14,
                "topics": [
                    {"name": "Deep-dive research", "hours": 4, "resource": "Google Scholar / YouTube", "resource_url": "https://scholar.google.com", "description": f"Research best practices, approaches, and common pitfalls for \"{goal}\"."},
                    {"name": "Define success criteria", "hours": 3, "resource": "Notion", "resource_url": "https://notion.so", "description": "Establish specific, measurable outcomes that define success."},
                    {"name": "Tool & resource setup", "hours": 3, "resource": "Varies", "resource_url": "#", "description": "Identify and set up all tools, accounts, and prerequisites."},
                    {"name": "Detailed milestone planning", "hours": 4, "resource": "Trello / Notion", "resource_url": "https://trello.com", "description": "Break the goal into weekly milestones with specific deliverables."},
                ],
                "milestone": "Clear understanding of the domain, tools ready, and milestones defined."
            },
            {
                "week": "Week 3-5", "title": "Core Execution", "total_hours": 24,
                "topics": [
                    {"name": "Primary deliverables", "hours": 12, "resource": "Domain-specific", "resource_url": "#", "description": "Work on the core tasks that directly move you toward the goal."},
                    {"name": "Progress tracking", "hours": 4, "resource": "Trello / GitHub", "resource_url": "https://trello.com", "description": "Compare actual progress with planned milestones, adjust as needed."},
                    {"name": "Feedback & iteration", "hours": 4, "resource": "Peer review", "resource_url": "#", "description": "Share work-in-progress, gather feedback, and incorporate improvements."},
                    {"name": "Documentation", "hours": 4, "resource": "Google Docs", "resource_url": "https://docs.google.com", "description": "Document decisions, challenges, solutions, and learnings."},
                ],
                "milestone": "Core deliverables completed and validated with feedback."
            },
            {
                "week": "Week 6-8", "title": "Polish & Completion", "total_hours": 14,
                "topics": [
                    {"name": "Quality review", "hours": 4, "resource": "Checklists", "resource_url": "#", "description": "Evaluate all work against original success criteria and quality standards."},
                    {"name": "Gap analysis & fixes", "hours": 4, "resource": "Self-review", "resource_url": "#", "description": "Identify anything missed, handle edge cases and remaining details."},
                    {"name": "Final documentation", "hours": 3, "resource": "Google Docs / Notion", "resource_url": "https://docs.google.com", "description": "Compile comprehensive documentation of process and outcomes."},
                    {"name": "Sustainability plan", "hours": 3, "resource": "Planning tools", "resource_url": "https://notion.so", "description": "Create maintenance plan and next steps for continued progress."},
                ],
                "milestone": "Goal achieved with complete documentation and sustainability plan."
            },
        ],
        "resources": [
            {"category": "Productivity", "items": [
                {"name": "Notion", "url": "https://notion.so"},
                {"name": "Trello", "url": "https://trello.com"},
                {"name": "Google Docs", "url": "https://docs.google.com"},
            ]},
            {"category": "Learning", "items": [
                {"name": "YouTube", "url": "https://youtube.com"},
                {"name": "Medium", "url": "https://medium.com"},
                {"name": "Reddit", "url": "https://reddit.com"},
            ]},
        ],
        "time_commitment": "8-12 hours per week for 6-8 weeks (total ~60-80 hours)",
        "execution_strategy": f"Start with thorough research before executing. Break \"{goal}\" into the smallest milestones. Focus on one thing at a time, review regularly, and adjust as you learn.",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_goal(prompt: str) -> str:
    match = re.search(r'Goal:\s*"(.+?)"', prompt)
    if match: return match.group(1).strip()
    match = re.search(r'goal:\s*\n\s*"(.+?)"', prompt, re.IGNORECASE)
    if match: return match.group(1).strip()
    match = re.search(r'Goal:\s*(.+)', prompt)
    if match: return match.group(1).strip().strip('"').strip("'")
    match = re.search(r'goal[:\s]*"([^"]+)"', prompt, re.IGNORECASE)
    if match: return match.group(1).strip()
    return "the given goal"
