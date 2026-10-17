from django.core.management.base import BaseCommand, CommandError

from content.studio import ai


class Command(BaseCommand):
    help = 'Makes one tiny request to the AI service to prove the key and model work. Costs a fraction of a cent.'

    def handle(self, *args, **options):
        if not ai.configured():
            raise CommandError('ANTHROPIC_API_KEY is not set in this shell. Load the env file first.')
        tool = {'name': 'submit_draft', 'description': 'Submit the reply.', 'input_schema': {
            'type': 'object', 'required': ['reply'], 'properties': {'reply': {'type': 'string'}}}}
        try:
            result = ai.call_model('You are a connection test. Call the tool.', 'Reply with the single word: ready', tool, 100)
        except ai.AIError as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS(f'AI assistant works. Model: {ai.model_name()}. Reply: {str(result.get("reply", ""))[:40]}'))
