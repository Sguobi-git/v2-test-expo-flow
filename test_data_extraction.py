# test_data_final.py
from abacusai import ApiClient
import pandas as pd

def extract_data_multiple_ways(api_key):
    client = ApiClient(api_key)
    feature_group_id = "4d868f4c"
    dataset_id = "3dee61c66"
    
    print("🚀 Trying Multiple Data Extraction Methods...")
    
    # Method 1: Try dataset methods
    try:
        print("\n📊 Method 1: Dataset data methods...")
        dataset_methods = [method for method in dir(client) if 'dataset' in method.lower() and ('data' in method.lower() or 'pandas' in method.lower())]
        print(f"Available dataset methods: {dataset_methods}")
        
        # Try common dataset data methods
        for method in ['get_dataset_data_as_pandas', 'describe_dataset_data', 'get_dataset_data']:
            if hasattr(client, method):
                try:
                    print(f"🔄 Trying {method}...")
                    data = getattr(client, method)(dataset_id)
                    print(f"✅ SUCCESS with {method}!")
                    print(f"📊 Data type: {type(data)}")
                    if hasattr(data, 'shape'):
                        print(f"📊 Shape: {data.shape}")
                        return data, method
                except Exception as e:
                    print(f"❌ {method} failed: {e}")
    
    except Exception as e:
        print(f"❌ Dataset methods failed: {e}")
    
    # Method 2: Try export methods
    try:
        print("\n📤 Method 2: Export methods...")
        export_methods = [method for method in dir(client) if 'export' in method.lower()]
        print(f"Available export methods: {export_methods[:5]}...")  # Show first 5
        
    except Exception as e:
        print(f"❌ Export methods failed: {e}")
    
    # Method 3: Try concatenate (this was in available methods)
    try:
        print("\n🔗 Method 3: Concatenate method...")
        if hasattr(client, 'concatenate_feature_group_data'):
            # This might work if we concatenate with itself
            print("🔄 Trying concatenate_feature_group_data...")
            # This method usually needs multiple feature groups, but let's try
    
    except Exception as e:
        print(f"❌ Concatenate failed: {e}")
    
    # Method 4: Check recent streaming data
    try:
        print("\n📡 Method 4: Recent streamed data...")
        if hasattr(client, 'get_recent_feature_group_streamed_data'):
            print("🔄 Trying get_recent_feature_group_streamed_data...")
            data = client.get_recent_feature_group_streamed_data(feature_group_id)
            print(f"✅ Got streaming data: {type(data)}")
            return data, 'streaming'
    
    except Exception as e:
        print(f"❌ Streaming data failed: {e}")
    
    # Method 5: Try through raw API calls or alternative approaches
    try:
        print("\n🔍 Method 5: Raw data exploration...")
        
        # Let's see what we can get from the feature group itself
        fg = client.describe_feature_group(feature_group_id)
        print(f"📋 Feature group details:")
        print(f"   - Table name: {fg.table_name}")
        print(f"   - Dataset ID: {fg.dataset_id}")
        print(f"   - Features: {len(fg.features)}")
        
        # Try to get feature group version data
        if hasattr(fg, 'latest_feature_group_version'):
            version = fg.latest_feature_group_version
            print(f"   - Version: {version.feature_group_version}")
            print(f"   - SQL: {version.sql}")
            
    except Exception as e:
        print(f"❌ Raw exploration failed: {e}")
    
    return None, None

def try_chatllm_approach(api_key):
    """Try getting data through ChatLLM since that works in the web interface"""
    client = ApiClient(api_key)
    project_id = "16b4367d2c"  # Your ChatLLM project
    
    try:
        print("\n💬 Method 6: ChatLLM approach...")
        
        # Create chat session
        session = client.create_chat_session(project_id)
        print(f"✅ Created chat session: {session.chat_session_id}")
        
        # Ask for data in a structured format
        response = client.get_chat_response(
            session.chat_session_id,
            "Show me the first 5 rows from the Orders sheet. Format the response as a simple table with columns: Booth #, Exhibitor Name, Item, Status, Date"
        )
        
        print(f"📋 ChatLLM Response:")
        print(response.content)
        
        # Try to parse this response
        return response.content, 'chatllm'
        
    except Exception as e:
        print(f"❌ ChatLLM approach failed: {e}")
        return None, None

if __name__ == "__main__":
    api_key = "s2_440d8b6da4094a9badee296fd7e6500d"  # REPLACE WITH YOUR REAL API KEY
    
    print("🚀 COMPREHENSIVE Data Extraction Test")
    print("=" * 60)
    
    # Try all approaches
    data, method = extract_data_multiple_ways(api_key)
    
    if data is None:
        print("\n" + "=" * 60)
        chat_data, chat_method = try_chatllm_approach(api_key)
        
        if chat_data:
            print(f"\n🎉 SUCCESS with {chat_method}!")
            print("📋 We can use ChatLLM to query your data!")
        else:
            print("\n❌ All methods failed - let's try a different approach")
    else:
        print(f"\n🎉 SUCCESS with {method}!")
        
    print("\n🎯 Next: If ChatLLM works, we can build your web app integration around that!")
