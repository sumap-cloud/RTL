"""
POS Test Scheduler - Advanced scheduling and orchestration
Handles complex test scheduling across multiple banners and machines
"""

import json
import datetime
import time
import threading
import queue
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import requests
import concurrent.futures

class TestPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class ScheduledTest:
    id: str
    test_file: str
    banner: str
    machine_preference: Optional[str]
    required_capabilities: List[str]
    priority: TestPriority
    scheduled_time: datetime.datetime
    estimated_duration: int
    test_params: Dict[str, Any]
    status: TestStatus = TestStatus.PENDING
    assigned_machine: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    result: Optional[Dict] = None

@dataclass 
class TestMachine:
    name: str
    ip: str
    port: int
    banner: str
    capabilities: List[str]
    status: str = "available"
    current_test: Optional[str] = None
    last_heartbeat: Optional[datetime.datetime] = None

class TestScheduler:
    def __init__(self):
        self.machines: Dict[str, TestMachine] = {}
        self.scheduled_tests: Dict[str, ScheduledTest] = {}
        self.test_queue = queue.PriorityQueue()
        self.results: Dict[str, Dict] = {}
        self.running = False
        self.scheduler_thread = None
        self.setup_logging()
        self.load_machines()
    
    def setup_logging(self):
        """Setup logging for the scheduler"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"Reports/scheduler_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_machines(self):
        """Load machine configuration"""
        # In a real scenario, this would load from configuration file or database
        machines_config = [
            {"name": "Banner1_POS1", "ip": "192.168.1.10", "port": 8080, "banner": "banner1", "capabilities": ["sale", "returns", "funds"]},
            {"name": "Banner1_POS2", "ip": "192.168.1.11", "port": 8080, "banner": "banner1", "capabilities": ["sale", "loyalty", "compliance"]},
            {"name": "Banner2_POS1", "ip": "192.168.2.10", "port": 8080, "banner": "banner2", "capabilities": ["sale", "returns", "funds"]},
            {"name": "Banner2_POS2", "ip": "192.168.2.11", "port": 8080, "banner": "banner2", "capabilities": ["sale", "loyalty", "compliance"]},
            {"name": "Banner3_POS1", "ip": "192.168.3.10", "port": 8080, "banner": "banner3", "capabilities": ["sale", "returns", "funds"]},
            {"name": "Banner4_POS1", "ip": "192.168.4.10", "port": 8080, "banner": "banner4", "capabilities": ["sale", "returns", "funds"]},
            {"name": "Banner5_POS1", "ip": "192.168.5.10", "port": 8080, "banner": "banner5", "capabilities": ["sale", "returns", "funds"]},
            {"name": "Banner6_POS1", "ip": "192.168.6.10", "port": 8080, "banner": "banner6", "capabilities": ["sale", "returns", "funds"]},
        ]
        
        for config in machines_config:
            machine = TestMachine(**config)
            self.machines[machine.name] = machine
    
    def check_machine_health(self, machine: TestMachine) -> bool:
        """Check if a machine is healthy and responsive"""
        try:
            response = requests.get(f"http://{machine.ip}:{machine.port}/health", timeout=5)
            if response.status_code == 200:
                machine.last_heartbeat = datetime.datetime.now()
                machine.status = "available"
                return True
        except requests.exceptions.RequestException:
            pass
        
        machine.status = "unreachable"
        return False
    
    def find_available_machine(self, test: ScheduledTest) -> Optional[TestMachine]:
        """Find an available machine for the test"""
        # Filter machines by banner if specified
        candidate_machines = []
        for machine in self.machines.values():
            if test.banner and machine.banner != test.banner:
                continue
            if test.machine_preference and machine.name != test.machine_preference:
                continue
            if not all(cap in machine.capabilities for cap in test.required_capabilities):
                continue
            if machine.status != "available":
                continue
            candidate_machines.append(machine)
        
        # Check health and return first available
        for machine in candidate_machines:
            if self.check_machine_health(machine):
                return machine
        
        return None
    
    def schedule_test(self, test_config: Dict) -> str:
        """Schedule a new test"""
        test_id = f"test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.scheduled_tests)}"
        
        scheduled_test = ScheduledTest(
            id=test_id,
            test_file=test_config['test_file'],
            banner=test_config.get('banner'),
            machine_preference=test_config.get('machine_preference'),
            required_capabilities=test_config.get('required_capabilities', ['sale']),
            priority=TestPriority(test_config.get('priority', 2)),
            scheduled_time=datetime.datetime.now(),
            estimated_duration=test_config.get('estimated_duration', 300),
            test_params=test_config.get('test_params', {})
        )
        
        self.scheduled_tests[test_id] = scheduled_test
        
        # Add to priority queue (lower number = higher priority)
        self.test_queue.put((scheduled_test.priority.value, test_id))
        
        self.logger.info(f"Scheduled test {test_id}: {test_config['test_file']}")
        return test_id
    
    def execute_test_on_machine(self, test: ScheduledTest, machine: TestMachine) -> Dict:
        """Execute a test on a specific machine via HTTP API"""
        try:
            machine.status = "busy"
            machine.current_test = test.id
            test.assigned_machine = machine.name
            test.start_time = datetime.datetime.now()
            test.status = TestStatus.RUNNING
            
            self.logger.info(f"Executing test {test.id} on machine {machine.name}")
            
            # Prepare request data
            request_data = {
                "test_file": test.test_file,
                "test_params": test.test_params
            }
            
            # Send execution request to machine agent
            response = requests.post(
                f"http://{machine.ip}:{machine.port}/execute",
                json=request_data,
                timeout=test.estimated_duration + 60  # Add buffer time
            )
            
            if response.status_code == 200:
                result = response.json()
                test.status = TestStatus.COMPLETED if result['status'] == 'passed' else TestStatus.FAILED
            else:
                result = {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                test.status = TestStatus.FAILED
            
            test.end_time = datetime.datetime.now()
            test.result = result
            
            self.logger.info(f"Test {test.id} completed on {machine.name} - Status: {test.status.value}")
            return result
            
        except requests.exceptions.Timeout:
            test.status = TestStatus.TIMEOUT
            test.result = {"status": "timeout", "error": "Test execution timed out"}
            self.logger.error(f"Test {test.id} timed out on {machine.name}")
            return test.result
        except Exception as e:
            test.status = TestStatus.FAILED
            test.result = {"status": "error", "error": str(e)}
            self.logger.error(f"Error executing test {test.id} on {machine.name}: {str(e)}")
            return test.result
        finally:
            machine.status = "available"
            machine.current_test = None
            test.end_time = datetime.datetime.now()
    
    def scheduler_worker(self):
        """Main scheduler worker thread"""
        self.logger.info("Scheduler worker started")
        
        while self.running:
            try:
                # Get next test from queue (with timeout to check running status)
                try:
                    priority, test_id = self.test_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                test = self.scheduled_tests[test_id]
                
                # Find available machine
                machine = self.find_available_machine(test)
                if not machine:
                    # Put test back in queue and wait
                    self.test_queue.put((priority, test_id))
                    time.sleep(5)
                    continue
                
                # Execute test in a separate thread
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(self.execute_test_on_machine, test, machine)
                
                # Mark queue task as done
                self.test_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in scheduler worker: {str(e)}")
                time.sleep(1)
        
        self.logger.info("Scheduler worker stopped")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self.scheduler_worker)
        self.scheduler_thread.start()
        self.logger.info("Test scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        self.logger.info("Test scheduler stopped")
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "running": self.running,
            "queue_size": self.test_queue.qsize(),
            "total_tests": len(self.scheduled_tests),
            "pending_tests": len([t for t in self.scheduled_tests.values() if t.status == TestStatus.PENDING]),
            "running_tests": len([t for t in self.scheduled_tests.values() if t.status == TestStatus.RUNNING]),
            "completed_tests": len([t for t in self.scheduled_tests.values() if t.status == TestStatus.COMPLETED]),
            "failed_tests": len([t for t in self.scheduled_tests.values() if t.status == TestStatus.FAILED]),
            "machines": {name: {"status": m.status, "current_test": m.current_test} for name, m in self.machines.items()}
        }
    
    def schedule_test_drop(self, drop_config: Dict) -> List[str]:
        """Schedule an entire test drop"""
        test_ids = []
        
        for test_file in drop_config['tests']:
            test_config = {
                "test_file": test_file,
                "banner": drop_config.get('banner'),
                "required_capabilities": drop_config.get('required_capabilities', ['sale']),
                "estimated_duration": drop_config.get('estimated_duration', 300),
                "priority": drop_config.get('priority', 2)
            }
            
            test_id = self.schedule_test(test_config)
            test_ids.append(test_id)
        
        return test_ids
    
    def generate_execution_report(self) -> Dict:
        """Generate comprehensive execution report"""
        completed_tests = [t for t in self.scheduled_tests.values() if t.status in [TestStatus.COMPLETED, TestStatus.FAILED, TestStatus.TIMEOUT]]
        
        if not completed_tests:
            return {"message": "No completed tests to report"}
        
        total_duration = sum(
            (t.end_time - t.start_time).total_seconds() 
            for t in completed_tests 
            if t.start_time and t.end_time
        )
        
        report = {
            "execution_summary": {
                "total_tests": len(completed_tests),
                "passed_tests": len([t for t in completed_tests if t.status == TestStatus.COMPLETED]),
                "failed_tests": len([t for t in completed_tests if t.status == TestStatus.FAILED]),
                "timeout_tests": len([t for t in completed_tests if t.status == TestStatus.TIMEOUT]),
                "total_duration": total_duration,
                "average_test_duration": total_duration / len(completed_tests) if completed_tests else 0
            },
            "banner_summary": {},
            "machine_summary": {},
            "test_details": []
        }
        
        # Banner summary
        for banner in set(m.banner for m in self.machines.values()):
            banner_tests = [t for t in completed_tests if self.machines.get(t.assigned_machine, {}).banner == banner]
            if banner_tests:
                report["banner_summary"][banner] = {
                    "total_tests": len(banner_tests),
                    "passed_tests": len([t for t in banner_tests if t.status == TestStatus.COMPLETED]),
                    "failed_tests": len([t for t in banner_tests if t.status == TestStatus.FAILED])
                }
        
        # Machine summary
        for machine_name, machine in self.machines.items():
            machine_tests = [t for t in completed_tests if t.assigned_machine == machine_name]
            if machine_tests:
                report["machine_summary"][machine_name] = {
                    "total_tests": len(machine_tests),
                    "passed_tests": len([t for t in machine_tests if t.status == TestStatus.COMPLETED]),
                    "failed_tests": len([t for t in machine_tests if t.status == TestStatus.FAILED]),
                    "average_duration": sum((t.end_time - t.start_time).total_seconds() for t in machine_tests if t.start_time and t.end_time) / len(machine_tests)
                }
        
        # Test details
        for test in completed_tests:
            report["test_details"].append({
                "test_id": test.id,
                "test_file": test.test_file,
                "machine": test.assigned_machine,
                "banner": self.machines.get(test.assigned_machine, TestMachine("", "", 0, "", [])).banner,
                "status": test.status.value,
                "duration": (test.end_time - test.start_time).total_seconds() if test.start_time and test.end_time else 0,
                "start_time": test.start_time.isoformat() if test.start_time else None,
                "end_time": test.end_time.isoformat() if test.end_time else None
            })
        
        # Save report
        report_file = Path(f"Reports/scheduler_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Execution report saved: {report_file}")
        return report

def main():
    """Example usage of the scheduler"""
    scheduler = TestScheduler()
    scheduler.start()
    
    try:
        # Example: Schedule some tests
        test_configs = [
            {
                "test_file": "test1_pos_flow.py",
                "banner": "banner1",
                "required_capabilities": ["sale"],
                "priority": 1,
                "estimated_duration": 300
            },
            {
                "test_file": "tests/fundsmanagement/TC001_paidout.py",
                "banner": "banner2",
                "required_capabilities": ["funds"],
                "priority": 2,
                "estimated_duration": 600
            }
        ]
        
        for config in test_configs:
            scheduler.schedule_test(config)
        
        print("Tests scheduled. Press Ctrl+C to stop and generate report...")
        
        # Wait for user interrupt
        while True:
            status = scheduler.get_status()
            print(f"Status: {status['pending_tests']} pending, {status['running_tests']} running, {status['completed_tests']} completed")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        
        # Generate final report
        report = scheduler.generate_execution_report()
        print(f"Final report: {report}")

if __name__ == "__main__":
    main()
