#!/usr/bin/env python3
"""
HTML Element Extractor with Complete Styling and Media Queries
Extracts an HTML element and all its children with complete CSS styling including media queries
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import sys

class HTMLExtractor:
    def __init__(self, headless=True, viewport_width=1920, viewport_height=1080):
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        
        # Set desktop viewport size
        self.options.add_argument(f'--window-size={viewport_width},{viewport_height}')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-plugins')
        self.options.add_argument('--disable-images')  # Faster loading
        
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.driver = None
    
    def start_browser(self):
        """Initialize the browser with desktop viewport"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        
        # Set viewport size explicitly
        self.driver.set_window_size(self.viewport_width, self.viewport_height)
        
        return self.driver
    
    def extract_element(self, url, xpath, output_file=None):
        """
        Extract HTML element with only relevant styling including media queries
        
        Args:
            url (str): The webpage URL
            xpath (str): XPath to the target element
            output_file (str): Optional output file path
        
        Returns:
            str: Element HTML with only relevant CSS in style tag
        """
        if not self.driver:
            self.start_browser()
        
        try:
            # Load the page
            print(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for initial page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content and lazy loading
            print("Waiting for page to fully load...")
            self.driver.implicitly_wait(3)
            
            # Scroll to trigger lazy loading of images/content
            self._scroll_page_to_load_content()
            
            # Wait for any remaining async content
            self.driver.execute_script("return document.readyState") == "complete"
            
            # Additional wait for JavaScript frameworks
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
                )
            except:
                pass  # jQuery might not be present
            
            # Find the target element with retry logic
            print(f"Finding element: {xpath}")
            element = None
            for attempt in range(3):
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    # Scroll element into view to ensure it's rendered
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    self.driver.implicitly_wait(2)
            
            if not element:
                raise Exception("Could not find element with the specified XPath")
                
            # Get the element's HTML first
            print("Extracting element HTML...")
            element_html = element.get_attribute('outerHTML')
            
            # Get all elements within the target element (including itself)
            all_elements = self.driver.execute_script("""
                var targetElement = arguments[0];
                var allElements = [targetElement];
                var descendants = targetElement.querySelectorAll('*');
                for (var i = 0; i < descendants.length; i++) {
                    allElements.push(descendants[i]);
                }
                return allElements;
            """, element)
            
            # Extract only relevant CSS for these elements (including media queries)
            print("Extracting relevant CSS and media queries...")
            css_content = self._extract_relevant_css_with_media_queries(all_elements)
            
            # Create drop-in HTML with style tag
            drop_in_html = self._create_drop_in_html(element_html, css_content)
            
            # Save to file if specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(drop_in_html)
                print(f"Saved to: {output_file}")
            
            return drop_in_html
            
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def _scroll_page_to_load_content(self):
        """Scroll through the page to trigger lazy loading"""
        try:
            # Get page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in chunks to load lazy content
            scroll_pause_time = 1
            current_position = 0
            
            while current_position < last_height:
                # Scroll down
                current_position += 800  # Scroll 800px at a time
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Wait for content to load
                self.driver.implicitly_wait(scroll_pause_time)
                
                # Check if new content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > last_height:
                    last_height = new_height
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.driver.implicitly_wait(1)
            
        except Exception as e:
            print(f"Scroll loading warning: {e}")
            pass
    
    def _extract_relevant_css_with_media_queries(self, elements):
        """Extract only CSS rules and media queries that apply to the given elements"""
        relevant_css = []
        relevant_media_queries = []
        
        # Get all stylesheets with media query support
        css_data = self.driver.execute_script("""
            var cssData = {
                regularRules: [],
                mediaRules: []
            };
            
            for (var i = 0; i < document.styleSheets.length; i++) {
                try {
                    var sheet = document.styleSheets[i];
                    var rules = sheet.cssRules || sheet.rules;
                    if (rules) {
                        for (var j = 0; j < rules.length; j++) {
                            var rule = rules[j];
                            
                            // Handle regular CSS rules
                            if (rule.selectorText && rule.style) {
                                cssData.regularRules.push({
                                    selector: rule.selectorText,
                                    css: rule.cssText
                                });
                            }
                            // Handle media queries
                            else if (rule.type === CSSRule.MEDIA_RULE) {
                                var mediaRule = {
                                    media: rule.media.mediaText,
                                    rules: []
                                };
                                
                                // Get rules inside media query
                                var mediaRules = rule.cssRules || rule.rules;
                                if (mediaRules) {
                                    for (var k = 0; k < mediaRules.length; k++) {
                                        var innerRule = mediaRules[k];
                                        if (innerRule.selectorText && innerRule.style) {
                                            mediaRule.rules.push({
                                                selector: innerRule.selectorText,
                                                css: innerRule.cssText
                                            });
                                        }
                                    }
                                }
                                
                                if (mediaRule.rules.length > 0) {
                                    cssData.mediaRules.push(mediaRule);
                                }
                            }
                        }
                    }
                } catch(e) {
                    // Skip inaccessible stylesheets (CORS)
                }
            }
            return cssData;
        """)
        
        # Test regular CSS rules against our elements
        for rule in css_data['regularRules']:
            try:
                # Check if any of our elements match this selector
                matches = self.driver.execute_script("""
                    var selector = arguments[0];
                    var elements = arguments[1];
                    
                    try {
                        for (var i = 0; i < elements.length; i++) {
                            if (elements[i].matches && elements[i].matches(selector)) {
                                return true;
                            }
                        }
                        return false;
                    } catch(e) {
                        return false;
                    }
                """, rule['selector'], elements)
                
                if matches:
                    relevant_css.append(rule['css'])
                    
            except Exception:
                continue
        
        # Test media query rules against our elements
        for media_rule in css_data['mediaRules']:
            relevant_rules_in_media = []
            
            for rule in media_rule['rules']:
                try:
                    # Check if any of our elements match this selector
                    matches = self.driver.execute_script("""
                        var selector = arguments[0];
                        var elements = arguments[1];
                        
                        try {
                            for (var i = 0; i < elements.length; i++) {
                                if (elements[i].matches && elements[i].matches(selector)) {
                                    return true;
                                }
                            }
                            return false;
                        } catch(e) {
                            return false;
                        }
                    """, rule['selector'], elements)
                    
                    if matches:
                        relevant_rules_in_media.append(rule['css'])
                        
                except Exception:
                    continue
            
            # If we found relevant rules in this media query, include the entire media query
            if relevant_rules_in_media:
                media_query_css = f"@media {media_rule['media']} {{\n"
                media_query_css += "\n".join(f"  {rule}" for rule in relevant_rules_in_media)
                media_query_css += "\n}"
                relevant_media_queries.append(media_query_css)
        
        # Get inline styles from elements
        inline_styles = []
        for el in elements:
            try:
                style_attr = el.get_attribute('style')
                if style_attr:
                    # Create a unique selector for this element
                    tag_name = el.tag_name.lower()
                    element_id = el.get_attribute('id')
                    classes = el.get_attribute('class')
                    
                    if element_id:
                        selector = f"#{element_id}"
                    elif classes:
                        class_list = classes.split()
                        selector = f".{'.'.join(class_list)}"
                    else:
                        selector = tag_name
                    
                    inline_styles.append(f"{selector} {{ {style_attr} }}")
            except Exception:
                continue
        
        # Combine all relevant CSS: regular rules + inline styles + media queries
        all_css = relevant_css + inline_styles + relevant_media_queries
        
        return '\n\n'.join(all_css)
    
    def _extract_relevant_css(self, elements):
        """Extract only CSS rules that apply to the given elements (legacy method)"""
        relevant_css = []
        
        # Get all stylesheets
        style_sheets = self.driver.execute_script("""
            var sheets = [];
            for (var i = 0; i < document.styleSheets.length; i++) {
                try {
                    var sheet = document.styleSheets[i];
                    var rules = sheet.cssRules || sheet.rules;
                    if (rules) {
                        for (var j = 0; j < rules.length; j++) {
                            if (rules[j].selectorText && rules[j].style) {
                                sheets.push({
                                    selector: rules[j].selectorText,
                                    css: rules[j].cssText
                                });
                            }
                        }
                    }
                } catch(e) {
                    // Skip inaccessible stylesheets (CORS)
                }
            }
            return sheets;
        """)
        
        # Test each CSS rule against our elements
        for rule in style_sheets:
            try:
                # Check if any of our elements match this selector
                matches = self.driver.execute_script("""
                    var selector = arguments[0];
                    var elements = arguments[1];
                    
                    try {
                        for (var i = 0; i < elements.length; i++) {
                            if (elements[i].matches && elements[i].matches(selector)) {
                                return true;
                            }
                        }
                        return false;
                    } catch(e) {
                        return false;
                    }
                """, rule['selector'], elements)
                
                if matches:
                    relevant_css.append(rule['css'])
                    
            except Exception:
                continue
        
        # Get inline styles from elements
        inline_styles = []
        for el in elements:
            try:
                style_attr = el.get_attribute('style')
                if style_attr:
                    # Create a unique selector for this element
                    tag_name = el.tag_name.lower()
                    element_id = el.get_attribute('id')
                    classes = el.get_attribute('class')
                    
                    if element_id:
                        selector = f"#{element_id}"
                    elif classes:
                        class_list = classes.split()
                        selector = f".{'.'.join(class_list)}"
                    else:
                        selector = tag_name
                    
                    inline_styles.append(f"{selector} {{ {style_attr} }}")
            except Exception:
                continue
        
        # Combine all relevant CSS
        all_css = relevant_css + inline_styles
        
        return '\n'.join(all_css)
    
    def _get_computed_styles(self):
        """Generate CSS from computed styles of all elements"""
        try:
            # JavaScript to extract computed styles
            js_script = """
            var styles = '';
            var elements = document.querySelectorAll('*');
            var processedSelectors = new Set();
            
            elements.forEach(function(el, index) {
                var computedStyle = window.getComputedStyle(el);
                var selector = el.tagName.toLowerCase();
                
                // Create more specific selector
                if (el.id) {
                    selector = '#' + el.id;
                } else if (el.className) {
                    var classes = el.className.split(' ').filter(c => c.trim());
                    if (classes.length > 0) {
                        selector = '.' + classes.join('.');
                    }
                } else {
                    selector = el.tagName.toLowerCase() + ':nth-child(' + (index + 1) + ')';
                }
                
                if (!processedSelectors.has(selector)) {
                    processedSelectors.add(selector);
                    styles += selector + ' {\\n';
                    
                    // Get important CSS properties
                    var importantProps = [
                        'display', 'position', 'top', 'right', 'bottom', 'left',
                        'width', 'height', 'margin', 'padding', 'border',
                        'background', 'color', 'font', 'text-align', 'z-index',
                        'float', 'clear', 'overflow', 'visibility', 'opacity'
                    ];
                    
                    for (var prop of importantProps) {
                        var value = computedStyle.getPropertyValue(prop);
                        if (value && value !== 'initial' && value !== 'normal') {
                            styles += '  ' + prop + ': ' + value + ';\\n';
                        }
                    }
                    
                    styles += '}\\n\\n';
                }
            });
            
            return styles;
            """
            
            return self.driver.execute_script(js_script)
        except:
            return ""
    
    def _create_drop_in_html(self, element_html, css_content):
        """Create drop-in HTML with minimal style tag"""
        if css_content.strip():
            return f"""<style>
{css_content}
</style>
{element_html}"""
        else:
            return element_html


def main():
    """Main function for command line usage"""
    if len(sys.argv) < 3:
        print("Usage: python html_extractor.py <URL> <XPATH> [output_file]")
        print("Example: python html_extractor.py https://example.com '/html/body/div[1]/footer' output.html")
        return
    
    url = sys.argv[1]
    xpath = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "extracted_element.html"
    
    extractor = HTMLExtractor(headless=True)
    result = extractor.extract_element(url, xpath, output_file)
    
    if result:
        print("Extraction completed successfully!")
        print(f"Element extracted from: {xpath}")
        print(f"Output saved to: {output_file}")
    else:
        print("Extraction failed!")


# Example usage as a module
if __name__ == "__main__":
    # Command line usage
    if len(sys.argv) > 1:
        main()
    else:
        # Example usage
        extractor = HTMLExtractor(headless=True, viewport_width=1920, viewport_height=1080)
        
        # Extract a footer element
        html_result = extractor.extract_element(
            url="https://example.com",
            xpath="/html/body/div[1]/footer",
            output_file="footer_extracted.html"
        )
        
        if html_result:
            print("Success! Drop-in HTML ready with media queries.")
        else:
            print("Failed to extract element.")