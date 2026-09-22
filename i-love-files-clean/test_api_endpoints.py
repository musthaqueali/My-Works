from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)

# 1. Test Convert DXF -> SVG
with open('test_artifacts/blueprint.dxf', 'rb') as f:
    res = client.post('/api/convert', files={'file': ('blueprint.dxf', f, 'application/dxf')}, data={'target_format': 'svg'})
print('Convert DXF -> SVG:', res.status_code)
assert res.status_code == 200, res.text
data = res.json()
print('Download URL:', data['download_url'])
print('Use Case:', data['use_case'])

# 2. Test Convert WAV -> MP3
with open('test_artifacts/tone.wav', 'rb') as f:
    res_wav = client.post('/api/convert', files={'file': ('tone.wav', f, 'audio/wav')}, data={'target_format': 'mp3'})
print('Convert WAV -> MP3:', res_wav.status_code)
assert res_wav.status_code == 200, res_wav.text

# 3. Test Resize PDF -> A4
with open('test_artifacts/large_doc.pdf', 'rb') as f:
    res_resize = client.post(
        '/api/resize',
        files={'file': ('large_doc.pdf', f, 'application/pdf')},
        data={'tool_type': 'pdf', 'options': json.dumps({'target_size': 'a4', 'compress_mode': 'medium'})}
    )
print('Resize PDF -> A4:', res_resize.status_code)
assert res_resize.status_code == 200, res_resize.text
print('Resize Stats:', res_resize.json()['stats'])

# 4. Test Inspect endpoint
with open('test_artifacts/blueprint.dxf', 'rb') as f:
    res_insp = client.post('/api/inspect', files={'file': ('blueprint.dxf', f, 'application/dxf')})
print('Inspect:', res_insp.status_code, res_insp.json()['category'], len(res_insp.json()['suggested_targets']))
assert res_insp.status_code == 200

print('ALL API TESTS PASSED!')
