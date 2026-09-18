c = open('/app/transcribe_backends.py').read()

patch = '''

def _transcribe_with_openai(media_path):
    import os, tempfile, subprocess
    from openai import OpenAI
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = "https://api.groq.com/openai/v1" if os.environ.get("GROQ_API_KEY") else None
    client = OpenAI(api_key=api_key, base_url=base_url)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as t:
        tmp = t.name
    subprocess.run(["ffmpeg","-y","-i",media_path,"-ar","16000","-ac","1","-b:a","32k",tmp], capture_output=True)
    with open(tmp, "rb") as f:
        model = "whisper-large-v3-turbo" if os.environ.get("GROQ_API_KEY") else "whisper-1"
        r = client.audio.transcriptions.create(model=model, file=f, response_format="verbose_json")
    os.unlink(tmp)
    segs = []
    for s in (r.segments or []):
        words = [{"word":w.word,"start":w.start,"end":w.end,"probability":0.9} for w in (getattr(s,"words",None) or [])]
        segs.append({"start":s.start,"end":s.end,"text":s.text,"words":words})
    return {"language":getattr(r,"language","id"),"segments":segs}
'''

old = '    return _transcribe_with_whisper(media_path)'
new = '    if backend == "openai":\n        return _transcribe_with_openai(media_path)\n    return _transcribe_with_whisper(media_path)'

if '_transcribe_with_openai' in c:
    import re
    c = re.sub(r'\ndef _transcribe_with_openai.*', '', c, flags=re.DOTALL)
    c = c.replace(new, old)

c = c.replace(old, new, 1) + patch
open('/app/transcribe_backends.py', 'w').write(c)
print("PATCH OK - Groq")
