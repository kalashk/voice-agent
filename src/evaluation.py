from __future__ import annotations
import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import SecretStr
from ragas.dataset_schema import EvaluationDataset, SingleTurnSampleOrMultiTurnSample, EvaluationResult, SingleTurnSample
from ragas.evaluation import evaluate
from ragas.metrics import AspectCritic
from ragas.metrics import SimpleCriteriaScore, RubricsScore
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from langchain_community.callbacks.manager import get_openai_callback
from helpers.config import SESSION_ID, TTS_PROVIDER, STT_PROVIDER, LLM_PROVIDER


def prepare_dataset_per_turn(conversations: list[dict]) -> EvaluationDataset:
    """
    Prepare dataset for Ragas evaluation per assistant turn.
    Consecutive user messages or assistant messages are combined.
    """
    print("[DEBUG] Preparing per-turn dataset...")
    samples: list[SingleTurnSampleOrMultiTurnSample] = []

    for i, conv in enumerate(conversations):
        dialogue = conv["dialogue"]
        # Combine consecutive same-role messages
        merged_dialogue = []
        prev_role = None
        buffer = ""
        for turn in dialogue:
            role = turn["role"]
            content = turn["content"]
            if role == prev_role:
                buffer += " " + content
            else:
                if prev_role is not None:
                    merged_dialogue.append({"role": prev_role, "content": buffer.strip()})
                buffer = content
                prev_role = role
        if buffer:
            merged_dialogue.append({"role": prev_role, "content": buffer.strip()})

        # Create per-turn samples (assistant turn with previous user context)
        for j, turn in enumerate(merged_dialogue):
            if turn["role"] == "assistant":
                prev_user_content = ""
                if j > 0 and merged_dialogue[j - 1]["role"] == "user":
                    prev_user_content = merged_dialogue[j - 1]["content"]
                sample = SingleTurnSample(
                    user_input=prev_user_content,
                    response=turn["content"],
                    reference=None
                )
                samples.append(sample)
                # print(f"[DEBUG] Created SingleTurnSample for assistant turn: {turn['content'][:50]}...")

    dataset = EvaluationDataset(samples=samples)
    print(f"[DEBUG] Prepared per-turn dataset with {len(dataset.samples)} samples")
    return dataset

# def get_metrics(llm: LangchainLLMWrapper) -> list[AspectCritic]:
#     print("[DEBUG] Defining metrics...")
#     metrics = [
#         AspectCritic(
#             name="persuasiveness",
#             llm=llm,
#             definition=(
#                 "Check if the assistant successfully tries to persuade the customer to consider "
#                 "a car or car loan while remaining subtle and convincing."
#             )
#         ),
#         AspectCritic(
#             name="clarity",
#             llm=llm,
#             definition=(
#                 "Check if the assistant's responses are clear, concise, and easy to understand "
#                 "for a customer on a voice call."
#             )
#         ),
#         AspectCritic(
#             name="politeness",
#             llm=llm,
#             definition=(
#                 "Check if the assistant is polite, friendly, and professional in tone "
#                 "throughout the conversation."
#             )
#         ),
#         AspectCritic(
#             name="relevance",
#             llm=llm,
#             definition=(
#                 "Check if the assistant's replies are contextually appropriate, "
#                 "directly responding to the customer's queries and inputs."
#             )
#         ),
#         AspectCritic(
#             name="language_script_compliance",
#             llm=llm,
#             definition="Check if the assistant's responses are written in Devanagari script."
#         ),
#         AspectCritic(
#             name="language_style_naturalness",
#             llm=llm,
#             definition="Check if the assistant's responses follow natural Hinglish style of conversation."
#         ),
#         AspectCritic(
#             name="language_no_forbidden_words",
#             llm=llm,
#             definition="Check if the assistant avoids forbidden or inappropriate words."
#         ),
#         AspectCritic(
#             name="language_number_format",
#             llm=llm,
#             definition="Check if numbers in the assistant's responses are converted correctly to Devanagari/Hinglish style."
#         ),
#         AspectCritic(
#             name="language_persona_consistency",
#             llm=llm,
#             definition="Check if the assistant maintains the intended persona throughout the conversation."
#         )
#     ]
#     print(f"[DEBUG] {len(metrics)} metrics defined")
#     return metrics

def get_metrics(llm: LangchainLLMWrapper):
    print("[DEBUG] Defining metrics...")

    metrics = [
        SimpleCriteriaScore(
            name="persuasiveness",
            definition="Score from 0 (not persuasive at all) to 5 (very persuasive and convincing).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="clarity",
            definition="Score from 0 (very unclear and confusing) to 5 (very clear, concise, and easy to understand).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="politeness",
            definition="Score from 0 (impolite or rude) to 5 (very polite, professional, and friendly).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="relevance",
            definition="Score from 0 (completely irrelevant) to 5 (highly relevant and directly addressing the customer).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="language_script_compliance",
            definition="Score from 0 (not in Devanagari at all) to 5 (fully compliant with Devanagari script).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="language_style_naturalness",
            definition="Score from 0 (unnatural Hinglish) to 5 (very natural Hinglish conversational style).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="language_no_forbidden_words",
            definition="Score from 0 (contains forbidden/inappropriate words) to 5 (no forbidden words at all).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="language_number_format",
            definition="Score from 0 (incorrect or inconsistent number formatting) to 5 (all numbers correctly converted to Devanagari/Hinglish).",
            llm=llm,
        ),
        SimpleCriteriaScore(
            name="language_persona_consistency",
            definition="Score from 0 (persona breaks often) to 5 (persona consistently maintained).",
            llm=llm,
        )
    ]

    print(f"[DEBUG] {len(metrics)} metrics defined (scored, not binary)")
    return metrics

