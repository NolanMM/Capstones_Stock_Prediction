document.addEventListener("DOMContentLoaded", function () {
    // Global variables for chart management
    let chartInstances = {};
    let currentSymbol = null;
    let predictionDataStore = null;
    let fixedHistoryForPredictionChart = null;

    // Initialize the page
    loadStockNames();
    setupEventListeners();

    // Simulated check for login status
    function isLoggedIn() {
        return true; // Placeholder
    }

    if (!isLoggedIn()) {
        document.querySelectorAll('.portfoliobutton').forEach(button => button.style.display = 'none');
        const portfolioLink = document.querySelector('.nav-link[href="portfolio.html"]');
        if (portfolioLink) portfolioLink.style.display = 'none';
        const accountLink = document.querySelector('.nav-link[href="account.html"]');
        if (accountLink) accountLink.setAttribute('href', 'register.html');
    }

    function setupEventListeners() {
        const stockInput = document.getElementById("DataList");
        stockInput.addEventListener("change", function () {
            const inputValue = this.value.trim();
            const options = Array.from(document.getElementById("datalistOptions").options).map(option => option.value);
            if (options.includes(inputValue)) {
                updateStock(inputValue);
            } else {
                this.value = "";
            }
        });

        document.getElementById("removeStock").addEventListener("click", function () {
            stockInput.value = "";
            resetStockData();
            resetCharts();
        });

        document.querySelectorAll('.chart-controls .chart-button').forEach(button => {
            button.addEventListener('click', function() {
                const range = this.getAttribute('data-range');
                let days;
                switch (range) {
                    case '1W': days = 7; break;
                    case '1M': days = 30; break;
                    case '1Y': days = 365; break;
                    default: days = 30;
                }
                changeDateRange(days);
            });
        });
    }

    function updateStock(stockName) {
        currentSymbol = stockName;
        const selectedStockElement = document.getElementById("selectedStock");
        const removeStockBtn = document.getElementById("removeStock");

        selectedStockElement.textContent = stockName;
        selectedStockElement.appendChild(removeStockBtn);
        removeStockBtn.style.display = "inline-block";
        document.getElementById("DataList").value = "";

        // Show loading placeholders
        const fields = [
            { id: "CurrentPrice", label: "Current Price" },
            { id: "PriceAtClose", label: "Price at Close" },
            { id: "AfterHoursPrice", label: "After Hours Price" },
            { id: "PriceToEarnings", label: "Price to Earnings" },
            { id: "PriceToBook", label: "Price to Book" }
        ];
        fields.forEach(field => {
            const element = document.getElementById(field.id);
            if(element) {
                element.innerHTML = `${field.label}:<br><span class="placeholder col-4">.</span>`;
                element.classList.add("placeholder-glow");
            }
        });

        // Fetch and display data
        fetchStockDetails(stockName);
        initializeAllCharts(stockName);
        fetchStockNews(stockName);

        document.getElementById("fourthSection").removeAttribute("hidden");
    }

    async function fetchStockDetails(stockName) {
        try {
            // This part can be replaced with an API call if details are available from the backend
            const response = await fetch("./static/json/stockdetails.json");
            const data = await response.json();
            const stockData = data.find(stock => stock.name === stockName);
            if (stockData) {
                const setValue = (id, label, value) => {
                    const element = document.getElementById(id);
                    if(element) {
                        element.innerHTML = `${label}:<br>${parseFloat(value).toFixed(2)}`;
                        element.classList.remove("placeholder-glow");
                    }
                };
                setValue("CurrentPrice", "Current Price", stockData.currentPrice || stockData.priceAtClose);
                setValue("PriceAtClose", "Price at Close", stockData.priceAtClose);
                setValue("AfterHoursPrice", "After Hour Price", stockData.afterHoursPrice);
                setValue("PriceToEarnings", "Price to Earnings", stockData.priceToEarnings);
                setValue("PriceToBook", "Price to Book", stockData.priceToBook);
            }
        } catch (error) {
            console.error("Error fetching stock details:", error);
        }
    }

    async function initializeAllCharts(symbol) {
        try {
            const [historyResponse, predictionResponse] = await Promise.all([
                almanacAPI.getStockHistory(symbol, 30),
                almanacAPI.getStockPredictions(symbol, 7)
            ]);

            if (!historyResponse || !historyResponse.history || historyResponse.history.length === 0) {
                console.error('No historical data available for', symbol);
                resetCharts();
                return;
            }
            if (!predictionResponse || predictionResponse.error) {
                console.error('No prediction data available for', symbol, predictionResponse?.error);
                updateHistoricalChart(historyResponse, symbol);
                return;
            }

            fixedHistoryForPredictionChart = historyResponse;
            predictionDataStore = predictionResponse;

            updateHistoricalChart(historyResponse, symbol);
            updatePredictionAndOtherCharts(fixedHistoryForPredictionChart, predictionDataStore, symbol);

        } catch (error) {
            console.error('Error initializing charts:', error);
            resetCharts();
        }
    }

    async function changeDateRange(days) {
        if (!currentSymbol) return;

        document.querySelectorAll('.chart-controls .chart-button').forEach(button => button.classList.remove('active'));
        let activeButton;
        if (days === 7) activeButton = document.querySelector('.chart-button[data-range="1W"]');
        else if (days === 30) activeButton = document.querySelector('.chart-button[data-range="1M"]');
        else if (days === 365) activeButton = document.querySelector('.chart-button[data-range="1Y"]');
        if (activeButton) activeButton.classList.add('active');

        try {
            const historyResponse = await almanacAPI.getStockHistory(currentSymbol, days);
            if (historyResponse && historyResponse.history && historyResponse.history.length > 0) {
                updateHistoricalChart(historyResponse, currentSymbol);
            } else {
                console.error('No historical data returned for the selected range.');
            }
        } catch (error) {
            console.error('Error fetching new date range:', error);
        }
    }

    function updateHistoricalChart(historyData, symbol) {
        const history = historyData.history.sort((a, b) => new Date(a.Date || a.date) - new Date(b.Date || b.date));
        if (!history.length) return;

        const labels = history.map(p => new Date(p.Date || p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        const prices = history.map(p => parseFloat(p.Close || p.close));

        createChart("chLine", "line", {
            title: `${symbol} - Historical Price`,
            labels: labels,
            datasets: [{
                label: 'Historical Price ($)',
                data: prices,
                borderColor: "#007bff",
                borderWidth: 3,
                pointBackgroundColor: "#007bff"
            }]
        });
    }

    function updatePredictionAndOtherCharts(historyData, predictionData, symbol) {
        const history = historyData.history.sort((a, b) => new Date(a.Date || a.date) - new Date(b.Date || b.date));
        const predictions = predictionData.forecast.sort((a, b) => new Date(a.date) - new Date(b.date));

        const historyMap = new Map();
        history.forEach(p => {
            const dateStr = new Date(p.Date || p.date).toISOString().split('T')[0];
            historyMap.set(dateStr, {
                price: parseFloat(p.Close || p.close),
                volume: parseInt(p.Volume || p.volume || 0)
            });
        });

        const predictionMap = new Map();
        predictions.forEach(p => {
            const dateStr = new Date(p.date).toISOString().split('T')[0];
            predictionMap.set(dateStr, parseFloat(p.price));
        });

        const allDateStrings = new Set([...historyMap.keys(), ...predictionMap.keys()]);
        const timeline = Array.from(allDateStrings).sort((a, b) => new Date(a) - new Date(b));
        const labels = timeline.map(dateStr => new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

        const historicalPrices = timeline.map(date => historyMap.get(date)?.price || null);
        const volumes = timeline.map(date => historyMap.get(date)?.volume || null).filter(v => v !== null);
        const historicalLabels = timeline.filter(date => historyMap.has(date))
                                         .map(dateStr => new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

        const lastHistoricalDate = [...historyMap.keys()].pop();
        let lastHistoricalPrice = [...historyMap.values()].pop().price;

        const predictedPrices = timeline.map(date => {
            if (date > lastHistoricalDate && predictionMap.has(date)) {
                return predictionMap.get(date);
            }
            return null;
        });

        const firstPredictionIndex = predictedPrices.findIndex(p => p !== null);
        if (firstPredictionIndex > 0) {
            predictedPrices[firstPredictionIndex - 1] = lastHistoricalPrice;
        }

        createChart("chLine2", "line", {
            title: `${symbol} - Price with 7-Day Predictions`,
            labels: labels,
            datasets: [
                {
                    label: 'Historical Price ($)',
                    data: historicalPrices,
                    borderColor: "#007bff",
                    borderWidth: 3,
                    pointBackgroundColor: "#007bff",
                    spanGaps: false
                },
                {
                    label: 'Predicted Price ($)',
                    data: predictedPrices,
                    borderColor: "#dc3545",
                    borderWidth: 3,
                    pointBackgroundColor: "#dc3545",
                    borderDash: [5, 5],
                    spanGaps: false
                }
            ]
        });

        createChart("chBar", "bar", {
            title: `${symbol} - Trading Volume (30 Days)`,
            labels: historicalLabels,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: "#28a745"
            }]
        });

        const predictedReturns = predictions
            .filter(p => new Date(p.date).toISOString().split('T')[0] > lastHistoricalDate)
            .map(p => parseFloat(p.return_pct));
            
        createChart("chScatter", "scatter", {
            title: `${symbol} - Predicted Daily Returns (%)`,
            datasets: [{
                label: 'Return %',
                data: predictedReturns.map((ret, index) => ({ x: index + 1, y: ret })),
                backgroundColor: predictedReturns.map(r => r >= 0 ? "#28a745" : "#dc3545")
            }]
        });
    }

    function createChart(canvasId, type, chartData) {
        let ctx = document.getElementById(canvasId);
        if (!ctx) return;
        ctx = ctx.getContext("2d");

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        chartInstances[canvasId] = new Chart(ctx, {
            type: type,
            data: {
                labels: chartData.labels || [],
                datasets: chartData.datasets || []
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    title: { display: !!chartData.title, text: chartData.title || '' },
                    legend: { display: true }
                },
                scales: type === 'scatter' ? {
                    x: { type: 'linear', position: 'bottom', title: { display: true, text: 'Day' } },
                    y: { title: { display: true, text: 'Return %' } }
                } : {
                    y: { beginAtZero: type === 'bar' }
                }
            }
        });
    }

    function resetCharts() {
        Object.values(chartInstances).forEach(chart => {
            if (chart) chart.destroy();
        });
        chartInstances = {};
    }

    function resetStockData() {
        document.getElementById("selectedStock").textContent = "";
        document.getElementById("removeStock").style.display = "none";
        const fields = ["CurrentPrice", "PriceAtClose", "AfterHoursPrice", "PriceToEarnings", "PriceToBook"];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if(el) {
                const label = id.replace(/([A-Z])/g, ' $1').trim();
                el.innerHTML = `${label}:<br>`;
            }
        });
        document.getElementById("newsContent").innerHTML = "";
        document.getElementById("newsRecentContent").innerHTML = "";
        document.getElementById("fourthSection").setAttribute("hidden", true);
    }

    async function loadStockNames() {
        const datalist = document.getElementById('datalistOptions');
        try {
            const response = await almanacAPI.getAvailableStocks();
            if (response && response.symbols) {
                datalist.innerHTML = '';
                response.symbols.forEach(symbol => {
                    let option = document.createElement('option');
                    option.value = symbol;
                    datalist.appendChild(option);
                });
            } else {
                loadStockNamesFromFile();
            }
        } catch (error) {
            console.error("Error loading stock names from API:", error);
            loadStockNamesFromFile();
        }
    }

    function loadStockNamesFromFile() {
        fetch("./static/json/stocknames.json")
            .then(response => response.json())
            .then(data => {
                const datalist = document.getElementById('datalistOptions');
                datalist.innerHTML = '';
                data.forEach(stock => {
                    let option = document.createElement('option');
                    option.value = stock.name;
                    datalist.appendChild(option);
                });
            })
            .catch(error => console.error("Error loading stock names from file:", error));
    }

    function fetchStockNews(stockName) {
        fetch("./static/json/newsarticles.json")
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
                    articleElement.classList.add("news-article", "mb-3");
                    articleElement.innerHTML = `
                        <h5><a href="${article.link}" target="_blank">${article.title}</a></h5>
                        <h6>${article.date}</h6>
                        <p>${article.description}</p>
                    `;
                    if (articleDate >= twoWeeksAgo) {
                        newsRecentContent.appendChild(articleElement);
                    } else {
                        newsContent.appendChild(articleElement);
                    }
                });
            })
            .catch(error => {
                console.error("Error fetching stock news:", error);
                document.getElementById("newsContent").innerHTML = "<p>Error loading news.</p>";
            });
    }
});