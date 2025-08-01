import requests
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class WebArchiveAnalyzer:
    """
    Analyzer for Web Archive (Wayback Machine) data
    """
    
    def __init__(self):
        self.wayback_base_url = "http://archive.org/wayback/available"
        self.cdx_base_url = "http://web.archive.org/cdx/search/search/cdx"
    
    def check_wayback_availability(self, domain: str) -> Dict[str, any]:
        """Check if domain has snapshots in Wayback Machine"""
        try:
            response = requests.get(
                f"{self.wayback_base_url}?url={domain}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'available': data.get('available', False),
                    'url': data.get('archived_snapshots', {}).get('closest', {}).get('url', ''),
                    'timestamp': data.get('archived_snapshots', {}).get('closest', {}).get('timestamp', ''),
                    'status': data.get('archived_snapshots', {}).get('closest', {}).get('status', '')
                }
            else:
                logger.warning(f"Wayback availability check failed for {domain}: {response.status_code}")
                return {'available': False}
        except Exception as e:
            logger.error(f"Error checking Wayback for {domain}: {e}")
            return {'available': False}
    
    def get_snapshot_count(self, domain: str) -> int:
        """Get approximate number of snapshots for domain"""
        try:
            response = requests.get(
                f"{self.cdx_base_url}?url={domain}&output=json&limit=1&showNumPages=true",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('num_pages', 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting snapshot count for {domain}: {e}")
            return 0
    
    def analyze_webarchive(self, domain: str) -> Dict[str, any]:
        """Comprehensive Web Archive analysis for domain"""
        analysis = {
            'domain': domain,
            'has_snapshots': False,
            'total_snapshots': 0,
            'first_snapshot': None,
            'last_snapshot': None,
            'years_covered': 0
        }
        
        try:
            availability = self.check_wayback_availability(domain)
            analysis['has_snapshots'] = availability['available']
            
            if analysis['has_snapshots']:
                analysis['total_snapshots'] = self.get_snapshot_count(domain)
                
                # Get first snapshot
                response_first = requests.get(
                    f"{self.cdx_base_url}?url={domain}&output=json&limit=1&sort=oldest",
                    timeout=10
                )
                if response_first.status_code == 200:
                    data_first = response_first.json()
                    if data_first and len(data_first) > 1:
                        analysis['first_snapshot'] = data_first[1][1]  # timestamp
                
                # Get last snapshot
                response_last = requests.get(
                    f"{self.cdx_base_url}?url={domain}&output=json&limit=1&sort=latest",
                    timeout=10
                )
                if response_last.status_code == 200:
                    data_last = response_last.json()
                    if data_last and len(data_last) > 1:
                        analysis['last_snapshot'] = data_last[1][1]
                
                # Calculate years covered
                if analysis['first_snapshot'] and analysis['last_snapshot']:
                    first_year = int(analysis['first_snapshot'][:4])
                    last_year = int(analysis['last_snapshot'][:4])
                    analysis['years_covered'] = last_year - first_year + 1
            
        except Exception as e:
            logger.error(f"Error analyzing Web Archive for {domain}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def batch_analyze_webarchive(self, domains: List[str]) -> Dict[str, any]:
        """Batch analysis of multiple domains in Web Archive"""
        results = {
            'total_domains': len(domains),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'domains': []
        }
        
        for domain in domains:
            try:
                analysis = self.analyze_webarchive(domain)
                results['domains'].append(analysis)
                results['successful'] += 1
            except Exception as e:
                logger.error(f"Failed to analyze {domain}: {e}")
                results['domains'].append({
                    'domain': domain,
                    'error': str(e)
                })
                results['failed'] += 1
            
            results['processed'] += 1
        
        return results