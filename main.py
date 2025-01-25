import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time
import re

def extract_page_details(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Title extraction
            title = soup.title.string if soup.title else "No Title"
            
            # Metadata extraction
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description['content'] if meta_description else ''
            
            # Keywords extraction
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            keywords = meta_keywords['content'] if meta_keywords else ''
            
            # Header text extraction
            headers_text = {
                'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
                'h2': [h.get_text(strip=True) for h in soup.find_all('h2')]
            }
            
            # Text content extraction
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
            
            # Link analysis
            internal_links = [a['href'] for a in soup.find_all('a', href=True) 
                              if a['href'].startswith('/') or a['href'].startswith(url)]
            external_links = [a['href'] for a in soup.find_all('a', href=True) 
                              if a['href'].startswith('http') and url not in a['href']]
            
            # Image count and alt text
            images = [{
                'src': img.get('src', ''),
                'alt': img.get('alt', '')
            } for img in soup.find_all('img')]
            
            # Language detection
            lang = soup.html.get('lang', 'Not specified')
            
            # Basic text statistics
            total_text = ' '.join(paragraphs)
            word_count = len(re.findall(r'\w+', total_text))
            
            return {
                'url': url,
                'title': title.strip(),
                'description': description,
                'keywords': keywords,
                'headers': headers_text,
                'word_count': word_count,
                'language': lang,
                'internal_links_count': len(internal_links),
                'external_links_count': len(external_links),
                'image_count': len(images),
                'sample_paragraphs': paragraphs[:3]  # First 3 paragraphs
            }
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e)
        }
    
    return None

def parse_sitemap(sitemap_path):
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    
    namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    urls = [url.find('sitemap:loc', namespace).text for url in root.findall('.//sitemap:url', namespace)]
    
    # Limit to first 20 URLs
    urls = urls[:20]
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        page_info_futures = {executor.submit(extract_page_details, url): url for url in urls}
        
        for future in concurrent.futures.as_completed(page_info_futures):
            result = future.result()
            if result:
                results.append(result)
            
            time.sleep(0.5)
    
    return results

def main():
    #sitemap_path = 'main-sitemap.xml'
    sitemap_path = 'support-sitemap.xml'
    page_details = parse_sitemap(sitemap_path)
    
    # Pretty print results
    import json
    print(json.dumps(page_details, indent=2))

if __name__ == "__main__":
    main()