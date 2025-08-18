@app.route('/api/checklist/booth/<booth_number>', methods=['GET'])
def get_checklist_by_booth(booth_number):
    """Get checklist items for a specific booth number with progress calculation"""
    cache_key = f"checklist_booth_{booth_number}"
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return jsonify(cached_data)
    
    try:
        # Get all checklist items and filter by booth number
        all_checklist_items = load_checklist_from_sheets(force_refresh=force_refresh)
        booth_items = [
            item for item in all_checklist_items 
            if str(item['booth_number']).lower() == str(booth_number).lower()
        ]
        
        if not booth_items:
            # Return empty result if no items found
            result = {
                'booth': booth_number,
                'exhibitor_name': f'Booth {booth_number}',
                'section': 'Unknown',
                'total_items': 0,
                'completed_items': 0,
                'items': [],
                'last_updated': datetime.now().isoformat(),
                'force_refreshed': force_refresh
            }
        else:
            # Calculate progress
            total_items = len(booth_items)
            completed_items = len([item for item in booth_items if item['status'] == True])
            
            # Get exhibitor info from first item
            exhibitor_name = booth_items[0].get('exhibitor_name', f'Booth {booth_number}')
            section = booth_items[0].get('section', 'Unknown')
            
            result = {
                'booth': booth_number,
                'exhibitor_name': exhibitor_name,
                'section': section,
                'total_items': total_items,
                'completed_items': completed_items,
                'progress_percentage': round((completed_items / total_items) * 100) if total_items > 0 else 0,
                'items': booth_items,
                'last_updated': datetime.now().isoformat(),
                'force_refreshed': force_refresh
            }
        
        set_cache(cache_key, result)
        
        if force_refresh:
            logger.info(f"🔄 MANUAL REFRESH: Fresh checklist data for booth {booth_number}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting checklist for booth {booth_number}: {e}")
        return jsonify({
            'booth': booth_number,
            'exhibitor_name': f'Booth {booth_number}',
            'section': 'Unknown',
            'total_items': 0,
            'completed_items': 0,
            'items': [],
            'last_updated': datetime.now().isoformat(),
            'error': str(e)
        }), 500

def load_checklist_from_sheets(force_refresh=False):
    """Load checklist items from Google Sheets with smart caching"""
    cache_key = "all_checklist_items"
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return cached_data
    
    try:
        if not gs_manager:
            logger.warning("No Google Sheets manager available, using mock checklist data")
            mock_data = get_mock_checklist()
            set_cache(cache_key, mock_data)
            return mock_data
            
        # Get all checklist items from Google Sheets
        # Using the new checklist sheet - you'll need to update your sheets_integration.py
        # to handle the checklist data structure
        all_items = []
        data = gs_manager.get_data(SHEET_ID, "Booth Checklist")  # Update sheet name as needed
        
        if data and len(data) > 0:
            if isinstance(data, list):
                all_items = parse_checklist_data(data)
                logger.info(f"Loaded {len(all_items)} checklist items from Google Sheets")
            
            if all_items:
                set_cache(cache_key, all_items)
                if force_refresh:
                    logger.info("🔄 FORCE REFRESH: Fresh checklist data loaded from Google Sheets")
                return all_items
        
        logger.warning("No checklist data found in Google Sheets, using mock data")
        mock_data = get_mock_checklist()
        set_cache(cache_key, mock_data)
        return mock_data
        
    except Exception as e:
        logger.error(f"Error loading checklist from sheets: {e}")
        logger.info("Falling back to mock checklist data")
        mock_data = get_mock_checklist()
        set_cache(cache_key, mock_data)
        return mock_data

