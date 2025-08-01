import requests
import json
import sqlite3
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """
    LLM analyzer using OpenRouter API for domain analysis
    """
    
    def __init__(self):
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        
    def get_settings(self) -> Dict[str, str]:
        """Get LLM settings from database"""
        conn = sqlite3.connect('data/drop_analyzer.db')
        cursor = conn.cursor()
        
        settings = {}
        cursor.execute('SELECT key, value FROM settings WHERE key IN (?, ?, ?)', 
                      ('openrouter_api_key', 'openrouter_model', 'analysis_prompt'))
        
        for key, value in cursor.fetchall():
            settings[key] = value
        
        conn.close()
        return settings
    
    def analyze_domains_with_llm(self, domains_data: List[Dict]) -> Dict[str, any]:
        """
        Analyze domains using LLM with configured prompt and model
        """
        settings = self.get_settings()
        
        api_key = settings.get('openrouter_api_key', '')
        model = settings.get('openrouter_model', 'openai/gpt-3.5-turbo')
        prompt_template = settings.get('analysis_prompt', 
            'Analyze the following domain data and provide insights about its quality, potential, and recommendations for use.')
        
        if not api_key:
            return {
                'error': 'OpenRouter API key not configured. Please configure it in settings.',
                'domains': []
            }
        
        results = {
            'total_domains': len(domains_data),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'domains': []
        }
        
        for domain_data in domains_data:
            try:
                analysis = self._analyze_single_domain(domain_data, api_key, model, prompt_template)
                results['domains'].append(analysis)
                results['successful'] += 1
            except Exception as e:
                logger.error(f"Failed to analyze {domain_data.get('domain', 'unknown')}: {e}")
                results['domains'].append({
                    'domain': domain_data.get('domain', 'unknown'),
                    'error': str(e),
                    'llm_analysis': None
                })
                results['failed'] += 1
            
            results['processed'] += 1
        
        return results
    
    def _analyze_single_domain(self, domain_data: Dict, api_key: str, model: str, prompt_template: str) -> Dict:
        """Analyze a single domain with LLM"""
        domain = domain_data.get('domain', 'unknown')
        
        # Prepare domain information for LLM
        domain_info = self._prepare_domain_info(domain_data)
        
        # Create the full prompt
        full_prompt = f"{prompt_template}\n\nDomain Information:\n{domain_info}\n\nPlease provide a comprehensive analysis including:\n1. Domain quality assessment\n2. Business potential\n3. Technical evaluation\n4. Recommendations\n5. Risk factors\n\nProvide the response in a structured format."
        
        # Make API call to OpenRouter
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://drop-analyzer.com',
            'X-Title': 'Drop Analyzer'
        }
        
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a domain analysis expert. Provide detailed, actionable insights about domain quality and potential.'
                },
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        response = requests.post(
            f"{self.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result['choices'][0]['message']['content']
            
            # Save LLM analysis to database
            self._save_llm_analysis(domain, llm_response)
            
            return {
                'domain': domain,
                'llm_analysis': llm_response,
                'model_used': model,
                'tokens_used': result.get('usage', {}).get('total_tokens', 0),
                'status': 'success'
            }
        else:
            error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _prepare_domain_info(self, domain_data: Dict) -> str:
        """Prepare domain information for LLM analysis"""
        domain = domain_data.get('domain', 'unknown')
        quality_score = domain_data.get('quality_score', 0)
        is_available = domain_data.get('is_available', None)
        dns_records = domain_data.get('dns_records', {})
        whois_info = domain_data.get('whois_info', {})
        ssl_info = domain_data.get('ssl_info', {})
        signatures = domain_data.get('signatures', [])
        
        info_parts = [
            f"Domain: {domain}",
            f"Quality Score: {quality_score}/100",
            f"Availability: {'Available' if is_available else 'Registered' if is_available is False else 'Unknown'}",
            f"Technical Signatures: {', '.join(signatures) if signatures else 'None'}",
        ]
        
        # DNS Information
        if dns_records:
            dns_info = []
            if dns_records.get('ns_records'):
                dns_info.append(f"NS Records: {len(dns_records['ns_records'])}")
            if dns_records.get('a_records'):
                dns_info.append(f"A Records: {len(dns_records['a_records'])}")
            if dns_records.get('mx_records'):
                dns_info.append(f"MX Records: {len(dns_records['mx_records'])}")
            if dns_info:
                info_parts.append(f"DNS: {', '.join(dns_info)}")
        
        # WHOIS Information
        if whois_info:
            whois_parts = []
            if whois_info.get('registrar'):
                whois_parts.append(f"Registrar: {whois_info['registrar']}")
            if whois_info.get('creation_date'):
                whois_parts.append(f"Created: {whois_info['creation_date']}")
            if whois_info.get('expiration_date'):
                whois_parts.append(f"Expires: {whois_info['expiration_date']}")
            if whois_parts:
                info_parts.append(f"WHOIS: {', '.join(whois_parts)}")
        
        # SSL Information
        if ssl_info and ssl_info.get('has_ssl'):
            ssl_parts = []
            if ssl_info.get('issuer'):
                issuer = ssl_info['issuer']
                if isinstance(issuer, dict):
                    ssl_parts.append(f"Issuer: {issuer.get('organizationName', 'Unknown')}")
            if ssl_info.get('not_after'):
                ssl_parts.append(f"SSL Expires: {ssl_info['not_after']}")
            if ssl_parts:
                info_parts.append(f"SSL: {', '.join(ssl_parts)}")
        
        return '\n'.join(info_parts)
    
    def _save_llm_analysis(self, domain: str, analysis: str):
        """Save LLM analysis to database"""
        try:
            conn = sqlite3.connect('data/drop_analyzer.db')
            cursor = conn.cursor()
            
            # Update domain with LLM analysis
            cursor.execute('''
                UPDATE domains 
                SET description = COALESCE(description, '') || '\n\nLLM Analysis:\n' || ?
                WHERE domain = ?
            ''', (analysis, domain))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save LLM analysis for {domain}: {e}")
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available OpenRouter models"""
        return [
            {'value': 'openai/gpt-3.5-turbo', 'label': 'GPT-3.5 Turbo', 'provider': 'OpenAI'},
            {'value': 'openai/gpt-4', 'label': 'GPT-4', 'provider': 'OpenAI'},
            {'value': 'openai/gpt-4-turbo', 'label': 'GPT-4 Turbo', 'provider': 'OpenAI'},
            {'value': 'anthropic/claude-3-haiku', 'label': 'Claude 3 Haiku', 'provider': 'Anthropic'},
            {'value': 'anthropic/claude-3-sonnet', 'label': 'Claude 3 Sonnet', 'provider': 'Anthropic'},
            {'value': 'anthropic/claude-3-opus', 'label': 'Claude 3 Opus', 'provider': 'Anthropic'},
            {'value': 'meta-llama/llama-3-8b-instruct', 'label': 'Llama 3 8B', 'provider': 'Meta'},
            {'value': 'meta-llama/llama-3-70b-instruct', 'label': 'Llama 3 70B', 'provider': 'Meta'},
            {'value': 'google/gemini-pro', 'label': 'Gemini Pro', 'provider': 'Google'},
            {'value': 'mistralai/mixtral-8x7b-instruct', 'label': 'Mixtral 8x7B', 'provider': 'Mistral'},
        ]