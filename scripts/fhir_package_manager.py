#!/usr/bin/env python3
"""
FHIR Package Manager - Download, cache, and manage FHIR packages locally
"""

import os
import json
import requests
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import sys

class FHIRPackageManager:
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or Path.home() / ".fhir" / "packages")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry_url = "https://packages.fhir.org"
    
    def install_package(self, package_id: str, version: str = "latest") -> Path:
        """Download and install a FHIR package"""
        print(f"Installing {package_id}@{version}")
        
        # Check if already cached
        package_dir = self.cache_dir / package_id / version
        if package_dir.exists():
            print(f"Package already cached at {package_dir}")
            return package_dir
        
        # Download package metadata
        metadata = self._get_package_metadata(package_id, version)
        if not metadata:
            raise ValueError(f"Package {package_id}@{version} not found")
        
        # Download package
        download_url = metadata.get("dist", {}).get("tarball")
        if not download_url:
            raise ValueError(f"No download URL found for {package_id}@{version}")
        
        package_dir.mkdir(parents=True, exist_ok=True)
        self._download_and_extract(download_url, package_dir)
        
        print(f"Package installed to {package_dir}")
        return package_dir
    
    def _get_package_metadata(self, package_id: str, version: str) -> Optional[Dict]:
        """Fetch package metadata from FHIR registry"""
        try:
            url = f"{self.registry_url}/{package_id}"
            if version != "latest":
                url += f"/{version}"
            
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching metadata: {e}")
            return None
    
    def _download_and_extract(self, url: str, destination: Path):
        """Download and extract package archive"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Determine archive type and extract
        if url.endswith('.tgz') or url.endswith('.tar.gz'):
            with tarfile.open(fileobj=response.raw, mode='r:gz') as tar:
                tar.extractall(destination)
        elif url.endswith('.zip'):
            import io
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(destination)
        else:
            raise ValueError(f"Unsupported archive format: {url}")
    
    def list_installed(self) -> List[Dict[str, str]]:
        """List installed packages"""
        packages = []
        if not self.cache_dir.exists():
            return packages
        
        for package_dir in self.cache_dir.iterdir():
            if package_dir.is_dir():
                for version_dir in package_dir.iterdir():
                    if version_dir.is_dir():
                        packages.append({
                            "id": package_dir.name,
                            "version": version_dir.name,
                            "path": str(version_dir)
                        })
        return packages
    
    def load_package_manifest(self, package_id: str, version: str = "latest") -> Optional[Dict]:
        """Load package.json manifest from installed package"""
        package_dir = self.cache_dir / package_id / version
        manifest_path = package_dir / "package.json"
        
        if not manifest_path.exists():
            return None
            
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def get_resource_files(self, package_id: str, version: str = "latest", 
                          resource_type: str = None) -> List[Path]:
        """Get list of FHIR resource files from package"""
        package_dir = self.cache_dir / package_id / version
        
        if not package_dir.exists():
            return []
        
        # Look for resources in common locations
        search_dirs = [
            package_dir / "package",
            package_dir,
            package_dir / "input"
        ]
        
        resource_files = []
        for search_dir in search_dirs:
            if search_dir.exists():
                pattern = "*.json"
                if resource_type:
                    pattern = f"*{resource_type}*.json"
                
                resource_files.extend(search_dir.rglob(pattern))
        
        return resource_files
    
    def build_resource_index(self, package_id: str, version: str = "latest") -> Dict[str, List[Dict]]:
        """Build searchable index of FHIR resources in package"""
        index = {
            "StructureDefinition": [],
            "ValueSet": [],
            "CodeSystem": [],
            "SearchParameter": [],
            "OperationDefinition": [],
            "CapabilityStatement": [],
            "examples": []
        }
        
        resource_files = self.get_resource_files(package_id, version)
        
        for file_path in resource_files:
            try:
                with open(file_path, 'r') as f:
                    resource = json.load(f)
                
                resource_type = resource.get("resourceType", "unknown")
                
                if resource_type in index:
                    index[resource_type].append({
                        "id": resource.get("id"),
                        "url": resource.get("url"),
                        "name": resource.get("name"),
                        "title": resource.get("title"),
                        "version": resource.get("version"),
                        "file_path": str(file_path)
                    })
                else:
                    # Treat as example
                    index["examples"].append({
                        "resourceType": resource_type,
                        "id": resource.get("id"),
                        "file_path": str(file_path)
                    })
            
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        return index
    
    def search_resources(self, package_id: str, version: str = "latest", 
                        query: str = None, resource_type: str = None) -> List[Dict]:
        """Search for resources in package by name, url, or type"""
        index = self.build_resource_index(package_id, version)
        results = []
        
        for res_type, resources in index.items():
            if resource_type and res_type != resource_type:
                continue
                
            for resource in resources:
                if not query:
                    results.append({**resource, "resourceType": res_type})
                elif (query.lower() in str(resource.get("name", "")).lower() or
                      query.lower() in str(resource.get("url", "")).lower() or
                      query.lower() in str(resource.get("title", "")).lower()):
                    results.append({**resource, "resourceType": res_type})
        
        return results


def main():
    parser = argparse.ArgumentParser(description="FHIR Package Manager")
    parser.add_argument("--cache-dir", help="Custom cache directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a package")
    install_parser.add_argument("package_id", help="Package ID (e.g., hl7.fhir.r4.core)")
    install_parser.add_argument("--version", default="latest", help="Package version")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List installed packages")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search resources in package")
    search_parser.add_argument("package_id", help="Package ID")
    search_parser.add_argument("--query", help="Search query")
    search_parser.add_argument("--type", help="Resource type filter")
    search_parser.add_argument("--version", default="latest", help="Package version")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Build resource index for package")
    index_parser.add_argument("package_id", help="Package ID")
    index_parser.add_argument("--version", default="latest", help="Package version")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = FHIRPackageManager(args.cache_dir)
    
    if args.command == "install":
        try:
            manager.install_package(args.package_id, args.version)
        except Exception as e:
            print(f"Error installing package: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "list":
        packages = manager.list_installed()
        if packages:
            print("Installed packages:")
            for pkg in packages:
                print(f"  {pkg['id']}@{pkg['version']} -> {pkg['path']}")
        else:
            print("No packages installed")
    
    elif args.command == "search":
        results = manager.search_resources(args.package_id, args.version, 
                                         args.query, args.type)
        if results:
            print(f"Found {len(results)} resources:")
            for result in results:
                name = result.get("name") or result.get("id", "unknown")
                print(f"  {result['resourceType']}: {name}")
                if result.get("url"):
                    print(f"    URL: {result['url']}")
        else:
            print("No resources found")
    
    elif args.command == "index":
        index = manager.build_resource_index(args.package_id, args.version)
        print(f"Resource index for {args.package_id}@{args.version}:")
        for res_type, resources in index.items():
            if resources:
                print(f"  {res_type}: {len(resources)} resources")


if __name__ == "__main__":
    main()
