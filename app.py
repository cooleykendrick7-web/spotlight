"""
Spotlight — Ken's acting-only board.
Like ClaimBoard / Workspace, but NOTHING but acting jobs:
  beginner + intermediate level ONLY (Ken's order 2026-11-03).
Lanes: film & TV, background/extra, commercials, vertical drama,
voiceover, indie & student film (reps).
Two kinds of entries:
  role     = a specific casting call Ken can be submitted to
  platform = a casting door/profile to create once, then it feeds roles
Workflow (Ken's Workspace rule): Ken taps APPROVE — MILLI APPLIES FOR ME,
Milli does the actual submission and writes back what happened in apply_note.
Hard stops (never faked past): paid subscriptions, passwords/codes (Ken's
hands), ID/tax/payment forms, self-tape RECORDING (Ken performs — Milli
can prep sides, reminders and upload once Ken records), contracts/signatures.
Admin/operator have NO password by Ken's standing board order.
Pay is what listings/platforms publish — never a guarantee.
Legit casting NEVER charges an upfront fee to audition.
"""
import os, datetime, sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).parent
DB_PATH = os.environ.get("SPOTLIGHT_DB", str(BASE / "spotlight.db"))

app = FastAPI(title="Spotlight", version="1.0.0")

CATEGORIES = ("film_tv", "background", "commercial", "vertical", "voiceover", "indie")
LEVELS = ("beginner", "intermediate")
STATUSES = ("found", "saved", "applied", "audition", "callback", "booked", "paid", "passed")
SIGNUP_STATES = ("not_started", "queued", "started", "done", "needs_ken")
KINDS = ("role", "platform")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# slug, title, category, platform, level, kind, pay_label, pay_low, pay_high, url, location, deadline, requirements, note
SEED = [
    # ---------- SPECIFIC ROLES — CLOSEST / BEST FIT FIRST ----------
    ("cupid-bar-patrons", "CUPID — background: Bywater Bar Patrons (feature film, Catherine Zeta-Jones)", "background", "Caballero Casting via Project Casting", "beginner", "role",
     "Background day rate — listed on Project Casting (verify at submission)", 100, 200,
     "https://projectcasting.com/jobs?location=mississippi", "Natchez, Mississippi — films Fri Nov 13, 2026",
     "2026-11-10", "Background talent, able to work in Natchez, MS on Nov 13. No experience needed for background.",
     "TOP PICK — in Mississippi. Tate Taylor feature filming in Natchez Oct 26–Nov 20. Bar-patron background is the classic beginner first credit. Milli verifies the live listing + submission route before applying."),
    ("cupid-standin-nick", "CUPID — male stand-in for 'Nick' (feature film)", "film_tv", "Caballero Casting via Project Casting", "intermediate", "role",
     "Stand-in day rate — listed on Project Casting (stand-ins ~$270/day SAG scale ref)", 182, 270,
     "https://projectcasting.com/jobs?location=mississippi", "Natchez, Mississippi — Oct 26–Nov 20, 2026, Mon–Fri",
     "2026-11-08", "Male stand-in for NICK. Stand-ins must match the actor's height/build/skin tone — Ken's height + measurements needed before Milli can submit honestly.",
     "In Mississippi and pays better than background. BLOCKER: needs Ken's height/weight/sizes (in the Actor Kit) — stand-in casting is a physical match game."),
    ("car-safety-commercial-nola", "$800/day Car Safety commercial — sing in a car, no pro singing needed", "commercial", "Alyson Horn Casting via Project Casting", "beginner", "role",
     "$800 per shoot day + $5,000–$10,000 if you make the final cut", 800, 10000,
     "https://projectcasting.com/job/10000-car-safety-ad-council-commercial-casting-call", "New Orleans, Louisiana — 1 shoot day",
     "", "Men & women 16–70, local to New Orleans area, comfortable singing a heartfelt song in a car. Professional singing experience NOT required.",
     "Published Nov 3, 2026 — fresh. Beginner-perfect commercial money if the New Orleans trip works. Milli checks the exact submit route live before applying."),
    ("the-jane-atlanta", "THE JANE — indie feature open call, actors 18+ all looks", "indie", "AllCasting #322710", "beginner", "role",
     "Pay not stated on listing — ask before booking", 0, 0,
     "https://allcasting.com/castingcall/322710", "Atlanta, GA — local talent",
     "2026-11-06", "Actors/actresses 18+, all looks. Open call, no breakdown on the listing.",
     "URGENT — listing expires Nov 6, 2026. 'Hustle. Betrayal. Loyalty.' Email submission per the listing. Milli submits Ken's package (headshot + intro) the same day he approves."),
    ("body-snatchers-tubi", "Body Snatchers (Tubi film) — open audition, 15+ roles, paid", "film_tv", "Destination Casting", "beginner", "role",
     "Paid — rates per role on the casting notice", 100, 500,
     "https://projectcasting.com/jobs?search=Casting+call", "Open audition Nov 7 in Stonecrest, GA — films Dec in Atlanta + DC",
     "2026-11-07", "Open audition, 15+ roles. Bring headshot/intro; follow Destination Casting notice for exact time/place.",
     "Open-audition format is beginner gold — no agent, no pre-screen. In-person in Georgia, so it's a trip decision for Ken."),
    ("generational-curses-atlanta", "Generational Curses (TV series) — bank manager, tellers, neighbors", "film_tv", "Nspire Media Group", "intermediate", "role",
     "Paid day-player / extra rates per role", 150, 375,
     "https://www.thekhaliseum.com", "Atlanta, GA",
     "", "Day players + extras for a TV series. Bank Manager role fits a man in his 30s who can look professional and carry a short scene.",
     "The Bank Manager day-player is exactly Ken's intermediate lane: one scene, real lines, real credit. Milli pulls the current submission details before applying."),
    ("kountry-wayne-skits", "Kountry Wayne skits — ongoing short-form soap, improv-heavy", "film_tv", "Kountry Wayne production (Atlanta)", "intermediate", "role",
     "Paid per skit/day — varies by role", 100, 400,
     "https://atlantafi.com/atlanta-casting-calls-see-what-movies-tv-shows-are-hiring/", "Atlanta, GA — ongoing",
     "", "Ongoing casting for an improv-driven online soap/skit series. Comfortable improvising and playing a character across many episodes.",
     "Huge audience and recurring work — this is how a lot of Southern actors get seen. Improv = intermediate: no script safety net, but no agent needed either."),
    ("vertical-ceo-love-interest", "Vertical drama — 'The CEO Love Interest' lead type, male 25–35", "vertical", "Vertical Casting Calls (ReelShort/DramaBox lane)", "intermediate", "role",
     "$1,000–$1,500/day for leads", 1000, 1500,
     "https://www.verticalcastingcalls.com", "Shoots nationwide (LA/Atlanta/Texas hubs) — self-tape from anywhere",
     "", "Male 25–35, intense screen presence, comfortable with romance scenes. Self-tape audition. Series shoots 7–10 days total.",
     "The single most in-demand vertical archetype right now, and Ken is dead-center in the age range. One booking can pay $7k–$15k for ~10 days. Free alerts — no membership fee."),
    ("reelshort-return-of-reaper", "ReelShort 'Return of the Reaper' — day players, male 30–39 roles at $250/day", "vertical", "AllCasting / ReelShort production", "intermediate", "role",
     "$120–$350/day by role + lunch (supporting lackey roles listed $250/12hr)", 120, 350,
     "https://allcasting.com/castingcall/298526", "San Antonio, TX — local talent only per listing",
     "", "Male 30–39 supporting/day-player roles. Stage combat a plus, NOT required. Comfortable with stage blood / SFX makeup.",
     "Listed as local-only San Antonio — kept on the board as the pattern of what ReelShort pays Ken's exact age bracket; Milli only submits if a remote/self-tape or travel exception opens. Honest fit note, not a blind apply."),
    ("backstage-telehealth-ugc", "Backstage — telehealth UGC acting spots (self-tape, nationwide)", "commercial", "Backstage", "beginner", "role",
     "$750 / 8 hrs listed", 750, 750,
     "https://www.backstage.com/casting", "Remote — self-tape from home, nationwide",
     "", "On-camera UGC-style acting for health brand ads (GLP-1 / ED brands — Ken's call on brand comfort). Phone camera is fine.",
     "Carried over from Ken's Workspace board (found there Nov 1). Acting work you can do from the house — but it's medication advertising, so Ken decides if he wants his face on it."),
    ("backstage-voiceover-freddy", "Backstage — voiceover role, male voice 18–30", "voiceover", "Backstage", "beginner", "role",
     "$300 / 4 hrs listed", 300, 300,
     "https://www.backstage.com/casting", "Remote — record from home",
     "", "Male voice, reads 18–30. Phone mic can start; a quiet room matters more than gear.",
     "Carried over from the Workspace board. NOTE: Ken turns 31 on Nov 11, 2026 — voice reads younger than face age, but Milli flags the age line honestly on submission."),
    ("backstage-cuts-youtube", "Backstage — YouTube acting spot, single man 18–36", "commercial", "Backstage", "beginner", "role",
     "$200 / 1 hr listed", 200, 200,
     "https://www.backstage.com/casting", "Shoot location not stated on listing — verify before applying",
     "", "Single man, 18–36. Short shoot, beginner-friendly.",
     "Carried over from the Workspace board. Fast, small, paid on-camera rep — the kind of credit that builds the reel."),

    # ---------- CASTING PLATFORMS — THE DOORS (create profile once) ----------
    ("backstage", "Backstage — the #1 beginner front door (film, TV, commercial, VO, background)", "film_tv", "Backstage", "beginner", "platform",
     "Jobs up to SAG scale $1,246/day · background $100–$300/day", 100, 1246,
     "https://www.backstage.com/casting", "Nationwide + remote self-tapes",
     "", "Browse free; subscription (~$20/mo) to apply — PAID step is Ken's hands only. No agent needed.",
     "Start here. Biggest volume for actors without an agent: indie, student, commercial, background, voiceover. Milli builds the profile from the Actor Kit; Ken only steps in at the paywall if he chooses it."),
    ("actors-access", "Actors Access — where real film & TV breakdowns live", "film_tv", "Actors Access (Breakdown Services)", "intermediate", "platform",
     "Project pay varies — SAG scale and up", 200, 1246,
     "https://actorsaccess.com", "Nationwide — Eco Cast self-tapes from anywhere",
     "", "FREE profile; ~$2 per submission or $68/yr unlimited. Headshot + resume needed.",
     "The industry standard for episodic TV and features — over 97% of scripted breakdowns run through its parent. Free to join, so this is a first-week door."),
    ("central-casting", "Central Casting — background/extra work, FREE, New Orleans + Atlanta offices", "background", "Central Casting", "beginner", "platform",
     "$100–$200/day non-union · $231/day SAG background (2026)", 100, 231,
     "https://www.centralcasting.com", "New Orleans, LA + Atlanta, GA hubs (also LA/NYC)",
     "", "FREE registration — never pay. Everyday phone photos OK. I-9 documents at signup (Ken's hands for ID step).",
     "The gold standard for extras since 1925 and the closest big door to Mississippi (New Orleans covers LA+MS). Three union background days can earn SAG eligibility later."),
    ("project-casting", "Project Casting — free casting board, strongest in the Southeast", "film_tv", "Project Casting", "beginner", "platform",
     "Varies per call — many paid background + day-player gigs", 100, 1000,
     "https://projectcasting.com", "Nationwide, strong Southeast / Atlanta / Mississippi coverage",
     "", "Free to browse + free tier to apply (1 free application/day). Verify each listing — aggregator quality varies.",
     "Where the Mississippi CUPID calls surfaced. Best free daily sweep source for Ken's region — Milli's daily check starts here."),
    ("mycastingfile", "MyCastingFile — paid movie & TV extra roles near you, FREE", "background", "MyCastingFile", "beginner", "platform",
     "Pay shown per call — production pays you direct", 100, 300,
     "https://mycastingfile.com", "By location — open calls near you",
     "", "FREE to join & apply, 2 photos, no experience needed. Ken's account was CREATED Nov 1, 2026 — profile still needs an emergency contact (Ken provides a name + phone).",
     "Account already exists from the Workspace run. 116,000+ days on set booked through it since 2020. One Ken-only blocker: the emergency contact."),
    ("casting-networks", "Casting Networks — the commercials platform", "commercial", "Casting Networks", "intermediate", "platform",
     "Commercial pay often $500+/day + usage", 200, 2000,
     "https://www.castingnetworks.com", "Nationwide — also runs a Vertical Shorts board (176 active roles, Nov 2026)",
     "", "~$29.99/mo subscription — PAID step is Ken's call. Dominant platform for ad casting offices.",
     "Add this when commercial work becomes the focus. Also a real vertical-drama door. Milli does NOT start a paid plan without Ken's fresh go."),
    ("allcasting", "AllCasting — free-to-browse film, TV & vertical calls (ReelShort posts here)", "vertical", "AllCasting", "beginner", "platform",
     "Varies per call — vertical day rates $120–$500+ seen", 120, 1000,
     "https://allcasting.com", "Nationwide + online auditions",
     "", "Free account to apply. Filter by age/ethnicity/location; many verticals cast here first.",
     "Where ReelShort productions post publicly. Good beginner volume and the vertical lane lives here."),
    ("mandy", "Mandy Network — film/TV/VO jobs board (Backstage's sister site)", "voiceover", "Mandy Network", "beginner", "platform",
     "Varies widely — VO jobs seen $85–$2,500", 85, 2500,
     "https://www.mandy.com", "Nationwide + remote VO from home",
     "", "Free profile to browse; ~$7.95/mo to apply — paid step is Ken's call.",
     "Strong for voiceover and indie work at every level. Lots of remote VO a beginner can record at home."),
    ("vertical-casting-calls", "Vertical Casting Calls — free alerts for ReelShort / DramaBox / ShortMax roles", "vertical", "Vertical Casting Calls", "beginner", "platform",
     "Leads $1,000–$1,500/day · supporting $250–$500 · extras $150–$200/day", 150, 1500,
     "https://www.verticalcastingcalls.com", "Shoots nationwide — self-tape from anywhere",
     "", "Free alerts, no membership fee.",
     "The hidden fast lane: 400+ vertical series a year, 7–10 day shoots, thousands of paid roles most actors never see. Sign-up is free — first queue item."),
    ("casting-frontier", "Casting Frontier — commercials + film/TV with virtual auditions", "commercial", "Casting Frontier", "beginner", "platform",
     "Varies per call", 100, 1000,
     "https://www.castingfrontier.com", "Nationwide — virtual auditions",
     "", "Free basic plan with limited submissions; Premium from $14.99/mo (Ken's call).",
     "One more legitimate door, especially commercials. Free tier is enough to start."),
]

