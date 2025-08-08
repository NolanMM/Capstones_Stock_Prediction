document.addEventListener("DOMContentLoaded", function () {
    // Use the auth manager to check authentication
    if (!authManager.requireAuth()) {
        // requireAuth will handle the redirect if not logged in
        return;
    }

    loadPortfolioData();
    // fetchChartData(); // This will load dummy charts initially or when View Details is clicked.
    loadStockNames();

    document.getElementById('stockForm').addEventListener('submit', function (event) {
        event.preventDefault();
        addStockToPortfolio();
    });
});

const headers = {
    "Content-Type": "application/json"
    // No Authorization header needed for session-based auth
};

let chartInstances = {}; // To manage Chart.js instances
let currentSymbol = null; // To store the currently viewed stock symbol
let predictionDataStore = null; // To store prediction data
let fixedHistoryForPredictionChart = null; // To store the 30-day history for the prediction chart

function loadPortfolioData() {
    fetch("/api/portfolio/", { 
        headers,
        credentials: 'include' // Include session cookies
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Could not fetch portfolio. Please log in again.');
            }
            return response.json();
        })
        .then(data => {
            let table = document.getElementById('portfolioTable');
            table.innerHTML = ''; // Clear existing table content
            if (data.length === 0) {
                table.innerHTML = "<tr><td colspan='2' class='text-center'>Your portfolio is empty. Add a stock to get started.</td></tr>";
                return;
            }
            data.forEach(stock => {
                let row = document.createElement('tr');
                row.dataset.symbol = stock.stock_symbol; // Store symbol in data attribute
                row.innerHTML = `
                    <td class='text-center'>${stock.stock_symbol}</td>
                    <td class='text-center'>
                        <button class='btn btn-primary-custom btn-sm' onclick='viewDetails(this)'>View Details</button>
                        <button class='btn btn-danger-custom btn-sm ms-2' onclick='removeStock(this)'>Remove</button>
                    </td>
                `;
                table.appendChild(row);
            });
        })
        .catch(error => {
            console.error("Error loading portfolio data:", error);
            alert(error.message);
            window.location.href = "/register.html";
        });
}

function addStockToPortfolio() {
    let stockSymbol = document.getElementById('name').value;
    if (!stockSymbol) {
        alert("Please select a stock.");
        return;
    }

    fetch("/api/portfolio/", {
        method: 'POST',
        headers: headers,
        credentials: 'include',
        body: JSON.stringify({ stock_symbol: stockSymbol })
    })
    .then(response => {
        if (response.status === 201) {
            return response.json();
        }
        return response.json().then(err => { throw new Error(err.error || 'Failed to add stock.') });
    })
    .then(() => {
        document.getElementById('stockForm').reset(); // Clear the input field
        loadPortfolioData(); // Refresh the portfolio table
    })
    .catch(error => {
        console.error("Error adding stock:", error);
        alert(error.message);
    });
}


function removeStock(button) {
    const row = button.closest('tr');
    const stockSymbol = row.dataset.symbol;
    if (confirm(`Are you sure you want to remove ${stockSymbol} from your portfolio?`)) {
        fetch(`/api/portfolio/${stockSymbol}/`, {
            method: 'DELETE',
            headers: headers,
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to remove stock.');
            }
            row.remove();
            // If the detailed view was open for this stock, minimize it
            if (currentSymbol === stockSymbol) {
                restoreTable();
            }
        })
        .catch(error => {
            console.error("Error removing stock:", error);
            alert(error.message);
        });
    }
}

