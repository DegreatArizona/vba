from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap 
from .views import account_verification_view



sitemaps = {
    # 'articles': ArticleSitemap,
    'static': StaticViewSitemap,

}

urlpatterns=[
    path('', views.index, name='index'),
    path('login', views.loginUser, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.user_logout, name='logout'),
    path('afterlogin', TemplateView.as_view(template_name='mechanic_wait_for_approval.html'),name='afterlogin'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("OneSignalSDKWorker.js", TemplateView.as_view(template_name="OneSignalSDKWorker.js", content_type="application/javascript")),
    path("state.json", TemplateView.as_view(template_name="state.json", content_type="application/json")),
    path("service-worker.js", TemplateView.as_view(template_name="service-worker.js", content_type="application/javascript")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('chatbot/', views.query_view, name='query'),
    path("verify-account/", account_verification_view, name="account_verification"),
    path('api/update-mechanic-location/<int:request_id>/', views.update_mechanic_location, name='update-mechanic-location'),
    path('api/get-mechanic-location/<int:request_id>/', views.get_mechanic_location, name='get-mechanic-location'),
    path('korapay-webhook/', views.korapay_webhook, name='korapay_webhook'),
    path('fund-virtual-account/<int:driver_id>/<int:amount>/', views.fund_virtual_account, name='fund_virtual_account'),
    path('create-virtual-account/<int:driver_id>/', views.create_virtual_account, name='create_virtual_account'),
    path('notify/', views.notify_users, name='notify_users'),
    path('managers/', views.managers, name='managers'),
    path('api/mechanic-managers/', views.mechanic_managers, name='mechanic_managers'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),
    path('go-pro/', views.goPro, name='pro'),

    ##################################
    #             Driver           #
    ##################################
    path('driver-dashboard', views.driverDashboard, name='driver-dashboard'),
    path('driver-request-history', views.requestHistory, name='driver-request-history'),
    path('driver-request-service', views.requestService, name='driver-request-service'),
    path('driver-notification/', views.driverNotification, name='driver-notification'),
    path('driver-request-detail/<int:request_id>/', views.requestDetail, name='request-detail'),
    path('driver-request-edit/<int:request_id>/', views.requestEdit, name='request-edit'),
    path('driver-request-delete/<int:request_id>/', views.requestDelete, name='request-delete'),
    path('driver-request-cancel/<int:request_id>/', views.requestCancel, name='request-cancel'),
    path('driver-invoice-history/', views.invoiceHistory, name='driver-invoice-history'),
    path('driver-invoice/<int:request_id>', views.driverInvoice, name='driver-invoice'),
    path('driver-profile', views.driverProfile, name='driver-profile'),
    path('driver-track-mechanic/<int:request_id>/', views.driverTrack, name='driver-track-mechanic'),
    path('driver-pro-request', views.proRequest, name='driver-pro-request'),
    path('driver-pro-request-send/<int:mechanic_id>/', views.proRequestSend, name='driver-pro-request-send'),
    path('driver-fund-wallet', views.driverFund, name='driver-fund-wallet'),

    ##################################
    #             Mechanic           #
    ##################################
    path('mechanic-dashboard', views.mechanicDashboard, name='mechanic-dashboard'),
    path('mechanic-job-history', views.mechanicHistory, name='mechanic-job-history'),
    path('mechanic-earning', views.mechanicEarning, name='mechanic-earning'),
    path('mechanic-withdraw', views.mechanicWithdraw, name='mechanic-withdraw'),
    path('mechanic-monthly-earning/<int:mechanic_id>/', views.mechanicMonthlyEarning, name='mechanic-monthly-earning'),
    path('mechanic-request-accept/<int:request_id>/', views.mechanicAccept, name='mechanic-request-accept'),
    path('mechanic-request-update/<int:request_id>/', views.mechanicUpdate, name='mechanic-request-update'),
    path('mechanic-request-release/<int:request_id>/', views.mechanicRelease, name='mechanic-request-release'),
    path('mechanic-request-done/<int:request_id>/', views.mechanicDone, name='mechanic-request-done'),
    path('mechanic-request-cancel/<int:request_id>/', views.mechanicCancel, name='mechanic-request-cancel'),
    path('mechanic-profile', views.mechanicProfile, name='mechanic-profile'),
    path('driver-pro-request-send/<int:mechanic_id>/', views.proRequestSend, name='driver-pro-request-send'),

    ##################################
    #             Manager            #
    ##################################
    path('manager-dashboard', views.managerDashboard, name='manager-dashboard'),
    path('manager-job-history', views.managerHistory, name='manager-job-history'),
    path('manager-earning', views.managerEarning, name='manager-earning'),
    path('manager-withdraw', views.managerWithdraw, name='manager-withdraw'),
    path('manager-monthly-earning/<int:manager_id>/', views.managerMonthlyEarning, name='manager-monthly-earning'),
    path('manager-request-accept/<int:request_id>/', views.managerAccept, name='manager-request-accept'),
    path('manager-request-update/<int:request_id>/', views.managerUpdate, name='manager-request-update'),
    path('manager-request-release/<int:request_id>/', views.managerRelease, name='manager-request-release'),
    path('manager-request-done/<int:request_id>/', views.managerDone, name='manager-request-done'),
    path('manager-request-cancel/<int:request_id>/', views.managerCancel, name='manager-request-cancel'),
    path('manager-profile', views.managerProfile, name='manager-profile'),
    path('manager-register', views.managerRegister, name='manager-register'),
    path('manager-mechanic', views.managerMechanic, name='manager-mechanic'),
    path('manager-onboard', views.managerOnboard, name='manager-onboard'),
    path('manager-approve/<int:mechanic_id>/', views.managerApprove, name='manager-approve'),
]

