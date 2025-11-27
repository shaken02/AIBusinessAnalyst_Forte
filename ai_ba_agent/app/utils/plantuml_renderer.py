"""Local PlantUML diagram renderer using Java."""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import shutil

from app.utils.logger import logger


def render_plantuml_to_png(plantuml_code: str) -> Optional[bytes]:
    """
    Render PlantUML code to PNG image bytes using local Java installation.
    
    Args:
        plantuml_code: PlantUML diagram code (with @startuml/@enduml)
        
    Returns:
        PNG image bytes or None if rendering failed
    """
    try:
        # Clean and prepare PlantUML code
        code = plantuml_code.strip()
        
        # Remove markdown code blocks if present
        if '```' in code:
            lines = code.split('\n')
            code = '\n'.join([line for line in lines if not line.strip().startswith('```')])
            code = code.strip()
        
        # Extract only PlantUML code between @startuml and @enduml
        if '@startuml' in code:
            start_idx = code.find('@startuml')
            code = code[start_idx:]
        
        if '@enduml' in code:
            end_idx = code.find('@enduml') + len('@enduml')
            code = code[:end_idx]
        
        # Ensure @startuml/@enduml are present
        if not code.startswith('@startuml'):
            code = f"@startuml\n{code}"
        if not code.endswith('@enduml'):
            code = f"{code}\n@enduml"
        
        # Remove any text after @enduml
        if '@enduml' in code:
            code = code[:code.rfind('@enduml') + len('@enduml')]
        
        code = code.strip()
        
        # Log the cleaned code for debugging
        logger.debug(f"Cleaned PlantUML code ({len(code)} chars): {code[:100]}...")
        
        # Find Java
        java_path = None
        java_paths_to_check = [
            '/opt/homebrew/opt/openjdk@17/bin/java',
            '/opt/homebrew/opt/openjdk@11/bin/java',
            '/opt/homebrew/bin/java',
            '/usr/bin/java',
            '/usr/local/bin/java',
            str(Path(os.environ.get("JAVA_HOME", "")) / "bin" / "java"),
            str(Path(os.environ.get("JAVA_HOME", "")) / "bin" / "java.exe"),
            r'C:\Program Files\Java\jdk-17\bin\java.exe',
            r'C:\Program Files\Eclipse Adoptium\jdk-17\bin\java.exe',
            r"C:\Program Files (x86)\Common Files\Oracle\Java\java8path\java.exe",
        ]
        
        for path in java_paths_to_check:
            if os.path.exists(path):
                java_path = path
                logger.info(f"Found Java at: {java_path}")
                break

        if not java_path:
            java_path = shutil.which("java") or shutil.which("java.exe")
        
        if not java_path:
            # Try which java
            try:
                result = subprocess.run(['which', 'java'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    java_path = result.stdout.strip()
                    logger.info(f"Found Java via 'which': {java_path}")
            except Exception:
                pass
        
        if not java_path:
            logger.error("Java not found for PlantUML rendering")
            logger.error(f"Checked paths: {java_paths_to_check}")
            return None
        
        # Verify Java works
        try:
            result = subprocess.run([java_path, '-version'], capture_output=True, text=True, timeout=5)
            logger.debug(f"Java version check: {result.returncode}")
        except Exception as e:
            logger.warning(f"Could not verify Java: {e}")
        
        # Find plantuml.jar
        script_dir = Path(__file__).parent.parent.parent
        jar_paths = [
            script_dir / "libs" / "plantuml.jar",
            Path("/usr/local/bin/plantuml.jar"),
            Path.home() / ".local" / "share" / "plantuml.jar",
        ]
        
        jar_path = None
        for path in jar_paths:
            if path.exists():
                jar_path = path
                logger.info(f"Found PlantUML JAR at: {jar_path}")
                break
        
        if not jar_path:
            logger.error(f"PlantUML JAR not found. Checked: {jar_paths}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Script directory: {script_dir}")
            logger.error(f"Script directory exists: {script_dir.exists()}")
            return None
        
        # Create temporary file for PlantUML code
        # ВАЖНО: Используем UTF-8 кодировку для поддержки кириллицы
        with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name
        
        try:
            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Run PlantUML
                # PlantUML outputs to the same directory as input file if -o is not specified
                # We'll use the input file directory as output
                input_dir = os.path.dirname(tmp_file_path)
                base_name = os.path.splitext(os.path.basename(tmp_file_path))[0]
                
                cmd = [
                    java_path,
                    '-jar', str(jar_path),
                    '-tpng',
                    '-o', input_dir,
                    tmp_file_path
                ]
                
                logger.debug(f"Running PlantUML command: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=input_dir  # Set working directory
                )
                
                # Check for errors - PlantUML can return 200 on error (not 0)
                # Also check stderr for error messages
                has_error = False
                if result.returncode != 0:
                    has_error = True
                    logger.debug(f"Non-zero return code: {result.returncode}")
                
                if result.stderr:
                    stderr_lower = result.stderr.lower()
                    if any(keyword in stderr_lower for keyword in ["error", "exception", "cannot", "failed"]):
                        has_error = True
                        logger.debug(f"Error detected in stderr: {result.stderr[:200]}")
                
                if has_error:
                    logger.error(f"PlantUML rendering failed")
                    logger.error(f"Return code: {result.returncode}")
                    logger.error(f"Stdout: {result.stdout[:500] if result.stdout else '(empty)'}")
                    logger.error(f"Stderr: {result.stderr[:500] if result.stderr else '(empty)'}")
                    logger.error(f"Input code ({len(code)} chars):\n{code[:500]}")
                    
                    # Try to find the error line
                    if result.stderr and "Error line" in result.stderr:
                        import re
                        match = re.search(r'Error line (\d+)', result.stderr)
                        if match:
                            error_line = int(match.group(1))
                            lines = code.split('\n')
                            if error_line <= len(lines):
                                logger.error(f"Error at line {error_line}: {lines[error_line-1]}")
                            else:
                                logger.error(f"Error at line {error_line} (code has {len(lines)} lines)")
                    
                    return None
                
                # Success
                logger.debug(f"PlantUML command succeeded (return code: {result.returncode})")
                
                logger.debug(f"PlantUML command succeeded. Stdout: {result.stdout[:200]}")
                
                # Find generated PNG file
                # PlantUML generates PNG with same base name as input file
                png_file = os.path.join(input_dir, f"{base_name}.png")
                
                logger.debug(f"Looking for PNG file: {png_file}")
                
                if not os.path.exists(png_file):
                    # Try to find any PNG in input directory
                    import glob
                    png_files = glob.glob(os.path.join(input_dir, '*.png'))
                    logger.debug(f"Found PNG files in {input_dir}: {png_files}")
                    
                    if png_files:
                        png_file = png_files[0]
                        logger.info(f"Using found PNG: {png_file}")
                    else:
                        # Sometimes PlantUML saves to same directory as input file
                        input_file_dir = os.path.dirname(tmp_file_path)
                        png_file_alt = os.path.join(input_file_dir, f"{base_name}.png")
                        logger.debug(f"Trying alternative location: {png_file_alt}")
                        
                        if os.path.exists(png_file_alt):
                            png_file = png_file_alt
                        else:
                            logger.error(f"PNG file not found after PlantUML rendering")
                            logger.error(f"Searched in: {input_dir}, {input_file_dir}")
                            logger.error(f"Expected: {png_file} or {png_file_alt}")
                            logger.error(f"Input file: {tmp_file_path}")
                            logger.error(f"Base name: {base_name}")
                            logger.error(f"Command output: {result.stdout}")
                            return None
                
                # Read PNG bytes
                with open(png_file, 'rb') as f:
                    png_bytes = f.read()
                
                if len(png_bytes) == 0:
                    logger.error(f"PNG file is empty: {png_file}")
                    return None
                
                logger.info(f"Successfully generated PNG: {len(png_bytes)} bytes from {png_file}")
                
                # Clean up PNG file
                try:
                    if os.path.exists(png_file):
                        os.unlink(png_file)
                except Exception:
                    pass  # Ignore cleanup errors
                
                return png_bytes
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            # Clean up PNG file if in same dir
            png_temp = tmp_file_path.replace('.puml', '.png')
            if os.path.exists(png_temp):
                os.unlink(png_temp)
                
    except subprocess.TimeoutExpired:
        logger.error("PlantUML rendering timed out")
        return None
    except Exception as e:
        logger.error(f"Error rendering PlantUML: {e}")
        import traceback
        traceback.print_exc()
        return None


__all__ = ["render_plantuml_to_png"]

