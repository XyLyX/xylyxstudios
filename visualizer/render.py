from pathlib import Path
import argparse, subprocess, math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
from scipy.signal import stft
parser=argparse.ArgumentParser(description="Render the XyLyX wired-globe music visualizer.")
parser.add_argument("audio",type=Path)
parser.add_argument("title")
parser.add_argument("output",type=Path)
parser.add_argument("--series",default="001")
parser.add_argument("--subtitle",default="OFFICIAL AUDIO")
parser.add_argument("--ffmpeg",default="ffmpeg")
parser.add_argument("--encoder",default="libx264")
parser.add_argument("--fonts",type=Path,default=Path("C:/Windows/Fonts"))
args=parser.parse_args()
ff=args.ffmpeg
song=args.audio
assets=Path(__file__).resolve().parent.parent/'assets'
dest=args.output
fps=24; w,h=960,540; cx,cy=480,247
raw=subprocess.check_output([str(ff),'-v','error','-i',str(song),'-vn','-ac','1','-ar','12000','-f','f32le','-'])
audio=np.frombuffer(raw,dtype='<f4')
freq,t,spec=stft(audio,12000,nperseg=1024,noverlap=524)
edges=np.geomspace(46,5600,22)
bands=np.array([np.linalg.norm(abs(spec[(freq>=a)&(freq<b)]),axis=0) for a,b in zip(edges,edges[1:])])
bands=np.clip(bands/np.maximum(np.percentile(bands,96,axis=1)[:,None],0.001),0,1.4)
banner=Image.open(assets/'studio.jpg').convert('RGB')
# Rebuild the stage from the banner's unlettered circuit board.
panel=banner.crop((0,0,566,768)).resize((480,540),Image.Resampling.LANCZOS)
stage=Image.new('RGB',(w,h))
stage.paste(panel,(0,0))
stage.paste(ImageOps.mirror(panel),(480,0))
src=np.asarray(stage,dtype=np.float32)/255
y,x=np.mgrid[:h,:w]
luma=src.mean(2)
relief=np.clip((np.roll(luma,(2,2),axis=(0,1))-luma)*1.9,-.15,.25)
left=np.exp(-((x-175)/245)**2-((y-180)/270)**2)
right=np.exp(-((x-792)/255)**2-((y-160)/250)**2)
center=np.exp(-((x-cx)/200)**2-((y-cy)/190)**2)
base=np.power(src,.63)*1.23
base+=relief[:,:,None]*np.array([.75,.9,1.2])
base+=left[:,:,None]*np.array([.17,.045,.30])+right[:,:,None]*np.array([.025,.21,.30])
base*=1-.27*center[:,:,None]
bg=Image.fromarray(np.uint8(np.clip(base,0,1)*255))
lighting=Image.new('RGB',(w,h))
ld=ImageDraw.Draw(lighting)
ld.ellipse((cx-154,cy-143,cx+154,cy+160),outline='#354da5',width=12)
from PIL import ImageChops
bg=ImageChops.screen(bg,lighting.filter(ImageFilter.GaussianBlur(17)))
bg=Image.blend(bg,Image.new('RGB',(w,h),'#070919'),.45)
wires=[
    (1,(80,240,255),[(-115,-43),(-175,-68),(-226,-117),(-333,-117),(-390,-166),(-445,-166)]),
    (4,(182,102,255),[(-123,-10),(-200,-10),(-245,-51),(-374,-51),(-419,-91),(-463,-91)]),
    (7,(255,185,73),[(-120,31),(-190,58),(-256,58),(-315,114),(-443,114)]),
    (10,(255,87,147),[(115,-43),(175,-68),(226,-117),(333,-117),(390,-166),(445,-166)]),
    (14,(126,255,130),[(123,-10),(200,-10),(245,-51),(374,-51),(419,-91),(463,-91)]),
    (19,(112,145,255),[(120,31),(190,58),(256,58),(315,114),(443,114)]),
]
wires=[(band,color,[(cx+x,cy+y) for x,y in pts]) for band,color,pts in wires]
d=ImageDraw.Draw(bg)
fonts=args.fonts
def font(name,size): return ImageFont.truetype(str(fonts/name),size)
small=font('consola.ttf',13); title=font('bahnschrift.ttf',44)
d.line((35,47,925,47),fill='#3e426a')
d.text((36,19),'XYLYX STUDIOS',font=small,fill='#92eafd')
d.text((924,19),f'AUDIO SERIES   /   {args.series}',anchor='ra',font=small,fill='#b4a7ef')
while title.size>10 and d.textlength(args.title.upper(),font=title)>w-60:
    title=font('bahnschrift.ttf',title.size-1)
