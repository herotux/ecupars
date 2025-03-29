// Utility Functions
// ================

// مدیریت توکن‌ها و احراز هویت
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        throw new Error('لطفاً ابتدا وارد حساب کاربری خود شوید');
    }

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };

    let response = await fetch(url, { ...options, headers });

    // اگر توکن منقضی شده بود
    if (response.status === 401) {
        try {
            const newToken = await refreshToken();
            headers.Authorization = `Bearer ${newToken}`;
            response = await fetch(url, { ...options, headers });
        } catch (refreshError) {
            console.error('خطا در احیای توکن:', refreshError);
            throw new Error('جلسه کاری شما به پایان رسیده. لطفاً مجدداً وارد شوید.');
        }
    }

    return response;
}

async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        throw new Error('No refresh token available');
    }

    const response = await fetch('https://django-noxeas.chbk.app/api/v1/token/refresh/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh: refreshToken })
    });

    if (!response.ok) {
        throw new Error('Failed to refresh token');
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return data.access;
}

// نمایش و مدیریت نتایج
function displayResults(results, containerId, formatResult) {
    const container = document.getElementById(containerId) || createResultsContainer(containerId);
    container.innerHTML = '';

    if (!results || results.length === 0) {
        container.innerHTML = '<div class="no-results">نتیجه‌ای یافت نشد</div>';
        return;
    }

    const resultsList = document.createElement('ul');
    resultsList.className = 'search-results-list';

    results.forEach(result => {
        const listItem = document.createElement('li');
        listItem.className = 'search-result-item';
        
        // استفاده از تابع formatSearchResult که لینک‌ها را ایجاد می‌کند
        listItem.innerHTML = formatSearchResult(result);
        
        // اضافه کردن رویداد کلیک برای مدیریت بهتر
        const link = listItem.querySelector('.result-link');
        if (link) {
            link.addEventListener('click', (e) => {
                // می‌توانید اینجا رویدادهای اضافه مثل analytics را ثبت کنید
                console.log('User clicked on:', result.type, 'with id:', result.id);
            });
        }
        
        resultsList.appendChild(listItem);
    });

    container.appendChild(resultsList);
}

function createResultsContainer(id) {
    const container = document.createElement('div');
    container.id = id;
    container.className = 'search-results-container';
    document.body.appendChild(container);
    return container;
}

// دسته‌بندی‌ها
// ==========

const categoriesList = document.getElementById('categories-list');

function createCategoryItem(category) {
    const item = document.createElement('li');
    item.className = 'nav-item';
    item.dataset.categoryId = category.id;

    // چک‌باکس
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `checkbox-${category.id}`;
    item.appendChild(checkbox);

    // لیبل
    const label = document.createElement('label');
    label.textContent = category.name;
    label.htmlFor = `checkbox-${category.id}`;
    item.appendChild(label);

    // فلش برای زیرمنوها
    if (category.subcategories?.length > 0) {
        const arrow = document.createElement('i');
        arrow.className = 'fas fa-chevron-left';
        arrow.style.marginLeft = '5px';
        item.appendChild(arrow);
    }

    // زیرمنوها
    if (category.subcategories?.length > 0) {
        const submenu = document.createElement('ul');
        submenu.className = 'nav';
        
        category.subcategories.forEach(subcategory => {
            submenu.appendChild(createCategoryItem(subcategory));
        });
        
        item.appendChild(submenu);
    }

    return item;
}

async function loadCategories() {
    try {
        const response = await fetchWithAuth('https://django-noxeas.chbk.app/api/v1/categories');
        const data = await response.json();

        // پاکسازی لیست موجود
        categoriesList.innerHTML = '';

        // افزودن گزینه جستجوی آزاد
        const searchItem = document.createElement('li');
        searchItem.className = 'nav-item';
        
        const searchCheckbox = document.createElement('input');
        searchCheckbox.type = 'checkbox';
        searchCheckbox.id = 'search-checkbox';
        searchItem.appendChild(searchCheckbox);
        
        const searchLabel = document.createElement('label');
        searchLabel.textContent = 'جستجوی آزاد';
        searchLabel.htmlFor = 'search-checkbox';
        searchItem.appendChild(searchLabel);
        
        categoriesList.appendChild(searchItem);

        // افزودن دسته‌بندی‌ها
        data.forEach(category => {
            categoriesList.appendChild(createCategoryItem(category));
        });

        // نمایش 8 دسته اول در بخش خاص
        const topCategoriesContainer = document.getElementById('top-categories');
        if (topCategoriesContainer) {
            data.slice(0, 8).forEach(category => {
                topCategoriesContainer.appendChild(createCategoryItem(category));
            });
        }

        // مدیریت رویدادهای کلیک
        setupCategoryEvents();

    } catch (error) {
        console.error('خطا در دریافت دسته‌بندی‌ها:', error);
        categoriesList.innerHTML = `<div class="error">${error.message}</div>`;
    }
}

