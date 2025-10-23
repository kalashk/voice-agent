# assistants/summary.py
import json
import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

logger = logging.getLogger("summary")

SUMMARY_PROMPT = """
You are a call summary generator for a car loan sales assistant.
Analyze the entire conversation and output a JSON object with these keys:
- call_metadata
- customer_profile
- vehicle_information
- financial_information
- intent_and_qualification
- summary_text

Follow this JSON schema exactly:
{
    "customer_profile": {
        "name": "string or null",
        "gender": "male | female | unknown",
        "age_estimate": "number or null",
        "location_city": "string or null",
        "occupation_type": "Salaried | Self-Employed | Business Owner | Unknown"
    },
    "vehicle_information": {
        "vehicle_type": "Car | SUV | Commercial | Unknown",
        "make_model": "string or null",
        "registration_year": "number or null",
        "ownership_status": "Owned | Financed | New Purchase | Not Mentioned",
        "current_loan_provider": "string or null"
    },
    "financial_information": {
        "monthly_income_bracket": "Below 25k | 25k-50k | 50k-1L | Above 1L | Unknown",
        "existing_emi_burden": "Low | Moderate | High | Unknown",
        "cibil_score_discussed": "Yes | No",
        "approximate_cibil_score": "number or null",
        "loan_amount_requested": "number or null",
        "tenure_requested_months": "number or null"
    },
    "intent_and_qualification": {
        "interested_in_loan": "Yes | No | Maybe",
        "reason_if_not_interested": "string or null",
        "shared_documents_on_whatsapp": "Yes | No | Pending",
        "documents_mentioned": ["PAN", "Aadhaar", "Salary Slip"],
        "communication_tone": "Cooperative | Polite | Rude | Disinterested",
        "follow_up_needed": "Yes | No",
        "preferred_follow_up_time": "string or null"
    },
    "summary_text": "2-3 sentences natural summary."
}

Output ONLY valid JSON.
"""

# ---------------- LLM Setup ----------------
_summarizer_llm = ChatGroq(model="moonshotai/kimi-k2-instruct-0905", temperature=0.3)
_parser = JsonOutputParser(pydantic_object={"type": "object"})
_prompt = ChatPromptTemplate.from_messages([
    ("system", SUMMARY_PROMPT),
    ("user", "{input}")
])
_summary_chain = _prompt | _summarizer_llm | _parser


# ---------------- Summary Function ----------------
async def generate_summary_llm(history_text: str, customer_data: dict) -> dict:
    """
    Generate a structured JSON summary from the call transcript and customer metadata.
    """
    logger.info("Generating call summary via independent LLM...")

    llm_input = f"""
    CUSTOMER CONTEXT:
    The following is structured customer information collected before or during the call.
    {json.dumps(customer_data, indent=2, ensure_ascii=False)}

    CONVERSATION HISTORY:
    {history_text}
    """

    try:
        result = _summary_chain.invoke({"input": llm_input})
        summary_json = json.loads(json.dumps(result))
        logger.info("Generated Summary: %s", summary_json)
        return summary_json
    except Exception as e:
        logger.error("Failed to parse summary JSON: %s", e)
        return {"error": "Invalid JSON generated", "exception": str(e)}