d.text((cx,447),args.title.upper(),anchor='mt',font=title,fill='#f7f4ff')
d.text((cx,493),' '.join(args.subtitle.upper()),anchor='mt',font=small,fill='#9bafd4')
logo=np.asarray(Image.open(assets/'logo.jpg').convert('RGB').resize((512,512)))/255
size=248
gy,gx=np.mgrid[-1:1:complex(size),-1:1:complex(size)]
mask=(gx*gx+gy*gy<=1)
gz=np.sqrt(np.clip(1-gx*gx-gy*gy,0,1))
longitude=np.arctan2(gx,gz)/(2*np.pi)
latitude=np.arcsin(np.clip(gy,-1,1))/np.pi
def light(dx,dy,dz):
    return np.maximum(0,(gx*dx+gy*dy+gz*dz)/math.sqrt(dx*dx+dy*dy+dz*dz))
violet=light(-1,-.4,.18)
cyan=light(1,-.22,.16)
front=light(0,-.3,1)
rim=(1-gz)**3*mask
sphere_frames=[]
for j in range(192):
    # Repeat the studio emblem on opposing sides of the rotating globe.
    u=np.mod((longitude-j/192)*2+.5,1)
    v=np.clip(latitude*1.75+.5,0,1)
    tex=logo[(v*511).astype(int),(u*511).astype(int)]
    lit=tex*(.32+.80*front[:,:,None])
    lit+=violet[:,:,None]*np.array([.29,.065,.60])
    lit+=cyan[:,:,None]*np.array([.035,.38,.53])
    lit+=rim[:,:,None]*np.array([.07,.12,.23])
    pixels=np.dstack([np.uint8(np.clip(lit,0,1)*255),mask.astype(np.uint8)*255])
    sphere_frames.append(Image.fromarray(pixels))
angles=np.arange(144)*2*np.pi/144-np.pi/2
cos=np.cos(angles); sin=np.sin(angles)
pos=(1+np.cos(angles+.22))/2*19
colors=[(int(83+86*q),int(221-129*q),int(248+7*q)) for q in (1+np.sin(angles))/2]
def ring(radius):
    return list(zip(cx+radius*cos,cy+radius*sin))
def frame(i):
    im=bg.copy()
    b=bands[:,min(i,bands.shape[1]-1)]
    d=ImageDraw.Draw(im)
    for band,color,pts in wires:
        gain=min(1,float(b[band]))
        bloom=tuple(int(c*(.11+.21*gain)) for c in color)
        core=tuple(int(c*(.36+.64*gain)) for c in color)
        d.line(pts,fill=bloom,width=9+int(5*gain),joint='curve')
        d.line(pts,fill=core,width=2+int(3*gain),joint='curve')
        for x,y in pts[1:]:
            d.ellipse((x-3,y-3,x+3,y+3),fill=core)
        phase=(i*(.9+band*.035)%100)/100*(len(pts)-1)
        j=int(phase)
        mix=phase-j
        x=pts[j][0]+(pts[j+1][0]-pts[j][0])*mix
        y=pts[j][1]+(pts[j+1][1]-pts[j][1])*mix
        r=2+4*gain
        d.ellipse((x-r,y-r,x+r,y+r),fill=core)
    sphere=sphere_frames[i%len(sphere_frames)]
    im.paste(sphere,(cx-size//2,cy-size//2),sphere)
    bass=float(np.mean(b[:5]))
    radius=133+6*min(1,bass)
    pulse=np.interp(pos,np.arange(len(b)),b)
    outer=radius+4+24*pulse**1.45
    low=radius+7+7*pulse
    d.line(ring(radius+1)+[ring(radius+1)[0]],fill='#373c86',width=8)
    d.line(ring(radius)+[ring(radius)[0]],fill='#70e9ff',width=2)
    for j,(p1,p2) in enumerate(zip(ring(low),ring(outer+5))):
        d.line((p1,p2),fill=colors[j],width=2)
    gold=ring(outer+10+9*pulse**1.4)
    d.line(gold+[gold[0]],fill='#ffbd68',width=2)
    path=ring(outer+5)
    d.line(path+[path[0]],fill='#73d9ff',width=1)
    d.line((38,518,922,518),fill='#323653',width=2)
    d.line((38,518,38+884*i/max(1,count-1),518),fill='#71d8fa',width=2)
    return im
count=math.ceil(len(audio)/12000*fps)
cmd=[str(ff),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','pipe:0','-i',str(song),'-map','0:v','-map','1:a','-vf','format=yuv420p','-c:v',args.encoder,'-b:v','3M','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',str(dest)]
with subprocess.Popen(cmd,stdin=subprocess.PIPE) as p:
    for i in range(count):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    if p.wait(): raise SystemExit('Video encoding failed')


