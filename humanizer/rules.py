"""Phrase tables. Every replacement stays within a formal academic register."""
from __future__ import annotations

# (regex, alternatives). An empty alternative deletes the phrase.
# Patterns are matched case-insensitively on word boundaries.
REPLACEMENTS: list[tuple[str, list[str]]] = [
    # Throat-clearing openers: delete outright.
    (r"it is (?:important|worth|crucial|essential|imperative) (?:to note|noting|to recognize|to acknowledge|to mention|mentioning|to emphasize) that\s+", [""]),
    (r"it (?:should|must) be (?:noted|emphasized|acknowledged|mentioned) that\s+", [""]),
    (r"it is (?:evident|clear|apparent|undeniable) that\s+", [""]),
    (r"it goes without saying that\s+", [""]),
    (r"needless to say,?\s+", [""]),
    (r"in today's (?:fast-paced|digital|modern|rapidly (?:changing|evolving)|interconnected|ever-(?:changing|evolving)) (?:world|age|era|society|landscape),?\s+", ["", "at present, "]),
    # Stock verbs.
    (r"delves (?:deeper )?into", ["examines", "analyses"]),
    (r"delve (?:deeper )?into", ["examine", "analyse"]),
    (r"delving (?:deeper )?into", ["examining"]),
    (r"delved (?:deeper )?into", ["examined"]),
    (r"sheds light on", ["clarifies", "helps explain"]),
    (r"shed light on", ["clarify", "help explain"]),
    (r"shedding light on", ["clarifying"]),
    (r"underscores", ["indicates", "points to", "confirms"]),
    (r"underscore", ["indicate", "confirm"]),
    (r"underscoring", ["indicating", "confirming"]),
    (r"showcases", ["shows", "demonstrates"]),
    (r"showcase", ["show", "demonstrate"]),
    (r"showcasing", ["showing", "demonstrating"]),
    (r"leverages", ["uses", "draws on"]),
    (r"leverage", ["use", "draw on"]),
    (r"leveraging", ["using", "drawing on"]),
    (r"utilizes", ["uses"]), (r"utilises", ["uses"]),
    (r"utilized", ["used"]), (r"utilised", ["used"]),
    (r"utilizing", ["using"]), (r"utilising", ["using"]),
    (r"utilize", ["use"]), (r"utilise", ["use"]),
    (r"utili[sz]ation", ["use"]),
    (r"fosters", ["encourages", "supports"]),
    (r"fostering", ["encouraging", "supporting"]),
    (r"foster", ["encourage", "support"]),
    (r"facilitates", ["enables", "supports", "allows"]),
    (r"facilitating", ["enabling", "supporting"]),
    (r"facilitate", ["enable", "support"]),
    (r"navigate the complexities of", ["address", "work through"]),
    (r"navigating the complexities of", ["addressing", "working through"]),
    (r"harness the power of", ["draw on", "make use of"]),
    (r"harnesses the power of", ["draws on", "makes use of"]),
    (r"paves the way for", ["makes possible", "prepares the ground for"]),
    (r"pave the way for", ["make possible", "prepare the ground for"]),
    (r"(?:stands as|is|serves as) a testament to", ["demonstrates", "attests to"]),
    (r"(?:stand as|are|serve as) a testament to", ["demonstrate", "attest to"]),
    # Role/landscape cliches.
    (r"plays an? (?:crucial|pivotal|vital|key|significant|important|critical|central|essential|instrumental|fundamental) role in", ["is central to", "contributes to", "matters for"]),
    (r"play an? (?:crucial|pivotal|vital|key|significant|important|critical|central|essential|instrumental|fundamental) role in", ["are central to", "contribute to", "matter for"]),
    (r"played an? (?:crucial|pivotal|vital|key|significant|important|critical|central|essential|instrumental|fundamental) role in", ["was central to", "contributed to"]),
    (r"(?:in|within) the realm of", ["in", "within"]),
    (r"the (?:ever-(?:changing|evolving) |rapidly evolving |evolving )?landscape of", ["the field of", "the state of"]),
    (r"a (?:rich )?tapestry of", ["a range of", "a mixture of"]),
    # Inflated modifiers.
    (r"ever-(?:evolving|changing)", ["changing", "shifting"]),
    (r"multifaceted", ["complex", "many-sided"]),
    (r"pivotal", ["central", "decisive"]),
    (r"crucial", ["important", "essential", "necessary"]),
    (r"robust", ["strong", "reliable", "sound"]),
    (r"comprehensive", ["thorough", "full", "detailed"]),
    (r"nuanced", ["subtle", "qualified", "fine-grained"]),
    (r"intricate", ["complex", "detailed"]),
    (r"seamlessly", ["smoothly", "without difficulty"]),
    (r"seamless", ["smooth", "uninterrupted"]),
    (r"meticulously", ["carefully", "closely"]),
    (r"meticulous", ["careful", "close"]),
    (r"groundbreaking", ["original", "influential"]),
    (r"transformative", ["far-reaching", "substantial"]),
    (r"holistic", ["integrated", "whole-system"]),
    (r"vibrant", ["active", "lively"]),
    (r"a (?:myriad|plethora|multitude|wide (?:range|array|variety)) of", ["many", "various", "numerous"]),
    (r"myriad", ["many", "numerous"]),
    # Wordy connectives.
    (r"in order to", ["to"]),
    (r"due to the fact that", ["because"]),
    (r"in light of the fact that", ["because", "given that"]),
    (r"despite the fact that", ["although"]),
    (r"(?:has|have) the (?:potential|ability|capacity) to", ["can", "may"]),
    (r"with (?:regard|respect) to", ["regarding", "on", "concerning"]),
    (r"when it comes to", ["regarding", "in"]),
    (r"at the end of the day,?", ["ultimately,"]),
    (r"a (?:significant|substantial|considerable|large) (?:number|amount) of", ["many", "much of the", "numerous"]),
]

