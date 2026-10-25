"""Patch 19: the Plan Notepad (notes API, calculation engine, calculator API). Safe to run twice. Needs patch 18."""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('.')
settings = ROOT / 'config/settings.py'
urls = ROOT / 'config/urls.py'
for f in (settings, urls):
    if not f.exists():
        sys.exit(f'STOP: {f} not found')

text = settings.read_text()
if "'notepad'" not in text:
    old = "'accounts', 'content', 'practice', 'calculations', 'planning', 'learning', 'discovery',"
    if text.count(old) != 1:
        sys.exit('STOP: INSTALLED_APPS line looks different from what this patch expects. Nothing was changed.')
    settings.write_text(text.replace(old, old[:-1] + ", 'notepad',", 1))

text = urls.read_text()
EDITS = [
    ("from learning import api as learning_api\n", "from learning import api as learning_api\nfrom notepad import api as notepad_api\n", 'notepad_api'),
    ("    path('admin/', admin_site.urls),",
     "    path('api/v1/notes/', notepad_api.notes, name='api-notes'),\n"
     "    path('api/v1/notes/for-context/', notepad_api.for_context, name='api-notes-context'),\n"
     "    path('api/v1/notes/<uuid:uid>/', notepad_api.note_detail, name='api-note'),\n"
     "    path('api/v1/notes/<uuid:uid>/duplicate/', notepad_api.duplicate, name='api-note-duplicate'),\n"
     "    path('api/v1/notes/<uuid:uid>/versions/', notepad_api.versions, name='api-note-versions'),\n"
     "    path('api/v1/notes/<uuid:uid>/versions/<int:number>/restore/', notepad_api.restore, name='api-note-restore'),\n"
     "    path('api/v1/notes/<uuid:uid>/export/', notepad_api.export, name='api-note-export'),\n"
     "    path('api/v1/calc/compound/', notepad_api.calc_compound, name='api-calc-compound'),\n"
     "    path('api/v1/calc/compare/', notepad_api.calc_compare, name='api-calc-compare'),\n"
     "    path('admin/', admin_site.urls),", "name='api-notes'"),
]
for old, new, done in EDITS:
    if done in text:
        continue
    if text.count(old) != 1:
        sys.exit(f'STOP: expected text not found exactly once in config/urls.py: {old[:60]!r}. Nothing was changed. (Patch 18 must be installed first.)')
    text = text.replace(old, new, 1)
urls.write_text(text)
print('Patch 19 edits applied.')
