"""Reproducible constructed writing batteries; not a natural-data admission.

Each template has an explicit answer. Names and ordinary objects vary the text,
not the label. Results retain template family so paired errors can be inspected.
Q2 needs an installed spaCy model for its independent entity cross-check.
"""

import re

from ..ledger.ids import digest
from .runner import validate_answer

NAMES = [
    "Alice",
    "Bob",
    "Carol",
    "David",
    "Elena",
    "Farah",
    "Grace",
    "Henry",
    "Isabel",
    "Jonah",
    "Kara",
    "Liam",
    "Maya",
    "Noah",
    "Olivia",
    "Priya",
    "Quinn",
    "Rosa",
    "Sam",
    "Tara",
    "Uma",
    "Victor",
    "Wendy",
    "Xavier",
    "Yara",
]
OBJECTS = [
    "book",
    "parcel",
    "lamp",
    "chair",
    "scarf",
    "basket",
    "bottle",
    "coat",
    "notebook",
    "painting",
]


def constructed(question, *, entity_model=None):
    items = []
    nlp = None
    if question == "Q2":
        if entity_model is None:
            raise ValueError("Q2 battery requires an installed pinned spaCy model directory")
        from pathlib import Path

        import spacy

        if not Path(entity_model).is_dir():
            raise ValueError("Entity model directory is unavailable; no download is attempted")
        nlp = spacy.load(entity_model)
    for i in range(200):
        name = NAMES[i % len(NAMES)]
        obj = OBJECTS[(i // len(NAMES)) % len(OBJECTS)]
        statement = f"{name} carried the {obj}."
        opposite = f"{name} did not carry the {obj}."
        context, before = statement, None
        cases = {
            "Q1": [
                (f"The {obj} was heavy to carry.", "yes"),
                ("The moon does not produce its own light.", "no"),
                (f"It was a very light {obj}.", "yes"),
                ("Volcanic rock forms from cooled magma.", "no"),
            ],
            "Q2": [
                (statement, "no"),
                (f"{name} met Napoleon in Paris.", "yes"),
                (f"{name} did not carry the {obj}.", "no"),
                (f"{name} visited Tokyo.", "yes"),
            ],
            "Q3": [
                (
                    f"Please be advised that {name} has submitted the {obj} for your consideration.",
                    "formal",
                ),
                (statement, "neutral"),
                (f"Hey, {name}, that {obj} is super cool!", "casual"),
                (f"{name} placed the {obj} on a table.", "neutral"),
            ],
            "Q4": [
                (f"{name} was delighted: the {obj} was wonderful!", "more positive"),
                (statement, "same"),
                (f"{name} was miserable: the {obj} was awful.", "more negative"),
                (f"{name} carried a {obj}.", "same"),
            ],
            "Q5": [
                (f'{name} said, "Please bring the {obj}." "Certainly," came the reply.', "yes"),
                (f"{name} carried the {obj} without speaking.", "no"),
                (
                    f'"Do not move the {obj}," said {name}. "I will leave it here," replied a friend.',
                    "yes",
                ),
                (f"{name} silently watched the {obj}. No conversation took place.", "no"),
            ],
            "Q6": [
                (f"I carried my {obj}.", "first"),
                (f"You carried your {obj}.", "second"),
                (f"She carried her {obj}.", "third"),
                (f"I gave you my {obj}.", "mixed"),
            ],
            "Q7": [
                (opposite, "yes"),
                (statement, "no"),
                (f"It is false that {name} carried the {obj}.", "yes"),
                (f"It is true that {name} carried the {obj}.", "no"),
            ],
            "Q9": [
                (opposite, "yes"),
                (statement.replace("carried", "transported"), "no"),
                (statement.replace("carried", "destroyed"), "yes"),
                (statement, "no"),
            ],
        }
        if question == "Q8":
            edits = [
                (statement.replace("the", "teh"), statement, "typo"),
                (f"{name} carry the {obj}.", statement, "grammar"),
                (statement, statement.replace("carried", "transported"), "wording"),
                (statement, statement + " The sky was cloudy.", "add content"),
                (statement + " The sky was cloudy.", statement, "remove content"),
                (statement + " The sky was cloudy.", "The sky was cloudy. " + statement, "reorder"),
                (f"Give {name} the {obj}, idiot!", f"Please give {name} the {obj}.", "tone"),
                (statement, "**" + statement + "**", "format"),
            ]
            before, text, answer = edits[i % len(edits)]
        elif question == "Q10":
            themes = [
                (f"{name} faced immediate danger from a collapsing roof.", ["danger"]),
                (f"{name} gently cared for and comforted a sick child.", ["care"]),
                (f"{name} played a silly game and laughed at a joke.", ["play or humor"]),
                (f"{name} argued and fought with a rival.", ["conflict"]),
                (f"{name} grieved after a loved one's death.", ["loss or separation"]),
                (f"{name} felt romantic desire and sexual attraction.", ["desire"]),
                (f"{name} discovered an unknown island while exploring.", ["discovery"]),
                (f"{name} gained prestige and high social rank.", ["status"]),
                (f"{name} ate food to satisfy physical hunger.", ["food or body"]),
                (f"The {obj} was rectangular.", []),
            ]
            text, answer = themes[i % len(themes)]
        else:
            if question not in cases:
                raise ValueError("Unknown question")
            text, answer = cases[question][i % 4]
            if question == "Q9":
                before = statement
        item = {
            "id": f"constructed-{question}-{i}",
            "context": context,
            "text": text,
            "before": before,
            "expected": answer,
            "source": "constructed-writing-v1:" + digest([context, before, text]),
            "tags": [
                "negation" if "not" in text or "false" in text else "paraphrase",
                f"family-{i % (8 if question == 'Q8' else 10 if question == 'Q10' else 4)}",
            ],
        }
        if question == "Q5":
            item["crosscheck"] = "yes" if '"' in text else "no"
        if question == "Q6":
            words = set(re.findall(r"\w+", text.lower()))
            groups = [
                bool(words & set(s.split()))
                for s in ("i me my we us our", "you your", "he him his she her they them their")
            ]
            item["crosscheck"] = (
                "mixed" if sum(groups) > 1 else ["first", "second", "third"][groups.index(True)]
            )
        if question == "Q2":
            seen = {e.text for e in nlp(context).ents}
            item["crosscheck"] = "yes" if any(e.text not in seen for e in nlp(text).ents) else "no"
        validate_answer(question, {"answer": answer})
        items.append(item)
    # Register/tone/theme batteries include explicit negation records as well;
    # labels are retained where a negation changes no register or theme presence.
    if question in {"Q3", "Q4", "Q6", "Q8", "Q10"}:
        for item in items[:10]:
            item["tags"].append("negation")
            # This tag names a negative source context, not a negated target label.
            item["context"] = "It was not raining. " + item["context"]
    return items
