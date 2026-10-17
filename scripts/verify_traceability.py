"""Check that each Phase 6A model has an explicit requirement/test trace."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.apps import apps

TRACE = {
 'accounts.UserAccount': ('ACCOUNTS', 'accounts/tests.py'),
 'content.Playbook': ('EDITORIAL', 'content/tests.py'),
 'content.PlaybookRevision': ('EDITORIAL', 'content/tests.py'),
 'content.Module': ('EDITORIAL', 'content/tests.py'),
 'content.ModuleRevision': ('EDITORIAL', 'content/tests.py'),
 'content.Lesson': ('EDITORIAL', 'content/tests.py'),
 'content.LessonRevision': ('EDITORIAL', 'content/tests.py'),
 'content.PracticeActivity': ('PRACTICE', 'practice/tests.py'),
 'content.PracticeActivityRevision': ('PRACTICE', 'practice/tests.py'),
 'content.ModuleLearningRequirement': ('PROGRESS', 'learning/tests.py'),
 'content.PlaybookModuleRecommendation': ('EDITORIAL', 'content/tests.py'),
 'content.RelatedContentRelationship': ('EDITORIAL', 'content/tests.py'),
 'content.ContentTopicAssignment': ('DISCOVERY', 'content/tests.py'),
 'content.Topic': ('DISCOVERY', 'content/tests.py'),
 'content.AchievementDefinition': ('ACHIEVEMENTS', 'learning/tests.py'),
 'content.AchievementDefinitionRevision': ('ACHIEVEMENTS', 'learning/tests.py'),
 'content.Source': ('PROVENANCE', 'content/tests.py'),
 'content.SourceSnapshot': ('PROVENANCE', 'content/tests.py'),
 'content.EditorialReview': ('GOVERNANCE', 'content/tests.py'),
 'content.PublicationEvent': ('GOVERNANCE', 'content/tests.py'),
 'content.MediaAsset': ('MEDIA', 'content/tests.py'),
 'practice.PracticeAttempt': ('OWNERSHIP', 'practice/tests.py'),
 'practice.PracticeResponse': ('OWNERSHIP', 'practice/tests.py'),
 'calculations.LabTool': ('CALCULATIONS', 'calculations/tests.py'),
 'calculations.CalculatorDefinition': ('CALCULATIONS', 'calculations/tests.py'),
 'calculations.FormulaVersion': ('CALCULATIONS', 'calculations/tests.py'),
 'calculations.FormulaApproval': ('GOVERNANCE', 'calculations/tests.py'),
 'calculations.CalculationResult': ('OWNERSHIP', 'calculations/tests.py'),
 'planning.MyPlan': ('PLANNING', 'planning/tests.py'),
 'planning.PlanRevision': ('PLANNING', 'planning/tests.py'),
 'learning.LearningJourney': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyTargetRef': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyStep': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyPlaybookTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyModuleTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyLessonTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyPracticeTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyAttemptTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyCalculationTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.JourneyPlanTarget': ('JOURNEY', 'learning/tests.py'),
 'learning.Note': ('NOTES', 'learning/tests.py'),
 'learning.LessonCompletion': ('PROGRESS', 'learning/tests.py'),
 'learning.RequirementEvidence': ('PROGRESS', 'learning/tests.py'),
 'learning.ModuleCompletion': ('PROGRESS', 'learning/tests.py'),
 'learning.UserAchievement': ('ACHIEVEMENTS', 'learning/tests.py'),
 'discovery.SearchProjection': ('SEARCH', 'discovery/tests.py'),
}
models={m._meta.label for m in apps.get_models() if m._meta.app_label in {'accounts','content','practice','calculations','planning','learning','discovery'}}
missing=models-set(TRACE)
extra=set(TRACE)-models
assert not missing, f'Models missing requirement/test trace: {sorted(missing)}'
assert not extra, f'Trace entries with missing models: {sorted(extra)}'
for requirement, test_path in TRACE.values():
    assert requirement and os.path.isfile(test_path), f'Missing requirement or test: {requirement} {test_path}'
print(f'Traceability PASS: {len(models)} Phase 6A models mapped to requirements and test files.')