function setupCategoryEvents() {
    document.querySelectorAll('#categories-list .nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.tagName === 'LI' || e.target.tagName === 'LABEL') {
                const li = e.target.tagName === 'LABEL' ? e.target.parentElement : e.target;
                const submenu = li.querySelector('ul');
                const icon = li.querySelector('i');
                
                if (submenu) {
                    if (submenu.style.display === 'block') {
                        submenu.style.display = 'none';
                        if (icon) icon.className = 'fas fa-chevron-left';
                    } else {
                        submenu.style.display = 'block';
                        if (icon) icon.className = 'fas fa-chevron-down';
                    }
                }
            }
        });
    });
}

// جستجو
// =====

const searchInput = document.querySelector('input.form-control');
let searchTimeout;

function formatSearchResult(result) {
    let link, title, content;
    
    switch (result.type) {
        case 'issue':
            link = `/user_issue/${result.data.issue.id}/`;
            title = result.data.issue.title;
            content = result.data.issue.description?.substring(0, 100) || '';
            return `
                <a href="${link}" class="result-link">
                    <div class="result-type issue">خطا</div>
                    <h3>${title}</h3>
                    
                    <div class="category">${result.data.full_category_name || ''}</div>
                </a>
            `;
            
        case 'solution':
            // توجه: step_id باید از داده‌های راهکار استخراج شود
            const stepId = result.data.step_id || 'unknown';
            link = `/user_step/${stepId}/`;
            title = result.data.solution.title;
            content = result.data.solution.description?.substring(0, 100) || '';
            return `
                <a href="${link}" class="result-link">
                    <div class="result-type solution">راه‌حل</div>
                    <h3>${title}</h3>
                   
                    <div class="category">${result.data.full_category_name || ''}</div>
                </a>
            `;
            
        case 'map':
            link = `/user_map/${result.data.map.id}/`;
            title = result.data.map.title;
            return `
                <a href="${link}" class="result-link">
                    <div class="result-type map">نقشه</div>
                    <h3>${title}</h3>
                    <div class="category">${result.data.full_category_name || ''}</div>
                </a>
            `;
            
        case 'article':
            link = `/user_article/${result.data.article.id}/`;
            title = result.data.article.title;
            content = result.data.article.content?.substring(0, 100) || '';
            return `
                <a href="${link}" class="result-link">
                    <div class="result-type article">مقاله</div>
                    <h3>${title}</h3>
                    <p>${content}...</p>
                    <div class="category">${result.data.full_category_name || ''}</div>
                </a>
            `;
            
        default:
            return `<div class="result-link">نوع نتیجه نامشخص</div>`;
    }
}


async function performSearch(query, options = {}) {
    try {
        if (!query || query.length < 2) return;

        const params = new URLSearchParams();
        params.append('query', query);
        
        if (options.filterOption) params.append('filter_option', options.filterOption);
        if (options.categoryId) params.append('category_id', options.categoryId);
        if (options.subcategoryId) params.append('subcategory_id', options.subcategoryId);

        const response = await fetchWithAuth(`https://django-noxeas.chbk.app/api/v1/search/?${params.toString()}`);
        const data = await response.json();

        displayResults(data.results, 'search-results', formatSearchResult);

    } catch (error) {
        console.error('خطا در جستجو:', error);
        const container = document.getElementById('search-results') || createResultsContainer('search-results');
        container.innerHTML = `<div class="error">${error.message}</div>`;
    }
}

// مدیریت رویدادهای جستجو
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = searchInput.value.trim();
        performSearch(query);
    }, 500);
});

// جستجوهای تخصصی
async function searchMaps(query) {
    await performSearch(query, { filterOption: 'maps' });
}

async function searchIssues(query) {
    await performSearch(query, { filterOption: 'issues' });
}

async function searchAdvanced(query, categoryId, subcategoryId) {
    await performSearch(query, { 
        filterOption: 'solutions,issues',
        categoryId,
        subcategoryId
    });
}

// مقداردهی اولیه
// =============

window.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    
    // بررسی وضعیت احراز هویت
    if (!localStorage.getItem('access_token')) {
        console.warn('کاربر وارد نشده است');
        // میتوانید کاربر را به صفحه لاگین هدایت کنید
        // window.location.href = '/login';
    }
});