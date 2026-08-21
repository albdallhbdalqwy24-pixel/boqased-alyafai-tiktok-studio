#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VideoFX Studio V2 - واجهة محلية لمعالجة وفحص الفيديو باستخدام FFmpeg.

يتطلب: python و ffmpeg و ffprobe. لا يعتمد على خدمة خارجية ولا يرفع الملفات إلى الإنترنت.
"""
import json
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8765"))
BASE = Path.cwd() / "VideoFX_Studio_Files"
BASE.mkdir(parents=True, exist_ok=True)
jobs = {}

HTML = r'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>بوقاصد اليافعي — TikTok Studio</title>
<style>
:root{--bg:#050505;--panel:#0b0b0c;--line:#252527;--muted:#8c8c92;--text:#f5f5f5;--lime:#d9ff63;--blue:#9ce8ff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);position:relative;overflow-x:hidden;color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial;letter-spacing:-.01em}body:before,body:after{content:'';position:fixed;width:340px;height:340px;border-radius:50%;filter:blur(90px);opacity:.10;pointer-events:none;z-index:-1;animation:orb 12s ease-in-out infinite alternate}body:before{background:#d9ff63;top:8%;right:-180px}body:after{background:#a7e9ff;bottom:2%;left:-190px;animation-delay:-5s}@keyframes orb{from{transform:translate3d(0,0,0) scale(.8)}to{transform:translate3d(-30px,25px,0) scale(1.15)}}@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}@keyframes pulseGlow{0%,100%{box-shadow:0 0 0 rgba(217,255,99,0)}50%{box-shadow:0 0 32px rgba(217,255,99,.16)}}.shell{max-width:1160px;margin:auto;padding:24px 26px 80px}.nav{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding:2px 0 22px}.brand{font-weight:900;font-size:19px;letter-spacing:-.04em}.brand i{display:inline-block;width:8px;height:8px;background:var(--lime);border-radius:50%;margin-left:7px}.navtag{font-size:11px;color:var(--muted);letter-spacing:.12em;text-transform:uppercase}.hero{text-align:center;padding:78px 0 58px;max-width:850px;margin:auto}.eyebrow{color:var(--lime);font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}.hero h1{font-size:clamp(42px,8vw,92px);line-height:.94;letter-spacing:-.08em;margin:18px 0 22px;font-weight:950}.hero h1 span{color:var(--muted)}.hero p{color:#aaaab0;font-size:16px;line-height:1.7;max-width:560px;margin:auto}.hero .cta{display:inline-flex;align-items:center;gap:12px;margin-top:29px;padding:15px 24px;border-radius:999px;background:var(--lime);color:#0b0b0b;border:0;font-weight:900;cursor:pointer}.arrow{font-size:18px}.signal{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:0 0 58px}.signal article{background:var(--panel);padding:22px;animation:rise .7s both}.signal article:nth-child(2){animation-delay:.12s}.signal article:nth-child(3){animation-delay:.24s}.num{font-size:11px;color:var(--lime);font-weight:800;letter-spacing:.12em}.signal h3{margin:18px 0 7px;font-size:17px}.signal p{margin:0;color:var(--muted);font-size:12px;line-height:1.6}.work{display:grid;grid-template-columns:1.1fr .9fr;gap:28px;align-items:start}.section-title{font-size:12px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:15px}.upload{border:1px dashed #55555b;min-height:330px;display:flex;align-items:center;justify-content:center;text-align:center;background:radial-gradient(circle at 50% 25%,#151518 0,#09090a 60%);cursor:pointer;position:relative}.upload:hover{border-color:var(--lime)}.upload input{display:none}.upload-icon{font-size:42px;color:var(--lime);font-weight:200}.upload h2{font-size:24px;margin:17px 0 8px;letter-spacing:-.05em}.upload p{color:var(--muted);font-size:12px;margin:0}.file-name{color:var(--blue);font-size:12px;margin-top:18px;min-height:18px}.side{border:1px solid var(--line);background:var(--panel);padding:20px}.side h2{margin:0;font-size:20px;letter-spacing:-.04em}.side .desc{color:var(--muted);font-size:12px;line-height:1.7;margin:8px 0 18px}.info{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);border:1px solid var(--line);margin-top:14px}.info div{background:#111113;padding:11px}.k{color:#707077;font-size:10px;text-transform:uppercase;letter-spacing:.1em}.v{font-size:13px;font-weight:800;margin-top:5px;word-break:break-word}.method-list{display:grid;gap:10px;margin-top:15px}.method-card{position:relative;animation:rise .65s both;border:1px solid #29292d;background:#0d0d0f;padding:18px 17px 16px;border-radius:12px;cursor:pointer;transition:.2s}.method-card:hover{border-color:#78782a}.method-card.selected{border:2px solid #d9ff63;background:linear-gradient(135deg,#17170e,#0d0d0f)}.method-card.recommended{animation:pulseGlow 3s ease-in-out infinite}.method-card.recommended:before{content:'RECOMMENDED — START HERE';position:absolute;top:-11px;right:16px;background:#d9ff63;color:#12120a;padding:4px 10px;border-radius:999px;font-size:9px;font-weight:950;letter-spacing:.08em}.method-top{display:flex;gap:12px;align-items:flex-start}.radio{width:20px;height:20px;border:1px solid #777;border-radius:50%;flex:none;margin-top:2px}.selected .radio{border:6px solid #d9ff63}.method-card h3{margin:0;font-size:17px}.method-card p{margin:7px 0 0 32px;color:#9b9ba2;font-size:11px;line-height:1.7}.method-help{display:inline-block;margin:13px 0 0 32px;border:1px solid #6d631d;color:#e7d657;border-radius:999px;padding:7px 12px;font-size:10px}.control{margin-top:14px}.control label{display:block;color:#88888f;font-size:11px;margin-bottom:6px}.control select,.control input[type=url]{width:100%;padding:12px;background:#161619;border:1px solid #333338;color:#fff;border-radius:2px;font-size:13px}.row{display:grid;grid-template-columns:1fr 1fr;gap:9px}.btn{width:100%;padding:14px;border:0;border-radius:2px;background:var(--lime);color:#0a0a0a;font-weight:900;font-size:14px;cursor:pointer;margin-top:15px}.btn.dark{background:#222225;color:#fff}.btn:disabled{opacity:.4;cursor:not-allowed}.note{font-size:11px;line-height:1.7;color:#8f8f96;border-top:1px solid var(--line);padding-top:13px;margin-top:17px}.progress{height:3px;background:#27272a;margin-top:17px}.bar{height:100%;background:var(--lime);width:0;transition:width .25s}.status{font-size:12px;color:#a5a5ac;min-height:19px;margin-top:10px}.ok{color:var(--lime)}.err{color:#ff8787}.result{margin-top:12px}.download{display:block;text-align:center;text-decoration:none;background:var(--blue);color:#061015;padding:13px;font-weight:900;font-size:13px}.below{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:72px;border-top:1px solid var(--line);padding-top:27px}.below h3{font-size:13px;margin:0 0 8px}.below p{font-size:12px;color:var(--muted);line-height:1.7;margin:0}.footer{display:flex;justify-content:space-between;color:#606066;font-size:10px;margin-top:70px;border-top:1px solid var(--line);padding-top:18px}@media(max-width:760px){.shell{padding:18px 15px 50px}.hero{padding:56px 0 42px}.signal,.work,.below{grid-template-columns:1fr}.signal{gap:1px}.upload{min-height:260px}.hero h1{font-size:55px}.navtag{display:none}}
</style></head><body><main class="shell">
<header class="nav"><div class="brand"><i></i>بوقاصد اليافعي</div><div class="navtag">01 / TikTok Studio</div></header>
<section class="hero"><div class="eyebrow">بوقاصد اليافعي / TikTok Studio</div><h1>Keep your edit<br><span>closer to the source.</span></h1><p>جهّز فيديوهاتك للنشر بجودة عالية جداً، مع الحفاظ على الحركة والتوقيت وبيانات الملف بالطريقة المناسبة لـTikTok.</p><button class="cta" onclick="document.getElementById('file').click()">ابدأ من ملفك <span class="arrow">↙</span></button></section>
<section class="signal"><article><div class="num">01 — THE UPLOAD</div><h3>ارفع الملف الأصلي</h3><p>لا نضغط الفيديو عشوائياً ولا نضيف فلاتر قبل اختيارك.</p></article><article><div class="num">02 — TARGET SIGNAL</div><h3>Better motion</h3><p>نحافظ على FPS المصدر ونجهز التوقيت بالشكل المناسب لرفع TikTok.</p></article><article><div class="num">03 — MAX QUALITY</div><h3>Closer to the source</h3><p>فحص فعلي للدقة والـCodec والـBitrate والمدة قبل التنزيل.</p></article></section>
<section class="work"><div><div class="section-title">01 — Upload your edit</div><label class="upload" for="file"><input id="file" type="file" accept="video/*,.mp4,.mov,.mkv,.webm"><div><div class="upload-icon">＋</div><h2>اسحب الفيديو هنا</h2><p>أو اضغط لاختيار ملف من جهازك</p><div class="file-name" id="picked">لم يتم اختيار ملف</div></div></label><div class="small note">ملفاتك تعالج محلياً على جهازك. رابط TikTok اختياري للتوثيق فقط؛ الملف المحفوظ هو الأدق للفحص.</div></div>
<div class="side"><h2>Final delivery</h2><p class="desc">اختر طريقة التصدير. الوضع السريع يحافظ على بيانات الإطارات ويجهز الملف لـTikTok دون إعادة ترميز. تحذير: TikTok High Quality يعيد ترميز 4K/60 وقد يستغرق وقتاً طويلاً على الهاتف.</p><div class="info" id="info" style="display:none"><div><div class="k">Resolution</div><div class="v" id="res">-</div></div><div><div class="k">FPS</div><div class="v" id="fps">-</div></div><div><div class="k">Codec</div><div class="v" id="codec">-</div></div><div><div class="k">Bitrate</div><div class="v" id="bitrate">-</div></div><div><div class="k">Duration</div><div class="v" id="dur">-</div></div><div><div class="k">Size</div><div class="v" id="size">-</div></div></div>
<div class="section-title" style="margin-top:18px">02 — Choose a method</div><input id="mode" type="hidden" value="multiplier"><div class="method-list"><div class="method-card recommended selected" data-mode="multiplier" onclick="chooseMethod('multiplier',this)"><div class="method-top"><span class="radio"></span><div><h3>الخيار الأنسب لـTikTok</h3></div></div><p>الطريقة التي أثبتت نجاحها مع TikTok: تحافظ على المصدر وتجهز توقيت الملف للنشر بدون ضغط أو إعادة ترميز ثقيلة.</p><span class="method-help">شاهد الشرح التعليمي ▸</span></div><div class="method-card" data-mode="fps" onclick="chooseMethod('fps',this)"><div class="method-top"><span class="radio"></span><div><h3>الخيار الاحترافي — 1080p60</h3></div></div><p>يعيد تجهيز الفيديو إلى 1080p و60 FPS بجودة عالية. مناسب عندما تريد نسخة طبيعية قبل النشر، لكنه أبطأ مع ملفات 4K.</p><span class="method-help">شاهد الشرح التعليمي ▸</span></div></div><div class="row"><div class="control"><label>الملف النهائي</label><select id="tiktok"><option value="off">أبعاد المصدر</option><option value="1080">TikTok 1080p بلا تكبير</option></select></div><div class="control"><label>Codec</label><select id="codecSelect"><option value="h264">H.264 — أعلى توافق</option><option value="hevc">HEVC — حجم أقل</option></select></div></div><div class="control"><label>رابط TikTok اختياري</label><input id="tiktokUrl" type="url" placeholder="https://www.tiktok.com/@user/video/..."/></div><button id="process" class="btn" disabled onclick="start()">تجهيز الفيديو لـTikTok</button><button id="inspect" class="btn dark" disabled onclick="inspectSaved()">فحص الملف المحفوظ</button><div class="progress"><div class="bar" id="bar"></div></div><div class="status" id="status">اختر ملفاً للبدء.</div><div class="result" id="result"></div></div></section>
<section class="below"><div><h3>Sharper. Smoother. Closer to the source.</h3><p>الهدف ليس تكبير الرقم، بل منع فقدان التفاصيل والحركة عندما ينتقل الفيديو إلى TikTok.</p></div><div><h3>ملاحظة عن العرض قبل النشر</h3><p>وضع TikTok High Quality قد يجعل الملف يبدو أبطأ خارج TikTok عند استخدام توقيت الرفع الخاص به؛ بعد النشر يعيد TikTok قراءة التوقيت بالشكل الطبيعي.</p></div></section>
<footer class="footer"><span>بوقاصد اليافعي / TikTok Studio</span><span>Built for creator workflows</span></footer></main>
<script>
let selected=null,meta=null,job=null;const fileEl=document.getElementById('file');const $=id=>document.getElementById(id);
fileEl.onchange=async()=>{selected=fileEl.files[0];if(!selected)return;$('picked').textContent=selected.name;status('','جاري تحليل الملف...');const fd=new FormData();fd.append('file',selected);const r=await fetch('/probe',{method:'POST',body:fd});const d=await r.json();if(!d.ok){status('err',d.error);return}meta=d;showInfo(d,selected.size);$('info').style.display='grid';$('process').disabled=false;$('inspect').disabled=false;status('ok','تم التحليل. الملف جاهز للتصدير.');};
function showInfo(d,size){$('res').textContent=d.width+' × '+d.height;$('fps').textContent=d.fps+' FPS';$('codec').textContent=d.codec.toUpperCase();$('bitrate').textContent=d.bitrate_mbps+' Mbps';$('dur').textContent=d.duration;$('size').textContent=fmt(size||d.size_bytes)}function fmt(n){let u=['B','KB','MB','GB'],i=0;while(n>=1024&&i<3){n/=1024;i++}return n.toFixed(i?1:0)+' '+u[i]}function status(c,m){$('status').className='status '+(c||'');$('status').textContent=m}
function chooseMethod(value,card){$('mode').value=value;document.querySelectorAll('.method-card').forEach(x=>x.classList.remove('selected'));card.classList.add('selected')}
async function start(){if(!selected)return;$('process').disabled=true;$('result').innerHTML='';$('bar').style.width='0%';status('','جاري تجهيز الملف...');let fd=new FormData();fd.append('file',selected);fd.append('mode',$('mode').value);fd.append('fps','auto');fd.append('profile','standard');fd.append('tiktok',$('tiktok').value);fd.append('codec',$('codecSelect').value);let r=await fetch('/start',{method:'POST',body:fd}),d=await r.json();if(!d.ok){status('err',d.error);$('process').disabled=false;return}job=d.job;poll()}
async function poll(){let r=await fetch('/progress?id='+encodeURIComponent(job)),d=await r.json();$('bar').style.width=(d.progress||0)+'%';status('',d.message||'جارٍ العمل...');if(d.state==='done'){$('bar').style.width='100%';status('ok','اكتمل التصدير والفحص.');$('result').innerHTML='<a class="download" href="/download?id='+encodeURIComponent(job)+'">تنزيل النسخة النهائية</a><div class="info" style="display:grid">'+report(d.info)+'</div>';$('process').disabled=false;return}if(d.state==='error'){status('err',d.message||'حدث خطأ');$('process').disabled=false;return}setTimeout(poll,700)}function report(x){return '<div><div class="k">Resolution</div><div class="v">'+x.width+' × '+x.height+'</div></div><div><div class="k">FPS</div><div class="v">'+x.fps+'</div></div><div><div class="k">Codec</div><div class="v">'+x.codec.toUpperCase()+'</div></div><div><div class="k">Bitrate</div><div class="v">'+x.bitrate_mbps+' Mbps</div></div><div><div class="k">Size</div><div class="v">'+fmt(x.size_bytes)+'</div></div><div><div class="k">Duration</div><div class="v">'+x.duration+'</div></div>'}async function inspectSaved(){if(!selected)return;status('','جاري الفحص...');let fd=new FormData();fd.append('file',selected);let r=await fetch('/probe',{method:'POST',body:fd}),d=await r.json();if(!d.ok){status('err',d.error);return}showInfo(d,selected.size);status('ok','الفحص مكتمل.')} 
</script></body></html>'''

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
def parse_rate(x):
    if not x or x in ('0/0','N/A'): return 0.0
    try:
        a,b=x.split('/'); return float(a)/float(b)
    except Exception: return 0.0

def format_duration(sec): return time.strftime('%H:%M:%S', time.gmtime(max(0, sec)))
def mbps(bits): return round(float(bits or 0)/1_000_000, 2)

def detect_profile(path, m):
    name=Path(path).name.lower()
    if any(k in name for k in ('game','gaming','gameplay','ps5','xbox','valorant','fortnite','pubg','cod')) or m['fps']>=50:
        return 'gaming', 'Gaming'
    if any(k in name for k in ('nature','forest','mountain','sea','ocean','lake','wildlife','nature')):
        return 'nature', 'Nature'
    return 'standard', 'Standard'

def probe(path):
    cmd=['ffprobe','-v','error','-show_entries','stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,duration,bit_rate:stream_tags=rotate:format=duration,size,bit_rate','-of','json',str(path)]
    p=run(cmd)
    if p.returncode!=0: raise RuntimeError(p.stderr.strip() or 'تعذر قراءة الفيديو')
    data=json.loads(p.stdout); streams=data.get('streams',[]); vs=next((s for s in streams if s.get('codec_type')=='video'),None)
    if not vs: raise RuntimeError('الملف لا يحتوي على مسار فيديو صالح')
    fmt=data.get('format',{}); dur=float(vs.get('duration') or fmt.get('duration') or 0); size=int(fmt.get('size') or Path(path).stat().st_size)
    rate=vs.get('bit_rate') or fmt.get('bit_rate') or 0
    raw_width=int(vs.get('width') or 0); raw_height=int(vs.get('height') or 0)
    try: rotation=int(float((vs.get('tags') or {}).get('rotate') or 0)) % 360
    except Exception: rotation=0
    display_width, display_height = (raw_height, raw_width) if rotation in (90,270) else (raw_width, raw_height)
    m={'width':display_width,'height':display_height,'raw_width':raw_width,'raw_height':raw_height,'rotation':rotation,'fps':round(parse_rate(vs.get('avg_frame_rate')) or parse_rate(vs.get('r_frame_rate')),3),'duration_sec':dur,'duration':format_duration(dur),'codec':vs.get('codec_name','?'),'bitrate_mbps':mbps(rate),'size_bytes':size}
    m['detected_profile'],m['detected_profile_label']=detect_profile(path,m); return m

def bitrate_for(w,h,fps,profile,codec):
    px=w*h
    if px>=3840*2160: base=45
    elif px>=2560*1440: base=28
    elif px>=1920*1080: base=12
    elif px>=1280*720: base=7
    else: base=4
    if fps>=60: base*=1.35
    if profile=='gaming': base*=1.12
    if profile=='nature': base*=1.05
    if codec=='hevc': base*=0.72
    return max(2, round(base,1))

def encoder_available(name):
    p=run(['ffmpeg','-hide_banner','-encoders'])
    return p.returncode==0 and re.search(r'\b'+re.escape(name)+r'\b',p.stdout) is not None

def make_output(src, tag):
    p=Path(src); out=p.with_name(p.stem+'_V2_'+tag+'.mp4'); n=1
    while out.exists(): out=p.with_name(p.stem+'_V2_'+tag+f'_{n}.mp4'); n+=1
    return out

def process(jid,src,target,profile,tiktok,codec_choice,mode='original'):
    try:
        jobs[jid].update(state='processing',progress=1,message='فحص الملف مع الحفاظ على التوقيت...'); m=probe(src)
        requested_fps = 0 if target in ('auto','') else float(target)
        output_fps = max(60.0, requested_fps or float(m['fps'] or 0))
        output_fps_text = str(int(output_fps)) if output_fps.is_integer() else str(round(output_fps,3))
        box = '1920:1080' if m['width'] >= m['height'] else '1080:1920'
        scale_filter = f'scale={box}:force_original_aspect_ratio=decrease:force_divisible_by=2'

        if mode == 'silhouette':
            if m['duration_sec'] > 20 or m['size_bytes'] > 350 * 1024 * 1024:
                raise RuntimeError('وضع عزل اللاعب يقبل مقاطع قصيرة حتى 20 ثانية وحجم 350MB لتفادي نفاد ذاكرة Render.')
            out=make_output(src,'AI_Silhouette_WhiteFog')
            jobs[jid].update(message='تشغيل AI لعزل اللاعب ثم إنشاء خلفية ضبابية بيضاء...', progress=3)
            command=['python3','/app/ai_silhouette.py',str(src),str(out)]
            p=subprocess.run(command,capture_output=True,text=True)
            if p.returncode!=0 or not out.exists():
                raise RuntimeError(p.stderr.strip()[-1200:] or 'فشل عزل اللاعب بالذكاء الاصطناعي.')
            final=probe(out)
            jobs[jid].update(state='done',progress=100,message='تم عزل اللاعب وتركيبه كظل أسود فوق خلفية ضبابية بيضاء.',output=str(out),output_name=out.name,info=final)
            return
        if mode in ('timing','multiplier'):
            # Restored working method: no video/audio re-encode; scale timestamps only.
            # A 15-second 60-FPS source becomes about 30 seconds before TikTok,
            # then TikTok reads the timing back to normal after upload.
            out=make_output(src,'HighestQuality_TikTokTiming')
            cmd=['ffmpeg','-hide_banner','-y','-itsscale','2','-i',str(src),'-map','0','-c','copy','-video_track_timescale','15360','-movflags','+faststart',str(out)]
            jobs[jid].update(message='تجهيز توقيت TikTok بدون إعادة ترميز...')
            p=subprocess.run(cmd,capture_output=True,text=True)
            if p.returncode!=0 or not out.exists(): raise RuntimeError(p.stderr.strip() or 'فشل تجهيز توقيت TikTok.')
            final=probe(out)
            jobs[jid].update(state='done',progress=100,message='تم تجهيز توقيت TikTok بدون إعادة ترميز.',output=str(out),output_name=out.name,info=final)
            return
        if mode == 'style':
            # VideoFX Style: visual-only treatment. Preserve source dimensions, orientation and frame timing.
            # The chain is intentionally light: denoise before sharpening, vivid but controlled color, and clean edges.
            out=make_output(src,'VideoFX_Style_PUBG_CleanClarity')
            style_filter='hqdn3d=1.0:1.0:2.0:2.0,eq=contrast=1.16:saturation=1.18:brightness=0.01,unsharp=5:5:0.55:5:5:0,format=yuv420p'
            source_rate=float(m.get('bitrate_mbps') or 0)
            style_maxrate=max(3.0,min(16.0,(source_rate or 6.0)*1.18))
            style_bufsize=max(6.0,style_maxrate*2)
            encode=['ffmpeg','-hide_banner','-y','-i',str(src),'-map','0:v:0','-map','0:a?','-vf',style_filter,'-c:v','libx264','-preset','superfast','-crf','17','-maxrate',f'{style_maxrate:.1f}M','-bufsize',f'{style_bufsize:.1f}M','-profile:v','high','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart','-fps_mode','passthrough','-progress','pipe:2','-nostats',str(out)]
            jobs[jid].update(message=f'تطبيق PUBG Clean Clarity دون تغيير الدقة أو FPS ({m["width"]}×{m["height"]} | {m["fps"]} FPS)...', progress=5)
            p=subprocess.Popen(encode,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,bufsize=1)
            dur=max(m['duration_sec'],.1); last=5
            for line in p.stderr:
                mm=re.search(r'out_time_ms=(\d+)',line)
                if mm:
                    prog=min(94,5+int((int(mm.group(1))/1000000)/dur*89))
                    if prog>last: last=prog; jobs[jid]['progress']=prog
            if p.wait()!=0 or not out.exists(): raise RuntimeError('فشل تطبيق VideoFX Style على الفيديو.')
            final=probe(out)
            jobs[jid].update(state='done',progress=100,message='اكتمل VideoFX Style مع الحفاظ على FPS والأبعاد والاتجاه.',output=str(out),output_name=out.name,info=final)
            return
        if mode == 'convert':
            out=make_output(src,'Auto_1080p_'+output_fps_text+'FPS')
            encode=['ffmpeg','-hide_banner','-y','-i',str(src),'-map','0:v:0','-map','0:a?','-vf',f'{scale_filter},fps={output_fps_text}','-c:v','libx264','-preset','superfast','-crf','18','-profile:v','high','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-fps_mode','cfr','-progress','pipe:2','-nostats',str(out)]
            jobs[jid].update(message=f'تحويل الفيديو إلى 1080p مع الحفاظ على الاتجاه و{output_fps_text} FPS...', progress=5)
            p=subprocess.Popen(encode,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,bufsize=1)
            dur=max(m['duration_sec'],.1); last=5
            for line in p.stderr:
                mm=re.search(r'out_time_ms=(\d+)',line)
                if mm:
                    prog=min(94,5+int((int(mm.group(1))/1000000)/dur*89))
                    if prog>last: last=prog; jobs[jid]['progress']=prog
            if p.wait()!=0 or not out.exists(): raise RuntimeError('فشل تحويل الفيديو إلى 1080p مع الحفاظ على الاتجاه.')
            final=probe(out)
            jobs[jid].update(state='done',progress=100,message='اكتمل التحويل، وتم فحص الدقة وFPS.',output=str(out),output_name=out.name,info=final)
            return
        if mode == 'fps':
            # Professional path: encode a natural 1080p60 master, then apply the
            # same timestamp trick used by the successful TikTok method.
            out=make_output(src,f'Professional_1080p_{output_fps_text}FPS_TikTokTiming')
            stage=out.with_name(out.stem+'_stage.mp4')
            encode=['ffmpeg','-hide_banner','-y','-i',str(src),'-map','0:v:0','-map','0:a?','-vf',f'{scale_filter},fps={output_fps_text}','-c:v','libx264','-preset','superfast','-crf','18','-profile:v','high','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-fps_mode','cfr','-progress','pipe:2','-nostats',str(stage)]
            jobs[jid].update(message=f'الخيار الاحترافي: تجهيز فيديو 1080p مع الحفاظ على الاتجاه و{output_fps_text} FPS...', progress=5)
            p=subprocess.Popen(encode,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,bufsize=1)
            dur=max(m['duration_sec'],.1); last=5
            for line in p.stderr:
                mm_ms=re.search(r'out_time_ms=(\d+)',line)
                mm=re.search(r'out_time=(\d+):([0-5]?\d):([0-5]?\d(?:\.\d+)?)',line)
                sec=(int(mm_ms.group(1))/1000000) if mm_ms else (int(mm.group(1))*3600+int(mm.group(2))*60+float(mm.group(3)) if mm else None)
                if sec is not None:
                    prog=min(88,5+int(sec/dur*83))
                    if prog>last: last=prog; jobs[jid]['progress']=prog
            if p.wait()!=0 or not stage.exists(): raise RuntimeError('فشل تجهيز النسخة الاحترافية.')
            jobs[jid].update(progress=92,message='تطبيق توقيت TikTok على النسخة الاحترافية...')
            timed=['ffmpeg','-hide_banner','-y','-itsscale','2','-i',str(stage),'-map','0','-c','copy','-video_track_timescale','15360','-movflags','+faststart',str(out)]
            p=subprocess.run(timed,capture_output=True,text=True); stage.unlink(missing_ok=True)
            if p.returncode!=0 or not out.exists(): raise RuntimeError(p.stderr.strip() or 'فشل تطبيق توقيت TikTok.')
            final=probe(out)
            jobs[jid].update(state='done',progress=100,message='تم تجهيز النسخة الاحترافية مع توقيت TikTok.',output=str(out),output_name=out.name,info=final)
            return
        if mode == 'original':
            out=make_output(src,'TikTok_Original')
            shutil.copy2(src,out)
            final=probe(out)
            jobs[jid].update(state='done',progress=100,message='تم حفظ الملف الأصلي دون إعادة ترميز.',output=str(out),output_name=out.name,info=final)
            return
        # TikTok High Quality keeps the source timebase and FPS. We never force CFR or -r,
        # because those options can duplicate/drop frames and make a 15-second clip appear slow.
        out_fps=max(1, round(m['fps'],3)); profile=m['detected_profile'] if profile=='auto' else profile
        codec='hevc' if codec_choice=='hevc' and encoder_available('libx265') else 'h264'
        vcodec='libx265' if codec=='hevc' else 'libx264'; tag=f'{profile}_{int(out_fps)}FPS_{codec}'; out=make_output(src,tag)
        cmd=['ffmpeg','-hide_banner','-y','-i',str(src),'-map','0:v:0','-map','0:a?']
        if tiktok=='1080': cmd += ['-vf',scale_filter]
        cmd += ['-c:v',vcodec,'-crf','16']
        if codec=='h264': cmd += ['-preset','slow','-profile:v','high','-pix_fmt','yuv420p']
        else: cmd += ['-preset','slow','-tag:v','hvc1','-pix_fmt','yuv420p']
        cmd += ['-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart','-fps_mode','passthrough',str(out)]
        jobs[jid].update(message=f'{profile} | {m["width"]}×{m["height"]} | المصدر {out_fps} FPS | {codec.upper()} | جودة CRF 16')
        p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,bufsize=1); dur=max(m['duration_sec'],.1); last=1
        for line in p.stderr:
            mm=re.search(r'time=(\d+):(\d+):(\d+(?:\.\d+)?)',line)
            if mm:
                sec=int(mm.group(1))*3600+int(mm.group(2))*60+float(mm.group(3)); prog=min(99,int(sec/dur*100))
                if prog>last: last=prog; jobs[jid]['progress']=prog
        if p.wait()!=0 or not out.exists(): raise RuntimeError('FFmpeg فشل في معالجة الفيديو.')
        final=probe(out); jobs[jid].update(state='done',progress=100,message='تمت المعالجة والفحص بنجاح.',output=str(out),output_name=out.name,info=final)
    except Exception as e: jobs[jid].update(state='error',progress=0,message=str(e))
    finally: Path(src).unlink(missing_ok=True)

class Handler(BaseHTTPRequestHandler):
    def send_json(self,obj,code=200):
        b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.end_headers()
    def do_GET(self):
        u=urlparse(self.path); q=parse_qs(u.query)
        if u.path=='/':
            b=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path=='/progress': self.send_json(jobs.get(q.get('id',[''])[0],{'state':'error','message':'المهمة غير موجودة'})); return
        if u.path=='/download':
            j=jobs.get(q.get('id',[''])[0]); p=Path(j.get('output','')) if j and j.get('state')=='done' else None
            if not p or not p.exists(): self.send_error(404); return
            self.send_response(200); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Content-Type','video/mp4'); self.send_header('Content-Disposition',f'attachment; filename="{p.name}"'); self.send_header('Content-Length',str(p.stat().st_size)); self.end_headers()
            with p.open('rb') as f: shutil.copyfileobj(f,self.wfile,1024*1024)
            return
        self.send_error(404)
    def _multipart(self):
        ctype=self.headers.get('Content-Type',''); mm=re.search(r'boundary=(?:"([^"]+)"|([^;]+))',ctype)
        if not mm: raise RuntimeError('صيغة رفع غير مدعومة')
        boundary=(mm.group(1) or mm.group(2)).encode(); body=self.rfile.read(int(self.headers.get('Content-Length','0'))); fields={}; files={}
        for part in body.split(b'--'+boundary):
            if b'\r\n\r\n' not in part: continue
            head,data=part.split(b'\r\n\r\n',1); data=data.rstrip(b'\r\n-'); hs=head.decode('utf-8','ignore'); nm=re.search(r'name="([^"]+)"',hs)
            if not nm: continue
            name=nm.group(1); fm=re.search(r'filename="([^"]*)"',hs); files[name]=(fm.group(1),data) if fm else None
            if not fm: fields[name]=data.decode('utf-8','ignore')
        return fields,files
    def do_POST(self):
        try:
            fields,files=self._multipart()
            if 'file' not in files or not files['file']: raise RuntimeError('لم يتم اختيار فيديو')
            name,data=files['file']; tmp=BASE/(uuid.uuid4().hex+(Path(name).suffix or '.input')); tmp.write_bytes(data)
            if self.path=='/probe':
                try: self.send_json({'ok':True,**probe(tmp)})
                finally: tmp.unlink(missing_ok=True)
                return
            if self.path=='/start':
                mode=fields.get('mode','original'); target=fields.get('fps','auto'); profile=fields.get('profile','auto'); tiktok=fields.get('tiktok','off'); codec=fields.get('codec','auto')
                if mode not in ('original','timing','multiplier','fps','convert','tiktok','style','silhouette') or target not in ('auto','60','90','120','preserve') or profile not in ('auto','gaming','nature','standard','pubg_clean_clarity') or tiktok not in ('off','1080') or codec not in ('auto','h264','hevc'): raise RuntimeError('خيار معالجة غير صالح')
                jid=uuid.uuid4().hex; jobs[jid]={'state':'queued','progress':0,'message':'في الانتظار...'}; threading.Thread(target=process,args=(jid,tmp,target,profile,tiktok,codec,mode),daemon=True).start(); self.send_json({'ok':True,'job':jid}); return
            tmp.unlink(missing_ok=True); self.send_error(404)
        except Exception as e: self.send_json({'ok':False,'error':str(e)},400)
    def log_message(self,*args): pass

def main():
    missing=[x for x in ('ffmpeg','ffprobe') if shutil.which(x) is None]
    if missing: print('[!] مفقود: '+', '.join(missing)+'\nنفّذ: pkg update && pkg install python ffmpeg'); return
    server=ThreadingHTTPServer((HOST,PORT),Handler); print(f'\nVideoFX Studio V2\nListening on {HOST}:{PORT}\n')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
