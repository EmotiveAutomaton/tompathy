"""B13 preparation. Explicit new profile; never changes the fixed CPU reader."""
from copy import deepcopy

from ..ledger.ids import digest
from .runner import CATALOGUE, Transcriber, answer_schema

Q10 = "Theme tags explicitly present in the text, not the maker's motives. Return an empty array [] when none of the listed themes is present. Ordinary objects, locations, mechanical descriptions and negated themes do not by themselves imply care, discovery or any other theme. Use unclear only when a theme is genuinely ambiguous; never use it as a substitute for no theme."
PROMPT_VERSION = "single-literal-question-v1"


class QuestionProfile(Transcriber):
    """Only the separately configured live-gpu-2 profile may opt in."""
    requires_empty_theme_gate = True

    def __init__(self, backend, cache, admissions=()):
        if backend.settings.get("profile") != "live-gpu-2":
            raise ValueError("Per-question pins require the new live-gpu-2 profile")
        super().__init__(backend, cache, admissions)

    def question(self, question_id):
        question = deepcopy(CATALOGUE["questions"][question_id])
        if question_id == "Q10":
            question["question"] = Q10
        return question

    def pin_for(self, question_id):
        return digest({"profile": "live-gpu-2", "model": self.backend.model_id,
                       "settings": self.backend.settings, "question": self.question(question_id),
                       "schema": answer_schema(question_id), "prompt": PROMPT_VERSION})

    def ask(self, question_id, **kwargs):
        if question_id == "Q10" and not kwargs.get("admission_test") and self.admissions.get("Q10", {}).get("protocol") != "q10-empty-v2":
            raise ValueError("The new Q10 requires its empty-set protocol receipt")
        return super().ask(question_id, **kwargs)


def empty_theme_battery():
    from .batteries import constructed
    positives = [item for item in constructed("Q10") if item["expected"]][:160]
    negatives = []
    shapes = ["rectangular", "circular", "triangular", "oval", "square"]
    for i in range(40):
        text = (f"The panel is {shapes[i % 5]} and has {i + 2} numbered sections."
                if i < 20 else f"This is a {shapes[i % 5]} label for section {i + 2}, not a story about caring, danger, conflict, desire, loss, discovery, status, food or play.")
        negatives.append({"id": f"q10-empty-v2-{i}", "context": "Literal description.", "text": text, "before": None,
                          "expected": [], "source": "constructed-q10-empty-v2:" + digest(text),
                          "tags": ["negation" if i >= 20 else "paraphrase", f"family-empty-{i % 5}"]})
    return positives + negatives
