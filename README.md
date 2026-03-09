# Nova Apply 🚀

**Fully automated job application agency for USA roles.**

Built by Nova (AI) & Dhruv (Twin) — co-founders in the trenches.

---

## Mission

- **180-350 applications/day** across 6-10 candidate profiles
- **25-30 apps/profile/day** (safety cap: NEVER exceed 30)
- **7 portals:** LinkedIn, Indeed, Glassdoor, Monster, SimplyHired, HiringCafe, JobRight.ai
- **Semantic matching:** LLM-powered high/medium fit detection
- **Stealth mode:** Human-like delays, anti-ban protocols
- **Daily reports:** WhatsApp updates on applications, confirmations, blockers

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Create a test profile
python -c "from utils.profile_manager import ProfileManager; pm = ProfileManager(); print('OK')"

# 5. Check system status
python run.py status

# 6. Run for single profile (test mode)
python run.py profile --profile test_profile --max 2

# 7. Run daily pipeline
python run.py daily

# 8. Generate report
python run.py report
```

---

## Directory Structure

```
nova-apply/
├── config/
│   ├── settings.json          # App configuration
│   └── profiles.json          # Active profiles list
├── profiles/
│   ├── template_profile.json  # Profile template
│   └── *.json                 # Candidate profiles
├── discovery/                 # Job portal adapters
├── matcher/                   # Semantic matching
├── applier/                   # Browser automation
├── tracker/                   # Gmail + SQLite tracking
├── orchestrator/              # Main scheduler
├── utils/                     # Shared utilities
├── memory/                    # SQLite DB + logs
├── run.py                     # Entry point
└── requirements.txt
```

---

## Core Principles

1. **Rate limits are LAW**
   - 5s between API calls
   - 10s between portal actions
   - Max 5 searches/batch, then 2min break
   - Max 30 applications/profile/day

2. **Cost control is ruthless**
   - Kimi API (kimi-k2.5) as primary
   - Gemini Flash as fallback only
   - Ollama for heartbeat/local tasks

3. **Stealth first**
   - Human-like mouse/typing simulation
   - Randomized delays
   - Proxy rotation (Phase 2)
   - CapSolver integration (Phase 2)

4. **Track everything**
   - Every application logged to SQLite
   - Gmail monitored for confirmations
   - Daily WhatsApp reports
   - Session-end memory updates

---

## Phase Roadmap

### Phase 1: Foundation (Week 1-2)
- ✅ Skeleton + config
- ⏳ Portal adapters (LinkedIn, Indeed first)
- ⏳ Semantic matcher integration
- ⏳ Basic browser automation

### Phase 2: Integration (Week 3-4)
- ⏳ Wire all components
- ⏳ Gmail monitoring
- ⏳ WhatsApp reporting
- ⏳ Testing with 1-2 profiles

### Phase 3: Scale (Week 5+)
- ⏳ All 7 portals
- ⏳ 6-10 test profiles
- ⏳ Full stealth (proxies, CAPTCHA)
- ⏳ Client onboarding

---

## Session Rules (LOCKED)

On EVERY session start:
1. Load SOUL.md
2. Load USER.md
3. Load IDENTITY.md
4. Load memory/YYYY-MM-DD.md (today only)
5. **DO NOT** auto-load full MEMORY.md or history
6. Use memory_search/get on demand only

At session end:
- Update memory/YYYY-MM-DD.md with work done
- Applications applied, thank-yous counted
- Blockers, next steps

---

## Commands

```bash
# System status
python run.py status

# Single profile run
python run.py profile -p <profile_id> -m <max_apps>

# Daily run (all active profiles)
python run.py daily

# Generate + send report
python run.py report
```

---

## Twin Commands

- `python run.py status` — Check system health
- `python run.py profile -p <id> -m 2` — Test run with 2 apps
- `python run.py daily` — Full daily pipeline
- `python run.py report` — WhatsApp daily report

---

*Built with 💥 by Nova & Dhruv*
