//API Client for Almanac Stock Prediction Service
// Half of it doesn't work, leaving for the next sprint 
// needs refactoring

class AlmanacAPI {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }

    async getAvailableStocks() {
        try {
            const response = await fetch(`${this.baseUrl}/available-stocks/`);
            if (!response.ok) throw new Error('Failed to fetch available stocks');
            return await response.json();
        } catch (error) {
            console.error('Error fetching stock symbols:', error);
            return { symbols: [] };
        }
    }

    async getMarketIndices() {
        try {
            const response = await fetch(`${this.baseUrl}/market-indices/`);
            if (!response.ok) throw new Error('Failed to fetch market indices');
            return await response.json();
        } catch (error) {
            console.error('Error fetching market indices:', error);
            return { indices: [] };
        }
    }

    async getStockHistory(symbol, days = 30) {
        try {
            const response = await fetch(`${this.baseUrl}/stock-history/${symbol}/?days=${days}`);
            if (!response.ok) throw new Error(`Failed to fetch history for ${symbol}`);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${symbol} history:`, error);
            return { symbol, history: [] };
        }
    }

    async getStocks(params = {}) {
        try {
            const queryParams = new URLSearchParams();
            if (params.symbol) queryParams.append('symbol', params.symbol);
            if (params.market) queryParams.append('market', params.market);
            
            const url = `${this.baseUrl}/stocks/?${queryParams.toString()}`;
            const response = await fetch(url);
            
            if (!response.ok) throw new Error('Failed to fetch stocks');
            return await response.json();
        } catch (error) {
            console.error('Error fetching stocks:', error);
            return { results: [] };
        }
    }

    async getStockDetails(symbol) {
        try {
            const response = await fetch(`${this.baseUrl}/stocks/?symbol=${symbol}`);
            if (!response.ok) throw new Error(`Failed to fetch details for ${symbol}`);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${symbol} details:`, error);
            return { results: [] };
        }
    }    
    
    async getStockPredictions(symbol, days = 7) {
        try {
            console.log(`Fetching predictions for ${symbol} with horizon ${days} days`);
            const response = await fetch(`${this.baseUrl}/predict-stock/?symbol=${symbol}&days=${days}`);
            const data = await response.json();
            
            if (!response.ok) {
                console.error(`Server error: ${data.error || 'Unknown error'}`);
                return { 
                    symbol, 
                    error: data.error || 'Failed to fetch predictions',
                    details: data.details || 'No additional details available'
                };
            }
            
            console.log(`Successfully retrieved predictions for ${symbol}`);
            return data;
        } catch (error) {
            console.error(`Error fetching ${symbol} predictions:`, error);
            return { symbol, error: error.message };
        }
    }
}

// Create a global instance
const almanacAPI = new AlmanacAPI();