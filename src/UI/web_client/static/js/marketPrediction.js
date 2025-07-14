    document.addEventListener("DOMContentLoaded", function () {
    const addToPortfolioButtons = document.querySelectorAll('.portfoliobutton');
    const portfolioLink = document.querySelector('.nav-link[href="portfolio.html"]');
    const accountLink = document.querySelector('.nav-link[href="account.html"]');
    
    // Simulated check for login status, replace with your actual check
    function isLoggedIn() {
        // This is a placeholder. Replace it with your actual login check.
        return true; // Assuming the user is not logged in for this example
    }

    // If the user is not logged in, hide the "Add to Portfolio" buttons
    if (!isLoggedIn()) {
        addToPortfolioButtons.forEach(button => {
            button.style.display = 'none';
        });
        if (portfolioLink) {
            portfolioLink.style.display = 'none'; // Hide "Your Portfolio" link
        }
        
        if (accountLink) {
            accountLink.setAttribute('href', 'register.html'); // Change "Account" button to redirect to register.html
        }
    }
});


document.addEventListener("DOMContentLoaded", function () {
    const removeStockBtn = document.getElementById("removeStock");
    const selectedStock = document.getElementById("selectedStock");
    const stockInput = document.getElementById("DataList");
    const datalist = document.getElementById("datalistOptions");

    removeStockBtn.style.display = "none";    function updateStock(stockName) {
        selectedStock.textContent = stockName;
        selectedStock.appendChild(removeStockBtn);
        removeStockBtn.style.display = "inline-block";
        stockInput.value = "";
        
        // Show loading indicators
        const fields = [
            { id: "CurrentPrice", label: "Current Price" },
            { id: "PriceAtClose", label: "Price at Close" },
            { id: "AfterHoursPrice", label: "After Hours Price" },
            { id: "PriceToEarnings", label: "Price to Earnings" },
            { id: "PriceToBook", label: "Price to Book" }
        ];

        fields.forEach(field => {
            const element = document.getElementById(field.id);
            element.innerHTML = `${field.label}:<br><span class="placeholder col-4">.</span><span class="placeholder col-4">.</span><span class="placeholder col-4">.</span>`;
            element.classList.add("placeholder-glow");
        });
        
        // Fetch stock data from the file and update the labels
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
                    setValue("CurrentPrice", "Current Price", stockData.currentPrice || stockData.priceAtClose);
                    setValue("PriceAtClose", "Price at Close", stockData.priceAtClose);
                    setValue("AfterHoursPrice", "After Hour Price", stockData.afterHoursPrice);
                    setValue("PriceToEarnings", "Price to Earnings", stockData.priceToEarnings);
                    setValue("PriceToBook", "Price to Book", stockData.priceToBook);
                }
            })
            .catch(error => {
                console.error("Error fetching stock data:", error);
            });

        // Get prediction data and update charts
        fetchPredictionData(stockName);
        
        // Load news articles
        fetchStockNews(stockName);
        
        // Show the content section
        document.getElementById("fourthSection").removeAttribute("hidden");
    }
    
    async function fetchPredictionData(symbol) {
        try {
            // Reset the charts first
            resetCharts();
            
            // Fetch historical data
            const historyResponse = await almanacAPI.getStockHistory(symbol, 30);
            if (!historyResponse || !historyResponse.history || historyResponse.history.length === 0) {
                console.error('No historical data available for', symbol);
                return;
            }
            
            // Fetch prediction data
            const predictionResponse = await almanacAPI.getStockPredictions(symbol);
            if (predictionResponse.error) {
                console.error('Error fetching predictions:', predictionResponse.error);
                loadChartDataWithoutPredictions(symbol);
                return;
            }
            
            // Update charts with combined historical and prediction data
            updateChartsWithPredictions(historyResponse, predictionResponse);
        } catch (error) {
            console.error('Error in fetchPredictionData:', error);
            loadChartDataWithoutPredictions(symbol);
        }
    }
    
    function loadChartDataWithoutPredictions(symbol) {
        // Fallback to load the standard chart data without predictions
        fetch("../json/chartdata.json")
            .then(response => response.json())
            .then(data => {
                updateCharts(data);
            })
            .catch(error => {
                console.error('Error loading chart data:', error);
            });
    }

    removeStockBtn.addEventListener("click", function () {
    

    // Reset the input field
    stockInput.value = "";

    resetStockData()
    resetCharts();
});

function resetCharts() {
    // Reset chart data to initial state or empty state
    const chartElements = [document.getElementById("chLine"), document.getElementById("chLine2"), document.getElementById("chBar"), document.getElementById("chScatter")];
    
    chartElements.forEach(chartElement => {
        if (chartElement && chartElement.chart) {
            chartElement.chart.data.datasets.forEach(dataset => {
                dataset.data = [];
            });
            chartElement.chart.update();
        }
    });
}

