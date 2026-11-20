// goods.js - record stock-in (FR12, Owner)
const goodsForm = document.querySelector("#goods-form");
const goodsProduct = document.querySelector("#goods-product");
const goodsQty = document.querySelector("#goods-qty");
const goodsDate = document.querySelector("#goods-date");
const goodsSupplier = document.querySelector("#goods-supplier");
const goodsMessage = document.querySelector("#goods-message");

startPage(async function () {
    await fillProducts(goodsProduct, "Choose a product");
    // today's date, as YYYY-MM-DD
    const today = new Date().toISOString().slice(0, 10);
    goodsDate.value = today;
    goodsDate.max = today;
});

goodsForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
        const result = await callApi("POST", "/api/stock-in", {
            product_id: Number(goodsProduct.value),
            quantity: goodsQty.value,
            date: goodsDate.value,
            supplier: goodsSupplier.value
        });
        showMessage(goodsMessage, "Saved. " + result.product + " now has " + result.stock + " in stock.", false);
        goodsQty.value = "";
        goodsSupplier.value = "";
    } catch (error) {
        showError(goodsMessage, error);
    }
});
