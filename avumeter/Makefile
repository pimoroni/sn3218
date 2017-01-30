all:
	gcc -c avumeter.c -fPIC -o avumeter.o -lwiringPi -Wall -O2
	gcc -shared avumeter.o -lwiringPi -Wl,-soname -Wl,libavumeter.so.0 -o libavumeter.so.0.0.0

install:
	cp libavumeter.so.0.0.0 /usr/local/lib/
	ln -s /usr/local/lib/libavumeter.so.0.0.0 /usr/local/lib/libavumeter.so.0
	ln -s /usr/local/lib/libavumeter.so.0.0.0 /usr/local/lib/libavumeter.so

clean:
	rm avumeter.o
	rm libavumeter.so.0.0.0
