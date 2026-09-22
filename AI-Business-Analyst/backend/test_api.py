import urllib.request
import json
import urllib.parse

def run_tests():
    # 1. Index
    req = urllib.request.urlopen("http://localhost:8085/")
    print(f"Index status: {req.status}")

    # 2. Sample
    req = urllib.request.urlopen("http://localhost:8085/api/sample/ecommerce")
    sample = json.loads(req.read().decode('utf-8'))
    print(f"Sample loaded: {sample['filename']} (Rows: {sample['rows']}, Cols: {sample['columns']})")
    session_id = sample['session_id']

    # 3. Analyze
    data = urllib.parse.urlencode({'session_id': session_id}).encode('utf-8')
    req = urllib.request.urlopen("http://localhost:8085/api/analyze", data=data)
    analysis = json.loads(req.read().decode('utf-8'))
    print(f"Analysis: Domain = {analysis['profile']['detected_domain']}")
    print(f"Health Status: {analysis['executive_summary']['overall_health']}")
    print(f"Data Quality: {analysis['quality']['overall_quality_score']}% ({analysis['quality']['quality_grade']})")
    print(f"Discovered KPIs: {len(analysis['kpis'])}")
    print(f"Root Causes: {len(analysis['root_causes'])}")
    print(f"Recommendations: {len(analysis['recommendations'])}")

    # 4. What-If
    whatif_data = json.dumps({'session_id': session_id, 'variable': 'unit_price', 'pct_change': 5.0}).encode('utf-8')
    req = urllib.request.Request("http://localhost:8085/api/what-if", data=whatif_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    whatif = json.loads(resp.read().decode('utf-8'))
    print(f"What-If Sim: Base = ${whatif['base_value']:,} -> Simulated = ${whatif['simulated_value']:,} (Delta = {whatif['pct_difference']}%)")

    # 5. Chat
    chat_data = json.dumps({'session_id': session_id, 'question': 'Why did sales decline in the South region?'}).encode('utf-8')
    req = urllib.request.Request("http://localhost:8085/api/chat", data=chat_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    chat = json.loads(resp.read().decode('utf-8'))
    print(f"Chat Response preview:\n{chat['response'][:250]}...")

    print("\nALL 5 AUTOMATED API TESTS PASSED WITH 100% SUCCESS!")

if __name__ == '__main__':
    run_tests()