def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs(
      slug TEXT PRIMARY KEY, title TEXT, category TEXT, platform TEXT,
      level TEXT, kind TEXT, pay_label TEXT, pay_low REAL, pay_high REAL,
      url TEXT, location TEXT, deadline TEXT, requirements TEXT, note TEXT,
      status TEXT DEFAULT 'found', paid_amount REAL DEFAULT 0,
      signup_state TEXT DEFAULT 'not_started',
      apply_approved INTEGER DEFAULT 0, apply_note TEXT DEFAULT '',
      updated_at TEXT)""")
    for row in SEED:
        c.execute("""INSERT OR IGNORE INTO jobs(slug,title,category,platform,level,kind,pay_label,pay_low,pay_high,url,location,deadline,requirements,note,status,updated_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'found', ?)""",
                  (*row, datetime.datetime.utcnow().isoformat()))
    c.commit(); c.close()
init_db()

@app.middleware("http")
async def headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp

@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "spotlight", "version": "1.0.0"}

@app.get("/api/notify")
async def api_notify(t: str = "", title: str = "Spotlight", msg: str = ""):
    """Fire a push to Ken's ntfy topic. Server-side on purpose: Render can
    reach ntfy.sh, the agent VM's egress proxy cannot. Token-guarded by the
    SPOTLIGHT_NOTIFY_TOKEN env var (fail-closed when unset). Added 2026-11-07
    on Ken's order: Spotlight notifications on ntfy."""
    import hmac, urllib.request, urllib.parse
    token = os.environ.get("SPOTLIGHT_NOTIFY_TOKEN", "")
    if not token:
        raise HTTPException(503, "Notify not configured.")
    if not hmac.compare_digest(t, token):
        raise HTTPException(403, "Bad token.")
    topic = os.environ.get("NTFY_TOPIC", "Ntfy1")
    safe_title = (title or "Spotlight")[:120].encode("ascii", "replace").decode()
    req = urllib.request.Request(
        "https://ntfy.sh/" + urllib.parse.quote(topic),
        data=(msg or "")[:1500].encode("utf-8", "replace"), method="POST",
        headers={"Title": safe_title, "Tags": "clapper",
                 "Click": "https://spotlight-1fgj.onrender.com/"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            ok = 200 <= r.status < 300
    except Exception:
        ok = False
    return {"ok": ok, "topic": topic}

@app.get("/api/jobs")
async def api_list(category: str | None = None, level: str | None = None, kind: str | None = None):
    c = db()
    q = "SELECT * FROM jobs WHERE 1=1"; args = []
    if category and category in CATEGORIES:
        q += " AND category=?"; args.append(category)
    if level and level in LEVELS:
        q += " AND level=?"; args.append(level)
    if kind and kind in KINDS:
        q += " AND kind=?"; args.append(kind)
    q += " ORDER BY deadline ASC, pay_high DESC"
    rows = c.execute(q, args).fetchall(); c.close()
    return [dict(r) for r in rows]

@app.get("/api/summary")
async def api_summary():
    c = db(); rows = c.execute("SELECT * FROM jobs").fetchall(); c.close()
    paid = sum((r["paid_amount"] or 0) for r in rows if r["status"] == "paid")
    by_cat = {cat: sum(1 for r in rows if r["category"] == cat) for cat in CATEGORIES}
    by_level = {lv: sum(1 for r in rows if r["level"] == lv) for lv in LEVELS}
    by_status = {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}
    active = [r for r in rows if r["status"] in ("saved", "applied", "audition", "callback", "booked")]
    return {
        "paid_total": round(paid, 2),
        "total": len(rows),
        "roles": sum(1 for r in rows if r["kind"] == "role"),
        "platforms": sum(1 for r in rows if r["kind"] == "platform"),
        "by_category": by_cat, "by_level": by_level, "counts": by_status,
        "active_count": len(active),
        "active_potential_low": round(sum((r["pay_low"] or 0) for r in active), 2),
        "active_potential_high": round(sum((r["pay_high"] or 0) for r in active), 2),
        "all_potential_high": round(sum((r["pay_high"] or 0) for r in rows if r["status"] != "passed"), 2),
        "updated": datetime.datetime.utcnow().isoformat(),
    }

class StatusIn(BaseModel):
    status: str

@app.patch("/api/jobs/{slug}")
async def api_set_status(slug: str, body: StatusIn):
    if body.status not in STATUSES:
        raise HTTPException(400, "Invalid status.")
    c = db()
    cur = c.execute("UPDATE jobs SET status=?, updated_at=? WHERE slug=?",
                    (body.status, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug, "status": body.status}

class JobIn(BaseModel):
    slug: str; title: str; category: str = "film_tv"; platform: str = ""
    level: str = "beginner"; kind: str = "role"
    pay_label: str = ""; pay_low: float | None = None; pay_high: float | None = None
    url: str = ""; location: str = ""; deadline: str = ""
    requirements: str = ""; note: str = ""; status: str = "found"

@app.post("/api/admin/jobs")
async def api_upsert(body: JobIn):
    if body.category not in CATEGORIES: raise HTTPException(400, "Invalid category.")
    if body.level not in LEVELS: raise HTTPException(400, "Invalid level — beginner/intermediate only.")
    if body.kind not in KINDS: raise HTTPException(400, "Invalid kind.")
    if body.status not in STATUSES: raise HTTPException(400, "Invalid status.")
    c = db()
    c.execute("""INSERT INTO jobs(slug,title,category,platform,level,kind,pay_label,pay_low,pay_high,url,location,deadline,requirements,note,status,updated_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(slug) DO UPDATE SET title=excluded.title, category=excluded.category, platform=excluded.platform,
      level=excluded.level, kind=excluded.kind, pay_label=excluded.pay_label, pay_low=excluded.pay_low, pay_high=excluded.pay_high,
      url=excluded.url, location=excluded.location, deadline=excluded.deadline, requirements=excluded.requirements,
      note=excluded.note, updated_at=excluded.updated_at""",
      (body.slug, body.title, body.category, body.platform, body.level, body.kind, body.pay_label, body.pay_low, body.pay_high,
       body.url, body.location, body.deadline, body.requirements, body.note, body.status, datetime.datetime.utcnow().isoformat()))
    c.commit(); c.close()
    return {"ok": True, "slug": body.slug}

class PaidIn(BaseModel):
    amount: float

@app.post("/api/admin/jobs/{slug}/paid")
async def api_paid(slug: str, body: PaidIn):
    c = db()
    cur = c.execute("UPDATE jobs SET status='paid', paid_amount=?, updated_at=? WHERE slug=?",
                    (body.amount, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True}

@app.delete("/api/admin/jobs/{slug}")
async def api_delete(slug: str):
    c = db()
    cur = c.execute("DELETE FROM jobs WHERE slug=?", (slug,))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True}

class SignupIn(BaseModel):
    signup_state: str

@app.patch("/api/jobs/{slug}/signup")
async def api_set_signup(slug: str, body: SignupIn):
    if body.signup_state not in SIGNUP_STATES:
        raise HTTPException(400, "Invalid signup_state.")
    c = db()
    cur = c.execute("UPDATE jobs SET signup_state=?, updated_at=? WHERE slug=?",
                    (body.signup_state, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug, "signup_state": body.signup_state}

class ApproveIn(BaseModel):
    approved: bool

@app.patch("/api/jobs/{slug}/approve")
async def api_set_approve(slug: str, body: ApproveIn):
    c = db()
    cur = c.execute("UPDATE jobs SET apply_approved=?, updated_at=? WHERE slug=?",
                    (1 if body.approved else 0, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug, "apply_approved": body.approved}

class ApplyNoteIn(BaseModel):
    note: str

@app.patch("/api/jobs/{slug}/apply-note")
async def api_set_apply_note(slug: str, body: ApplyNoteIn):
    c = db()
    cur = c.execute("UPDATE jobs SET apply_note=?, updated_at=? WHERE slug=?",
                    (body.note[:600], datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug}

@app.get("/api/operator/summary")
async def api_operator_summary():
    c = db(); rows = c.execute("SELECT * FROM jobs").fetchall(); c.close()
    paid = sum((r["paid_amount"] or 0) for r in rows if r["status"] == "paid")
    def cnt(key, val): return sum(1 for r in rows if r[key] == val)
    approved = [dict(r) for r in rows if (r["apply_approved"] or 0) == 1]
    needs_ken = [dict(r) for r in rows if (r["signup_state"] or "") == "needs_ken"]
    return {
        "service": "spotlight", "version": "1.0.0",
        "total": len(rows),
        "roles": sum(1 for r in rows if r["kind"] == "role"),
        "platforms": sum(1 for r in rows if r["kind"] == "platform"),
        "by_category": {cat: cnt("category", cat) for cat in CATEGORIES},
        "by_level": {lv: cnt("level", lv) for lv in LEVELS},
        "by_status": {s: cnt("status", s) for s in STATUSES},
        "by_signup": {s: cnt("signup_state", s) for s in SIGNUP_STATES},
        "paid_total": round(paid, 2),
        "approved_to_apply": [{"slug": r["slug"], "platform": r["platform"], "title": r["title"],
                               "category": r["category"], "level": r["level"], "kind": r["kind"],
                               "status": r["status"], "signup_state": r["signup_state"] or "not_started",
                               "deadline": r["deadline"] or "", "apply_note": r["apply_note"] or ""} for r in approved],
        "approved_count": len(approved),
        "needs_ken": [{"slug": r["slug"], "platform": r["platform"], "note": r["note"]} for r in needs_ken],
        "next_actions": [
            "APPLY QUEUE: when Ken taps Approve, Milli submits him — profile, headshot, intro/self-tape link and cover note she can write from his Actor Kit. She verifies the listing is still live first; expired or changed listings get noted, never blind-applied.",
            "HARD STOPS: paid subscriptions (Backstage/Casting Networks/Mandy paywalls), passwords & verification codes, ID/tax/payment forms, signing contracts, and RECORDING a self-tape — Ken performs; Milli preps the sides, the deadline and the upload.",
            "ACTOR KIT blockers to clear once: height/weight/sizes, 2 phone headshots + 1 full-body, a 60-second intro video, MyCastingFile emergency contact. Without sizes, stand-in and wardrobe-fit roles cannot be submitted honestly.",
            "DAILY SWEEP: Milli checks Project Casting (Mississippi/Southeast), Backstage, AllCasting and Vertical Casting Calls for new beginner/intermediate roles matching male, plays 25–35, and posts fits to this board as 'found'.",
        ],
        "updated": datetime.datetime.utcnow().isoformat(),
    }

app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(str(BASE / "static" / "index.html"))

@app.get("/operator", response_class=HTMLResponse)
async def operator():
    return FileResponse(str(BASE / "static" / "operator.html"))

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return FileResponse(str(BASE / "static" / "admin.html"))

@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(str(BASE / "static" / "manifest.webmanifest"), media_type="application/manifest+json")

@app.get("/sw.js")
async def sw():
    return FileResponse(str(BASE / "static" / "sw.js"), media_type="application/javascript")
