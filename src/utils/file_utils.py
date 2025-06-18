from pathlib import Path
from typing import List, Optional
import os
import shutil
import logging
from datetime import datetime

class FileUtils:
    @staticmethod
    def ensure_directory(path: str) -> Path:
        """Ensure a directory exists, create if not."""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def backup_file(file_path: str, backup_dir: str = "backups") -> Optional[Path]:
        """Create a backup of a file with timestamp."""
        try:
            src_path = Path(file_path)
            if not src_path.exists():
                return None
            
            # Create backup directory
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"{src_path.stem}_{timestamp}{src_path.suffix}"
            
            # Copy file to backup location
            shutil.copy2(src_path, backup_file)
            return backup_file
        
        except Exception as e:
            logging.error(f"Backup failed for {file_path}: {e}")
            return None
    
    @staticmethod
    def list_files(directory: str, extensions: List[str] = None) -> List[Path]:
        """List all files in directory with optional extension filter."""
        try:
            path = Path(directory)
            if not path.exists():
                return []
            
            files = []
            for item in path.rglob("*"):
                if item.is_file():
                    if extensions:
                        if item.suffix.lower() in extensions:
                            files.append(item)
                    else:
                        files.append(item)
            return files
        
        except Exception as e:
            logging.error(f"Error listing files in {directory}: {e}")
            return []
    
    @staticmethod
    def safe_delete(path: str, backup: bool = True) -> bool:
        """Safely delete a file with optional backup."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return False
            
            if backup:
                FileUtils.backup_file(file_path)
            
            if file_path.is_file():
                file_path.unlink()
            else:
                shutil.rmtree(file_path)
            return True
        
        except Exception as e:
            logging.error(f"Delete failed for {path}: {e}")
            return False