def compute_average_scores(conversation_results: list[dict]) -> dict:
    """
    Compute average score per metric across all assistant turns.
    """
    avg_scores = {}
    metrics = conversation_results[0].keys() if conversation_results else []
    for metric in metrics:
        values = [
            conv_result.get(metric, 0)
            for conv_result in conversation_results
            if conv_result.get(metric) is not None
        ]
        avg_scores[metric] = round(sum(values) / len(values), 3) if values else None
        print(f"[DEBUG] Average {metric}: {avg_scores[metric]}")  # Added debug
    return avg_scores

def evaluate_per_turn(conversations: list[dict], llm_model: str = "gpt-4o-mini"):
    """
    Full evaluation pipeline for per-turn evaluation with averages and token usage tracking.
    """
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env.local"))
    openai_key_value = os.environ.get("OPENAI_API_KEY")
    if not openai_key_value:
        raise ValueError("Set your OPENAI_API_KEY as environment variable.")
    openai_key = SecretStr(secret_value=openai_key_value)
    
    # Wrap your LLM with verbose=True (optional) and track tokens via callback
    llm = LangchainLLMWrapper(ChatOpenAI(model=llm_model, api_key=openai_key, verbose=True))

    dataset = prepare_dataset_per_turn(conversations)

    # Define metrics
    metrics = get_metrics(llm)

    # Track token usage
    print("[DEBUG] Running evaluation per assistant turn...")
    with get_openai_callback() as cb:
        result = evaluate(dataset=dataset, metrics=metrics, show_progress=True, return_executor=False)
        usage_info = {
            "total_tokens": cb.total_tokens,
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "reasoning_tokens": getattr(cb, "reasoning_tokens", 0),
            "successful_requests": cb.successful_requests,
            "total_cost": cb.total_cost
        }


    print("[DEBUG] Evaluation finished")

    if isinstance(result, EvaluationResult):
        # Print per-turn scores
        print("[DEBUG] Processing per-turn scores...")
        for i, turn_result in enumerate(result.scores):
            print(f"\nAssistant Turn {i} Scores:")
            for metric, score in turn_result.items():
                print(f"{metric}: {score:.3f}" if score is not None else f"{metric}: None")

        # Compute average per metric
        avg_scores = compute_average_scores(result.scores)
        print("\nAverage Scores Across All Turns:")
        for metric, score in avg_scores.items():
            print(f"{metric}: {score}" if score is not None else f"{metric}: None")

        return avg_scores, usage_info
    else:
        raise TypeError("evaluate returned an Executor, not an EvaluationResult. Ensure return_executor=False")

def load_and_prepare_dataset_from_logs() -> List[Dict]:
    """
    Load a specific session JSON log from the 'log' folder (relative to this script)
    and convert it into a dataset suitable for evaluation.

    Only keeps:
        - Assistant responses
        - User responses with is_final = True

    Returns
    -------
    List[Dict]
        A list of conversation dictionaries suitable for evaluate_conversation().
    """
    script_dir = os.path.dirname(__file__)
    log_folder = os.path.join(script_dir, "logs")
    print(f"[DEBUG] Script directory: {script_dir}")
    print(f"[DEBUG] Logs folder: {log_folder}")

    # Construct the specific session file name
    session_to_evaluate = f"{TTS_PROVIDER}_{STT_PROVIDER}_{LLM_PROVIDER}_session_{SESSION_ID}.json"
    # session_to_evaluate=f"sarvam_anushka_deepgram_session_eaa7c2f1-548a-404d-be46-0c11736cbf12.json"
    filepath = os.path.join(log_folder, session_to_evaluate)
    print(f"[DEBUG] Evaluating session log file: {filepath}")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Session log file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        log_data = json.load(f)
    print(f"[DEBUG] Loaded JSON data. Transcript entries: {len(log_data.get('transcript', []))}")


    conversation = []
    for item in log_data.get("transcript", []):
        # if item["role"] == "assistant" and item.get("interrupted", False):
        if item["role"] == "assistant":
            conversation.append({"role": "assistant", "content": item["text"]})
            # print(f"[DEBUG] Assistant: {item['text']}")
        elif item["role"] == "user" and item.get("is_final", False):
            conversation.append({"role": "user", "content": item["text"]})
            # print(f"[DEBUG] User: {item['text']}")
    print(f"[DEBUG] Filtered conversation length: {len(conversation)}")

    formatted_conversations = []
    if conversation:
        formatted_conversations.append({"dialogue": conversation})
        print(f"[DEBUG] Formatted conversations ready for evaluation.")

    return formatted_conversations

def main():
    print("[DEBUG] Starting evaluation script...")

    # Load and prepare dataset from the specific session log
    conversations = load_and_prepare_dataset_from_logs()
    if not conversations:
        print("[DEBUG] No conversation data found in the log.")
        return {}, {}
    print(f"[DEBUG] Number of conversations to evaluate: {len(conversations)}") 

    # Run evaluation and get average scores and total tokens
    avg_scores, usage_info = evaluate_per_turn(conversations)
    print("[DEBUG] Evaluation completed.")

    # Print final average scores (only once)
    print("\n[DEBUG] Final average scores per metric:")
    for metric, score in avg_scores.items():
        print(f"{metric}: {score}" if score is not None else f"{metric}: None")

    # Print total token usage
    print("\n[DEBUG] Token usage and cost:")
    for k, v in usage_info.items():
        if k == "total_cost":
            print(f"{k}: ${v:.6f}")
        else:
            print(f"{k}: {v}")

    print("[DEBUG] Evaluation script finished successfully.")
    return avg_scores, usage_info

if __name__ == "__main__":
    main()