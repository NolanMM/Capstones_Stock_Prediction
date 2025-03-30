document.addEventListener("DOMContentLoaded", function () {
    loadPortfolioData();
    fetchChartData();
    loadStockNames();

    // Attach the event listener for form submission
    document.getElementById('stockForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent default form submission behavior
        addStockToTable();
    });
});

let chartInstances = {}; // Store chart instances globally

function loadPortfolioData() {
    fetch("./static/json/portfoliodata.json")
        .then(response => response.json())
        .then(data => {
            let table = document.getElementById('portfolioTable');
            table.innerHTML = '';
            data.forEach(stock => {
                let row = document.createElement('tr');
                row.innerHTML = `
                    <td>${stock.name}</td>
                    <td>$${stock.pricePaid}</td>
                    <td>${stock.quantity}</td>
                    <td>${stock.purchaseDate}</td>
                    <td>${stock.roi}</td>
                    <td>
                        <button class='btn btn-info btn-sm' onclick='viewDetails(this)'>View Details</button>
                        <button class='btn btn-danger btn-sm' onclick='removeStock(this)'>Remove</button>
                    </td>
                `;
                table.appendChild(row);
            });
        })
        .catch(error => console.error("Error loading portfolio data:", error));
}

function addStockToTable() {
    let name = document.getElementById('name').value;
    let pricePaid = document.getElementById('stockPrice').value;
    let quantity = document.getElementById('stockQuantity').value;
    let purchaseDate = document.getElementById('stockDate').value;

    // Calculate ROI or other logic if needed
    let roi = calculateROI(pricePaid, quantity); // Placeholder for ROI calculation

    let table = document.getElementById('portfolioTable');
    let row = document.createElement('tr');
    row.innerHTML = `
        <td>${name}</td>
        <td>$${pricePaid}</td>
        <td>${quantity}</td>
        <td>${purchaseDate}</td>
        <td>${roi}</td>
        <td>
            <button class='btn btn-info btn-sm' onclick='viewDetails(this)'>View Details</button>
            <button class='btn btn-danger btn-sm' onclick='removeStock(this)'>Remove</button>
        </td>
    `;
    table.appendChild(row);

    // Optionally reset the form after adding the stock
    document.getElementById('stockForm').reset();
}

function calculateROI(pricePaid, quantity) {
    // Add your ROI calculation logic here
    // For now, it's a simple placeholder that returns '0%' for demonstration
    return "0%";
}

function removeStock(button) {
    button.closest('tr').remove();
}

function viewDetails(button) {
    let row = button.closest('tr');
    let table = document.getElementById('portfolioTable');
    let minimizeBtn = document.getElementById('minimizeView');
    let chartContainer = document.getElementById('chartContainer');

    // Get the stock name from the selected row (assuming the stock name is in the first cell of the row)
    let stockName = row.cells[0].textContent.trim(); // Adjust this selector based on your table structure

    // Move selected row to the top
    table.innerHTML = '';
    table.appendChild(row);

    // Show charts
    chartContainer.classList.remove('d-none');
    minimizeBtn.classList.remove('d-none');

    // Fetch and update charts
    fetchChartData();

    // Fetch and update News
    fetchStockNews(stockName);
}

function restoreTable() {
    location.reload(); // Reloading restores the full table
}

// Fetch Chart Data and Populate Charts
function fetchChartData() {
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

// Create Chart Function
function createChart(canvasId, type, chartData) {
    let ctx = document.getElementById(canvasId).getContext("2d");

    // Destroy existing chart if it exists (avoids duplicate charts)
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    // Construct Chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: type,
        data: {
            labels: chartData.labels || [],
            datasets: chartData.datasets || []
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
}


function loadStockNames() {
    fetch("./static/json/stocknames.json") // Fetch the JSON file with stock symbols
        .then(response => response.json())
        .then(data => {
            let datalist = document.getElementById('datalistOptions');
            datalist.innerHTML = ''; // Clear existing datalist items

            // Ensure data is in the expected format and loop through it
            data.forEach(stock => {
                let option = document.createElement('option');
                option.value = stock.name; // Set the stock symbol as the option value
                datalist.appendChild(option); // Add the option to the datalist
            });
        })
        .catch(error => console.error("Error loading stock names:", error));
}


function fetchStockNews(stockName) {
    fetch("./static/json/newsarticles.json")
        .then(response => response.json())
        .then(data => {
            const newsContent = document.getElementById("newsContent");
            newsContent.innerHTML = ""; // Clear the existing news content

            const stockNews = data.find(stock => stock.stock === stockName);

            if (!stockNews) {
                newsContent.innerHTML = "<p>No news available for this stock.</p>";
                return;
            }

            const currentDate = new Date();
            const twoWeeksAgo = new Date();
            twoWeeksAgo.setDate(currentDate.getDate() - 14); // Calculate the date 14 days ago

            stockNews.articles.forEach(article => {
                const articleDate = new Date(article.date);

                // Only include articles that are within the last 2 weeks
                if (articleDate >= twoWeeksAgo) {
                    const articleElement = document.createElement("div");
                    articleElement.classList.add("news-article");
                    articleElement.innerHTML = `
                        <h5><a href="${article.link}" target="_blank">${article.title}</a></h5>
                        <h6>${article.date}</h6>
                        <p>${article.description}</p>
                    `;
                    newsContent.appendChild(articleElement);
                }
            });
        })
        .catch(error => {
            console.error("Error fetching stock news:", error);
            document.getElementById("newsContent").innerHTML = "<p>Error loading news.</p>";
        });
}