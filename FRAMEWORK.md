# Nova Apply - Framework Architecture

## Core Components

### 1. Profile Manager (`/profiles/`)
- JSON/YAML profiles per candidate
- Fields: name, email, phone, resume path, skills[], experience, preferences
- Target roles, industries, locations (USA), salary expectations
- Visa status: "Willing to relocate anywhere USA" (no visa sponsorship focus)

### 2. Job Discovery Engine (`/discovery/`)
- Portal adapters for each job board (LinkedIn, Indeed, Glassdoor, Monster, SimplyHired, HiringCafe, JobRight.ai)
- Search params: Past 24 hours, USA only, role keywords
- Rate limiting: 5 searches/batch, 2 min breaks
- Proxy rotation (placeholder for now)

### 3. Semantic Matcher (`/matcher/`)
- LLM-based job-to-candidate matching
- Scoring: High / Medium / Low (apply only to High/Medium)
- Better than keywords — understands skill relevance
- Kimi API for judgment calls

### 4. Application Engine (`/applier/`)
- Browser automation (Playwright/Selenium)
- Auto-fill forms with profile data
- Cover letter generation (custom per application)
- Human-like delays: 10s between portal actions
- Anti-detection: mouse movement, typing simulation

### 5. Tracking & Reporting (`/tracker/`)
- Gmail integration: Monitor for "Application submitted" / "Thank you" confirmations
- SQLite/JSON database of applications sent
- Daily WhatsApp report generator
- Blocker logging for manual intervention

### 6. Orchestrator (`/orchestrator/`)
- Main scheduler for daily runs
- Profile rotation logic
- Rate limit enforcement
- Error handling & retries

## Directory Structure

```
nova-apply/
├── config/
│   ├── settings.json          # API keys, rate limits, thresholds
│   └── profiles.json          # List of active profiles
├── profiles/
│   ├── profile_01.json        # Individual candidate profiles
│   ├── profile_02.json
│   └── ...
├── discovery/
│   ├── base.py                # Base portal adapter
│   ├── linkedin.py
│   ├── indeed.py
│   ├── glassdoor.py
│   ├── monster.py
│   ├── simplyhired.py
│   ├── hiringcafe.py
│   └── jobright.py
├── matcher/
│   ├── semantic_matcher.py    # LLM-based matching logic
│   └── prompts/               # Matching prompts
├── applier/
│   ├── browser.py             # Browser automation core
│   ├── form_filler.py         # Form auto-fill logic
│   └── cover_letter.py        # CL generation
├── tracker/
│   ├── gmail_monitor.py       # Email monitoring
│   ├── database.py            # Application tracking DB
│   └── reporter.py            # WhatsApp report generator
├── orchestrator/
│   └── scheduler.py           # Main orchestration logic
├── utils/
│   ├── rate_limiter.py        # Rate limiting enforcement
│   ├── logger.py              # Logging utilities
│   └── helpers.py             # Common utilities
├── tests/
│   └── ...
├── memory/
│   └── applications.db        # SQLite DB
└── run.py                     # Entry point
```

## Tech Stack

- **Language:** Python 3.11+
- **Browser:** Playwright (stealth mode)
- **LLM:** Kimi API (kimi-k2.5)
- **DB:** SQLite (applications tracking)
- **Messaging:** WhatsApp (already connected via gateway)
- **Monitoring:** Gmail API or IMAP for email tracking

## Rate Limits (HARD RULES)

```python
API_CALL_DELAY = 5  # seconds between API calls
PORTAL_ACTION_DELAY = 10  # seconds between portal actions
MAX_SEARCHES_PER_BATCH = 5
SEARCH_BATCH_BREAK = 120  # 2 minutes
MAX_APPLICATIONS_PER_PROFILE_PER_DAY = 30
```

## Phase 1: Build Order (This Week)

1. **Day 1-2:** Skeleton + Profile Manager
2. **Day 3-4:** Discovery Engine (1-2 portals first)
3. **Day 5-6:** Semantic Matcher
4. **Day 7:** Application Engine (basic form fill)

## Phase 2: Integration & Testing (Weeks 2-3)

- Wire components together
- Test with 1-2 dummy profiles
- Tune matching thresholds
- Gmail monitoring
- Daily reporting

## Phase 3: Scale (Week 4+)

- All 7 portals
- 6-10 test profiles
- Full stealth mode with proxies

---

Ready to start building, Twin. What's the first component you want to tackle?
