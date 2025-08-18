from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import logging
import os
import json

# Initialize Flask app with static folder for React build
app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)  # Enable CORS for React app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SMART CACHING SYSTEM
CACHE = {}
CACHE_DURATION = 120  # 2 minutes cache
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

# Mock data functions
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
            'booth_number': '100',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'item': 'Round Table 30" high',
            'description': 'Professional exhibition furniture',
            'color': 'White',
            'quantity': 2,
            'status': 'delivered',
            'order_date': 'June 13, 2025',
            'comments': 'Coordinated by Expo Convention Contractors',
            'section': 'Section 1'
        },
        {
            'id': 'ORD-2025-003',
            'booth_number': '101',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'item': 'White Side Chair',
            'description': 'Professional seating solution',
            'color': 'White',
            'quantity': 4,
            'status': 'out-for-delivery',
            'order_date': 'June 12, 2025',
            'comments': 'High-quality event furniture',
            'section': 'Section 1'
        }
    ]

def get_mock_checklist():
    return [
        # Booth 100 items (7 completed, 4 pending = 64% complete)
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': '3m x 4m Corner Booth',
            'special_instructions': '',
            'status': True,
            'date': '01-28-25',
            'hour': '13:10:22',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': 'BeMatrix Structure with White Double Fabric Walls',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': 'Rectangular White Table',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 4,
            'name': 'White Chair',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': 'Wastebasket',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': 'Company Name Sign 24"W x 16"H',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': '500 Watt Electrical Outlet',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': '6 Track with Three Can Lights',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': 'White Shelving Unit',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': '3m x 4m Wood Vinyl Flooring',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '100',
            'section': 'Section 1',
            'exhibitor_name': 'APACKAGING GROUP, LLC',
            'quantity': 1,
            'name': '3M Fabric Graphic',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        # Booth 101 items (5 completed, 3 pending = 63% complete)
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': '3m x 8m Corner Booth',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': 'BeMatrix Structure with White Double Fabric Walls',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': 'Rectangular White Table',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 4,
            'name': 'White Chair',
            'special_instructions': '',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': 'Mini Refrigerator',
            'special_instructions': 'Color May Vary',
            'status': True,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': 'VIP Glow Bar 6 Frosted Plexi',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': 'TV Rental - 55" with Wall Mount Brackets',
            'special_instructions': '',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        },
        {
            'booth_number': '101',
            'section': 'Section 1',
            'exhibitor_name': 'Pure Beauty Labs, LLC',
            'quantity': 1,
            'name': 'Advance Shipment',
            'special_instructions': 'TO SHOW - LIFT GATE, RESIDENTIAL, INSIDE DELIVERY',
            'status': False,
            'date': '',
            'hour': '',
            'data_source': 'Mock Data'
        }
    ]

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
        return send_from_directory('frontend/build', path)
    except FileNotFoundError:
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

@app.route('/api/orders/booth/<booth_number>', methods=['GET'])
def get_orders_by_booth(booth_number):
    """Get orders for a specific booth number"""
    cache_key = f"booth_{booth_number}"
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return jsonify(cached_data)
    
    try:
        all_orders = get_mock_orders()
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

@app.route('/api/checklist/booth/<booth_number>', methods=['GET'])
def get_checklist_by_booth(booth_number):
    """Get checklist items for a specific booth number with progress calculation"""
    cache_key = f"checklist_booth_{booth_number}"
    force_refresh = request.args.get(FORCE_REFRESH_PARAM, 'false').lower() == 'true'
    
    if not force_refresh:
        cached_data = get_from_cache(cache_key, allow_cache=True)
        if cached_data:
            return jsonify(cached_data)
    
    try:
        all_checklist_items = get_mock_checklist()
        booth_items = [
            item for item in all_checklist_items 
            if str(item['booth_number']).lower() == str(booth_number).lower()
        ]
        
        if not booth_items:
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
            total_items = len(booth_items)
            completed_items = len([item for item in booth_items if item['status'] == True])
            
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

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all cached data"""
    global CACHE
    CACHE = {}
    logger.info("Cache cleared manually")
    return jsonify({'message': 'Cache cleared successfully'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
