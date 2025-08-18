# abacus_integration.py
# Integrates with your Abacus AI setup to pull data from Google Sheets

import logging
from datetime import datetime
from typing import List, Dict, Optional
import re

try:
    from abacusai import ApiClient
    ABACUS_AVAILABLE = True
except ImportError:
    ABACUS_AVAILABLE = False
    print("⚠️ AbacusAI not installed. Using mock data only.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbacusManager:
    """
    Abacus AI Manager - integrates with your existing setup
    """
    
    def __init__(self):
        """Initialize Abacus AI Manager"""
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        """Setup Abacus AI client"""
        try:
            if ABACUS_AVAILABLE:
                logger.info("Setting up Abacus AI client...")
                # Client will be initialized with API key when methods are called
                self.client = None  # Will be created per request with API key
                logger.info("Abacus AI client setup ready")
            else:
                logger.warning("Abacus AI not available - using fallback mode")
                
        except Exception as e:
            logger.error(f"Error setting up Abacus AI client: {e}")
            self.client = None
    
    def get_orders_data(self, api_key: str, feature_group_id: str, dataset_id: str, project_id: str) -> List[Dict]:
        """
        Get orders data from Abacus AI using your existing setup
        
        Args:
            api_key: Your Abacus AI API key
            feature_group_id: Your feature group ID (4d868f4c)
            dataset_id: Your dataset ID (3dee61c66)
            project_id: Your ChatLLM project ID (16b4367d2c)
            
        Returns:
            List of order dictionaries
        """
        try:
            if not ABACUS_AVAILABLE:
                logger.warning("Abacus AI not available, using mock data")
                return self._get_mock_data()
            
            # Initialize client with API key
            client = ApiClient(api_key)
            logger.info(f"🤖 Connecting to Abacus AI with project {project_id}")
            
            # Try multiple methods to get data, based on your test files
            orders_data = []
            
            # Method 1: Try ChatLLM approach (this worked in your tests)
            try:
                logger.info("📋 Trying ChatLLM method...")
                orders_data = self._get_data_via_chatllm(client, project_id)
                if orders_data:
                    logger.info(f"✅ SUCCESS with ChatLLM: {len(orders_data)} orders")
                    return orders_data
            except Exception as e:
                logger.warning(f"ChatLLM method failed: {e}")
            
            # Method 2: Try direct dataset methods
            try:
                logger.info("📊 Trying direct dataset methods...")
                orders_data = self._get_data_via_dataset(client, dataset_id, feature_group_id)
                if orders_data:
                    logger.info(f"✅ SUCCESS with dataset method: {len(orders_data)} orders")
                    return orders_data
            except Exception as e:
                logger.warning(f"Dataset method failed: {e}")
            
            # Method 3: Try feature group streaming data
            try:
                logger.info("📡 Trying streaming data method...")
                orders_data = self._get_data_via_streaming(client, feature_group_id)
                if orders_data:
                    logger.info(f"✅ SUCCESS with streaming: {len(orders_data)} orders")
                    return orders_data
            except Exception as e:
                logger.warning(f"Streaming method failed: {e}")
            
            # If all methods fail, use mock data
            logger.warning("All Abacus AI methods failed, using mock data")
            return self._get_mock_data()
            
        except Exception as e:
            logger.error(f"Error getting data from Abacus AI: {e}")
            return self._get_mock_data()
    
    def _get_data_via_chatllm(self, client, project_id: str) -> List[Dict]:
        """
        Get data using ChatLLM approach (this worked in your tests)
        """
        try:
            # Create chat session
            session = client.create_chat_session(project_id)
            logger.info(f"Created chat session: {session.chat_session_id}")
            
            # Ask for structured data
            response = client.get_chat_response(
                session.chat_session_id,
                "Show me all orders from the Orders sheet. Format the response as a structured list with these fields for each order: Booth #, Exhibitor Name, Item, Status, Date, Quantity, Color, Comments, Section. Include all available orders."
            )
            
            logger.info("📋 ChatLLM Response received")
            
            # Parse the response into structured data
            orders = self._parse_chatllm_response(response.content)
            return orders
            
        except Exception as e:
            logger.error(f"ChatLLM method error: {e}")
            return []
    
    def _get_data_via_dataset(self, client, dataset_id: str, feature_group_id: str) -> List[Dict]:
        """
        Try to get data via direct dataset methods
        """
        try:
            # Try different dataset methods from your test file
            methods_to_try = [
                'get_dataset_data_as_pandas',
                'describe_dataset_data',
                'get_dataset_data'
            ]
            
            for method_name in methods_to_try:
                if hasattr(client, method_name):
                    try:
                        logger.info(f"🔄 Trying {method_name}...")
                        data = getattr(client, method_name)(dataset_id)
                        
                        if data is not None:
                            logger.info(f"✅ Got data with {method_name}")
                            return self._parse_dataset_response(data)
                            
                    except Exception as e:
                        logger.warning(f"{method_name} failed: {e}")
            
            return []
            
        except Exception as e:
            logger.error(f"Dataset method error: {e}")
            return []
    
    def _get_data_via_streaming(self, client, feature_group_id: str) -> List[Dict]:
        """
        Try to get data via streaming feature group data
        """
        try:
            if hasattr(client, 'get_recent_feature_group_streamed_data'):
                logger.info("🔄 Trying get_recent_feature_group_streamed_data...")
                data = client.get_recent_feature_group_streamed_data(feature_group_id)
                
                if data is not None:
                    logger.info("✅ Got streaming data")
                    return self._parse_streaming_response(data)
            
            return []
            
        except Exception as e:
            logger.error(f"Streaming method error: {e}")
            return []
    
    def _parse_chatllm_response(self, response_content: str) -> List[Dict]:
        """
        Parse ChatLLM response into structured order data
        """
        try:
            orders = []
            lines = response_content.split('\n')
            
            current_order = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for field patterns
                if 'Booth' in line and '#' in line:
                    if current_order:
                        orders.append(self._normalize_order(current_order))
                        current_order = {}
                    
                    # Extract booth number
                    booth_match = re.search(r'[A-Z]-?\d+', line)
                    if booth_match:
                        current_order['booth_number'] = booth_match.group()
                
                elif 'Exhibitor' in line and 'Name' in line:
                    # Extract exhibitor name
                    name_match = re.search(r'Name:?\s*(.+)', line, re.IGNORECASE)
                    if name_match:
                        current_order['exhibitor_name'] = name_match.group(1).strip()
                
                elif 'Item:' in line:
                    item_match = re.search(r'Item:?\s*(.+)', line, re.IGNORECASE)
                    if item_match:
                        current_order['item'] = item_match.group(1).strip()
                
                elif 'Status:' in line:
                    status_match = re.search(r'Status:?\s*(.+)', line, re.IGNORECASE)
                    if status_match:
                        current_order['status'] = self._map_status(status_match.group(1).strip())
                
                # Add other field parsing as needed
            
            # Add the last order
            if current_order:
                orders.append(self._normalize_order(current_order))
            
            logger.info(f"Parsed {len(orders)} orders from ChatLLM response")
            return orders
            
        except Exception as e:
            logger.error(f"Error parsing ChatLLM response: {e}")
            return []
    
    def _parse_dataset_response(self, data) -> List[Dict]:
        """
        Parse dataset response into structured order data
        """
        try:
            orders = []
            
            # Handle pandas DataFrame
            if hasattr(data, 'iterrows'):
                for index, row in data.iterrows():
                    order = {
                        'booth_number': str(row.get('Booth #', '')),
                        'exhibitor_name': str(row.get('Exhibitor Name', '')),
                        'item': str(row.get('Item', '')),
                        'status': self._map_status(str(row.get('Status', ''))),
                        'order_date': str(row.get('Date', '')),
                        'quantity': self._safe_int(row.get('Quantity', 1)),
                        'color': str(row.get('Color', '')),
                        'comments': str(row.get('Comments', '')),
                        'section': str(row.get('Section', ''))
                    }
                    orders.append(self._normalize_order(order))
            
            # Handle list of dictionaries
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        orders.append(self._normalize_order(item))
            
            logger.info(f"Parsed {len(orders)} orders from dataset response")
            return orders
            
        except Exception as e:
            logger.error(f"Error parsing dataset response: {e}")
            return []
    
    def _parse_streaming_response(self, data) -> List[Dict]:
        """
        Parse streaming response into structured order data
        """
        try:
            orders = []
            
            # Handle the streaming data format
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        orders.append(self._normalize_order(item))
            
            logger.info(f"Parsed {len(orders)} orders from streaming response")
            return orders
            
        except Exception as e:
            logger.error(f"Error parsing streaming response: {e}")
            return []
    
    def _normalize_order(self, order_dict: Dict) -> Dict:
        """
        Normalize order data to consistent format
        """
        return {
            'id': order_dict.get('id', f"ORD-{datetime.now().strftime('%Y%m%d')}-{hash(str(order_dict)) % 1000:03d}"),
            'booth_number': str(order_dict.get('booth_number', order_dict.get('Booth #', ''))).strip(),
            'exhibitor_name': str(order_dict.get('exhibitor_name', order_dict.get('Exhibitor Name', ''))).strip(),
            'item': str(order_dict.get('item', order_dict.get('Item', ''))).strip(),
            'description': str(order_dict.get('description', f"Order from Abacus AI: {order_dict.get('item', 'Unknown item')}")),
