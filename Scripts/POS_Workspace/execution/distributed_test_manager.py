"""
Distributed Test Execution Manager for POS Testing
Handles multi-banner, multi-machine test execution with load balancing
"""

import yaml
import asyncio
import concurrent.futures
import subprocess
import json
import datetime
import os
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Machine:
    ip: str
    name: str
    capabilities: List[str]
    status: str = "available"
    current_test: str = None

@dataclass
class Banner:
    name: str
    machines: List[Machine]

@dataclass
class TestDrop:
    name: str
    description: str
    tests: List[str]
    required_capabilities: List[str]
    estimated_duration: int

class DistributedTestManager:
    def __init__(self, config_path: str):
        """Initialize the distributed test manager"""
        self.config_path = config_path
        self.config = self._load_config()
        self.banners = self._parse_banners()
        self.test_drops = self._parse_test_drops()
        self.execution_results = {}
        self.setup_logging()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _parse_banners(self) -> Dict[str, Banner]:
        """Parse banner configuration"""
        banners = {}
        for banner_id, banner_config in self.config['test_execution']['banners'].items():
            machines = []
            for machine_config in banner_config['machines']:
                machine = Machine(
                    ip=machine_config['ip'],
                    name=machine_config['name'],
                    capabilities=machine_config['capabilities']
                )
                machines.append(machine)
            banners[banner_id] = Banner(name=banner_config['name'], machines=machines)
        return banners
    
    def _parse_test_drops(self) -> Dict[str, TestDrop]:
        """Parse test drop configuration"""
        test_drops = {}
        for drop_id, drop_config in self.config['test_execution']['test_drops'].items():
            test_drop = TestDrop(
                name=drop_id,
                description=drop_config['description'],
                tests=drop_config['tests'],
                required_capabilities=drop_config['required_capabilities'],
                estimated_duration=drop_config['estimated_duration']
            )
            test_drops[drop_id] = test_drop
        return test_drops
    
    def setup_logging(self):
        """Setup logging for test execution"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"Reports/test_execution_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_available_machines(self, required_capabilities: List[str]) -> List[Machine]:
        """Get machines that are available and have required capabilities"""
        available_machines = []
        for banner in self.banners.values():
            for machine in banner.machines:
                if (machine.status == "available" and 
                    all(cap in machine.capabilities for cap in required_capabilities)):
                    available_machines.append(machine)
        return available_machines
    
    def allocate_machine(self, test_name: str, required_capabilities: List[str]) -> Machine:
        """Allocate a machine for test execution"""
        available_machines = self.get_available_machines(required_capabilities)
        if not available_machines:
            return None
        
        # Simple allocation - can be enhanced with load balancing
        machine = available_machines[0]
        machine.status = "busy"
        machine.current_test = test_name
        return machine
    
    def release_machine(self, machine: Machine):
        """Release a machine after test completion"""
        machine.status = "available"
        machine.current_test = None
    
    async def execute_test_on_machine(self, test_path: str, machine: Machine) -> Dict:
        """Execute a test on a specific machine"""
        start_time = datetime.datetime.now()
        self.logger.info(f"Starting test {test_path} on machine {machine.name} ({machine.ip})")
        
        try:
            # Prepare remote execution command
            remote_command = self._prepare_remote_command(test_path, machine)
            
            # Execute test
            result = await self._execute_remote_test(remote_command, machine)
            
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            test_result = {
                "test_path": test_path,
                "machine": machine.name,
                "machine_ip": machine.ip,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration,
                "status": result["status"],
                "output": result["output"],
                "error": result.get("error", "")
            }
            
            self.logger.info(f"Completed test {test_path} on {machine.name} - Status: {result['status']}")
            return test_result
            
        except Exception as e:
            self.logger.error(f"Error executing test {test_path} on {machine.name}: {str(e)}")
            return {
                "test_path": test_path,
                "machine": machine.name,
                "machine_ip": machine.ip,
                "start_time": start_time.isoformat(),
                "status": "error",
                "error": str(e)
            }
        finally:
            self.release_machine(machine)
    
    def _prepare_remote_command(self, test_path: str, machine: Machine) -> str:
        """Prepare command for remote test execution"""
        # This would be customized based on your remote execution setup
        # Options: SSH, Windows Remote Management, or agent-based approach
        
        base_command = f"pytest {test_path} -v --html=report_{machine.name}.html"
        
        # For Windows Remote Management (WinRM)
        remote_command = f"""
        winrs -r:{machine.ip} -u:admin -p:password "cd C:\\POS_Tests && {base_command}"
        """
        
        # For SSH (if using SSH on Windows)
        # remote_command = f"ssh admin@{machine.ip} 'cd /c/POS_Tests && {base_command}'"
        
        return remote_command
    
    async def _execute_remote_test(self, command: str, machine: Machine) -> Dict:
        """Execute remote test command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "status": "passed" if process.returncode == 0 else "failed",
                "output": stdout.decode(),
                "error": stderr.decode() if stderr else ""
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }
    
    async def execute_test_drop(self, drop_name: str) -> Dict:
        """Execute all tests in a test drop across available machines"""
        if drop_name not in self.test_drops:
            raise ValueError(f"Test drop {drop_name} not found")
        
        test_drop = self.test_drops[drop_name]
        self.logger.info(f"Starting execution of test drop: {test_drop.description}")
        
        # Get all test files for this drop
        test_files = self._get_test_files(test_drop.tests)
        
        # Execute tests concurrently
        tasks = []
        for test_file in test_files:
            machine = self.allocate_machine(test_file, test_drop.required_capabilities)
            if machine:
                task = asyncio.create_task(self.execute_test_on_machine(test_file, machine))
                tasks.append(task)
            else:
                self.logger.warning(f"No available machine for test {test_file}")
        
        # Wait for all tests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        drop_result = {
            "drop_name": drop_name,
            "description": test_drop.description,
            "total_tests": len(test_files),
            "executed_tests": len([r for r in results if not isinstance(r, Exception)]),
            "passed_tests": len([r for r in results if isinstance(r, dict) and r.get("status") == "passed"]),
            "failed_tests": len([r for r in results if isinstance(r, dict) and r.get("status") == "failed"]),
            "test_results": [r for r in results if isinstance(r, dict)]
        }
        
        return drop_result
    
    def _get_test_files(self, test_patterns: List[str]) -> List[str]:
        """Get actual test files from patterns"""
        test_files = []
        for pattern in test_patterns:
            # Use glob to find matching files
            import glob
            files = glob.glob(pattern, recursive=True)
            test_files.extend(files)
        return test_files
    
    async def execute_all_drops(self) -> Dict:
        """Execute all test drops"""
        all_results = {}
        start_time = datetime.datetime.now()
        
        for drop_name in self.test_drops.keys():
            try:
                result = await self.execute_test_drop(drop_name)
                all_results[drop_name] = result
            except Exception as e:
                self.logger.error(f"Error executing drop {drop_name}: {str(e)}")
                all_results[drop_name] = {"status": "error", "error": str(e)}
        
        end_time = datetime.datetime.now()
        
        # Generate summary report
        summary = {
            "execution_start": start_time.isoformat(),
            "execution_end": end_time.isoformat(),
            "total_duration": (end_time - start_time).total_seconds(),
            "total_drops": len(self.test_drops),
            "drop_results": all_results
        }
        
        self._generate_report(summary)
        return summary
    
    def _generate_report(self, summary: Dict):
        """Generate execution report"""
        report_dir = Path("Reports")
        report_dir.mkdir(exist_ok=True)
        
        # Generate JSON report
        json_report = report_dir / f"execution_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_report, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(summary, report_dir)
        
        self.logger.info(f"Execution report generated: {json_report}")
    
    def _generate_html_report(self, summary: Dict, report_dir: Path):
        """Generate HTML execution report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>POS Test Execution Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .drop {{ margin: 20px 0; border: 1px solid #ccc; padding: 10px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .error {{ color: orange; }}
            </style>
        </head>
        <body>
            <h1>POS Test Execution Report</h1>
            <div class="summary">
                <h2>Execution Summary</h2>
                <p><strong>Start Time:</strong> {summary['execution_start']}</p>
                <p><strong>End Time:</strong> {summary['execution_end']}</p>
                <p><strong>Total Duration:</strong> {summary['total_duration']:.2f} seconds</p>
                <p><strong>Total Drops:</strong> {summary['total_drops']}</p>
            </div>
        """
        
        for drop_name, drop_result in summary['drop_results'].items():
            if isinstance(drop_result, dict) and 'test_results' in drop_result:
                html_content += f"""
                <div class="drop">
                    <h3>{drop_name}</h3>
                    <p>{drop_result.get('description', '')}</p>
                    <p><strong>Total Tests:</strong> {drop_result.get('total_tests', 0)}</p>
                    <p><span class="passed">Passed: {drop_result.get('passed_tests', 0)}</span></p>
                    <p><span class="failed">Failed: {drop_result.get('failed_tests', 0)}</span></p>
                </div>
                """
        
        html_content += """
        </body>
        </html>
        """
        
        html_report = report_dir / f"execution_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_report, 'w') as f:
            f.write(html_content)

# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Distributed POS Test Execution")
    parser.add_argument("--config", default="config/test_config.yaml", help="Configuration file path")
    parser.add_argument("--drop", help="Specific test drop to execute")
    parser.add_argument("--all", action="store_true", help="Execute all test drops")
    
    args = parser.parse_args()
    
    manager = DistributedTestManager(args.config)
    
    async def main():
        if args.all:
            result = await manager.execute_all_drops()
        elif args.drop:
            result = await manager.execute_test_drop(args.drop)
        else:
            print("Please specify --all or --drop <drop_name>")
            return
        
        print("Execution completed. Check Reports directory for detailed results.")
    
    asyncio.run(main())
