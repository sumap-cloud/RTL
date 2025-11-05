#!/usr/bin/env python3
"""
Remote Test Agent for POS Testing
This agent runs on each POS machine to execute tests remotely
"""

import json
import subprocess
import datetime
import os
import sys
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import logging

class TestAgent:
    def __init__(self, machine_name: str, capabilities: list, port: int = 8080):
        self.machine_name = machine_name
        self.capabilities = capabilities
        self.port = port
        self.current_test = None
        self.status = "available"
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the agent"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"agent_{self.machine_name}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def execute_test(self, test_file: str, test_params: dict = None) -> dict:
        """Execute a test file and return results"""
        if self.status != "available":
            return {
                "status": "error",
                "message": f"Agent busy executing: {self.current_test}"
            }
        
        self.status = "busy"
        self.current_test = test_file
        start_time = datetime.datetime.now()
        
        try:
            self.logger.info(f"Executing test: {test_file}")
            
            # Prepare pytest command
            cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                "-v",
                f"--html=Reports/report_{self.machine_name}_{start_time.strftime('%H%M%S')}.html",
                "--self-contained-html",
                "--tb=short"
            ]
            
            # Add test parameters if provided
            if test_params:
                for key, value in test_params.items():
                    cmd.extend(["-D", f"{key}={value}"])
            
            # Execute test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
                cwd=os.getcwd()
            )
            
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            execution_result = {
                "status": "passed" if result.returncode == 0 else "failed",
                "test_file": test_file,
                "machine": self.machine_name,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
            self.logger.info(f"Test completed: {test_file} - Status: {execution_result['status']}")
            return execution_result
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test timed out: {test_file}")
            return {
                "status": "timeout",
                "test_file": test_file,
                "machine": self.machine_name,
                "error": "Test execution timed out after 10 minutes"
            }
        except Exception as e:
            self.logger.error(f"Error executing test {test_file}: {str(e)}")
            return {
                "status": "error",
                "test_file": test_file,
                "machine": self.machine_name,
                "error": str(e)
            }
        finally:
            self.status = "available"
            self.current_test = None
    
    def get_status(self) -> dict:
        """Get current agent status"""
        return {
            "machine_name": self.machine_name,
            "capabilities": self.capabilities,
            "status": self.status,
            "current_test": self.current_test,
            "timestamp": datetime.datetime.now().isoformat()
        }

class AgentRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, agent: TestAgent):
        self.agent = agent
        super().__init__()
    
    def __call__(self, *args, **kwargs):
        # Store agent reference
        self.agent = self.server.agent
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        self.agent.logger.info(f"HTTP: {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/status":
            self._send_json_response(self.agent.get_status())
        elif parsed_url.path == "/health":
            self._send_json_response({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/execute":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                test_file = request_data.get('test_file')
                test_params = request_data.get('test_params', {})
                
                if not test_file:
                    self._send_error(400, "Missing test_file parameter")
                    return
                
                # Execute test
                result = self.agent.execute_test(test_file, test_params)
                self._send_json_response(result)
                
            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON in request body")
            except Exception as e:
                self._send_error(500, f"Internal server error: {str(e)}")
        else:
            self._send_error(404, "Not Found")
    
    def _send_json_response(self, data: dict, status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_data = {"error": message, "status_code": status_code}
        self.wfile.write(json.dumps(error_data).encode())

class AgentServer:
    def __init__(self, agent: TestAgent):
        self.agent = agent
        self.server = None
        
    def start(self):
        """Start the agent server"""
        handler = lambda *args, **kwargs: AgentRequestHandler(*args, **kwargs)
        self.server = HTTPServer(('0.0.0.0', self.agent.port), handler)
        self.server.agent = self.agent  # Attach agent to server
        
        self.agent.logger.info(f"Starting test agent server on port {self.agent.port}")
        self.agent.logger.info(f"Machine: {self.agent.machine_name}")
        self.agent.logger.info(f"Capabilities: {', '.join(self.agent.capabilities)}")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.agent.logger.info("Agent server stopped by user")
            self.stop()
    
    def stop(self):
        """Stop the agent server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

def main():
    """Main function to start the agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="POS Test Agent")
    parser.add_argument("--name", required=True, help="Machine name")
    parser.add_argument("--capabilities", nargs='+', required=True, 
                       help="Machine capabilities (e.g., sale funds compliance)")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    
    args = parser.parse_args()
    
    # Create and start agent
    agent = TestAgent(args.name, args.capabilities, args.port)
    server = AgentServer(agent)
    
    print(f"🤖 Starting POS Test Agent: {args.name}")
    print(f"🔧 Capabilities: {', '.join(args.capabilities)}")
    print(f"🌐 Listening on port: {args.port}")
    print("📡 Agent ready to receive test execution requests...")
    print("Press Ctrl+C to stop")
    
    try:
        server.start()
    except Exception as e:
        print(f"❌ Error starting agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
