import requests
import json

# Test the upload endpoint
def test_upload():
    url = "http://127.0.0.1:8000/api/upload"
    
    # Create a simple test PDF content (just text for testing)
    test_content = b"""
    %PDF-1.4
    Test Invoice Content
    Invoice Number: TEST-001
    Total Amount: $100.00
    """
    
    # Prepare the file upload
    files = {
        'file': ('test_invoice.pdf', test_content, 'application/pdf')
    }
    
    try:
        print("Testing upload endpoint...")
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Upload failed!")
            try:
                error_detail = response.json()
                print(f"Error Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_upload()