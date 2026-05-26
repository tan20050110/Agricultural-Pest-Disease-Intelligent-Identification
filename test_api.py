import requests

print("Testing Detection API...")
print("=" * 60)

try:
    # 测试检测API
    img_path = "frontend/src/assets/images/bus.jpg"
    with open(img_path, 'rb') as f:
        resp = requests.post(
            'http://localhost:8000/api/detection/single',
            files={'file': f},
            data={'model_name': 'yolo11n.pt'}
        )

    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', 'N/A')}")

    if result.get('data'):
        data = result['data']
        print(f"Detection ID: {data.get('detection_id', 'N/A')}")
        print(f"Total Objects: {data.get('total_objects', 0)}")
        print(f"Detection Time: {data.get('detection_time', 0):.3f}s")
        print(f"Model: {data.get('model_name', 'N/A')}")
        print(f"Boxes Count: {len(data.get('boxes', []))}")
    else:
        print(f"Error Detail: {result.get('detail', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ Detection API Test Complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
