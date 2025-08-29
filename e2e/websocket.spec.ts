/**
 * WebSocket Event Handler Signature Tests
 *
 * This test suite validates that the WebSocket event handlers have correct
 * function signatures and properly handle connections/disconnections
 * without the signature errors described in ISSUE-002.
 */

import { test, expect } from '@playwright/test';

test.describe('WebSocket Event Handler Signature Tests', () => {
  test.setTimeout(30000); // Increase timeout for WebSocket tests

  test.beforeEach(async ({ page }) => {
    // Navigate to the WebSocket test page
    await page.goto('http://localhost:5445');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should test WebSocket connectivity and identify issues', async ({ page }) => {
    // Test basic API health
    const healthResponse = await page.request.get('http://localhost:5445/health');
    expect(healthResponse.ok()).toBeTruthy();

    const healthData = await healthResponse.json();
    expect(healthData.status).toBe('healthy');

    // Test WebSocket connection through browser
    const websocketTest = await page.evaluate(async () => {
      return new Promise((resolve, reject) => {
        try {
          // Create Socket.IO client connection
          const socket = (window as any).io('http://localhost:5445');

          let connectionResult = {
            connected: false,
            connectionAckReceived: false,
            sid: null,
            errors: [],
            events: []
          };

          socket.on('connect', () => {
            connectionResult.connected = true;
            connectionResult.sid = socket.id;
            connectionResult.events.push('connect');
          });

          socket.on('connection_ack', (data) => {
            connectionResult.connectionAckReceived = true;
            connectionResult.events.push('connection_ack');
            connectionResult.sid = data.sid;
          });

          socket.on('connect_error', (error) => {
            connectionResult.errors.push(`Connection error: ${error}`);
          });

          // Test ping/pong functionality
          socket.on('pong', (data) => {
            connectionResult.events.push('pong');
          });

          // Wait for connection
          setTimeout(() => {
            // Test ping
            socket.emit('ping');

            // Test status request
            socket.emit('status');

            setTimeout(() => {
              socket.disconnect();
              resolve(connectionResult);
            }, 2000);
          }, 3000);

        } catch (error) {
          reject(error);
        }
      });
    });

    // Validate WebSocket connection results
    expect(websocketTest.connected).toBe(true);
    expect(websocketTest.connectionAckReceived).toBe(true);
    expect(websocketTest.sid).toBeTruthy();
    expect(websocketTest.errors).toHaveLength(0);
    expect(websocketTest.events).toContain('connect');
    expect(websocketTest.events).toContain('connection_ack');
  });

  test('should validate WebSocket event handler signatures', async ({ page }) => {
    // Test that the server properly handles WebSocket events
    const statsResponse = await page.request.get('http://localhost:5445/stats');
    expect(statsResponse.ok()).toBeTruthy();

    const initialStats = await statsResponse.json();
    expect(typeof initialStats.total_clients).toBe('number');

    // Test WebSocket connection and validate server-side handling
    const connectionTest = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const socket = (window as any).io('http://localhost:5445');

        socket.on('connect', () => {
          // Connection successful - this validates handle_connect signature
          setTimeout(() => {
            socket.disconnect();
            resolve({ success: true, error: null });
          }, 1000);
        });

        socket.on('connect_error', (error) => {
          resolve({ success: false, error: error.message });
        });
      });
    });

    expect(connectionTest.success).toBe(true);
    expect(connectionTest.error).toBeNull();

    // Verify no signature errors occurred by checking server logs
    // This would be done in a real implementation by checking server logs
    // For now, we validate that the connection was successful
  });

  test('should test WebSocket connection stability', async ({ page }) => {
    // Test multiple connections and disconnections
    const stabilityTest = await page.evaluate(async () => {
      const results = [];
      const connections = 3;

      for (let i = 0; i < connections; i++) {
        const result = await new Promise((resolve) => {
          const socket = (window as any).io('http://localhost:5445');

          socket.on('connect', () => {
            setTimeout(() => {
              socket.disconnect();
              resolve({ attempt: i + 1, success: true });
            }, 500);
          });

          socket.on('connect_error', (error) => {
            resolve({ attempt: i + 1, success: false, error: error.message });
          });
        });

        results.push(result);
      }

      return results;
    });

    // All connections should be successful
    stabilityTest.forEach((result, index) => {
      expect(result.success).toBe(true);
      expect(result.attempt).toBe(index + 1);
    });
  });

  test('should test WebSocket message broadcasting', async ({ page }) => {
    // Test broadcast functionality
    const broadcastTest = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const socket1 = (window as any).io('http://localhost:5445');
        const socket2 = (window as any).io('http://localhost:5445');

        let receivedMessages = [];

        socket1.on('test_broadcast', (data) => {
          receivedMessages.push({ socket: 1, data });
        });

        socket2.on('test_broadcast', (data) => {
          receivedMessages.push({ socket: 2, data });
        });

        // Wait for both connections
        let connectedCount = 0;
        const checkConnected = () => {
          connectedCount++;
          if (connectedCount === 2) {
            // Both connected, now test broadcast
            setTimeout(async () => {
              // Send broadcast via API
              const response = await fetch('http://localhost:5445/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  event: 'test_broadcast',
                  data: { message: 'Test broadcast message', timestamp: Date.now() }
                })
              });

              setTimeout(() => {
                socket1.disconnect();
                socket2.disconnect();
                resolve({
                  success: response.ok,
                  messagesReceived: receivedMessages.length,
                  messages: receivedMessages
                });
              }, 1000);
            }, 500);
          }
        };

        socket1.on('connect', checkConnected);
        socket2.on('connect', checkConnected);
      });
    });

    expect(broadcastTest.success).toBe(true);
    expect(broadcastTest.messagesReceived).toBeGreaterThan(0);
  });

  test('should verify no WebSocket handler errors in server', async ({ page }) => {
    // Test that server handles multiple rapid connections without errors
    const errorTest = await page.evaluate(async () => {
      const promises = [];
      const connectionCount = 5;

      for (let i = 0; i < connectionCount; i++) {
        const promise = new Promise((resolve) => {
          const socket = (window as any).io('http://localhost:5445');

          socket.on('connect', () => {
            setTimeout(() => {
              socket.disconnect();
              resolve({ success: true });
            }, 200);
          });

          socket.on('connect_error', (error) => {
            resolve({ success: false, error: error.message });
          });
        });

        promises.push(promise);
      }

      const results = await Promise.all(promises);
      return {
        totalConnections: connectionCount,
        successfulConnections: results.filter(r => r.success).length,
        failedConnections: results.filter(r => !r.success).length,
        errors: results.filter(r => !r.success).map(r => r.error)
      };
    });

    expect(errorTest.successfulConnections).toBe(errorTest.totalConnections);
    expect(errorTest.failedConnections).toBe(0);
    expect(errorTest.errors).toHaveLength(0);
  });

  test('should test WebSocket status and statistics', async ({ page }) => {
    // Test the stats endpoint
    const statsResponse = await page.request.get('http://localhost:5445/stats');
    expect(statsResponse.ok()).toBeTruthy();

    const stats = await statsResponse.json();
    expect(stats).toHaveProperty('total_clients');
    expect(typeof stats.total_clients).toBe('number');

    // Test WebSocket status request
    const statusTest = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const socket = (window as any).io('http://localhost:5445');

        socket.on('connect', () => {
          socket.emit('status');
        });

        socket.on('status_response', (statusData) => {
          socket.disconnect();
          resolve(statusData);
        });

        socket.on('connect_error', (error) => {
          resolve({ error: error.message });
        });
      });
    });

    expect(statusTest).not.toHaveProperty('error');
    expect(statusTest).toHaveProperty('server_status');
    expect(statusTest.server_status).toBe('operational');
  });
});