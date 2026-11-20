// products.js - categories and products (FR07 add category, FR08 add product,
// FR09 edit product, FR10 deactivate product, FR11 set reorder level)
const categoryForm = document.querySelector("#category-form");
const categoryName = document.querySelector("#category-name");
const categoryMessage = document.querySelector("#category-message");

const productForm = document.querySelector("#product-form");
const productName = document.querySelector("#product-name");
const productCategory = document.querySelector("#product-category");
const productPrice = document.querySelector("#product-price");
const productStock = document.querySelector("#product-stock");
const productReorder = document.querySelector("#product-reorder");
const productMessage = document.querySelector("#product-message");

const editSection = document.querySelector("#edit-section");
const editForm = document.querySelector("#edit-form");
const editName = document.querySelector("#edit-name");
const editCategory = document.querySelector("#edit-category");
const editPrice = document.querySelector("#edit-price");
const editClose = document.querySelector("#edit-close");
const editMessage = document.querySelector("#edit-message");

const productsBody = document.querySelector("#products-body");
const listMessage = document.querySelector("#list-message");

let categories = [];
let products = [];
let editingId = null;

startPage(loadAll);

async function loadAll() {
    try {
        categories = await callApi("GET", "/api/categories");
        fillCategories(productCategory);
        fillCategories(editCategory);
        loadProducts();
    } catch (error) {
        showError(listMessage, error);
    }
}

function fillCategories(select) {
    select.innerHTML = "";
    select.add(new Option("Choose a category", ""));
    for (const c of categories) {
        select.add(new Option(c.name, c.id));
    }
}

// the table of active products
async function loadProducts() {
    try {
        const all = await callApi("GET", "/api/products?all=1");
        products = all.filter(function (p) { return p.active; });
        productsBody.innerHTML = "";
        for (const p of products) {
            const row = makeRow([p.name, p.category, ksh(p.price), p.stock]);
            row.children[2].className = "num";

            // reorder level: a number box and a Set level button
            const levelCell = document.createElement("td");
            const levelBox = document.createElement("input");
            levelBox.type = "number";
            levelBox.min = 0;
            levelBox.value = p.reorder_level;
            const levelButton = document.createElement("button");
            levelButton.textContent = "Set level";
            levelButton.className = "small";
            levelButton.addEventListener("click", function () { setLevel(p.id, levelBox.value); });
            levelCell.appendChild(levelBox);
            levelCell.appendChild(levelButton);
            row.appendChild(levelCell);

            // Edit and Deactivate buttons
            const actionCell = document.createElement("td");
            const editButton = document.createElement("button");
            editButton.textContent = "Edit";
            editButton.className = "small";
            editButton.addEventListener("click", function () { openEdit(p); });
            const offButton = document.createElement("button");
            offButton.textContent = "Deactivate";
            offButton.className = "small danger";
            offButton.addEventListener("click", function () { deactivate(p.id); });
            actionCell.appendChild(editButton);
            actionCell.appendChild(offButton);
            row.appendChild(actionCell);

            productsBody.appendChild(row);
        }
    } catch (error) {
        showError(listMessage, error);
    }
}

// FR07 Add category
categoryForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
        await callApi("POST", "/api/categories", { name: categoryName.value });
        showMessage(categoryMessage, "Category added.", false);
        categoryName.value = "";
        categories = await callApi("GET", "/api/categories");
        fillCategories(productCategory);
        fillCategories(editCategory);
    } catch (error) {
        showError(categoryMessage, error);
    }
});

// FR08 Add product
productForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
        await callApi("POST", "/api/products", {
            name: productName.value,
            category_id: Number(productCategory.value),
            price: productPrice.value,
            stock: productStock.value,
            reorder_level: productReorder.value
        });
        showMessage(productMessage, "Product added.", false);
        productForm.reset();
        loadProducts();
    } catch (error) {
        showError(productMessage, error);
    }
});

// FR09 Edit product: show the edit form with the product's values
function openEdit(p) {
    editingId = p.id;
    editName.value = p.name;
    editCategory.value = p.category_id;
    editPrice.value = p.price;
    showMessage(editMessage, "", false);
    editSection.hidden = false;
    editName.focus();
}

editForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
        await callApi("PUT", "/api/products/" + editingId, {
            name: editName.value,
            category_id: Number(editCategory.value),
            price: editPrice.value
        });
        editSection.hidden = true;
        showMessage(listMessage, "Product updated. Past sales keep the price they were sold at.", false);
        loadProducts();
    } catch (error) {
        showError(editMessage, error);
    }
});

editClose.addEventListener("click", function () {
    editSection.hidden = true;
});

// FR10 Deactivate product
async function deactivate(id) {
    if (!confirm("Deactivate this product? It disappears from the sales and stock-in forms. Its history is kept.")) {
        return;
    }
    try {
        await callApi("POST", "/api/products/" + id + "/deactivate");
        showMessage(listMessage, "Product deactivated.", false);
        loadProducts();
    } catch (error) {
        showError(listMessage, error);
    }
}

// FR11 Set reorder level
async function setLevel(id, level) {
    try {
        await callApi("PUT", "/api/products/" + id + "/reorder-level", { reorder_level: level });
        showMessage(listMessage, "Reorder level saved.", false);
    } catch (error) {
        showError(listMessage, error);
    }
}
