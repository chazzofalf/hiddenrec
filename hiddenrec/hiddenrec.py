class HiddenRecorder(object):
    from io import FileIO as __hr_fileio_cls
    from Crypto.Hash.SHA256 import new as __hr_hash_builder
    from Crypto.Random import get_random_bytes as __hr_random_bytes_generator
    from Crypto.Cipher import AES as __hr_aes_package
    from sounddevice import RawInputStream as __hr_raw_input_stream_cls
    from time import sleep as __hr_sleep_func
    def __init__(self) -> None:
        pass
    def record(self,password:str,output:__hr_fileio_cls=None,filename:str=None):
        if filename is not None and output is None:
            file=HiddenRecorder.__hr_fileio_cls(file=filename,mode="w")   
            self.record_noise(password=password,output=file)
        elif output is not None and filename is None:
            password_bytes=bytes(password,encoding='utf8')
            hash_object=HiddenRecorder.__hr_hash_builder()
            hash_object.update(password_bytes)
            password_key=hash_object.digest()
            del password_bytes
            hash_object=HiddenRecorder.__hr_hash_builder()
            hash_object.update(password_key)
            password_nonce=hash_object.digest()[:16]        
            def write_key():
                cipher=HiddenRecorder.__hr_aes_package.new(key=password_key,nonce=password_nonce,mode=self.__hr_aes_package.MODE_EAX)
                cipher_out=cipher.encrypt_and_digest
                real_key=HiddenRecorder.__hr_random_bytes_generator(32)
                c,m = cipher_out(real_key)
                n = cipher.nonce
                mlen=len(m)
                clen=len(c)
                nlen=len(n)
                mlen=bytes([mlen//256,mlen%256])  
                clen=bytes([clen//256,clen%256])
                nlen=bytes([nlen//256,nlen%256])
                def cmblock():
                    for f in [nlen,n,mlen,m,clen,c]:
                        for ff in f:
                            yield ff   
                cmblock_=bytes([f for f in cmblock()])
                cmblocklen=len(cmblock_)
                cmblocklen=bytes([cmblocklen//256,cmblocklen%256])
                def cmblock():
                    for f in [cmblocklen,cmblock_]:
                        for ff in f:
                            yield ff
                cmblock_=bytes([f for f in cmblock()])
                output.write(cmblock_)
                return real_key
            key=write_key()
            tf_buf=bytearray()
            def output_write(audio_input_data):
                tf_buf.extend(bytes(audio_input_data))
                while len(tf_buf) >= 1 << 15:
                    data=bytes(tf_buf[:1<<15])
                    remainder=bytes(tf_buf[1<<15:])
                    tf_buf.clear()
                    tf_buf.extend(remainder)
                    cipher = HiddenRecorder.__hr_aes_package.new(key=key,mode=HiddenRecorder.__hr_aes_package.MODE_EAX)
                    c,m = cipher.encrypt_and_digest(data)
                    n = cipher.nonce
                    mlen=len(m)
                    clen=len(c)
                    nlen=len(n)
                    mlen=bytes([mlen//256,mlen%256])  
                    clen=bytes([clen//256,clen%256])
                    nlen=bytes([nlen//256,nlen%256])
                    def cmblock():
                        for f in [nlen,n,mlen,m,clen,c]:
                            for ff in f:
                                yield ff   
                    cmblock_=bytes([f for f in cmblock()])
                    cmblocklen=len(cmblock_)
                    cmblocklen=bytes([cmblocklen//256,cmblocklen%256])
                    def cmblock():
                        for f in [cmblocklen,cmblock_]:
                            for ff in f:
                                yield ff
                    cmblock_=bytes([f for f in cmblock()])
                    output.write(cmblock_)                                   
                    tf_buf.clear()
            def output_flush():            
                while len(tf_buf) >= 0:
                    data=bytes(tf_buf[:1<<15])
                    remainder=bytes(tf_buf[1<<15:])
                    tf_buf.clear()
                    tf_buf.extend(remainder)
                    cipher = HiddenRecorder.__hr_aes_package.new(key=key,mode=HiddenRecorder.__hr_aes_package.MODE_EAX)
                    c,m = cipher.encrypt_and_digest(data)
                    n = cipher.nonce
                    mlen=len(m)
                    clen=len(c)
                    nlen=len(n)
                    mlen=bytes([mlen//256,mlen%256])  
                    clen=bytes([clen//256,clen%256])
                    nlen=bytes([nlen//256,nlen%256])
                    def cmblock():
                        for f in [nlen,n,mlen,m,clen,c]:
                            for ff in f:
                                yield ff   
                    cmblock_=bytes([f for f in cmblock()])
                    cmblocklen=len(cmblock_)
                    cmblocklen=bytes([cmblocklen//256,cmblocklen%256])
                    def cmblock():
                        for f in [cmblocklen,cmblock_]:
                            for ff in f:
                                yield ff
                    cmblock_=bytes([f for f in cmblock()])
                    output.write(cmblock_)                                   
                    tf_buf.clear()
            def audio_callback(ind,frames,time,status):
                output_write(ind)            
            def on_escape():
                output_flush()
                output.close()            
            with HiddenRecorder.__hr_raw_input_stream_cls(samplerate=44100,dtype='int16',channels=2,callback=audio_callback) as ss:
                try:                
                    while True:                    
                        HiddenRecorder.__hr_sleep_func(0.01)
                except KeyboardInterrupt:
                    on_escape()     
        else:
            raise ValueError()
    def main(self):
        pass

def main():
    hr=HiddenRecorder()
    hr.main()