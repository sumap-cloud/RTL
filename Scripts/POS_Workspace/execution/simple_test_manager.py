"""
Simple Test Scheduler and Executor for POS Testing
Handles batch execution across multiple machines without external dependencies
"""

import json
import subprocess
import datetime
import os
import logging
import concurrent.futures
import time
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import csv

@dataclass
class Machine:
    ip: str
    name: str
    capabilities: List[str]
    status: str = "available"
    current_test: str = None

@dataclass
class TestExecution:
    test_file: str
    machine_name: str
    machine_ip: str
    status: str = "pending"
    start_time: str = None
    end_time: str = None
    duration: float = 0
    output: str = ""
    error: str = ""

class SimpleTestManager:
    def __init__(self):
        """Initialize the simple test manager"""
        self.machines = self._load_machines()
        self.test_drops = self._load_test_drops()
        self.executions = []
        self.setup_logging()
    
    def _load_machines(self) -> List[Machine]:
        """Load machine configuration from JSON/CSV"""
        machines = [
            Machine("192.168.1.10", "Banner1_POS1", ["sale", "returns", "funds"]),
            Machine("192.168.1.11", "Banner1_POS2", ["sale", "loyalty", "compliance"]),
            Machine("192.168.2.10", "Banner2_POS1", ["sale", "returns", "funds"]),
            Machine("192.168.2.11", "Banner2_POS2", ["sale", "loyalty", "compliance"]),
            Machine("192.168.3.10", "Banner3_POS1", ["sale", "returns", "funds"]),
            Machine("192.168.4.10", "Banner4_POS1", ["sale", "returns", "funds"]),
            Machine("192.168.5.10", "Banner5_POS1", ["sale", "returns", "funds"]),
            Machine("192.168.6.10", "Banner6_POS1", ["sale", "returns", "funds"]),
        ]
        return machines
    
    def _load_test_drops(self) -> Dict[str, Dict]:
        """Load test drop configuration"""
        return {
            "drop1_basic_sale": {
                "description": "Basic POS sale functionality",
                "tests": ["test1_pos_flow.py"],
                "required_capabilities": ["sale"]
            },
            "drop2_funds_management": {
                "description": "Funds management and cash handling",
                "tests": ["tests/fundsmanagement/TC001_paidout.py"],
                "required_capabilities": ["funds"]
            },
            "drop3_compliance": {
                "description": "Age restrictions and legislation",
                "tests": ["tests/Legistlation/*.py"],
                "required_capabilities": ["compliance"]
            }
        }
    
    def setup_logging(self):
        """Setup logging for test execution"""
        os.makedirs("Reports", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"Reports/test_execution_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_available_machine(self, required_capabilities: List[str]) -> Machine:
        """Get first available machine with required capabilities"""
        for machine in self.machines:
            if (machine.status == "available" and 
                all(cap in machine.capabilities for cap in required_capabilities)):
                return machine
        return None
    
    def execute_test_local(self, test_file: str, machine: Machine) -> TestExecution:
        """Execute test locally (simulating remote execution)"""
        execution = TestExecution(
            test_file=test_file,
            machine_name=machine.name,
            machine_ip=machine.ip,
            start_time=datetime.datetime.now().isoformat()
        )
        
        machine.status = "busy"
        machine.current_test = test_file
        
        try:
            self.logger.info(f"Executing {test_file} on {machine.name}")
            
            # Prepare pytest command
            cmd = [
                "python", "-m", "pytest", 
                test_file, 
                "-v", 
                f"--html=Reports/report_{machine.name}_{datetime.datetime.now().strftime('%H%M%S')}.html",
                "--self-contained-html"
            ]
            
            # Execute test
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10 minutes timeout
                cwd=os.getcwd()
            )
            
            execution.end_time = datetime.datetime.now().isoformat()
            execution.duration = (datetime.datetime.fromisoformat(execution.end_time) - 
                                datetime.datetime.fromisoformat(execution.start_time)).total_seconds()
            execution.status = "passed" if result.returncode == 0 else "failed"
            execution.output = result.stdout
            execution.error = result.stderr
            
            self.logger.info(f"Completed {test_file} on {machine.name} - Status: {execution.status}")
            
        except subprocess.TimeoutExpired:
            execution.status = "timeout"
            execution.error = "Test execution timed out"
            self.logger.error(f"Test {test_file} timed out on {machine.name}")
        except Exception as e:
            execution.status = "error"
            execution.error = str(e)
            self.logger.error(f"Error executing {test_file} on {machine.name}: {str(e)}")
        finally:
            machine.status = "available"
            machine.current_test = None
        
        return execution
    
    def execute_test_drop(self, drop_name: str) -> List[TestExecution]:
        """Execute all tests in a test drop"""
        if drop_name not in self.test_drops:
            raise ValueError(f"Test drop {drop_name} not found")
        
        drop_config = self.test_drops[drop_name]
        test_files = drop_config["tests"]
        required_capabilities = drop_config["required_capabilities"]
        
        self.logger.info(f"Starting test drop: {drop_config['description']}")
        
        executions = []
        
        # Use ThreadPoolExecutor for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.machines)) as executor:
            futures = []
            
            for test_file in test_files:
                # Wait for available machine
                while True:
                    machine = self.get_available_machine(required_capabilities)
                    if machine:
                        break
                    time.sleep(1)  # Wait 1 second before checking again
                
                # Submit test execution
                future = executor.submit(self.execute_test_local, test_file, machine)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                execution = future.result()
                executions.append(execution)
                self.executions.append(execution)
        
        return executions
    
    def execute_all_drops(self) -> Dict:
        """Execute all test drops"""
        all_results = {}
        start_time = datetime.datetime.now()
        
        for drop_name in self.test_drops.keys():
            try:
                executions = self.execute_test_drop(drop_name)
                all_results[drop_name] = {
                    "executions": executions,
                    "total_tests": len(executions),
                    "passed": len([e for e in executions if e.status == "passed"]),
                    "failed": len([e for e in executions if e.status == "failed"]),
                    "errors": len([e for e in executions if e.status == "error"])
                }
            except Exception as e:
                self.logger.error(f"Error executing drop {drop_name}: {str(e)}")
                all_results[drop_name] = {"error": str(e)}
        
        end_time = datetime.datetime.now()
        
        summary = {
            "execution_start": start_time.isoformat(),
            "execution_end": end_time.isoformat(),
            "total_duration": (end_time - start_time).total_seconds(),
            "drop_results": all_results
        }
        
        self._generate_reports(summary)
        return summary
    
    def _generate_reports(self, summary: Dict):
        """Generate execution reports"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate JSON report
        json_report = Path(f"Reports/execution_summary_{timestamp}.json")
        
        # Convert executions to dictionaries for JSON serialization
        summary_for_json = summary.copy()
        for drop_name, drop_data in summary_for_json["drop_results"].items():
            if "executions" in drop_data:
                drop_data["executions"] = [asdict(exec) for exec in drop_data["executions"]]
        
        with open(json_report, 'w') as f:
            json.dump(summary_for_json, f, indent=2)
        
        # Generate CSV report
        self._generate_csv_report(timestamp)
        
        # Generate HTML report
        self._generate_html_report(summary, timestamp)
        
        self.logger.info(f"Reports generated in Reports directory")
    
    def _generate_csv_report(self, timestamp: str):
        """Generate CSV report of all executions"""
        csv_file = Path(f"Reports/execution_details_{timestamp}.csv")
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Test File", "Machine Name", "Machine IP", "Status", 
                "Start Time", "End Time", "Duration (s)", "Error"
            ])
            
            for execution in self.executions:
                writer.writerow([
                    execution.test_file,
                    execution.machine_name,
                    execution.machine_ip,
                    execution.status,
                    execution.start_time,
                    execution.end_time,
                    execution.duration,
                    execution.error
                ])
    
    def _generate_html_report(self, summary: Dict, timestamp: str):
        """Generate HTML execution report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>POS Test Execution Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
                .summary {{ background-color: #e9f4ff; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .summary h2 {{ color: #007bff; margin-top: 0; }}
                .drop {{ margin: 20px 0; border: 1px solid #ddd; padding: 20px; border-radius: 8px; background-color: #fafafa; }}
                .drop h3 {{ color: #333; margin-top: 0; }}
                .stats {{ display: flex; gap: 20px; margin: 10px 0; }}
                .stat {{ background-color: white; padding: 10px 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                .passed {{ color: #28a745; font-weight: bold; }}
                .failed {{ color: #dc3545; font-weight: bold; }}
                .error {{ color: #fd7e14; font-weight: bold; }}
                .machine-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px; }}
                .machine {{ background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; }}
                .machine.busy {{ border-left: 4px solid #ffc107; }}
                .machine.available {{ border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏪 POS Multi-Banner Test Execution Report</h1>
                    <p>Distributed testing across 6 banners and multiple machines</p>
                </div>
                
                <div class="summary">
                    <h2>📊 Execution Summary</h2>
                    <div class="stats">
                        <div class="stat">
                            <strong>Start Time:</strong><br>{summary['execution_start']}
                        </div>
                        <div class="stat">
                            <strong>End Time:</strong><br>{summary['execution_end']}
                        </div>
                        <div class="stat">
                            <strong>Total Duration:</strong><br>{summary['total_duration']:.2f} seconds
                        </div>
                        <div class="stat">
                            <strong>Total Drops:</strong><br>{len(summary['drop_results'])}
                        </div>
                    </div>
                </div>
                
                <h2>🧪 Test Drop Results</h2>
        """
        
        for drop_name, drop_result in summary['drop_results'].items():
            if isinstance(drop_result, dict) and 'total_tests' in drop_result:
                html_content += f"""
                <div class="drop">
                    <h3>📋 {drop_name.replace('_', ' ').title()}</h3>
                    <div class="stats">
                        <div class="stat">
                            <strong>Total Tests:</strong><br>{drop_result.get('total_tests', 0)}
                        </div>
                        <div class="stat passed">
                            <strong>Passed:</strong><br>{drop_result.get('passed', 0)}
                        </div>
                        <div class="stat failed">
                            <strong>Failed:</strong><br>{drop_result.get('failed', 0)}
                        </div>
                        <div class="stat error">
                            <strong>Errors:</strong><br>{drop_result.get('errors', 0)}
                        </div>
                    </div>
                </div>
                """
        
        # Add machine status
        html_content += """
                <h2>🖥️ Machine Status</h2>
                <div class="machine-grid">
        """
        
        for machine in self.machines:
            status_class = machine.status
            html_content += f"""
                    <div class="machine {status_class}">
                        <strong>{machine.name}</strong><br>
                        IP: {machine.ip}<br>
                        Status: {machine.status.title()}<br>
                        Capabilities: {', '.join(machine.capabilities)}
                    </div>
            """
        
        html_content += """
                </div>
            </div>
        </body>
        </html>
        """
        
        html_report = Path(f"Reports/execution_report_{timestamp}.html")
        with open(html_report, 'w') as f:
            f.write(html_content)

def main():
    """Main execution function"""
    print("🚀 Starting POS Distributed Test Execution")
    print("=" * 50)
    
    manager = SimpleTestManager()
    
    # Show available machines
    print("\n🖥️ Available Machines:")
    for machine in manager.machines:
        print(f"  • {machine.name} ({machine.ip}) - {', '.join(machine.capabilities)}")
    
    # Show available test drops
    print("\n📋 Available Test Drops:")
    for drop_name, drop_config in manager.test_drops.items():
        print(f"  • {drop_name}: {drop_config['description']}")
    
    print("\n" + "=" * 50)
    
    choice = input("\nChoose execution mode:\n1. Execute all drops\n2. Execute specific drop\nEnter choice (1 or 2): ")
    
    if choice == "1":
        print("\n🏃 Executing all test drops...")
        result = manager.execute_all_drops()
        print("\n✅ All test drops completed!")
        
    elif choice == "2":
        drop_name = input(f"\nEnter drop name ({', '.join(manager.test_drops.keys())}): ")
        if drop_name in manager.test_drops:
            print(f"\n🏃 Executing test drop: {drop_name}")
            executions = manager.execute_test_drop(drop_name)
            print(f"\n✅ Test drop {drop_name} completed!")
            
            # Show summary
            passed = len([e for e in executions if e.status == "passed"])
            failed = len([e for e in executions if e.status == "failed"])
            print(f"📊 Results: {passed} passed, {failed} failed")
        else:
            print("❌ Invalid drop name")
    else:
        print("❌ Invalid choice")
    
    print(f"\n📁 Reports generated in: {os.path.abspath('Reports')}")
    print("🎉 Execution completed!")

if __name__ == "__main__":
    main()
