"""Export actual-game selection comparison and Mankind's captured motion segment."""
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageSequence
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--old-selection',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True)
a=p.parse_args();old=Image.open(a.old_selection);new=Image.open(a.proof_dir/'mankind-selection.png')
canvas=Image.new('RGB',(448,384),(23,26,31));draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
for i,(title,source)in enumerate([('Önce',old),('Düzeltilmiş',new)]):
 # Only crop/enlarge recorded game output. Character pixels are unedited.
 crop=source.crop((14,42,65,125)).resize((204,332),Image.Resampling.NEAREST)
 canvas.paste(crop,(i*224+10,40));draw.text((i*224+10,8),title,font=font,fill='white')
canvas.save(a.proof_dir/'mankind-tie-before-after.png')
with Image.open(a.proof_dir/'reference-trio-gameplay.gif')as gif:
 frames=[f.convert('RGB').copy()for n,f in enumerate(ImageSequence.Iterator(gif))if 60<=n<120]
assert len(frames)==60
frames[0].save(a.proof_dir/'mankind-tie-gameplay.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,disposal=2)
