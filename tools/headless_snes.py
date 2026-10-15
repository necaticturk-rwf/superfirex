import ctypes as C
from pathlib import Path
import numpy as np
from PIL import Image

class Game(C.Structure):
    _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
class Emulator:
    keys={'b':0,'y':1,'select':2,'start':3,'up':4,'down':5,'left':6,'right':7,'a':8,'x':9,'l':10,'r':11}
    def __init__(self,rom,core):
        self.core=C.CDLL(str(core))
        self.buttons=set();self.pixels=None;self.format=0;self.frames=0
        self.directory=C.create_string_buffer(b'/tmp')
        @C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
        def environment(cmd,data):
            if cmd==10:
                self.format=C.cast(data,C.POINTER(C.c_int))[0];return True
            if cmd in (9,31,30):
                C.cast(data,C.POINTER(C.c_char_p))[0]=C.cast(self.directory,C.c_char_p);return True
            if cmd==3:
                C.cast(data,C.POINTER(C.c_bool))[0]=False;return True
            if cmd==47:
                C.cast(data,C.POINTER(C.c_uint))[0]=3;return True
            if cmd in (18,11,16,35,36):return True
            return False
        @C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
        def video(data,w,h,pitch):
            if data:
                raw=C.string_at(data,h*pitch)
                self.pixels=(raw,w,h,pitch)
        @C.CFUNCTYPE(None,C.c_int16,C.c_int16)
        def audio(l,r):pass
        @C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)
        def audio_batch(data,frames):return frames
        @C.CFUNCTYPE(None)
        def poll():pass
        @C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
        def state(port,device,index,key):return int(port==0 and key in self.buttons)
        self.callbacks=[environment,video,audio,audio_batch,poll,state]
        for name,cb in zip(('environment','video_refresh','audio_sample','audio_sample_batch','input_poll','input_state'),self.callbacks):getattr(self.core,'retro_set_'+name)(cb)
        self.core.retro_init()
        self.core.retro_load_game.argtypes=[C.POINTER(Game)]
        self.core.retro_load_game.restype=C.c_bool
        self.rom=C.create_string_buffer(Path(rom).read_bytes())
        assert self.core.retro_load_game(C.byref(Game(str(rom).encode(),C.cast(self.rom,C.c_void_p),len(self.rom)-1,None)))
        self.core.retro_set_controller_port_device(0,1)
        self.core.retro_serialize_size.restype=C.c_size_t
        self.core.retro_serialize.argtypes=[C.c_void_p,C.c_size_t]
        self.core.retro_serialize.restype=C.c_bool
        self.core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t]
        self.core.retro_unserialize.restype=C.c_bool
        self.core.retro_get_memory_data.argtypes=[C.c_uint]
        self.core.retro_get_memory_data.restype=C.c_void_p
        self.core.retro_get_memory_size.argtypes=[C.c_uint]
        self.core.retro_get_memory_size.restype=C.c_size_t
    def run(self,n=1,buttons=()):
        self.buttons={self.keys[x] for x in buttons}
        for _ in range(n):self.core.retro_run()
        self.frames+=n
    def press(self,button,n=1):self.run(n,[button]);self.run(12)
    def frame(self):
        raw,w,h,pitch=self.pixels
        if self.format==1:
            a=np.frombuffer(raw,np.uint8).reshape(h,pitch)[:,:w*4].reshape(h,w,4)
            im=Image.fromarray(a[:,:,[2,1,0]])
        else:
            a=np.frombuffer(raw,'<u2').reshape(h,pitch//2)[:,:w]
            if self.format==2:r=(a>>11)&31;g=(a>>5)&63;b=a&31;g=g*255//63
            else:r=(a>>10)&31;g=(a>>5)&31;b=a&31;g=g*255//31
            im=Image.fromarray(np.stack((r*255//31,g,b*255//31),axis=2).astype(np.uint8))
        return im
    def image(self,path):
        self.frame().save(path)
    def save(self,path):
        n=self.core.retro_serialize_size();b=C.create_string_buffer(n);assert self.core.retro_serialize(b,n);Path(path).write_bytes(b.raw)
    def load(self,path):
        b=Path(path).read_bytes();buf=C.create_string_buffer(b);assert self.core.retro_unserialize(buf,len(b))
