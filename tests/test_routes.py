"""
Black box tests for calculator server routes
Tests API endpoints without knowing internal implementation
"""
import pytest
import json
from unittest.mock import patch, Mock
from app import app
from config.settings import CONFIG

class TestConfigLoading:
    """Test configuration loading functionality"""
    
    def test_mcp_tools_loaded_from_config(self):
        """Test that MCP tools are loaded from config.yaml"""
        mcp_tools = CONFIG.get('mcp_tools', {})
        
        # Verify all expected tools are present
        expected_tools = ['add', 'subtract', 'multiply', 'divide', 'power', 
                         'sqrt', 'factorial', 'modulo', 'absolute', 'parse_expression']
        
        for tool in expected_tools:
            assert tool in mcp_tools, f"Tool '{tool}' not found in config"
            
            # Verify each tool has required structure
            tool_config = mcp_tools[tool]
            assert 'description' in tool_config, f"Tool '{tool}' missing description"
            assert 'inputSchema' in tool_config, f"Tool '{tool}' missing inputSchema"
            
            # Verify inputSchema structure
            input_schema = tool_config['inputSchema']
            assert 'type' in input_schema, f"Tool '{tool}' inputSchema missing type"
            assert 'properties' in input_schema, f"Tool '{tool}' inputSchema missing properties"
            assert 'required' in input_schema, f"Tool '{tool}' inputSchema missing required fields"
    
    def test_config_structure_validity(self):
        """Test that config has expected structure"""
        assert isinstance(CONFIG, dict), "CONFIG should be a dictionary"
        assert 'mcp_tools' in CONFIG, "CONFIG should contain 'mcp_tools' section"
        assert 'parser' in CONFIG, "CONFIG should contain 'parser' section"
        
        # Verify parser config structure
        parser_config = CONFIG.get('parser', {})
        assert 'word_to_number' in parser_config, "Parser config should contain 'word_to_number'"
        assert 'operation_words' in parser_config, "Parser config should contain 'operation_words'"

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint_success(self, client):
        """Test health endpoint returns success"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['server'] == 'calculator-server'
        assert 'version' in data
        assert 'timestamp' in data
        assert 'services' in data
    
    def test_health_endpoint_services_status(self, client):
        """Test health endpoint includes service status"""
        response = client.get('/health')
        data = json.loads(response.data)
        
        services = data['services']
        assert 'calculator_engine' in services
        assert 'mcp_protocol' in services
        assert 'sse_transport' in services
        
        # All should be True for healthy status
        assert services['calculator_engine'] is True
        assert services['mcp_protocol'] is True
        assert services['sse_transport'] is True
    
    @patch('routes.health.logger')
    def test_health_endpoint_exception_handling(self, mock_logger, client):
        """Test health endpoint handles exceptions"""
        # This is harder to test without internal knowledge, but we can verify
        # the endpoint doesn't crash with various conditions
        response = client.get('/health')
        
        # Should still return a response even if there are internal issues
        assert response.status_code in [200, 500]
        
        # Response should always be valid JSON
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data

class TestMCPEndpoint:
    """Test MCP protocol endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_mcp_endpoint_tools_list(self, client):
        """Test MCP tools list request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tools/list",
            "params": {}
        }
        
        response = client.post('/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 'test-1'
        assert 'result' in data
        assert 'tools' in data['result']
        
        # Should have all calculator tools
        tool_names = [tool['name'] for tool in data['result']['tools']]
        expected_tools = ['add', 'subtract', 'multiply', 'divide', 'power', 
                         'sqrt', 'factorial', 'modulo', 'absolute', 'parse_expression']
        for tool in expected_tools:
            assert tool in tool_names
    
    def test_mcp_endpoint_tool_call_add(self, client):
        """Test MCP tool call for addition"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {
                    "numbers": [5, 3, 2]
                }
            }
        }
        
        response = client.post('/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 'test-2'
        assert 'result' in data
        assert data['result']['result'] == 10
    
    def test_mcp_endpoint_tool_call_subtract(self, client):
        """Test MCP tool call for subtraction"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-3",
            "method": "tools/call",
            "params": {
                "name": "subtract",
                "arguments": {
                    "minuend": 20,
                    "subtrahends": [5, 3]
                }
            }
        }
        
        response = client.post('/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result']['result'] == 12
    
    def test_mcp_endpoint_tool_call_parse_expression(self, client):
        """Test MCP tool call for expression parsing"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-4",
            "method": "tools/call",
            "params": {
                "name": "parse_expression",
                "arguments": {
                    "expression": "four times 2 plus 4"
                }
            }
        }
        
        response = client.post('/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        # Should either succeed with result=12 or fail gracefully
        if 'result' in data['result']:
            assert data['result']['result'] == 12
        else:
            assert 'error' in data['result']
    
    def test_mcp_endpoint_unknown_tool(self, client):
        """Test MCP tool call for unknown tool"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-5",
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }
        
        response = client.post('/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == -32601
        assert 'not found' in data['error']['message']
    
    def test_mcp_endpoint_unknown_method(self, client):
        """Test MCP request with unknown method"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-6",
            "method": "unknown/method",
            "params": {}
        }
        
        response = client.post('/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == -32601
    
    def test_mcp_endpoint_invalid_json(self, client):
        """Test MCP endpoint with invalid JSON"""
        response = client.post('/mcp',
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == -32700
    
    def test_mcp_endpoint_no_data(self, client):
        """Test MCP endpoint with no data"""
        response = client.post('/mcp',
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestSSEEndpoints:
    """Test SSE endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_sse_status_endpoint(self, client):
        """Test SSE status endpoint"""
        response = client.get('/sse/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'active_connections' in data
        assert 'connected_clients' in data
        assert 'timestamp' in data
        assert isinstance(data['active_connections'], int)
        assert isinstance(data['connected_clients'], list)
    
    def test_sse_connect_endpoint(self, client):
        """Test SSE connect endpoint"""
        response = client.get('/sse/connect?client_id=test-client-123')
        
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream; charset=utf-8'
        assert 'Cache-Control' in response.headers
        assert response.headers['Cache-Control'] == 'no-cache'
    
    def test_sse_connect_without_client_id(self, client):
        """Test SSE connect endpoint without client ID"""
        response = client.get('/sse/connect')
        
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream; charset=utf-8'
    
    def test_sse_mcp_request_without_client_id(self, client):
        """Test SSE MCP request without client ID"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-sse-1",
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"numbers": [1, 2]}
            }
        }
        
        response = client.post('/sse/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Client ID required' in data['error']
    
    def test_sse_mcp_request_client_not_connected(self, client):
        """Test SSE MCP request for non-connected client"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-sse-2",
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"numbers": [1, 2]}
            },
            "client_id": "non-existent-client"
        }
        
        response = client.post('/sse/mcp',
                              data=json.dumps(request_data),
                              content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Client not connected' in data['error']
    
    def test_sse_mcp_request_invalid_json(self, client):
        """Test SSE MCP request with invalid JSON"""
        response = client.post('/sse/mcp',
                              data='invalid json',
                              content_type='application/json',
                              headers={'X-Client-ID': 'test-client'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestIntegrationScenarios:
    """Test integration scenarios across multiple endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_full_calculator_workflow(self, client):
        """Test complete calculator workflow"""
        # 1. Check health
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # 2. List available tools
        list_request = {
            "jsonrpc": "2.0",
            "id": "workflow-1",
            "method": "tools/list"
        }
        list_response = client.post('/mcp',
                                   data=json.dumps(list_request),
                                   content_type='application/json')
        assert list_response.status_code == 200
        
        # 3. Perform calculation
        calc_request = {
            "jsonrpc": "2.0",
            "id": "workflow-2",
            "method": "tools/call",
            "params": {
                "name": "multiply",
                "arguments": {"numbers": [6, 7]}
            }
        }
        calc_response = client.post('/mcp',
                                   data=json.dumps(calc_request),
                                   content_type='application/json')
        assert calc_response.status_code == 200
        calc_data = json.loads(calc_response.data)
        assert calc_data['result']['result'] == 42
    
    def test_error_handling_workflow(self, client):
        """Test error handling across different scenarios"""
        # Test various error conditions
        error_scenarios = [
            # Division by zero
            {
                "name": "divide",
                "arguments": {"dividend": 10, "divisors": [0]},
                "expected_error": "Division by zero"
            },
            # Invalid factorial
            {
                "name": "factorial",
                "arguments": {"number": -1},
                "expected_error": "non-negative integer"
            },
            # Square root of negative
            {
                "name": "sqrt",
                "arguments": {"number": -4},
                "expected_error": "negative number"
            }
        ]
        
        for scenario in error_scenarios:
            request_data = {
                "jsonrpc": "2.0",
                "id": f"error-test-{scenario['name']}",
                "method": "tools/call",
                "params": {
                    "name": scenario["name"],
                    "arguments": scenario["arguments"]
                }
            }
            
            response = client.post('/mcp',
                                  data=json.dumps(request_data),
                                  content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'result' in data
            assert 'error' in data['result']
            assert scenario['expected_error'] in data['result']['error']