# Sentence-initial transitions that detectors and readers both notice when
# they open sentence after sentence. Each maps to formal alternatives; ""
# drops the transition and lets the sentence stand on its own.
OPENERS: dict[str, list[str]] = {
    "moreover": ["", "", "In addition,", "Further,"],
    "furthermore": ["", "", "In addition,", "Beyond this,"],
    "additionally": ["", "", "Further,", "Also,"],
    "in addition": ["", "Further,"],
    "consequently": ["As a result,", "", "For this reason,"],
    "notably": ["", "In particular,"],
    "importantly": ["", ""],
    "ultimately": ["", "In the end,"],
    "overall": ["", "On balance,", "Taken together,"],
    "in conclusion": ["Taken together,", "On this evidence,", ""],
    "in summary": ["Taken together,", "In short,", ""],
    "to summarize": ["In short,", ""],
    "in essence": ["", "In short,"],
    "indeed": ["", ""],
    "firstly": ["First,"],
    "secondly": ["Second,"],
    "thirdly": ["Third,"],
    "lastly": ["Finally,"],
}

# Flag-only patterns: reported by the analyzer but too structure-dependent
# to rewrite safely with rules (the LLM pass handles them).
FLAG_ONLY: list[tuple[str, str]] = [
    (r"\bnot only\b.{1,120}?\bbut also\b", "not only ... but also"),
    (r"\bnot (?:just|merely|simply)\b.{1,80}?\bbut\b", "not just ... but"),
    (r"\b(?:this|these|it)\b[^.]{0,40}\b(?:highlights?|emphasi[sz]es?)\s+the\s+(?:importance|need|significance)\b", "highlights the importance of"),
    (r"\bboth\b[^.]{1,60}\band\b[^.]{1,60}\balike\b", "both X and Y alike"),
    (r"\bserves as a (?:reminder|catalyst|cornerstone|foundation|bridge)\b", "serves as a ..."),
    (r"\bis (?:not|more than) (?:just|merely) a\b", "is not merely a"),
    (r"\bthe (?:importance|significance|role) of\b[^.]{1,60}\bcannot be overstated\b", "cannot be overstated"),
]

# First words that are always safe to lower-case when two sentences are joined.
LOWERABLE = {
    "The", "This", "These", "Those", "That", "It", "Its", "They", "Their",
    "Such", "A", "An", "In", "On", "At", "By", "For", "With", "Without",
    "Each", "Some", "Many", "Most", "Both", "There", "Here", "One", "Other",
    "Several", "Few", "No", "All", "When", "While", "Where", "If", "As",
}