function viewDetails(button) {
    let row = button.closest('tr');
    let table = document.getElementById('portfolioTable');
    let chartContainer = document.getElementById('chartContainer');
    let stockName = row.cells[0].textContent.trim(); // Get the stock name from the first cell
    currentSymbol = stockName; // Store the currently viewed stock

    // Clear the table and show only the selected stock
    table.innerHTML = '';
    table.appendChild(row); // Keep only the clicked row

    let actionCell = row.cells[1]; // Get the action cell
    actionCell.className = 'text-center'; // Apply text-center to the cell itself
    actionCell.innerHTML = `
        <button class='btn btn-primary-custom btn-sm' onclick='viewDetails(this)'>View Details</button>
        <button class='btn btn-danger-custom btn-sm ms-2' onclick='removeStock(this)'>Remove</button>
        <button class='btn btn-outline-custom btn-sm ms-2' onclick='restoreTable()'>Minimize View</button>
    `;

    chartContainer.classList.remove('d-none'); // Show charts and news section

    // Set the default active button for the date range
    const buttons = document.querySelectorAll('#dateRangeButtons .btn');
    buttons.forEach(button => button.classList.remove('active'));
    if (buttons.length > 1) {
        buttons[1].classList.add('active'); // Default to 1M
    }

    // Fetch all necessary data to initialize the charts
    initializeAllCharts(stockName);
    fetchStockNews(stockName); // Fetch news specific to the selected stock
}

async function initializeAllCharts(symbol) {
    try {
        // Fetch all data in parallel for efficiency
        const [historyResponse, predictionResponse] = await Promise.all([
            almanacAPI.getStockHistory(symbol, 30), // Default 30 days for both charts initially
            almanacAPI.getStockPredictions(symbol, 7)
        ]);

        // Check for valid data
        if (!historyResponse || !historyResponse.history || historyResponse.history.length === 0) {
            console.error('No historical data available for', symbol);
            fetchChartData(); // Fallback to dummy data
            return;
        }
        if (!predictionResponse || predictionResponse.error) {
            console.error('No prediction data available for', symbol, predictionResponse?.error);
            // If predictions fail, still show the historical chart
            updateHistoricalChart(historyResponse, symbol);
            return;
        }

        // Store data for later use
        fixedHistoryForPredictionChart = historyResponse;
        predictionDataStore = predictionResponse;

        // Render all charts with the initial data
        updateHistoricalChart(historyResponse, symbol);
        updatePredictionAndOtherCharts(fixedHistoryForPredictionChart, predictionDataStore, symbol);

    } catch (error) {
        console.error('Error initializing charts:', error);
        fetchChartData(); // Fallback to dummy data
    }
}

async function changeDateRange(days) {
    if (!currentSymbol) return;

    // Update active button state
    const buttons = document.querySelectorAll('#dateRangeButtons .btn');
    buttons.forEach(button => button.classList.remove('active'));
    let activeButton;
    switch(days) {
        case 7: activeButton = buttons[0]; break;
        case 30: activeButton = buttons[1]; break;
        case 365: activeButton = buttons[2]; break;
    }
    if (activeButton) activeButton.classList.add('active');

    try {
        // Fetch only the historical data for the new range
        const historyResponse = await almanacAPI.getStockHistory(currentSymbol, days);
        if (historyResponse && historyResponse.history && historyResponse.history.length > 0) {
            // Update ONLY the historical chart
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
    if (!history.length) {
        console.error('No historical data to draw chart.');
        return;
    }

    const labels = history.map(p => new Date(p.Date || p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    const prices = history.map(p => parseFloat(p.Close || p.close));

    // Chart 1: Historical prices only
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
    // This function is now responsible for the prediction, volume, and return charts.
    // It uses a fixed set of data and is not called by changeDateRange.

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

    // Chart 2: Combined historical and prediction chart
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

    // Chart 3: Volume chart
    createChart("chBar", "bar", {
        title: `${symbol} - Trading Volume (30 Days)`,
        labels: historicalLabels,
        datasets: [{
            label: 'Volume',
            data: volumes,
            backgroundColor: "#28a745"
        }]
    });

    // Chart 4: Predicted returns
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

function resetCharts() {
    // Destroy existing chart instances
    Object.values(chartInstances).forEach(chart => {
        if (chart) {
            chart.destroy();
        }
    });
    chartInstances = {};
}

function restoreTable() {
    // Simply reload the page to reset the table and hide chart/news sections
    location.reload();
}

function fetchChartData() {
    // This fetches generic chart data for demonstration.
    // In a real application, you'd fetch specific data for the selected stock.
    fetch("./static/json/chartdata.json")
        .then(response => response.json())
        .then(data => {
            createChart("chLine", "line", data.chart1);
            createChart("chLine2", "line", data.chart2);
            createChart("chBar", "bar", data.barChart);
            createChart("chScatter", "scatter", data.scatterChart);
        })
        .catch(error => console.error("Error loading chart data:", error));
}

function createChart(canvasId, type, chartData) {
    console.log(`Creating chart ${canvasId} with type ${type}`, chartData);
    
    let ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.warn(`Canvas element with ID '${canvasId}' not found.`);
        return;
    }
    ctx = ctx.getContext("2d");

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy(); // Destroy previous chart instance if it exists
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
                title: {
                    display: !!chartData.title,
                    text: chartData.title || ''
                },
                legend: {
                    display: true
                }
            },
            scales: type === 'scatter' ? {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Day'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Return %'
                    }
                }
            } : {
                y: {
                    beginAtZero: type === 'bar'
                }
            }
        }
    });
}

