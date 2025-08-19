from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import logging
import os
import json
import requests

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

# Your Google Sheet IDs
ORDERS_SHEET_ID = "1zaRPHP3k-K1L0z3Bi_Wk--S1Xe2erOAAVYp78h18UUI"
CHECKLIST_SHEET_ID = "1jkeob2XkPLBDgqqQqjKeQXq686EmxQhenEET8yuKvlk"

# Abacus AI Configuration for Checklist
ABACUS_API_BASE = "https://cloud.abacus.ai"
CHECKLIST_DATASET_ID = "7a88a4bc0"
CHECKLIST_FEATURE_GROUP_ID = "236a2273a"

def query_abacus_checklist(booth_number=None, force_refresh=False):
    """Query Abacus AI for checklist data"""
    try:
        # Get API key from environment
        api_key = os.environ.get('ABACUS_API_KEY')
        if not api_key:
            logger.warning("Abacus API key not found, using mock data")
            return get_mock_checklist(booth_number)
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Query the feature group using the correct Abacus AI endpoint
        endpoint = f"{ABACUS_API_BASE}/api/v0/deployments/search"
        
        # Build query based on booth number - try different approaches
        if booth_number:
            # Try exact match first
            query_data = {
                "deploymentId": CHECKLIST_FEATURE_GROUP_ID,
                "query": f"Booth # == '{booth_number}'",
                "limit": 100
            }
        else:
            query_data = {
                "deploymentId": CHECKLIST_FEATURE_GROUP_ID,
                "query": "*",
                "limit": 1000
            }
        
        logger.info(f"Querying Abacus AI with: {query_data}")
        response = requests.post(endpoint, headers=headers, json=query_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Abacus AI response: {data}")
            return parse_checklist_data(data.get('data', []), booth_number)
        else:
            logger.error(f"Abacus API error: {response.status_code} - {response.text}")
            # Try alternative endpoint
            return try_alternative_abacus_query(booth_number, headers)
            
    except Exception as e:
        logger.error(f"Error querying Abacus checklist: {e}")
        return get_mock_checklist(booth_number)

def try_alternative_abacus_query(booth_number, headers):
    """Try alternative Abacus AI query methods"""
    try:
        # Try feature group query endpoint
        endpoint = f"{ABACUS_API_BASE}/api/v0/featureGroups/{CHECKLIST_FEATURE_GROUP_ID}/query"
        
        query_data = {
            "limit": 1000
        }
        
        if booth_number:
            query_data["filters"] = [
                {
                    "column": "Booth #",
                    "operator": "==",
                    "value": str(booth_number)
                }
            ]
        
        response = requests.post(endpoint, headers=headers, json=query_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Alternative Abacus AI response: {data}")
            return parse_checklist_data(data.get('data', []), booth_number)
        else:
            logger.error(f"Alternative Abacus API error: {response.status_code} - {response.text}")
            return get_mock_checklist(booth_number)
            
    except Exception as e:
        logger.error(f"Error in alternative Abacus query: {e}")
        return get_mock_checklist(booth_number)

def parse_checklist_data(raw_data, booth_number=None):
    """Parse checklist data from Abacus AI response"""
    checklist_items = []
    
    for row in raw_data:
        try:
            # Handle different possible response formats
            if isinstance(row, dict):
                booth_num = str(row.get('Booth #', row.get('booth_number', row.get('Booth', ''))))
                
                # Filter by booth number if specified
                if booth_number and booth_num != str(booth_number):
                    continue
                
                # Handle status - could be "TRUE"/"FALSE" or True/False or "checked"/"unchecked"
                status_value = row.get('Status', False)
                if isinstance(status_value, str):
                    completed = status_value.upper() in ['TRUE', 'CHECKED', 'YES', '1']
                else:
                    completed = bool(status_value)
                
                item = {
                    'id': f"CHK-{booth_num}-{len(checklist_items) + 1}",
                    'booth_number': booth_num,
                    'section': row.get('Section', ''),
                    'exhibitor_name': row.get('Exhibitor Name', ''),
                    'quantity': int(row.get('Quantity', 0)) if row.get('Quantity') else 0,
                    'item_name': row.get('Item Name', ''),
                    'special_instructions': row.get('Special Instructions', ''),
                    'status': completed,
                    'date': row.get('Date', ''),
                    'hour': row.get('Hour', ''),
                    'completed': completed,
                    'priority': 1 if not completed else 5  # Incomplete items have higher priority
                }
                checklist_items.append(item)
        except Exception as e:
            logger.error(f"Error parsing checklist row: {row} - Error: {e}")
            continue
    
    logger.info(f"Parsed {len(checklist_items)} checklist items for booth {booth_number}")
    return checklist_items

def get_mock_checklist(booth_number=None):
    """Mock checklist data for testing"""
    mock_items = [
        {
            'id': 'CHK-100-001',
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'item_name': '3m x 4m Corner Booth',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'completed': False,
            'priority': 1
        },
        {
            'id': 'CHK-100-002',
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'item_name': 'BeMatrix Structure with White Double Fabric Walls',
            'special_instructions': '',
            'status': True,
            'date': '01-28-25',
            'hour': '10:30:00',
            'completed': True,
            'priority': 5
        },
        {
            'id': 'CHK-100-003',
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 4,
            'item_name': 'White Chair',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'completed': False,
            'priority': 1
        },
        {
            'id': 'CHK-101-001',
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'item_name': '3m x 8m Corner Booth',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'completed': False,
            'priority': 1
        }
    ]
    
    if booth_number:
        return [item for item in mock_items if item['booth_number'] == str(booth_number)]
    return mock_items

def load_checklist_from_abacus(booth_number=None, force_refresh=False):
    """Load checklist from Abacus AI with smart caching"""
    cache_key = f"checklist_{booth_number}" if booth_number else "checklist_all"
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return cached_data
    
    try:
        checklist_items = query_abacus_checklist(booth_number, force_refresh)
        
        if checklist_items:
            # Sort by priority (incomplete items first)
            checklist_items.sort(key=lambda x: x['priority'])
            set_cache(cache_key, checklist_items)
            if force_refresh:
                logger.info("🔄 FORCE REFRESH: Fresh checklist data loaded from Abacus AI")
            return checklist_items
        
        logger.warning("No checklist data found, using mock data")
        mock_data = get_mock_checklist(booth_number)
        set_cache(cache_key, mock_data)
        return mock_data
        
    except Exception as e:
        logger.error(f"Error loading checklist: {e}")
        logger.info("Falling back to mock checklist data")
        mock_data = get_mock_checklist(booth_number)
        set_cache(cache_key, mock_data)
        return mock_data

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
        data = gs_manager.get_data(ORDERS_SHEET_ID, "Orders")
        
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
        'abacus_checklist_enabled': os.environ.get('ABACUS_API_KEY') is not None,
        'cache_size': len(CACHE)
    })

