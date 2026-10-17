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

urlpatterns = [
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
    path('admin/', admin_site.urls),
]