def parse_checklist_data(data):
    """Parse checklist data from Google Sheets"""
    items = []
    
    try:
        if not data or len(data) < 2:
            return []
        
        # Find header row
        header_row_idx = 0
        headers = []
        
        for i, row in enumerate(data):
            if any('Booth' in str(cell) for cell in row):
                headers = [str(cell).strip() for cell in row]
                header_row_idx = i
                break
        
        if not headers:
            headers = [str(cell).strip() for cell in data[0]]
            header_row_idx = 0
        
        logger.info(f"Using checklist headers: {headers}")
        
        # Process data rows
        for row_idx, row in enumerate(data[header_row_idx + 1:], start=header_row_idx + 1):
            if not row or len(row) == 0:
                continue
            
            # Create dictionary from row data
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    row_dict[headers[i]] = str(value).strip()
            
            # Extract checklist item data
            booth_num = row_dict.get('Booth #', '').strip()
            if not booth_num or booth_num == '0':  # Skip invalid booth numbers
                continue
                
            exhibitor_name = row_dict.get('Exhibitor Name', '').strip()
            item_name = row_dict.get('Item Name', '').strip()
            
            if not exhibitor_name or not item_name:
                continue
            
            # Parse status (TRUE/FALSE to boolean)
            status_str = row_dict.get('Status', 'FALSE').strip().upper()
            status = status_str == 'TRUE'
            
            # Build checklist item dictionary
            item = {
                'booth_number': booth_num,
                'section': row_dict.get('Section', '').strip(),
                'exhibitor_name': exhibitor_name,
                'quantity': safe_int(row_dict.get('Quantity', '1')),
                'name': item_name,
                'special_instructions': row_dict.get('Special Instructions', '').strip(),
                'status': status,
                'date': row_dict.get('Date', '').strip(),
                'hour': row_dict.get('Hour', '').strip(),
                'data_source': 'Google Sheets Checklist'
            }
            
            items.append(item)
        
        logger.info(f"Parsed {len(items)} valid checklist items from Google Sheets")
        return items
        
    except Exception as e:
        logger.error(f"Error parsing checklist data: {e}")
        return []

def safe_int(value, default=1):
    """Safely convert value to int"""
    try:
        return int(float(str(value))) if value else default
    except (ValueError, TypeError):
        return default

def get_mock_checklist():
    """Mock checklist data for testing"""
    return [
        # Booth 100 items
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 4, 'name': 'White Chair', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': 'Wastebasket', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': 'Company Name Sign 24"W x 16"H', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': '500 Watt Electrical Outlet', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': '6\' Track with Three Can Lights', 'special_instructions': '', 'status': False, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': 'White Shelving Unit', 'special_instructions': '', 'status': False, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': '3m x 4m Wood Vinyl Flooring', 'special_instructions': '', 'status': False, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': '3M Fabric Graphic - 117.17"W x 95.20"H', 'special_instructions': '', 'status': False, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        
        # Booth 101 items
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 1, 'name': '3m x 8m Corner Booth', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 1, 'name': 'BeMatrix Structure with White Double Fabric Walls', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 1, 'name': 'Rectangular White Table', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 4, 'name': 'White Chair', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 1, 'name': 'Mini Refrigerator - Color May Vary', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 1, 'name': 'VIP Glow Bar 6\' Frosted Plexi', 'special_instructions': '', 'status': False, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '101', 'section': 'Section 1', 'exhibitor_name': 'Pure Beauty Labs, LLC', 'quantity': 1, 'name': 'TV Rental - 55" with Wall Mount Brackets', 'special_instructions': '', 'status': False, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': 'BeMatrix Structure with White Double Fabric Walls', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
        {'booth_number': '100', 'section': 'Section 1', 'exhibitor_name': 'APACKAGING GROUP, LLC', 'quantity': 1, 'name': 'Rectangular White Table', 'special_instructions': '', 'status': True, 'date': '', 'hour': '', 'data_source': 'Mock Data'},
    ]
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import logging
import os
import json

# Import the Google Sheets manager (from your existing code)
try:
    from sheets_integration import GoogleSheetsManager
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("⚠️ Google Sheets integration not available")

