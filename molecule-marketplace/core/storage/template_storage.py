"""
Template Storage System
Manages template files, versioning, and file system operations.
"""

import os
import shutil
import tarfile
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TemplateStorage:
    """Manages template file storage and operations."""

    def __init__(self, storage_root: str = "~/.local/share/molecule-marketplace/templates"):
        """Initialize template storage."""
        self.storage_root = Path(storage_root).expanduser()
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.templates_dir = self.storage_root / "templates"
        self.archives_dir = self.storage_root / "archives"
        self.cache_dir = self.storage_root / "cache"

        for directory in [self.templates_dir, self.archives_dir, self.cache_dir]:
            directory.mkdir(exist_ok=True)

    def get_template_path(self, template_name: str, version: str = None) -> Path:
        """Get the file system path for a template."""
        if version:
            return self.templates_dir / template_name / version
        else:
            return self.templates_dir / template_name / "latest"

    def store_template_files(self,
                           template_name: str,
                           files: Dict[str, str],
                           version: str = "1.0.0") -> Path:
        """Store template files to disk."""

        template_path = self.get_template_path(template_name, version)
        template_path.mkdir(parents=True, exist_ok=True)

        stored_files = []

        try:
            for file_path, content in files.items():
                full_path = template_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file content
                full_path.write_text(content, encoding='utf-8')
                stored_files.append(full_path)

                logger.info(f"Stored template file: {full_path}")

            # Create symlink to latest version
            latest_path = self.get_template_path(template_name)
            if latest_path.exists() and latest_path.is_symlink():
                latest_path.unlink()
            elif latest_path.exists():
                shutil.rmtree(latest_path)

            latest_path.symlink_to(version, target_is_directory=True)

            # Create template manifest
            self._create_manifest(template_path, template_name, version, files)

            return template_path

        except Exception as e:
            # Cleanup on failure
            for file_path in stored_files:
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass

            logger.error(f"Failed to store template {template_name}: {e}")
            raise

    def _create_manifest(self,
                        template_path: Path,
                        name: str,
                        version: str,
                        files: Dict[str, str]):
        """Create a manifest file for the template."""

        manifest = {
            "name": name,
            "version": version,
            "stored_at": str(template_path),
            "files": list(files.keys()),
            "checksum": self._calculate_checksum(files)
        }

        manifest_path = template_path / ".manifest.json"
        import json
        manifest_path.write_text(json.dumps(manifest, indent=2))

    def _calculate_checksum(self, files: Dict[str, str]) -> str:
        """Calculate checksum for template files."""
        hasher = hashlib.sha256()
        for file_path in sorted(files.keys()):
            hasher.update(f"{file_path}:{files[file_path]}".encode())
        return hasher.hexdigest()

    def load_template_files(self, template_name: str, version: str = None) -> Dict[str, str]:
        """Load template files from storage."""

        template_path = self.get_template_path(template_name, version)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        files = {}

        for file_path in template_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                relative_path = file_path.relative_to(template_path)
                try:
                    files[str(relative_path)] = file_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    # Handle binary files
                    logger.warning(f"Skipping binary file: {relative_path}")
                    continue

        return files

    def delete_template(self, template_name: str, version: str = None):
        """Delete a template version or entire template."""

        if version:
            # Delete specific version
            version_path = self.templates_dir / template_name / version
            if version_path.exists():
                shutil.rmtree(version_path)
                logger.info(f"Deleted template version: {template_name} v{version}")
        else:
            # Delete entire template
            template_dir = self.templates_dir / template_name
            if template_dir.exists():
                shutil.rmtree(template_dir)
                logger.info(f"Deleted template: {template_name}")

    def list_versions(self, template_name: str) -> List[str]:
        """List all versions of a template."""

        template_dir = self.templates_dir / template_name
        if not template_dir.exists():
            return []

        versions = []
        for item in template_dir.iterdir():
            if item.is_dir() and item.name != "latest":
                versions.append(item.name)

        return sorted(versions, reverse=True)  # Latest first

    def create_archive(self, template_name: str, version: str = None) -> Path:
        """Create a tar.gz archive of a template."""

        template_path = self.get_template_path(template_name, version)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        archive_name = f"{template_name}-{version or 'latest'}.tar.gz"
        archive_path = self.archives_dir / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(template_path, arcname=template_name, recursive=True)

        logger.info(f"Created archive: {archive_path}")
        return archive_path

    def extract_archive(self, archive_path: Path, destination: Path = None) -> Path:
        """Extract a template archive."""

        if destination is None:
            destination = self.cache_dir / "extracted"

        destination.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive_path, "r:gz") as tar:
            # Validate tar members for security
            members = tar.getmembers()
            for member in members:
                # Check for directory traversal attacks
                if member.name.startswith('/') or '..' in member.name:
                    raise ValueError(f"Unsafe tar member: {member.name}")

                # Check for symlinks outside destination
                if member.issym() or member.islnk():
                    raise ValueError(f"Symlinks not allowed in templates: {member.name}")

                # Limit file sizes (100MB max per file)
                if member.size > 100 * 1024 * 1024:
                    raise ValueError(f"File too large: {member.name} ({member.size} bytes)")

            tar.extractall(path=destination, members=members)

        logger.info(f"Extracted archive to: {destination}")
        return destination

    def install_template(self,
                        template_name: str,
                        target_path: Path,
                        config_values: Dict[str, str] = None,
                        version: str = None) -> List[Path]:
        """Install a template to a target location with variable substitution."""

        # Load template files
        template_files = self.load_template_files(template_name, version)

        if not template_files:
            raise ValueError(f"No files found for template: {template_name}")

        installed_files = []
        config_values = config_values or {}

        try:
            for file_path, content in template_files.items():
                # Substitute variables in file path
                processed_path = self._substitute_variables(file_path, config_values)

                # Substitute variables in content
                processed_content = self._substitute_variables(content, config_values)

                # Create target file
                target_file = target_path / processed_path
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Check if file already exists
                if target_file.exists():
                    backup_path = target_file.with_suffix(target_file.suffix + '.bak')
                    shutil.copy2(target_file, backup_path)
                    logger.info(f"Backed up existing file: {backup_path}")

                target_file.write_text(processed_content, encoding='utf-8')
                installed_files.append(target_file)

                logger.info(f"Installed: {target_file}")

            return installed_files

        except Exception as e:
            logger.error(f"Failed to install template {template_name}: {e}")
            # Cleanup on failure
            for file_path in installed_files:
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass
            raise

    def _substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Substitute template variables in text."""

        for key, value in variables.items():
            # Support both {{var}} and {var} syntax
            text = text.replace(f"{{{{{key}}}}}", str(value))
            text = text.replace(f"{{{key}}}", str(value))

        return text

    def get_storage_stats(self) -> Dict[str, any]:
        """Get storage statistics."""

        stats = {
            "storage_root": str(self.storage_root),
            "template_count": 0,
            "total_size_mb": 0,
            "templates": {}
        }

        if self.templates_dir.exists():
            for template_dir in self.templates_dir.iterdir():
                if template_dir.is_dir():
                    stats["template_count"] += 1

                    # Calculate template size
                    size = sum(f.stat().st_size for f in template_dir.rglob('*') if f.is_file())

                    stats["templates"][template_dir.name] = {
                        "versions": len(self.list_versions(template_dir.name)),
                        "size_mb": round(size / (1024 * 1024), 2)
                    }

                    stats["total_size_mb"] += size / (1024 * 1024)

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats