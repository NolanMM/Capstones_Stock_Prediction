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

    removeStockBtn.style.display = "none";

    function updateStock(stockName) {
        selectedStock.textContent = stockName;
        selectedStock.appendChild(removeStockBtn);
        removeStockBtn.style.display = "inline-block";
        stockInput.value = "";
         // Fetch stock data from the file and update the labels
        fetch("../json/stockdetails.json")
            .then(response => response.json())
            .then(data => {
                const stockData = data.find(stock => stock.name === stockName);
                if (stockData) {
                    document.getElementById("PriceAtClose").textContent = "Price At Close: " + stockData.priceAtClose;
                    document.getElementById("AfterHoursPrice").textContent = "After Hour Price: " + stockData.afterHoursPrice;
                    document.getElementById("PriceToEarnings").textContent = "Price To Earnings: " + stockData.priceToEarnings;
                    document.getElementById("PriceToBook").textContent = "Price To Book: " + stockData.priceToBook;
                }
            })
        .catch(error => {
            console.error("Error fetching stock data:", error);
        });

    fetchStockNews(stockName);
    document.getElementById("fourthSection").removeAttribute("hidden");
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

function createChart(ctx, type, data, options) {
    if (ctx) {
        new Chart(ctx, { type, data, options });
    }
}

const commonChartOptions = {
    scales: {
        yAxes: [{ ticks: { beginAtZero: false } }]
    },
    legend: { display: false }
};

fetch('../json/chartdata.json')
    .then(response => response.json())
    .then(data => {
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
    })
    .catch(error => console.error('Error fetching the JSON data:', error));