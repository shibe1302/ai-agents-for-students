import subprocess
import json
import os
import tempfile


def run_code_in_docker(code_str, test_cases, timeout=5):
    """
    Run C++ code in a Docker container

    Args:
        code_str (str): C++ code as a string
        test_cases (list): List of test case dictionaries with 'input' and 'expected_output' keys
        timeout (int): Timeout in seconds for each test case

    Returns:
        dict: Results of code execution
    """
    try:
        # Create a temporary directory to hold files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code to a file
            code_path = os.path.join(temp_dir, "solution.cpp")
            with open(code_path, "w") as f:
                f.write(code_str)

            # Create config file for the Docker script
            config = {
                "code_path": "/code/solution.cpp",
                "test_cases": test_cases,
                "timeout": timeout
            }

            config_path = os.path.join(temp_dir, "config.json")
            with open(config_path, "w") as f:
                json.dump(config, f)

            # Run Docker command
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{temp_dir}:/code",
                "-w", "/code",
                "--network=none",  # No network access for security
                "--memory=512m",  # Limit memory to prevent DoS
                "--cpus=1",  # Limit CPU to prevent DoS
                "cpp-runner",  # Name of the Docker image
                "/code/config.json"
            ]

            # Execute Docker
            result = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=timeout + 10  # Give extra time for Docker overhead
            )

            # Check if Docker ran successfully
            if result.returncode != 0:
                return {
                    "error": f"Docker execution failed: {result.stderr}",
                    "passed_tests": 0,
                    "total_tests": len(test_cases),
                    "feedback": result.stderr
                }

            # Parse results
            try:
                docker_results = json.loads(result.stdout)

                # Format results for the application
                feedback_lines = []
                passed_tests = docker_results.get("summary", {}).get("passed", 0)
                total_tests = docker_results.get("summary", {}).get("total", 0)

                # Check for compilation errors
                if docker_results.get("compilation", {}).get("returncode", 0) != 0:
                    feedback_lines.append("Compilation Error:")
                    feedback_lines.append(docker_results["compilation"]["stderr"])
                else:
                    # Add test results to feedback
                    feedback_lines.append(f"Test Results: {passed_tests}/{total_tests} passed\n")

                    for i, test in enumerate(docker_results.get("test_results", [])):
                        status = "✅ Passed" if test["passed"] else "❌ Failed"
                        feedback_lines.append(f"Test {i + 1}: {status}")

                        if not test["passed"]:
                            feedback_lines.append(f"  Input: {test['input']}")
                            feedback_lines.append(f"  Expected: {test['expected_output']}")
                            feedback_lines.append(f"  Your output: {test['actual_output']}")
                            if test["stderr"]:
                                feedback_lines.append(f"  Error output: {test['stderr']}")
                            feedback_lines.append("")

                return {
                    "passed_tests": passed_tests,
                    "total_tests": total_tests,
                    "feedback": "\n".join(feedback_lines)
                }

            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse Docker output",
                    "passed_tests": 0,
                    "total_tests": len(test_cases),
                    "feedback": result.stdout
                }

    except Exception as e:
        return {
            "error": str(e),
            "passed_tests": 0,
            "total_tests": len(test_cases),
            "feedback": f"Error running code: {str(e)}"
        }


