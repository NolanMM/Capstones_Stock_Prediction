document.addEventListener("DOMContentLoaded", function () {
    // === Debug Mode Flag ===
    const debugMode = true;

    // === Auth Token Setup ===
    const token = localStorage.getItem("authToken");
    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Token ${token}`
    };

    // === Login State ===
    const userIsLoggedIn = debugMode ? true : !!token;

    // === UI Adjustments for Login ===
    const portfolioLink = document.querySelector('.nav-link[href="portfolio.html"]');
    const accountLink = document.querySelector('.nav-link[href="account.html"]');

    if (userIsLoggedIn) {
        if (portfolioLink) portfolioLink.style.display = 'block';
        if (accountLink) accountLink.setAttribute('href', 'account.html');
    } else {
        if (portfolioLink) portfolioLink.style.display = 'none';
        if (accountLink) accountLink.setAttribute('href', 'register.html');
    }

    // === Stock Input and Selection Logic ===
    const removeStockBtn = document.getElementById("removeStock");
    const selectedStock = document.getElementById("selectedStock");
    const stockInput = document.getElementById("DataList");
    const datalist = document.getElementById("datalistOptions");

    removeStockBtn.style.display = "none";

    function updateStock(stockName) {
        selectedStock.textContent = stockName;
        selectedStock.appendChild(removeStockBtn);
        removeStockBtn.style.display = "inline-block";
        stockInput.value = "";

        const now = new Date();
        const currentHour = now.getHours();
        const currentDay = now.getDay();
        let priceAtCloseLabel = "Price at Close";

        const isWeekday = currentDay >= 1 && currentDay <= 5;
        const isTradingHours = currentHour >= 9 && currentHour < 17;

        if (isWeekday && isTradingHours) {
            priceAtCloseLabel = "Yesterday's Close Price";
        }

        fetch("../json/stockdetails.json")
            .then(response => response.json())
            .then(data => {
                const stockData = data.find(stock => stock.name === stockName);
                if (stockData) {
                    const setValue = (id, label, value) => {
                        const element = document.getElementById(id);
                        element.innerHTML = `${label}:<br>${parseFloat(value).toFixed(2)}`;
                        element.classList.remove("placeholder-glow");
                    };
                    setValue("CurrentPrice", "Current Price", stockData.currentPrice);
                    setValue("PriceAtClose", priceAtCloseLabel, stockData.priceAtClose);
                    setValue("AfterHoursPrice", "After Hours Price", stockData.afterHoursPrice);
                    setValue("PriceToEarnings", "Price to Earnings", stockData.priceToEarnings);
                    setValue("PriceToBook", "Price to Book", stockData.priceToBook);
                }
            })
            .catch(error => console.error("Error fetching stock data:", error));

        fetchStockNews(stockName);
        document.getElementById("fourthSection").removeAttribute("hidden");
    }

    removeStockBtn.addEventListener("click", function () {
        stockInput.value = "";
        resetStockData();
        resetCharts();
    });

    function resetCharts() {
        ["chLine", "chLine2", "chBar", "chScatter"].forEach(id => {
            const chartEl = document.getElementById(id);
            if (chartEl && chartEl.chart) {
                chartEl.chart.data.datasets.forEach(ds => ds.data = []);
                chartEl.chart.update();
                const container = chartEl.parentElement;
                if (container) container.classList.add("placeholder-glow");
            }
        });
    }

    function resetStockData() {
        selectedStock.textContent = "";
        removeStockBtn.style.display = "none";

        const now = new Date();
        const currentHour = now.getHours();
        const currentDay = now.getDay();
        const priceAtCloseLabel = (currentDay >= 1 && currentDay <= 5 && currentHour >= 9 && currentHour < 17) ?
            "Yesterday's Close Price" : "Price at Close";

        const fields = [
            { id: "CurrentPrice", label: "Current Price" },
            { id: "PriceAtClose", label: priceAtCloseLabel },
            { id: "AfterHoursPrice", label: "After Hours Price" },
            { id: "PriceToEarnings", label: "Price to Earnings" },
            { id: "PriceToBook", label: "Price to Book" }
        ];

        fields.forEach(field => {
            const element = document.getElementById(field.id);
            element.innerHTML = `${field.label}:<br><span class="placeholder col-4">.</span><span class="placeholder col-4">.</span><span class="placeholder col-4">.</span>`;
            element.classList.add("placeholder-glow");
        });

        document.getElementById("newsContent").innerHTML = "";
        resetCharts();
        document.getElementById("fourthSection").setAttribute("hidden", true);
    }

    stockInput.addEventListener("change", function () {
        const inputValue = stockInput.value.trim();
        const options = Array.from(datalist.options).map(option => option.value);
        if (options.includes(inputValue)) {
            resetStockData();
            updateStock(inputValue);
        } else {
            stockInput.value = "";
        }
    });

    function fetchStockList() {
        fetch("../json/stocknames.json")
            .then(response => response.json())
            .then(data => {
                datalist.innerHTML = "";
                data.forEach(stock => {
                    const option = document.createElement("option");
                    option.value = stock.name;
                    datalist.appendChild(option);
                });
            })
            .catch(error => console.error("Error fetching stocks:", error));
    }

    fetchStockList();
});

function fetchStockNews(stockName) {
    fetch("../json/newsarticles.json")
        .then(response => response.json())
        .then(data => {
            const newsContent = document.getElementById("newsContent");
            const newsRecentContent = document.getElementById("newsRecentContent");
            newsContent.innerHTML = "";
            newsRecentContent.innerHTML = "";

            const stockNews = data.find(stock => stock.stock === stockName);

            if (!stockNews) {
                newsContent.innerHTML = "<p>No news available for this stock.</p>";
                return;
            }

            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(new Date().getDate() - 14);

            stockNews.articles.forEach(article => {
                const articleDate = new Date(article.date);
                const articleElement = document.createElement("div");
                articleElement.classList.add("news-article");
                articleElement.innerHTML = `
                    <h5><a href="${article.link}" target="_blank">${article.title}</a></h5>
                    <h6>${article.date}</h6>
                    <p>${article.description}</p>`;

                if (articleDate >= twoWeeksAgo) {
                    newsRecentContent.appendChild(articleElement);
                } else {
                    newsContent.appendChild(articleElement);
                }
            });
        })
        .catch(error => {
            console.error("Error fetching news:", error);
            document.getElementById("newsContent").innerHTML = "<p>Error loading news.</p>";
        });
}

document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".btn-group .btn");
    const contentSections = document.querySelectorAll(".content-section");

    buttons.forEach(button => {
        button.addEventListener("click", () => {
            buttons.forEach(btn => btn.classList.remove("active"));
            contentSections.forEach(section => section.classList.remove("active"));
            button.classList.add("active");
            const targetId = button.getAttribute("data-target");
            document.getElementById(targetId).classList.add("active");
        });
    });
});
