import socket
import ssl
import whois
import dns.resolver
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainScanner:
    """
    Domain scanner based on xuemian168/domain-scanner functionality
    Provides DNS, WHOIS, and SSL certificate analysis
    """
    
    def __init__(self):
        self.available_indicators = [
            "no match for", "not found", "no data found", "no entries found",
            "domain not found", "no object found", "no matching record",
            "status: free", "status: available", "is available for registration",
            "domain status: no object found", "no match!!", "not registered",
            "available for registration", "domain available", "available domain",
            "free domain", "domain free", "unregistered domain", "domain unregistered",
            "no match", "not found in database", "no matching record found",
            "domain name not found", "object does not exist", "no such domain",
            "domain status: available", "registration status: available",
            "state: available", "domain state: available", "available for purchase",
            "this domain is available", "domain is available", "can be registered",
            "eligible for registration", "free for registration", "open for registration",
            "ready for registration", "registration available", "status code: 210",
            "status code: 220", "response: 210", "response: 220",
        ]
        
        self.unavailable_indicators = [
            "registrar:", "registrant:", "creation date:", "updated date:",
            "expiration date:", "name server:", "nserver:", "status: registered",
            "status: active", "status: ok", "status: connect",
            "status: clienttransferprohibited", "status: servertransferprohibited",
            "domain status: registered", "domain status: active", "registration date:",
            "expiry date:", "registry expiry date:", "registrar registration expiration date:",
            "admin contact:", "tech contact:", "billing contact:", "dnssec:",
            "domain servers in listed order:", "registered domain", "registered on:",
            "expires on:", "last updated on:", "changed:", "holder:", "person:",
            "sponsoring registrar:", "whois server:", "referral url:", "domain name:",
            "registry domain id:", "registrar whois server:", "registrar url:",
            "registrar iana id:", "registrar abuse contact email:",
            "registrar abuse contact phone:", "reseller:", "domain status:",
            "name server", "dnssec: unsigned", "dnssec: signed",
        ]

    def check_dns_records(self, domain: str) -> Dict[str, any]:
        """Check DNS records for a domain"""
        dns_info = {
            'ns_records': [],
            'a_records': [],
            'mx_records': [],
            'txt_records': [],
            'cname_records': []
        }
        
        try:
            # NS Records
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                dns_info['ns_records'] = [str(record) for record in ns_records]
            except:
                pass
            
            # A Records
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                dns_info['a_records'] = [str(record) for record in a_records]
            except:
                pass
            
            # MX Records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                dns_info['mx_records'] = [f"{record.preference} {record.exchange}" for record in mx_records]
            except:
                pass
            
            # TXT Records
            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                dns_info['txt_records'] = [str(record) for record in txt_records]
            except:
                pass
            
            # CNAME Records
            try:
                cname_records = dns.resolver.resolve(domain, 'CNAME')
                dns_info['cname_records'] = [str(record) for record in cname_records]
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error checking DNS for {domain}: {e}")
        
        return dns_info

    def check_whois_info(self, domain: str, max_retries: int = 3) -> Dict[str, any]:
        """Check WHOIS information for a domain"""
        whois_info = {
            'raw_data': '',
            'registrar': '',
            'creation_date': None,
            'expiration_date': None,
            'last_updated': None,
            'name_servers': [],
            'status': [],
            'registrant': '',
            'admin_contact': '',
            'tech_contact': '',
            'is_registered': False,
            'is_available': False
        }
        
        for attempt in range(max_retries):
            try:
                w = whois.whois(domain)
                
                if w:
                    whois_info['raw_data'] = str(w)
                    whois_info['registrar'] = w.registrar if hasattr(w, 'registrar') and w.registrar else ''
                    whois_info['creation_date'] = w.creation_date if hasattr(w, 'creation_date') else None
                    whois_info['expiration_date'] = w.expiration_date if hasattr(w, 'expiration_date') else None
                    whois_info['last_updated'] = w.updated_date if hasattr(w, 'updated_date') else None
                    whois_info['name_servers'] = w.name_servers if hasattr(w, 'name_servers') and w.name_servers else []
                    whois_info['status'] = w.status if hasattr(w, 'status') and w.status else []
                    
                    # Check if domain is registered
                    raw_lower = whois_info['raw_data'].lower()
                    
                    # Check for availability indicators
                    is_available = any(indicator in raw_lower for indicator in self.available_indicators)
                    
                    # Check for registration indicators
                    is_registered = any(indicator in raw_lower for indicator in self.unavailable_indicators)
                    
                    whois_info['is_available'] = is_available and not is_registered
                    whois_info['is_registered'] = is_registered
                    
                break
                
            except Exception as e:
                logger.warning(f"WHOIS attempt {attempt + 1} failed for {domain}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error(f"All WHOIS attempts failed for {domain}")
        
        return whois_info

    def check_ssl_certificate(self, domain: str, timeout: int = 5) -> Dict[str, any]:
        """Check SSL certificate for a domain"""
        ssl_info = {
            'has_ssl': False,
            'issuer': '',
            'subject': '',
            'not_before': None,
            'not_after': None,
            'serial_number': '',
            'version': '',
            'signature_algorithm': ''
        }
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((domain, 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        ssl_info['has_ssl'] = True
                        ssl_info['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                        ssl_info['subject'] = dict(x[0] for x in cert.get('subject', []))
                        ssl_info['not_before'] = cert.get('notBefore', '')
                        ssl_info['not_after'] = cert.get('notAfter', '')
                        ssl_info['serial_number'] = cert.get('serialNumber', '')
                        ssl_info['version'] = cert.get('version', '')
                        
        except Exception as e:
            logger.warning(f"SSL check failed for {domain}: {e}")
        
        return ssl_info

    def check_domain_signatures(self, domain: str) -> List[str]:
        """Check domain signatures similar to the Go implementation"""
        signatures = []
        
        try:
            # Check DNS NS records
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                if ns_records:
                    signatures.append('DNS_NS')
            except:
                pass
            
            # Check DNS A records
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                if a_records:
                    signatures.append('DNS_A')
            except:
                pass
            
            # Check DNS MX records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                if mx_records:
                    signatures.append('DNS_MX')
            except:
                pass
            
            # Check WHOIS
            whois_info = self.check_whois_info(domain)
            if whois_info['is_registered']:
                signatures.append('WHOIS')
            
            # Check SSL
            ssl_info = self.check_ssl_certificate(domain)
            if ssl_info['has_ssl']:
                signatures.append('SSL')
                
        except Exception as e:
            logger.error(f"Error checking signatures for {domain}: {e}")
        
        return signatures

    def analyze_domain(self, domain: str) -> Dict[str, any]:
        """Comprehensive domain analysis"""
        logger.info(f"Analyzing domain: {domain}")
        
        analysis = {
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'dns_records': {},
            'whois_info': {},
            'ssl_info': {},
            'signatures': [],
            'is_available': None,
            'quality_score': 0,
            'recommendations': []
        }
        
        try:
            # DNS Analysis
            analysis['dns_records'] = self.check_dns_records(domain)
            
            # WHOIS Analysis
            analysis['whois_info'] = self.check_whois_info(domain)
            
            # SSL Analysis
            analysis['ssl_info'] = self.check_ssl_certificate(domain)
            
            # Signatures
            analysis['signatures'] = self.check_domain_signatures(domain)
            
            # Availability
            analysis['is_available'] = analysis['whois_info']['is_available']
            
            # Quality Score Calculation
            analysis['quality_score'] = self._calculate_quality_score(analysis)
            
            # Recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing domain {domain}: {e}")
            analysis['error'] = str(e)
        
        return analysis

    def _calculate_quality_score(self, analysis: Dict) -> int:
        """Calculate domain quality score based on various factors"""
        score = 0
        
        # DNS records presence
        dns = analysis['dns_records']
        if dns.get('ns_records'):
            score += 20
        if dns.get('a_records'):
            score += 20
        if dns.get('mx_records'):
            score += 15
        if dns.get('txt_records'):
            score += 10
        
        # WHOIS information
        whois = analysis['whois_info']
        if whois.get('registrar'):
            score += 10
        if whois.get('creation_date'):
            score += 10
        if whois.get('name_servers'):
            score += 10
        
        # SSL certificate
        if analysis['ssl_info'].get('has_ssl'):
            score += 15
        
        return min(score, 100)

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if analysis['is_available']:
            recommendations.append("Domain is available for registration")
        else:
            recommendations.append("Domain is already registered")
        
        if not analysis['dns_records'].get('a_records'):
            recommendations.append("No A records found - domain may not be actively used")
        
        if not analysis['ssl_info'].get('has_ssl'):
            recommendations.append("No SSL certificate found - HTTPS not available")
        
        if analysis['quality_score'] < 50:
            recommendations.append("Low quality score - limited web presence")
        elif analysis['quality_score'] > 80:
            recommendations.append("High quality score - strong web presence")
        
        return recommendations

    def batch_analyze_domains(self, domains: List[str]) -> Dict[str, any]:
        """Analyze multiple domains in batch"""
        results = {
            'total_domains': len(domains),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'domains': []
        }
        
        for domain in domains:
            try:
                analysis = self.analyze_domain(domain)
                results['domains'].append(analysis)
                results['successful'] += 1
            except Exception as e:
                logger.error(f"Failed to analyze {domain}: {e}")
                results['domains'].append({
                    'domain': domain,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                results['failed'] += 1
            
            results['processed'] += 1
        
        return results