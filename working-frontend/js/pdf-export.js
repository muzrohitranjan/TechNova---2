/**
 * PDF Export Module
 * Handles generating and downloading recipe PDFs
 */

const API_BASE_URL = 'http://localhost:8000';

// Download Single Recipe PDF
async function downloadRecipePDF(recipeId, recipeTitle) {
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        showNotification('Please login to download PDF', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/voice/pdf/recipe/${recipeId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.type === 'pdf_ready') {
            // Convert HTML to PDF using browser print or download as HTML
            downloadHTMLAsFile(result.pdf_content, `${recipeTitle || 'recipe'}.html`);
            showNotification('Recipe PDF generated!', 'success');
        } else {
            showNotification(result.message || 'Error generating PDF', 'error');
        }
    } catch (error) {
        console.error('Error generating PDF:', error);
        showNotification('Error generating PDF', 'error');
    }
}

// Download Cooking Guide PDF
async function downloadCookingGuidePDF(recipeId, currentStep = 0) {
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        showNotification('Please login to download', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/voice/pdf/cooking-guide/${recipeId}?current_step=${currentStep}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.type === 'pdf_ready') {
            downloadHTMLAsFile(result.pdf_content, 'cooking-guide.html');
            showNotification('Cooking guide generated!', 'success');
        } else {
            showNotification(result.message || 'Error generating guide', 'error');
        }
    } catch (error) {
        console.error('Error generating cooking guide:', error);
        showNotification('Error generating cooking guide', 'error');
    }
}

// Create Recipe Book from Selected Recipes
async function createRecipeBook(recipeIds, bookTitle = "My Recipe Book") {
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        showNotification('Please login to create recipe book', 'error');
        return;
    }
    
    if (!recipeIds || recipeIds.length === 0) {
        showNotification('Please select at least one recipe', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/voice/recipe-book/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                recipe_ids: recipeIds,
                title: bookTitle
            })
        });
        
        const result = await response.json();
        
        if (result.type === 'recipe_book_ready') {
            downloadHTMLAsFile(result.pdf_content, `${bookTitle.replace(/\s+/g, '-').toLowerCase()}.html`);
            showNotification(`Recipe book created with ${result.total_recipes} recipes!`, 'success');
        } else {
            showNotification(result.message || 'Error creating recipe book', 'error');
        }
    } catch (error) {
        console.error('Error creating recipe book:', error);
        showNotification('Error creating recipe book', 'error');
    }
}

// Download HTML content as file
function downloadHTMLAsFile(htmlContent, filename) {
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Print Recipe (Alternative to PDF)
function printRecipe() {
    window.print();
}

// Show Recipe Book Creation Modal
function showRecipeBookModal() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'recipeBookModal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="closeRecipeBookModal()">
                <i class="fas fa-times"></i>
            </button>
            <div class="modal-header">
                <h2>Create Recipe Book</h2>
                <p>Select recipes to compile into a book</p>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="bookTitle">Book Title</label>
                    <input type="text" id="bookTitle" placeholder="My Recipe Collection" value="My Recipe Book">
                </div>
                <div class="recipe-selection" id="recipeSelection">
                    <!-- Recipes loaded dynamically -->
                </div>
            </div>
            <button class="btn-submit" onclick="confirmRecipeBook()">
                <i class="fas fa-book"></i> Create Recipe Book
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    loadRecipesForBook();
}

function closeRecipeBookModal() {
    const modal = document.getElementById('recipeBookModal');
    if (modal) {
        modal.remove();
    }
}

async function loadRecipesForBook() {
    const container = document.getElementById('recipeSelection');
    if (!container) return;
    
    const authToken = localStorage.getItem('auth_token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/recipes/my-recipes`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayRecipeSelection(container, data.recipes || []);
        } else {
            // Demo recipes
            displayDemoRecipeSelection(container);
        }
    } catch (error) {
        displayDemoRecipeSelection(container);
    }
}

function displayRecipeSelection(container, recipes) {
    if (recipes.length === 0) {
        container.innerHTML = '<p>No recipes available. Create some recipes first!</p>';
        return;
    }
    
    container.innerHTML = recipes.map(recipe => `
        <div class="recipe-checkbox">
            <label>
                <input type="checkbox" value="${recipe.id}" class="recipe-select">
                <span>${recipe.title}</span>
                <small>${recipe.cuisine}</small>
            </label>
        </div>
    `).join('');
}

function displayDemoRecipeSelection(container) {
    const demoRecipes = [
        { id: '1', title: 'Masala Dosa', cuisine: 'South Indian' },
        { id: '2', title: 'Butter Chicken', cuisine: 'North Indian' },
        { id: '3', title: 'Dhokla', cuisine: 'Gujarati' }
    ];
    
    container.innerHTML = demoRecipes.map(recipe => `
        <div class="recipe-checkbox">
            <label>
                <input type="checkbox" value="${recipe.id}" class="recipe-select">
                <span>${recipe.title}</span>
                <small>${recipe.cuisine}</small>
            </label>
        </div>
    `).join('');
}

function confirmRecipeBook() {
    const checkboxes = document.querySelectorAll('.recipe-select:checked');
    const recipeIds = Array.from(checkboxes).map(cb => cb.value);
    const title = document.getElementById('bookTitle')?.value || 'My Recipe Book';
    
    if (recipeIds.length === 0) {
        showNotification('Please select at least one recipe', 'error');
        return;
    }
    
    closeRecipeBookModal();
    createRecipeBook(recipeIds, title);
}

// Export to PDF Module
window.PDFExport = {
    downloadRecipePDF,
    downloadCookingGuidePDF,
    createRecipeBook,
    printRecipe,
    showRecipeBookModal,
    closeRecipeBookModal
};

