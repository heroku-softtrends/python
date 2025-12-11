import requests

try:
    print('🧪 Testing AI-powered upload...')
    files = {'file': ('test_invoice.pdf', b'Sample PDF content', 'application/pdf')}
    response = requests.post('http://127.0.0.1:8000/api/upload', files=files, timeout=30)
    
    print(f'📊 Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print('🎉 SUCCESS! AI extraction worked!')
        print(f'📄 Invoice ID: {data["invoice_id"]}')
        print(f'📋 Status: {data["status"]}')
        print(f'🔍 Fields extracted: {len(data["extracted_fields"])}')
        
        print('\n📈 AI-extracted fields:')
        for field in data["extracted_fields"]:
            name = field["field_name"]
            value = field["field_value"] 
            confidence = field["confidence_score"]
            selected = field["is_selected"]
            print(f'  • {name}: {value} (confidence: {confidence:.3f})')
            
    else:
        print('❌ ERROR:', response.text)
        
except Exception as e:
    print(f'💥 Error: {e}')