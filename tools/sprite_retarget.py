"""Compile canonical costume views onto the game's native animation geometry.

The generated RGB views supply appearance; native masks, frame indexes and
joint positions supply geometry. Nearest native view/rotation is cached for
each modular collection. This is a small-pixel pose approximation, not a new
set of motion-captured animation frames.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageOps
from build_reference_trio import decode, encode

CACHE = Path('/tmp/sfpx-native-pose-cache')

def split_cells(indices):
    return np.array([indices[y:y+16,x:x+16] for y in range(0,indices.shape[0],16)
                     for x in range(0,128,16)])

def join_cells(cells):
    return np.block([[cells[y*8+x] for x in range(8)] for y in range(len(cells)//8)])

def bounds(array):
    y,x=np.nonzero(array)
    return (int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)) if len(x) else (0,0,16,16)

def transform(array,mirror,angle):
    im=Image.fromarray(array.astype('uint8'))
    if mirror: im=ImageOps.mirror(im)
    return im.rotate(angle,Image.Resampling.NEAREST,expand=True,fillcolor=0)

def normalized(array):
    im=Image.fromarray(array)
    return np.asarray(im.crop(bounds(array)).resize((12,12),Image.Resampling.NEAREST))

def features(array):
    a=normalized(array)
    # Shape dominates; native shade/category arrangement distinguishes the
    # chest from the back when their silhouettes are similar.
    return np.concatenate(((a!=0).ravel().astype(np.int32)*30,
                           a.astype(np.int32).ravel()))

def pose_map(data):
    digest=hashlib.sha256(data).hexdigest();CACHE.mkdir(exist_ok=True)
    path=CACHE/('integer-v2-'+digest+'.json')
    if path.exists(): return json.loads(path.read_text())
    frames=split_cells(decode(data));basis=frames[:8]
    candidates=[];vectors=[]
    for i,frame in enumerate(basis):
        for mirror in [False,True]:
            for angle in [0,30,-30,60,-60,90,-90,120,-120,150,-150,180]:
                a=np.asarray(transform(frame,mirror,angle))
                candidates.append([i,mirror,angle]);vectors.append(features(a))
    matrix=np.array(vectors);targets=np.array([features(f)for f in frames])
    cost=(targets**2).sum(1)[:,None]+(matrix**2).sum(1)[None,:]-2*targets@matrix.T
    mapping=[candidates[int(i)]for i in cost.argmin(1)]
    for i in range(8): mapping[i]=[i,False,0]
    path.write_text(json.dumps(mapping));return mapping

def normalize_generated(rgb,original):
    # Fit each canonical drawing to the native view's bounds before rotating.
    mask=rgb.max(2)>22
    if np.count_nonzero(mask)<5: return rgb
    box=bounds(mask);target=bounds(original);im=Image.new('RGB',(16,16))
    patch=Image.fromarray(rgb.astype('uint8')).crop(box).resize(
        (target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS)
    im.paste(patch,target[:2]);return np.asarray(im)

def compile_part(data,rgb_views,palette,bare=False,ink=False,preserve_skin=False,covered=False):
    original=split_cells(decode(data));out=original.copy();basis=original[:8]
    views=[normalize_generated(rgb,frame)for rgb,frame in zip(rgb_views,basis)]
    mapping=pose_map(data)
    pal=np.asarray(palette,dtype=np.int32);allowed=np.arange(1,16,dtype=np.uint8)
    for i,(frame,(view,mirror,angle))in enumerate(zip(original,mapping)):
        mask=frame!=0
        if mask.sum()<8: continue
        if bare and not ink: continue
        reference=np.asarray(transform(basis[view],mirror,angle))
        rgb=transform(views[view],mirror,angle).crop(bounds(reference))
        box=bounds(frame);w,h=box[2]-box[0],box[3]-box[1]
        rgb=np.asarray(rgb.resize((w,h),Image.Resampling.LANCZOS)).astype(np.int32)
        if bare:
            dark=(rgb.max(2)<95)&(rgb.max(2)-rgb.min(2)<65)
            patch=out[i,box[1]:box[3],box[0]:box[2]]
            skin=np.isin(frame[box[1]:box[3],box[0]:box[2]],[2,3,4,7])
            patch[dark&skin]=1
            continue
        q=allowed[((rgb[:,:,None,:]-pal[None,None,1:,:])**2).sum(3).argmin(2)]
        if covered:
            # Source costume views can include arms beside the shirt. Arms
            # render separately in-game; their skin must not open the shirt.
            skin=np.isin(q,[2,3,4,7]);cloth=np.arange(10,13,dtype=np.uint8)
            shades=cloth[((rgb[:,:,None,:]-pal[None,None,10:13,:])**2).sum(3).argmin(2)]
            q[skin]=shades[skin]
        if preserve_skin:mask &= ~np.isin(frame,[2,3,4,7])
        submask=mask[box[1]:box[3],box[0]:box[2]]
        patch=out[i,box[1]:box[3],box[0]:box[2]];patch[submask]=q[submask]
    return encode(join_cells(out))

@lru_cache(maxsize=100)
def canonical_layout(path,members):
    # Generated costume pieces may join into headless paper dolls and leave
    # footer padding. Recover character blocks from actual ink, not canvas
    # height. This also prevents a boot row becoming the next chest row.
    im=Image.open(path).convert('RGB');rgb=np.asarray(im)
    occupied=(rgb.max(2)>12).mean(1)>.01
    positions=np.flatnonzero(occupied)
    assert len(positions),path
    top,bottom=int(positions[0]),int(positions[-1])+1
    gaps=[];start=None
    for y in range(top,bottom+1):
        blank=y==bottom or not occupied[y]
        if blank and start is None:start=y
        if not blank and start is not None:
            if y-start>=2:gaps.append((start,y))
            start=None
    cuts=[top]
    weights=[3,4,4]if Path(path).stem=='canonical-04'else [1]*members
    for n in range(1,members):
        target=top+(bottom-top)*sum(weights[:n])/sum(weights)
        choices=[g for g in gaps if cuts[-1]+(bottom-top)*.15<(g[0]+g[1])/2<target+(bottom-top)*.16]
        if choices:
            gap=min(choices,key=lambda g:abs((g[0]+g[1])/2-target)-.5*(g[1]-g[0]))
            cuts.append(round((gap[0]+gap[1])/2))
        else:cuts.append(round(target))
    cuts.append(bottom);blocks=[]
    for a,b in zip(cuts,cuts[1:]):
        ys=np.flatnonzero(occupied[a:b]);blocks.append((a+int(ys[0]),a+int(ys[-1])+1))
    return blocks

def sheet_views(path,member_index,part_index,members):
    im=Image.open(path).convert('RGB')
    top,bottom=canonical_layout(str(path),members)[member_index]
    short=Path(path).stem=='canonical-02' or (Path(path).stem=='canonical-04'and member_index==0)
    fractions=[0,0,.34,.67,1]if short else [0,.27,.45,.72,1]
    # Separate rows of garment pieces have real gaps. Prefer those over the
    # anatomical fractions used for joined paper-doll output.
    rgb=np.asarray(im)[top:bottom];occupied=(rgb.max(2)>12).mean(1)>.01
    segments=[];start=None
    for y in range(len(occupied)+1):
        on=y<len(occupied)and occupied[y]
        if on and start is None:start=y
        if not on and start is not None:
            if y-start>8:segments.append((start,y))
            start=None
    if len(segments)==(3 if short else 4):
        index=part_index-1 if short else part_index
        a,b=segments[max(0,index)];a+=top;b+=top
    else:
        a=round(top+(bottom-top)*fractions[part_index]);b=round(top+(bottom-top)*fractions[part_index+1])
    return [np.asarray(im.crop((round(x*im.width/8),a,round((x+1)*im.width/8),b))
             .resize((16,16),Image.Resampling.LANCZOS)).astype(np.int32)for x in range(8)]