# Initialize Flask app with static folder for React build
app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)  # Enable CORS for React app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SMART CACHING SYSTEM - Allows manual refresh override
CACHE = {}
CACHE_DURATION = 120  # 2 minutes cache for auto-refresh
FORCE_REFRESH_PARAM = 'force_refresh'

def get_from_cache(key, allow_cache=True):
    if not allow_cache:
        logger.info(f"Cache bypassed for {key} (manual refresh)")
        return None
        
    if key in CACHE:
        data, timestamp = CACHE[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_DURATION):
            logger.info(f"Using cached data for {key}")
            return data
    return None

def set_cache(key, data):
    CACHE[key] = (data, datetime.now())
    logger.info(f"Cached data for {key}")

# Initialize Google Sheets Manager
def get_credentials():
    """Get Google credentials from environment variable or file"""
    try:
        # Try to get credentials from environment variable first
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if credentials_json:
            # Parse the JSON string and create a temporary file
            credentials_dict = json.loads(credentials_json)
            
            # Create temporary credentials file
            with open('/tmp/credentials.json', 'w') as f:
                json.dump(credentials_dict, f)
            return '/tmp/credentials.json'
        else:
            # Fallback to local file (for development)
            return 'credentials.json'
    except Exception as e:
        logger.error(f"Error setting up credentials: {e}")
        return None

# Initialize Google Sheets Manager
if SHEETS_AVAILABLE:
    credentials_path = get_credentials()
    if credentials_path:
        gs_manager = GoogleSheetsManager(credentials_path)
    else:
        gs_manager = None
        logger.warning("No valid credentials found - using mock data only")
else:
    gs_manager = None
    logger.warning("Google Sheets integration not available - using mock data only")

# Your Google Sheet ID
SHEET_ID = "1zaRPHP3k-K1L0z3Bi_Wk--S1Xe2erOAAVYp78h18UUI"

# Mock data for testing
def get_mock_orders():
    return [
        {
            'id': 'ORD-2025-001',
            'booth_number': 'A-245',
            'exhibitor_name': 'TechFlow Innovations',
            'item': 'Premium Booth Setup Package',
            'description': 'Complete booth installation with premium furniture, lighting, and tech setup',
            'color': 'White',
            'quantity': 1,
            'status': 'out-for-delivery',
            'order_date': 'June 14, 2025',
            'comments': 'Rush delivery requested',
            'section': 'Section A'
        },
        {
            'id': 'ORD-2025-002',
            'booth_number': 'A-245',
            'exhibitor_name': 'TechFlow Innovations',
            'item': 'Interactive Display System',
            'description': '75" 4K touchscreen display with interactive software and mounting',
            'color': 'Black',
            'quantity': 1,
            'status': 'in-route',
            'order_date': 'June 13, 2025',
            'comments': '',
            'section': 'Section A'
        },
        {
            'id': 'ORD-2025-003',
            'booth_number': 'B-156',
            'exhibitor_name': 'GreenWave Energy',
            'item': 'Marketing Materials Bundle',
            'description': 'Banners, brochures, business cards, and promotional items',
            'color': 'Green',
            'quantity': 5,
            'status': 'delivered',
            'order_date': 'June 12, 2025',
            'comments': 'Eco-friendly materials requested',
            'section': 'Section B'
        },
        {
            'id': 'ORD-2025-004',
            'booth_number': 'C-089',
            'exhibitor_name': 'SmartHealth Corp',
            'item': 'Audio-Visual Equipment',
            'description': 'Professional sound system, microphones, and presentation equipment',
            'color': 'White',
            'quantity': 1,
            'status': 'in-process',
            'order_date': 'June 14, 2025',
            'comments': 'Medical grade equipment required',
            'section': 'Section C'
        }
    ]

