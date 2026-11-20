// sales.js - record a sale (FR13, Attendant) and cancel a sale (FR14, Owner)
const saleForm = document.querySelector("#sale-form");
const saleProduct = document.querySelector("#sale-product");
const saleQty = document.querySelector("#sale-qty");
const saleMessage = document.querySelector("#sale-message");
const basketList = document.querySelector("#basket");
const basketTotal = document.querySelector("#basket-total");
const saveSale = document.querySelector("#save-sale");
const salesBody = document.querySelector("#sales-body");
const salesMessage = document.querySelector("#sales-message");

let products = [];      // the product list from the server
let basket = [];        // the items in the sale being made
let isOwner = false;

startPage(async function (user) {
    isOwner = user.role === "Owner";
    products = await fillProducts(saleProduct, "Choose a product");
    drawBasket();
    loadSales();
});

// show the items in the basket and the total
function drawBasket() {
    basketList.innerHTML = "";
    let total = 0;
    for (const item of basket) {
        const li = document.createElement("li");
        li.textContent = item.name + " x " + item.qty + " = " + ksh(item.qty * item.price) + " ";
        const remove = document.createElement("button");
        remove.textContent = "Remove";
        remove.className = "small plain";
        remove.addEventListener("click", function () {
            basket.splice(basket.indexOf(item), 1);
            drawBasket();
        });
        li.appendChild(remove);
        basketList.appendChild(li);
        total = total + item.qty * item.price;
    }
    basketTotal.textContent = ksh(total);
    saveSale.disabled = basket.length === 0;
}

// Add to sale
saleForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const id = Number(saleProduct.value);
    const qty = Number(saleQty.value);
    if (!id) {
        showMessage(saleMessage, "Choose a product.", true);
        return;
    }
    if (!Number.isInteger(qty) || qty < 1) {
        showMessage(saleMessage, "Quantity must be a whole number of 1 or more.", true);
        return;
    }
    const product = products.find(function (p) { return p.id === id; });
    let item = basket.find(function (i) { return i.id === id; });
    const wanted = (item ? item.qty : 0) + qty;
    if (wanted > product.stock) {
        showMessage(saleMessage, "Only " + product.stock + " of " + product.name + " in stock.", true);
        return;
    }
    if (item) {
        item.qty = wanted;
    } else {
        basket.push({ id: id, name: product.name, price: product.price, qty: qty });
    }
    saleQty.value = 1;
    showMessage(saleMessage, "", false);
    drawBasket();
});

// Save sale
saveSale.addEventListener("click", async function () {
    saveSale.disabled = true;
    const items = basket.map(function (i) {
        return { product_id: i.id, quantity: i.qty };
    });
    try {
        const sale = await callApi("POST", "/api/sales", { items: items });
        basket = [];
        drawBasket();
        showMessage(saleMessage, "Sale #" + sale.id + " saved: " + ksh(sale.total), false);
        products = await fillProducts(saleProduct, "Choose a product");
        loadSales();
    } catch (error) {
        showError(saleMessage, error);
        saveSale.disabled = false;
    }
});

// the list of recent sales
async function loadSales() {
    try {
        const sales = await callApi("GET", "/api/sales");
        salesBody.innerHTML = "";
        for (const s of sales) {
            const names = s.items.map(function (i) { return i.product + " x " + i.quantity; });
            const row = makeRow(["#" + s.id, s.date.replace("T", " "), names.join(", "), ksh(s.total)]);
            row.children[3].className = "num";
            const status = document.createElement("td");
            status.appendChild(makeBadge(s.status, s.status === "Completed" ? "ok" : "off"));
            row.appendChild(status);

            // only the Owner gets a Cancel button
            if (isOwner) {
                const cell = document.createElement("td");
                if (s.status === "Completed") {
                    const cancel = document.createElement("button");
                    cancel.textContent = "Cancel sale";
                    cancel.className = "small danger";
                    cancel.addEventListener("click", function () { cancelSale(s.id); });
                    cell.appendChild(cancel);
                }
                row.appendChild(cell);
            }
            salesBody.appendChild(row);
        }
    } catch (error) {
        showError(salesMessage, error);
    }
}

async function cancelSale(id) {
    if (!confirm("Cancel sale #" + id + "? The items go back into stock.")) {
        return;
    }
    try {
        await callApi("POST", "/api/sales/" + id + "/cancel");
        showMessage(salesMessage, "Sale #" + id + " cancelled. Stock returned.", false);
        loadSales();
    } catch (error) {
        showError(salesMessage, error);
    }
}
