"""Decides a run's stack. The founder's form wins; then what the request names ("a Python API
on AWS with Stripe"); then our defaults (Next.js, Supabase, Vercel, Razorpay). Anything we have
no ready-made part for (Java, Cashfree, …) is still followed: the team builds it, from the
founder's notes. No model call: the same request always gets the same stack."""

import re

from app.features.starters.schemas import ModuleSpec, Source, Stack, StackChoice

# name -> words in a request that mean it (matched as whole words, case-insensitive)
FRONTENDS = {
    "nextjs": ["next.js", "nextjs", "next js", "react"],
    "vue": ["vue", "nuxt"],
    "angular": ["angular"],
    "svelte": ["svelte", "sveltekit"],
    "none": ["no frontend", "api only", "only an api", "just an api", "backend only", "headless"],
}
APIS = {
    "python": ["python", "fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "java": ["java", "spring boot", "spring"],
    "node": ["express", "nestjs", "node.js api", "node api"],
    "go": ["golang", "go api"],
    "ruby": ["rails", "ruby"],
    "php": ["php", "laravel"],
    "dotnet": [".net", "dotnet", "c#", "asp.net"],
}
DATABASES = {
    "supabase": ["supabase"],
    "postgres": ["postgres", "postgresql"],
    "mysql": ["mysql", "mariadb"],
    "mongodb": ["mongodb", "mongo"],
    "sqlite": ["sqlite"],
    "firebase": ["firebase", "firestore"],
    "dynamodb": ["dynamodb"],
}
HOSTS = {
    "vercel": ["vercel"],
    "docker": ["docker", "docker compose", "self-host", "self host", "my own server", "vps"],
    "digitalocean": ["digitalocean", "digital ocean"],
    "aws": ["aws", "amazon web services", "ec2", "lightsail", "elastic beanstalk"],
    "gcp": ["gcp", "google cloud", "cloud run"],
    "azure": ["azure"],
    "railway": ["railway"],
    "render": ["render.com"],
    "fly": ["fly.io"],
    "netlify": ["netlify"],
    "heroku": ["heroku"],
}
PAYMENTS = {
    "razorpay": ["razorpay"],
    "stripe": ["stripe"],
    "cashfree": ["cashfree"],
    "paypal": ["paypal"],
    "phonepe": ["phonepe"],
    "payu": ["payu"],
    "paytm": ["paytm"],
    "instamojo": ["instamojo"],
}
# Requests for these aren't apps: no starter unless the founder asks for one
NOT_APPS = [
    "script",
    "cli",
    "command-line",
    "command line",
    "library",
    "package",
    "function",
    "module that",
    "parser",
    "algorithm",
    "kata",
    "utility",
]
# Clearly a web app, whatever else the request says ("a package delivery website")
WEB_APPS = [
    "website",
    "web app",
    "web page",
    "webpage",
    "portal",
    "dashboard",
    "saas",
    "login",
    "sign in",
    "sign up",
    "landing page",
    "online store",
    "shop",
]
APPS = [
    "app",
    "application",
    "website",
    "web site",
    "site",
    "web page",
    "webpage",
    "page",
    "portal",
    "dashboard",
    "store",
    "shop",
    "marketplace",
    "saas",
    "api",
    "backend",
    "booking",
    "landing",
    "platform",
    "crm",
    "blog",
    "login",
    "sign in",
    "sign up",
]

STARTER_APIS = {"nextjs": "nextjs", "python": "fastapi"}  # api -> its starter
OUR_DATABASES = {"nextjs": {"supabase", "postgres"}, "fastapi": {"sqlite"}}
OUR_PAYMENTS = {"razorpay", "stripe"}
OUR_HOSTS = {"vercel", "docker", "digitalocean", "aws", "gcp", "azure", "railway", "render", "fly"}


def mentions(text: str, words: list[str]) -> bool:
    return any(re.search(rf"(?<![\w.]){re.escape(w)}(?![\w])", text) for w in words)


def detect(text: str, table: dict[str, list[str]]) -> str | None:
    return next((name for name, words in table.items() if mentions(text, words)), None)


def canonical(value: str | None, table: dict[str, list[str]]) -> str | None:
    """Our name for what the founder typed ("Next.js" -> "nextjs"); other names as given."""
    if not value:
        return value
    if value in table:
        return value
    return next((name for name, words in table.items() if value in words), value)


def resolve_stack(request: str, choice: StackChoice, modules: list[ModuleSpec]) -> Stack:
    text = request.lower()
    picked: dict[str, str] = {}
    sources: dict[str, Source] = {}

    def decide(field: str, table: dict[str, list[str]], default: str) -> None:
        names = {**table, "nextjs": FRONTENDS["nextjs"]} if field == "api" else table
        given = canonical(getattr(choice, field), names)
        found = detect(text, table)
        picked[field], sources[field] = (
            (given, "founder") if given else (found, "request") if found else (default, "team")
        )

    decide("frontend", FRONTENDS, "nextjs")
    decide("api", APIS, "nextjs" if picked["frontend"] == "nextjs" else "python")
    database = {"nextjs": "supabase", "python": "sqlite"}.get(picked["api"], "postgres")
    decide("database", DATABASES, database)
    decide("hosting", HOSTS, "vercel" if picked["api"] == "nextjs" else "docker")
    decide("payments", PAYMENTS, "razorpay")

    starter, layout = _starter(picked)
    use_starter = _wants_starter(text, choice)
    custom = _custom(picked, starter if use_starter else None)
    chosen = _modules(text, choice, picked, modules) if use_starter and starter else []
    if use_starter and starter and layout == "split" and chosen:
        custom.append(
            f"Ready-made modules ({', '.join(chosen)}) exist only for the Next.js API; "
            "build these parts in the Python API yourselves."
        )
        chosen = []
    return Stack(
        **picked,
        sources=sources,
        starter=starter if use_starter else None,
        layout=layout if use_starter and starter else None,
        modules=chosen,
        custom=custom,
        notes=choice.notes.strip(),
    )


def _starter(picked: dict[str, str]) -> tuple[str | None, str | None]:
    starter = STARTER_APIS.get(picked["api"])
    if starter is None or picked["frontend"] not in ("nextjs", "none"):
        return None, None
    if starter == "fastapi" and picked["frontend"] == "nextjs":
        return "fastapi", "split"
    return starter, "single"


def _wants_starter(text: str, choice: StackChoice) -> bool:
    if choice.starter is not None:
        return choice.starter
    if not choice.empty:  # the founder chose a stack: it's an app
        return True
    if mentions(text, WEB_APPS):
        return True
    return mentions(text, APPS) and not mentions(text, NOT_APPS)


def _custom(picked: dict[str, str], starter: str | None) -> list[str]:
    """What the team sets up itself, said plainly for the CTO and the developers."""
    notes: list[str] = []
    if starter is None and (
        picked["api"] not in STARTER_APIS or picked["frontend"] not in ("nextjs", "none")
    ):
        notes.append(
            f"No ready-made starter for {picked['frontend']} + {picked['api']}: set the project "
            "up yourselves with that stack's usual structure and test tools."
        )
    if starter and picked["database"] not in OUR_DATABASES.get(starter, set()):
        notes.append(
            f"Database {picked['database']}: the starter's data layer doesn't support it yet; "
            "add an implementation behind the same interface (lib/db or app/store.py)."
        )
    if picked["payments"] not in OUR_PAYMENTS | {"none"}:
        notes.append(
            f"Payments through {picked['payments']}: no ready-made provider; if payments are "
            "needed, add one behind the same interface, following its docs (the founder's notes)."
        )
    if picked["hosting"] not in OUR_HOSTS:
        notes.append(f"Hosting on {picked['hosting']}: add the files it needs to deploy.")
    return notes


def _modules(
    text: str, choice: StackChoice, picked: dict[str, str], catalog: list[ModuleSpec]
) -> list[str]:
    known = {m.name: m for m in catalog if "nextjs" in m.starters}
    if choice.modules is not None:
        wanted = [m for m in choice.modules if m in known]
    else:
        wanted = [m.name for m in known.values() if mentions(text, m.keywords)]
        if choice.payments and choice.payments != "none" and "payments" in known:
            wanted.append("payments")
    if picked["payments"] == "none" or picked["payments"] not in OUR_PAYMENTS:
        wanted = [m for m in wanted if m != "payments"]
    ordered: list[str] = []
    for name in wanted:  # required modules first (the dashboard needs sign-in)
        for needed in [*known[name].requires, name]:
            if needed in known and needed not in ordered:
                ordered.append(needed)
    return ordered
