from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('car/<int:cat_id>/', views.car_detail, name='car_detail'),
    path('cat/<int:cat_id>/', views.cat_detail, name='cat_detail'),
    path('user_cat/<int:cat_id>/', views.user_cat_detail, name='user_cat_detail'),
    path('user_car/<int:cat_id>/', views.user_car_detail, name='user_car_detail'),
    path('login/', views.CustomLoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),  # اضافه کردن ویوی ثبت‌نام
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('user_detail/<int:user_id>', views.user_detail, name='user_detail'),
    path('manage-cars/', views.manage_cars, name='manage_cars'),
    path('manage-issues/', views.manage_issues, name='manage_issues'),
    path('manage_issues_categories/', views.manage_issue_categories, name='manage_issue_categories'),



    
    path('manage-solutions/', views.manage_solutions, name='manage_solutions'),
    path('manage-subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
    path('search/', views.search_webapp, name='search'),  # برای جستجوی 
    
     
    path('issue/<int:issue_id>/', views.issue_detail, name='issue_detail'),

    path('step/<int:step_id>/', views.step_detail, name='step_detail'),
    path('user_step/<int:step_id>/', views.user_step_detail, name='user_step_detail'),
    
    
    path('user_issue/<int:issue_id>/', views.user_issue_detail, name='user_issue_detail'),
    path('user_article/<int:article_id>/', views.user_article_detail, name='user_article_detail'),
    path('issue_categories/create/', views.issue_category_create, name='issue_category_create'),
    path('add_subcategory/', views.add_subcategory, name='issue_category_create'),
    path('issue_categories/update/<int:category_id>/', views.issue_category_update, name='issue_category_update'),
    path('issue_categories/delete/<int:category_id>/', views.issue_category_delete, name='issue_category_delete'),


    path('issue/<int:issue_id>/solutions/create/', views.issue_solution_create, name='issue_solution_create'),
    path('issues/create/', views.issue_create, name='issue_create'),
    path('cat_issues/create/<int:cat_id>', views.issue_cat_create, name='issue_cat_create'),
    path('issues/update/<int:issue_id>/', views.issue_update, name='issue_update'),
    path('issues/delete/<int:issue_id>/', views.issue_delete, name='issue_delete'),
    path('issue/<int:issue_id>/create-diagnostic-steps/', views.create_diagnostic_steps, name='create_diagnostic_steps'),
    path('diagnostic/<int:issue_id>/', views.diagnostic_process, name='diagnostic_process'),
    path('load_next_step/<int:option_id>/', views.load_next_step, name='load_next_step'),

    
    path('user_solution/<int:solution_id>/', views.user_solution_detail, name='user_solution_detail'),
    path('solution/<int:solution_id>/', views.solution_detail, name='solution_detail'),
    path('solutions/create/', views.solution_create, name='solution_create'),
    path('solutions/update/<int:solution_id>/', views.solution_update, name='solution_update'),
    path('solutions/delete/<int:solution_id>/', views.solution_delete, name='solution_delete'),

    path('subscriptions/create/', views.subscription_create, name='subscription_create'),
    path('subscriptions/update/<int:subscription_id>/', views.subscription_update, name='subscription_update'),
    path('subscriptions/delete/<int:subscription_id>/', views.subscription_delete, name='subscription_delete'),

    path('bookmarks/', views.manage_bookmarks, name='manage_bookmarks'),
    path('bookmarks/create/', views.bookmark_create, name='bookmark_create'),
    path('bookmarks/delete/<int:bookmark_id>/', views.bookmark_delete, name='bookmark_delete'),

    path('issue/<int:issue_id>/option/<str:option_id>/<int:order>/diagnostic-steps/', views.option_diagnostic_steps, name='option_diagnostic_steps'),
    path('question/create_question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/add_option/', views.create_option, name='create_option'),




    path('api/get_solutions/<int:issue_id>', views.get_solutions, name='get_solutions'),
    path('api/get_selected_solutions/<int:issue_id>', views.get_selected_solutions, name='get_selected_solutions'),
    path('api/update_selection/', views.update_selection, name='update_selection'),
    path('api/delete_selection/', views.delete_selection, name='delete_selection'),
    path('api/get_options/<int:question_id>/', views.get_options, name='get_options'),
    path('api/get_step_options/<int:step_id>/', views.get_step_options, name='get_step_options'),
    
    
    path('api/create_question/', views.create_question, name='create_question'),
    path('api/create_step_question/', views.create_step_question, name='create_step_question'),
    
    path('api/add_option/', views.add_option, name='add_option'),
    path('api/update_option/<int:option_id>/', views.update_option, name='update_option'),
    path('api/delete_option/<int:option_id>/', views.delete_option, name='delete_option'),
    path('api/update_question/<int:question_id>/', views.update_question, name='update_question'),
    path('api/delete_question/<int:question_id>/', views.delete_question, name='delete_question'),


    path('api/create_solution/', views.create_solution, name='create_solution'),
    path('api/tags/add/',  views.add_tag, name='add_tag'),
    path('api/get_steps/<int:issue_id>/', views.get_steps, name='get_steps'),
    path('api/categorization/', views.CategorizationView.as_view(), name='categorization'),








    # path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/update/<int:pk>/', views.user_update, name='user_update'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),


    path('api/import_issues/<int:car_id>/', views.import_issues, name='import_issues'),
    path('api/add_map/', views.add_map, name='add_map'),
    path('api/get_maps/', views.get_maps, name='get_maps'),
    path('api/set_solution/', views.set_solution, name='set_solution'),
    path('api/set_map/', views.set_map, name='set_map'),
    path('api/edit_solution/', views.edit_solution, name='edit_solution'),
    path('api/edit_issue/', views.edit_issue, name='edit_issue'),


    path('map/<int:map_id>/', views.map_detail, name='map_detail'),
    path('user_map/<int:map_id>/', views.user_map_detail, name='user_map_detail'),
    path('cat_map/create/<int:cat_id>', views.map_cat_create, name='map_cat_create'),
    path('api/mapcategorization/', views.MapCategorizationView.as_view(), name='mapcategorization'),
    path('manage_maps/', views.manage_maps, name='manage_maps'),
    path('map_categories/update/<int:category_id>/', views.map_category_update, name='map_category_update'),
    path('map_categories/delete/<int:category_id>/', views.map_category_delete, name='map_category_delete'),
    path('mapcat/<int:cat_id>/', views.mapcat_detail, name='mapcat_detail'),

    path('map/update/<int:map_id>/', views.map_update, name='map_update'),
    path('map/delete/<int:map_id>/', views.map_delete, name='map_delete'),
    path('search_maps/', views.search_maps, name='search_maps'),
    path('check_bookmark/', views.check_bookmark, name='check_bookmark'),
    path('bulk/delete/', views.bulk_delete, name='bulk_delete'),
    path('bulk/update/', views.bulk_update_category, name='bulk_update_category'),
    path('import-maps/<int:category_id>/', views.import_maps, name='import_maps'),
    path('plans/', views.subscription_plans, name='subscription_plans'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),


    # تأیید پرداخت
    path('payment/verify/', views.verify_payment, name='verify_payment'),

    path('support-chat/', views.consultants_chat, name='support_chat'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
    path('articles/create/<int:category_id>/', views.article_create, name='article_create'),
    path('articles/update/<int:article_id>/', views.article_update, name='article_update'),
    path('articles/delete/<int:article_id>/', views.article_delete, name='article_delete'),
    path('payment_history/', views.payment_history, name='payment_history'),
    


]
