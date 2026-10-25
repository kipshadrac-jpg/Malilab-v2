from django.urls import path
from django.views.decorators.cache import never_cache
from config.admin_site import admin_site
from config.cache_policy import private_for_signed_in
from content import views as content_views
from accounts import views as account_views
from practice import views as practice_views
from learning import views as learning_views
from planning import views as planning_views
from discovery import views as discovery_views
from learning import staff_views
from learning import lesson_views
from accounts import registration_views as signup
from content.studio import views as studio
from content.studio import ai_views as studio_ai
from content.studio import cover_views as studio_cover
from content import media_views
from content import api as content_api
from content import api_modules as content_api_modules
from accounts import api as account_api
from learning import api as learning_api
from learning import practice_api
from billing import api as billing_api
from billing import views as billing_views
from billing import ads as billing_ads
from notepad import api as notepad_api

urlpatterns = [
    path('app-ads.txt', billing_ads.app_ads, name='app-ads'),
    path('sign-in/', never_cache(account_views.sign_in), name='sign-in'),
    path('sign-out/', never_cache(account_views.sign_out), name='sign-out'),
    path('register/', never_cache(signup.register), name='register'),
    path('enter-code/', never_cache(signup.enter_code), name='enter-code'),
    path('check-email/', never_cache(signup.check_email), name='check-email'),
    path('forgot-password/', never_cache(signup.forgot_password), name='forgot-password'),
    path('', private_for_signed_in(content_views.home), name='home'),
    path('playbooks/', private_for_signed_in(content_views.playbook_list), name='playbook-list'),
    path('playbooks/<slug:slug>/', private_for_signed_in(content_views.playbook_detail), name='playbook-detail'),
    path('modules/', private_for_signed_in(content_views.module_list), name='module-list'),
    path('modules/<slug:slug>/', private_for_signed_in(content_views.module_detail), name='module-detail'),
    path('modules/<slug:slug>/completion/', never_cache(learning_views.record_module_completion), name='module-completion'),
    path('lessons/<slug:slug>/', private_for_signed_in(content_views.lesson_detail), name='lesson-detail'),
    path('lessons/<slug:slug>/complete/', never_cache(lesson_views.complete), name='lesson-complete'),
    path('lessons/<slug:slug>/notes/', never_cache(learning_views.notes), name='lesson-notes'),
    path('notes/', never_cache(learning_views.notes), name='notes'),
    path('notes/<int:note_id>/source/', never_cache(learning_views.note_source), name='note-source'),
    path('progress/', never_cache(learning_views.progress), name='progress'),
    path('my-plan/', never_cache(planning_views.my_plans), name='my-plans'),
    path('my-plan/<int:plan_id>/', never_cache(planning_views.plan_revisions), name='plan-revisions'),
    path('search/', private_for_signed_in(discovery_views.search), name='search'),
    path('practice/<slug:slug>/', private_for_signed_in(practice_views.activity), name='practice-activity'),
    path('practice/<slug:slug>/attempts/', never_cache(practice_views.start), name='practice-start'),
    path('practice/attempts/<int:attempt_id>/', never_cache(practice_views.attempt), name='practice-attempt'),
    path('practice/attempts/<int:attempt_id>/responses/', never_cache(practice_views.save), name='practice-save'),
    path('practice/attempts/<int:attempt_id>/submit/', never_cache(practice_views.submit), name='practice-submit'),
    path('practice/attempts/<int:attempt_id>/submitted/', never_cache(practice_views.submitted), name='practice-submitted'),
    path('practice-unavailable/', private_for_signed_in(practice_views.unavailable), name='practice-unavailable'),
    path('staff/evaluations/', never_cache(staff_views.queue), name='staff-evaluations'),
    path('staff/evaluations/<int:attempt_id>/', never_cache(staff_views.detail), name='staff-evaluation'),
    path('studio/', studio.home, name='studio-home'),
    path('studio/ai/', studio_ai.start, name='studio-ai'),
    path('studio/playbook/<int:rev_id>/cover/', studio_cover.cover, name='studio-cover'),
    path('media/cover/<slug:key>/', media_views.cover_image, name='cover-image'),
    path('studio/new/<slug:kind>/', studio.create, name='studio-new'),
    path('studio/<slug:kind>/<int:rev_id>/', studio.revision, name='studio-revision'),
    path('studio/<slug:kind>/<int:rev_id>/edit/', studio.edit, name='studio-edit'),
    path('studio/<slug:kind>/<int:rev_id>/<slug:name>/', studio.act, name='studio-act'),
    path('api/v1/playbooks/', content_api.playbook_list, name='api-playbooks'),
    path('api/v1/playbooks/<slug:slug>/', content_api.playbook_detail, name='api-playbook'),
    path('api/v1/modules/', content_api_modules.module_list, name='api-modules'),
    path('api/v1/modules/<slug:slug>/', content_api_modules.module_detail, name='api-module'),
    path('api/v1/account/code/', account_api.ask_code, name='api-account-code'),
    path('api/v1/account/verify/', account_api.verify_code, name='api-account-verify'),
    path('api/v1/account/signin/', account_api.sign_in, name='api-account-signin'),
    path('api/v1/account/signout/', account_api.sign_out, name='api-account-signout'),
    path('api/v1/account/me/', account_api.me, name='api-account-me'),
    path('api/v1/lessons/<slug:slug>/', learning_api.lesson_detail, name='api-lesson'),
    path('api/v1/lessons/<slug:slug>/complete/', learning_api.complete_lesson, name='api-lesson-complete'),
    path('api/v1/progress/', learning_api.progress, name='api-progress'),
    path('unlock/', never_cache(billing_views.unlock), name='unlock'),
    path('unlock/waiting/<int:payment_id>/', never_cache(billing_views.waiting), name='unlock-waiting'),
    path('unlock/status/<int:payment_id>/', never_cache(billing_views.payment_status), name='unlock-status'),
    path('api/v1/billing/status/', billing_api.status, name='api-billing-status'),
    path('api/v1/billing/pay/', billing_api.pay, name='api-billing-pay'),
    path('api/v1/billing/payments/', billing_api.payment_list, name='api-billing-payments'),
    path('api/v1/billing/payments/<int:payment_id>/', billing_api.payment_detail, name='api-billing-payment'),
    path('api/v1/billing/mpesa/callback/<str:secret>/', billing_api.mpesa_callback, name='api-billing-callback'),
    path('api/v1/practice/', practice_api.history, name='api-practice-history'),
    path('api/v1/practice/attempts/<int:attempt_id>/', practice_api.attempt_detail, name='api-practice-attempt'),
    path('api/v1/practice/attempts/<int:attempt_id>/answers/<slug:question_id>/', practice_api.answer, name='api-practice-answer'),
    path('api/v1/practice/attempts/<int:attempt_id>/submit/', practice_api.submit, name='api-practice-submit'),
    path('api/v1/practice/<slug:slug>/', practice_api.detail, name='api-practice'),
    path('api/v1/practice/<slug:slug>/attempts/', practice_api.start, name='api-practice-start'),
    path('api/v1/notes/', notepad_api.notes, name='api-notes'),
    path('api/v1/notes/for-context/', notepad_api.for_context, name='api-notes-context'),
    path('api/v1/notes/<uuid:uid>/', notepad_api.note_detail, name='api-note'),
    path('api/v1/notes/<uuid:uid>/duplicate/', notepad_api.duplicate, name='api-note-duplicate'),
    path('api/v1/notes/<uuid:uid>/versions/', notepad_api.versions, name='api-note-versions'),
    path('api/v1/notes/<uuid:uid>/versions/<int:number>/restore/', notepad_api.restore, name='api-note-restore'),
    path('api/v1/notes/<uuid:uid>/export/', notepad_api.export, name='api-note-export'),
    path('api/v1/calc/compound/', notepad_api.calc_compound, name='api-calc-compound'),
    path('api/v1/calc/compare/', notepad_api.calc_compare, name='api-calc-compare'),
    path('api/v1/calc/instrument/', notepad_api.calc_instrument, name='api-calc-instrument'),
    path('api/v1/calc/rules/', notepad_api.calc_rules, name='api-calc-rules'),
    path('admin/', admin_site.urls),
]
