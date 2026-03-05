from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import re

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEXTILE_DATA_FILE = "textile_data.json"
SPINNING_DATA_FILE = "spinning_data.json"


# -------------------- MODELS --------------------

class QueryRequest(BaseModel):
    UserQuery: str


class QueryResponse(BaseModel):
    success: bool
    insight: str | None = None
    matched_question: str | None = None
    debug_keywords: list | None = None


# -------------------- DATA LOADER --------------------

def load_data(spinning: bool):
    if spinning == False:
        if not os.path.exists(TEXTILE_DATA_FILE):
            return []
        with open(TEXTILE_DATA_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    elif spinning == True:
        if not os.path.exists(SPINNING_DATA_FILE):
            return []
        with open(SPINNING_DATA_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            # Optionally, we could modify the data here to simulate "spinning"
            return data


# -------------------- KEYWORD EXTRACTION --------------------

def extract_keywords(text: str):
    text = text.lower()
    words = re.findall(r"\w+", text)

    stopwords = {
        "show", "me", "the", "what", "is", "a", "an", "of", "for", "to", "in",
        "with", "this", "that", "from", "us", "who", "by", "based", "on",
        "summary", "current"
    }

    return [w for w in words if w not in stopwords]


# -------------------- MAIN QUERY HANDLER --------------------

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    data = load_data(spinning=False)
    user_query = request.UserQuery.lower()
    user_keywords = set(extract_keywords(user_query))

    if not user_keywords:
        return QueryResponse(
            success=False,
            insight="Please ask a more specific question."
        )

    # -------- DOMAIN & MEASURE INTELLIGENCE --------

    DOMAIN_HINTS = {
        "sales": {"sales", "order", "buyer", "export", "shipment"},
        "manufacturing": {"manufacturing", "production", "packing", "cutting", "weaving"},
        "stock": {"stock", "inventory", "warehouse", "yarn", "fabric", "fg"},
        "mis": {"profit", "invoiced", "p&l"},
        "budget": {"budget", "variance", "overrun", "underrun"}
    }

    MEASURE_HINTS = {
        "value": {"value", "amount", "crore", "crores", "lakh", "lakhs"},
        "count": {"count", "number", "orders", "shipments"},
        "percentage": {"percentage", "percent", "%"}
    }

    detected_domains = {
        d for d, kws in DOMAIN_HINTS.items() if user_keywords & kws
    }
    detected_measures = {
        m for m, kws in MEASURE_HINTS.items() if user_keywords & kws
    }

    best_match = None
    best_score = -1

    # ---------------- MATCH LOOP ----------------

    for item in data:
        item_keywords_raw = item.get("keywords", [])
        item_keywords = set()

        for k in item_keywords_raw:
            item_keywords.update(re.findall(r"\w+", k.lower()))

        # Base lexical match
        matching_words = user_keywords & item_keywords
        score = len(matching_words)

        if score == 0:
            continue

        # Phrase boost
        for k in item_keywords_raw:
            if " " in k and k.lower() in user_query:
                score += 0.5

        # Domain boost
        item_domains = {
            d for d, kws in DOMAIN_HINTS.items() if item_keywords & kws
        }
        if detected_domains and item_domains & detected_domains:
            score += 1.5

        # Measure boost / penalty
        item_measures = {
            m for m, kws in MEASURE_HINTS.items() if item_keywords & kws
        }
        if detected_measures:
            if item_measures & detected_measures:
                score += 1
            else:
                score -= 0.5

        # Final selection
        if score > best_score:
            best_score = score
            best_match = item

    # ---------------- RESPONSE ----------------

    if best_match and best_score >= 1:
        return QueryResponse(
            success=True,
            insight=best_match.get("insight"),
            matched_question=best_match.get("question"),
            debug_keywords=list(user_keywords)
        )

    return QueryResponse(
        success=False,
        insight="I need a bit more clarity. Do you mean sales, manufacturing, stock, MIS, or budget?",
        debug_keywords=list(user_keywords)
    )



# ---------------------------- Spinning ----------------------
@app.post("/spin_query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    data = load_data(spinning=True)
    user_query = request.UserQuery.lower()
    user_keywords = set(extract_keywords(user_query))

    if not user_keywords:
        return QueryResponse(
            success=False,
            insight="Please ask a more specific question."
        )

    # -------- DOMAIN & MEASURE INTELLIGENCE --------

    DOMAIN_HINTS = {
        "sales": {"sales", "order", "buyer", "export", "shipment"},
        "manufacturing": {"manufacturing", "production", "packing", "cutting", "weaving"},
        "stock": {"stock", "inventory", "warehouse", "yarn", "fabric", "fg"},
        "mis": {"profit", "invoiced", "p&l"},
        "budget": {"budget", "variance", "overrun", "underrun"}
    }

    MEASURE_HINTS = {
        "value": {"value", "amount", "crore", "crores", "lakh", "lakhs"},
        "count": {"count", "number", "orders", "shipments"},
        "percentage": {"percentage", "percent", "%"}
    }

    detected_domains = {
        d for d, kws in DOMAIN_HINTS.items() if user_keywords & kws
    }
    detected_measures = {
        m for m, kws in MEASURE_HINTS.items() if user_keywords & kws
    }

    best_match = None
    best_score = -1

    # ---------------- MATCH LOOP ----------------

    for item in data:
        item_keywords_raw = item.get("keywords", [])
        item_keywords = set()

        for k in item_keywords_raw:
            item_keywords.update(re.findall(r"\w+", k.lower()))

        # Base lexical match
        matching_words = user_keywords & item_keywords
        score = len(matching_words)

        if score == 0:
            continue

        # Phrase boost
        for k in item_keywords_raw:
            if " " in k and k.lower() in user_query:
                score += 0.5

        # Domain boost
        item_domains = {
            d for d, kws in DOMAIN_HINTS.items() if item_keywords & kws
        }
        if detected_domains and item_domains & detected_domains:
            score += 1.5

        # Measure boost / penalty
        item_measures = {
            m for m, kws in MEASURE_HINTS.items() if item_keywords & kws
        }
        if detected_measures:
            if item_measures & detected_measures:
                score += 1
            else:
                score -= 0.5

        # Final selection
        if score > best_score:
            best_score = score
            best_match = item

    # ---------------- RESPONSE ----------------

    if best_match and best_score >= 1:
        return QueryResponse(
            success=True,
            insight=best_match.get("insight"),
            matched_question=best_match.get("question"),
            debug_keywords=list(user_keywords)
        )

    return QueryResponse(
        success=False,
        insight="I need a bit more clarity. Do you mean sales, manufacturing, stock, MIS, or budget?",
        debug_keywords=list(user_keywords)
    )


# -------------------- HEALTH CHECK --------------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "demo"}


# -------------------- RUN --------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
