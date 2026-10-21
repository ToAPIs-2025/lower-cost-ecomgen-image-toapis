"""Optional server/desktop asset boundary; no keys accepted through stdin.

Presets constrain request fields. A stable caller job ID and private state keep
repeated application invocations on the original task, including after failure.
"""
from pathlib import Path
import json,os,sys,hashlib,struct,subprocess,re
from unified_client import Client,generate

def generate_asset(request):
    if set(request)-{'model','prompt','jobId','image'}:
        raise ValueError('Unsupported input field')
    model=request['model'];prompt=request['prompt'];job=request['jobId']
    if not isinstance(job,str) or not job.strip():raise ValueError('A stable caller jobId is required')
    presets=json.loads(Path(__file__).with_name('presets.json').read_text(encoding='utf-8'))
    if model not in presets:raise ValueError('Model not in reviewed presets')
    preset=presets[model];state=Path(os.environ.get('TOAPIS_STATE_DIR',str(Path(__file__).with_name('.state'))));output=Path(os.environ.get('TOAPIS_OUTPUT_DIR',str(Path(__file__).with_name('outputs'))))
    client=Client(state=state)
    if os.environ.get('TOAPIS_RESUME_ONLY')=='1':
        original=client.json
        def get_only(path,body=None,content_type='application/json'):
            if body is not None:raise ValueError('Resume-only mode blocks every POST')
            return original(path)
        client.json=get_only
    result=generate(client,preset,prompt,output,os.environ.get('TOAPIS_MAX_CASE_USD','0.80' if preset['kind']=='video' else '0.10'),True,request.get('image'),job)
    if result.get('status')!='completed':raise RuntimeError('Task ended without usable output; see private receipt')
    file=Path(result['output']);raw=file.read_bytes();media={'kind':preset['kind'],'file':str(file),'cost':result['cost']}
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        media.update(mimeType='image/png',width=struct.unpack('>I',raw[16:20])[0],height=struct.unpack('>I',raw[20:24])[0])
    elif preset['kind']=='video':
        ffmpeg=os.environ.get('FFMPEG_PATH','ffmpeg');p=subprocess.run([ffmpeg,'-hide_banner','-i',str(file),'-map','0:v:0','-f','null',os.devnull],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        if p.returncode:raise ValueError('Video decode failed')
        duration=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',p.stderr);dim=re.search(r'Video:.*?\b(\d{3,5})x(\d{3,5})\b',p.stderr)
        if not duration or not dim:raise ValueError('Video metadata missing')
        media.update(mimeType='video/mp4',width=int(dim[1]),height=int(dim[2]),durationSeconds=int(duration[1])*3600+int(duration[2])*60+float(duration[3]))
    else:raise ValueError('This adapter currently accepts PNG image results only')
    return media

if __name__=='__main__':
    try:print(json.dumps(generate_asset(json.load(sys.stdin)),ensure_ascii=False))
    except Exception as e:print(json.dumps({'error':type(e).__name__,'message':str(e)},ensure_ascii=False));sys.exit(1)