def setup_docker():
    """
    Check if Docker is set up correctly and build the image if needed

    Returns:
        bool: True if Docker is ready, False otherwise
    """
    try:
        # Check if Docker is installed and running
        subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Check if our image exists
        result = subprocess.run(
            ["docker", "images", "-q", "cpp-runner"],
            text=True,
            capture_output=True
        )

        if not result.stdout.strip():
            print("Docker image 'cpp-runner' not found. Building it now...")

            # Create temporary directory for Dockerfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write Dockerfile
                dockerfile_path = os.path.join(temp_dir, "Dockerfile")
                with open(dockerfile_path, "w") as f:
                    f.write("""FROM gcc:latest

# Install necessary dependencies
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/*

# Set up a non-root user for better security
RUN useradd -m cpprunner
USER cpprunner
WORKDIR /home/cpprunner

# Create directories for code
RUN mkdir -p /home/cpprunner/code

# Copy the executor script
COPY --chown=cpprunner:cpprunner run_cpp.py /home/cpprunner/

# Default command
ENTRYPOINT ["python3", "/home/cpprunner/run_cpp.py"]
""")

                # Write the run_cpp.py script
                script_path = os.path.join(temp_dir, "run_cpp.py")
                with open(script_path, "w") as f:
                    # Copy the contents of the run_cpp.py script here
                    f.write("""#!/usr/bin/env python3
import subprocess
import json
import os
import sys
import tempfile
import time
import signal

def run_with_timeout(cmd, input_data=None, timeout=5):
    \"\"\"Run a command with timeout and input data\"\"\"
    start = time.time()
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if input_data else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        stdout, stderr = process.communicate(input=input_data, timeout=timeout)
        end = time.time()
        return {
            'returncode': process.returncode,
            'stdout': stdout,
            'stderr': stderr,
            'time': end - start
        }
    except subprocess.TimeoutExpired:
        # Kill the process if it times out
        process.kill()
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': 'Process timed out',
            'time': timeout
        }

def main():
    \"\"\"Main function to run C++ code against test cases\"\"\"
    if len(sys.argv) < 2:
        print("Usage: python run_cpp.py <path-to-config-json>")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Get code file path
        code_path = config.get('code_path')
        if not code_path or not os.path.exists(code_path):
            raise Exception(f"Code file not found at {code_path}")

        # Compile the code
        compile_result = run_with_timeout(['g++', code_path, '-o', f"{code_path}.out", '-std=c++11'])

        results = {
            'compilation': compile_result,
            'test_results': [],
            'summary': {
                'passed': 0,
                'total': 0
            }
        }

        # If compilation failed, return results immediately
        if compile_result['returncode'] != 0:
            results['summary']['error'] = "Compilation failed"
            print(json.dumps(results))
            sys.exit(0)

        # Get test cases
        test_cases = config.get('test_cases', [])
        results['summary']['total'] = len(test_cases)

        # Run each test case
        for i, test in enumerate(test_cases):
            test_input = test.get('input', '')
            expected_output = test.get('expected_output', '').strip()
            is_hidden = test.get('is_hidden', False)

            # Run the program
            run_result = run_with_timeout([f"{code_path}.out"], test_input, timeout=config.get('timeout', 5))

            # Check output
            actual_output = run_result['stdout'].strip()
            passed = actual_output == expected_output and run_result['returncode'] == 0

            if passed:
                results['summary']['passed'] += 1

            # Add test result
            test_result = {
                'test_id': i + 1,
                'passed': passed,
                'input': test_input if not is_hidden else "[Hidden]",
                'expected_output': expected_output if not is_hidden else "[Hidden]",
                'actual_output': actual_output if not is_hidden else "[Hidden]",
                'stderr': run_result['stderr'],
                'time': run_result['time'],
                'is_hidden': is_hidden
            }

            results['test_results'].append(test_result)

        # Output results as JSON
        print(json.dumps(results))

    except Exception as e:
        error_result = {
            'error': str(e),
            'summary': {
                'passed': 0,
                'total': 0,
                'error': str(e)
            }
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
""")

                # Build the Docker image
                subprocess.run(
                    ["docker", "build", "-t", "cpp-runner", temp_dir],
                    check=True
                )

        return True

    except subprocess.CalledProcessError as e:
        print(f"Docker setup error: {e}")
        return False
    except Exception as e:
        print(f"Error setting up Docker: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    if setup_docker():
        test_code = """
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << "Sum: " << (a + b) << endl;
    return 0;
}
"""
        test_cases = [
            {"input": "5\n7", "expected_output": "Sum: 12"},
            {"input": "10\n20", "expected_output": "Sum: 30"}
        ]

        results = run_code_in_docker(test_code, test_cases)
        print(json.dumps(results, indent=2))
    else:
        print("Docker setup failed")