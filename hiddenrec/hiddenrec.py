class HiddenRecorder(object):
    from io import RawIOBase as __hr_io_cls
    from io import FileIO as __hr_file_io_cls
    from Crypto.Hash.SHA256 import new as __hr_hash_builder
    from Crypto.Random import get_random_bytes as __hr_random_bytes_generator
    from Crypto.Cipher import AES as __hr_aes_package
    from sounddevice import RawInputStream as __hr_raw_input_stream_cls
    from sounddevice import RawOutputStream as __hr_raw_output_stream_cls
    from time import sleep as __hr_sleep_func
    def __init__(self) -> None:
        pass
    def play(self,password:str,input:__hr_io_cls=None,filename:str=None):
        if filename is not None and input is None:
            file=HiddenRecorder.__hr_file_io_cls(file=filename,mode="r")
            self.play(password=password,input=file)
            file.close()
        elif input is not None and filename is None:
            password_bytes=bytes(password,encoding='utf8')
            hash_object=HiddenRecorder.__hr_hash_builder()
            hash_object.update(password_bytes)
            password_key=hash_object.digest()
            del password_bytes
            hash_object=HiddenRecorder.__hr_hash_builder()
            hash_object.update(password_key)
            password_nonce=hash_object.digest()[:16] 
            def read_next_valid_block(file:HiddenRecorder.__hr_io_cls,key):
                # For recovery. 
                # There is chance the program was forcibly closed and there may be a
                # bad/partial block at the end of the file as of result. 
                # This helps ensure they are ignored and do not break the recovery process.
                valid=False
                valid_block=None
                block=None
                while not valid:
                    try:
                        block=read_block_univ(file,key)
                        valid=True
                        valid_block=block
                    except:
                        print('Partial Block Found. This was ignored.')
                return valid_block
            
            def read_block_univ(file:HiddenRecorder.__hr_io_cls,key):
                size=file.read(2)
                if len(size) == 0:
                    return size
                if len(size) == 2:
                    size = size[0]*256+size[1]
                else:
                    raise IOError()
                cmblock=file.read(size)
                if len(cmblock) != size:
                    raise IOError()
                from io import BytesIO
                tfi = BytesIO(cmblock)
                size = tfi.read(2)
                if len(size) == 2:
                    size = size[0]*256 + size[1]
                else:
                    raise IOError()
                n = tfi.read(size)
                if len(n) != size:
                    raise IOError()
                size = tfi.read(2)
                if len(size) == 2:
                    size=size[0]*256+size[1]
                else:
                    raise IOError()
                m = tfi.read(size)
                if len(m) != size:
                    raise IOError()
                size=tfi.read(2)
                if len(size) == 2:
                    size = size[0]*256+size[1]
                else:
                    raise IOError()
                c = tfi.read(size)
                if len(c) != size:
                    raise IOError()
                from sounddevice import Stream as x
                
                cipher= HiddenRecorder.__hr_aes_package.new(key=key,nonce=n,mode=HiddenRecorder.__hr_aes_package.MODE_EAX)
                return cipher.decrypt_and_verify(c,m)          
            key=read_block_univ(input,password_key)
            eof=[False]
            bufsize=[None]
            block:list[bytearray]=[None]
            blockIndex=[-1]
            def audio_callback(outd,frames,time,status):
                if bufsize[0] is None:
                    bufsize[0]=len(outd)
                if block[0] is None:
                    blockIndex[0]=0
                    block[0]=read_block_univ(input,key)
                    outd[:]=block[0][blockIndex[0]:blockIndex[0]+len(outd)]
                    blockIndex[0] += len(outd)
                if blockIndex[0] == -1 or ((blockIndex[0] + bufsize[0]) >= len(block[0])):                    
                    remainder=bytearray(block[0][blockIndex[0]:])
                    old_block_size=len(block[0])
                    block[0]=read_block_univ(input,key)
                    if block[0] is None or len(block[0]) == 0:                        
                        eof[0] = True
                    else:
                        piece_size = len(outd)-old_block_size+blockIndex[0]
                        remainder.extend(block[0][:piece_size])
                        outd[:]=remainder[:]
                        blockIndex[0] = piece_size                                
                else:
                    outd[:]=block[0][blockIndex[0]:blockIndex[0]+len(outd)]
                    blockIndex[0] += len(outd)
                
            with HiddenRecorder.__hr_raw_output_stream_cls(samplerate=44100,channels=2,dtype='int16',callback=audio_callback):
                while not eof[0]:
                    HiddenRecorder.__hr_sleep_func(0.01)
                
                    
               
    def record(self,password:str,output:__hr_io_cls=None,filename:str=None):
        if filename is not None and output is None:
            file=HiddenRecorder.__hr_file_io_cls(file=filename,mode="w")   
            self.record(password=password,output=file)
            file.close()
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
            def output_flush():                          
                while len(tf_buf) > 0:
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
            def audio_callback(ind,frames,time,status):
                output_write(ind)            
            def on_escape():
                output_flush()                
            with HiddenRecorder.__hr_raw_input_stream_cls(samplerate=44100,dtype='int16',channels=2,callback=audio_callback) as ss:
                try:                
                    while True:                    
                        HiddenRecorder.__hr_sleep_func(0.01)
                except KeyboardInterrupt:
                    on_escape()     
        else:
            raise ValueError()
    def main(self):
        from sys import argv
        if len(argv)==3:
            command=argv[1]
            file=argv[2]            
            if command=='record':
                verified=False
                while not verified:
                    from getpass import getpass
                    rp = getpass(prompt="Recovery Password: ")
                    rpv = getpass(prompt="Verify: ")                
                    
                    if (rp == rpv):                                
                        verified=True                          
                    else:
                        msg = 'Passwords do not match. Try again!' + '\n'
                        from sys import stderr
                        print(msg)
                self.record(password=rp,filename=file)
            elif command=='play':
                from getpass import getpass
                rp = getpass(prompt="Recovery Password: ")
                self.play(password=rp,filename=file)

def main():
    
        
    hr=HiddenRecorder()
    hr.main()