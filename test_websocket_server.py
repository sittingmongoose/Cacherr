#!/usr/bin/env python3
"""
Simple WebSocket server test script.

This script starts the WebSocket server and performs basic validation
to ensure the WebSocket functionality works correctly.
"""

import sys
import os
import time
import threading
import requests
import socketio
from src.core.websocket_manager import WebSocketManager

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_server_health():
    """Test that the server health endpoint is working."""
    try:
        response = requests.get('http://localhost:5445/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server health check PASSED")
            print(f"   Status: {data.get('status')}")
            print(f"   WebSocket clients: {data.get('websocket_clients')}")
            return True
        else:
            print(f"❌ Server health check FAILED: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Server health check FAILED: {e}")
        return False

def test_api_endpoint():
    """Test the API info endpoint."""
    try:
        response = requests.get('http://localhost:5445/api', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint test PASSED")
            print(f"   Name: {data.get('name')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ API endpoint test FAILED: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ API endpoint test FAILED: {e}")
        return False

def test_websocket_connection():
    """Test WebSocket connection and basic functionality."""
    try:
        sio = socketio.Client()

        connection_results = {
            'connected': False,
            'connection_ack_received': False,
            'sid': None,
            'ping_response': False,
            'status_response': False,
            'errors': []
        }

        @sio.on('connect')
        def on_connect():
            connection_results['connected'] = True
            print("✅ WebSocket connection established")

        @sio.on('connection_ack')
        def on_connection_ack(data):
            connection_results['connection_ack_received'] = True
            connection_results['sid'] = data.get('sid')
            print(f"✅ Connection acknowledged: {data.get('sid')}")

        @sio.on('pong')
        def on_pong(data):
            connection_results['ping_response'] = True
            print("✅ Ping response received")

        @sio.on('status_response')
        def on_status_response(data):
            connection_results['status_response'] = True
            print(f"✅ Status response received: {data.get('server_status')}")

        @sio.on('connect_error')
        def on_connect_error(error):
            connection_results['errors'].append(f"Connection error: {error}")
            print(f"❌ WebSocket connection error: {error}")

        @sio.on('error')
        def on_error(error):
            connection_results['errors'].append(f"Socket error: {error}")
            print(f"❌ WebSocket error: {error}")

        # Connect to the server
        print("🔌 Connecting to WebSocket server...")
        sio.connect('http://localhost:5445')

        # Wait a bit for connection
        time.sleep(2)

        if connection_results['connected']:
            # Test ping functionality
            sio.emit('ping')
            time.sleep(1)

            # Test status request
            sio.emit('status')
            time.sleep(1)

        # Disconnect
        sio.disconnect()
        time.sleep(1)

        # Validate results
        success = True

        if not connection_results['connected']:
            print("❌ WebSocket connection FAILED")
            success = False

        if not connection_results['connection_ack_received']:
            print("❌ Connection acknowledgment FAILED")
            success = False

        if connection_results['errors']:
            print(f"❌ WebSocket errors: {connection_results['errors']}")
            success = False

        if success:
            print("✅ WebSocket functionality test PASSED")
            print(f"   Connected with SID: {connection_results['sid']}")

        return success

    except Exception as e:
        print(f"❌ WebSocket test FAILED: {e}")
        return False

def test_broadcast_functionality():
    """Test WebSocket broadcasting functionality."""
    try:
        # Create two clients
        sio1 = socketio.Client()
        sio2 = socketio.Client()

        broadcast_results = {
            'client1_connected': False,
            'client2_connected': False,
            'client1_received': False,
            'client2_received': False,
            'broadcast_sent': False
        }

        @sio1.on('connect')
        def on_connect1():
            broadcast_results['client1_connected'] = True

        @sio1.on('test_broadcast')
        def on_broadcast1(data):
            broadcast_results['client1_received'] = True
            print(f"✅ Client 1 received broadcast: {data.get('message')}")

        @sio2.on('connect')
        def on_connect2():
            broadcast_results['client2_connected'] = True

        @sio2.on('test_broadcast')
        def on_broadcast2(data):
            broadcast_results['client2_received'] = True
            print(f"✅ Client 2 received broadcast: {data.get('message')}")

        # Connect both clients
        print("🔌 Connecting two WebSocket clients for broadcast test...")
        sio1.connect('http://localhost:5445')
        sio2.connect('http://localhost:5445')

        # Wait for connections
        time.sleep(3)

        # Send broadcast via API
        if broadcast_results['client1_connected'] and broadcast_results['client2_connected']:
            try:
                response = requests.post('http://localhost:5445/broadcast', json={
                    'event': 'test_broadcast',
                    'data': {'message': 'Test broadcast message', 'timestamp': time.time()}
                }, timeout=5)

                if response.status_code == 200:
                    broadcast_results['broadcast_sent'] = True
                    print("✅ Broadcast request sent successfully")
                else:
                    print(f"❌ Broadcast request failed: {response.status_code}")
            except requests.RequestException as e:
                print(f"❌ Broadcast request error: {e}")
        else:
            print("❌ Clients not connected for broadcast test")

        # Wait for broadcast to be received
        time.sleep(2)

        # Disconnect clients
        sio1.disconnect()
        sio2.disconnect()
        time.sleep(1)

        # Validate results
        success = True

        if not broadcast_results['broadcast_sent']:
            print("❌ Broadcast not sent")
            success = False

        if not broadcast_results['client1_received']:
            print("❌ Client 1 did not receive broadcast")
            success = False

        if not broadcast_results['client2_received']:
            print("❌ Client 2 did not receive broadcast")
            success = False

        if success:
            print("✅ Broadcast functionality test PASSED")

        return success

    except Exception as e:
        print(f"❌ Broadcast test FAILED: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Cacherr WebSocket Server")
    print("=" * 50)

    # Give server time to start if it's starting up
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)

    tests = [
        ("Server Health Check", test_server_health),
        ("API Endpoint Test", test_api_endpoint),
        ("WebSocket Connection Test", test_websocket_connection),
        ("Broadcast Functionality Test", test_broadcast_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All WebSocket server tests PASSED!")
        print("✅ WebSocket functionality is working correctly!")
        return 0
    else:
        print("❌ Some tests failed. Check the server implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())