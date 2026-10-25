"""Create two published sample practice activities and a sample module that requires them (safe to re-run)."""
from django.core.management.base import BaseCommand

from content.models import Module, ModuleLearningRequirement, ModuleRevision, PracticeActivity, PracticeActivityRevision

BUDGET = {'schema_version': 1, 'questions': [
    {'id': 'income', 'type': 'decimal_amount', 'label': 'What is your take-home income in a typical month?', 'required': True, 'constraints': {'currency': 'KES', 'minimum': '0'}},
    {'id': 'rent', 'type': 'decimal_amount', 'label': 'How much goes to rent and utilities?', 'required': True, 'constraints': {'currency': 'KES', 'minimum': '0'}},
    {'id': 'dependants', 'type': 'integer', 'label': 'How many people depend on this income (including you)?', 'required': True, 'constraints': {'minimum': 1, 'maximum': 30}},
    {'id': 'biggest', 'type': 'single_choice', 'label': 'Which cost surprises you most each month?', 'required': True,
     'options': [{'id': 'food', 'label': 'Food'}, {'id': 'transport', 'label': 'Transport'}, {'id': 'airtime', 'label': 'Airtime and data'}, {'id': 'other', 'label': 'Something else'}]},
    {'id': 'habits', 'type': 'multiple_choice', 'label': 'Which of these do you already do?', 'required': False,
     'options': [{'id': 'track', 'label': 'Track spending'}, {'id': 'save', 'label': 'Save on payday'}, {'id': 'envelope', 'label': 'Use separate wallets or envelopes'}]},
    {'id': 'plan', 'type': 'short_text', 'label': 'One change you will make this month', 'required': True, 'constraints': {'max_length': 140}},
]}
FUND = {'schema_version': 1, 'questions': [
    {'id': 'target_months', 'type': 'integer', 'label': 'How many months of expenses do you want in your emergency fund?', 'required': True, 'constraints': {'minimum': 1, 'maximum': 24}},
    {'id': 'monthly_expenses', 'type': 'decimal_amount', 'label': 'Your essential monthly expenses', 'required': True, 'constraints': {'currency': 'KES', 'minimum': '0'}},
    {'id': 'monthly_saving', 'type': 'decimal_amount', 'label': 'How much can you set aside each month?', 'required': True, 'constraints': {'currency': 'KES', 'minimum': '0'}},
    {'id': 'where', 'type': 'single_choice', 'label': 'Where would you keep it?', 'required': True,
     'options': [{'id': 'mmf', 'label': 'Money market fund'}, {'id': 'sacco', 'label': 'SACCO'}, {'id': 'bank', 'label': 'Savings account'}, {'id': 'tbill', 'label': 'Treasury bills'}]},
    {'id': 'reflection', 'type': 'long_text', 'label': 'What could stop you from reaching it, and what will you do about that?', 'required': False, 'constraints': {'max_length': 2000}},
]}


def publish(revision, identity):
    revision.status = 'published'
    revision._allow_lifecycle_transition = True
    revision.save()
    identity.current_published_revision = revision
    identity.status = 'published'
    identity._allow_pointer_update = True
    identity.save()


def make_activity(slug, title, instructions, prompt, schema, tool_refs):
    if PracticeActivity.objects.filter(slug=slug).exists():
        return PracticeActivity.objects.get(slug=slug).current_published_revision
    activity = PracticeActivity.objects.create(slug=slug)
    revision = PracticeActivityRevision.objects.create(
        activity=activity, revision_number=1, title=title, instructions=instructions, prompt=prompt,
        response_schema=schema, tool_refs=tool_refs, safety_text='Sample activity for testing. Educational only, not financial advice.')
    publish(revision, activity)
    return revision


class Command(BaseCommand):
    help = 'Create sample practice activities and a sample module (does nothing if they exist).'

    def handle(self, *args, **options):
        budget = make_activity('sample-monthly-budget', '[Sample] Your monthly budget',
                               'Answer from your own month. Nothing here is shared.', 'Write down the real numbers, not the ideal ones.',
                               BUDGET, [{'tool': 'calculator', 'model': 'compound', 'label': 'Open the savings calculator'}])
        fund = make_activity('sample-emergency-fund', '[Sample] Plan your emergency fund',
                             'Decide how big a cushion you want and where it will live.', 'Be honest about what you can set aside.',
                             FUND, [{'tool': 'calculator', 'model': 'mmf', 'label': 'Try a money market fund'},
                                    {'tool': 'calculator', 'model': 'compound', 'label': 'Savings growth'}])
        if not Module.objects.filter(slug='sample-practice-module').exists():
            module = Module.objects.create(slug='sample-practice-module')
            revision = ModuleRevision.objects.create(module=module, revision_number=1, title='[Sample] Practice sampler',
                                                     description='A small module to try the practice activities.')
            ModuleLearningRequirement.objects.create(module_revision=revision, target_kind='practice', practice_revision=budget, classification='required', position=1)
            ModuleLearningRequirement.objects.create(module_revision=revision, target_kind='practice', practice_revision=fund, classification='optional', position=2)
            publish(revision, module)
        if options.get('verbosity', 1) > 0:
            self.stdout.write(self.style.SUCCESS('Sample practice content is ready.'))
