c = open('/app/transcribe_backends.py').read()
if '_transcribe_with_openai' not in c:
    patch = '''

def _transcribe_with_openai(media_path):
    import openai, os, tempfile, subprocess
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as t:
        tmp = t.name
    subprocess.run(["ffmpeg","-y","-i",media_path,"-ar","16000","-ac","1","-b:a","32k",tmp], capture_output=True)
    with open(tmp, "rb") as f:
        r = client.audio.transcriptions.create(model="whisper-1", file=f,
            response_format="verbose_json", timestamp_granularities=["word","segment"])
    os.unlink(tmp)
    segs = []
    for s in (r.segments or []):
        words = [{"word":w.word,"start":w.start,"end":w.end,"probability":0.9} for w in (getattr(s,"words",None) or [])]
        segs.append({"start":s.start,"end":s.end,"text":s.text,"words":words})
    return {"language":getattr(r,"language","id"),"segments":segs}
'''
    old = '    return _transcribe_with_whisper(media_path)'
    new = '    if backend == "openai":\n        return _transcribe_with_openai(media_path)\n    return _transcribe_with_whisper(media_path)'
    c = c.replace(old, new, 1) + patch
    open('/app/transcribe_backends.py', 'w').write(c)
    print("PATCH OK")
else:
    print("Already patched")