async function loadStockNames() {
    try {
        const response = await almanacAPI.getAvailableStocks();
        if (response && response.symbols) {
            let datalist = document.getElementById('datalistOptions');
            datalist.innerHTML = ''; // Clear existing options
            response.symbols.forEach(symbol => {
                let option = document.createElement('option');
                option.value = symbol;
                datalist.appendChild(option);
            });
        } else {
            // Fallback to JSON file
            loadStockNamesFromFile();
        }
    } catch (error) {
        console.error("Error loading stock names from API:", error);
        // Fallback to JSON file
        loadStockNamesFromFile();
    }
}

function loadStockNamesFromFile() {
    fetch("./static/json/stocknames.json")
        .then(response => response.json())
        .then(data => {
            let datalist = document.getElementById('datalistOptions');
            datalist.innerHTML = ''; // Clear existing options
            data.forEach(stock => {
                let option = document.createElement('option');
                option.value = stock.name;
                datalist.appendChild(option);
            });
        })
        .catch(error => console.error("Error loading stock names:", error));
}

function fetchStockNews(stockName) {
    fetch("./static/json/newsarticles.json")
        .then(response => response.json())
        .then(data => {
            const newsContent = document.getElementById("newsContent");
            newsContent.innerHTML = ""; // Clear previous news

            // Find news for the specific stock
            const stockNews = data.find(stock => stock.stock === stockName);

            if (!stockNews || stockNews.articles.length === 0) {
                newsContent.innerHTML = "<p>No recent news available for this stock.</p>";
                return;
            }

            const currentDate = new Date();
            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(currentDate.getDate() - 14); // Set date to 14 days ago

            let hasRecentNews = false;
            stockNews.articles.forEach(article => {
                const articleDate = new Date(article.date);
                if (articleDate >= twoWeeksAgo) { // Only show articles from the last 2 weeks
                    hasRecentNews = true;
                    const articleElement = document.createElement("div");
                    articleElement.classList.add("news-article", "mb-3"); // Add some bottom margin
                    articleElement.innerHTML = `
                        <h5><a href="${article.link}" target="_blank">${article.title}</a></h5>
                        <h6>${article.date}</h6>
                        <p>${article.description}</p>
                    `;
                    newsContent.appendChild(articleElement);
                }
            });

            if (!hasRecentNews) {
                newsContent.innerHTML = "<p>No recent news (last 2 weeks) available for this stock.</p>";
            }
        })
        .catch(error => {
            console.error("Error fetching stock news:", error);
            document.getElementById("newsContent").innerHTML = "<p>Error loading news.</p>";
        });
}