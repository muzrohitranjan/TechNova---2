/**
 * Tech Nova - Frontend Application JavaScript
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State Management
let authToken = localStorage.getItem('auth_token');
let currentUser = null;

// DOM Elements
const loginBtn = document.getElementById('loginBtn');
const userMenu = document.getElementById('userMenu');
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const navLinks = document.getElementById('navLinks');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initMobileMenu();
    initModals();
    initForms();
    loadFeaturedRecipes();
    checkDeviceType();
});

// Check Device Type
function checkDeviceType() {
    const deviceType = getDeviceType();
    console.log('Device Type:', deviceType);
    localStorage.setItem('device_type', deviceType);
}

// Get Device Type from User Agent
function getDeviceType() {
    const userAgent = navigator.userAgent.toLowerCase();
    if (/mobile|android|iphone|ipod|blackberry|windows phone/i.test(userAgent)) {
        return 'mobile';
    } else if (/ipad|tablet|playbook|silk/i.test(userAgent)) {
        return 'tablet';
    }
    return 'laptop';
}

// Initialize Authentication
function initAuth() {
    if (authToken) {
        fetchCurrentUser();
    }
}

// Fetch Current User
async function fetchCurrentUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            updateAuthUI(true);
            registerDevice();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Error fetching user:', error);
        logout();
    }
}

// Update Auth UI
function updateAuthUI(isLoggedIn) {
    if (isLoggedIn) {
        loginBtn.style.display = 'none';
        userMenu.style.display = 'block';
    } else {
        loginBtn.style.display = 'block';
        userMenu.style.display = 'none';
    }
}

// Register Device for Push Notifications
async function registerDevice() {
    try {
        const deviceType = localStorage.getItem('device_type') || 'laptop';
        const deviceData = {
            device_token: generateDeviceToken(),
            device_type: deviceType,
            device_name: navigator.platform,
            push_provider: 'none'
        };

        await fetch(`${API_BASE_URL}/api/devices/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(deviceData)
        });
    } catch (error) {
        console.error('Error registering device:', error);
    }
}

// Generate Device Token
function generateDeviceToken() {
    return 'device_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
}

// Initialize Mobile Menu
function initMobileMenu() {
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }
}

// Initialize Modals
function initModals() {
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            loginModal.classList.add('active');
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            closeLoginModal();
        }
        if (e.target === registerModal) {
            closeRegisterModal();
        }
    });
}

function closeLoginModal() {
    loginModal.classList.remove('active');
}

function closeRegisterModal() {
    registerModal.classList.remove('active');
}

function showRegister() {
    closeLoginModal();
    registerModal.classList.add('active');
}

function showLogin() {
    closeRegisterModal();
    loginModal.classList.add('active');
}

// Initialize Forms
function initForms() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    const heroSearch = document.getElementById('heroSearch');
    if (heroSearch) {
        heroSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchRecipes();
            }
        });
    }
}

// Handle Login
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('auth_token', authToken);
            closeLoginModal();
            fetchCurrentUser();
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
    }
}

// Handle Register
async function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                email, 
                password,
                confirm_password: password,
                full_name: name
            })
        });

        const data = await response.json();

        if (response.ok) {
            if (data.requires_verification) {
                // Show verification message
                closeRegisterModal();
                showNotification('Registration successful! Please check your email to verify your account before logging in.', 'success');
            } else {
                authToken = data.access_token;
                localStorage.setItem('auth_token', authToken);
                closeRegisterModal();
                fetchCurrentUser();
                showNotification('Registration successful!', 'success');
            }
        } else {
            showNotification(data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please try again.', 'error');
    }
}

// Logout
function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('auth_token');
    updateAuthUI(false);
    showNotification('Logged out successfully', 'success');
    window.location.href = 'index.html';
}

// Search Recipes
function searchRecipes() {
    const searchInput = document.getElementById('heroSearch');
    const query = searchInput.value.trim();
    
    if (query) {
        window.location.href = `search.html?q=${encodeURIComponent(query)}`;
    }
}

// Load Featured Recipes
async function loadFeaturedRecipes() {
    const recipesGrid = document.getElementById('featuredRecipes');
    if (!recipesGrid) return;

    try {
        // Try API first
        const deviceType = localStorage.getItem('device_type');
        const endpoint = deviceType === 'mobile' ? '/api/recipes/mobile' : '/api/recipes';
        
        const response = await fetch(`${API_BASE_URL}${endpoint}?page_size=6`);
        
        if (response.ok) {
            const data = await response.json();
            const recipes = data.recipes || [];
            displayRecipes(recipesGrid, recipes);
        } else {
            // Fallback to real restaurant data
            loadRestaurantRecipes(recipesGrid);
        }
    } catch (error) {
        console.error('Error loading recipes:', error);
        loadRestaurantRecipes(recipesGrid);
    }
}

async function loadRestaurantRecipes(container) {
    try {
        const response = await fetch('/data/restaurants.json');
        const data = await response.json();
        const restaurants = data.restaurants || [];
        displayRestaurantRecipes(container, restaurants);
    } catch (error) {
        console.error('Error loading restaurant data:', error);
        displayStaticRecipes(container);
    }
}

function displayRestaurantRecipes(container, restaurants) {
    container.innerHTML = restaurants.map(restaurant => createRestaurantCard(restaurant)).join('');
}

function createRestaurantCard(restaurant) {
    return `
        <div class="recipe-card restaurant-card" onclick="viewRestaurant('${restaurant.id}')">
            <div class="recipe-image">
                <img src="${restaurant.image}" alt="${restaurant.name}">
                <span class="recipe-badge">${restaurant.rating}★</span>
            </div>
            <div class="recipe-content">
                <h3>${restaurant.name}</h3>
                <p>${restaurant.location} • ${restaurant.cuisine}</p>
                <div class="recipe-meta">
                    <span><i class="fas fa-star"></i> ${restaurant.rating}</span>
                </div>
                <div class="signature-dish">
                    <i class="fas fa-utensils"></i> ${restaurant.signature_dish}
                </div>
            </div>
        </div>
    `;
}

function viewRestaurant(id) {
    window.location.href = `restaurant.html?id=${id}`;
}

function displayStaticRecipes(container) {
    const staticRecipes = [
        {
            title: "Butter Chicken from Haldiram's",
            cuisine: "North Indian",
            image_url: "https://images.unsplash.com/photo-1579586140626-58c4ef739630?w=400"
        },
        {
            title: "Masala Dosa from Saravana Bhavan",
            cuisine: "South Indian",
            image_url: "https://images.unsplash.com/photo-1630383249896-424e482df921?w=400"
        }
    ];
    
    container.innerHTML = staticRecipes.map(recipe => createRecipeCard(recipe)).join('');
}

// Display Recipes
function displayRecipes(container, recipes) {
    if (recipes.length === 0) {
        container.innerHTML = '<p class="no-recipes">No recipes found</p>';
        return;
    }

    container.innerHTML = recipes.map(recipe => createRecipeCard(recipe)).join('');
}

// Display Demo Recipes
function displayDemoRecipes(container) {
    const demoRecipes = [
        {
            id: '1',
            title: 'Masala Dosa',
            description: 'Crispy rice and lentil crepe with spiced potato filling',
            cuisine: 'South Indian',
            prep_time: 30,
            cook_time: 20,
            difficulty: 'medium',
            image_url: 'https://images.unsplash.com/photo-1630383249896-424e482df921?w=400'
        },
        {
            id: '2',
            title: 'Butter Chicken',
            description: 'Creamy tomato-based curry with tender chicken pieces',
            cuisine: 'North Indian',
            prep_time: 30,
            cook_time: 45,
            difficulty: 'medium',
            image_url: 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=400'
        },
        {
            id: '3',
            title: 'Dhokla',
            description: 'Steamed savory cake made from fermented batter',
            cuisine: 'Gujarati',
            prep_time: 15,
            cook_time: 25,
            difficulty: 'easy',
            image_url: 'https://images.unsplash.com/photo-1695504236952-16e6d11f6c44?w=400'
        },
        {
            id: '4',
            title: 'Puran Poli',
            description: 'Sweet flatbread stuffed with lentil and jaggery',
            cuisine: 'Maharashtrian',
            prep_time: 30,
            cook_time: 30,
            difficulty: 'hard',
            image_url: 'https://images.unsplash.com/photo-1567337710282-00832b415979?w=400'
        },
        {
            id: '5',
            title: 'Rosogolla',
            description: 'Soft cheese balls soaked in sugar syrup',
            cuisine: 'Bengali',
            prep_time: 20,
            cook_time: 30,
            difficulty: 'medium',
            image_url: 'https://images.unsplash.com/photo-1559305616-3f99cd43e353?w=400'
        },
        {
            id: '6',
            title: 'Daal Baati',
            description: 'Lentils served with baked wheat balls',
            cuisine: 'Rajasthani',
            prep_time: 20,
            cook_time: 45,
            difficulty: 'medium',
            image_url: 'https://images.unsplash.com/photo-1599043513900-489f22695880?w=400'
        }
    ];

    container.innerHTML = demoRecipes.map(recipe => createRecipeCard(recipe)).join('');
}

// Create Recipe Card HTML
function createRecipeCard(recipe) {
    const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
    
    return `
        <div class="recipe-card" onclick="viewRecipe('${recipe.id}')">
            <div class="recipe-image">
                <img src="${recipe.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400'}" alt="${recipe.title}">
                <span class="recipe-badge">${recipe.difficulty || 'Easy'}</span>
            </div>
            <div class="recipe-content">
                <h3>${recipe.title}</h3>
                <p>${recipe.description || ''}</p>
                <div class="recipe-meta">
                    <span><i class="fas fa-clock"></i> ${totalTime} min</span>
                    <span><i class="fas fa-fire"></i> ${recipe.difficulty || 'Easy'}</span>
                </div>
                <span class="recipe-region">${recipe.cuisine || 'Indian'}</span>
            </div>
        </div>
    `;
}

// View Recipe Details
function viewRecipe(id) {
    window.location.href = `recipe.html?id=${id}`;
}

// Show Notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Export functions
window.TechNova = {
    apiCall,
    logout,
    showNotification,
    viewRecipe,
    searchRecipes
};

