# sheets_integration.py
# This script adapts your existing Google Sheets code for the API (NO PANDAS)

import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """
    Google Sheets Manager - adapted from your existing code (NO PANDAS)
    """
    
    def __init__(self, credentials_path: str = None):
        """
        Initialize Google Sheets Manager
        
        Args:
            credentials_path: Path to your Google service account JSON file
        """
        self.credentials_path = credentials_path
        self.gc = None
        self.setup_client()
    
    def setup_client(self):
        """Setup Google Sheets client"""
        try:
            if self.credentials_path:
                # Use service account credentials
                credentials = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                self.gc = gspread.authorize(credentials)
            else:
                # Use default authentication (for development)
                self.gc = gspread.service_account()
            
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets client: {e}")
            self.gc = None
    
    def get_data(self, sheet_id: str, worksheet_name: str = "Orders") -> List[List]:
        """
        Get data from Google Sheets - NO PANDAS VERSION
        
        Args:
            sheet_id: Google Sheet ID
            worksheet_name: Name of the worksheet
            
        Returns:
            List of lists with the sheet data
        """
        try:
            if not self.gc:
                raise Exception("Google Sheets client not initialized")
            
            # Open the spreadsheet
            spreadsheet = self.gc.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Get all values
            data = worksheet.get_all_values()
            
            if not data:
                return []
            
            logger.info(f"Successfully loaded {len(data)} rows from {worksheet_name}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting data from sheet: {e}")
            return []
    
    def get_worksheets(self, sheet_id: str) -> List[str]:
        """
        Get list of worksheet names
        
        Args:
            sheet_id: Google Sheet ID
            
        Returns:
            List of worksheet names
        """
        try:
            if not self.gc:
                return []
            
            spreadsheet = self.gc.open_by_key(sheet_id)
            worksheets = [ws.title for ws in spreadsheet.worksheets()]
            
            logger.info(f"Found worksheets: {worksheets}")
            return worksheets
            
        except Exception as e:
            logger.error(f"Error getting worksheets: {e}")
            return []
    
    def map_order_status(self, sheet_status: str) -> str:
        """
        Map Google Sheets status to API status format
        
        Args:
            sheet_status: Status from Google Sheets
            
        Returns:
            Mapped status for API
        """
        status_mapping = {
            'Delivered': 'delivered',
            'Received': 'delivered',
            'Out for delivery': 'out-for-delivery',
            'In route from warehouse': 'in-route',
            'In Process': 'in-process',
            'cancelled': 'cancelled',
            'Cancelled': 'cancelled'
        }
        
        return status_mapping.get(sheet_status, 'in-process')
    
    def parse_orders_data(self, data: List[List]) -> List[Dict]:
        """
        Parse raw data and convert to order dictionaries - NO PANDAS VERSION
        
        Args:
            data: List of lists with raw sheet data
            
        Returns:
            List of order dictionaries
        """
        orders = []
        
        try:
            if not data or len(data) < 2:
                return []
            
            # Find header row (look for 'Booth' column)
            header_row_idx = 0
            headers = []
            
            for i, row in enumerate(data):
                if any('Booth' in str(cell) for cell in row):
                    headers = [str(cell).strip() for cell in row]
                    header_row_idx = i
                    break
            
            if not headers:
                # Use first row as headers if no 'Booth' found
                headers = [str(cell).strip() for cell in data[0]]
                header_row_idx = 0
            
            logger.info(f"Using headers: {headers}")
            
            # Process data rows
            for row_idx, row in enumerate(data[header_row_idx + 1:], start=header_row_idx + 1):
                if not row or len(row) == 0:
                    continue
                
                # Create dictionary from row data
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = str(value).strip()
                
                # Extract order data
                booth_num = row_dict.get('Booth #', '').strip()
                exhibitor_name = row_dict.get('Exhibitor Name', '').strip()
                item = row_dict.get('Item', '').strip()
                
                # Skip rows without essential data
                if not booth_num or not exhibitor_name:
                    continue
                
                # Create order ID
                date = row_dict.get('Date', '').strip()
                order_id = f"ORD-{date.replace('/', '-')}-{booth_num}-{row_idx}"
                
                # Build order dictionary
                order = {
                    'id': order_id,
                    'booth_number': booth_num,
                    'exhibitor_name': exhibitor_name,
                    'item': item,
                    'description': f"Order from Google Sheets: {item}",
                    'color': row_dict.get('Color', '').strip(),
                    'quantity': self._safe_int(row_dict.get('Quantity', '1')),
                    'status': self.map_order_status(row_dict.get('Status', '').strip()),
                    'order_date': date,
                    'comments': row_dict.get('Comments', '').strip(),
                    'section': row_dict.get('Section', '').strip(),
                    'type': row_dict.get('Type', '').strip(),
                    'user': row_dict.get('User', '').strip(),
                    'hour': row_dict.get('Hour', '').strip(),
                    'abacus_ai_processed': True,
                    'data_source': 'Google Sheets via Abacus AI'
                }
                
                orders.append(order)
            
            logger.info(f"Parsed {len(orders)} valid orders from Google Sheets")
            return orders
            
        except Exception as e:
            logger.error(f"Error parsing orders data: {e}")
            return []
    
    def _safe_int(self, value, default=1):
        """Safely convert value to int"""
        try:
            return int(float(str(value))) if value else default
        except (ValueError, TypeError):
            return default
    
    def get_orders_for_exhibitor(self, sheet_id: str, exhibitor_name: str) -> List[Dict]:
        """
        Get all orders for a specific exhibitor
        
        Args:
            sheet_id: Google Sheet ID
            exhibitor_name: Name of the exhibitor
            
        Returns:
            List of orders for the exhibitor
        """
        try:
            # Get raw data from main Orders sheet
            data = self.get_data(sheet_id, "Orders")
            
            if not data:
                logger.warning("No data found in Orders sheet")
                return []
            
            # Parse all orders
            all_orders = self.parse_orders_data(data)
            
            # Filter by exhibitor name (case-insensitive)
            exhibitor_orders = [
                order for order in all_orders 
                if order['exhibitor_name'].lower() == exhibitor_name.lower()
            ]
            
            logger.info(f"Found {len(exhibitor_orders)} orders for {exhibitor_name}")
            return exhibitor_orders
            
        except Exception as e:
            logger.error(f"Error getting orders for exhibitor {exhibitor_name}: {e}")
            return []
    
    def get_all_exhibitors(self, sheet_id: str) -> List[Dict]:
        """
        Get list of all exhibitors with their order counts
        
        Args:
            sheet_id: Google Sheet ID
            
        Returns:
            List of exhibitor dictionaries
        """
        try:
            data = self.get_data(sheet_id, "Orders")
            
            if not data:
                return []
            
            all_orders = self.parse_orders_data(data)
            
            # Group by exhibitor
            exhibitors = {}
            for order in all_orders:
                name = order['exhibitor_name']
                booth = order['booth_number']
                
                if name not in exhibitors:
                    exhibitors[name] = {
                        'name': name,
                        'booth': booth,
                        'total_orders': 0,
                        'delivered_orders': 0
                    }
                
                exhibitors[name]['total_orders'] += 1
                if order['status'] == 'delivered':
                    exhibitors[name]['delivered_orders'] += 1
            
            return list(exhibitors.values())
            
        except Exception as e:
            logger.error(f"Error getting exhibitors: {e}")
            return []

# Example usage and testing
def test_sheets_integration():
    """Test the Google Sheets integration"""
    
    # Initialize manager
    manager = GoogleSheetsManager()
    
    # Your sheet ID
    sheet_id = "1zaRPHP3k-K1L0z3Bi_Wk--S1Xe2erOAAVYp78h18UUI"
    
    try:
        # Test getting all exhibitors
        print("Testing exhibitors retrieval...")
        exhibitors = manager.get_all_exhibitors(sheet_id)
        print(f"Found {len(exhibitors)} exhibitors:")
        for exhibitor in exhibitors:
            print(f"  - {exhibitor['name']} (Booth {exhibitor['booth']}): {exhibitor['total_orders']} orders")
        
        # Test getting orders for specific exhibitor
        if exhibitors:
            test_exhibitor = exhibitors[0]['name']
            print(f"\nTesting orders for {test_exhibitor}...")
            orders = manager.get_orders_for_exhibitor(sheet_id, test_exhibitor)
            print(f"Found {len(orders)} orders for {test_exhibitor}")
            
            if orders:
                print("Sample order:")
                print(f"  - {orders[0]['item']} (Status: {orders[0]['status']})")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_sheets_integration()
