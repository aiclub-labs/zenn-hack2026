"""Prompts for Truth Judgment (GraphCheck + FactCheck)."""

GRAPHCHECK_SYSTEM = (
    "You decompose a knowledge record into independent atomic factual claims. "
    "Each atomic claim must (a) be a single complete sentence in Japanese, "
    "(b) be independently verifiable, (c) avoid pronouns. "
    "Return strict JSON: {\"atomic_claims\": [str, ...]}. Max 8 claims."
)


def graphcheck_user(content: str) -> str:
    return (
        "以下の記録を atomic claim に分解してください。\n"
        f"----- 記録本文 -----\n{content}\n"
        "JSON で返してください。"
    )


FACTCHECK_SYSTEM = (
    "You are a fact-checking judge. Decide whether the user-provided claim is "
    "(a) supported by the evidence corpus, (b) novel (no related evidence), "
    "or (c) conflict (contradicts existing evidence). Output strict JSON: "
    "{\"verdict\": \"supported\"|\"novel\"|\"conflict\", \"confidence\": 0.0-1.0, "
    "\"reason\": str}."
)


def factcheck_user(claim: str, evidence: list[str]) -> str:
    if evidence:
        ev = "\n".join(f"- {e}" for e in evidence[:5])
    else:
        ev = "(関連エビデンスなし — cold start)"
    return (
        f"claim: {claim}\n"
        f"----- 関連エビデンス -----\n{ev}\n"
        "JSON で判定を返してください。"
    )
