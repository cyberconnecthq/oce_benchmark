from datetime import datetime

INSTRUCTIONS_PROMPT = """You are a Crypto AI assistant agent. Today is {date}. You are given a question and you need to answer it using the tools provided.
You may not interract with the user.
When you have the answer, you should respond with 'FINAL ANSWER:' followed by your answer.
If you need to generate a TX params that is executable and signable, here is a validate format:
```json
# Legacy transaction:
{{
    'from': '0xFAafe5FcaC0E87D40017E44CD462398026a12230',   #hex address
    'to': '0xF0109fC8DF283027b6285cc889F5aA624EaC1F55', #hex address
    'value': 1000000000, # decimal
    'gas': 2000000,  # decimal
    'gasPrice': 234567897654321,     # decimal
    'nonce': 0,  # decimal
    'chainId': 1337  # decimal
}}

#dynamic fee transaction

{{
    'type': 2,  # optional - can be implicitly determined based on max fee params
    'gas': 100000,
    'maxFeePerGas': 2000000000,
    'maxPriorityFeePerGas': 2000000000,
    'data': '0x616263646566',
    'nonce': 34,
    'to': '0x09616C3d61b3331fc4109a9E41a8BDB7d9776609',
    'value': '0x5af3107a4000',
    'accessList': (  # optional
        {{
            'address': '0x0000000000000000000000000000000000000001',
            'storageKeys': (
                '0x0100000000000000000000000000000000000000000000000000000000000000',
            )
        }},
    ),
    'chainId': 1337,
}}

```
Note:
1. All hex data should be calculated correctly using python
2. all address should be correct
3. 'nonce' should be a number calculated from python, don't make it up

Question:
{question}
"""


def merge_statistics(metadata: dict) -> dict:
    """
    Merge turn-level statistics into session-level statistics.

    Args:
        metadata (dict): The metadata with turn-level statistics

    Returns:
        dict: Updated metadata with merged statistics
    """
    # Reset aggregate values to recalculate
    metadata["total_tokens"] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    metadata["total_tokens_retrieval"] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    metadata["tool_usage"] = {}
    metadata["tool_calls_count"] = 0
    metadata["api_calls_count"] = len(metadata["turns"])
    metadata["error_count"] = 0

    # Aggregate statistics from all turns
    for turn in metadata["turns"]:
        # Aggregate token usage
        metadata["total_tokens"]["prompt_tokens"] += turn["tokens"]["prompt_tokens"]
        metadata["total_tokens"]["completion_tokens"] += turn["tokens"][
            "completion_tokens"
        ]
        metadata["total_tokens"]["total_tokens"] += turn["tokens"]["total_tokens"]
        metadata["total_tokens_retrieval"]["prompt_tokens"] += turn["tokens_retrieval"][
            "prompt_tokens"
        ]
        metadata["total_tokens_retrieval"]["completion_tokens"] += turn[
            "tokens_retrieval"
        ]["completion_tokens"]
        metadata["total_tokens_retrieval"]["total_tokens"] += turn["tokens_retrieval"][
            "total_tokens"
        ]
        # Count errors
        metadata["error_count"] += len(turn["errors"])

        # Aggregate tool usage
        for tool_call in turn["tool_calls"]:
            tool_name = tool_call["tool_name"]
            if tool_name not in metadata["tool_usage"]:
                metadata["tool_usage"][tool_name] = 0
            metadata["tool_usage"][tool_name] += 1
            metadata["tool_calls_count"] += 1

    # Calculate total duration
    if metadata["start_time"] and metadata["end_time"]:
        start = datetime.fromisoformat(metadata["start_time"])
        end = datetime.fromisoformat(metadata["end_time"])
        metadata["total_duration_seconds"] = (end - start).total_seconds()

    return metadata


# Filter out by pattern because all providers dont throw the same exceptions to OpenAI SDK
def is_token_limit_error(error_msg: str) -> bool:
    token_limit_patterns = [
        "token limit",
        "tokens_exceeded_error",
        "context length",
        "maximum context length",
        "token_limit_exceeded",
        "maximum tokens",
        "too many tokens",
        "prompt is too long",
        "maximum prompt length",
        "maximum number of tokens allowed",
        "input length and `max_tokens` exceed context",
        "error code: 400",
        "error code: 413",
        "string too long",
        "413",
        "request exceeds the maximum size",
        "request_too_large",
        "too many total text bytes",
    ]

    return any(pattern in error_msg.lower() for pattern in token_limit_patterns)

