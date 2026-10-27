"""
Turns a natural-language instruction into a plan, using an LLM with tool calling.

The LLM never touches the robot. It can only pick from four tools: two that add steps to
a plan, one to ask a question back, one to refuse. Everything it returns is plain data
that still has to pass validation and human approval before anything moves.
"""
import json
import os
from dataclasses import dataclass, field

import anthropic
from dotenv import load_dotenv

from .actions import Transfer, transfer, distribute

load_dotenv()

MODEL = os.getenv("LAB_AGENT_MODEL", "claude-sonnet-5-5")

WELL_PATTERN = "^[A-Ha-h](1[0-2]|[1-9])$"  # A1..H12 on a 96-well plate
PLATE_NAMES = ["source", "target"]

TOOLS = [
    {
        "name": "transfer",
        "description": "Move one volume of liquid from one well to another well.",
        "input_schema": {
            "type": "object",
            "properties": {
                "volume_ul": {"type": "number", "description": "Volume in microlitres."},
                "source_plate": {"type": "string", "enum": PLATE_NAMES},
                "source_well": {"type": "string", "pattern": WELL_PATTERN},
                "dest_plate": {"type": "string", "enum": PLATE_NAMES},
                "dest_well": {"type": "string", "pattern": WELL_PATTERN},
            },
            "required": ["volume_ul", "source_plate", "source_well", "dest_plate", "dest_well"],
        },
    },
    {
        "name": "distribute",
        "description": "Move the same volume from one source well into each of several wells.",
        "input_schema": {
            "type": "object",
            "properties": {
                "volume_ul": {"type": "number", "description": "Volume per destination well, in microlitres."},
                "source_plate": {"type": "string", "enum": PLATE_NAMES},
                "source_well": {"type": "string", "pattern": WELL_PATTERN},
                "dest_plate": {"type": "string", "enum": PLATE_NAMES},
                "dest_wells": {"type": "array", "items": {"type": "string", "pattern": WELL_PATTERN}},
            },
            "required": ["volume_ul", "source_plate", "source_well", "dest_plate", "dest_wells"],
        },
    },
    {
        "name": "ask_clarification",
        "description": "Ask the user a question when the instruction is missing information "
                       "(volume, wells, plate) or could mean more than one thing.",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
    {
        "name": "refuse",
        "description": "Decline an instruction that is not a liquid handling task on this deck, "
                       "or that should not be run.",
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]

SYSTEM_PROMPT = """You plan liquid handling steps for a lab robot.

Translate the user's instruction into tool calls. You may call transfer and distribute as
many times as needed, in the order the steps should run. All volumes are in microlitres.

Do not guess. If a volume, well or plate is missing or ambiguous, call ask_clarification
instead of planning. If the request is not a liquid handling task on this deck, call refuse.
Never combine planning tools with ask_clarification or refuse in the same answer.
Always answer with tool calls only, never with plain text.

Current deck state:
{deck}"""


@dataclass
class PlannerResult:
    plan: list[Transfer] = field(default_factory=list)
    question: str | None = None
    refusal: str | None = None
    free_text: str | None = None  # the model answered in prose instead of calling a tool


def parse_response(content) -> PlannerResult:
    """Turn the LLM's tool calls into a PlannerResult. Kept separate so it can be tested offline."""
    result = PlannerResult()
    for block in content:
        if block.type != "tool_use":
            continue
        args = block.input
        if block.name == "transfer":
            result.plan += transfer(**args)
        elif block.name == "distribute":
            result.plan += distribute(**args)
        elif block.name == "ask_clarification":
            result.question = args["question"]
        elif block.name == "refuse":
            result.refusal = args["reason"]

    if not (result.plan or result.question or result.refusal):
        text = " ".join(b.text for b in content if b.type == "text").strip()
        result.free_text = text or "(empty response)"
    return result


def plan_instruction(instruction: str, deck_state: dict, client=None) -> PlannerResult:
    client = client or anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT.format(deck=json.dumps(deck_state, indent=2)),
        tools=TOOLS,
        # Forcing tool use (tool_choice "any") isn't supported by every model, so the prompt
        # asks for tools only and parse_response flags any answer that comes back as prose.
        tool_choice={"type": "auto"},
        messages=[{"role": "user", "content": instruction}],
    )
    return parse_response(response.content)
