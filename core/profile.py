"""Student profile: stores what we learn about the student during the chat."""

# key -> (label shown in sidebar, is_list)
FIELDS = {
    "name": ("Name", False),
    "degree": ("Degree", False),
    "branch": ("Branch/Major", False),
    "year_or_semester": ("Year/Semester", False),
    "cgpa_or_percentage": ("CGPA/Percentage", False),
    "graduation_year": ("Graduation Year", False),
    "subjects": ("Important Subjects", True),
    "skills": ("Skills", True),
    "interests": ("Interests", True),
    "career_goal": ("Career Goal", False),
    "industry_preference": ("Industry Preference", False),
    "research_or_industry": ("Research / Industry", False),
    "location_preference": ("India / Abroad", False),
    "preferred_country": ("Preferred Country", False),
    "budget": ("Budget", False),
    "study_mode": ("Full-time / Part-time", False),
    "duration": ("Duration", False),
}

# Sidebar sections
SECTIONS = {
    "🎓 Academic Background": ["name", "degree", "branch", "year_or_semester", "cgpa_or_percentage", "graduation_year", "subjects"],
    "💻 Skills": ["skills"],
    "❤️ Interests": ["interests"],
    "🎯 Career Goal": ["career_goal", "industry_preference", "research_or_industry"],
    "🌍 Study Preference": ["location_preference", "preferred_country", "budget", "study_mode", "duration"],
}

_EMPTY = {"", "null", "none", "unknown", "not provided", "n/a"}


def new_profile():
    return {k: ([] if is_list else None) for k, (_, is_list) in FIELDS.items()}


def _clean(v):
    if v is None:
        return None
    v = str(v).strip()
    return None if v.lower() in _EMPTY else v


def merge_profile(current, extracted):
    """Merge newly extracted facts into the profile.
    Newer non-empty values overwrite scalars; list items are added without duplicates."""
    for key, (_, is_list) in FIELDS.items():
        new = extracted.get(key)
        if is_list:
            items = new if isinstance(new, list) else []
            for item in items:
                item = _clean(item)
                if item and item.lower() not in [x.lower() for x in current[key]]:
                    current[key].append(item)
        else:
            val = _clean(new)
            if val:
                current[key] = val
    return current


def profile_to_text(profile):
    """Turn the profile into text that is given to the AI as context."""
    lines = []
    for key, (label, is_list) in FIELDS.items():
        v = profile[key]
        if (is_list and v) or (not is_list and v):
            lines.append(f"- {label}: {', '.join(v) if is_list else v}")
    return "\n".join(lines) if lines else "(nothing known yet)"
