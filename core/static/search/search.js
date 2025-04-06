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

function displayResults(results) {
    const container = document.getElementById('search-results');
    container.innerHTML = '';

    const groupedResults = groupResultsByType(results);

    for (const [type, items] of Object.entries(groupedResults)) {
        const section = document.createElement('div');
        section.className = 'results-section';
        section.innerHTML = `
            <h3 class="section-title">${getTypeTitle(type)}</h3>
            <div class="items-container" id="${type}-items"></div>
        `;

        container.appendChild(section);

        items.forEach(item => {
            document.getElementById(`${type}-items`).appendChild(
                createResultItem(item)
            );
        });
    }
}

function groupResultsByType(results) {
    return results.reduce((groups, item) => {
        if (!groups[item.type]) {
            groups[item.type] = [];
        }
        groups[item.type].push(item);
        return groups;
    }, {});
}

function getTypeTitle(type) {
    const titles = {
        'issue': 'خطاها',
        'solution': 'راهکارها',
        'map': 'نقشه‌ها',
        'article': 'مقالات'
    };
    return titles[type] || type;
}

function createResultItem(result) {
    const item = document.createElement('div');
    item.className = 'result-item';
    item.innerHTML = formatSearchResult(result); // از تابع موجود شما
    return item;
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


const categoriesListItems = document.querySelectorAll('#categories-list');

function setupCategoryEvents() {
    categoriesListItems.forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.tagName === 'LI') {
                const submenu = e.target.querySelector('ul');
                if (submenu) {
                    if (submenu.style.display === 'block') {
                        submenu.style.display = 'none';
                        e.target.querySelector('i').className = 'fas fa-chevron-left';
                    } else {
                        submenu.style.display = 'block';
                        e.target.querySelector('i').className = 'fas fa-chevron-down';
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


let activeSearchQuery = null;

async function performSearch(query, options = {}) {
    // ذخیره آخرین کوئری جستجو
    activeSearchQuery = query;

    try {
        if (!query || query.length < 2) {
            clearResults();
            return;
        }

        showLoader();

        const params = new URLSearchParams();
        params.append('query', query.trim());

        // اضافه کردن پارامترهای فیلتر
        if (options.filterOption) params.append('filter_option', options.filterOption);
        if (options.categoryId) params.append('category_id', options.categoryId);
        if (options.subcategoryId) params.append('subcategory_id', options.subcategoryId);

        const response = await fetchWithAuth(`/api/v1/search/?${params.toString()}`);

        // بررسی اگر این آخرین درخواست جستجو نباشد
        if (query !== activeSearchQuery) return;

        const data = await response.json();

        if (data.results && data.results.length > 0) {
            displayResults(data.results);
        } else {
            showNoResults();
        }
    } catch (error) {
        if (query === activeSearchQuery) {
            showError(error);
        }
    } finally {
        if (query === activeSearchQuery) {
            hideLoader();
        }
    }
}

const searchButton = document.querySelector('.btn.btn-success');

// مدیریت رویدادهای جستجو
searchButton.addEventListener('click', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = searchInput.value.trim();
        performSearch(query);
    }, 500);
});


// توابع کمکی
function clearResults() {
    document.getElementById('search-results').innerHTML = '';
}

function showLoader() {
    document.getElementById('search-results').innerHTML = '<div class="loader">در حال جستجو...</div>';
}

function hideLoader() {
    const loader = document.querySelector('.loader');
    if (loader) loader.remove();
}

function showNoResults() {
    document.getElementById('search-results').innerHTML = '<div class="no-results">نتیجه‌ای یافت نشد</div>';
}

function showError(error) {
    document.getElementById('search-results').innerHTML = `<div class="error">خطا: ${error.message}</div>`;
}



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



// همه
const allbtn = document.getElementById('all-btn')

// خطا ها
const errorbtn = document.getElementById('errors-btn')

// مقالات
const articlebtn = document.getElementById('article-btn')

// راهکار ها
const sectionbtn = document.getElementById('section-btn')

// مپ ها
const mapsbtn = document.getElementById('maps-btn')


allbtn.addEventListener('click', () => {
    const sectionTitles = document.querySelectorAll('.section-title');

    // تغییر حالت نمایش عناصر به none
    sectionTitles.forEach(title => {
        title.style.display = 'block';
    });

    allbtn.classList.add('active')
    errorbtn.classList.remove('active')
    articlebtn.classList.remove('active')
    sectionbtn.classList.remove('active')
    mapsbtn.classList.remove('active')


    const errors = document.getElementById('issue-items')
    const article = document.getElementById('article-items')
    const section = document.getElementById('solution-items')
    const maps = document.getElementById('maps')
    errors.style.display = 'block'
    article.style.display = 'block'
    section.style.display = 'block'
    maps.style.display = 'block'
})

errorbtn.addEventListener('click', () => {
    const sectionTitles = document.querySelectorAll('.section-title');

    // تغییر حالت نمایش عناصر به none
    sectionTitles.forEach(title => {
        title.style.display = 'none';
    });

    allbtn.classList.remove('active')
    errorbtn.classList.add('active')
    articlebtn.classList.remove('active')
    sectionbtn.classList.remove('active')
    mapsbtn.classList.remove('active')

    const errors = document.getElementById('issue-items')
    const article = document.getElementById('article-items')
    const section = document.getElementById('solution-items')
    const maps = document.getElementById('maps')
    errors.style.display = 'block'
    article.style.display = 'none'
    section.style.display = 'none'
    maps.style.display = 'none'
})

articlebtn.addEventListener('click', () => {
    const sectionTitles = document.querySelectorAll('.section-title');

    // تغییر حالت نمایش عناصر به none
    sectionTitles.forEach(title => {
        title.style.display = 'none';
    });


    allbtn.classList.remove('active')
    errorbtn.classList.remove('active')
    articlebtn.classList.add('active')
    sectionbtn.classList.remove('active')
    mapsbtn.classList.remove('active')

    const errors = document.getElementById('issue-items')
    const article = document.getElementById('article-items')
    const section = document.getElementById('solution-items')
    const maps = document.getElementById('maps')
    errors.style.display = 'none'
    article.style.display = 'block'
    section.style.display = 'none'
    maps.style.display = 'none'
})

sectionbtn.addEventListener('click', () => {
    const sectionTitles = document.querySelectorAll('.section-title');

    // تغییر حالت نمایش عناصر به none
    sectionTitles.forEach(title => {
        title.style.display = 'none';
    });


    allbtn.classList.remove('active')
    errorbtn.classList.remove('active')
    articlebtn.classList.remove('active')
    sectionbtn.classList.add('active')
    mapsbtn.classList.remove('active')

    const errors = document.getElementById('issue-items')
    const article = document.getElementById('article-items')
    const section = document.getElementById('solution-items')
    const maps = document.getElementById('maps')
    errors.style.display = 'none'
    article.style.display = 'none'
    section.style.display = 'block'
    maps.style.display = 'none'
})

mapsbtn.addEventListener('click', () => {
    const sectionTitles = document.querySelectorAll('.section-title');

    // تغییر حالت نمایش عناصر به none
    sectionTitles.forEach(title => {
        title.style.display = 'none';
    });


    allbtn.classList.remove('active')
    errorbtn.classList.remove('active')
    articlebtn.classList.remove('active')
    sectionbtn.classList.remove('active')
    mapsbtn.classList.add('active')

    const errors = document.getElementById('issue-items')
    const article = document.getElementById('article-items')
    const section = document.getElementById('solution-items')
    const maps = document.getElementById('maps')
    errors.style.display = 'none'
    article.style.display = 'none'
    section.style.display = 'none'
    maps.style.display = 'block'
})




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

