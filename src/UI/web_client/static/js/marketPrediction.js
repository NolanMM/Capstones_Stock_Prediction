document.addEventListener("DOMContentLoaded", function () {
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

        // Determine the label for "PriceAtClose" based on current time
        const now = new Date();
        const currentHour = now.getHours(); // Get the current hour (0-23)
        const currentDay = now.getDay(); // Get the current day of the week (0 for Sunday, 1 for Monday, etc.)

        let priceAtCloseLabel = "Price at Close";

        const isWeekday = currentDay >= 1 && currentDay <= 5;
        const isTradingHours = currentHour >= 9 && currentHour < 17;

        if (isWeekday && isTradingHours) {
            priceAtCloseLabel = "Yesterday's Close Price";
        }

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
                    setValue("CurrentPrice", "Current Price", stockData.currentPrice);
                    // Use the dynamically set label for PriceAtClose
                    setValue("PriceAtClose", priceAtCloseLabel, stockData.priceAtClose);
                    setValue("AfterHoursPrice", "After Hours Price", stockData.afterHoursPrice);
                    setValue("PriceToEarnings", "Price to Earnings", stockData.priceToEarnings);
                    setValue("PriceToBook", "Price to Book", stockData.priceToBook);
                }
            })
            .catch(error => {
                console.error("Error fetching stock data:", error);
            });

        fetchStockNews(stockName);
        document.getElementById("fourthSection").removeAttribute("hidden");
    }

    removeStockBtn.addEventListener("click", function () {
        stockInput.value = "";
        resetStockData();
        resetCharts();
    });

    function resetCharts() {
        const chartElements = [
            document.getElementById("chLine"),
            document.getElementById("chLine2"),
            document.getElementById("chBar"),
            document.getElementById("chScatter")
        ];

        chartElements.forEach(chartElement => {
            if (chartElement && chartElement.chart) {
                // Clear the dataset data
                chartElement.chart.data.datasets.forEach(dataset => {
                    dataset.data = [];
                });

                chartElement.chart.update();

                // Add glow effect back to the container
                const container = chartElement.parentElement;
                if (container) {
                    container.classList.add("placeholder-glow");
                }
            }
        });
    }

    function resetStockData() {
        selectedStock.textContent = "";
        removeStockBtn.style.display = "none";

        const fields = [
            { id: "CurrentPrice", label: "Current Price" },
            { id: "PriceAtClose", label: "Price at Close" }, // Default label
            { id: "AfterHoursPrice", label: "After Hours Price" },
            { id: "PriceToEarnings", label: "Price to Earnings" },
            { id: "PriceToBook", label: "Price to Book" }
        ];

        // Determine the label for "PriceAtClose" on reset
        const now = new Date();
        const currentHour = now.getHours();
        const currentDay = now.getDay();

        if (currentDay >= 1 && currentDay <= 5 && currentHour >= 9 && currentHour < 17) {
            fields[1].label = "Yesterday's Close Price"; // Update label for PriceAtClose
        }

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
            resetStockData(); // Reset first to ensure correct label before updating
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
            newsContent.innerHTML = "";
            newsRecentContent.innerHTML = ""; // Clear recent news as well

            const stockNews = data.find(stock => stock.stock === stockName);

            if (!stockNews) {
                newsContent.innerHTML = "<p>No news available for this stock.</p>";
                newsRecentContent.innerHTML = "";
                return;
            }

            const currentDate = new Date();
            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(currentDate.getDate() - 14);

            stockNews.articles.forEach(article => {
                const articleDate = new Date(article.date);

                const articleElement = document.createElement("div");
                articleElement.classList.add("news-article");
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
            document.getElementById("newsRecentContent").innerHTML = "";
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const stockInput = document.getElementById("DataList");
    const datalist = document.getElementById("datalistOptions");

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

const colors = ['#007bff', '#28a745', '#333333', '#c3e6cb', '#dc3545', '#6c757d'];

function createChart(ctx, type, data, options) {
    if (ctx) {
        // Add a custom title if predictions are present or not
        const hasPredictions = data.datasets.some(ds =>
            ds.label === "Predictions" || ds.label === "Fallback Predictions");

        // Update title to show prediction status
        if (options.title && options.title.text === "Stock Price History") {
            options.title.text = hasPredictions ?
                "Stock Price History with Predictions" :
                "Stock Price History (No Predictions Available)";
        }

        const chart = new Chart(ctx, { type, data, options });

        // Adjust the size of the chart placeholder after the chart has loaded
        const container = ctx.parentElement; // chart-placeholder div
        container.classList.remove("placeholder-glow"); // Remove the glow
        container.style.height = '400px'; // Set the height to auto to allow resizing
        return chart;
    }
}

const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        x: {
            ticks: {
            },
        },
        y: {
            beginAtZero: true,
        },
    },
    plugins: {

    },
};

fetch('../json/chartdata.json')
    .then(response => response.json())
    .then(data => {
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
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        // Custom tooltip to indicate predictions vs actual data
                        title: function (context) {
                            const datasetLabel = context[0].dataset.label || '';
                            if (datasetLabel.includes("Predictions")) {
                                return `Prediction for ${context[0].label}`;
                            }
                            return context[0].label;
                        },
                        label: function (context) {
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
        createChart(document.getElementById("chLine"), 'line', chartData1, chartOptions1);

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
    })
    .catch(error => console.error('Error fetching the JSON data:', error));