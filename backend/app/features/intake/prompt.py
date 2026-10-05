"""The CTO's intake: what to ask, and the tool that hands over the brief."""

from app.features.models.schemas import ToolSpec

INTAKE_PROMPT = """You are {name}, the CTO of a solo founder's AI software team (MedhKarm).
The founder is telling you what they want built. Your job is to turn it into a clear brief
for your team, through a short, friendly conversation.

Ask only what you really need, at most 3 short questions at a time, in plain words:
- Is it a new project, or a change to an existing GitHub repository (ask for the link)?
- The stack, only if they seem to care: whatever they name is followed (any frontend, API
  language, database, hosting or payment provider). If they don't mind, say the team will
  pick Next.js, Supabase, Vercel and Razorpay, and don't ask again.
- Whether it needs sign-in, payments, reminders or an admin dashboard, if the request
  suggests it but isn't clear.
- Anything in the scope that is genuinely ambiguous.
Technologies listed as content (e.g. a landing page describing a company's tech) are not
stack choices. Never invent repository links.

Your first reply always asks your questions; never call submit_brief on the founder's first
message unless they say to just start. When you have enough, call submit_brief. Put the whole
ask in `request`, including their answers, so the team needs nothing else. Leave stack fields
empty unless the founder chose them. Then, in your message, say briefly what will happen.
Keep every message short."""

BRIEF_TOOL: ToolSpec = {
    "type": "function",
    "function": {
        "name": "submit_brief",
        "description": "Hand the agreed brief to the team (the founder confirms before it starts).",
        "parameters": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "The complete ask for the team, with the founder's answers",
                },
                "summary": {"type": "string", "description": "2-3 lines for the founder to check"},
                "repo_url": {"type": "string", "description": "Existing GitHub repo URL, if any"},
                "branch": {"type": "string"},
                "create_repo": {
                    "type": "boolean",
                    "description": "New project: create a private GitHub repo on release",
                },
                "new_repo_name": {"type": "string"},
                "frontend": {"type": "string", "description": "Only if the founder chose one"},
                "api": {"type": "string", "description": "Only if the founder chose one"},
                "database": {"type": "string", "description": "Only if the founder chose one"},
                "hosting": {"type": "string", "description": "Only if the founder chose one"},
                "payments": {"type": "string", "description": "Only if the founder chose one"},
                "modules": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["auth", "payments", "reminders", "dashboards"],
                    },
                    "description": "Ready-made modules: sign-in, payments, reminders, admin",
                },
                "starter": {
                    "type": "string",
                    "enum": ["auto", "yes", "no"],
                    "description": "Start from our tested starter: auto (if it's an app), yes, no",
                },
                "notes": {"type": "string", "description": "Docs or links for anything new"},
                "test_command": {"type": "string", "description": "Only if the founder gave one"},
            },
            "required": ["request", "summary"],
        },
    },
}


PROJECT_PROMPT = """You are {name}, the product manager of a solo founder's AI software team
(MedhKarm). The founder is describing a product they want built over days or weeks. Your job is
to understand it well enough to plan a backlog, through a short, friendly conversation.

Ask only what you need, at most 3 short questions at a time, in plain words:
- What the product is and who uses it, if that isn't clear.
- The main things it must do first (so you can plan the first items); suggest a few if
  they're unsure.
- New project, or an existing GitHub repository (ask for the link)?
- The stack, only if they seem to care: whatever they name is followed. If they don't mind,
  say the team will pick Next.js, Supabase, Vercel and Razorpay, and don't ask again.
- Whether the team should work through the backlog on its own (autopilot) and how many items
  a day, or wait for them to start each one (the default).
Technologies listed as content are not stack choices. Never invent repository links.

Your first reply always asks your questions; never call submit_project on the founder's first
message unless they say to just go. When you have enough, call submit_project. Put the whole
product in `goal`, with their answers, so you can plan from it alone. Give it a short `name`.
Leave stack fields empty unless the founder chose them. Keep every message short."""

PROJECT_TOOL: ToolSpec = {
    "type": "function",
    "function": {
        "name": "submit_project",
        "description": "Hand over the agreed project (the founder confirms, then you plan it).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short project name, 2-6 words"},
                "goal": {
                    "type": "string",
                    "description": "The whole product, with the founder's answers",
                },
                "summary": {"type": "string", "description": "2-3 lines for the founder to check"},
                "repo_url": {"type": "string", "description": "Existing GitHub repo URL, if any"},
                "frontend": {"type": "string", "description": "Only if the founder chose one"},
                "api": {"type": "string", "description": "Only if the founder chose one"},
                "database": {"type": "string", "description": "Only if the founder chose one"},
                "hosting": {"type": "string", "description": "Only if the founder chose one"},
                "payments": {"type": "string", "description": "Only if the founder chose one"},
                "modules": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["auth", "payments", "reminders", "dashboards"],
                    },
                    "description": "Ready-made modules: sign-in, payments, reminders, admin",
                },
                "notes": {"type": "string", "description": "Docs or links for anything new"},
                "autopilot": {
                    "type": "boolean",
                    "description": "Work through the backlog on its own",
                },
                "daily_limit": {"type": "integer", "description": "Items a day on autopilot, 1-10"},
            },
            "required": ["name", "goal", "summary"],
        },
    },
}


# Asked when the model hands over a brief before asking anything
FIRST_QUESTIONS = {
    "cto": (
        "Before I hand this to the team, a few quick questions:\n\n"
        "1. Is this a **new project**, or a change to an **existing GitHub repository**? "
        "If existing, share the link.\n"
        "2. Any **stack** you want (frontend, backend, database, hosting, payments)? If not, "
        "we'll use Next.js, Supabase, Vercel and Razorpay.\n"
        "3. Does it need **sign-in, payments, reminders or an admin dashboard**?"
    ),
    "pm": (
        "Before I plan the backlog, a few quick questions:\n\n"
        "1. What are the **main things it must do first**? I'll suggest more if you're unsure.\n"
        "2. Is this a **new project**, or an **existing GitHub repository**? If existing, "
        "share the link.\n"
        "3. Should the team **work through the backlog on its own** (how many items a day), "
        "or wait for you to start each item?"
    ),
}
