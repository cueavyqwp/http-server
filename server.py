import threading
import traceback
import argparse
import socket
import json
import ssl
import os
import re

__all__ = [ "server" ]

class server :

    def __init__( self , port : int = 80 , dir : str = "./" ) -> None :
        self.types = { "GET" : self.get }
        self.socket = socket.socket( socket.AF_INET6 )
        self.socket.setsockopt( socket.IPPROTO_IPV6 , socket.IPV6_V6ONLY , 0 )
        self.https = False
        self.port = port
        self.dir = dir

    def quit( self ) -> None :
        self.socket.close()
        quit()

    def run( self ) -> None :
        self.socket.bind( ( "" , self.port ) )
        self.socket.listen( 0 )
        print( f"http{ "s" if self.https else "" }://{ self.ip( self.socket , 80 ) }\n" )
        main = threading.Thread( target = self.main )
        main.daemon = True
        main.start()
        try :
            while main.is_alive() : main.join( 1 )
        except :
            pass
        self.quit()

    def ip( self , s : socket.socket , default : int = None ) -> str :
        ip , port = s.getsockname()[ : 2 ]
        if s.family == socket.AF_INET6 : ip = f"[{ ip }]"
        if port != default : ip = f"{ ip }:{ port }"
        return ip

    def error( self , text : str ) -> None :
        print( f"{ text }\n{ "".join( f"    | { e }\n" for e in traceback.format_exc().splitlines() ) }" )

    def main( self ) -> None :
        try :
            while True : self.send( *self.socket.accept()[ : 2 ] )
        except :
            self.error( "error at main function :" )

    def send( self , client : socket.socket , ip : tuple ) :
        try :
            try :
                requests = client.recv( 1024 ).decode().splitlines()
                type , path = requests[ 0 ].split()[ : 2 ]
                path = path.split( "?" , 1 )
                text = path[ 1 : ]
                path = path[ 0 ]
                header = {}
                args = {}
                for i in range( 1 , len( requests ) ) :
                    line = requests[ i ]
                    if ":" in line :
                        header.update( dict( [ re.split( "\\s*:\\s*" , line , 1 ) ] ) )
                    else :
                        break
                for line in text + requests[ i : ] :
                    print([ re.split( "\\s*=\\s*" , item ) for item in re.split( "\\s*&\\s*" , line ) ])
                    if line and "=" in line : args.update( dict ( [ re.split( "\\s*=\\s*" , item ) for item in re.split( "\\s*&\\s*" , line ) ] ) )
            except :
                self.error( "error at get requests :" )
            else :
                ip = ip[ : 2 ]
                print( *ip , type , path )
                if type in self.types :
                    code , data = self.types[ type ]( path , args , header , client )
                else :
                    code , data = 505 , b""
                client.send( f"HTTP/1.1 { code }\r\n\r\n".encode() + data )
        except BaseException :
            self.error( "error at send function :" )
        client.close()

    def get( self , path : str , *args ) -> list :
        path , code = os.path.join( self.dir , path[ 1 : ] ) , 404
        if os.path.exists( path ) :
            i = os.path.join( path , "index.html" )
            if os.path.isdir( path ) and os.path.exists( i ) : path = i
            if os.path.exists( path ) and os.path.isfile( path ) : code = 200
        if code == 404 :
            if os.path.isfile( path ) : path = os.path.dirname( path )
            for i in [ os.path.join( i , "404.html" ) for i in [ path , self.dir ] ] :
                if os.path.exists( i ) :
                    path = i
                    break
        if path :
            with open( path , "rb" ) as file : data = file.read()
        else :
            data = b""
        return code , data

if __name__ == "__main__" :
    parser = argparse.ArgumentParser( description = "a simple http server" )
    parser.add_argument( "-port" , "-p" , type = int , help = "server port" , default = 80 )
    parser.add_argument( "-dir" , "-d" , type = str , help = "server directory" , default = os.path.dirname( __file__ ) )
    args = parser.parse_args()
    assert os.path.exists( args.dir ) and os.path.isdir( args.dir ) , "directory not find"
    main = server( **vars( args ) )
    main.run()
