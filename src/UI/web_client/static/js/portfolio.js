document.addEventListener("DOMContentLoaded", function () {
    loadPortfolioData();
    fetchChartData(); // This will load dummy charts initially or when View Details is clicked.
    loadStockNames();

    document.getElementById('stockForm').addEventListener('submit', function (event) {
        event.preventDefault();
        addStockToTable();
    });
});

let chartInstances = {}; // To manage Chart.js instances

function loadPortfolioData() {
    fetch("./static/json/portfoliodata.json")
        .then(response => response.json())
        .then(data => {
            let table = document.getElementById('portfolioTable');
            table.innerHTML = ''; // Clear existing table content
            data.forEach(stock => {
                let row = document.createElement('tr');
                row.innerHTML = `
                    <td class='text-center'>${stock.name}</td>
                    <td class='text-center'>
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

    let table = document.getElementById('portfolioTable');
    let row = document.createElement('tr');
    row.innerHTML = `
        <td class='text-center'>${name}</td>
        <td class='text-center'>
            <button class='btn btn-info btn-sm' onclick='viewDetails(this)'>View Details</button>
            <button class='btn btn-danger btn-sm' onclick='removeStock(this)'>Remove</button>
        </td>
    `;
    table.appendChild(row);

    document.getElementById('stockForm').reset(); // Clear the input field
}

function removeStock(button) {
    if (confirm("Are you sure you want to remove this stock?")) {
        button.closest('tr').remove();
        location.reload(); // Reload the page after removing the stock
    }
}

function viewDetails(button) {
    let row = button.closest('tr');
    let table = document.getElementById('portfolioTable');
    let chartContainer = document.getElementById('chartContainer');
    let stockName = row.cells[0].textContent.trim(); // Get the stock name from the first cell

    // Clear the table and show only the selected stock
    table.innerHTML = '';
    table.appendChild(row); // Keep only the clicked row

    
    let actionCell = row.cells[1]; // Get the action cell
    actionCell.className = 'text-center'; // Apply text-center to the cell itself
    actionCell.innerHTML = `
        <button class='btn btn-info btn-sm' onclick='viewDetails(this)'>View Details</button>
        <button class='btn btn-danger btn-sm' onclick='removeStock(this)'>Remove</button>
        <button class='btn btn-secondary btn-sm ms-2' onclick='restoreTable()'>Minimize View</button>
    `;

    chartContainer.classList.remove('d-none'); // Show charts and news section

    fetchChartData(); // Reload charts
    fetchStockNews(stockName); // Fetch news specific to the selected stock
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
            maintainAspectRatio: true
        }
    });
}

function loadStockNames() {
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