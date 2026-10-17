"""Ask the model to choose a cover from the fixed art options (it never draws anything itself)."""
from content import covers
from . import ai

DESCRIPTIONS = {
    'coins': 'a stack of coins', 'growth': 'rising bars with an upward arrow', 'sprout': 'a sprout growing beside two coins',
    'shield': 'a shield with a tick', 'house': 'a small house', 'phone': 'a phone with arrows moving money in and out',
    'scales': 'balance scales', 'target': 'a target with an arrow', 'pie': 'a pie chart', 'calendar': 'a calendar with marked days'}

SYSTEM = """You choose the cover picture for a MaliLab playbook (a short guided path of learning about money in Kenya). You do not draw. You pick one option from each fixed list so the picture suits the playbook's subject, and you describe the finished picture for a screen reader.
- motif: the main symbol. Pick the one that best fits the subject.
- palette: the colour set. Vary colours between playbooks; prefer calm, trustworthy choices for debt, risk or protection, and warm ones for starting out or growth.
- pattern: the background texture.
- alt_text: one plain sentence (under 140 characters) that describes what the picture SHOWS, for example "Illustration of a sprout growing beside two coins". Do not repeat the title and do not describe feelings.
Reply only by calling the submit_draft tool."""


def tool():
    return {'name': 'submit_draft', 'description': 'Submit the cover choices.', 'input_schema': {
        'type': 'object', 'required': ['motif', 'palette', 'pattern', 'alt_text'], 'properties': {
            'motif': {'type': 'string', 'enum': list(covers.MOTIFS)},
            'palette': {'type': 'string', 'enum': list(covers.PALETTES)},
            'pattern': {'type': 'string', 'enum': list(covers.PATTERNS)},
            'alt_text': {'type': 'string'}}}}


def design(revision, user):
    """Return {'motif','palette','pattern','alt_text'}, every value checked against the fixed lists."""
    if ai.throttled(user):
        raise ai.AIError('You have used the hourly limit for AI requests. Please try again later.')
    options = '\n'.join(f'- {m}: {DESCRIPTIONS[m]}' for m in covers.MOTIFS)
    prompt = (f'Playbook title: {revision.title}\nSummary: {revision.summary}\nSituation: {revision.scenario}\n\n'
              f'Motifs:\n{options}\nPalettes: {", ".join(covers.PALETTES)}\nPatterns: {", ".join(covers.PATTERNS)}')
    result = None
    for attempt in range(2):
        try:
            result = ai.call_model(SYSTEM, prompt, tool(), 400)
            break
        except ai.NoDraft:
            if attempt:
                raise
    motif, palette, pattern = (result.get(k) for k in ('motif', 'palette', 'pattern'))
    if motif not in covers.MOTIFS or palette not in covers.PALETTES or pattern not in covers.PATTERNS:
        raise ai.AIError('The AI picked a design that does not exist. Please try again.')
    alt = ' '.join(str(result.get('alt_text') or '').split())
    if not 10 <= len(alt) <= 200:
        alt = f'Illustration of {DESCRIPTIONS[motif]}'
    return {'motif': motif, 'palette': palette, 'pattern': pattern, 'alt_text': alt}