function resetStockData() {
    // Reset the selected stock display
    selectedStock.textContent = "";
    removeStockBtn.style.display = "none";

    // Reset the stock data fields
    document.getElementById("PriceAtClose").textContent = "Price at Close";
    document.getElementById("AfterHoursPrice").textContent = "After Hours Price";
    document.getElementById("PriceToEarnings").textContent = "Price to Earnings";
    document.getElementById("PriceToBook").textContent = "Price to Book";

    // Clear the news content
    document.getElementById("newsContent").innerHTML = "";

    // Reset the charts (if needed)
    resetCharts();

    // Optionally, hide the fourth section until new data is loaded
    document.getElementById("fourthSection").setAttribute("hidden", true);
}

function resetCharts() {
    // Reset chart data to initial state or empty state
    const chartElements = [document.getElementById("chLine"), document.getElementById("chLine2"), document.getElementById("chBar"), document.getElementById("chScatter")];
    
    chartElements.forEach(chartElement => {
        if (chartElement && chartElement.chart) {
            chartElement.chart.data.datasets.forEach(dataset => {
                dataset.data = [];
            });
            chartElement.chart.update();
        }
    });
}

    stockInput.addEventListener("change", function () {
    const inputValue = stockInput.value.trim();
    const options = Array.from(datalist.options).map(option => option.value);
    
    // If the selected stock is in the options, reset and update
    if (options.includes(inputValue)) {
        // Reset the data before updating
        resetStockData();
        
        // Update the stock data
        updateStock(inputValue);
    } else {
        stockInput.value = "";
    }
});
});

