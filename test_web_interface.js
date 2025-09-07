#!/usr/bin/env node

const http = require('http');

// Test the web interface for basic functionality
async function testWebInterface() {
    console.log('Testing Cacherr Web Interface...\n');
    
    // Test health endpoint
    try {
        const healthResponse = await makeRequest('http://localhost:5445/health');
        console.log('✅ Health endpoint:', healthResponse.status);
        console.log('   Response:', JSON.stringify(healthResponse.data, null, 2));
    } catch (error) {
        console.log('❌ Health endpoint failed:', error.message);
    }
    
    // Test main page
    try {
        const mainResponse = await makeRequest('http://localhost:5445/');
        console.log('\n✅ Main page:', mainResponse.status);
        console.log('   Content-Type:', mainResponse.headers['content-type']);
        console.log('   Content length:', mainResponse.data.length);
        
        // Check if it's HTML
        if (mainResponse.data.includes('<html')) {
            console.log('   ✅ Valid HTML response');
        } else {
            console.log('   ❌ Invalid HTML response');
        }
        
        // Check for JavaScript assets
        const jsMatches = mainResponse.data.match(/assets\/.*\.js/g);
        if (jsMatches) {
            console.log('   ✅ JavaScript assets found:', jsMatches.length);
        } else {
            console.log('   ❌ No JavaScript assets found');
        }
        
        // Check for CSS assets
        const cssMatches = mainResponse.data.match(/assets\/.*\.css/g);
        if (cssMatches) {
            console.log('   ✅ CSS assets found:', cssMatches.length);
        } else {
            console.log('   ❌ No CSS assets found');
        }
        
    } catch (error) {
        console.log('❌ Main page failed:', error.message);
    }
    
    // Test API endpoints
    const apiEndpoints = [
        '/api/status',
        '/api/system/health',
        '/api/settings',
        '/api/logs'
    ];
    
    for (const endpoint of apiEndpoints) {
        try {
            const response = await makeRequest(`http://localhost:5445${endpoint}`);
            console.log(`\n✅ ${endpoint}:`, response.status);
            if (response.data) {
                console.log('   Response:', JSON.stringify(response.data, null, 2).substring(0, 200) + '...');
            }
        } catch (error) {
            console.log(`❌ ${endpoint} failed:`, error.message);
        }
    }
    
    console.log('\n🎉 Web interface testing completed!');
}

function makeRequest(url) {
    return new Promise((resolve, reject) => {
        const req = http.get(url, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                let parsedData = data;
                try {
                    if (res.headers['content-type']?.includes('application/json')) {
                        parsedData = JSON.parse(data);
                    }
                } catch (e) {
                    // Not JSON, keep as string
                }
                
                resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    data: parsedData
                });
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        req.setTimeout(5000, () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });
    });
}

// Run the test
testWebInterface().catch(console.error);