@app.route('/api/abacus-status', methods=['GET'])
def abacus_status():
    """System status endpoint"""
    return jsonify({
        'platform': 'Expo Convention Contractors',
        'status': 'connected',
        'database': 'Google Sheets Integration + Abacus AI',
        'last_sync': datetime.now().isoformat(),
        'version': '3.1.0',
        'cache_enabled': True,
        'checklist_integration': 'Abacus AI Enabled'
    })

# ORDERS ENDPOINTS (Keep existing functionality)
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

# NEW CHECKLIST ENDPOINTS
@app.route('/api/checklist/booth/<booth_number>', methods=['GET'])
def get_checklist_by_booth(booth_number):
    """Get checklist items for a specific booth number"""
    cache_key = f"checklist_booth_{booth_number}"
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return jsonify(cached_data)
    
    try:
        # Get checklist items for the booth
        checklist_items = load_checklist_from_abacus(booth_number, force_refresh=force_refresh)
        
        completed_count = len([item for item in checklist_items if item['completed']])
        pending_count = len([item for item in checklist_items if not item['completed']])
        
        # Get exhibitor name from first item
        exhibitor_name = checklist_items[0]['exhibitor_name'] if checklist_items else f'Booth {booth_number} Exhibitor'
        
        result = {
            'booth': booth_number,
            'exhibitor_name': exhibitor_name,
            'checklist_items': checklist_items,
            'total_items': len(checklist_items),
            'completed_items': completed_count,
            'pending_items': pending_count,
            'completion_percentage': round((completed_count / len(checklist_items)) * 100, 1) if checklist_items else 0,
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
            'exhibitor_name': f'Booth {booth_number} Exhibitor',
            'checklist_items': [],
            'total_items': 0,
            'completed_items': 0,
            'pending_items': 0,
            'completion_percentage': 0,
            'last_updated': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/checklist', methods=['GET'])
def get_all_checklist():
    """Get all checklist items with smart caching"""
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    checklist_items = load_checklist_from_abacus(force_refresh=force_refresh)
    return jsonify(checklist_items)

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