function fetchStockNews(stockName) {
    fetch("../json/newsarticles.json")
        .then(response => response.json())
        .then(data => {
            const newsContent = document.getElementById("newsContent");
            const newsRecentContent = document.getElementById("newsRecentContent");
            newsContent.innerHTML = ""; // Clear the existing news content

            const stockNews = data.find(stock => stock.stock === stockName);

            if (!stockNews) {
                newsContent.innerHTML = "<p>No news available for this stock.</p>";
                return;
            }

            const currentDate = new Date();
            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(currentDate.getDate() - 14); // Calculate the date 14 days ago

            console.log('Current Date:', currentDate);
            console.log('Two Weeks Ago:', twoWeeksAgo);

            stockNews.articles.forEach(article => {
                const articleDate = new Date(article.date);
                console.log('Article Date:', articleDate);

                const articleElement = document.createElement("div");
                articleElement.classList.add("news-article");
                articleElement.innerHTML = `
                    <h5><a href="${article.link}" target="_blank">${article.title}</a></h5>
                    <h6>${article.date}</h6>
                    <p>${article.description}</p>
                `;

                // Check if the article date is within the last two weeks (recent) or older (historical)
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


document.addEventListener("DOMContentLoaded", function () {
    const stockInput = document.getElementById("DataList");
    const datalist = document.getElementById("datalistOptions");

    function fetchStockList() {
        fetch("../json/stocknames.json") // Fetch data from stocknames.json
            .then(response => response.json())
            .then(data => {
                datalist.innerHTML = ""; // Clear existing options
                
                data.forEach(stock => {
                    const option = document.createElement("option");
                    option.value = stock.name;
                    datalist.appendChild(option);
                });
            })
            .catch(error => console.error("Error fetching stocks:", error));
    }

    // Call fetchStockList to populate stocks dynamically
    fetchStockList();
});

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

const colors = ['#007bff','#28a745','#333333','#c3e6cb','#dc3545','#6c757d'];

// createChart function is now loaded from createChart.js

const commonChartOptions = {
    scales: {
        yAxes: [{ ticks: { beginAtZero: false } }]
    },
    legend: { display: false }
};

// Initial chart load is now handled in the updateStock function

// Function to update charts with just the base data
function updateCharts(data) {
    // Create the first chart
    const chartData1 = {
        labels: data.chart1.labels,
        datasets: data.chart1.datasets
    };

    const chartOptions1 = {
        ...commonChartOptions,
        title: {
            display: true,
            text: data.chart1.title,
            fontSize: 16,
            fontColor: '#333'
        }
    };
    createChart(document.getElementById("chLine"), 'line', chartData1, chartOptions1);

    // Create the second chart
    const chartData2 = {
        labels: data.chart2.labels,
        datasets: data.chart2.datasets
    };

    const chartOptions2 = {
        ...commonChartOptions,
        title: {
            display: true,
            text: data.chart2.title,
            fontSize: 16,
            fontColor: '#333'
        }
    };
    createChart(document.getElementById("chLine2"), 'line', chartData2, chartOptions2);

    // Create the bar chart
    const barData = {
        labels: data.barChart.labels,
        datasets: data.barChart.datasets
    };

    const barOptions = {
        ...commonChartOptions,
        title: {
            display: true,
            text: data.barChart.title,
            fontSize: 16,
            fontColor: '#333'
        }
    };
    createChart(document.getElementById("chBar"), 'bar', barData, barOptions);

    // Create the scatter chart
    const scatterData = {
        datasets: data.scatterChart.datasets
    };

    const scatterOptions = {
        ...commonChartOptions,
        title: {
            display: true,
            text: data.scatterChart.title,
            fontSize: 16,
            fontColor: '#333'
        }
    };
    createChart(document.getElementById("chScatter"), 'scatter', scatterData, scatterOptions);
}

// Function to update charts with predictions and historical data
function updateChartsWithPredictions(historyData, predictionData) {
    if (!historyData.history || historyData.history.length === 0) {
        console.error('No historical data available');
        return;
    }
    
    if (!predictionData.forecast || predictionData.forecast.length === 0) {
        console.error('No prediction data available');
        return;
    }
    
    // Process historical data
    const symbol = historyData.symbol;
    const history = historyData.history.sort((a, b) => new Date(a.Date) - new Date(b.Date));
    
    // Extract dates and prices for historical data
    const histDates = history.map(item => item.Date);
    const histPrices = history.map(item => parseFloat(item.Close));
    
    // Process prediction data
    const lastDate = predictionData.last_date;
    const lastPrice = predictionData.last_price;
    const forecast = predictionData.forecast;
    
    // Extract dates and prices for prediction data
    const predDates = forecast.map(item => item.date);
    const predPrices = forecast.map(item => item.price);
    
    // Combine dates and add a slight overlap for continuity
    const allDates = [...histDates, ...predDates];
    
    // Create the price history + prediction chart
    const priceHistoryData = {
        labels: allDates,
        datasets: [
            {
                label: symbol + " History",
                data: histPrices,
                borderColor: "#007bff",
                backgroundColor: "transparent",
                pointRadius: 2
            },
            {
                label: symbol + " Predictions",
                data: Array(histDates.length).fill(null).concat(predPrices),
                borderColor: "#28a745",
                backgroundColor: "rgba(40, 167, 69, 0.1)",
                borderDash: [5, 5],
                pointRadius: 3
            }
        ]
    };
    
    const priceHistoryOptions = {
        ...commonChartOptions,
        title: {
            display: true,
            text: "Stock Price History with Predictions",
            fontSize: 16,
            fontColor: '#333'
        },
        plugins: {
            tooltip: {
                callbacks: {
                    // Custom tooltip to indicate predictions vs actual data
                    title: function(context) {
                        const datasetLabel = context[0].dataset.label || '';
                        if (datasetLabel.includes("Predictions")) {
                            return `Prediction for ${context[0].label}`;
                        }
                        return context[0].label;
                    },
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label.includes("Predictions")) {
                            return `Predicted: ${context.formattedValue}`;
                        }
                        return `${label}: ${context.formattedValue}`;
                    }
                }
            }
        }
    };
    
    createChart(document.getElementById("chLine"), 'line', priceHistoryData, priceHistoryOptions);
    
    // Create the return percentage chart
    const returnsData = {
        labels: predDates,
        datasets: [
            {
                label: "Predicted Return %",
                data: forecast.map(item => item.return_pct),
                borderColor: "#dc3545",
                backgroundColor: "rgba(220, 53, 69, 0.1)",
                pointRadius: 3
            }
        ]
    };
    
    const returnsOptions = {
        ...commonChartOptions,
        title: {
            display: true,
            text: "Predicted Return Percentages",
            fontSize: 16,
            fontColor: '#333'
        }
    };
    
    createChart(document.getElementById("chLine2"), 'line', returnsData, returnsOptions);
    
    // Create a price comparison bar chart between last actual and last predicted
    const comparisonData = {
        labels: ["Current Price", "Predicted (End of Forecast)"],
        datasets: [
            {
                label: "Price Comparison",
                data: [lastPrice, predPrices[predPrices.length - 1]],
                backgroundColor: ["#007bff", "#28a745"]
            }
        ]
    };
    
    const comparisonOptions = {
        ...commonChartOptions,
        title: {
            display: true,
            text: "Current vs Predicted Price",
            fontSize: 16,
            fontColor: '#333'
        }
    };
    
    createChart(document.getElementById("chBar"), 'bar', comparisonData, comparisonOptions);
    
    // Create a scatter chart for prediction progression
    const scatterData = {
        datasets: [
            {
                label: "Price Progression",
                data: predPrices.map((price, i) => ({
                    x: i + 1,  // days into future
                    y: price
                })),
                borderColor: "#6f42c1",
                backgroundColor: "#6f42c1",
                pointRadius: 5
            }
        ]
    };
    
    const scatterOptions = {
        ...commonChartOptions,
        title: {
            display: true,
            text: "Prediction Progression",
            fontSize: 16,
            fontColor: '#333'
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: "Days into Future"
                }
            },
            y: {
                title: {
                    display: true,
                    text: "Predicted Price"
                }
            }
        }
    };
    
    createChart(document.getElementById("chScatter"), 'scatter', scatterData, scatterOptions);
}