def load_orders_from_sheets(force_refresh=False):
    """Load orders from Google Sheets with smart caching"""
    cache_key = "all_orders"
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return cached_data
    
    try:
        if not gs_manager:
            logger.warning("No Google Sheets manager available, using mock data")
            mock_data = get_mock_orders()
            set_cache(cache_key, mock_data)
            return mock_data
            
        # Get all orders from Google Sheets
        all_orders = []
        data = gs_manager.get_data(SHEET_ID, "Orders")
        
        if data and len(data) > 0:
            if isinstance(data, list):
                all_orders = gs_manager.parse_orders_data(data)
                logger.info(f"Loaded {len(all_orders)} orders from Google Sheets")
            
            if all_orders:
                set_cache(cache_key, all_orders)
                if force_refresh:
                    logger.info("🔄 FORCE REFRESH: Fresh data loaded from Google Sheets")
                return all_orders
        
        logger.warning("No data found in Google Sheets, using mock data")
        mock_data = get_mock_orders()
        set_cache(cache_key, mock_data)
        return mock_data
        
    except Exception as e:
        logger.error(f"Error loading orders from sheets: {e}")
        logger.info("Falling back to mock data")
        mock_data = get_mock_orders()
        set_cache(cache_key, mock_data)
        return mock_data

# REACT APP SERVING ROUTES
@app.route('/')
def serve_react_app():
    """Serve the React app"""
    try:
        return send_file('frontend/build/index.html')
    except FileNotFoundError:
        return "Frontend not built. Please run 'npm run build' in frontend directory.", 404

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files or React app for client-side routing"""
    try:
        # Try to serve static file first
        return send_from_directory('frontend/build', path)
    except FileNotFoundError:
        # If file not found, serve React app (for client-side routing)
        try:
            return send_file('frontend/build/index.html')
        except FileNotFoundError:
            return "Frontend not built. Please run 'npm run build' in frontend directory.", 404

# API ROUTES
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'google_sheets_connected': gs_manager is not None,
        'cache_size': len(CACHE)
    })

@app.route('/api/abacus-status', methods=['GET'])
def abacus_status():
    """System status endpoint"""
    return jsonify({
        'platform': 'Expo Convention Contractors',
        'status': 'connected',
        'database': 'Google Sheets Integration',
        'last_sync': datetime.now().isoformat(),
        'version': '3.0.0',
        'cache_enabled': True
    })

@app.route('/api/checklist', methods=['GET'])
def get_all_checklist_items():
    """Get all checklist items with smart caching"""
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    items = load_checklist_from_sheets(force_refresh=force_refresh)
    return jsonify(items)

@app.route('/api/orders/booth/<booth_number>', methods=['GET'])
def get_orders_by_booth(booth_number):
    """Get orders for a specific booth number with smart caching"""
    cache_key = f"booth_{booth_number}"
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return jsonify(cached_data)
    
    try:
        # Get all orders and filter by booth number
        all_orders = load_orders_from_sheets(force_refresh=force_refresh)
        booth_orders = [
            order for order in all_orders 
            if order['booth_number'].lower() == booth_number.lower()
        ]
        
        delivered_count = len([o for o in booth_orders if o['status'] == 'delivered'])
        
        result = {
            'booth': booth_number,
            'orders': booth_orders,
            'total_orders': len(booth_orders),
            'delivered_orders': delivered_count,
            'last_updated': datetime.now().isoformat(),
            'force_refreshed': force_refresh
        }
        
        set_cache(cache_key, result)
        
        if force_refresh:
            logger.info(f"🔄 MANUAL REFRESH: Fresh data for booth {booth_number}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting orders for booth {booth_number}: {e}")
        return jsonify({
            'booth': booth_number,
            'orders': [],
            'total_orders': 0,
            'delivered_orders': 0,
            'last_updated': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    """Get all orders with smart caching"""
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    orders = load_orders_from_sheets(force_refresh=force_refresh)
    return jsonify(orders)

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all cached data - useful for forcing fresh data"""
    global CACHE
    CACHE = {}
    logger.info("🗑️ Cache cleared manually")
    return jsonify({'message': 'Cache cleared successfully'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
